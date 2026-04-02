# routes/rules_users.py
"""
系统规则和用户管理路由
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

sys_bp = Blueprint("sys", __name__)

_rule_engine = None
_notification_hub = None


def init_sys(rule_engine, notification_hub):
    global _rule_engine, _notification_hub
    _rule_engine = rule_engine
    _notification_hub = notification_hub


@sys_bp.route('/api/rules', methods=['GET'])
def list_rules():
    enabled_only = request.args.get('enabled', 'false').lower() == 'true'
    return jsonify(_rule_engine.list_rules(enabled_only) if _rule_engine else [])


@sys_bp.route('/api/rules', methods=['POST'])
def add_rule():
    data = request.json or {}
    from core.rule_engine import Rule, RuleEngine
    rule = Rule(
        rule_id=data.get("id", ""),
        name=data.get("name", ""),
        condition=data.get("condition", {}),
        action=data.get("action", []),
        enabled=data.get("enabled", True),
        priority=data.get("priority", 0),
    )
    rule_id = _rule_engine.add_rule(rule) if _rule_engine else None
    return jsonify({"success": True, "rule_id": rule_id})


@sys_bp.route('/api/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    ok = _rule_engine.remove_rule(rule_id) if _rule_engine else False
    return jsonify({"success": ok})


@sys_bp.route('/api/rules/<rule_id>/enable', methods=['POST'])
def enable_rule(rule_id):
    _rule_engine.enable_rule(rule_id, True) if _rule_engine else None
    return jsonify({"success": True})


@sys_bp.route('/api/rules/<rule_id>/disable', methods=['POST'])
def disable_rule(rule_id):
    _rule_engine.enable_rule(rule_id, False) if _rule_engine else None
    return jsonify({"success": True})


@sys_bp.route('/api/rules/check', methods=['POST'])
def check_rules():
    data = request.json or {}
    context = data.get("context", {})
    results = _rule_engine.check_and_fire(context) if _rule_engine else []
    return jsonify({"results": results})


@sys_bp.route('/api/notifications/recent', methods=['GET'])
def recent_notifications():
    n = int(request.args.get('n', 20))
    hub = _notification_hub
    if hub:
        return jsonify(hub.recent(n))
    return jsonify([])
