"""
adapters/home_assistant_adapter.py
Home Assistant 适配器
让三省六部制可以控制智能家居设备
"""
import logging
import requests
import json
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)


class HomeAssistantAdapter:
    """
    Home Assistant 适配器
    提供简单的接口来控制智能家居设备
    """

    def __init__(self, host: str = "http://localhost:8123", token: str = None):
        """
        初始化 Home Assistant 适配器

        Args:
            host: Home Assistant 地址 (默认: http://localhost:8123)
            token: Home Assistant 长期访问令牌
        """
        self.host = host.rstrip("/")
        self.token = token
        self._session = requests.Session()
        if token:
            self._session.headers.update({
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            })
        logger.info(f"HomeAssistantAdapter 初始化: {host}")

    def health_check(self) -> bool:
        """检查 Home Assistant 是否可达"""
        try:
            response = self._session.get(f"{self.host}/api/", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Home Assistant 健康检查失败: {e}")
            return False

    def get_states(self) -> List[Dict[str, Any]]:
        """获取所有设备状态"""
        try:
            response = self._session.get(f"{self.host}/api/states", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取状态失败: {e}")
            return []

    def get_state(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """获取单个设备状态"""
        try:
            response = self._session.get(f"{self.host}/api/states/{entity_id}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"获取状态失败 {entity_id}: {e}")
            return None

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        调用 Home Assistant 服务

        Args:
            domain: 领域 (light, switch, climate, cover 等)
            service: 服务 (turn_on, turn_off, toggle, set_temperature 等)
            service_data: 服务数据 (可选)

        Returns:
            是否成功
        """
        try:
            payload = {}
            if service_data:
                payload.update(service_data)

            response = self._session.post(
                f"{self.host}/api/services/{domain}/{service}",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            logger.info(f"调用服务: {domain}.{service}")
            return True
        except Exception as e:
            logger.error(f"调用服务失败 {domain}.{service}: {e}")
            return False

    # ========== 灯光控制 ==========

    def light_turn_on(self, entity_id: str, brightness: int = None, color_temp: int = None, rgb_color: tuple = None) -> bool:
        """开灯"""
        service_data = {"entity_id": entity_id}
        if brightness is not None:
            service_data["brightness"] = brightness
        if color_temp is not None:
            service_data["color_temp"] = color_temp
        if rgb_color is not None:
            service_data["rgb_color"] = list(rgb_color)
        return self.call_service("light", "turn_on", service_data)

    def light_turn_off(self, entity_id: str) -> bool:
        """关灯"""
        return self.call_service("light", "turn_off", {"entity_id": entity_id})

    def light_toggle(self, entity_id: str) -> bool:
        """切换灯光"""
        return self.call_service("light", "toggle", {"entity_id": entity_id})

    # ========== 开关控制 ==========

    def switch_turn_on(self, entity_id: str) -> bool:
        """开开关"""
        return self.call_service("switch", "turn_on", {"entity_id": entity_id})

    def switch_turn_off(self, entity_id: str) -> bool:
        """关开关"""
        return self.call_service("switch", "turn_off", {"entity_id": entity_id})

    # ========== 空调/温度控制 ==========

    def climate_set_temperature(self, entity_id: str, temperature: float, hvac_mode: str = None) -> bool:
        """设置空调温度"""
        service_data = {"entity_id": entity_id, "temperature": temperature}
        if hvac_mode:
            service_data["hvac_mode"] = hvac_mode
        return self.call_service("climate", "set_temperature", service_data)

    def climate_set_hvac_mode(self, entity_id: str, hvac_mode: str) -> bool:
        """设置空调模式 (heat, cool, auto, off)"""
        return self.call_service("climate", "set_hvac_mode", {"entity_id": entity_id, "hvac_mode": hvac_mode})

    # ========== 窗帘控制 ==========

    def cover_open(self, entity_id: str) -> bool:
        """开窗帘"""
        return self.call_service("cover", "open_cover", {"entity_id": entity_id})

    def cover_close(self, entity_id: str) -> bool:
        """关窗帘"""
        return self.call_service("cover", "close_cover", {"entity_id": entity_id})

    def cover_set_position(self, entity_id: str, position: int) -> bool:
        """设置窗帘位置 (0-100)"""
        return self.call_service("cover", "set_cover_position", {"entity_id": entity_id, "position": position})

    # ========== 场景控制 ==========

    def scene_activate(self, scene_id: str) -> bool:
        """激活场景"""
        return self.call_service("scene", "turn_on", {"entity_id": scene_id})

    # ========== 快捷方法 ==========

    def activate_mood(self, mood: str) -> bool:
        """
        激活氛围模式

        Args:
            mood: 模式名称 (relax, work, movie, sleep 等)
        """
        mood_scenes = {
            "relax": "scene.放松模式",
            "work": "scene.工作模式",
            "movie": "scene.电影模式",
            "sleep": "scene.睡眠模式",
            "welcome": "scene.回家模式",
            "away": "scene.离家模式",
        }

        scene_id = mood_scenes.get(mood.lower())
        if scene_id:
            return self.scene_activate(scene_id)

        logger.warning(f"未知模式: {mood}")
        return False

    def get_device_summary(self) -> Dict[str, Any]:
        """获取设备摘要"""
        states = self.get_states()
        summary = {
            "total": len(states),
            "lights": [],
            "switches": [],
            "climates": [],
            "covers": [],
            "sensors": [],
            "others": [],
        }

        for state in states:
            entity_id = state.get("entity_id", "")
            if entity_id.startswith("light."):
                summary["lights"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                })
            elif entity_id.startswith("switch."):
                summary["switches"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                })
            elif entity_id.startswith("climate."):
                summary["climates"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                    "temperature": state.get("attributes", {}).get("temperature"),
                })
            elif entity_id.startswith("cover."):
                summary["covers"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                })
            elif entity_id.startswith("sensor.") or entity_id.startswith("binary_sensor."):
                summary["sensors"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                })
            else:
                summary["others"].append({
                    "id": entity_id,
                    "name": state.get("attributes", {}).get("friendly_name", entity_id),
                    "state": state.get("state"),
                })

        return summary


# 全局实例（延迟初始化）
_hass_adapter: Optional[HomeAssistantAdapter] = None


def get_hass_adapter() -> Optional[HomeAssistantAdapter]:
    """获取 Home Assistant 适配器全局实例"""
    return _hass_adapter


def init_hass_adapter(host: str = "http://localhost:8123", token: str = None) -> HomeAssistantAdapter:
    """初始化 Home Assistant 适配器全局实例"""
    global _hass_adapter
    _hass_adapter = HomeAssistantAdapter(host, token)
    return _hass_adapter
