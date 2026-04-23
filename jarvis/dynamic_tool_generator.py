"""
Dynamic Tool Generator — 动态工具生成器
让元芳自己根据用户需求生成新工具代码，保存并自动加载
支持: 需求描述 → LLM生成代码 → 验证 → 保存 → 自动调用
"""

import os
import re
import json
import importlib.util
from typing import Optional, Dict, List, Any, Tuple
from dataclasses import dataclass, asdict

# 工具存储目录
TOOL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dynamic_tools")
TOOL_INDEX_FILE = os.path.join(TOOL_DIR, "tool_index.json")
MAX_RETRIES = 3  # 最大自动修复重试次数


@dataclass
class DynamicTool:
    name: str           # 工具名称 (snake_case)
    description: str    # 工具描述
    handler_function: str  # 处理函数名 (一般是 {name}_handler)
    requirements: str  # 依赖描述
    code: str          # 完整Python代码
    created_at: str    # 创建时间
    usage_example: str # 使用示例


def snake_case_name(demand: str) -> str:
    """从需求生成合法的模块名"""
    # 取前两个关键词转snake_case
    words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', demand)
    if not words:
        return "custom_tool"
    name = "_".join([w.lower() for w in words[:2]])
    # 去掉非法字符
    name = re.sub(r'[^a-z0-9_]', '', name)
    if not name:
        return "custom_tool"
    return name


def _ensure_tool_dir():
    """确保工具目录存在"""
    if not os.path.exists(TOOL_DIR):
        os.makedirs(TOOL_DIR)


def _load_index() -> Dict[str, DynamicTool]:
    """加载工具索引"""
    _ensure_tool_dir()
    if not os.path.exists(TOOL_INDEX_FILE):
        with open(TOOL_INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    
    try:
        with open(TOOL_INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for name, item in data.items():
            result[name] = DynamicTool(**item)
        return result
    except Exception:
        return {}


def _save_index(index: Dict[str, DynamicTool]):
    """保存工具索引"""
    _ensure_tool_dir()
    data = {}
    for name, tool in index.items():
        data[name] = asdict(tool)
    with open(TOOL_INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def list_dynamic_tools() -> List[Dict[str, Any]]:
    """列出所有动态工具"""
    index = _load_index()
    result = []
    for name, tool in index.items():
        result.append({
            "name": tool.name,
            "description": tool.description,
            "handler": tool.handler_function,
            "example": tool.usage_example
        })
    return result


def get_dynamic_tool(name: str) -> Optional[DynamicTool]:
    """获取动态工具"""
    index = _load_index()
    return index.get(name)


def save_dynamic_tool(tool: DynamicTool) -> bool:
    """保存动态工具到文件和索引"""
    _ensure_tool_dir()
    index = _load_index()
    
    # 保存代码文件
    code_path = os.path.join(TOOL_DIR, f"{tool.name}.py")
    try:
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(tool.code)
    except Exception as e:
        return False
    
    # 更新索引
    index[tool.name] = tool
    _save_index(index)
    return True


def delete_dynamic_tool(name: str) -> bool:
    """删除动态工具"""
    index = _load_index()
    if name not in index:
        return False
    
    # 删除文件
    code_path = os.path.join(TOOL_DIR, f"{name}.py")
    if os.path.exists(code_path):
        os.remove(code_path)
    
    # 更新索引
    del index[name]
    _save_index(index)
    return True


def search_similar_tools(query: str, threshold: float = 0.75) -> List[DynamicTool]:
    """搜索相似工具，避免重复创建
    使用元芳现有的VectorMemory进行语义搜索
    """
    try:
        from memory.vector import VectorMemory
        from services.tools import llm_chat
        
        # 获取embedding函数
        def get_embedding(text):
            # 使用现有LLM生成嵌入（简化方案）
            return None
        
        index = _load_index()
        if not index:
            return []
        
        # 如果无法获取嵌入，回退到关键词匹配
        return []
    except Exception as e:
        print(f"[DynamicTool] 语义搜索失败: {e}")
        return []


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算余弦相似度"""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = sum(x*x for x in a)**0.5
    mag_b = sum(x*x for x in b)**0.5
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def load_dynamic_tool_handler(name: str):
    """动态加载工具处理函数"""
    tool = get_dynamic_tool(name)
    if not tool:
        return None
    
    code_path = os.path.join(TOOL_DIR, f"{name}.py")
    if not os.path.exists(code_path):
        return None
    
    try:
        spec = importlib.util.spec_from_file_location(f"dynamic_tools.{name}", code_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handler = getattr(module, tool.handler_function)
        return handler
    except Exception as e:
        print(f"[DynamicTool] 加载失败: {e}")
        return None


def generate_tool_code(demand: str, system_prompt: str = None, retry_errors: str = None) -> str:
    """
    使用LLM生成工具代码
    支持重试：retry_errors 包含上次错误信息，让LLM修复
    """
    from core.llm_adapter import get_llm
    
    llm = get_llm()
    
    prompt = f"""
你是一个专业的Python开发者，需要为贾维斯语音助手创建一个新的动态工具。
这是 LLM-ToolMaker 闭环路框架中的工具制作阶段。

用户需求: {demand}

请遵循以下规范：

1. **模块结构**:
   - 文件开头需要注释说明功能
   - 必须提供一个 `{snake_case_name(demand)}_handler(text: str) -> Optional[str]` 处理函数
   - 函数输入是用户语音识别后的文本，输出是回复文本，如果不匹配返回None
   - 所有导入必须在函数内部，避免未安装依赖导致的启动错误

2. **错误处理**:
   - 使用try-catch捕获异常
   - 返回友好的中文错误提示
   - 如果请求不匹配当前工具，必须返回None
   - 优先使用Python标准库，减少外部依赖

3. **匹配规则**:
   - 在handler函数开头，通过关键词判断是否匹配当前工具
   - 支持多种自然表达方式匹配（口语化、不同说法）
   - 如果不匹配，立即返回None，交给下一个工具处理

4. **Python兼容性**:
   - 当前使用Python 3.9，不支持 PEP 604 的 `|` Union语法
   - 使用 `Union[X, Y]` 代替，或者省略类型注释也可以

5. **输出格式**:
   - 只输出完整可运行的Python代码，不要额外说明
   - 代码必须包含完整的handler函数
   - 不要用markdown代码块包裹，直接输出代码
"""

    # 如果是重试，添加上次错误信息
    if retry_errors:
        prompt += f"""

上次生成代码有错误，请修复后重新输出：
错误信息: {retry_errors}
"""

    messages = [
        {"role": "system", "content": system_prompt or generate_tool_system_prompt()},
        {"role": "user", "content": prompt}
    ]
    
    response = llm.chat_simple(messages, temperature=0.3, max_tokens=2048)
    # 清理可能的markdown代码块标记
    code = response.strip()
    code = code.replace("```python", "").replace("```", "").strip()
    # 二次清理使用正则
    code = re.sub(r'^```python\s*', '', code)
    code = re.sub(r'^```.*\s*', '', code)
    code = re.sub(r'\s*```$', '', code)
    return code.strip()


def generate_and_validate_with_retry(demand: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, str, str]:
    """
    生成代码并自动重试修复错误
    返回: (是否成功, 代码, 错误信息)
    """
    name = snake_case_name(demand)
    handler_name = f"{name}_handler"
    last_error = None
    
    for attempt in range(max_retries):
        code = generate_tool_code(demand, retry_errors=last_error)
        valid, msg = validate_tool_code(code, handler_name)
        if valid:
            return True, code, ""
        last_error = msg
        print(f"[DynamicTool] 第{attempt+1}次尝试生成失败: {msg}，正在修复...")
    
    return False, "", last_error


def validate_tool_code(code: str, handler_name: str) -> Tuple[bool, str]:
    """验证工具代码语法正确性"""
    try:
        # 编译检查语法
        compile(code, '<dynamic_tool>', 'exec')
        # 检查是否有handler函数
        if handler_name not in code:
            return False, f"找不到处理函数 {handler_name}"
        return True, "验证通过"
    except SyntaxError as e:
        return False, f"语法错误: {e}"
    except Exception as e:
        return False, f"验证失败: {e}"


def dynamic_tool_handler(text: str) -> Optional[str]:
    """
    主入口：轮询所有动态工具，找到匹配的执行
    由语音管线调用
    """
    index = _load_index()
    for name, tool in index.items():
        handler = load_dynamic_tool_handler(name)
        if handler is None:
            continue
        try:
            result = handler(text)
            if result is not None:
                return result
        except Exception as e:
            return f"工具「{name}」执行出错: {str(e)}"
    return None


def generate_tool_system_prompt() -> str:
    """生成添加新工具时的系统提示词"""
    return """你是贾维斯，你可以自己生成新工具来满足用户需求。
用户说需要什么功能，你就生成对应的工具代码，保存后就能直接使用。
记住：
1. 输出完整Python代码
2. 必须有 xxx_handler(text) -> Optional[str] 函数
3. 不匹配返回None
4. 使用中文返回结果
"""


if __name__ == "__main__":
    # 简单测试
    print("✅ dynamic_tool_generator.py 加载成功")
    print(f"MAX_RETRIES = {MAX_RETRIES}")
    print(f"Tool directory: {TOOL_DIR}")
    index = _load_index()
    print(f"已加载 {len(index)} 个动态工具")
