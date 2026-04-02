# routes/chat.py
"""Chat routes - conversation and voice pipeline"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

_kairos_daemon = None
_socketio = None


def init_chat(socketio, kairos_daemon=None):
    global _socketio, _kairos_daemon
    _socketio = socketio
    _kairos_daemon = kairos_daemon


def _load_recent_chats(n=50):
    """Load recent chat history from Redis or memory"""
    try:
        import redis
        import os
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"),
                         port=int(os.getenv("REDIS_PORT", 6379)),
                         db=1, decode_responses=False)
        chats = []
        for key in r.keys("chat:*"):
            chat = r.hgetall(key)
            if chat:
                chats.append({k.decode() if isinstance(k, bytes) else k:
                              v.decode() if isinstance(v, bytes) else v for k, v in chat.items()})
        chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return chats[:n]
    except Exception:
        return []


def _parse_ha_command(text):
    """Parse HA commands from text"""
    import re
    if not text:
        return []
    pattern = r'\{[\s\S]*?\}'
    matches = re.findall(pattern, text)
    results = []
    for m in matches:
        try:
            import json
            results.append(json.loads(m))
        except Exception:
            pass
    return results


def _execute_ha_commands(commands):
    """
    Execute HomeAssistant commands
    Returns list of results with success status
    """
    if not commands:
        return []

    results = []
    for cmd in commands:
        if isinstance(cmd, str):
            try:
                import json
                cmd = json.loads(cmd)
            except Exception:
                results.append({"success": False, "result": f"Invalid command: {cmd}"})
                continue

        entity_id = cmd.get("entity_id", "")
        action = cmd.get("action", "")
        data = cmd.get("data", {})

        if not entity_id:
            results.append({"success": False, "result": "No entity_id specified"})
            continue

        try:
            import os
            from adapters.ha_adapter import get_ha_adapter
            ha = get_ha_adapter()
            if action == "activate_scene":
                result = ha.call_service("scene", "turn_on", {"entity_id": entity_id})
            elif action == "turn_on":
                result = ha.call_service("homeassistant", "turn_on", {"entity_id": entity_id, **data})
            elif action == "turn_off":
                result = ha.call_service("homeassistant", "turn_off", {"entity_id": entity_id})
            elif action == "toggle":
                result = ha.call_service("homeassistant", "toggle", {"entity_id": entity_id})
            elif action == "set_value":
                result = ha.call_service("input_number", "set_value",
                    {"entity_id": entity_id, "value": data.get("value", 0)})
            elif action == "select_option":
                result = ha.call_service("input_select", "select_option",
                    {"entity_id": entity_id, "option": data.get("option", "")})
            else:
                result = ha.call_service(action.split(".")[0] if "." in action else "homeassistant", action,
                    {"entity_id": entity_id, **data})
            results.append({"success": True, "result": result, "entity_id": entity_id, "action": action})
        except Exception as e:
            logger.error(f"HA command failed for {entity_id}: {e}")
            results.append({"success": False, "result": str(e), "entity_id": entity_id, "action": action})

    return results


# Voice pipeline placeholder
_voice_chat_pipeline = None


@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get("message", "")
    return jsonify({"response": f"Echo: {message}"})
