"""
⚙️ 规则引擎 + 多用户管�?+ 通知中心 路由
"""
import logging
from flask import Blueprint, request, jsonify

from core.rule_engine import get_rule_engine, Rule
from services.user_manager import get_user_manager
from services.notification_hub import get_notification_hub
from services.app_security import rate_limit

import app_state as state

logger = logging.getLogger(__name__)

sys_bp = Blueprint("sys", __name__)

# 全局实例（由 main.py 注入�?
_rule_engine = None
_notification_hub = None


def init_sys(rule_engine, notification_hub):
    global _rule_engine, _notification_hub
    _rule_engine = rule_engine
    _notification_hub = notification_hub


# ==================== 规则引擎 ====================

@sys_bp.route('/api/rules', methods=['GET'])
def rule_list():
    engine = get_rule_engine()
    enabled_only = request.args.get("enabled") == "true"
    return jsonify(engine.list_rules(enabled_only=enabled_only))


@sys_bp.route('/api/rules', methods=['POST'])
def rule_add():
    data = request.json
    engine = get_rule_engine()
    rule = Rule(
        name=data.get("name", ""), description=data.get("description", ""),
        trigger_type=data.get("trigger_type", "sensor_threshold"),
        trigger_config=data.get("trigger_config", {}),
        actions=data.get("actions", []),
        cooldown_minutes=data.get("cooldown_minutes", 30),
        priority=data.get("priority", 5),
        enabled=data.get("enabled", True),
        metadata=data.get("metadata", {}),
    )
    if not rule.name:
        return jsonify({"error": "name is required"}), 400
    rule_id = engine.add_rule(rule)
    return jsonify({"success": True, "rule_id": rule_id})


@sys_bp.route('/api/rules/<rule_id>', methods=['PUT'])
def rule_update(rule_id):
    data = request.json
    engine = get_rule_engine()
    ok = engine.update_rule(rule_id, data)
    if ok:
        return jsonify({"success": True})
    return jsonify({"error": "rule not found"}), 404


@sys_bp.route('/api/rules/<rule_id>', methods=['DELETE'])
def rule_delete(rule_id):
    engine = get_rule_engine()
    ok = engine.remove_rule(rule_id)
    if ok:
        return jsonify({"success": True})
    return jsonify({"error": "rule not found"}), 404


@sys_bp.route('/api/rules/<rule_id>/toggle', methods=['POST'])
def rule_toggle(rule_id):
    data = request.json or {}
    engine = get_rule_engine()
    ok = engine.toggle_rule(rule_id, enabled=data.get("enabled"))
    if ok:
        return jsonify({"success": True})
    return jsonify({"error": "rule not found"}), 404


@sys_bp.route('/api/rules/evaluate', methods=['POST'])
def rule_evaluate():
    engine = get_rule_engine()
    triggered = engine.evaluate(context={"nodes": state.get_nodes_copy()})
    return jsonify({
        "matched_count": len(triggered),
        "rules": [{"rule_id": t["rule"].id, "rule_name": t["rule"].name,
                    "conditions": t["matched_conditions"]} for t in triggered],
    })


@sys_bp.route('/api/rules/run', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def rule_run():
    engine = get_rule_engine()
    triggered = engine.evaluate(context={"nodes": state.get_nodes_copy()})
    if not triggered:
        return jsonify({"matched": 0, "results": []})
    results = engine.execute_triggered(triggered)
    return jsonify({"matched": len(triggered), "results": results})


@sys_bp.route('/api/rules/logs', methods=['GET'])
def rule_logs():
    n = int(request.args.get("n", 20))
    rule_id = request.args.get("rule_id")
    engine = get_rule_engine()
    return jsonify(engine.get_execution_logs(n=n, rule_id=rule_id))


@sys_bp.route('/api/rules/report', methods=['GET'])
def rule_report():
    return jsonify(get_rule_engine().report())


# ==================== 多用户管�?====================

@sys_bp.route('/api/users', methods=['GET'])
def user_list():
    return jsonify(get_user_manager().list_users())


@sys_bp.route('/api/users/register', methods=['POST'])
def user_register():
    data = request.json
    name = data.get("name", "")
    if not name:
        return jsonify({"error": "name is required"}), 400
    manager = get_user_manager()
    result = manager.register(
        name=name, display_name=data.get("display_name", ""),
        role=data.get("role", "member"), preferences=data.get("preferences", {}),
    )
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@sys_bp.route('/api/users/auth', methods=['POST'])
def user_auth():
    data = request.json
    token = data.get("token", "")
    if not token:
        return jsonify({"error": "token is required"}), 400
    manager = get_user_manager()
    user = manager.authenticate(token)
    if user:
        return jsonify({"success": True, "user": user.to_dict(include_token=True)})
    return jsonify({"error": "invalid token"}), 401


@sys_bp.route('/api/users/<username>', methods=['PUT'])
def user_update(username):
    token = request.headers.get("X-User-Token", "")
    data = request.json
    manager = get_user_manager()
    result = manager.update_user(username, data, operator_token=token)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@sys_bp.route('/api/users/<username>', methods=['DELETE'])
def user_delete(username):
    token = request.headers.get("X-User-Token", "")
    manager = get_user_manager()
    result = manager.delete_user(username, operator_token=token)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@sys_bp.route('/api/users/sessions', methods=['GET'])
def user_sessions():
    return jsonify(get_user_manager().get_active_sessions())


@sys_bp.route('/api/users/report', methods=['GET'])
def user_report():
    return jsonify(get_user_manager().report())


# ==================== 通知中心 ====================

@sys_bp.route('/api/notify/send', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def notify_send():
    data = request.json
    hub = get_notification_hub()
    result = hub.notify(
        title=data.get("title", ""), message=data.get("message", ""),
        level=data.get("level", "info"), category=data.get("category", ""),
        user_token=data.get("user_token"), skip_aggregation=data.get("skip_aggregation", False),
    )
    return jsonify(result)


@sys_bp.route('/api/notify/history', methods=['GET'])
def notify_history():
    hub = get_notification_hub()
    n = int(request.args.get("n", 20))
    level = request.args.get("level")
    ack = request.args.get("acknowledged")
    acknowledged = None
    if ack == "true":
        acknowledged = True
    elif ack == "false":
        acknowledged = False
    return jsonify(hub.get_history(n=n, level=level, acknowledged=acknowledged))


@sys_bp.route('/api/notify/acknowledge', methods=['POST'])
def notify_acknowledge():
    data = request.json or {}
    hub = get_notification_hub()
    result = hub.acknowledge(
        notification_id=data.get("id"), acknowledge_all=data.get("all", False),
    )
    return jsonify(result)


@sys_bp.route('/api/notify/unread', methods=['GET'])
def notify_unread():
    hub = get_notification_hub()
    return jsonify({"count": hub.get_unread_count()})


@sys_bp.route('/api/notify/channels', methods=['GET'])
def notify_channels():
    channel = request.args.get("channel")
    return jsonify(get_notification_hub().get_channel_config(channel))


@sys_bp.route('/api/notify/channels', methods=['PUT'])
def notify_channel_update():
    data = request.json
    channel = data.get("channel", "")
    config = data.get("config", {})
    hub = get_notification_hub()
    result = hub.update_channel_config(channel, config)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@sys_bp.route('/api/notify/silence', methods=['GET'])
def notify_silence_get():
    return jsonify(get_notification_hub().get_silence_periods())


@sys_bp.route('/api/notify/silence', methods=['PUT'])
def notify_silence_set():
    data = request.json
    periods = data.get("periods", [])
    return jsonify(get_notification_hub().set_silence_periods(periods))


@sys_bp.route('/api/notify/prefs/<user_token>', methods=['GET'])
def notify_user_prefs_get(user_token):
    return jsonify(get_notification_hub().get_user_prefs(user_token))


@sys_bp.route('/api/notify/prefs/<user_token>', methods=['PUT'])
def notify_user_prefs_set(user_token):
    data = request.json
    ok = get_notification_hub().set_user_prefs(user_token, data)
    return jsonify({"success": ok})


@sys_bp.route('/api/notify/report', methods=['GET'])
def notify_report():
    return jsonify(get_notification_hub().report())

