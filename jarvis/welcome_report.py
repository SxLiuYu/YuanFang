"""
Home Welcome Report — 回家自动欢迎 + 今日环境报告
- 欢迎回家
- 播报今日天气
- 提醒待办事项
- 提醒快递
- 空气质量（如果有传感器）
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# 数据文件
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HOME_REPORT_FILE = os.path.join(DATA_DIR, "home_welcome.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _get_upcoming_reminders():
    """获取最近的提醒"""
    from jarvis.notes_reminder_timer import get_upcoming_reminders
    try:
        return get_upcoming_reminders(24)  # 24小时内
    except:
        return []


def generate_welcome_report() -> str:
    """生成回家欢迎报告"""
    now = datetime.now()
    hour = now.hour
    weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]
    
    # 问候语
    if hour < 12:
        greeting = "早上好"
    elif hour < 18:
        greeting = "下午好"
    else:
        greeting = "晚上好"
    
    parts = [f"欢迎回家！{greeting}，今天是{weekday}，{now.month}月{now.day}日。"]
    parts.append("")
    
    # 获取天气
    try:
        from services.tools import _weather
        weather_result = _weather("北京")
        parts.append("🌤️  今日天气：")
        parts.append(weather_result)
        parts.append("")
    except Exception as e:
        pass
    
    # 提醒事项
    try:
        from jarvis.notes_reminder_timer import get_upcoming_reminders
        reminders_text = get_upcoming_reminders(24)  # 24小时内
        if "没有即将到来" not in reminders_text:
            parts.append("📝 你有这些待办提醒：")
            parts.append(reminders_text)
            parts.append("")
    except Exception as e:
        pass
    
    # 购物清单提醒
    from jarvis.quick_tools import list_shopping_items
    shopping = list_shopping_items()
    if "购物清单是空的" not in shopping:
        parts.append("🛒 购物清单：")
        lines = shopping.split("\n")
        for line in lines:
            if line.strip():
                parts.append(line)
        parts.append("")
    
    # TODO: 传感器数据（温度湿度/空气质量）会从 /api/sensors 获取
    
    # 如果没有其他内容，就是简单欢迎
    if len(parts) == 2:
        return parts[0] + "祝你一天愉快！"
    
    return "\n".join(parts)


def welcome_home_handler(text: str) -> Optional[str]:
    """
    回家欢迎意图处理
    """
    text = text.lower().strip()
    
    greetings = [
        "我回来了", "我到家了", "欢迎回家", "开门", "回家"
    ]
    
    if any(greet in text for greet in greetings) or len(text) <= 4 and text == "回家":
        return generate_welcome_report()
    
    return None