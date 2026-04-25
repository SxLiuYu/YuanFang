# routes/sensors.py
"""
传感器数据接收路由
接收 Termux 节点推送的传感器数据
"""
from flask import Blueprint, request, jsonify
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

sensors_bp = Blueprint("sensors", __name__)

# 内存存储（生产环境建议用 Redis）
_sensor_cache = {}
_conversation_cache = []


@sensors_bp.route("/api/sensors/<node_id>", methods=["POST"])
def receive_sensor_data(node_id):
    """
    接收 Termux 传感器节点推送的数据
    
    POST /api/sensors/termux_vivo_x9s
    Content-Type: application/json
    
    {
        "battery": {"level": 80, "status": "discharging"},
        "location": {...},
        "wifi": {...},
        "timestamp": "2026-04-08T07:00:00"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data"}), 400
        
        data["node_id"] = node_id
        data["received_at"] = datetime.now().isoformat()
        
        _sensor_cache[node_id] = data
        
        logger.info(f"[Sensors] Data from {node_id}: battery={data.get('battery')}, timestamp={data.get('timestamp')}")
        
        return jsonify({"status": "ok", "received": True}), 200
    
    except Exception as e:
        logger.error(f"[Sensors] Error receiving data: {e}")
        return jsonify({"error": str(e)}), 500


@sensors_bp.route("/api/sensors/<node_id>", methods=["GET"])
def get_sensor_data(node_id):
    """获取指定节点的最新传感器数据"""
    if node_id in _sensor_cache:
        return jsonify(_sensor_cache[node_id]), 200
    return jsonify({"error": "No data for this node"}), 404


@sensors_bp.route("/api/sensors", methods=["GET"])
def list_sensor_nodes():
    """列出所有已知的传感器节点"""
    return jsonify({
        "nodes": list(_sensor_cache.keys()),
        "count": len(_sensor_cache)
    }), 200


# ==================== 对话记录 ====================

CONVERSATION_LOG_FILE = os.path.expanduser("~/YuanFang/data/conversation_log.json")


def log_to_memory(entry: dict):
    """追加记入本地 conversation_log.json"""
    import json
    os.makedirs(os.path.dirname(CONVERSATION_LOG_FILE), exist_ok=True)
    try:
        logs = json.load(open(CONVERSATION_LOG_FILE)) if os.path.exists(CONVERSATION_LOG_FILE) else []
    except:
        logs = []
    logs.append(entry)
    # 只保留最近 1000 条
    logs = logs[-1000:]
    with open(CONVERSATION_LOG_FILE, "w") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


@sensors_bp.route("/api/conversation/log", methods=["POST"])
def conversation_log():
    """
    记录一次语音对话
    
    POST /api/conversation/log
    {
        "node": "termux_vivo_x9s",
        "user_text": "用户说的话",
        "assistant_text": "助手回复",
        "latency_ms": 6500
    }
    """
    try:
        data = request.get_json() or {}
        node = data.get("node", "unknown")
        
        entry = {
            "node": node,
            "user_text": data.get("user_text", ""),
            "assistant_text": data.get("assistant_text", ""),
            "latency_ms": data.get("latency_ms", 0),
            "timestamp": datetime.now().isoformat(),
        }
        
        _conversation_cache.append(entry)
        if len(_conversation_cache) > 100:
            _conversation_cache.pop(0)
        
        log_to_memory(entry)
        logger.info(f"[Memory] Voice log from {node}: user={entry['user_text'][:30]}...")
        
        return jsonify({"status": "ok", "logged": True}), 200
    except Exception as e:
        logger.error(f"[Memory] Log error: {e}")
        return jsonify({"error": str(e)}), 500


@sensors_bp.route("/api/conversation/log", methods=["GET"])
def conversation_get():
    """获取最近对话记录"""
    limit = int(request.args.get("limit", 20))
    return jsonify({
        "conversations": _conversation_cache[-limit:],
        "count": len(_conversation_cache)
    }), 200


def init_sensors_routes(app):
    """注册传感器路由"""
    app.register_blueprint(sensors_bp)
    logger.info("[Sensors] 路由已注册: /api/sensors")
