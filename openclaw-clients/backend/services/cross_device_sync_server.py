"""
跨设备协同 WebSocket 服务
支持设备注册、实时通信、数据同步
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import logging

# 延迟导入可选依赖，避免启动警告
websockets = None
WebSocketServerProtocol = None

def try_import_dependencies():
    """尝试导入可选依赖，仅在使用时导入"""
    global websockets, WebSocketServerProtocol
    if websockets is None:
        try:
            import websockets
            from websockets.server import WebSocketServerProtocol as WSSP
            WebSocketServerProtocol = WSSP
        except ImportError:
            websockets = None
            WebSocketServerProtocol = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CrossDeviceSync")


@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    device_name: str
    device_type: str = "phone"
    user_id: Optional[str] = None
    family_id: Optional[str] = None
    websocket: Optional[WebSocketServerProtocol] = None
    last_seen: float = field(default_factory=time.time)
    app_version: str = "1.0"
    os_version: str = ""
    status: str = "online"

    def to_dict(self) -> dict:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "user_id": self.user_id,
            "family_id": self.family_id,
            "last_seen": self.last_seen,
            "status": self.status,
            "app_version": self.app_version,
            "os_version": self.os_version
        }


class CrossDeviceSyncServer:
    """跨设备协同服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port

        # 设备管理
        self.devices: Dict[str, DeviceInfo] = {}  # device_id -> DeviceInfo
        self.user_devices: Dict[str, Set[str]] = {}  # user_id -> set of device_ids
        self.family_devices: Dict[str, Set[str]] = {}  # family_id -> set of device_ids

        # 数据版本控制
        self.data_versions: Dict[str, Dict[str, int]] = {}  # {data_type: {device_id: version}}
        self.data_cache: Dict[str, Dict[int, dict]] = {}  # {data_type: {version: data}}

        # 心跳超时
        self.heartbeat_timeout = 120  # 秒

    async def start(self):
        """启动服务器"""
        if websockets is None:
            logger.error("websockets 未安装")
            return

        logger.info(f"启动跨设备协同服务器: ws://{self.host}:{self.port}")

        # 启动心跳检查任务
        asyncio.create_task(self.heartbeat_checker())

        async with websockets.serve(self.handle_connection, self.host, self.port):
            await asyncio.Future()  # 永远运行

    async def handle_connection(self, websocket: WebSocketServerProtocol, path: str = ""):
        """处理 WebSocket 连接"""
        device_id = None

        try:
            # 解析请求头获取设备信息
            device_id = websocket.request_headers.get("X-Device-Id", None)
            device_name = websocket.request_headers.get("X-Device-Name", "Unknown")
            device_type = websocket.request_headers.get("X-Device-Type", "phone")
            user_id = websocket.request_headers.get("X-User-Id", None)
            family_id = websocket.request_headers.get("X-Family-Id", None)

            if not device_id:
                await websocket.close(4000, "缺少设备ID")
                return

            # 注册设备
            device = DeviceInfo(
                device_id=device_id,
                device_name=device_name,
                device_type=device_type,
                user_id=user_id,
                family_id=family_id,
                websocket=websocket,
                status="online"
            )

            self.register_device(device)

            # 发送欢迎消息
            await self.send_message(websocket, {
                "type": "welcome",
                "device_id": device_id,
                "server_time": datetime.now().isoformat()
            })

            # 通知其他设备有新设备上线
            await self.broadcast_device_online(device)

            # 处理消息
            async for message in websocket:
                await self.handle_message(device, message)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"设备断开连接: {device_id}")
        except Exception as e:
            logger.error(f"处理连接错误: {e}")
        finally:
            if device_id:
                await self.unregister_device(device_id)

    def register_device(self, device: DeviceInfo):
        """注册设备"""
        self.devices[device.device_id] = device

        # 用户-设备映射
        if device.user_id:
            if device.user_id not in self.user_devices:
                self.user_devices[device.user_id] = set()
            self.user_devices[device.user_id].add(device.device_id)

        # 家庭-设备映射
        if device.family_id:
            if device.family_id not in self.family_devices:
                self.family_devices[device.family_id] = set()
            self.family_devices[device.family_id].add(device.device_id)

        logger.info(f"设备注册: {device.device_name} ({device.device_id})")

    async def unregister_device(self, device_id: str):
        """注销设备"""
        device = self.devices.pop(device_id, None)
        if device:
            device.status = "offline"

            # 从用户映射中移除
            if device.user_id and device.user_id in self.user_devices:
                self.user_devices[device.user_id].discard(device_id)

            # 从家庭映射中移除
            if device.family_id and device.family_id in self.family_devices:
                self.family_devices[device.family_id].discard(device_id)

            # 通知其他设备
            await self.broadcast_device_offline(device_id)

            logger.info(f"设备注销: {device.device_name} ({device_id})")

    async def handle_message(self, device: DeviceInfo, message: str):
        """处理消息"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            # 更新最后活跃时间
            device.last_seen = time.time()

            if msg_type == "register":
                await self.handle_register(device, data)

            elif msg_type == "sync_data":
                await self.handle_sync_data(device, data)

            elif msg_type == "sync_request":
                await self.handle_sync_request(device, data)

            elif msg_type == "initial_sync":
                await self.handle_initial_sync(device, data)

            elif msg_type == "device_message":
                await self.handle_device_message(device, data)

            elif msg_type == "broadcast":
                await self.handle_broadcast(device, data)

            elif msg_type == "ping":
                await self.send_message(device.websocket, {"type": "pong"})

            else:
                logger.warning(f"未知消息类型: {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"无效JSON: {message[:100]}")
        except Exception as e:
            logger.error(f"处理消息错误: {e}")

    async def handle_register(self, device: DeviceInfo, data: dict):
        """处理设备注册"""
        device_info = data.get("device", {})
        device.device_name = device_info.get("device_name", device.device_name)
        device.app_version = device_info.get("app_version", "1.0")
        device.os_version = device_info.get("os_version", "")

        logger.info(f"设备更新注册信息: {device.device_name}")

    async def handle_sync_data(self, device: DeviceInfo, data: dict):
        """处理数据同步"""
        data_type = data.get("data_type")
        sync_data = data.get("data")
        version = data.get("version", 1)
        target_device = data.get("target_device")

        # 存储数据版本
        if data_type not in self.data_versions:
            self.data_versions[data_type] = {}
        if data_type not in self.data_cache:
            self.data_cache[data_type] = {}

        self.data_versions[data_type][device.device_id] = version
        self.data_cache[data_type][version] = sync_data

        # 转发给目标设备或家庭内所有设备
        if target_device:
            target = self.devices.get(target_device)
            if target and target.websocket:
                await self.send_message(target.websocket, {
                    "type": "sync_data",
                    "data_type": data_type,
                    "data": sync_data,
                    "version": version,
                    "source_device": device.device_id
                })
        else:
            # 广播到家庭内所有设备
            await self.broadcast_to_family(device.family_id, {
                "type": "sync_data",
                "data_type": data_type,
                "data": sync_data,
                "version": version,
                "source_device": device.device_id
            }, exclude_device=device.device_id)

    async def handle_sync_request(self, device: DeviceInfo, data: dict):
        """处理同步请求"""
        data_type = data.get("data_type")

        # 获取该数据类型的最新版本
        versions = self.data_versions.get(data_type, {})
        if versions:
            max_version = max(versions.values())
            cached_data = self.data_cache.get(data_type, {}).get(max_version)

            if cached_data:
                await self.send_message(device.websocket, {
                    "type": "sync_data",
                    "data_type": data_type,
                    "data": cached_data,
                    "version": max_version,
                    "source_device": "server"
                })

    async def handle_initial_sync(self, device: DeviceInfo, data: dict):
        """处理初始同步请求"""
        data_types = data.get("data_types", [])

        sync_status = {}
        for data_type in data_types:
            versions = self.data_versions.get(data_type, {})
            if versions:
                sync_status[data_type] = {
                    "available": True,
                    "latest_version": max(versions.values())
                }
            else:
                sync_status[data_type] = {"available": False}

        await self.send_message(device.websocket, {
            "type": "initial_sync_response",
            "sync_status": sync_status
        })

    async def handle_device_message(self, device: DeviceInfo, data: dict):
        """处理设备间消息"""
        target_device_id = data.get("target_device")
        message_type = data.get("message_type")
        payload = data.get("payload")

        target_device = self.devices.get(target_device_id)
        if target_device and target_device.websocket:
            await self.send_message(target_device.websocket, {
                "type": "device_message",
                "from_device": device.device_id,
                "message_type": message_type,
                "payload": payload
            })
        else:
            # 目标设备离线，存储消息
            await self.send_message(device.websocket, {
                "type": "error",
                "message": f"目标设备 {target_device_id} 离线"
            })

    async def handle_broadcast(self, device: DeviceInfo, data: dict):
        """处理广播消息"""
        message_type = data.get("message_type")
        payload = data.get("payload")

        await self.broadcast_to_family(device.family_id, {
            "type": "device_message",
            "from_device": device.device_id,
            "message_type": message_type,
            "payload": payload
        }, exclude_device=device.device_id)

    async def broadcast_device_online(self, device: DeviceInfo):
        """广播设备上线"""
        await self.broadcast_to_family(device.family_id, {
            "type": "device_online",
            "device": device.to_dict()
        }, exclude_device=device.device_id)

    async def broadcast_device_offline(self, device_id: str):
        """广播设备离线"""
        device = self.devices.get(device_id)
        if device:
            await self.broadcast_to_family(device.family_id, {
                "type": "device_offline",
                "device_id": device_id
            })

    async def broadcast_to_family(self, family_id: Optional[str], message: dict,
                                   exclude_device: str = None):
        """广播到家庭内所有设备"""
        if not family_id or family_id not in self.family_devices:
            return

        device_ids = self.family_devices[family_id]
        for device_id in device_ids:
            if device_id == exclude_device:
                continue
            device = self.devices.get(device_id)
            if device and device.websocket:
                await self.send_message(device.websocket, message)

    async def send_message(self, websocket: WebSocketServerProtocol, message: dict):
        """发送消息"""
        try:
            await websocket.send(json.dumps(message))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")

    async def heartbeat_checker(self):
        """心跳检查任务"""
        while True:
            await asyncio.sleep(30)  # 每30秒检查一次

            current_time = time.time()
            offline_devices = []

            for device_id, device in self.devices.items():
                if current_time - device.last_seen > self.heartbeat_timeout:
                    offline_devices.append(device_id)

            for device_id in offline_devices:
                logger.info(f"设备心跳超时: {device_id}")
                await self.unregister_device(device_id)

    def get_online_devices(self) -> List[dict]:
        """获取在线设备列表"""
        return [d.to_dict() for d in self.devices.values() if d.status == "online"]

    def get_stats(self) -> dict:
        """获取服务器统计"""
        return {
            "total_devices": len(self.devices),
            "online_devices": sum(1 for d in self.devices.values() if d.status == "online"),
            "total_users": len(self.user_devices),
            "total_families": len(self.family_devices),
            "data_types": list(self.data_versions.keys())
        }


# Flask 集成
def create_sync_blueprint():
    """创建 Flask 蓝图"""
    from flask import Blueprint, jsonify, request

    bp = Blueprint('cross_device_sync', __name__)

    # 全局服务器实例（需要在主应用中初始化）
    sync_server = None

    @bp.route('/devices', methods=['GET'])
    def get_devices():
        """获取在线设备列表"""
        if sync_server:
            return jsonify({"success": True, "devices": sync_server.get_online_devices()})
        return jsonify({"success": False, "error": "服务未启动"})

    @bp.route('/stats', methods=['GET'])
    def get_stats():
        """获取服务器统计"""
        if sync_server:
            return jsonify({"success": True, "stats": sync_server.get_stats()})
        return jsonify({"success": False, "error": "服务未启动"})

    @bp.route('/sync/<data_type>', methods=['POST'])
    def sync_data(data_type):
        """同步数据"""
        data = request.get_json()
        # 存储数据
        return jsonify({"success": True})

    return bp


# 启动服务器
async def main():
    server = CrossDeviceSyncServer(host="0.0.0.0", port=8765)
    await server.start()


if __name__ == "__main__":
    if websockets:
        asyncio.run(main())
    else:
        logger.info("请先安装 websockets: pip install websockets")