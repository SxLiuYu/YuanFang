# services/kairos_tools.py
"""
KAIROS 工具集 · KAIROS Tools
环境感知 + 异常检测 + 自动修复
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class KairosTools:
    """
    KAIROS 智能家居工具集
    功能：
    1. 环境感知 — 温湿度、空气质量、人体感应
    2. 异常检测 — 设备异常、能耗异常、环境超标
    3. 自动修复 — 根据策略自动执行修复动作
    """

    AUTO_REMEDY_ACTIONS = {
        "high_humidity": {
            "description": "高湿度环境处理",
            "remedies": [
                {"action": "turn_on", "entity_id": "switch.dehumidifier"},
                {"action": "turn_on", "entity_id": "switch.bedroom_dehumidifier"},
            ],
        },
        "high_temp": {
            "description": "高温环境处理",
            "remedies": [
                {"action": "turn_on", "entity_id": "switch.air_conditioner"},
                {"action": "turn_on", "entity_id": "switch.bedroom_ac"},
            ],
        },
        "motion_detected": {
            "description": "检测到人体活动",
            "remedies": [
                {"action": "turn_on", "entity_id": "light.entrance"},
            ],
        },
        "energy_anomaly": {
            "description": "能耗异常检测",
            "remedies": [
                {"action": "turn_off", "entity_id": "switch.standby_power"},
            ],
        },
    }

    def __init__(self):
        self._socketio = None
        self._ha_executor = None
        self._anomalies = []
        self._notifications = []
        self._recent_env = {}

    def set_socketio(self, socketio):
        self._socketio = socketio

    def set_ha_executor(self, fn):
        self._ha_executor = fn

    def sense_environment(self, nodes_data: dict) -> dict:
        """
        感知当前环境状态
        返回：{temp, humidity, aqi, light, motion}
        """
        sensor_readings = nodes_data.get("sensor_readings", {})
        device_states = nodes_data.get("device_states", {})

        env = {}
        # 温度
        for sid, sdata in sensor_readings.items():
            if "temperature" in sid.lower() or "temp" in sid.lower():
                env["temp"] = sdata.get("value") or sdata.get("state")
            if "humidity" in sid.lower() or "humid" in sid.lower():
                env["humidity"] = sdata.get("value") or sdata.get("state")
            if "aqi" in sid.lower() or "air" in sid.lower():
                env["aqi"] = sdata.get("value") or sdata.get("state")

        # 设备状态
        for did, ddata in device_states.items():
            if "motion" in did.lower() or "presence" in did.lower():
                if ddata.get("state") == "on":
                    env["motion"] = True

        self._recent_env = env
        return env

    def check_and_remedy_environment(self, nodes_data: dict = None, auto_execute: bool = False) -> list:
        """检查环境异常并执行自动修复"""
        if nodes_data is None:
            nodes_data = self._recent_env or {}
        env = self.sense_environment(nodes_data)
        results = []

        # 高湿度检测
        humidity = env.get("humidity", 0)
        if isinstance(humidity, (int, float)) and humidity > 70:
            action = self.AUTO_REMEDY_ACTIONS["high_humidity"]
            anomaly = self._create_anomaly("high_humidity", f"湿度{humidity}%过高", env)
            self._anomalies.append(anomaly)
            if auto_execute:
                results.extend(self._execute_remedy("high_humidity"))
            else:
                results.append({"anomaly": "high_humidity", "remedy": action["description"], "auto_executed": False})

        # 高温检测
        temp = env.get("temp", 0)
        if isinstance(temp, (int, float)) and temp > 30:
            action = self.AUTO_REMEDY_ACTIONS["high_temp"]
            anomaly = self._create_anomaly("high_temp", f"温度{temp}°C过高", env)
            self._anomalies.append(anomaly)
            if auto_execute:
                results.extend(self._execute_remedy("high_temp"))
            else:
                results.append({"anomaly": "high_temp", "remedy": action["description"], "auto_executed": False})

        # 能耗异常（简化版：检测 standby 设备）
        if auto_execute:
            try:
                from adapters.ha_adapter import get_ha_adapter
                ha = get_ha_adapter()
                standby_state = ha.get_state("switch.standby_power")
                if standby_state and standby_state.get("state") == "on":
                    results.extend(self._execute_remedy("energy_anomaly"))
            except Exception:
                pass

        # WebSocket 推送
        if self._socketio and results:
            try:
                self._socketio.emit("kairos_event", {"anomalies": results, "timestamp": datetime.now().isoformat()})
            except Exception:
                pass

        if len(self._anomalies) > 100:
            self._anomalies = self._anomalies[-100:]

        return results

    def _create_anomaly(self, anomaly_type: str, message: str, env: dict) -> dict:
        return {
            "type": anomaly_type,
            "message": message,
            "env": env,
            "timestamp": datetime.now().isoformat(),
        }

    def _execute_remedy(self, remedy_key: str) -> list:
        if not self._ha_executor:
            return [{"error": "no HA executor"}]
        remedy = self.AUTO_REMEDY_ACTIONS.get(remedy_key, {})
        commands = remedy.get("remedies", [])
        results = []
        for cmd in commands:
            try:
                r = self._ha_executor([cmd])
                results.append({**cmd, "success": r[0].get("success", False) if r else False})
            except Exception as e:
                results.append({**cmd, "error": str(e)})
        return results

    def get_anomalies(self, n: int = 20, severity: str = None) -> list:
        anomalies = self._anomalies[-n:]
        if severity:
            anomalies = [a for a in anomalies if a.get("type") == severity]
        return anomalies

    def get_notifications(self, n: int = 10) -> list:
        return self._notifications[-n:]


_tools: Optional[KairosTools] = None


def get_kairos_tools(socketio=None) -> KairosTools:
    global _tools
    if _tools is None:
        _tools = KairosTools()
    if socketio:
        _tools.set_socketio(socketio)
    return _tools
