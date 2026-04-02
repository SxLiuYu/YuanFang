"""
🏠 Home Assistant + 设备适配器路�?
"""
import datetime
import logging
from flask import Blueprint, request, jsonify

from adapters.homeassistant import get_ha
from services.app_security import rate_limit

logger = logging.getLogger(__name__)

ha_bp = Blueprint("ha", __name__)


@ha_bp.route('/api/ha/ping', methods=['GET'])
def ha_ping():
    ok = get_ha().ping()
    return jsonify({"connected": ok})


@ha_bp.route('/api/ha/summary', methods=['GET'])
def ha_summary():
    return jsonify(get_ha().summary())


@ha_bp.route('/api/ha/states', methods=['GET'])
def ha_states():
    domain = request.args.get('domain')
    return jsonify(get_ha().get_states(domain))


@ha_bp.route('/api/ha/state/<path:entity_id>', methods=['GET'])
def ha_state(entity_id):
    return jsonify(get_ha().get_state(entity_id))


@ha_bp.route('/api/ha/control', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def ha_control():
    data = request.json or {}
    entity_id = data.get("entity_id", "")
    action = data.get("action", "on")
    if not entity_id:
        return jsonify({"error": "entity_id is required"}), 400
    ha = get_ha()
    if action == "off":
        result = ha.turn_off(entity_id)
    else:
        kwargs = {k: v for k, v in data.items() if k not in ("entity_id", "action")}
        result = ha.turn_on(entity_id, **kwargs)
    return jsonify(result)


@ha_bp.route('/api/ha/light', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def ha_light():
    data = request.json or {}
    entity_id = data.get("entity_id", "")
    if not entity_id:
        return jsonify({"error": "entity_id is required"}), 400
    result = get_ha().set_light(
        entity_id,
        brightness=data.get("brightness"),
        color_temp=data.get("color_temp"),
        rgb_color=data.get("rgb_color"),
    )
    return jsonify(result)


@ha_bp.route('/api/ha/climate', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def ha_climate():
    data = request.json or {}
    entity_id = data.get("entity_id", "")
    temp = data.get("temperature")
    if not entity_id or temp is None:
        return jsonify({"error": "entity_id and temperature are required"}), 400
    result = get_ha().set_climate(entity_id, float(temp), data.get("hvac_mode"))
    return jsonify(result)


@ha_bp.route('/api/ha/scenes', methods=['GET'])
def ha_scenes():
    return jsonify(get_ha().list_scenes())


@ha_bp.route('/api/ha/scene/activate', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def ha_scene_activate():
    data = request.json or {}
    scene_id = data.get("entity_id", "")
    if not scene_id:
        return jsonify({"error": "entity_id is required"}), 400
    return jsonify(get_ha().activate_scene(scene_id))


# ==================== MQTT 设备 ====================

@ha_bp.route('/api/mqtt/status', methods=['GET'])
def mqtt_status():
    from adapters.mqtt_adapter import get_mqtt
    mqtt = get_mqtt()
    return jsonify({"connected": mqtt.connected, "devices": len(mqtt.list_devices())})


@ha_bp.route('/api/mqtt/devices', methods=['GET'])
def mqtt_devices():
    from adapters.mqtt_adapter import get_mqtt
    return jsonify(get_mqtt().list_devices())


@ha_bp.route('/api/mqtt/control', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def mqtt_control():
    from adapters.mqtt_adapter import get_mqtt
    data = request.json or {}
    device_id = data.get("device_id", "")
    action = data.get("action", "")
    value = data.get("value", "")
    mqtt = get_mqtt()
    if action == "on":
        return jsonify(mqtt.turn_on(device_id))
    elif action == "off":
        return jsonify(mqtt.turn_off(device_id))
    elif action == "set" and value:
        return jsonify(mqtt.set_state(device_id, value))
    return jsonify({"error": "无效操作"}), 400


# ==================== SwitchBot ====================

@ha_bp.route('/api/switchbot/status', methods=['GET'])
def switchbot_status():
    from adapters.switchbot_adapter import get_switchbot
    sb = get_switchbot()
    return jsonify({"configured": sb.configured, "devices": sb.list_devices()})


@ha_bp.route('/api/switchbot/devices', methods=['GET'])
def switchbot_devices():
    from adapters.switchbot_adapter import get_switchbot
    return jsonify(get_switchbot().list_devices())


@ha_bp.route('/api/switchbot/control', methods=['POST'])
@rate_limit(max_requests=60, window_seconds=60)
def switchbot_control():
    from adapters.switchbot_adapter import get_switchbot
    data = request.json or {}
    device_id = data.get("device_id", "")
    action = data.get("action", "")
    sb = get_switchbot()
    if action == "on":
        return jsonify(sb.turn_on(device_id))
    elif action == "off":
        return jsonify(sb.turn_off(device_id))
    elif action == "toggle":
        return jsonify(sb.toggle(device_id))
    elif action == "brightness":
        return jsonify(sb.set_brightness(device_id, data.get("value", 50)))
    return jsonify({"error": "无效操作"}), 400


# ==================== Frigate 摄像�?====================

@ha_bp.route('/api/frigate/status', methods=['GET'])
def frigate_status():
    from adapters.frigate_adapter import get_frigate
    frigate = get_frigate()
    return jsonify({"configured": frigate.configured, "cameras": frigate.get_cameras()})


@ha_bp.route('/api/frigate/events', methods=['GET'])
def frigate_events():
    from adapters.frigate_adapter import get_frigate
    label = request.args.get("label")
    minutes = int(request.args.get("minutes", "60"))
    limit = int(request.args.get("limit", "25"))
    return jsonify(get_frigate().get_recent_events(label=label, minutes=minutes, limit=limit))


@ha_bp.route('/api/frigate/summary', methods=['GET'])
def frigate_summary():
    from adapters.frigate_adapter import get_frigate
    minutes = int(request.args.get("minutes", "60"))
    return jsonify(get_frigate().get_summary(minutes=minutes))

