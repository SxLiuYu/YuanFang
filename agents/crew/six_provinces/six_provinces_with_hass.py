"""
agents/crew/six_provinces/six_provinces_with_hass.py
三省六部制 + Home Assistant 整合版
让六部可以直接控制智能家居设备
"""
import logging
from typing import Optional, Dict, Any

from .six_provinces_hyper import SixProvincesSystem, SixProvinceMinister

logger = logging.getLogger(__name__)


class SixProvincesWithHASS(SixProvincesSystem):
    """
    三省六部制 + Home Assistant 整合版
    六部可以直接控制智能家居设备
    """

    def __init__(self, model: str = None, hass_host: str = None, hass_token: str = None):
        super().__init__(model)
        self.hass = None
        if hass_host and hass_token:
            self._init_hass(hass_host, hass_token)

    def _init_hass(self, host: str, token: str):
        """初始化 Home Assistant 适配器"""
        try:
            from adapters.home_assistant_adapter import HomeAssistantAdapter
            self.hass = HomeAssistantAdapter(host, token)
            logger.info(f"Home Assistant 已连接: {host}")
        except Exception as e:
            logger.warning(f"Home Assistant 连接失败: {e}")
            self.hass = None

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> dict:
        """
        运行三省六部制团队处理任务
        如果检测到需要控制设备，先调用Home Assistant
        """
        # 先分析任务，看看是否需要控制设备
        device_actions = self._extract_device_actions(task)

        if device_actions and self.hass:
            logger.info(f"检测到设备控制需求: {device_actions}")
            # 先执行设备控制
            control_result = self._execute_device_actions(device_actions)
            # 把设备控制结果加入上下文
            if context is None:
                context = {}
            context["device_control_result"] = control_result

        # 然后运行正常的三省六部制流程
        return super().run(task, context)

    def _extract_device_actions(self, task: str) -> Dict[str, Any]:
        """从任务中提取设备控制需求"""
        task_lower = task.lower()
        actions = {}

        # 灯光控制
        if "开灯" in task_lower or "开一下灯" in task_lower:
            actions["light"] = {"action": "turn_on"}
        elif "关灯" in task_lower or "关一下灯" in task_lower:
            actions["light"] = {"action": "turn_off"}

        # 空调控制
        if "空调" in task_lower and ("度" in task_lower or "温度" in task_lower):
            import re
            temp_match = re.search(r'(\d+)\s*度', task)
            if temp_match:
                temp = int(temp_match.group(1))
                actions["climate"] = {"action": "set_temperature", "value": temp}

        # 窗帘控制
        if "开窗帘" in task_lower:
            actions["cover"] = {"action": "open"}
        elif "关窗帘" in task_lower:
            actions["cover"] = {"action": "close"}

        # 氛围模式
        mood_map = {
            "放松": "relax",
            "工作": "work",
            "电影": "movie",
            "睡眠": "sleep",
            "回家": "welcome",
            "离家": "away",
        }
        for mood_key, mood_value in mood_map.items():
            if mood_key in task_lower and ("模式" in task_lower or "切换" in task_lower):
                actions["mood"] = {"action": "activate", "value": mood_value}

        return actions

    def _execute_device_actions(self, actions: Dict[str, Any]) -> Dict[str, Any]:
        """执行设备控制"""
        results = {}

        if not self.hass:
            return {"error": "Home Assistant 未连接"}

        try:
            # 灯光控制
            if "light" in actions:
                light_action = actions["light"]
                # 这里简化处理，实际应该指定具体的entity_id
                # 可以通过get_device_summary()获取设备列表让用户选择
                results["light"] = "灯光控制请求已接收（需要配置具体的entity_id）"

            # 空调控制
            if "climate" in actions:
                climate_action = actions["climate"]
                results["climate"] = f"空调温度设置请求已接收: {climate_action.get('value')}度"

            # 窗帘控制
            if "cover" in actions:
                cover_action = actions["cover"]
                results["cover"] = "窗帘控制请求已接收"

            # 氛围模式
            if "mood" in actions:
                mood_action = actions["mood"]
                mood = mood_action.get("value")
                if self.hass.activate_mood(mood):
                    results["mood"] = f"已激活 {mood} 模式"
                else:
                    results["mood"] = f"激活 {mood} 模式失败"

        except Exception as e:
            logger.error(f"设备控制执行失败: {e}")
            results["error"] = str(e)

        return results

    def get_available_devices(self) -> Dict[str, Any]:
        """获取可用设备列表"""
        if not self.hass:
            return {"error": "Home Assistant 未连接"}
        return self.hass.get_device_summary()

    def control_device(self, domain: str, entity_id: str, action: str, **kwargs) -> bool:
        """
        直接控制设备

        Args:
            domain: 设备类型 (light, switch, climate, cover)
            entity_id: 设备ID
            action: 操作 (turn_on, turn_off, set_temperature, etc.)
            **kwargs: 其他参数

        Returns:
            是否成功
        """
        if not self.hass:
            logger.warning("Home Assistant 未连接")
            return False

        try:
            if domain == "light":
                if action == "turn_on":
                    return self.hass.light_turn_on(entity_id, **kwargs)
                elif action == "turn_off":
                    return self.hass.light_turn_off(entity_id)
                elif action == "toggle":
                    return self.hass.light_toggle(entity_id)
            elif domain == "switch":
                if action == "turn_on":
                    return self.hass.switch_turn_on(entity_id)
                elif action == "turn_off":
                    return self.hass.switch_turn_off(entity_id)
            elif domain == "climate":
                if action == "set_temperature":
                    return self.hass.climate_set_temperature(entity_id, **kwargs)
                elif action == "set_hvac_mode":
                    return self.hass.climate_set_hvac_mode(entity_id, **kwargs)
            elif domain == "cover":
                if action == "open":
                    return self.hass.cover_open(entity_id)
                elif action == "close":
                    return self.hass.cover_close(entity_id)
                elif action == "set_position":
                    return self.hass.cover_set_position(entity_id, **kwargs)
            elif domain == "scene":
                if action == "activate":
                    return self.hass.scene_activate(entity_id)

            logger.warning(f"未知的设备操作: {domain}.{action}")
            return False
        except Exception as e:
            logger.error(f"设备控制失败: {e}")
            return False
