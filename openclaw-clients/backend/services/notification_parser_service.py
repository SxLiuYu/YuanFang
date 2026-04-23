#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知解析服务
自动识别支付通知、快递通知、验证码、银行短信等
"""

import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    PAYMENT = "payment"
    EXPRESS = "express"
    VERIFICATION_CODE = "verification_code"
    BANK_SMS = "bank_sms"
    UNKNOWN = "unknown"


class PaymentPlatform(Enum):
    ALIPAY = "alipay"
    WECHAT = "wechat"
    BANK = "bank"
    UNKNOWN = "unknown"


@dataclass
class PaymentInfo:
    amount: float
    merchant: str
    time: Optional[str]
    platform: str
    raw_text: str
    card_tail: Optional[str] = None


@dataclass
class ExpressInfo:
    company: str
    tracking_number: Optional[str]
    pickup_code: Optional[str]
    raw_text: str


@dataclass
class VerificationCodeInfo:
    code: str
    service: Optional[str]
    raw_text: str


@dataclass
class BankSmsInfo:
    card_tail: Optional[str]
    amount: Optional[float]
    balance: Optional[float]
    transaction_type: Optional[str]
    merchant: Optional[str]
    time: Optional[str]
    raw_text: str


class NotificationParserService:
    """通知解析服务"""
    
    EXPRESS_COMPANIES = {
        "顺丰": "顺丰速运",
        "sf": "顺丰速运",
        "圆通": "圆通速递",
        "yt": "圆通速递",
        "中通": "中通快递",
        "zt": "中通快递",
        "申通": "申通快递",
        "韵达": "韵达快递",
        "yd": "韵达快递",
        "极兔": "极兔速递",
        "邮政": "中国邮政",
        "ems": "EMS",
        "ems": "EMS",
        "京东": "京东快递",
        "jd": "京东快递",
        "百世": "百世快递",
        "德邦": "德邦快递",
    }
    
    PAYMENT_PATTERNS = {
        PaymentPlatform.ALIPAY: [
            r"你通过扫码向(.+?)付款(\d+\.?\d*)元",
            r"支付宝.*向(.+?)付款(\d+\.?\d*)元",
            r"向(.+?)转账(\d+\.?\d*)元.*支付宝",
            r"支付宝.*支付(\d+\.?\d*)元.*商户[：:](.+?)(?:\s|$)",
        ],
        PaymentPlatform.WECHAT: [
            r"支付成功.*向(.+?)付款(\d+\.?\d*)元",
            r"微信支付.*(\d+\.?\d*)元.*商户[：:](.+?)(?:\s|$)",
            r"向(.+?)转账(\d+\.?\d*)元.*微信",
            r"微信.*支付(\d+\.?\d*)元",
        ],
        PaymentPlatform.BANK: [
            r"您尾号(\d{4})的.*卡消费(\d+\.?\d*)元",
            r"尾号(\d{4}).*支出(\d+\.?\d*)元",
            r"银行卡.*消费(\d+\.?\d*)元.*商户[：:](.+?)(?:\s|$)",
        ],
    }
    
    EXPRESS_PATTERNS = [
        r"(顺丰|圆通|中通|申通|韵达|极兔|京东|百世|德邦|邮政|EMS).*(?:快递|速递)?.*?单号[：:]?\s*([A-Za-z0-9]+)",
        r"快递.*取件码[：:]?\s*(\d{4,8})",
        r"您的快递.*?取件码[：:]?\s*(\d{4,8})",
        r"(?:驿站|快递柜).*取件码[：:]?\s*(\d{4,8})",
        r"单号[：:]?\s*([A-Za-z0-9]{8,}).*?(顺丰|圆通|中通|申通|韵达)",
    ]
    
    VERIFICATION_CODE_PATTERNS = [
        r"验证码[：:]?\s*(\d{4,8})",
        r"验证码.*?(\d{4,8})",
        r"动态码[：:]?\s*(\d{4,8})",
        r"校验码[：:]?\s*(\d{4,8})",
        r"安全码[：:]?\s*(\d{4,8})",
        r"code[：:]?\s*(\d{4,8})",
        r"(\d{4,8}).*验证码",
        r"您的验证码是[：:]?\s*(\d{4,8})",
    ]
    
    BANK_SMS_PATTERNS = {
        "consumption": [
            r"尾号(\d{4}).*消费(\d+\.?\d*)元",
            r"尾号(\d{4}).*支出(\d+\.?\d*)元",
            r"尾号(\d{4}).*付款(\d+\.?\d*)元",
        ],
        "deposit": [
            r"尾号(\d{4}).*存入(\d+\.?\d*)元",
            r"尾号(\d{4}).*收入(\d+\.?\d*)元",
            r"尾号(\d{4}).*转入(\d+\.?\d*)元",
        ],
        "balance": [
            r"余额(\d+\.?\d*)元",
            r"可用余额[：:]?\s*(\d+\.?\d*)元",
        ],
    }
    
    def __init__(self):
        pass
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        解析通知文本，自动识别类型并提取信息
        
        Args:
            text: 通知文本
            
        Returns:
            解析结果字典
        """
        text = text.strip()
        
        verification_result = self._parse_verification_code(text)
        if verification_result:
            return {
                "type": NotificationType.VERIFICATION_CODE.value,
                "data": asdict(verification_result),
                "success": True
            }
        
        payment_result = self._parse_payment(text)
        if payment_result:
            return {
                "type": NotificationType.PAYMENT.value,
                "data": asdict(payment_result),
                "success": True
            }
        
        express_result = self._parse_express(text)
        if express_result:
            return {
                "type": NotificationType.EXPRESS.value,
                "data": asdict(express_result),
                "success": True
            }
        
        bank_result = self._parse_bank_sms(text)
        if bank_result:
            return {
                "type": NotificationType.BANK_SMS.value,
                "data": asdict(bank_result),
                "success": True
            }
        
        return {
            "type": NotificationType.UNKNOWN.value,
            "data": {"raw_text": text},
            "success": False
        }
    
    def _parse_payment(self, text: str) -> Optional[PaymentInfo]:
        """解析支付通知"""
        time_match = re.search(r"(\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", text)
        time_str = time_match.group(1) if time_match else None
        
        for platform, patterns in self.PAYMENT_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if platform == PaymentPlatform.ALIPAY:
                        if len(groups) >= 2:
                            if self._is_amount(groups[1]):
                                merchant = groups[0]
                                amount = float(groups[1])
                            else:
                                merchant = groups[1]
                                amount = float(groups[0])
                            return PaymentInfo(
                                amount=amount,
                                merchant=merchant,
                                time=time_str,
                                platform=platform.value,
                                raw_text=text
                            )
                    
                    elif platform == PaymentPlatform.WECHAT:
                        if len(groups) >= 2:
                            if self._is_amount(groups[1]):
                                merchant = groups[0]
                                amount = float(groups[1])
                            else:
                                merchant = groups[1]
                                amount = float(groups[0])
                            return PaymentInfo(
                                amount=amount,
                                merchant=merchant,
                                time=time_str,
                                platform=platform.value,
                                raw_text=text
                            )
                    
                    elif platform == PaymentPlatform.BANK:
                        if len(groups) >= 2:
                            card_tail = groups[0] if len(groups[0]) == 4 else None
                            amount = float(groups[1]) if len(groups) > 1 else 0
                            merchant = groups[2] if len(groups) > 2 else None
                            return PaymentInfo(
                                amount=amount,
                                merchant=merchant or "未知商户",
                                time=time_str,
                                platform=platform.value,
                                raw_text=text,
                                card_tail=card_tail
                            )
        
        return None
    
    def _parse_express(self, text: str) -> Optional[ExpressInfo]:
        """解析快递通知"""
        company = None
        tracking_number = None
        pickup_code = None
        
        for company_keyword, company_name in self.EXPRESS_COMPANIES.items():
            if company_keyword.lower() in text.lower():
                company = company_name
                break
        
        for pattern in self.EXPRESS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                for i, g in enumerate(groups):
                    if g and len(g) >= 4:
                        if re.match(r'^[A-Za-z0-9]{8,}$', g):
                            tracking_number = g
                        elif re.match(r'^\d{4,8}$', g):
                            pickup_code = g
                
                if not company:
                    for g in groups:
                        if g in self.EXPRESS_COMPANIES:
                            company = self.EXPRESS_COMPANIES[g]
                            break
        
        code_match = re.search(r"取件码[：:]?\s*(\d{4,8})", text)
        if code_match:
            pickup_code = code_match.group(1)
        
        tracking_match = re.search(r"单号[：:]?\s*([A-Za-z0-9]{8,})", text)
        if tracking_match:
            tracking_number = tracking_match.group(1)
        
        if company or tracking_number or pickup_code:
            return ExpressInfo(
                company=company or "未知快递",
                tracking_number=tracking_number,
                pickup_code=pickup_code,
                raw_text=text
            )
        
        return None
    
    def _parse_verification_code(self, text: str) -> Optional[VerificationCodeInfo]:
        """解析验证码"""
        for pattern in self.VERIFICATION_CODE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                
                service = None
                service_patterns = [
                    (r"(\S+).*验证码", "prefix"),
                    (r"验证码.*?(\S+)", "suffix"),
                    (r"【(.+?)】", "brackets"),
                ]
                
                for sp, mode in service_patterns:
                    sm = re.search(sp, text)
                    if sm:
                        service = sm.group(1)
                        break
                
                return VerificationCodeInfo(
                    code=code,
                    service=service,
                    raw_text=text
                )
        
        return None
    
    def _parse_bank_sms(self, text: str) -> Optional[BankSmsInfo]:
        """解析银行短信"""
        card_tail = None
        amount = None
        balance = None
        transaction_type = None
        merchant = None
        time_match = re.search(r"(\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s\d{2}:\d{2})", text)
        time_str = time_match.group(1) if time_match else None
        
        tail_match = re.search(r"尾号(\d{4})", text)
        if tail_match:
            card_tail = tail_match.group(1)
        
        for t_type, patterns in self.BANK_SMS_PATTERNS.items():
            if t_type in ["consumption", "deposit"]:
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        groups = match.groups()
                        if len(groups) >= 2:
                            card_tail = groups[0] if len(groups[0]) == 4 else card_tail
                            amount = float(groups[1])
                            transaction_type = "支出" if t_type == "consumption" else "收入"
                        break
            elif t_type == "balance":
                for pattern in patterns:
                    match = re.search(pattern, text)
                    if match:
                        balance = float(match.group(1))
                        break
        
        merchant_match = re.search(r"商户[：:]\s*(.+?)(?:\s|$|，|。)", text)
        if merchant_match:
            merchant = merchant_match.group(1).strip()
        
        if card_tail or amount or balance:
            return BankSmsInfo(
                card_tail=card_tail,
                amount=amount,
                balance=balance,
                transaction_type=transaction_type,
                merchant=merchant,
                time=time_str,
                raw_text=text
            )
        
        return None
    
    def _is_amount(self, text: str) -> bool:
        """判断字符串是否为金额"""
        try:
            float(text)
            return True
        except (ValueError, TypeError):
            return False
    
    def parse_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """批量解析通知"""
        return [self.parse(text) for text in texts]
    
    def get_payment_notifications(self, texts: List[str]) -> List[Dict[str, Any]]:
        """筛选支付通知"""
        results = []
        for text in texts:
            result = self.parse(text)
            if result["type"] == NotificationType.PAYMENT.value:
                results.append(result)
        return results
    
    def get_express_notifications(self, texts: List[str]) -> List[Dict[str, Any]]:
        """筛选快递通知"""
        results = []
        for text in texts:
            result = self.parse(text)
            if result["type"] == NotificationType.EXPRESS.value:
                results.append(result)
        return results
    
    def get_verification_codes(self, texts: List[str]) -> List[Dict[str, Any]]:
        """筛选验证码"""
        results = []
        for text in texts:
            result = self.parse(text)
            if result["type"] == NotificationType.VERIFICATION_CODE.value:
                results.append(result)
        return results


notification_parser = NotificationParserService()


async def parse_notification(text: str) -> Dict[str, Any]:
    """解析单个通知"""
    return notification_parser.parse(text)


async def parse_notifications(texts: List[str]) -> List[Dict[str, Any]]:
    """批量解析通知"""
    return notification_parser.parse_batch(texts)


async def get_payment_info(text: str) -> Optional[Dict[str, Any]]:
    """获取支付信息"""
    result = notification_parser.parse(text)
    if result["type"] == NotificationType.PAYMENT.value:
        return result["data"]
    return None


async def get_express_info(text: str) -> Optional[Dict[str, Any]]:
    """获取快递信息"""
    result = notification_parser.parse(text)
    if result["type"] == NotificationType.EXPRESS.value:
        return result["data"]
    return None


async def get_verification_code(text: str) -> Optional[str]:
    """获取验证码"""
    result = notification_parser.parse(text)
    if result["type"] == NotificationType.VERIFICATION_CODE.value:
        return result["data"]["code"]
    return None