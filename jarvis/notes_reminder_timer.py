"""
贾维斯语音笔记 + 日程提醒 + 闹钟计时器
存储在本地JSON文件，持久化存储
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# 数据文件路径
NOTES_FILE = "~/YuanFang/data/jarvis_notes.json"
REMINDERS_FILE = "~/YuanFang/data/jarvis_reminders.json"
TIMERS_FILE = "~/YuanFang/data/jarvis_timers.json"

def _ensure_data_dir():
    """确保数据目录存在"""
    import os
    data_dir = os.path.expanduser("~/YuanFang/data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


def _load_json(path: str, default: Any) -> Any:
    """加载JSON文件"""
    _ensure_data_dir()
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def _save_json(path: str, data: Any) -> bool:
    """保存JSON文件"""
    _ensure_data_dir()
    path = os.path.expanduser(path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False


# ============ 语音笔记 ============

def add_note(content: str, tags: List[str] = None) -> Dict:
    """添加一条笔记"""
    notes = _load_json(NOTES_FILE, [])
    note = {
        "id": len(notes) + 1,
        "content": content,
        "tags": tags or [],
        "created_at": datetime.now().isoformat(),
    }
    notes.append(note)
    _save_json(NOTES_FILE, notes)
    return {
        "success": True,
        "message": f"已保存笔记",
        "note_id": note["id"],
        "content": content
    }


def list_notes(limit: int = 10) -> str:
    """列出最近笔记"""
    notes = _load_json(NOTES_FILE, [])
    if not notes:
        return "暂无笔记"
    # 按创建时间倒序
    notes_sorted = sorted(notes, key=lambda x: x["created_at"], reverse=True)
    out = [f"📝 最近 {min(limit, len(notes))} 条笔记:" + "-" * 30 + "\n"]
    for i, n in enumerate(notes_sorted[:limit]):
        dt = datetime.fromisoformat(n["created_at"]).strftime("%m-%d %H:%M")
        content = n["content"]
        if len(content) > 40:
            content = content[:37] + "..."
        out.append(f"[{dt}] #{n['id']} {content}")
    return "\n".join(out)


def search_notes(keyword: str) -> str:
    """搜索笔记"""
    notes = _load_json(NOTES_FILE, [])
    results = []
    for n in notes:
        if keyword.lower() in n["content"].lower():
            results.append(n)
    if not results:
        return f"未找到包含 '{keyword}' 的笔记"
    out = [f"🔍 找到 {len(results)} 条笔记:\n"]
    for n in results:
        dt = datetime.fromisoformat(n["created_at"]).strftime("%m-%d %H:%M")
        out.append(f"- [{dt}] #{n['id']} {n['content']}")
    return "\n".join(out)


# ============ 日程提醒 ============

def add_reminder(content: str, remind_at: datetime) -> Dict:
    """添加日程提醒"""
    reminders = _load_json(REMINDERS_FILE, [])
    reminder = {
        "id": len([r for r in reminders if not r["done"]]) + 1,
        "content": content,
        "created_at": datetime.now().isoformat(),
        "remind_at": remind_at.isoformat(),
        "done": False,
    }
    reminders.append(reminder)
    _save_json(REMINDERS_FILE, reminders)
    return {
        "success": True,
        "message": f"已添加提醒: {content}，时间: {remind_at.strftime('%Y-%m-%d %H:%M')}",
        "reminder_id": reminder["id"],
    }


def get_upcoming_reminders(hours_ahead: int = 48) -> str:
    """获取未来N小时内即将到来的提醒"""
    reminders = _load_json(REMINDERS_FILE, [])
    now = datetime.now()
    cutoff = now + timedelta(hours=hours_ahead)
    upcoming = []
    for r in reminders:
        if r["done"]:
            continue
        remind_at = datetime.fromisoformat(r["remind_at"])
        if now <= remind_at <= cutoff:
            upcoming.append((remind_at, r))
    if not upcoming:
        return f"未来 {hours_ahead} 小时内没有待办提醒"
    upcoming.sort(key=lambda x: x[0])
    out = [f"⏰ 未来 {hours_ahead} 小时内有 {len(upcoming)} 条提醒:\n"]
    for remind_at, r in upcoming:
        time_str = remind_at.strftime("%m-%d %H:%M")
        out.append(f"- {time_str}: {r['content']}")
    return "\n".join(out)


def check_due_reminders() -> List[Dict]:
    """检查哪些提醒已经到期（需要提醒了"""
    reminders = _load_json(REMINDERS_FILE, [])
    now = datetime.now()
    due = []
    for r in reminders:
        if r["done"]:
            continue
        remind_at = datetime.fromisoformat(r["remind_at"])
        if remind_at <= now:
            due.append(r)
    return due


def mark_reminder_done(reminder_id: int) -> bool:
    """标记提醒已完成"""
    reminders = _load_json(REMINDERS_FILE, [])
    for r in reminders:
        if r["id"] == reminder_id:
            r["done"] = True
            _save_json(REMINDERS_FILE, reminders)
            return True
    return False


def list_all_reminders() -> str:
    """列出所有未完成提醒"""
    reminders = _load_json(REMINDERS_FILE, [])
    upcoming = []
    for r in reminders:
        if not r["done"]:
            remind_at = datetime.fromisoformat(r["remind_at"])
            upcoming.append((remind_at, r))
    if not upcoming:
        return "没有未完成的提醒"
    upcoming.sort(key=lambda x: x[0])
    out = [f"📅 所有未完成提醒 ({len(upcoming)} 条):\n"]
    for remind_at, r in upcoming:
        time_str = remind_at.strftime("%Y-%m-%d %H:%M")
        out.append(f"- [{time_str}] {r['content']}")
    return "\n".join(out)


# ============ 闹钟/计时器 ============

def add_timer(duration_minutes: int, content: str = "") -> Dict:
    """添加一个计时器（多少分钟后提醒"""
    timers = _load_json(TIMERS_FILE, [])
    start_at = datetime.now()
    end_at = start_at + timedelta(minutes=duration_minutes)
    timer = {
        "id": len(timers) + 1,
        "content": content or f"{duration_minutes}分钟计时器",
        "duration_minutes": duration_minutes,
        "started_at": start_at.isoformat(),
        "end_at": end_at.isoformat(),
        "done": False,
    }
    timers.append(timer)
    _save_json(TIMERS_FILE, timers)
    return {
        "success": True,
        "message": f"已设置{duration_minutes}分钟计时器，{end_at.strftime('%H:%M')}提醒",
        "timer_id": timer["id"],
        "end_at": end_at,
    }


def get_due_timers() -> List[Dict]:
    """检查哪些计时器已经到期"""
    timers = _load_json(TIMERS_FILE, [])
    now = datetime.now()
    due = []
    for t in timers:
        if t["done"]:
            continue
        end_at = datetime.fromisoformat(t["end_at"])
        if end_at <= now:
            due.append(t)
    return due


def mark_timer_done(timer_id: int) -> bool:
    """标记计时器已完成"""
    timers = _load_json(TIMERS_FILE, [])
    for t in timers:
        if t["id"] == timer_id:
            t["done"] = True
            _save_json(TIMERS_FILE, timers)
            return True
    return False


def list_active_timers() -> str:
    """列出所有正在运行的计时器"""
    timers = _load_json(TIMERS_FILE, [])
    active = []
    now = datetime.now()
    for t in timers:
        if not t["done"]:
            end_at = datetime.fromisoformat(t["end_at"])
        if end_at > now:
            remaining = (end_at - now).total_seconds() / 60
            remaining = round(remaining, 1)
            active.append((end_at, t, remaining))
    if not active:
        return "没有正在运行的计时器"
    active.sort(key=lambda x: x[0])
    out = [f"⏱️ 正在运行的计时器 ({len(active)} 个):\n"]
    for end_at, t, remaining in active:
        time_str = end_at.strftime("%H:%M")
        out.append(f"- #{t['id']} {t['content']} — {remaining}分钟剩余，结束于 {time_str}")
    return "\n".join(out)


# ============ 自动建议 ============

def get_auto_suggestions() -> str:
    """
    根据当前时间、天气、日程，自动生成建议
    这个函数被定时心跳调用
    """
    suggestions = []
    now = datetime.now()
    weekday = now.weekday()  # 0=周一, 4=周五, 5=周六, 6=周日
    hour = now.hour
    
    # 时间相关建议
    if 7 <= hour <= 9:
        suggestions.append("早上好！早上好呀，早上好，准备上班/上学，新的一天开始了。")
        # 检查有没有今天的提醒
        reminders = get_upcoming_reminders(24)
        if "没有" not in reminders:
            suggestions.append("\n今天你有这些安排：\n" + reminders)
    
    elif 11 <= hour <= 13:
        suggestions.append("中午了，该吃午饭了，休息一下吧。")
    
    elif 17 <= hour <= 19:
        suggestions.append("下班/下学了，回家路上注意安全。")
    
    elif 21 <= hour <= 23:
        suggestions.append("夜深了，该准备睡觉了，记得给手机充电。")
    
    # 周末
    if weekday >= 5:
        suggestions.append("今天周末，好好休息放松一下吧。")
    
    # 检查天气预报
    try:
        from services.tools import _weather
        # 假设在北京
        weather_str = _weather("北京")
        suggestions.append(f"\n今日天气：{weather_str}")
        if "+" in weather_str:
            try:
                temp = int(weather_str.split("+")[-1].split("°")[0])
                if temp >= 28:
                    suggestions.append("\n今天天气比较热，记得多喝水，开空调。")
                elif temp <= 10:
                    suggestions.append("\n今天天气比较冷，注意多穿衣服。")
            except:
                pass
    except:
        pass
    
    # 检查即将到来的提醒
    upcoming_2h = get_upcoming_reminders(2)
    if "没有" not in upcoming_2h and "未来" not in upcoming_2h:
        suggestions.append("\n⚠️ 未来2小时内你有：\n" + upcoming_2h)
    
    if not suggestions:
        return "一切正常，没有特别建议。"
    
    return "\n".join(suggestions)


# ============ 自然语言解析工具 ============

def parse_natural_datetime(text: str) -> Optional[datetime]:
    """
    从自然语言解析时间，比如：
    - "明天早上8点" → datetime
    - "下午3点提醒我开会" → datetime
    - "半小时后" → datetime
    - "后天" → datetime
    """
    from dateutil import parser
    from dateutil.relativedelta import relativedelta
    now = datetime.now()
    
    # 半小时/一小时后
    if "半小时后" in text or "半小時後" in text:
        return now + timedelta(minutes=30)
    if "一小时后" in text or "一小時後" in text:
        return now + timedelta(hours=1)
    if "一小时" in text:
        return now + timedelta(hours=1)
    if "五分钟后" in text:
        return now + timedelta(minutes=5)
    if "十分钟后" in text:
        return now + timedelta(minutes=10)
    if "十五分钟后" in text:
        return now + timedelta(minutes=15)
    
    # 今天几点
    import re
    match_hm = re.search(r'今天.*?(\d+)[点时](\d+)?分?', text)
    if match_hm:
        h = int(match_hm.group(1))
        m = int(match_hm.group(2)) if match_hm.group(2) else 0
        return datetime(now.year, now.month, now.day, h, m)
    
    match_h = re.search(r'今天.*?(\d+)[点时]', text)
    if match_h:
        h = int(match_h.group(1))
        return datetime(now.year, now.month, now.day, h, 0)
    
    # 明天几点
    match_hm_tomorrow = re.search(r'明天.*?(\d+)[点时](\d+)?分?', text)
    if match_hm_tomorrow:
        h = int(match_hm_tomorrow.group(1))
        m = int(match_hm_tomorrow.group(2)) if match_hm_tomorrow.group(2) else 0
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, h, m)
    
    match_h_tomorrow = re.search(r'明天.*?(\d+)[点时]', text)
    if match_h_tomorrow:
        h = int(match_h_tomorrow.group(1))
        tomorrow = now + timedelta(days=1)
        return datetime(tomorrow.year, tomorrow.month, tomorrow.day, h, 0)
    
    # "上午"/"下午"
    if "上午" in text:
        match_am = re.search(r'上午\s*(\d+)', text)
        if match_am:
            h = int(match_am.group(1))
            if h == 12:
                h = 0
            today = now
            if "明天" in text:
                today = now + timedelta(days=1)
            return datetime(today.year, today.month, today.day, h, 0)
    if "下午" in text:
        match_pm = re.search(r'下午\s*(\d+)', text)
        if match_pm:
            h = int(match_pm.group(1))
        if h != 12:
            h += 12
        today = now
        if "明天" in text:
            today = now + timedelta(days=1)
        return datetime(today.year, today.month, today.day, h, 0)
    
    # 尝试直接解析
    try:
        return parser.parse(text, fuzzy=True)
    except:
        return None
