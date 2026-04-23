"""
Health Reminder — 喝水提醒、站立活动提醒
定时提醒用户喝水、起身活动，保护颈椎和腰椎
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 数据文件存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
HEALTH_REMINDER_FILE = os.path.join(DATA_DIR, "health_reminder.json")


def _ensure_data_dir():
    """确保数据目录存在"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_json(file_path: str, default: dict) -> dict:
    """加载JSON文件"""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(file_path: str, data: dict) -> bool:
    """保存JSON文件"""
    _ensure_data_dir()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


# ============ 默认配置 ============

DEFAULT_CONFIG = {
    "water_reminder_enabled": True,
    "water_interval_minutes": 60,  # 每60分钟提醒喝水
    "last_water_reminder": None,   # 上次提醒时间
    "stand_reminder_enabled": True,
    "stand_interval_minutes": 45,  # 每45分钟提醒站立
    "last_stand_reminder": None,   # 上次提醒时间
    "start_time": "09:00",         # 开始提醒时间
    "end_time": "22:00",           # 结束提醒时间
}


def _get_config() -> dict:
    """获取配置"""
    data = _load_json(HEALTH_REMINDER_FILE, DEFAULT_CONFIG)
    # 补全缺失字段
    for k, v in DEFAULT_CONFIG.items():
        if k not in data:
            data[k] = v
    return data


def _is_in_remind_window() -> bool:
    """判断当前是否在提醒时间窗口"""
    now = datetime.now()
    config = _get_config()
    
    # 解析开始结束时间
    start_h, start_m = map(int, config["start_time"].split(":"))
    end_h, end_m = map(int, config["end_time"].split(":"))
    
    start_dt = now.replace(hour=start_h, minute=start_m, second=0)
    end_dt = now.replace(hour=end_h, minute=end_m, second=0)
    
    return start_dt <= now <= end_dt


def should_remind_water() -> Optional[str]:
    """判断是否需要提醒喝水，如果需要返回提醒文案"""
    config = _get_config()
    
    if not config["water_reminder_enabled"]:
        return None
    
    if not _is_in_remind_window():
        return None
    
    last_remind = config.get("last_water_reminder")
    if last_remind is None:
        # 第一次启动，记录时间不提醒
        _record_water_reminder()
        return None
    
    # 计算间隔
    last_dt = datetime.fromisoformat(last_remind)
    now = datetime.now()
    interval = timedelta(minutes=config["water_interval_minutes"])
    
    if now - last_dt >= interval:
        _record_water_reminder()
        return "该喝水啦！站起来喝杯水，活动一下身体吧~"
    
    return None


def should_remind_stand() -> Optional[str]:
    """判断是否需要提醒站立，如果需要返回提醒文案"""
    config = _get_config()
    
    if not config["stand_reminder_enabled"]:
        return None
    
    if not _is_in_remind_window():
        return None
    
    last_remind = config.get("last_stand_reminder")
    if last_remind is None:
        # 第一次启动，记录时间不提醒
        _record_stand_reminder()
        return None
    
    # 计算间隔
    last_dt = datetime.fromisoformat(last_remind)
    now = datetime.now()
    interval = timedelta(minutes=config["stand_interval_minutes"])
    
    if now - last_dt >= interval:
        _record_stand_reminder()
        return "已经坐了很久了，站起来走走，活动一下颈椎和腰椎吧~"
    
    return None


def _record_water_reminder():
    """记录喝水提醒时间"""
    config = _get_config()
    config["last_water_reminder"] = datetime.now().isoformat()
    _save_json(HEALTH_REMINDER_FILE, config)


def _record_stand_reminder():
    """记录站立提醒时间"""
    config = _get_config()
    config["last_stand_reminder"] = datetime.now().isoformat()
    _save_json(HEALTH_REMINDER_FILE, config)


# ============ 控制接口 ============

def enable_water_reminder(enabled: bool = True) -> str:
    """启用/禁用喝水提醒"""
    config = _get_config()
    config["water_reminder_enabled"] = enabled
    _save_json(HEALTH_REMINDER_FILE, config)
    return f"喝水提醒已{'开启' if enabled else '关闭'}"


def enable_stand_reminder(enabled: bool = True) -> str:
    """启用/禁用站立提醒"""
    config = _get_config()
    config["stand_reminder_enabled"] = enabled
    _save_json(HEALTH_REMINDER_FILE, config)
    return f"站立提醒已{'开启' if enabled else '关闭'}"


def set_water_interval(minutes: int) -> str:
    """设置喝水提醒间隔"""
    if minutes < 15:
        return "间隔太短了哦，建议至少15分钟"
    if minutes > 180:
        return "间隔太长了，对身体不好哦"
    config = _get_config()
    config["water_interval_minutes"] = minutes
    _save_json(HEALTH_REMINDER_FILE, config)
    return f"喝水提醒间隔已设置为 {minutes} 分钟"


def set_stand_interval(minutes: int) -> str:
    """设置站立提醒间隔"""
    if minutes < 20:
        return "间隔太短了哦"
    if minutes > 120:
        return "间隔太长了，坐太久对腰椎不好哦"
    config = _get_config()
    config["stand_interval_minutes"] = minutes
    _save_json(HEALTH_REMINDER_FILE, config)
    return f"站立提醒间隔已设置为 {minutes} 分钟"


def set_remind_time(start_time: str, end_time: str) -> str:
    """设置提醒时间段"""
    # 简单验证格式
    try:
        sh, sm = map(int, start_time.split(":"))
        eh, em = map(int, end_time.split(":"))
        if not (0 <= sh < 24 and 0 <= sm < 60 and 0 <= eh < 24 and 0 <= em < 60):
            raise ValueError
    except:
        return "时间格式不对，请用 HH:MM 格式，比如 09:00 22:00"
    
    config = _get_config()
    config["start_time"] = start_time
    config["end_time"] = end_time
    _save_json(HEALTH_REMINDER_FILE, config)
    return f"提醒时间段已设置为 {start_time} - {end_time}"


def get_status() -> str:
    """获取当前状态"""
    config = _get_config()
    now = datetime.now()
    
    def format_last(name, last_key):
        last = config.get(last_key)
        if last is None:
            return f"{name}: 尚未提醒"
        dt = datetime.fromisoformat(last)
        diff = now - dt
        mins = int(diff.total_seconds() / 60)
        return f"{name}: {mins}分钟前"
    
    water_status = f"✅ 开启" if config["water_reminder_enabled"] else "❌ 关闭"
    stand_status = f"✅ 开启" if config["stand_reminder_enabled"] else "❌ 关闭"
    
    lines = [
        f"健康提醒状态:",
        f"喝水提醒: {water_status}, 间隔 {config['water_interval_minutes']} 分钟",
        format_last("上次喝水提醒", "last_water_reminder"),
        f"站立提醒: {stand_status}, 间隔 {config['stand_interval_minutes']} 分钟",
        format_last("上次站立提醒", "last_stand_reminder"),
        f"提醒时间段: {config['start_time']} - {config['end_time']}",
    ]
    return "\n".join(lines)


# ============ 意图匹配封装 ============

def health_reminder_handler(text: str) -> Optional[str]:
    """
    健康提醒意图处理，匹配成功返回响应，失败返回None
    """
    text = text.lower().strip()
    
    # 喝水提醒控制
    if "喝水" in text and ("提醒" in text or "打开" in text or "开启" in text or "关" in text):
        if "关" in text or "停止" in text:
            return enable_water_reminder(False)
        else:
            return enable_water_reminder(True)
    
    # 站立提醒控制
    if ("站立" in text or "起身" in text or "活动" in text) and ("提醒" in text or "打开" in text or "开启" in text or "关" in text):
        if "关" in text or "停止" in text:
            return enable_stand_reminder(False)
        else:
            return enable_stand_reminder(True)
    
    # 设置喝水间隔
    if "喝水" in text and ("间隔" in text or "分钟" in text):
        import re
        match = re.search(r'(\d+)\s*分', text)
        if match:
            minutes = int(match.group(1))
            return set_water_interval(minutes)
    
    # 设置站立间隔
    if ("站立" in text or "起身" in text) and ("间隔" in text or "分钟" in text):
        import re
        match = re.search(r'(\d+)\s*分', text)
        if match:
            minutes = int(match.group(1))
            return set_stand_interval(minutes)
    
    # 设置时间段
    if ("开始" in text and "结束" in text) or ("从" in text and "到" in text):
        import re
        match = re.search(r'(\d\d?:\d\d).*(\d\d?:\d\d)', text)
        if match:
            start = match.group(1)
            end = match.group(2)
            return set_remind_time(start, end)
    
    # 查看状态
    if "状态" in text or ("怎么样" in text) or ("看看" in text and "提醒" in text):
        return get_status()
    
    # 手动触发提醒（检测到喝水了，更新记录）
    if ("喝了" in text and "水" in text) or ("喝完水" in text):
        _record_water_reminder()
        config = _get_config()
        return "好的，已记录，下次提醒会在 {} 分钟后".format(config["water_interval_minutes"])
    
    # 手动触发提醒（站立过了，更新记录）
    if ("站起来了" in text) or ("活动完了" in text):
        _record_stand_reminder()
        config = _get_config()
        return "好的，已记录，下次提醒会在 {} 分钟后".format(config["stand_interval_minutes"])
    
    return None