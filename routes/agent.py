# routes/agent.py
"""
Agent Routes - /api/agent/* endpoints (crew + single agent)
Other routes split to: personality.py, memory.py, skills.py, kairos.py, hyper.py
"""
from flask import Blueprint, request, jsonify
from agents import LobsterArmyCrew
from services.app_security import rate_limit

agent_bp = Blueprint("agent", __name__)

# Global instances (injected by main.py)
_kairos_daemon = None
_kairos_tools = None
_rule_engine = None
_notification_hub = None


def init_agent(kairos_daemon, kairos_tools, rule_engine, notification_hub):
    global _kairos_daemon, _kairos_tools, _rule_engine, _notification_hub
    _kairos_daemon = kairos_daemon
    _kairos_tools = kairos_tools
    _rule_engine = rule_engine
    _notification_hub = notification_hub


@agent_bp.route('/api/agent/crew', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def agent_crew():
    data = request.json or {}
    task = data.get("task", "")
    if not task:
        return jsonify({"error": "task is required"}), 400
    crew = LobsterArmyCrew()
    result = crew.run(task)
    return jsonify(result)


@agent_bp.route('/api/agent/<agent_name>', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def agent_single(agent_name):
    data = request.json or {}
    input_data = data.get("input", "")
    crew = LobsterArmyCrew()
    result = crew.run_agent(agent_name, input_data)
    return jsonify(result)
