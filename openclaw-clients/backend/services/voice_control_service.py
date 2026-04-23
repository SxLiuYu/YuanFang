#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音控制服务 - 完整语音交互系统
支持唤醒词检测、连续语音识别、指令执行、语音反馈、多轮对话

Author: OpenClaw Team
Version: 1.0.0
"""

import os
import re
import json
import uuid
import logging
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from collections import deque

from .db_helper import DatabaseHelper

logger = logging.getLogger(__name__)


class SessionState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    RESPONDING = "responding"
    WAITING_CONFIRM = "waiting_confirm"


class CommandType(Enum):
    SYSTEM_CONTROL = "system_control"
    INFO_QUERY = "info_query"
    ACCOUNTING = "accounting"
    REMINDER = "reminder"
    SCHEDULE = "schedule"
    WEATHER = "weather"
    UNKNOWN = "unknown"


@dataclass
class VoiceSession:
    session_id: str
    state: SessionState = SessionState.IDLE
    wake_word: Optional[str] = None
    command_history: List[Dict[str, Any]] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "wake_word": self.wake_word,
            "turn_count": self.turn_count,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat()
        }


@dataclass
class VoiceCommand:
    text: str
    command_type: CommandType
    intent: str
    slots: Dict[str, Any]
    confidence: float
    raw_text: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "command_type": self.command_type.value,
            "intent": self.intent,
            "slots": self.slots,
            "confidence": self.confidence,
            "raw_text": self.raw_text,
            "timestamp": self.timestamp.isoformat()
        }


class WakeWordDetector:
    """唤醒词检测器"""
    
    DEFAULT_WAKE_WORDS = {
        "小助手": {"aliases": ["小助手", "助手", "小帮手"], "sensitivity": 0.8},
        "你好小助手": {"aliases": ["你好小助手", "嗨小助手", "小助手你好"], "sensitivity": 0.9},
        "嘿助手": {"aliases": ["嘿助手", "嘿小助手"], "sensitivity": 0.7}
    }
    
    def __init__(self, wake_words: Dict[str, Dict] = None):
        self.wake_words = wake_words or self.DEFAULT_WAKE_WORDS.copy()
        self._build_patterns()
    
    def _build_patterns(self):
        self.patterns = {}
        for wake_word, config in self.wake_words.items():
            aliases = config.get("aliases", [wake_word])
            pattern = "|".join(re.escape(alias) for alias in aliases)
            self.patterns[wake_word] = {
                "pattern": re.compile(f"^({pattern})[，,。.!！?？]?\\s*", re.IGNORECASE),
                "sensitivity": config.get("sensitivity", 0.8)
            }
    
    def detect(self, text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        
        text = text.strip()
        for wake_word, config in self.patterns.items():
            match = config["pattern"].match(text)
            if match:
                remaining = text[match.end():].strip()
                return {
                    "detected": True,
                    "wake_word": wake_word,
                    "confidence": config["sensitivity"],
                    "remaining_text": remaining,
                    "matched_text": match.group(1)
                }
        
        return None
    
    def add_wake_word(self, wake_word: str, aliases: List[str] = None, sensitivity: float = 0.8):
        self.wake_words[wake_word] = {
            "aliases": aliases or [wake_word],
            "sensitivity": sensitivity
        }
        self._build_patterns()
    
    def remove_wake_word(self, wake_word: str):
        if wake_word in self.wake_words:
            del self.wake_words[wake_word]
            self._build_patterns()


class CommandParser:
    """语音指令解析器"""
    
    COMMAND_PATTERNS = {
        CommandType.SYSTEM_CONTROL: {
            "patterns": [
                (r"^(打开|开启|启动)(.{1,10})(灯|空调|电视|音响|窗帘|风扇|加湿器|净化器)", ["device", "action"]),
                (r"^(关闭|关掉|停止)(.{1,10})(灯|空调|电视|音响|窗帘|风扇|加湿器|净化器)", ["device", "action"]),
                (r"^(调高|调低)(.{1,10})(温度|亮度|音量)", ["device", "action"]),
                (r"^(把|将)(.{1,10})(温度|亮度|音量)调到(\d+)", ["device", "value"]),
            ],
            "keywords": ["打开", "关闭", "开启", "关掉", "调高", "调低", "启动", "停止"]
        },
        CommandType.INFO_QUERY: {
            "patterns": [
                (r"(今天|昨天|本周|本月).*(花了多少|消费|支出)", ["time_range", "query_type"]),
                (r"(查一下|查询).*(余额|账单|消费)", ["query_type"]),
            ],
            "keywords": ["花了多少", "消费", "支出", "查询", "余额", "账单"]
        },
        CommandType.ACCOUNTING: {
            "patterns": [
                (r"记一笔(\d+(?:\.\d{1,2})?)块?(.{2,10})", ["amount", "category"]),
                (r"(花了|消费|支出)(\d+(?:\.\d{1,2})?)块?(.{2,10})?", ["action", "amount", "category"]),
                (r"(工资|奖金|收入|到账)(\d+(?:\.\d{1,2})?)", ["category", "amount"]),
            ],
            "keywords": ["记一笔", "记账", "花了", "消费", "支出", "收入", "工资", "到账"]
        },
        CommandType.REMINDER: {
            "patterns": [
                (r"提醒我(\d{1,2})点(\d{1,2})?分?(.+)", ["hour", "minute", "content"]),
                (r"(\d+)分钟后?提醒我(.+)", ["minutes", "content"]),
                (r"提醒我(.+)", ["content"]),
            ],
            "keywords": ["提醒我", "提醒", "叫我", "别忘了"]
        },
        CommandType.SCHEDULE: {
            "patterns": [
                (r"(今天|明天|后天).*(有什么|有啥)(安排|日程|计划)", ["date", "query_type"]),
                (r"查询(今天|明天|后天).*(日程|安排)", ["date"]),
            ],
            "keywords": ["安排", "日程", "计划", "有什么安排"]
        },
        CommandType.WEATHER: {
            "patterns": [
                (r"(今天|明天|后天)(.{2,10})?天气", ["date", "location"]),
                (r"(.{2,10})天气(怎么样|如何)", ["location"]),
            ],
            "keywords": ["天气", "气温", "温度", "下雨", "晴天"]
        }
    }
    
    DEVICE_MAP = {
        "灯": {"type": "light", "room": None},
        "客厅灯": {"type": "light", "room": "living_room"},
        "卧室灯": {"type": "light", "room": "bedroom"},
        "空调": {"type": "air_conditioner", "room": None},
        "电视": {"type": "tv", "room": None},
        "音响": {"type": "speaker", "room": None},
        "窗帘": {"type": "curtain", "room": None},
        "风扇": {"type": "fan", "room": None},
        "加湿器": {"type": "humidifier", "room": None},
        "净化器": {"type": "purifier", "room": None},
    }
    
    ACTION_MAP = {
        "打开": "on", "开启": "on", "启动": "on",
        "关闭": "off", "关掉": "off", "停止": "off",
        "调高": "increase", "调低": "decrease",
    }
    
    TIME_KEYWORDS = {
        "今天": 0, "今日": 0,
        "昨天": -1, "昨日": -1,
        "明天": 1, "明日": 1,
        "后天": 2,
        "本周": "week",
        "本月": "month",
    }
    
    CATEGORY_KEYWORDS = {
        "餐饮": ["午饭", "午餐", "早餐", "晚饭", "晚餐", "吃饭", "外卖", "餐", "饭", "奶茶", "咖啡", "饮料", "零食"],
        "交通": ["打车", "滴滴", "地铁", "公交", "加油", "停车", "出行"],
        "购物": ["买了", "买", "购物", "淘宝", "京东", "超市"],
        "娱乐": ["电影", "游戏", "KTV", "健身"],
        "医疗": ["医院", "看病", "买药", "药"],
        "收入": ["工资", "奖金", "红包", "收入"],
    }
    
    def __init__(self):
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.compiled_patterns = {}
        for cmd_type, config in self.COMMAND_PATTERNS.items():
            self.compiled_patterns[cmd_type] = [
                (re.compile(p), slots) for p, slots in config["patterns"]
            ]
    
    def parse(self, text: str) -> VoiceCommand:
        if not text or not text.strip():
            return VoiceCommand(
                text=text or "",
                command_type=CommandType.UNKNOWN,
                intent="unknown",
                slots={},
                confidence=0.0,
                raw_text=text or ""
            )
        
        text = text.strip()
        cmd_type = self._detect_command_type(text)
        slots = self._extract_slots(text, cmd_type)
        intent = self._determine_intent(cmd_type, slots)
        confidence = self._calculate_confidence(text, cmd_type, slots)
        
        return VoiceCommand(
            text=text,
            command_type=cmd_type,
            intent=intent,
            slots=slots,
            confidence=confidence,
            raw_text=text
        )
    
    def _detect_command_type(self, text: str) -> CommandType:
        scores = {}
        
        for cmd_type, config in self.COMMAND_PATTERNS.items():
            score = 0
            for keyword in config["keywords"]:
                if keyword in text:
                    score += 1
            scores[cmd_type] = score
        
        if not scores or max(scores.values()) == 0:
            return CommandType.UNKNOWN
        
        return max(scores, key=scores.get)
    
    def _extract_slots(self, text: str, cmd_type: CommandType) -> Dict[str, Any]:
        slots = {}
        
        if cmd_type == CommandType.SYSTEM_CONTROL:
            slots = self._extract_control_slots(text)
        elif cmd_type == CommandType.ACCOUNTING:
            slots = self._extract_accounting_slots(text)
        elif cmd_type == CommandType.REMINDER:
            slots = self._extract_reminder_slots(text)
        elif cmd_type == CommandType.SCHEDULE:
            slots = self._extract_schedule_slots(text)
        elif cmd_type == CommandType.WEATHER:
            slots = self._extract_weather_slots(text)
        elif cmd_type == CommandType.INFO_QUERY:
            slots = self._extract_query_slots(text)
        
        return slots
    
    def _extract_control_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        for device_name, device_info in self.DEVICE_MAP.items():
            if device_name in text:
                slots["device"] = device_info["type"]
                slots["device_name"] = device_name
                if device_info["room"]:
                    slots["room"] = device_info["room"]
                break
        
        for action_text, action_value in self.ACTION_MAP.items():
            if action_text in text:
                slots["action"] = action_value
                break
        
        value_match = re.search(r"调到(\d+)", text)
        if value_match:
            slots["value"] = int(value_match.group(1))
        
        return slots
    
    def _extract_accounting_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        amount_match = re.search(r"(\d+(?:\.\d{1,2})?)", text)
        if amount_match:
            slots["amount"] = float(amount_match.group(1))
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    slots["category"] = category
                    break
            if "category" in slots:
                break
        
        if any(kw in text for kw in ["工资", "奖金", "收入", "到账"]):
            slots["transaction_type"] = "income"
        else:
            slots["transaction_type"] = "expense"
        
        slots["description"] = re.sub(r"[\d.]+\s*(块|元|块钱)?", "", text).strip()
        
        return slots
    
    def _extract_reminder_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        hour_match = re.search(r"(\d{1,2})点(\d{1,2})?分?", text)
        if hour_match:
            slots["hour"] = int(hour_match.group(1))
            slots["minute"] = int(hour_match.group(2)) if hour_match.group(2) else 0
            slots["time_type"] = "absolute"
        
        minutes_match = re.search(r"(\d+)分钟", text)
        if minutes_match:
            slots["minutes_later"] = int(minutes_match.group(1))
            slots["time_type"] = "relative"
        
        content_match = re.search(r"提醒我(.+)", text)
        if content_match:
            content = content_match.group(1)
            content = re.sub(r"\d+点\d*分?", "", content).strip()
            content = re.sub(r"\d+分钟后?", "", content).strip()
            if content:
                slots["content"] = content
        
        if "每天" in text:
            slots["repeat"] = "daily"
        elif "每周" in text:
            slots["repeat"] = "weekly"
        
        return slots
    
    def _extract_schedule_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text:
                if isinstance(offset, int):
                    target_date = datetime.now() + timedelta(days=offset)
                    slots["date"] = target_date.strftime("%Y-%m-%d")
                else:
                    slots["date_range"] = offset
                break
        
        slots["query_type"] = "list"
        
        return slots
    
    def _extract_weather_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text and isinstance(offset, int):
                target_date = datetime.now() + timedelta(days=offset)
                slots["date"] = target_date.strftime("%Y-%m-%d")
                break
        
        city_pattern = r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆)"
        city_match = re.search(city_pattern, text)
        if city_match:
            slots["location"] = city_match.group(1)
        
        return slots
    
    def _extract_query_slots(self, text: str) -> Dict[str, Any]:
        slots = {}
        
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text:
                slots["time_range"] = str(offset)
                break
        
        if "花了多少" in text or "消费" in text or "支出" in text:
            slots["query_type"] = "expense"
        elif "余额" in text:
            slots["query_type"] = "balance"
        elif "账单" in text:
            slots["query_type"] = "bill"
        else:
            slots["query_type"] = "summary"
        
        return slots
    
    def _determine_intent(self, cmd_type: CommandType, slots: Dict[str, Any]) -> str:
        if cmd_type == CommandType.SYSTEM_CONTROL:
            action = slots.get("action", "unknown")
            device = slots.get("device", "unknown")
            return f"{action}_{device}"
        elif cmd_type == CommandType.ACCOUNTING:
            return "add_transaction"
        elif cmd_type == CommandType.REMINDER:
            return "create_reminder"
        elif cmd_type == CommandType.SCHEDULE:
            return "query_schedule"
        elif cmd_type == CommandType.WEATHER:
            return "query_weather"
        elif cmd_type == CommandType.INFO_QUERY:
            return slots.get("query_type", "query")
        return "unknown"
    
    def _calculate_confidence(self, text: str, cmd_type: CommandType, slots: Dict[str, Any]) -> float:
        if cmd_type == CommandType.UNKNOWN:
            return 0.0
        
        base_confidence = 0.5
        keyword_bonus = 0.1 * len([k for k in self.COMMAND_PATTERNS.get(cmd_type, {}).get("keywords", []) if k in text])
        slot_bonus = 0.1 * len(slots)
        
        return min(base_confidence + keyword_bonus + slot_bonus, 1.0)


class CommandExecutor:
    """指令执行器"""
    
    def __init__(self, db: DatabaseHelper):
        self.db = db
        self.handlers: Dict[str, Callable[..., Awaitable[Dict[str, Any]]]] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        self.handlers = {
            "on_light": self._handle_light_control,
            "off_light": self._handle_light_control,
            "on_air_conditioner": self._handle_ac_control,
            "off_air_conditioner": self._handle_ac_control,
            "add_transaction": self._handle_accounting,
            "create_reminder": self._handle_reminder,
            "query_schedule": self._handle_schedule_query,
            "query_weather": self._handle_weather_query,
            "expense": self._handle_expense_query,
            "balance": self._handle_balance_query,
        }
    
    async def execute(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        intent = command.intent
        handler = self.handlers.get(intent, self._handle_unknown)
        
        try:
            result = await handler(command, session)
            result["intent"] = intent
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return {
                "success": False,
                "intent": intent,
                "error": str(e),
                "message": "执行指令时发生错误"
            }
    
    async def _handle_light_control(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        action = slots.get("action", "on")
        device_name = slots.get("device_name", "灯")
        room = slots.get("room", "")
        
        action_text = "打开" if action == "on" else "关闭"
        room_text = f"{room}" if room else ""
        
        return {
            "message": f"已{action_text}{room_text}{device_name}",
            "device": device_name,
            "action": action,
            "executed": True
        }
    
    async def _handle_ac_control(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        action = slots.get("action", "on")
        value = slots.get("value")
        
        action_text = "打开" if action == "on" else "关闭"
        
        message = f"已{action_text}空调"
        if value:
            message += f"，温度设置为{value}度"
        
        return {
            "message": message,
            "device": "空调",
            "action": action,
            "value": value,
            "executed": True
        }
    
    async def _handle_accounting(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        amount = slots.get("amount", 0)
        category = slots.get("category", "其他")
        transaction_type = slots.get("transaction_type", "expense")
        description = slots.get("description", "")
        
        record_data = {
            "amount": amount,
            "category": category,
            "type": transaction_type,
            "description": description,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "created_at": datetime.now().isoformat()
        }
        
        try:
            record_id = self.db.insert("transactions", record_data)
            type_text = "收入" if transaction_type == "income" else "支出"
            return {
                "message": f"已记录{type_text}：{amount}元，分类：{category}",
                "record_id": record_id,
                "amount": amount,
                "category": category,
                "executed": True
            }
        except Exception as e:
            return {
                "message": f"记账失败：{str(e)}",
                "executed": False
            }
    
    async def _handle_reminder(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        content = slots.get("content", "提醒")
        time_type = slots.get("time_type", "relative")
        
        reminder_data = {
            "content": content,
            "time_type": time_type,
            "hour": slots.get("hour"),
            "minute": slots.get("minute", 0),
            "minutes_later": slots.get("minutes_later"),
            "repeat": slots.get("repeat"),
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        try:
            reminder_id = self.db.insert("reminders", reminder_data)
            
            if time_type == "absolute":
                time_str = f"{slots.get('hour')}点{slots.get('minute', 0)}分"
            else:
                time_str = f"{slots.get('minutes_later', 10)}分钟后"
            
            return {
                "message": f"已设置提醒：{time_str}{content}",
                "reminder_id": reminder_id,
                "content": content,
                "executed": True
            }
        except Exception as e:
            return {
                "message": f"设置提醒失败：{str(e)}",
                "executed": False
            }
    
    async def _handle_schedule_query(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        date = slots.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        events = self.db.fetch_all(
            "SELECT * FROM calendar_events WHERE date(start_time) = ? ORDER BY start_time",
            (date,)
        )
        
        if events:
            event_list = [f"{e.get('title', '未命名事件')}" for e in events]
            message = f"当天有{len(events)}个安排：" + "、".join(event_list[:5])
        else:
            message = "当天没有安排"
        
        return {
            "message": message,
            "date": date,
            "events": events,
            "executed": True
        }
    
    async def _handle_weather_query(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        date = slots.get("date", "今天")
        location = slots.get("location", "北京")
        
        weather_data = {
            "location": location,
            "date": date,
            "temperature": "22-28",
            "condition": "晴转多云",
            "humidity": "65%",
            "wind": "东南风3级"
        }
        
        return {
            "message": f"{location}{date}天气：{weather_data['condition']}，气温{weather_data['temperature']}度",
            "weather": weather_data,
            "executed": True
        }
    
    async def _handle_expense_query(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        slots = command.slots
        time_range = slots.get("time_range", "0")
        
        try:
            offset = int(time_range)
            target_date = datetime.now() + timedelta(days=offset)
            date_str = target_date.strftime("%Y-%m-%d")
        except:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        total = self.db.fetch_value(
            "SELECT SUM(amount) FROM transactions WHERE type = 'expense' AND date = ?",
            (date_str,)
        ) or 0
        
        return {
            "message": f"当天共消费{total}元",
            "date": date_str,
            "total": total,
            "executed": True
        }
    
    async def _handle_balance_query(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        income = self.db.fetch_value(
            "SELECT SUM(amount) FROM transactions WHERE type = 'income'"
        ) or 0
        
        expense = self.db.fetch_value(
            "SELECT SUM(amount) FROM transactions WHERE type = 'expense'"
        ) or 0
        
        balance = income - expense
        
        return {
            "message": f"当前余额：{balance}元（收入{income}元，支出{expense}元）",
            "balance": balance,
            "income": income,
            "expense": expense,
            "executed": True
        }
    
    async def _handle_unknown(self, command: VoiceCommand, session: VoiceSession) -> Dict[str, Any]:
        return {
            "message": "抱歉，我没有理解您的意思，请再说一遍",
            "executed": False,
            "suggestions": [
                "您可以说：打开客厅灯",
                "您可以说：记一笔50块午饭",
                "您可以说：提醒我三点开会",
                "您可以说：明天天气怎么样"
            ]
        }
    
    def register_handler(self, intent: str, handler: Callable[..., Awaitable[Dict[str, Any]]]):
        self.handlers[intent] = handler


class VoiceFeedback:
    """语音反馈生成器"""
    
    SUCCESS_TEMPLATES = {
        "light_control": "{action_text}成功",
        "ac_control": "空调已{action_text}",
        "accounting": "好的，已记录{amount}元{category}",
        "reminder": "好的，{time}会提醒您{content}",
        "schedule": "{date}有{count}个安排",
        "weather": "{location}{date}{condition}，气温{temperature}",
        "expense_query": "{date}共消费{total}元",
        "balance_query": "当前余额{balance}元"
    }
    
    ERROR_TEMPLATES = {
        "not_understood": "抱歉，我没有理解您的意思",
        "execution_failed": "执行失败了，请稍后再试",
        "network_error": "网络连接出现问题",
        "timeout": "操作超时，请重试"
    }
    
    CONFIRMATION_TEMPLATES = {
        "accounting": "您说的是记一笔{amount}元{category}吗？",
        "reminder": "要设置{time}提醒{content}吗？",
        "delete": "确定要删除吗？"
    }
    
    @classmethod
    def generate_response(cls, result: Dict[str, Any], command: VoiceCommand) -> str:
        if result.get("success"):
            return result.get("message", "操作成功")
        else:
            return result.get("message", cls.ERROR_TEMPLATES["execution_failed"])
    
    @classmethod
    def generate_confirmation(cls, intent: str, slots: Dict[str, Any]) -> str:
        template = cls.CONFIRMATION_TEMPLATES.get(intent, "请确认您的操作？")
        try:
            return template.format(**slots)
        except KeyError:
            return "请确认您的操作？"
    
    @classmethod
    def generate_greeting(cls, wake_word: str = "小助手") -> str:
        greetings = [
            f"我在，请说",
            f"好的，请说",
            f"嗯，有什么可以帮您",
            f"在呢，请吩咐"
        ]
        import random
        return random.choice(greetings)
    
    @classmethod
    def generate_farewell(cls) -> str:
        farewells = [
            "好的，有问题随时叫我",
            "再见，随时为您服务",
            "好的，我一直在"
        ]
        import random
        return random.choice(farewells)


class DialogueManager:
    """多轮对话管理器"""
    
    MAX_TURNS = 20
    SESSION_TIMEOUT = 300  # 5分钟
    
    def __init__(self):
        self.sessions: Dict[str, VoiceSession] = {}
        self.session_history: deque = deque(maxlen=100)
    
    def create_session(self, wake_word: str = None) -> VoiceSession:
        session_id = str(uuid.uuid4())
        session = VoiceSession(
            session_id=session_id,
            state=SessionState.LISTENING,
            wake_word=wake_word
        )
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[VoiceSession]:
        return self.sessions.get(session_id)
    
    def update_session(self, session: VoiceSession, command: VoiceCommand = None, response: Dict = None):
        session.last_active = datetime.now()
        session.turn_count += 1
        
        if command:
            session.command_history.append({
                "command": command.to_dict(),
                "timestamp": datetime.now().isoformat()
            })
        
        if response:
            session.command_history[-1]["response"] = response if session.command_history else None
        
        if session.turn_count >= self.MAX_TURNS:
            session.state = SessionState.IDLE
    
    def is_session_active(self, session: VoiceSession) -> bool:
        if session.state == SessionState.IDLE:
            return False
        
        elapsed = (datetime.now() - session.last_active).total_seconds()
        if elapsed > self.SESSION_TIMEOUT:
            session.state = SessionState.IDLE
            return False
        
        return True
    
    def end_session(self, session_id: str):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            self.session_history.append({
                "session_id": session_id,
                "turn_count": session.turn_count,
                "ended_at": datetime.now().isoformat()
            })
            session.state = SessionState.IDLE
    
    def cleanup_expired_sessions(self):
        expired = []
        for session_id, session in self.sessions.items():
            if not self.is_session_active(session):
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
    
    def get_context(self, session: VoiceSession) -> Dict[str, Any]:
        return {
            "turn_count": session.turn_count,
            "last_commands": session.command_history[-3:] if session.command_history else [],
            "context": session.context
        }


class VoiceControlService:
    """语音控制服务主类"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            data_dir = Path(__file__).parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "voice_control.db")
        
        self.db = DatabaseHelper(db_path)
        self.wake_detector = WakeWordDetector()
        self.command_parser = CommandParser()
        self.command_executor = CommandExecutor(self.db)
        self.dialogue_manager = DialogueManager()
        
        self._init_database()
        
        self.is_listening = False
        self.current_session: Optional[VoiceSession] = None
    
    def _init_database(self):
        self.db.create_table(
            "voice_sessions",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            wake_word TEXT,
            command TEXT,
            response TEXT,
            executed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """
        )
        
        self.db.create_table(
            "transactions",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            type TEXT,
            description TEXT,
            date TEXT,
            created_at TIMESTAMP
            """
        )
        
        self.db.create_table(
            "reminders",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT,
            time_type TEXT,
            hour INTEGER,
            minute INTEGER,
            minutes_later INTEGER,
            repeat TEXT,
            status TEXT,
            created_at TIMESTAMP
            """
        )
        
        self.db.create_table(
            "calendar_events",
            """
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            start_time TEXT,
            end_time TEXT,
            description TEXT,
            created_at TIMESTAMP
            """
        )
    
    async def process_input(self, text: str, session_id: str = None) -> Dict[str, Any]:
        """处理语音输入"""
        if not text or not text.strip():
            return self._response("抱歉，没有听到您的声音", success=False)
        
        text = text.strip()
        
        wake_result = self.wake_detector.detect(text)
        if wake_result and wake_result["detected"]:
            return await self._handle_wake_word(wake_result)
        
        if session_id:
            session = self.dialogue_manager.get_session(session_id)
            if session and self.dialogue_manager.is_session_active(session):
                return await self._process_command(text, session)
        
        if self.current_session and self.dialogue_manager.is_session_active(self.current_session):
            return await self._process_command(text, self.current_session)
        
        command = self.command_parser.parse(text)
        if command.confidence > 0.7:
            session = self.dialogue_manager.create_session()
            return await self._process_command(text, session)
        
        return self._response(
            "您可以说'小助手'来唤醒我，然后告诉我您想做什么",
            success=False
        )
    
    async def _handle_wake_word(self, wake_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理唤醒词"""
        session = self.dialogue_manager.create_session(wake_result["wake_word"])
        self.current_session = session
        
        remaining_text = wake_result.get("remaining_text", "")
        
        self._log_session(session, wake_result["wake_word"], None, None, False)
        
        if remaining_text:
            return await self._process_command(remaining_text, session)
        
        greeting = VoiceFeedback.generate_greeting(wake_result["wake_word"])
        session.state = SessionState.LISTENING
        
        return self._response(greeting, session_id=session.session_id, state="listening")
    
    async def _process_command(self, text: str, session: VoiceSession) -> Dict[str, Any]:
        """处理指令"""
        command = self.command_parser.parse(text)
        
        if command.command_type == CommandType.UNKNOWN and command.confidence < 0.3:
            return self._response(
                "抱歉，我没有理解您的意思，请再说一遍",
                session_id=session.session_id,
                success=False
            )
        
        result = await self.command_executor.execute(command, session)
        
        response_text = VoiceFeedback.generate_response(result, command)
        
        self.dialogue_manager.update_session(session, command, result)
        
        self._log_session(
            session,
            session.wake_word,
            command.raw_text,
            response_text,
            result.get("success", False)
        )
        
        return self._response(
            response_text,
            session_id=session.session_id,
            command=command.to_dict(),
            result=result,
            state="responding" if result.get("success") else "listening"
        )
    
    def _log_session(self, session: VoiceSession, wake_word: str, command: str, response: str, executed: bool):
        """记录会话日志"""
        try:
            self.db.insert("voice_sessions", {
                "session_id": session.session_id,
                "wake_word": wake_word,
                "command": command or "",
                "response": response or "",
                "executed": executed,
                "created_at": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to log session: {e}")
    
    def _response(self, message: str, **kwargs) -> Dict[str, Any]:
        """构建响应"""
        return {
            "success": kwargs.get("success", True),
            "message": message,
            "session_id": kwargs.get("session_id"),
            "command": kwargs.get("command"),
            "result": kwargs.get("result"),
            "state": kwargs.get("state", "idle"),
            "timestamp": datetime.now().isoformat()
        }
    
    async def end_session(self, session_id: str = None) -> Dict[str, Any]:
        """结束会话"""
        if session_id:
            self.dialogue_manager.end_session(session_id)
        elif self.current_session:
            self.dialogue_manager.end_session(self.current_session.session_id)
            self.current_session = None
        
        return self._response(VoiceFeedback.generate_farewell())
    
    def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取会话历史"""
        return self.db.fetch_all(
            "SELECT * FROM voice_sessions WHERE session_id = ? ORDER BY created_at DESC LIMIT ?",
            (session_id, limit)
        )
    
    def get_all_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取所有会话"""
        return self.db.fetch_all(
            "SELECT DISTINCT session_id, wake_word, created_at FROM voice_sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        total_commands = self.db.count("voice_sessions")
        successful_commands = self.db.count("voice_sessions", "executed = 1")
        
        wake_word_stats = self.db.fetch_all(
            "SELECT wake_word, COUNT(*) as count FROM voice_sessions GROUP BY wake_word"
        )
        
        return {
            "total_commands": total_commands,
            "successful_commands": successful_commands,
            "success_rate": successful_commands / total_commands if total_commands > 0 else 0,
            "wake_word_distribution": {r["wake_word"]: r["count"] for r in wake_word_stats if r["wake_word"]}
        }
    
    def add_custom_wake_word(self, wake_word: str, aliases: List[str] = None, sensitivity: float = 0.8):
        """添加自定义唤醒词"""
        self.wake_detector.add_wake_word(wake_word, aliases, sensitivity)
        return {"success": True, "message": f"已添加唤醒词：{wake_word}"}
    
    def get_supported_commands(self) -> List[Dict[str, Any]]:
        """获取支持的命令列表"""
        return [
            {
                "type": "system_control",
                "description": "系统控制",
                "examples": ["打开灯光", "关闭空调", "把温度调到26度"],
                "slots": ["device", "action", "value"]
            },
            {
                "type": "info_query",
                "description": "信息查询",
                "examples": ["今天花了多少钱", "查询余额"],
                "slots": ["time_range", "query_type"]
            },
            {
                "type": "accounting",
                "description": "记账",
                "examples": ["记一笔50块午饭", "工资到账10000"],
                "slots": ["amount", "category", "transaction_type"]
            },
            {
                "type": "reminder",
                "description": "提醒",
                "examples": ["提醒我三点开会", "10分钟后提醒我喝水"],
                "slots": ["time", "content", "repeat"]
            },
            {
                "type": "schedule",
                "description": "日程",
                "examples": ["明天有什么安排", "查询今天的日程"],
                "slots": ["date", "query_type"]
            },
            {
                "type": "weather",
                "description": "天气",
                "examples": ["今天天气怎么样", "明天北京天气"],
                "slots": ["date", "location"]
            }
        ]


_service_instance: Optional[VoiceControlService] = None


def get_voice_control_service() -> VoiceControlService:
    global _service_instance
    if _service_instance is None:
        _service_instance = VoiceControlService()
    return _service_instance


async def process_voice_input(text: str, session_id: str = None) -> Dict[str, Any]:
    service = get_voice_control_service()
    return await service.process_input(text, session_id)


async def end_voice_session(session_id: str = None) -> Dict[str, Any]:
    service = get_voice_control_service()
    return await service.end_session(session_id)


def run_tests():
    """运行测试"""
    import asyncio
    
    async def test():
        service = VoiceControlService()
        
        print("=" * 60)
        print("语音控制服务测试")
        print("=" * 60)
        
        test_cases = [
            ("小助手", "唤醒词测试"),
            ("打开客厅灯", "系统控制"),
            ("关闭空调", "系统控制"),
            ("记一笔50块午饭", "记账"),
            ("工资到账10000", "收入记账"),
            ("提醒我三点开会", "提醒"),
            ("10分钟后提醒我喝水", "相对时间提醒"),
            ("今天花了多少钱", "消费查询"),
            ("明天天气怎么样", "天气查询"),
            ("明天有什么安排", "日程查询"),
        ]
        
        session_id = None
        
        for text, description in test_cases:
            print(f"\n[{description}] 输入: {text}")
            result = await service.process_input(text, session_id)
            print(f"  响应: {result.get('message')}")
            print(f"  状态: {result.get('state')}")
            if result.get('session_id'):
                session_id = result.get('session_id')
        
        print("\n" + "=" * 60)
        print("测试完成")
        print("=" * 60)
        
        stats = service.get_statistics()
        print(f"\n统计: {stats}")
    
    asyncio.run(test())


if __name__ == "__main__":
    run_tests()