"""
Birthday Reminder — 生日纪念日提醒
存储重要生日，到期自动提醒
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# 数据文件
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
BIRTHDAY_FILE = os.path.join(DATA_DIR, "birthdays.json")


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def _load_birthdays() -> dict:
    return _load_json(BIRTHDAY_FILE, {"birthdays": []})


def _load_json(file_path: str, default: dict) -> dict:
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(file_path: str, data: dict) -> bool:
    _ensure_data_dir()
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False


def add_birthday(name: str, month: int, day: int, year: Optional[int] = None) -> str:
    """添加生日"""
    data = _load_birthdays()
    # 检查是否已存在
    for b in data["birthdays"]:
        if b["name"] == name:
            return f"{name} 的生日已经记录过了"
    
    birthday = {
        "name": name,
        "month": month,
        "day": day,
        "year": year,
        "created_at": datetime.now().isoformat()
    }
    data["birthdays"].append(birthday)
    _save_json(BIRTHDAY_FILE, data)
    
    if year:
        return f"已记录 {name} 的生日：{month}月{day}日 ({year}年)"
    else:
        return f"已记录 {name} 的生日：{month}月{day}日"


def delete_birthday(name: str) -> str:
    """删除生日"""
    data = _load_birthdays()
    original_len = len(data["birthdays"])
    data["birthdays"] = [b for b in data["birthdays"] if b["name"] != name]
    
    if len(data["birthdays"]) < original_len:
        _save_json(BIRTHDAY_FILE, data)
        return f"已删除 {name} 的生日记录"
    else:
        return f"没有找到 {name} 的生日记录"


def list_birthdays() -> str:
    """列出所有生日"""
    data = _load_birthdays()
    birthdays = data["birthdays"]
    
    if not birthdays:
        return "还没有记录任何生日"
    
    # 按月份排序
    birthdays.sort(key=lambda x: (x["month"], x["day"]))
    
    lines = ["已记录生日："]
    for b in birthdays:
        name = b["name"]
        month = b["month"]
        day = b["day"]
        year = b.get("year")
        if year:
            lines.append(f"- {name}: {month}月{day}日 ({year}年)")
        else:
            lines.append(f"- {name}: {month}月{day}日")
    
    return "\n".join(lines)


def get_upcoming_birthdays(days_ahead: int = 30) -> str:
    """获取最近days_ahead天内即将到来的生日"""
    data = _load_birthdays()
    birthdays = data["birthdays"]
    
    if not birthdays:
        return None
    
    today = datetime.now()
    upcoming = []
    
    for b in birthdays:
        # 今年的生日日期
        b_month = b["month"]
        b_day = b["day"]
        
        # 计算今年生日和距离今天多少天
        try:
            b_this_year = today.replace(month=b_month, day=b_day)
        except ValueError:
            continue  # 2月29日忽略
        
        days_diff = (b_this_year - today).days
        if 0 <= days_diff <= days_ahead:
            upcoming.append({
                "name": b["name"],
                "days": days_diff,
                "date": f"{b_month}月{b_day}日"
            })
        
        # 如果今年已经过了，看明年
        if days_diff < 0:
            # 明年
            next_year = today.year + 1
            try:
                b_next_year = datetime(next_year, b_month, b_day)
                days_diff = (b_next_year - today).days
                if 0 <= days_diff <= days_ahead:
                    upcoming.append({
                        "name": b["name"],
                        "days": days_diff,
                        "date": f"{b_month}月{b_day}日 ({next_year}年)"
                    })
            except:
                continue
    
    if not upcoming:
        return None
    
    # 按天数排序
    upcoming.sort(key=lambda x: x["days"])
    
    lines = [f"📅 未来 {days_ahead} 天内有 {len(upcoming)} 个生日："]
    for u in upcoming:
        if u["days"] == 0:
            lines.append(f"- 今天就是 {u['name']} 的生日 ({u['date']})！")
        elif u["days"] == 1:
            lines.append(f"- 明天：{u['name']} 的生日 ({u['date']})")
        else:
            lines.append(f"- {u['days']} 天后：{u['name']} 的生日 ({u['date']})")
    
    return "\n".join(lines)


def add_anniversary(name: str, month: int, day: int, year: int) -> str:
    """添加周年纪念日"""
    data = _load_birthdays()
    # 检查是否已存在
    for b in data["birthdays"]:
        if b["name"] == name:
            return f"{name} 的纪念日已经记录过了"
    
    anniversary = {
        "name": name,
        "month": month,
        "day": day,
        "year": year,
        "type": "anniversary",
        "created_at": datetime.now().isoformat()
    }
    data["birthdays"].append(anniversary)
    _save_json(BIRTHDAY_FILE, data)
    
    return f"已记录 {name} 纪念日：{month}月{day}日 ({year}年开始)"


def birthday_reminder_handler(text: str) -> Optional[str]:
    """生日纪念日意图处理"""
    text = text.lower().strip()
    
    # 添加生日
    if "生日" in text and ("记" in text or "添加" in text):
        # "记住张三的生日是5月12日"
        # 提取月日
        import re
        # 匹配 "X月X日"
        match = re.search(r'(\d+)月(\d+)(?:日)?', text)
        if not match:
            return None
        
        month = int(match.group(1))
        day = int(match.group(2))
        
        # 提取名字："X的生日" → X
        name_match = re.search(r'(.+?)的生日', text)
        if name_match:
            name = name_match.group(1).strip()
            name = name.replace("记住", "").replace("记", "").replace("添加", "").strip()
        else:
            #  fallback
            name = text
            for kw in ["记住", "记", "添加", "生日", "的", "是", "我", "的", "在", "。", ",", f"{month}月{day}日"]:
                name = name.replace(kw, "")
            name = name.strip()
        if not name:
            name = "我的"
        
        # 找年份
        year_match = re.search(r'(19|20)(\d\d)', text)
        year = int(year_match.group(0)) if year_match else None
        
        return add_birthday(name, month, day, year)
    
    # 添加纪念日
    if "纪念日" in text and ("记" in text or "添加" in text):
        import re
        match = re.search(r'(\d+)月(\d+)(?:日)?', text)
        if not match:
            return None
        
        month = int(match.group(1))
        day = int(match.group(2))
        
        year_match = re.search(r'(19|20)(\d\d)', text)
        if not year_match:
            return "请告诉我是哪一年开始的纪念日"
        year = int(year_match.group(0))
        
        # 提取名字："X的纪念日" → X
        name_match = re.search(r'(.+?)的纪念日', text)
        if name_match:
            name = name_match.group(1).strip()
            name = name.replace("记住", "").replace("记", "").replace("添加", "").strip()
        else:
            #  fallback
            name = text
            for kw in ["记住", "记", "添加", "纪念日", "的", "是", "我", "的", "在", "。", ",", f"{month}月{day}日", f"{year}年"]:
                name = name.replace(kw, "")
            name = name.strip()
        
        if not name:
            name = "结婚纪念日"
        
        return add_anniversary(name, month, day, year)
    
    # 删除
    if ("删除" in text or "去掉" in text) and "生日" in text:
        name = text.replace("删除", "").replace("去掉", "").replace("生日", "").strip()
        if name:
            return delete_birthday(name)
    
    # 列出所有
    if ("列出" in text or "看" in text or "有哪些") and "生日" in text:
        return list_birthdays()
    
    # 最近提醒
    if ("即将" in text or "最近" in text) and "生日" in text:
        result = get_upcoming_birthdays(30)
        return result if result else "最近30天没有生日"
    
    return None