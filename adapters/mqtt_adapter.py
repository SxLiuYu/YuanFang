# adapters/mqtt_adapter.py
"""
MQTT 适配器 · MQTT Adapter
支持 MQTT 设备双向通信
"""
import os
import json
import logging
import threading
from typing import Optional, Callable

logger = logging.getLogger(__name__)

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed, MQTT adapter unavailable")


class MQTTAdapter:
    """
    MQTT 客户端适配器
    功能：
    - 连接 MQTT Broker
    - 订阅设备 topic
    - 发布设备命令
    - 设备状态回调
    """

    def __init__(self, host: str = None, port: int = 1883,
                 username: str = None, password: str = None):
        self.host = host or os.getenv("MQTT_HOST", "localhost")
        self.port = port or int(os.getenv("MQTT_PORT", "1883"))
        self.username = username or os.getenv("MQTT_USERNAME", "")
        self.password = password or os.getenv("MQTT_PASSWORD", "")
        self._client: Optional["mqtt.Client"] = None
        self._devices: dict[str, dict] = {}
        self._callbacks: dict[str, Callable] = {}
        self._connected = False

    def connect(self, timeout: int = 5) -> bool:
        if not MQTT_AVAILABLE:
            logger.warning("MQTT library not available")
            return False

        try:
            self._client = mqtt.Client()
            if self.username:
                self._client.username_pw_set(self.username, self.password)
            self._client.on_connect = self._on_connect
            self._client.on_message = self._on_message
            self._client.on_disconnect = self._on_disconnect
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            self._connected = True
            logger.info(f"[MQTT] Connected to {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"[MQTT] Connect failed: {e}")
            return False

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("[MQTT] Connected")
            for topic in self._devices:
                client.subscribe(topic)
        else:
            logger.warning(f"[MQTT] Connect failed, rc={rc}")

    def _on_disconnect(self, client, userdata, rc):
        logger.warning(f"[MQTT] Disconnected, rc={rc}")
        self._connected = False

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            topic = msg.topic
            logger.debug(f"[MQTT] {topic}: {payload}")
            # Update device state
            if topic in self._devices:
                self._devices[topic].update(payload)
            # Call callback
            if topic in self._callbacks:
                self._callbacks[topic](payload)
        except Exception as e:
            logger.warning(f"[MQTT] Message parse error: {e}")

    def subscribe(self, topic: str, callback: Callable = None):
        """订阅设备 topic"""
        if topic not in self._devices:
            self._devices[topic] = {}
        if callback:
            self._callbacks[topic] = callback
        if self._client and self._connected:
            self._client.subscribe(topic)
            logger.info(f"[MQTT] Subscribed to {topic}")

    def publish(self, topic: str, payload: dict):
        """发布设备命令"""
        if not self._connected:
            logger.warning("[MQTT] Not connected")
            return False
        try:
            msg = json.dumps(payload, ensure_ascii=False)
            result = self._client.publish(topic, msg)
            logger.info(f"[MQTT] Published to {topic}: {payload}")
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"[MQTT] Publish failed: {e}")
            return False

    def get_state(self, topic: str) -> dict:
        """获取设备状态（缓存）"""
        return self._devices.get(topic, {})

    def list_devices(self) -> list[str]:
        """列出所有已知设备 topic"""
        return list(self._devices.keys())

    def load_devices_from_config(self, config_json: str):
        """从 JSON 配置加载设备列表"""
        try:
            devices = json.loads(config_json)
            for device in devices:
                topic = device.get("topic", "")
                if topic:
                    self.subscribe(topic)
                    self._devices[topic] = device
            logger.info(f"[MQTT] Loaded {len(devices)} devices")
        except Exception as e:
            logger.error(f"[MQTT] Config load failed: {e}")


_mqtt: Optional[MQTTAdapter] = None


def get_mqtt() -> Optional[MQTTAdapter]:
    global _mqtt
    if _mqtt is None:
        _mqtt = MQTTAdapter()
    return _mqtt
