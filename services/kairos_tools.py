# services/kairos_tools.py
"""
KAIROS Tools - 环境感知 + 异常检测 + 自动修复
Claude Code Marker: IIICAgA
"""
import datetime
import json
from pathlib import Path

DEMO_LOG_DIR = Path(__file__).parent / "daemon_logs"
DEMO_LOG_DIR.mkdir(exist_ok=True)


class KAIROSTools:
    """
    KAIROS 工具集
    """

    def __init__(self, socketio=None):
        self._socketio = socketio
        self._notification_queue = []
        self._max_queue = 50

    def send_notification(self, title: str, message: str, level: str = "info",
                          target: str = "all") -> dict:
        notification = {
            "type": "kairos_notification",
            "title": title,
            "message": message,
            "level": level,
            "target": target,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self._notification_queue.append(notification)
        if len(self._notification_queue) > self._max_queue:
            self._notification_queue = self._notification_queue[-self._max_queue:]

        if self._socketio:
            if target in ("all", "dashboard"):
                self._socketio.emit("kairos_notification", notification)
            if target in ("all", "voice_nodes"):
                self._socketio.emit("kairos_notification", notification)

        return {"success": True, "notification_id": len(self._notification_queue)}

    def get_notifications(self, n: int = 10) -> list:
        return self._notification_queue[-n:]

    def sense_environment(self, nodes_data: dict = None) -> dict:
        now = datetime.datetime.now()
        result = {
            "timestamp": now.isoformat(),
            "hour": now.hour,
            "weekday": now.strftime("%A"),
            "ha_status": None,
            "sensor_summary": {},
            "scene_prediction": None,
            "anomalies": [],
        }

        # 1. HA status
        try:
            from adapters.ha_adapter import get_ha_adapter
            ha = get_ha_adapter()
            if ha.ping():
                summary = ha.summary()
                result["ha_status"] = "connected"
                result["ha_summary"] = summary
            else:
                result["ha_status"] = "disconnected"
        except Exception as e:
            result["ha_status"] = f"error: {e}"

        # 2. Sensor data from nodes
        if nodes_data:
            for node_id, data in nodes_data.items():
                sensors = data.get("sensors", {})
                if sensors:
                    result["sensor_summary"][node_id] = {
                        "battery": sensors.get("battery"),
                        "temperature": sensors.get("temperature"),
                        "humidity": sensors.get("humidity"),
                        "light": sensors.get("light"),
                        "wifi_ssid": sensors.get("wifi_ssid"),
                    }

        # 3. Scene prediction
        try:
            from core.memory_system import get_memory
            mem = get_memory()
            result["scene_prediction"] = mem.scene.predict_next()
            result["emotion_summary"] = mem.emotional.summary()
        except Exception:
            pass

        return result

    AUTO_REMEDY_ACTIONS = {
        "device_offline": {
            "description": "HomeAssistant disconnected",
            "remedies": [
                {"action": "notify", "message": "HomeAssistant is offline, check connection"},
                {"action": "ha_retry", "entity_id": "{entity_id}", "service": "homeassistant.restart"},
                {"action": "sensor_poll", "node_id": "{node_id}"},
            ],
        },
        "sensor_anomaly": {
            "description": "Sensor reading unusual",
            "remedies": [
                {"action": "notify", "message": "Sensor {node_id} reading unusual: {detail}"},
                {"action": "sensor_poll", "node_id": "{node_id}"},
            ],
        },
        "emotion_spike": {
            "description": "Emotional spike detected",
            "remedies": [
                {"action": "notify", "message": "Emotional spike: {detail}"},
                {"action": "personality_calm", "message": "Take a breath. {detail}"},
            ],
        },
        "no_data_timeout": {
            "description": "No data received from node",
            "remedies": [
                {"action": "notify", "message": "No data from {node_id} for {timeout}"},
                {"action": "node_ping", "node_id": "{node_id}"},
            ],
        },
    }

    def auto_remedy(self, anomaly_type: str, context: dict = None,
                    auto_execute: bool = False) -> dict:
        strategy = self.AUTO_REMEDY_ACTIONS.get(anomaly_type)
        if not strategy:
            return {"actions_taken": [], "success": False, "message": f"Unknown anomaly: {anomaly_type}"}

        ctx = context or {}
        actions_taken = []
        errors = []

        for remedy in strategy["remedies"]:
            action_type = remedy.get("action", "")
            action_message = remedy.get("message", "")

            # Substitute context values
            for key, val in ctx.items():
                action_message = action_message.replace(f"{{{key}}}", str(val))

            try:
                if action_type == "notify":
                    self.send_notification(
                        title=f"Auto: {strategy['description']}",
                        message=action_message,
                        level="warning",
                    )
                    actions_taken.append({"type": "notify", "message": action_message})

                elif action_type == "ha_retry" and auto_execute:
                    entity_id = remedy.get("entity_id", "").format(**ctx)
                    service = remedy.get("service", "").format(**ctx)
                    for key, val in ctx.items():
                        entity_id = entity_id.replace(f"{{{key}}}", str(val))
                        service = service.replace(f"{{{key}}}", str(val))
                    if entity_id and service:
                        try:
                            from adapters.ha_adapter import get_ha_adapter
                            ha = get_ha_adapter()
                            ha.call_service(service, {"entity_id": entity_id})
                            actions_taken.append({"type": "ha_retry", "entity_id": entity_id})
                        except Exception as e:
                            errors.append(f"HA retry failed: {e}")

                elif action_type == "sensor_poll":
                    node_id = remedy.get("node_id", "").format(**ctx)
                    for key, val in ctx.items():
                        node_id = node_id.replace(f"{{{key}}}", str(val))
                    if node_id and self._socketio:
                        self._socketio.emit("sensor_poll_request", {"node_id": node_id})
                        actions_taken.append({"type": "sensor_poll", "node_id": node_id})

                elif action_type == "node_ping":
                    node_id = remedy.get("node_id", "").format(**ctx)
                    for key, val in ctx.items():
                        node_id = node_id.replace(f"{{{key}}}", str(val))
                    if node_id and self._socketio:
                        self._socketio.emit("node_ping", {"node_id": node_id})
                        actions_taken.append({"type": "node_ping", "node_id": node_id})

                elif action_type == "personality_calm" and auto_execute:
                    message = remedy.get("message", "").format(**ctx)
                    try:
                        from core.personality import get_personality
                        pe = get_personality()
                        pe.update_mood("calm", stress_delta=-0.2)
                        actions_taken.append({"type": "personality_calm"})
                    except Exception as e:
                        errors.append(f"Personality calm failed: {e}")

            except Exception as e:
                errors.append(f"Action {action_type} failed: {e}")

        return {
            "actions_taken": actions_taken,
            "success": len(errors) == 0,
            "message": f"{len(actions_taken)} actions, {len(errors)} errors" if errors else "All OK",
            "errors": errors,
        }

    def check_and_remedy_environment(self, nodes_data: dict = None,
                                     auto_execute: bool = False) -> list:
        env = self.sense_environment(nodes_data)
        results = []

        # 1. HA disconnected
        if env.get("ha_status") in ("disconnected", None):
            if isinstance(env.get("ha_status"), str) and "error" in env.get("ha_status", ""):
                pass
            elif env.get("ha_status") == "disconnected":
                r = self.auto_remedy("device_offline", {"detail": "HA disconnected"}, auto_execute)
                r["anomaly"] = "ha_disconnected"
                results.append(r)

        # 2. Sensor anomalies
        for node_id, sensors in env.get("sensor_summary", {}).items():
            battery = sensors.get("battery")
            if battery is not None and float(battery) < 20:
                r = self.auto_remedy("sensor_anomaly", {
                    "node_id": node_id,
                    "detail": f"battery {battery}%",
                }, auto_execute)
                r["anomaly"] = f"sensor_battery_low_{node_id}"
                results.append(r)

        # 3. Emotion spike
        emotion_summary = env.get("emotion_summary", {})
        neg_ratio = emotion_summary.get("negative_ratio", 0)
        if neg_ratio and float(neg_ratio) > 0.3:
            r = self.auto_remedy("emotion_spike", {"detail": f"negative ratio {neg_ratio}"}, auto_execute)
            r["anomaly"] = "emotion_spike"
            results.append(r)

        return results

    def report_anomaly(self, anomaly_type: str, description: str,
                       severity: str = "low", context: dict = None) -> dict:
        report = {
            "type": anomaly_type,
            "description": description,
            "severity": severity,
            "context": context or {},
            "timestamp": datetime.datetime.now().isoformat(),
        }

        # Log to file
        anomaly_file = DEMO_LOG_DIR / "anomalies.json"
        anomalies = []
        if anomaly_file.exists():
            try:
                anomalies = json.loads(anomaly_file.read_text("utf-8"))
            except Exception:
                pass
        anomalies.append(report)
        anomaly_file.write_text(json.dumps(anomalies, ensure_ascii=False, indent=2), encoding="utf-8")

        # Notify if high severity
        if severity in ("high", "critical"):
            self.send_notification(
                title=f"Anomaly: {anomaly_type}",
                message=description,
                level="error",
            )

        return {"success": True, "anomaly_id": len(anomalies)}

    def get_context_summary(self) -> str:
        lines = []
        now = datetime.datetime.now()
        lines.append(f"KAIROS {now.strftime('%H:%M:%S')} | ")

        try:
            from core.memory_system import get_memory
            mem = get_memory()
            lines.append(f"next: {mem.scene.predict_next()} | ")
            lines.append(f"emotion: {mem.emotional.summary()}")
        except Exception:
            pass

        try:
            from services.daemon_mode import KAIROSDaemon
            pass
        except Exception:
            pass

        return "".join(lines)

    @staticmethod
    def to_brief(text: str, max_chars: int = 200) -> str:
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars]
        last_end = -1
        for sep in ['. ', '! ', '? ', ', ', '; ', ': ']:
            pos = truncated.rfind(sep)
            if pos > last_end:
                last_end = pos
        if last_end > max_chars * 0.5:
            return truncated[:last_end + 1].strip()
        return truncated.rsplit(' ', 1)[0].strip() + "..."


_kairos_tools = None


def get_kairos_tools(socketio=None) -> KAIROSTools:
    global _kairos_tools
    if _kairos_tools is None:
        _kairos_tools = KAIROSTools(socketio=socketio)
    return _kairos_tools
