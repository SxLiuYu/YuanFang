"""通知数据采集器"""

import re
import random
from datetime import datetime
from typing import Dict, Any, List, Optional


class NotificationCollector:
    """
    通知数据采集器
    
    在真实App中，这里会调用:
    - Android: NotificationListenerService
    - iOS: 无法直接访问通知
    
    目前提供模拟数据用于测试
    """
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        
        # 支付App包名/标识
        self.payment_apps = {
            'com.alibaba.android.rimet': '钉钉',
            'com.eg.android.AlipayGphone': '支付宝',
            'com.tencent.mm': '微信',
            'com.jd.pingou': '京东',
            'com.meituan': '美团',
        }
    
    def process_notification(self, package_name: str, title: str, text: str) -> Dict[str, Any]:
        """
        处理通知
        
        Args:
            package_name: 应用包名
            title: 通知标题
            text: 通知内容
        
        Returns:
            处理结果
        """
        notification = {
            'package': package_name,
            'title': title,
            'text': text,
            'timestamp': datetime.now().isoformat()
        }
        
        self.notifications.append(notification)
        
        # 检测是否是支付通知
        payment_info = self._extract_payment_info(title, text)
        if payment_info:
            notification['type'] = 'payment'
            notification['payment_info'] = payment_info
            return notification
        
        notification['type'] = 'general'
        return notification
    
    def _extract_payment_info(self, title: str, text: str) -> Optional[Dict[str, Any]]:
        """
        从通知中提取支付信息
        
        Args:
            title: 通知标题
            text: 通知内容
        
        Returns:
            支付信息或None
        """
        combined = f"{title} {text}"
        
        # 支付宝支付成功
        # 示例: "支付宝" "你通过扫码向XXX付款50.00元"
        alipay_pattern = r'付款(\d+\.?\d*)元'
        match = re.search(alipay_pattern, combined)
        if match:
            return {
                'amount': float(match.group(1)),
                'merchant': self._extract_merchant(combined),
                'type': 'expense',
                'platform': 'alipay'
            }
        
        # 微信支付
        # 示例: "微信支付" "你向XXX付款50.00元"
        wechat_pattern = r'付款(\d+\.?\d*)元'
        match = re.search(wechat_pattern, combined)
        if match:
            return {
                'amount': float(match.group(1)),
                'merchant': self._extract_merchant(combined),
                'type': 'expense',
                'platform': 'wechat'
            }
        
        # 银行卡消费
        # 示例: "招商银行" "您尾号1234的卡消费50.00元"
        bank_pattern = r'消费(\d+\.?\d*)元'
        match = re.search(bank_pattern, combined)
        if match:
            return {
                'amount': float(match.group(1)),
                'merchant': self._extract_merchant(combined),
                'type': 'expense',
                'platform': 'bank'
            }
        
        return None
    
    def _extract_merchant(self, text: str) -> str:
        """提取商户名称"""
        # 简单的商户提取逻辑
        patterns = [
            r'向(.+?)付款',
            r'在(.+?)消费',
            r'(.+?)支付成功',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return '未知商户'
    
    def simulate_payment_notification(self, amount: float, merchant: str) -> Dict[str, Any]:
        """
        模拟支付通知（用于测试）
        
        Args:
            amount: 金额
            merchant: 商户
        
        Returns:
            模拟的通知
        """
        title = "支付宝"
        text = f"你通过扫码向{merchant}付款{amount:.2f}元"
        
        return self.process_notification(
            'com.eg.android.AlipayGphone',
            title,
            text
        )
    
    def get_payment_notifications(self) -> List[Dict[str, Any]]:
        """获取所有支付通知"""
        return [n for n in self.notifications if n.get('type') == 'payment']