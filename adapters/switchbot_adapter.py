"""
🔌 SwitchBot 设备适配器
通过 SwitchBot API 控制蓝牙/WiFi 智能设备。

支持设备：
- SwitchBot Bot (按键机器人)
- SwitchBot Curtain (智能窗帘)
- SwitchBot Plug (智能插座)
- SwitchBot Light Strip (灯带)
- SwitchBot Meter (温湿度计)

使用方式：
  from adapters.switchbot_adapter import SwitchBotAdapter, get_switchbot
  sb = get_switchbot()
  sb.turn_on("device_id")
"""

import os
import json
import time
import threading
import logging

logger = logging.getLogger(__name__)


class SwitchBotAdapter:
    """SwitchBot 设备适配器"""

    API_BASE = "https://api.switch-bot.com/v1.1"

    def __init__(self, token=None, secret=None):
        self.token = token or os.getenv("SWITCHBOT_TOKEN", "")
        self.secret = secret or os.getenv("SWITCHBOT_SECRET", "")
        self._devices = {}  # device_id → device_info
        self._scenes = {}   # scene_id → scene_info
        self._last_refresh = 0
        self._refresh_interval = 300  # 5 分钟缓存

    @property
    def configured(self) -> bool:
        return bool(self.token)

    def _headers(self) -> dict:
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
        }

    def _request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """发送 API 请求"""
        import urllib.request
        url = f"{self.API_BASE}{endpoint}"
        headers = self._headers()

        if data:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers=headers,
                method=method,
            )
        else:
            req = urllib.request.Request(url, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"statusCode": 500, "message": str(e)}

    def refresh_devices(self) -> list:
        """刷新设备列表"""
        if not self.configured:
            return []

        result = self._request("GET", "/devices")
        if result.get("statusCode") == 100:
            devices = result.get("body", {}).get("deviceList", [])
            self._devices = {d["deviceId"]: d for d in devices}
            self._last_refresh = time.time()
            return devices

        logger.error(f"[SwitchBot] 获取设备列表失败: {result.get('message')}")
        return []

    def refresh_scenes(self) -> list:
        """刷新场景列表"""
        if not self.configured:
            return []

        result = self._request("GET", "/scenes")
        if result.get("statusCode") == 100:
            scenes = result.get("body", {}).get("sceneList", [])
            self._scenes = {s["sceneId"]: s for s in scenes}
            return scenes

        return []

    def list_devices(self) -> list:
        """列出所有设备"""
        if time.time() - self._last_refresh > self._refresh_interval:
            self.refresh_devices()
        return [
            {
                "device_id": d["deviceId"],
                "name": d.get("deviceName", ""),
                "type": d.get("deviceType", ""),
                "hub": d.get("hubDeviceId", ""),
            }
            for d in self._devices.values()
        ]

    def get_device_status(self, device_id: str) -> dict:
        """获取设备状态"""
        result = self._request("GET", f"/devices/{device_id}/status")
        if result.get("statusCode") == 100:
            return result.get("body", {})
        return {"error": result.get("message", "未知错误")}

    def send_command(self, device_id: str, command: str, parameter: str = "default",
                     command_type: str = "command") -> dict:
        """
        发送控制指令。

        command: turnOn / turnOff / toggle / pause / setBrightness / ...
        parameter: default / 0-255 / etc
        command_type: command / commandCustom
        """
        payload = {
            "command": command,
            "parameter": parameter,
            "commandType": command_type,
        }
        result = self._request("POST", f"/devices/{device_id}/commands", payload)
        if result.get("statusCode") == 100:
            return {"success": True, "message": result.get("body", {}).get("message", "OK")}
        return {"success": False, "message": result.get("message", "未知错误")}

    def execute_scene(self, scene_id: str) -> dict:
        """执行场景"""
        result = self._request("POST", f"/scenes/{scene_id}/execute")
        if result.get("statusCode") == 100:
            return {"success": True}
        return {"success": False, "message": result.get("message", "未知错误")}

    # ─────────── 便捷方法 ───────────

    def turn_on(self, device_id: str) -> dict:
        return self.send_command(device_id, "turnOn")

    def turn_off(self, device_id: str) -> dict:
        return self.send_command(device_id, "turnOff")

    def toggle(self, device_id: str) -> dict:
        return self.send_command(device_id, "toggle")

    def set_brightness(self, device_id: str, brightness: int) -> dict:
        """设置亮度 (0-100)"""
        if not 0 <= brightness <= 100:
            return {"success": False, "message": "亮度范围 0-100"}
        return self.send_command(device_id, "setBrightness", str(brightness))

    def set_color(self, device_id: str, r: int, g: int, b: int) -> dict:
        """设置颜色 (RGB 0-255)"""
        color = f"{r:02x}{g:02x}{b:02x}"
        return self.send_command(device_id, "setColor", color)

    def curtain_open(self, device_id: str) -> dict:
        return self.send_command(device_id, "fullyOpen")

    def curtain_close(self, device_id: str) -> dict:
        return self.send_command(device_id, "fullyClose")

    def curtain_position(self, device_id: str, position: int) -> dict:
        """设置窗帘位置 (0-100, 0=全关, 100=全开)"""
        if not 0 <= position <= 100:
            return {"success": False, "message": "位置范围 0-100"}
        index = f"{index},0,ff"  # 暂不使用多帘
        return self.send_command(device_id, "setPosition", f"{position},0,ff")


# ─────────── 单例 ───────────

_switchbot_instance = None


def get_switchbot() -> SwitchBotAdapter:
    global _switchbot_instance
    if _switchbot_instance is None:
        _switchbot_instance = SwitchBotAdapter()
    return _switchbot_instance
