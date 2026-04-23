"""
设备认证服务
支持设备注册、确认码生成、飞书通知、令牌管理
"""

import logging
import secrets
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from flask import Blueprint, request, jsonify

logger = logging.getLogger("DeviceAuth")


@dataclass
class PendingConfirmation:
    """待确认的设备"""
    device_id: str
    device_name: str
    device_model: str
    confirm_code: str
    temp_id: str
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime = field(default_factory=lambda: datetime.now() + timedelta(minutes=5))
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


@dataclass
class ConfirmedDevice:
    """已确认的设备"""
    device_id: str
    device_name: str
    device_model: str
    token: str
    confirmed_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)


class DeviceAuthService:
    """设备认证服务"""
    
    CONFIRMATION_CODE_LENGTH = 6
    TOKEN_LENGTH = 32
    CONFIRMATION_EXPIRY_MINUTES = 5
    
    def __init__(self, feishu_webhook: Optional[str] = None):
        self.feishu_webhook = feishu_webhook
        
        # 内存存储（生产环境建议使用 Redis）
        self.pending_confirmations: Dict[str, PendingConfirmation] = {}  # temp_id -> PendingConfirmation
        self.confirmed_devices: Dict[str, ConfirmedDevice] = {}  # device_id -> ConfirmedDevice
        self.tokens: Dict[str, str] = {}  # token -> device_id
        
        logger.info("设备认证服务已初始化")
    
    def set_feishu_webhook(self, webhook_url: str):
        """设置飞书 Webhook"""
        self.feishu_webhook = webhook_url
        logger.info(f"飞书 Webhook 已设置")
    
    def generate_confirm_code(self) -> str:
        """生成 6 位确认码"""
        return ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') 
                      for _ in range(self.CONFIRMATION_CODE_LENGTH))
    
    def generate_temp_id(self) -> str:
        """生成临时 ID"""
        return secrets.token_urlsafe(16)
    
    def generate_token(self) -> str:
        """生成永久令牌"""
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    def register_device(self, device_id: str, device_name: str, device_model: str) -> Dict:
        """
        注册或登录设备
        
        Returns:
            {
                "confirmed": bool,
                "token": str (如果已确认),
                "status": str ("pending" 如果待确认),
                "temp_id": str (如果待确认)
            }
        """
        # 检查设备是否已确认
        if device_id in self.confirmed_devices:
            device = self.confirmed_devices[device_id]
            device.last_seen = datetime.now()
            logger.info(f"设备已确认: {device_name} ({device_id})")
            return {
                "confirmed": True,
                "token": device.token,
                "device_name": device.device_name
            }
        
        # 清理过期的确认请求
        self._cleanup_expired()
        
        # 检查是否已有待确认请求
        for temp_id, pending in self.pending_confirmations.items():
            if pending.device_id == device_id and not pending.is_expired():
                logger.info(f"设备已有待确认请求: {device_name} ({device_id})")
                return {
                    "confirmed": False,
                    "status": "pending",
                    "temp_id": temp_id,
                    "message": "请查看飞书获取确认码"
                }
        
        # 创建新的确认请求
        temp_id = self.generate_temp_id()
        confirm_code = self.generate_confirm_code()
        
        pending = PendingConfirmation(
            device_id=device_id,
            device_name=device_name,
            device_model=device_model,
            confirm_code=confirm_code,
            temp_id=temp_id
        )
        
        self.pending_confirmations[temp_id] = pending
        
        # 发送飞书通知
        self._send_feishu_notification(device_name, confirm_code)
        
        logger.info(f"新设备注册请求: {device_name} ({device_id}), 确认码: {confirm_code}")
        
        return {
            "confirmed": False,
            "status": "pending",
            "temp_id": temp_id,
            "message": "请查看飞书获取确认码"
        }
    
    def confirm_device(self, temp_id: str, confirm_code: str) -> Dict:
        """
        确认设备
        
        Returns:
            {
                "confirmed": bool,
                "token": str (如果成功),
                "message": str
            }
        """
        # 检查临时 ID 是否存在
        if temp_id not in self.pending_confirmations:
            logger.warning(f"无效的临时 ID: {temp_id}")
            return {
                "confirmed": False,
                "message": "无效的确认链接，请重新发起登录"
            }
        
        pending = self.pending_confirmations[temp_id]
        
        # 检查是否过期
        if pending.is_expired():
            del self.pending_confirmations[temp_id]
            logger.warning(f"确认码已过期: {temp_id}")
            return {
                "confirmed": False,
                "message": "确认码已过期，请重新发起登录"
            }
        
        # 验证确认码
        if pending.confirm_code.upper() != confirm_code.upper():
            logger.warning(f"确认码错误: {temp_id}, 输入: {confirm_code}, 正确: {pending.confirm_code}")
            return {
                "confirmed": False,
                "message": "确认码错误，请重新输入"
            }
        
        # 确认成功，生成永久令牌
        token = self.generate_token()
        
        device = ConfirmedDevice(
            device_id=pending.device_id,
            device_name=pending.device_name,
            device_model=pending.device_model,
            token=token
        )
        
        self.confirmed_devices[pending.device_id] = device
        self.tokens[token] = pending.device_id
        
        # 删除待确认记录
        del self.pending_confirmations[temp_id]
        
        # 发送成功通知
        self._send_feishu_success_notification(pending.device_name)
        
        logger.info(f"设备确认成功: {pending.device_name} ({pending.device_id})")
        
        return {
            "confirmed": True,
            "token": token,
            "device_name": pending.device_name,
            "message": "设备登录成功"
        }
    
    def check_device_status(self, device_id: str) -> Dict:
        """检查设备状态"""
        if device_id in self.confirmed_devices:
            device = self.confirmed_devices[device_id]
            device.last_seen = datetime.now()
            return {
                "confirmed": True,
                "device_name": device.device_name,
                "last_seen": device.last_seen.isoformat()
            }
        return {
            "confirmed": False,
            "message": "设备未注册"
        }
    
    def validate_token(self, token: str) -> Optional[str]:
        """验证令牌，返回设备 ID"""
        if token in self.tokens:
            device_id = self.tokens[token]
            if device_id in self.confirmed_devices:
                self.confirmed_devices[device_id].last_seen = datetime.now()
                return device_id
        return None
    
    def logout_device(self, device_id: str) -> bool:
        """设备登出"""
        if device_id in self.confirmed_devices:
            device = self.confirmed_devices[device_id]
            if device.token in self.tokens:
                del self.tokens[device.token]
            del self.confirmed_devices[device_id]
            logger.info(f"设备已登出: {device_id}")
            return True
        return False
    
    def _cleanup_expired(self):
        """清理过期的确认请求"""
        expired = [temp_id for temp_id, pending in self.pending_confirmations.items() 
                   if pending.is_expired()]
        for temp_id in expired:
            del self.pending_confirmations[temp_id]
            logger.debug(f"清理过期确认请求: {temp_id}")
    
    def _send_feishu_notification(self, device_name: str, confirm_code: str):
        """发送飞书确认码通知"""
        if not self.feishu_webhook:
            logger.warning("飞书 Webhook 未配置，跳过通知")
            return
        
        try:
            message = {
                "msg_type": "interactive",
                "card": {
                    "config": {
                        "wide_screen_mode": True
                    },
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": "🔐 设备登录确认"
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**设备名称：**{device_name}"
                            }
                        },
                        {
                            "tag": "div",
                            "text": {
                                "tag": "lark_md",
                                "content": f"**确认码：**`{confirm_code}`"
                            }
                        },
                        {
                            "tag": "note",
                            "elements": [
                                {
                                    "tag": "plain_text",
                                    "content": f"⏱️ 确认码有效期：{self.CONFIRMATION_EXPIRY_MINUTES} 分钟"
                                },
                                {
                                    "tag": "plain_text",
                                    "content": "请在应用中输入确认码完成登录"
                                }
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(
                self.feishu_webhook,
                json=message,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"飞书确认码通知已发送: {device_name}")
            else:
                logger.error(f"飞书通知发送失败: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"发送飞书通知失败: {e}")
    
    def _send_feishu_success_notification(self, device_name: str):
        """发送登录成功通知"""
        if not self.feishu_webhook:
            return
        
        try:
            message = {
                "msg_type": "text",
                "content": {
                    "text": f"✅ 设备登录成功\n设备：{device_name}\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            }
            
            requests.post(self.feishu_webhook, json=message, timeout=10)
            logger.info(f"登录成功通知已发送: {device_name}")
            
        except Exception as e:
            logger.error(f"发送成功通知失败: {e}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "pending_count": len(self.pending_confirmations),
            "confirmed_count": len(self.confirmed_devices),
            "devices": [
                {
                    "device_id": d.device_id,
                    "device_name": d.device_name,
                    "confirmed_at": d.confirmed_at.isoformat(),
                    "last_seen": d.last_seen.isoformat()
                }
                for d in self.confirmed_devices.values()
            ]
        }


# Flask 蓝图
def create_device_auth_blueprint(auth_service: DeviceAuthService) -> Blueprint:
    """创建设备认证 API 蓝图"""
    bp = Blueprint('device_auth', __name__, url_prefix='/device')
    
    @bp.route('/register', methods=['POST'])
    def register():
        """设备注册/登录"""
        try:
            data = request.get_json()
            
            device_id = data.get('device_id')
            device_name = data.get('device_name', 'Unknown Device')
            device_model = data.get('device_model', 'Unknown')
            
            if not device_id:
                return jsonify({
                    "success": False,
                    "error": "缺少 device_id"
                }), 400
            
            result = auth_service.register_device(device_id, device_name, device_model)
            
            return jsonify({
                "success": True,
                **result
            })
            
        except Exception as e:
            logger.error(f"设备注册失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/confirm', methods=['POST'])
    def confirm():
        """确认设备"""
        try:
            data = request.get_json()
            
            temp_id = data.get('temp_id')
            confirm_code = data.get('confirm_code')
            
            if not temp_id or not confirm_code:
                return jsonify({
                    "success": False,
                    "error": "缺少 temp_id 或 confirm_code"
                }), 400
            
            result = auth_service.confirm_device(temp_id, confirm_code)
            
            return jsonify({
                "success": result.get("confirmed", False),
                **result
            })
            
        except Exception as e:
            logger.error(f"设备确认失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    @bp.route('/status', methods=['GET'])
    def status():
        """检查设备状态"""
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({
                "success": False,
                "error": "缺少 device_id"
            }), 400
        
        result = auth_service.check_device_status(device_id)
        
        return jsonify({
            "success": True,
            **result
        })
    
    @bp.route('/stats', methods=['GET'])
    def stats():
        """获取统计信息"""
        return jsonify({
            "success": True,
            "stats": auth_service.get_stats()
        })
    
    @bp.route('/logout', methods=['POST'])
    def logout():
        """设备登出"""
        try:
            data = request.get_json()
            device_id = data.get('device_id')
            
            if not device_id:
                return jsonify({
                    "success": False,
                    "error": "缺少 device_id"
                }), 400
            
            success = auth_service.logout_device(device_id)
            
            return jsonify({
                "success": success,
                "message": "已登出" if success else "设备不存在"
            })
            
        except Exception as e:
            logger.error(f"设备登出失败: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    return bp


# 全局实例（可在主应用中配置）
device_auth_service = DeviceAuthService(
    feishu_webhook="https://open.feishu.cn/open-apis/bot/v2/hook/8c164cc1-e173-4011-a53c-75153147de7d"
)


# 使用示例
if __name__ == '__main__':
    # 测试设备注册
    result = device_auth_service.register_device(
        device_id="test-device-001",
        device_name="Test Windows PC",
        device_model="Windows 11"
    )
    print(f"注册结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    # 获取统计
    stats = device_auth_service.get_stats()
    print(f"统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")