#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自然语言记账解析服务
解析用户的自然语言输入，自动提取记账信息
"""

import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AccountingEntry:
    """记账条目数据结构"""
    amount: float
    category: str
    type: str
    date: str
    description: str
    merchant: Optional[str] = None
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class NaturalLanguageAccountingParser:
    """自然语言记账解析器"""
    
    CATEGORY_KEYWORDS = {
        "餐饮": ["午饭", "早餐", "晚餐", "吃饭", "外卖", "餐", "饭", "早餐", "午餐", "晚饭", "早饭", "点餐", "美团", "饿了么", "肯德基", "麦当劳", "KFC", "星巴克", "奶茶", "咖啡", "饮料", "零食", "水果"],
        "交通": ["打车", "滴滴", "出租", "地铁", "公交", "高铁", "火车", "机票", "飞机", "加油", "停车", "过路费", "出行", "骑车", "共享单车", "单车"],
        "购物": ["买了", "买", "购物", "淘宝", "京东", "拼多多", "超市", "商场", "网购", "下单", "天猫", "衣服", "鞋子", "包", "化妆品", "护肤"],
        "娱乐": ["电影", "游戏", "KTV", "ktv", "健身", "运动", "旅游", "门票", "景点", "玩", "休闲娱乐"],
        "医疗": ["医院", "看病", "买药", "药", "体检", "挂号", "治疗"],
        "教育": ["书", "课程", "培训", "学习", "学费", "考试", "报名"],
        "通讯": ["话费", "流量", "宽带", "手机", "充值"],
        "住房": ["房租", "水电", "物业", "维修", "装修", "家具"],
        "收入": ["工资", "收入", "奖金", "红包", "返现", "退款", "报销", "收到", "转入", "到账"],
    }
    
    INCOME_KEYWORDS = ["工资", "收入", "奖金", "红包", "返现", "退款", "报销", "收到", "转入", "到账", "领取"]
    
    TIME_PATTERNS = {
        "今天": 0,
        "今日": 0,
        "昨天": -1,
        "昨日": -1,
        "前天": -2,
        "明天": 1,
        "后天": 2,
    }
    
    MERCHANT_PATTERNS = [
        r"(?:在|于|去|到)([^\s,，。！？]+?)(?:买了?|花了?|消费|购买)",
        r"([^\s,，。！？]+?)(?:外卖|打车|买单|付钱)",
        r"(?:美团|饿了么|滴滴|淘宝|京东|拼多多|星巴克|肯德基|麦当劳|KFC)",
    ]

    def __init__(self):
        self.amount_pattern = re.compile(
            r"(?:花了?|消费|支出|收入|收到|转入|到账|买|购买)?"
            r"(\d+(?:\.\d{1,2})?)"
            r"(?:块|元|块钱|￥|¥|RMB|rmb)?"
            r"(?:块|元|块钱)?"
            r"|"
            r"(?:￥|¥)"
            r"(\d+(?:\.\d{1,2})?)"
        )
        
        self.date_pattern = re.compile(
            r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)"
            r"|"
            r"(\d{1,2}[-/月]\d{1,2}[日]?)"
        )

    def parse(self, text: str) -> Optional[AccountingEntry]:
        """解析自然语言文本，提取记账信息"""
        if not text or not text.strip():
            return None
        
        text = text.strip()
        logger.info(f"Parsing accounting text: {text}")
        
        amount = self._extract_amount(text)
        if amount is None:
            logger.warning(f"No amount found in: {text}")
            return None
        
        category = self._detect_category(text)
        entry_type = self._detect_type(text, category)
        date = self._parse_date(text)
        description = self._generate_description(text, category, amount)
        merchant = self._extract_merchant(text)
        
        confidence = self._calculate_confidence(text, amount, category)
        
        entry = AccountingEntry(
            amount=amount,
            category=category,
            type=entry_type,
            date=date,
            description=description,
            merchant=merchant,
            confidence=confidence
        )
        
        logger.info(f"Parsed entry: {entry.to_dict()}")
        return entry

    def _extract_amount(self, text: str) -> Optional[float]:
        """提取金额"""
        match = self.amount_pattern.search(text)
        if match:
            if match.group(1):
                return float(match.group(1))
            elif match.group(2):
                return float(match.group(2))
        
        simple_pattern = re.compile(r"(\d+(?:\.\d{1,2})?)\s*(?:块|元|块钱)")
        match = simple_pattern.search(text)
        if match:
            return float(match.group(1))
        
        return None

    def _detect_category(self, text: str) -> str:
        """检测分类"""
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text.lower():
                    return category
        return "其他"

    def _detect_type(self, text: str, category: str) -> str:
        """检测类型（收入/支出）"""
        if category == "收入":
            return "income"
        
        for keyword in self.INCOME_KEYWORDS:
            if keyword in text:
                return "income"
        
        return "expense"

    def _parse_date(self, text: str) -> str:
        """解析日期"""
        for time_word, offset in self.TIME_PATTERNS.items():
            if time_word in text:
                target_date = datetime.now() + timedelta(days=offset)
                return target_date.strftime("%Y-%m-%d")
        
        match = self.date_pattern.search(text)
        if match:
            date_str = match.group(1) or match.group(2)
            if date_str:
                date_str = date_str.replace("年", "-").replace("月", "-").replace("日", "").replace("/", "-")
                try:
                    if len(date_str.split("-")) == 2:
                        month, day = date_str.split("-")
                        year = datetime.now().year
                        date_str = f"{year}-{int(month):02d}-{int(day):02d}"
                    return date_str
                except:
                    pass
        
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_merchant(self, text: str) -> Optional[str]:
        """提取商户名称"""
        for pattern in self.MERCHANT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if match.groups() and match.group(1):
                    return match.group(1)
                return match.group(0)
        
        platform_keywords = ["美团", "饿了么", "滴滴", "淘宝", "京东", "拼多多", "星巴克", "肯德基", "麦当劳", "KFC"]
        for platform in platform_keywords:
            if platform in text:
                return platform
        
        return None

    def _generate_description(self, text: str, category: str, amount: float) -> str:
        """生成描述"""
        text = re.sub(r"[\d.]+\s*(?:块|元|块钱|￥|¥|RMB)", f"{amount}元", text)
        text = re.sub(r"^(?:今天|昨天|前天|明日|后日|今日)", "", text)
        text = re.sub(r"^(?:花了?|消费|支出|收入|收到|转入|到账)", "", text)
        return text.strip() or f"{category}支出"

    def _calculate_confidence(self, text: str, amount: float, category: str) -> float:
        """计算置信度"""
        confidence = 0.5
        
        if amount and amount > 0:
            confidence += 0.2
        
        if category != "其他":
            confidence += 0.15
        
        if any(word in text for word in ["今天", "昨天", "前天"]):
            confidence += 0.05
        
        if any(word in text for word in ["午饭", "晚餐", "打车", "工资"]):
            confidence += 0.1
        
        return min(confidence, 1.0)


async def parse_accounting_text(text: str) -> Dict[str, Any]:
    """
    解析自然语言记账文本
    
    Args:
        text: 自然语言文本，如 "今天午饭花了50块"
    
    Returns:
        解析结果字典
    """
    parser = NaturalLanguageAccountingParser()
    entry = parser.parse(text)
    
    if entry is None:
        return {
            "success": False,
            "message": "无法解析记账信息，请确认输入包含金额",
            "data": None
        }
    
    return {
        "success": True,
        "message": "解析成功",
        "data": entry.to_dict()
    }


async def quick_add_transaction(text: str) -> Dict[str, Any]:
    """
    快速记账：解析并添加交易记录
    
    Args:
        text: 自然语言文本
    
    Returns:
        添加结果
    """
    from .finance_service import add_transaction
    
    parser = NaturalLanguageAccountingParser()
    entry = parser.parse(text)
    
    if entry is None:
        return {
            "success": False,
            "message": "无法解析记账信息"
        }
    
    transaction = await add_transaction(
        amount=entry.amount,
        category=entry.category,
        type=entry.type,
        description=entry.description,
        date=entry.date
    )
    
    return {
        "success": True,
        "message": f"已记录: {entry.type == 'income' and '收入' or '支出'} {entry.amount}元 ({entry.category})",
        "data": {
            "parsed": entry.to_dict(),
            "transaction": transaction
        }
    }


def run_tests():
    """运行测试用例"""
    test_cases = [
        "今天午饭花了50块",
        "打车花了25元",
        "收工资5000",
        "买了本书35元",
        "昨天晚餐120",
        "美团外卖花了38",
        "滴滴打车20块",
        "工资到账10000",
        "收到红包200元",
        "前天买衣服花了399",
        "淘宝下单128元",
        "京东购物599",
        "星巴克咖啡35块",
        "充话费50",
        "水电费200",
        "电影票60元两张",
        "超市买菜150",
        "加油300",
        "地铁6块",
        "KTV消费280",
    ]
    
    parser = NaturalLanguageAccountingParser()
    
    print("=" * 80)
    print("自然语言记账解析测试")
    print("=" * 80)
    
    for text in test_cases:
        entry = parser.parse(text)
        if entry:
            print(f"\n输入: {text}")
            print(f"  金额: {entry.amount}元")
            print(f"  分类: {entry.category}")
            print(f"  类型: {'收入' if entry.type == 'income' else '支出'}")
            print(f"  日期: {entry.date}")
            print(f"  描述: {entry.description}")
            print(f"  商户: {entry.merchant or '无'}")
            print(f"  置信度: {entry.confidence:.0%}")
        else:
            print(f"\n输入: {text}")
            print(f"  结果: 解析失败")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()