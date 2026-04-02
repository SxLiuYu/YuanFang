"""
📡 MQTT 设备适配器
通过 MQTT 协议连接和控制智能家居设备。

支持场景：
- Tasmota / ESPHome 等开源固件设备
- 智能灯泡、插座、传感器（温湿度/人体/门磁）
- 自定义 MQTT 设备

使用方式：
  from adapters.mqtt_adapter import MQTTAdapter, get_mqtt
  mqtt = get_mqtt()
  mqtt.connect()
  mqtt.publish("cmnd/tasmota_XXX/Power", "ON")
"""

import os
import json
import time
import threading
import logging
from typing import Optional, Callable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class MQTTDevice:
    """MQTT 设备定义"""
    device_id: str
    name: str
    topic_set: str       # 控制主题 (e.g., "cmnd/tasmota_lamp/Power")
    topic_state: str     # 状态主题 (e.g., "stat/tasmota_lamp/POWER")
    topic_avail: str     # 在线状态主题 (e.g., "tele/tasmota_lamp/LWT")
    device_type: str = "switch"  # switch / light / sensor / binary_sensor
    payload_on: str = "ON"
    payload_off: str = "OFF"
    state: str = "unknown"
    available: bool = False
    metadata: dict = field(default_factory=dict)


class MQTTAdapter:
    """MQTT 设备适配器"""

    def __init__(self, host=None, port=None, username=None, password=None,
                 client_id=None):
        self.host = host or os.getenv("MQTT_HOST", "localhost")
        self.port = int(port or os.getenv("MQTT_PORT", "1883"))
        self.username = username or os.getenv("MQTT_USERNAME", "")
        self.password = password or os.getenv("MQTT_PASSWORD", "")
        self.client_id = client_id or f"yuanfang_{int(time.time())}"

        self._client = None
        self._connected = False
        self._devices = {}  # device_id → MQTTDevice
        self._message_callbacks = {}  # topic_pattern → callback
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self, timeout=10) -> bool:
        """连接 MQTT Broker"""
        try:
            import paho.mqtt.client as mqtt_client

            self._client = mqtt_client.Client(
                client_id=self.client_id,
                callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2,
            )

            if self.username and self.password:
                self._client.username_pw_set(self.username, self.password)

            def on_connect(client, userdata, flags, reason_code, properties=None):
                if reason_code == 0:
                    self._connected = True
                    print(f"[MQTT] 已连接到 {self.host}:{self.port}")
                    # 重新订阅
                    for topic in list(self._message_callbacks.keys()):
                        client.subscribe(topic)
                else:
                    print(f"[MQTT] 连接失败: {reason_code}")
                    self._connected = False

            def on_disconnect(client, userdata, reason_code, properties=None):
                self._connected = False
                print(f"[MQTT] 已断开: {reason_code}")

            def on_message(client, userdata, msg):
                self._handle_message(msg.topic, msg.payload.decode("utf-8", errors="ignore"))

            self._client.on_connect = on_connect
            self._client.on_disconnect = on_disconnect
            self._client.on_message = on_message

            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()

            # 等待连接
            deadline = time.time() + timeout
            while time.time() < deadline and not self._connected:
                time.sleep(0.1)

            return self._connected

        except ImportError:
            print("[MQTT] paho-mqtt 未安装 (pip install paho-mqtt)")
            return False
        except Exception as e:
            logger.error(f"[MQTT] 连接失败: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def register_device(self, device: MQTTDevice):
        """注册 MQTT 设备"""
        with self._lock:
            self._devices[device.device_id] = device
            # 订阅状态主题
            if device.topic_state:
                self._message_callbacks[device.topic_state] = self._device_state_update
                if self._connected and self._client:
                    self._client.subscribe(device.topic_state)
            if device.topic_avail:
                self._message_callbacks[device.topic_avail] = self._device_avail_update
                if self._connected and self._client:
                    self._client.subscribe(device.topic_avail)

    def register_device_from_dict(self, data: dict):
        """从字典注册设备"""
        device = MQTTDevice(
            device_id=data["device_id"],
            name=data.get("name", data["device_id"]),
            topic_set=data["topic_set"],
            topic_state=data.get("topic_state", ""),
            topic_avail=data.get("topic_avail", ""),
            device_type=data.get("device_type", "switch"),
            payload_on=data.get("payload_on", "ON"),
            payload_off=data.get("payload_off", "OFF"),
            metadata=data.get("metadata", {}),
        )
        self.register_device(device)

    def _device_state_update(self, topic: str, payload: str):
        """处理设备状态更新"""
        for device in self._devices.values():
            if device.topic_state == topic:
                device.state = payload
                break

    def _device_avail_update(self, topic: str, payload: str):
        """处理设备在线状态"""
        for device in self._devices.values():
            if device.topic_avail == topic:
                device.available = payload.lower() not in ("offline", "dead", "lost")
                break

    def _handle_message(self, topic: str, payload: str):
        """处理收到的 MQTT 消息"""
        # 精确匹配
        if topic in self._message_callbacks:
            self._message_callbacks[topic](topic, payload)
            return

        # 通配符匹配
        for pattern, callback in self._message_callbacks.items():
            if self._topic_match(pattern, topic):
                callback(topic, payload)
                return

    @staticmethod
    def _topic_match(pattern: str, topic: str) -> bool:
        """简单 MQTT 主题通配符匹配（支持 + 和 #）"""
        pattern_parts = pattern.split("/")
        topic_parts = topic.split("/")
        if len(pattern_parts) != len(topic_parts) and pattern_parts[-1] != "#":
            return False
        for p, t in zip(pattern_parts, topic_parts):
            if p == "#":
                return True
            if p != "+" and p != t:
                return False
        return len(pattern_parts) == len(topic_parts)

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        """发布消息"""
        if not self._connected or not self._client:
            logger.warning(f"[MQTT] 未连接，无法发布到 {topic}")
            return False
        try:
            result = self._client.publish(topic, payload, qos=qos, retain=retain)
            return result.rc == 0
        except Exception as e:
            logger.error(f"[MQTT] 发布失败: {e}")
            return False

    def subscribe(self, topic: str, callback: Callable):
        """订阅主题并注册回调"""
        self._message_callbacks[topic] = callback
        if self._connected and self._client:
            self._client.subscribe(topic)

    # ─────────── 设备控制接口（HA 兼容风格） ───────────

    def turn_on(self, device_id: str) -> dict:
        """打开设备"""
        device = self._devices.get(device_id)
        if not device:
            return {"success": False, "error": f"设备 {device_id} 不存在"}
        ok = self.publish(device.topic_set, device.payload_on)
        if ok:
            device.state = device.payload_on
        return {"success": ok, "device": device_id, "state": device.payload_on}

    def turn_off(self, device_id: str) -> dict:
        """关闭设备"""
        device = self._devices.get(device_id)
        if not device:
            return {"success": False, "error": f"设备 {device_id} 不存在"}
        ok = self.publish(device.topic_set, device.payload_off)
        if ok:
            device.state = device.payload_off
        return {"success": ok, "device": device_id, "state": device.payload_off}

    def set_state(self, device_id: str, value: str) -> dict:
        """设置设备状态（通用）"""
        device = self._devices.get(device_id)
        if not device:
            return {"success": False, "error": f"设备 {device_id} 不存在"}
        ok = self.publish(device.topic_set, value)
        if ok:
            device.state = value
        return {"success": ok, "device": device_id, "state": value}

    def get_state(self, device_id: str) -> dict:
        """获取设备状态"""
        device = self._devices.get(device_id)
        if not device:
            return {"error": f"设备 {device_id} 不存在"}
        return {
            "device_id": device.device_id,
            "name": device.name,
            "type": device.device_type,
            "state": device.state,
            "available": device.available,
        }

    def list_devices(self) -> list:
        """列出所有注册的设备"""
        return [
            {
                "device_id": d.device_id,
                "name": d.name,
                "type": d.device_type,
                "state": d.state,
                "available": d.available,
            }
            for d in self._devices.values()
        ]

    def load_devices_from_config(self, config_path: str):
        """从 JSON 配置文件批量加载设备"""
        from pathlib import Path
        path = Path(config_path)
        if not path.exists():
            logger.warning(f"[MQTT] 配置文件不存在: {config_path}")
            return 0

        try:
            data = json.loads(path.read_text("utf-8"))
            devices = data if isinstance(data, list) else data.get("devices", [])
            count = 0
            for d in devices:
                if "device_id" in d and "topic_set" in d:
                    self.register_device_from_dict(d)
                    count += 1
            logger.info(f"[MQTT] 从配置加载了 {count} 个设备")
            return count
        except Exception as e:
            logger.error(f"[MQTT] 加载配置失败: {e}")
            return 0


# ─────────── 单例 ───────────

_mqtt_instance = None


def get_mqtt() -> MQTTAdapter:
    global _mqtt_instance
    if _mqtt_instance is None:
        _mqtt_instance = MQTTAdapter()
    return _mqtt_instance
