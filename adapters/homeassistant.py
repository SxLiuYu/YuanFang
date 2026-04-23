"""
🏠 Home Assistant 适配器 · HomeAssistantAdapter
通过 HA REST API 读取实体状态、控制设备。
配置方式：在 .env 中填写：
  HA_URL=http://homeassistant.local:8123
  HA_TOKEN=your_long_lived_access_token
"""
import os
import json
import urllib.request
import urllib.error
from typing import Optional

HA_URL   = os.getenv("HA_URL", "").rstrip("/")
HA_TOKEN = os.getenv("HA_TOKEN", "")

# 设备权限三级分类（绿=自动执行 黄=需确认 红=禁止自动）
PERMISSION_LEVEL = {
    "green":  ["light", "media_player", "climate", "fan", "switch"],
    "yellow": ["lock", "cover", "alarm_control_panel"],
    "red":    ["script", "automation", "input_boolean"],  # 谨慎
}


def _ha_request(method: str, path: str, body: dict = None) -> dict:
    """发送 HA REST 请求"""
    if not HA_URL or not HA_TOKEN:
        return {"error": "HA_URL 或 HA_TOKEN 未配置，请在 .env 中填写"}

    url = f"{HA_URL}/api{path}"
    headers = {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
#  适配器核心类
# ============================================================
class HomeAssistantAdapter:

    # ---------- 查询 ----------

    def ping(self) -> bool:
        """检查 HA 连接"""
        r = _ha_request("GET", "/")
        return "message" in r and "error" not in r

    def get_states(self, domain: str = None) -> list:
        """获取所有实体状态，可按 domain 过滤（如 light、climate）"""
        r = _ha_request("GET", "/states")
        if isinstance(r, list):
            if domain:
                return [e for e in r if e.get("entity_id", "").startswith(f"{domain}.")]
            return r
        return []

    def get_state(self, entity_id: str) -> dict:
        """获取单个实体状态"""
        return _ha_request("GET", f"/states/{entity_id}")

    def get_lights(self) -> list:
        return self.get_states("light")

    def get_climate(self) -> list:
        return self.get_states("climate")

    def get_sensors(self) -> list:
        return self.get_states("sensor")

    def summary(self) -> dict:
        """获取家庭设备概览（快速摘要）"""
        all_states = self.get_states()
        if not all_states:
            return {"error": "无法获取设备状态，请检查 HA 连接"}

        summary = {}
        for entity in all_states:
            eid = entity.get("entity_id", "")
            domain = eid.split(".")[0] if "." in eid else "other"
            if domain not in summary:
                summary[domain] = {"on": 0, "off": 0, "total": 0}
            summary[domain]["total"] += 1
            if entity.get("state") in ("on", "open", "home", "playing"):
                summary[domain]["on"] += 1
            else:
                summary[domain]["off"] += 1
        return summary

    # ---------- 控制 ----------

    def _get_permission(self, entity_id: str) -> str:
        domain = entity_id.split(".")[0] if "." in entity_id else "other"
        for level, domains in PERMISSION_LEVEL.items():
            if domain in domains:
                return level
        return "yellow"  # 未知 domain 默认需确认

    def call_service(self, domain: str, service: str, data: dict = None) -> dict:
        """调用 HA 服务（底层方法）"""
        return _ha_request("POST", f"/services/{domain}/{service}", data or {})

    def turn_on(self, entity_id: str, **kwargs) -> dict:
        """打开设备（自动判断权限）"""
        perm = self._get_permission(entity_id)
        if perm == "red":
            return {"error": f"设备 {entity_id} 属于红色权限，禁止自动控制"}
        domain = entity_id.split(".")[0]
        payload = {"entity_id": entity_id}
        payload.update(kwargs)
        return self.call_service(domain, "turn_on", payload)

    def turn_off(self, entity_id: str) -> dict:
        """关闭设备"""
        perm = self._get_permission(entity_id)
        if perm == "red":
            return {"error": f"设备 {entity_id} 属于红色权限，禁止自动控制"}
        domain = entity_id.split(".")[0]
        return self.call_service(domain, "turn_off", {"entity_id": entity_id})

    def set_light(self, entity_id: str, brightness: int = None,
                  color_temp: int = None, rgb_color: list = None) -> dict:
        """设置灯光参数（brightness 0-255，color_temp 150-500 mired）"""
        kwargs = {}
        if brightness is not None:
            kwargs["brightness"] = max(0, min(255, brightness))
        if color_temp is not None:
            kwargs["color_temp"] = color_temp
        if rgb_color:
            kwargs["rgb_color"] = rgb_color
        return self.turn_on(entity_id, **kwargs)

    def set_climate(self, entity_id: str, temperature: float,
                    hvac_mode: str = None) -> dict:
        """设置空调温度和模式（hvac_mode: cool/heat/auto/off）"""
        payload = {"entity_id": entity_id, "temperature": temperature}
        if hvac_mode:
            self.call_service("climate", "set_hvac_mode",
                              {"entity_id": entity_id, "hvac_mode": hvac_mode})
        return self.call_service("climate", "set_temperature", payload)

    def lock(self, entity_id: str, action: str = "lock") -> dict:
        """门锁控制（lock/unlock），需要 yellow 权限确认"""
        perm = self._get_permission(entity_id)
        if perm in ("red",):
            return {"error": "权限不足"}
        return self.call_service("lock", action, {"entity_id": entity_id})

    # ---------- 场景 ----------

    def activate_scene(self, scene_entity_id: str) -> dict:
        """激活 HA 场景"""
        return self.call_service("scene", "turn_on", {"entity_id": scene_entity_id})

    def list_scenes(self) -> list:
        """列出所有可用场景"""
        return self.get_states("scene")


# ============================================================
#  全局单例
# ============================================================
_ha: Optional[HomeAssistantAdapter] = None

def get_ha() -> HomeAssistantAdapter:
    global _ha
    if _ha is None:
        _ha = HomeAssistantAdapter()
    return _ha
