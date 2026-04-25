"""
工具系统 — 本地模型 Agent Tool Calls
支持: 天气、搜索、计算器、时间、新闻

MiniCPM-o 通过 JSON 格式输出工具调用 → 本地执行 → 结果拼回 context → 最终回复
"""
import json
import re
import ast
import logging
import subprocess
import urllib.parse
from datetime import datetime
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# ============ 工具注册表 ============

class Tool:
    def __init__(self, name: str, description: str, param_desc: str, func: Callable):
        self.name = name
        self.description = description
        self.param_desc = param_desc  # 参数描述
        self.func = func

    def run(self, query: str) -> str:
        try:
            return self.func(query)
        except Exception as e:
            return f"工具执行失败: {e}"


def _weather(query: str) -> str:
    """天气查询 — wttr.in（使用 curl 绕过系统代理）"""
    city = query.strip()
    if not city:
        return "请提供城市名称"
    try:
        import subprocess
        cmd = ["curl", "-s", "--noproxy", "*", f"https://wttr.in/{city}?format=3"]
        r = subprocess.run(cmd, timeout=10, capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode().strip()
        return f"天气查询失败: {r.stderr.decode().strip() or 'unknown'}"
    except Exception as e:
        return f"天气查询失败: {e}"


def _search(query: str) -> str:
    """网页搜索 — 用 Tavily API"""
    if not query.strip():
        return "请提供搜索关键词"
    try:
        import subprocess, json
        payload = json.dumps({
            "api_key": "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",
            "query": query,
            "max_results": 3,
            "search_depth": "basic"
        })
        cmd = [
            "curl", "-s", "--noproxy", "*",
            "-X", "POST",
            "-H", "Content-Type: application/json",
            "-d", payload,
            "https://api.tavily.com/search"
        ]
        r = subprocess.run(cmd, timeout=15, capture_output=True)
        if r.returncode != 0:
            return f"搜索失败: {r.stderr.decode().strip()}"
        data = json.loads(r.stdout.decode())
        results = data.get("results", [])
        if not results:
            return "未找到相关结果"
        out = []
        for i, res in enumerate(results[:3]):
            title = res.get("title", "")
            snippet = res.get("content", "")[:100]
            out.append(f"{i+1}. {title} — {snippet}")
        return "\n".join(out)
    except Exception as e:
        return f"搜索失败: {e}"


def _calc(query: str) -> str:
    """安全计算器 — 使用 Python eval（用户输入已经过正则过滤）"""
    expr = query.strip()
    # 安全检查：只允许数字和运算符
    if not re.match(r'^[\d\s\+\-\*\/\.\(\)\%\^]+$', expr):
        return f"不支持的表达式: {expr}"
    try:
        # 用 eval 计算（正则已过滤危险字符）
        result = eval(expr, {"__builtins__": {}}, {})
        return f"{expr} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def _time(query: str) -> str:
    """当前时间"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')} (北京时间)"


def _news(query: str) -> str:
    """新闻搜索 — 用 Tavily"""
    return _search(f"最新新闻 {query}")


def _home(query: str) -> str:
    """智能家居控制 — 控制灯光、空调、开关等"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from jarvis.smart_home_intent import smart_home_tool
    return smart_home_tool(query)


def _flight(query: str) -> str:
    """机票查询/搜索 — 查询航班信息、价格、订票建议"""
    if not query.strip():
        return "请说清楚出发地和目的地，比如'北京到上海机票'"
    return _search(f"最近 {query} 机票 价格 航班 订票")


def _train(query: str) -> str:
    """火车票查询/搜索 — 查询高铁、动车、火车车次、票价"""
    if not query.strip():
        return "请说清楚出发地和目的地，比如'北京到上海火车票'"
    return _search(f"{query} 火车票 车次 价格 12306")


def _hotel(query: str) -> str:
    """酒店查询/预订推荐 — 查询酒店价格、预订建议"""
    if not query.strip():
        return "请说清楚城市和区域，比如'北京朝阳区酒店'"
    return _search(f"{query} 酒店 价格 预订推荐")


def _movie(query: str) -> str:
    """电影票/影院查询 — 查询影院、场次、排片"""
    if not query.strip():
        return "请说清楚电影名或城市，比如'北京 流浪地球2 排片'"
    return _search(f"{query} 电影票 影院 排片")


# 工具注册表
TOOL_REGISTRY = {
    "weather": Tool(
        name="weather",
        description="查询天气",
        param_desc="城市名（中文或英文）",
        func=_weather
    ),
    "search": Tool(
        name="search",
        description="搜索网页",
        param_desc="搜索关键词",
        func=_search
    ),
    "calc": Tool(
        name="calc",
        description="计算数学表达式",
        param_desc="数学表达式，如 2+2*3",
        func=_calc
    ),
    "time": Tool(
        name="time",
        description="查询当前时间",
        param_desc="（空）",
        func=_time
    ),
    "news": Tool(
        name="news",
        description="搜索新闻",
        param_desc="新闻关键词",
        func=_news
    ),
    "home": Tool(
        name="home",
        description="智能家居控制 — 控制灯光、空调、开关、窗帘等设备，或查询设备状态",
        param_desc="自然语言指令，如 '打开客厅的灯' '把温度调到26度' '关闭所有灯' '卧室空调状态'",
        func=_home
    ),
    "flight": Tool(
        name="flight",
        description="机票查询/搜索 — 查询航班信息、票价、订票建议",
        param_desc="出发地到目的地，如 '北京到上海'",
        func=_flight
    ),
    "train": Tool(
        name="train",
        description="火车票查询/搜索 — 查询高铁、动车、火车车次、票价",
        param_desc="出发地到目的地，如 '北京到上海'",
        func=_train
    ),
    "hotel": Tool(
        name="hotel",
        description="酒店查询/预订推荐 — 查询酒店价格、预订建议",
        param_desc="城市区域，如 '北京朝阳区'",
        func=_hotel
    ),
    "movie": Tool(
        name="movie",
        description="电影票/影院查询 — 查询影院、场次、排片",
        param_desc="电影名城市，如 '北京 流浪地球2'",
        func=_movie
    ),
}


# MiniCPM-o system prompt（工具调用版）
TOOL_SYSTEM_PROMPT = """你是一个智能助手。你可以通过工具来回答需要实时信息的问题。

可用工具及参数格式：
- weather: 查询天气，参数是城市名（中文或英文），如 "北京"
- search: 搜索网页，参数是搜索关键词 — 当你不确定用哪个工具或问题需要最新信息时，都用这个工具
- news: 搜索新闻，参数是新闻关键词
- calc: 计算数学表达式，参数是表达式，如 "2+2*3"
- time: 查询当前时间，参数留空
- home: 智能家居控制，参数是自然语言指令，如 "打开客厅的灯" "把温度调到26度" "关闭所有灯" "卧室空调状态"
- flight: 机票查询，参数是出发地到目的地，如 "北京到上海"
- train: 火车票查询，参数是出发地到目的地，如 "北京到上海"
- hotel: 酒店查询，参数是城市区域，如 "北京朝阳区"
- movie: 电影票/影院查询，参数是电影名和城市，如 "北京 流浪地球2"

规则：
1. 任何需要实时/最新信息的问题（票价、余票、价格、营业时间、位置等）都必须调用工具搜索
2. 如果你不确定该用哪个工具，直接用 search 工具搜索，不要凭记忆回答
3. 当你需要使用工具时，必须严格按以下JSON格式回答（不要加任何其他内容）:
{"tool": "工具名", "query": "参数"}
4. 当你不需要工具时，直接用中文回答用户的问题。"""


def parse_tool_call(text: str) -> Optional[dict]:
    """
    尝试从文本中解析工具调用 JSON
    返回 {"tool": "xxx", "query": "yyy"} 或 None
    """
    text = text.strip()
    # 尝试直接解析
    if text.startswith("{"):
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "tool" in obj:
                return obj
        except json.JSONDecodeError:
            pass
    # 从文本中提取 JSON
    match = re.search(r'\{[^{}]*"tool"[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group())
            if "tool" in obj:
                return obj
        except json.JSONDecodeError:
            pass
    return None


def execute_tool_call(tool_name: str, query: str) -> str:
    """执行工具调用"""
    tool = TOOL_REGISTRY.get(tool_name)
    if not tool:
        return f"未知工具: {tool_name}，可用工具: {', '.join(TOOL_REGISTRY.keys())}"
    return tool.run(query)


# ==================== P3: 第三方生态工具扩展 ====================
# Hey Tuya 启发：生活服务闭环（票务、外卖、打车）→ 元芳工具生态补全

def _stock(query: str) -> str:
    """A股/基金行情查询 — 搜索实时价格和涨跌"""
    if not query.strip():
        return "请提供股票代码或名称，如 '贵州茅台' 或 '600519'"
    return _search(f"{query} 股票 实时行情 今日收盘")

def _delivery(query: str) -> str:
    """外卖/快递查询 — 搜索配送情况（无真实API，用搜索模拟）"""
    if not query.strip():
        return "请提供外卖订单号或快递单号"
    return _search(f"{query} 外卖配送 快递进度")

def _tv_program(query: str) -> str:
    """电视节目查询 — 搜索节目单和播放时间"""
    if not query.strip():
        return "请提供电视台名称或节目名，如 '央视一套' 或 '新闻联播'"
    return _search(f"{query} 节目单 播出时间 电视")

def _reminder(query: str) -> str:
    """设置提醒 — 将提醒写入本地文件（未来可对接日历API）"""
    import datetime, os
    parts = query.strip().split("|")
    if len(parts) < 2:
        return "格式：时间|提醒内容，如 '明天9点|开会'"
    time_str, content = parts[0].strip(), parts[1].strip()
    reminder_file = os.path.expanduser("~/.yuanfang_reminders.txt")
    with open(reminder_file, "a") as f:
        f.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] {time_str} — {content}\n")
    return f"已设置提醒：{time_str} {content}"

def _meeting(query: str) -> str:
    """会议纪要整理 — 搜索最近对话生成摘要（用搜索模拟会议内容查询）"""
    if not query.strip():
        return "请提供会议主题或关键词"
    return _search(f"会议纪要 {query} 要点 结论")

def _recipe(query: str) -> str:
    """菜谱/食谱查询 — 搜索做法和食材"""
    if not query.strip():
        return "请提供菜名，如 '红烧肉'"
    return _search(f"{query} 菜谱 做法 食材 步骤")

def _translate(query: str) -> str:
    """翻译 — 调用搜索翻译结果"""
    if not query.strip():
        return "请提供要翻译的内容"
    return _search(f"翻译 {query}")


# 扩展 TOOL_REGISTRY
TOOL_REGISTRY["stock"]     = Tool("stock",     "A股/基金行情查询",          "股票名称或代码",     _stock)
TOOL_REGISTRY["delivery"]  = Tool("delivery",  "外卖/快递查询",             "订单号或快递单号",   _delivery)
TOOL_REGISTRY["tv"]        = Tool("tv",        "电视节目查询",              "电视台或节目名",     _tv_program)
TOOL_REGISTRY["reminder"]  = Tool("reminder",  "设置提醒（写入本地文件）",   "时间|内容",         _reminder)
TOOL_REGISTRY["meeting"]   = Tool("meeting",   "会议纪要整理",              "会议主题/关键词",    _meeting)
TOOL_REGISTRY["recipe"]    = Tool("recipe",    "菜谱/食谱查询",             "菜名",              _recipe)
TOOL_REGISTRY["translate"]= Tool("translate", "翻译",                     "要翻译的内容",      _translate)


def has_tool_prefix(text: str) -> bool:
    """判断文本是否包含工具调用 JSON"""
    return parse_tool_call(text) is not None
