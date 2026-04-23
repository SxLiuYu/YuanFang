#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音命令解析服务
解析用户的语音输入，识别意图并提取槽位信息
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型枚举"""
    ACCOUNTING = "accounting"
    QUERY = "query"
    REMINDER = "reminder"
    CONTROL = "control"
    WEATHER = "weather"
    UNKNOWN = "unknown"


@dataclass
class VoiceCommand:
    """语音命令数据结构"""
    intent: str
    slots: Dict[str, Any]
    original_text: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IntentPattern:
    """意图模式"""
    keywords: List[str]
    slot_patterns: Optional[Dict[str, Any]] = None
    priority: int = 0


class VoiceCommandParser:
    """语音命令解析器"""
    
    INTENT_PATTERNS = {
        IntentType.ACCOUNTING: IntentPattern(
            keywords=[
                "记一笔", "记账", "花了", "消费", "支出", "收入",
                "买了", "购物", "支付", "付款", "转账", "红包",
                "块", "元", "块钱", "￥", "¥", "工资", "到账", "奖金"
            ],
            slot_patterns={
                "amount": r"(\d+(?:\.\d{1,2})?)\s*(?:块|元|块钱)?",
                "category": None,
                "action": None
            },
            priority=1
        ),
        IntentType.QUERY: IntentPattern(
            keywords=[
                "花了多少", "花了多少钱", "消费多少", "支出多少",
                "查询", "查一下", "看看", "统计", "账单",
                "收入多少", "余额", "还剩多少"
            ],
            slot_patterns={
                "query_type": None,
                "time_range": None,
                "category": None
            },
            priority=2
        ),
        IntentType.REMINDER: IntentPattern(
            keywords=[
                "提醒我", "提醒", "叫我", "通知我", "别忘了",
                "记得", "定时", "闹钟", "几点", "分钟后再"
            ],
            slot_patterns={
                "time": None,
                "content": None,
                "repeat": None
            },
            priority=2
        ),
        IntentType.CONTROL: IntentPattern(
            keywords=[
                "打开", "开启", "关掉", "关闭", "启动", "停止",
                "调高", "调低", "设置", "切换", "调节", "调到",
                "温度调", "亮度调", "音量调"
            ],
            slot_patterns={
                "device": None,
                "action": None,
                "value": None
            },
            priority=1
        ),
        IntentType.WEATHER: IntentPattern(
            keywords=[
                "天气", "气温", "温度", "下雨", "晴天", "阴天",
                "天气预报", "今天天气", "明天天气", "冷不冷", "热不热"
            ],
            slot_patterns={
                "location": None,
                "date": None
            },
            priority=2
        )
    }
    
    TIME_KEYWORDS = {
        "今天": 0, "今日": 0,
        "昨天": -1, "昨日": -1,
        "前天": -2,
        "明天": 1, "明日": 1,
        "后天": 2,
        "大后天": 3,
        "本周": "week",
        "上周": "last_week",
        "下周": "next_week",
        "本月": "month",
        "上月": "last_month",
        "下月": "next_month"
    }
    
    CATEGORY_KEYWORDS = {
        "餐饮": ["午饭", "午餐", "早餐", "晚饭", "晚餐", "吃饭", "外卖", "餐", "饭", 
                 "奶茶", "咖啡", "饮料", "零食", "水果", "肯德基", "麦当劳", "星巴克"],
        "交通": ["打车", "滴滴", "出租", "地铁", "公交", "高铁", "火车", "飞机", 
                 "机票", "加油", "停车", "过路费", "出行", "单车"],
        "购物": ["买了", "买", "购物", "淘宝", "京东", "拼多多", "超市", "商场", 
                 "网购", "衣服", "鞋子", "包", "化妆品"],
        "娱乐": ["电影", "游戏", "KTV", "健身", "运动", "旅游", "门票"],
        "医疗": ["医院", "看病", "买药", "药", "体检", "挂号"],
        "教育": ["书", "课程", "培训", "学习", "学费", "考试"],
        "通讯": ["话费", "流量", "宽带", "充值"],
        "住房": ["房租", "水电", "物业", "维修", "装修"],
        "收入": ["工资", "奖金", "红包", "返现", "退款", "报销", "到账"]
    }
    
    DEVICE_KEYWORDS = {
        "灯": ["灯", "台灯", "吊灯", "吸顶灯", "射灯", "灯带"],
        "空调": ["空调", "冷气", "暖风"],
        "电视": ["电视", "电视机", "投影", "投影仪"],
        "音响": ["音响", "音箱", "蓝牙音箱"],
        "窗帘": ["窗帘", "百叶窗", "遮光帘"],
        "风扇": ["风扇", "电风扇", "吊扇"],
        "扫地机": ["扫地机", "扫地机器人", "清洁机器人"],
        "加湿器": ["加湿器", "湿度"],
        "净化器": ["净化器", "空气净化器"]
    }
    
    ROOM_KEYWORDS = ["客厅", "卧室", "厨房", "卫生间", "书房", "阳台", "餐厅"]
    
    CONTROL_ACTIONS = {
        "on": ["打开", "开启", "启动", "开", "打开"],
        "off": ["关闭", "关掉", "关", "停止", "停掉"],
        "up": ["调高", "升高", "增大", "加大", "提高"],
        "down": ["调低", "降低", "减小", "减少", "调小"]
    }
    
    TIME_PATTERNS = [
        (r"(\d{1,2})\s*点\s*(\d{1,2})?\s*分?", "absolute_time"),
        (r"(\d{1,2})\s*点", "hour_only"),
        (r"(\d+)\s*分钟后?", "minutes_later"),
        (r"(\d+)\s*小时后?", "hours_later"),
        (r"(明天|后天|大后天)\s*(上午|下午|晚上|早上)?", "relative_day"),
        (r"(上午|下午|晚上|早上|中午|傍晚)\s*(\d{1,2})\s*点?", "period_time")
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """预编译正则表达式"""
        self.amount_regex = re.compile(
            r"(?:花了?|消费|支出|收入|收到|转入|到账|买|购买)?"
            r"(\d+(?:\.\d{1,2})?)"
            r"(?:块|元|块钱|￥|¥|RMB)?"
        )
        self.time_regex = re.compile(r"(\d{1,2})\s*点(?:\s*(\d{1,2})\s*分)?")
        self.minutes_later_regex = re.compile(r"(\d+)\s*分钟后?")
        self.hours_later_regex = re.compile(r"(\d+)\s*小时后?")

    def parse(self, text: str) -> VoiceCommand:
        """解析语音命令"""
        if not text or not text.strip():
            return VoiceCommand(
                intent=IntentType.UNKNOWN.value,
                slots={},
                original_text=text or "",
                confidence=0.0
            )
        
        text = text.strip()
        logger.info(f"Parsing voice command: {text}")
        
        intent, confidence = self._detect_intent(text)
        slots = self._extract_slots(text, intent)
        
        command = VoiceCommand(
            intent=intent.value,
            slots=slots,
            original_text=text,
            confidence=confidence
        )
        
        logger.info(f"Parsed command: {command.to_dict()}")
        return command

    def _detect_intent(self, text: str) -> Tuple[IntentType, float]:
        """检测意图"""
        text_lower = text.lower()
        scores: Dict[IntentType, float] = {}
        
        for intent_type, pattern in self.INTENT_PATTERNS.items():
            score = 0.0
            for keyword in pattern.keywords:
                if keyword in text_lower:
                    score += 1.0 / len(pattern.keywords)
            scores[intent_type] = score * (10 - pattern.priority)
        
        if not scores or max(scores.values()) == 0:
            return IntentType.UNKNOWN, 0.0
        
        best_intent = max(scores, key=lambda k: scores[k])
        best_score = scores[best_intent]
        
        max_possible = 10 - self.INTENT_PATTERNS[best_intent].priority
        confidence = min(best_score / max_possible, 1.0) if max_possible > 0 else 0.0
        
        return best_intent, round(confidence, 2)

    def _extract_slots(self, text: str, intent: IntentType) -> Dict[str, Any]:
        """提取槽位"""
        slots: Dict[str, Any] = {}
        
        if intent == IntentType.ACCOUNTING:
            slots = self._extract_accounting_slots(text)
        elif intent == IntentType.QUERY:
            slots = self._extract_query_slots(text)
        elif intent == IntentType.REMINDER:
            slots = self._extract_reminder_slots(text)
        elif intent == IntentType.CONTROL:
            slots = self._extract_control_slots(text)
        elif intent == IntentType.WEATHER:
            slots = self._extract_weather_slots(text)
        
        return slots

    def _extract_accounting_slots(self, text: str) -> Dict[str, Any]:
        """提取记账槽位"""
        slots: Dict[str, Any] = {}
        
        amount = self._extract_amount(text)
        if amount:
            slots["amount"] = amount
        
        category = self._detect_category(text)
        if category:
            slots["category"] = category
        
        action = self._detect_accounting_action(text)
        slots["action"] = action
        
        date = self._extract_date(text)
        if date:
            slots["date"] = date
        
        merchant = self._extract_merchant(text)
        if merchant:
            slots["merchant"] = merchant
        
        description = self._generate_description(text)
        slots["description"] = description
        
        return slots

    def _extract_query_slots(self, text: str) -> Dict[str, Any]:
        """提取查询槽位"""
        slots: Dict[str, Any] = {}
        
        if any(kw in text for kw in ["花了多少", "支出", "消费"]):
            slots["query_type"] = "expense"
        elif any(kw in text for kw in ["收入", "赚了"]):
            slots["query_type"] = "income"
        elif any(kw in text for kw in ["余额", "还剩"]):
            slots["query_type"] = "balance"
        else:
            slots["query_type"] = "summary"
        
        time_range = self._extract_time_range(text)
        if time_range:
            slots["time_range"] = time_range
        
        category = self._detect_category(text)
        if category and category != "其他":
            slots["category"] = category
        
        return slots

    def _extract_reminder_slots(self, text: str) -> Dict[str, Any]:
        """提取提醒槽位"""
        slots: Dict[str, Any] = {}
        
        time_info = self._extract_reminder_time(text)
        if time_info:
            slots["time"] = time_info
        
        content = self._extract_reminder_content(text)
        if content:
            slots["content"] = content
        
        repeat = self._extract_repeat_pattern(text)
        if repeat:
            slots["repeat"] = repeat
        
        return slots

    def _extract_control_slots(self, text: str) -> Dict[str, Any]:
        """提取控制槽位"""
        slots: Dict[str, Any] = {}
        
        device = self._extract_device(text)
        if device:
            slots["device"] = device
        
        room = self._extract_room(text)
        if room:
            slots["room"] = room
        
        action = self._extract_control_action(text)
        slots["action"] = action
        
        value = self._extract_control_value(text)
        if value:
            slots["value"] = value
        
        return slots

    def _extract_weather_slots(self, text: str) -> Dict[str, Any]:
        """提取天气槽位"""
        slots: Dict[str, Any] = {}
        
        date = self._extract_weather_date(text)
        if date:
            slots["date"] = date
        
        location = self._extract_location(text)
        if location:
            slots["location"] = location
        
        return slots

    def _extract_amount(self, text: str) -> Optional[float]:
        """提取金额"""
        match = self.amount_regex.search(text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return None

    def _detect_category(self, text: str) -> str:
        """检测分类"""
        text_lower = text.lower()
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return category
        return "其他"

    def _detect_accounting_action(self, text: str) -> str:
        """检测记账类型"""
        income_keywords = ["工资", "收入", "奖金", "红包", "返现", "退款", "报销", 
                          "收到", "转入", "到账", "领取"]
        for kw in income_keywords:
            if kw in text:
                return "income"
        return "expense"

    def _extract_date(self, text: str) -> Optional[str]:
        """提取日期"""
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text:
                if isinstance(offset, int):
                    target_date = datetime.now() + timedelta(days=offset)
                    return target_date.strftime("%Y-%m-%d")
        
        date_match = re.search(r"(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})", text)
        if date_match:
            return f"{date_match.group(1)}-{int(date_match.group(2)):02d}-{int(date_match.group(3)):02d}"
        
        month_day_match = re.search(r"(\d{1,2})[-/月](\d{1,2})", text)
        if month_day_match:
            year = datetime.now().year
            return f"{year}-{int(month_day_match.group(1)):02d}-{int(month_day_match.group(2)):02d}"
        
        return None

    def _extract_time_range(self, text: str) -> Optional[str]:
        """提取时间范围"""
        for time_word, value in self.TIME_KEYWORDS.items():
            if time_word in text:
                return str(value)
        return None

    def _extract_merchant(self, text: str) -> Optional[str]:
        """提取商户"""
        platforms = ["美团", "饿了么", "滴滴", "淘宝", "京东", "拼多多", 
                     "星巴克", "肯德基", "麦当劳", "KFC"]
        for platform in platforms:
            if platform in text:
                return platform
        return None

    def _generate_description(self, text: str) -> str:
        """生成描述"""
        desc = re.sub(r"[\d.]+\s*(?:块|元|块钱|￥|¥)", "", text)
        desc = re.sub(r"^(今天|昨天|前天|明日|后日|今日)", "", desc)
        desc = re.sub(r"^(记一笔|记账|花了?|消费|支出|收入|收到)", "", desc)
        return desc.strip() or "消费"

    def _extract_reminder_time(self, text: str) -> Optional[Dict[str, Any]]:
        """提取提醒时间"""
        hour_min_match = self.time_regex.search(text)
        if hour_min_match:
            hour = int(hour_min_match.group(1))
            minute = int(hour_min_match.group(2)) if hour_min_match.group(2) else 0
            return {"hour": hour, "minute": minute, "type": "absolute"}
        
        minutes_match = self.minutes_later_regex.search(text)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            return {"minutes_later": minutes, "type": "relative"}
        
        hours_match = self.hours_later_regex.search(text)
        if hours_match:
            hours = int(hours_match.group(1))
            return {"hours_later": hours, "type": "relative"}
        
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text:
                return {"relative_day": offset, "type": "day_offset"}
        
        return None

    def _extract_reminder_content(self, text: str) -> Optional[str]:
        """提取提醒内容"""
        prefix_patterns = ["提醒我", "提醒", "叫我", "通知我", "别忘了", "记得"]
        for pattern in prefix_patterns:
            if pattern in text:
                content = text.split(pattern)[-1].strip()
                content = re.sub(r"\d+\s*点.*", "", content)
                content = re.sub(r"\d+\s*分钟.*", "", content)
                if content:
                    return content
        
        return None

    def _extract_repeat_pattern(self, text: str) -> Optional[str]:
        """提取重复模式"""
        if "每天" in text:
            return "daily"
        elif "每周" in text or "每星期" in text:
            return "weekly"
        elif "每月" in text:
            return "monthly"
        return None

    def _extract_device(self, text: str) -> Optional[str]:
        """提取设备"""
        for device_type, keywords in self.DEVICE_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return device_type
        return None

    def _extract_room(self, text: str) -> Optional[str]:
        """提取房间"""
        for room in self.ROOM_KEYWORDS:
            if room in text:
                return room
        return None

    def _extract_control_action(self, text: str) -> str:
        """提取控制动作"""
        for action, keywords in self.CONTROL_ACTIONS.items():
            for kw in keywords:
                if kw in text:
                    return action
        return "unknown"

    def _extract_control_value(self, text: str) -> Optional[Any]:
        """提取控制值"""
        temp_match = re.search(r"(\d+)\s*度", text)
        if temp_match:
            return {"temperature": int(temp_match.group(1))}
        
        percent_match = re.search(r"(\d+)\s*%", text)
        if percent_match:
            return {"percentage": int(percent_match.group(1))}
        
        level_match = re.search(r"(最大|最小|中间|自动)", text)
        if level_match:
            return {"level": level_match.group(1)}
        
        return None

    def _extract_weather_date(self, text: str) -> Optional[str]:
        """提取天气日期"""
        for time_word, offset in self.TIME_KEYWORDS.items():
            if time_word in text and isinstance(offset, int):
                if -3 <= offset <= 3:
                    target_date = datetime.now() + timedelta(days=offset)
                    return target_date.strftime("%Y-%m-%d")
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """提取地点"""
        city_pattern = r"(北京|上海|广州|深圳|杭州|南京|成都|武汉|西安|重庆|天津|苏州|厦门|青岛|大连|宁波|无锡|长沙|郑州|济南|福州)"
        match = re.search(city_pattern, text)
        if match:
            return match.group(1)
        return None


class VoiceCommandService:
    """语音命令服务"""
    
    def __init__(self):
        self.parser = VoiceCommandParser()
    
    def parse_command(self, text: str) -> Dict[str, Any]:
        """解析语音命令"""
        command = self.parser.parse(text)
        return command.to_dict()
    
    def batch_parse(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量解析语音命令"""
        return [self.parse_command(text) for text in texts]
    
    def get_supported_intents(self) -> List[Dict[str, Any]]:
        """获取支持的意图列表"""
        return [
            {
                "intent": "accounting",
                "description": "记账意图",
                "examples": ["记一笔50块午饭", "打车花了25元", "工资到账10000"],
                "slots": ["amount", "category", "action", "date", "merchant", "description"]
            },
            {
                "intent": "query",
                "description": "查询意图",
                "examples": ["今天花了多少钱", "查询本月支出", "看看餐饮消费"],
                "slots": ["query_type", "time_range", "category"]
            },
            {
                "intent": "reminder",
                "description": "提醒意图",
                "examples": ["提醒我3点开会", "10分钟后叫我", "每天早上7点叫醒我"],
                "slots": ["time", "content", "repeat"]
            },
            {
                "intent": "control",
                "description": "控制意图",
                "examples": ["打开客厅灯", "关闭空调", "把温度调到26度"],
                "slots": ["device", "room", "action", "value"]
            },
            {
                "intent": "weather",
                "description": "天气意图",
                "examples": ["今天天气怎么样", "明天北京天气", "后天会不会下雨"],
                "slots": ["date", "location"]
            }
        ]


async def parse_voice_command(text: str) -> Dict[str, Any]:
    """解析语音命令的异步接口"""
    service = VoiceCommandService()
    return service.parse_command(text)


def run_tests():
    """运行测试用例"""
    test_cases = [
        ("记一笔50块午饭", "accounting"),
        ("打车花了25元", "accounting"),
        ("今天花了多少钱", "query"),
        ("查询本月支出", "query"),
        ("提醒我3点开会", "reminder"),
        ("10分钟后叫我", "reminder"),
        ("打开客厅灯", "control"),
        ("关闭空调", "control"),
        ("把温度调到26度", "control"),
        ("今天天气怎么样", "weather"),
        ("明天北京天气", "weather"),
        ("工资到账10000", "accounting"),
        ("每天早上7点提醒我吃早饭", "reminder"),
        ("美团外卖花了38", "accounting"),
        ("查一下餐饮消费", "query"),
    ]
    
    service = VoiceCommandService()
    
    print("=" * 80)
    print("语音命令解析测试")
    print("=" * 80)
    
    for text, expected_intent in test_cases:
        result = service.parse_command(text)
        status = "[OK]" if result["intent"] == expected_intent else "[FAIL]"
        print(f"\n{status} 输入: {text}")
        print(f"  意图: {result['intent']} (预期: {expected_intent})")
        print(f"  槽位: {result['slots']}")
        print(f"  置信度: {result['confidence']}")
    
    print("\n" + "=" * 80)
    print("支持的命令列表:")
    print("=" * 80)
    
    for intent_info in service.get_supported_intents():
        print(f"\n{intent_info['intent']} - {intent_info['description']}")
        print(f"  示例: {', '.join(intent_info['examples'][:3])}")
        print(f"  槽位: {', '.join(intent_info['slots'])}")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()