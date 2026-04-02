# routes/kairos.py
"""
KAIROS 守护进程路由
"""
import datetime
from flask import Blueprint, request, jsonify

kairos_bp = Blueprint("kairos", __name__)

# 全局实例（由 main.py 注入）
_kairos_daemon = None
_kairos_tools = None
_rule_engine = None


def init_kairos(kairos_daemon, kairos_tools, rule_engine):
    global _kairos_daemon, _kairos_tools, _rule_engine
    _kairos_daemon = kairos_daemon
    _kairos_tools = kairos_tools
    _rule_engine = rule_engine


@kairos_bp.route('/api/kairos/status', methods=['GET'])
def kairos_status():
    daemon_status = _kairos_daemon.status() if _kairos_daemon else {"running": False}
    from core.yuanfang_dream import DreamSystem
    dream_status = DreamSystem().status()
    tools_status = {
        "recent_notifications": len(_kairos_tools.get_notifications()) if _kairos_tools else 0,
        "recent_anomalies": len(_kairos_tools.get_anomalies()) if _kairos_tools else 0,
    } if _kairos_tools else {}
    return jsonify({"daemon": daemon_status, "dream": dream_status, "tools": tools_status})


@kairos_bp.route('/api/kairos/start', methods=['POST'])
def kairos_start():
    global _kairos_daemon, _kairos_tools, _rule_engine
    if not _kairos_daemon:
        from services.daemon_mode import KairosDaemon
        from services.kairos_tools import get_kairos_tools
        from core.rule_engine import get_rule_engine
        from routes.chat import _execute_ha_commands
        _kairos_daemon = KairosDaemon()
        _kairos_tools = get_kairos_tools()
        _rule_engine = get_rule_engine()
        _kairos_daemon.set_tools(_kairos_tools)
        _kairos_daemon.set_rule_engine(_rule_engine)
        _rule_engine.set_ha_executor(_execute_ha_commands)
    return jsonify({"success": True, "status": _kairos_daemon.status()})


@kairos_bp.route('/api/kairos/stop', methods=['POST'])
def kairos_stop():
    global _kairos_daemon
    if _kairos_daemon:
        _kairos_daemon.stop()
        _kairos_daemon = None
    return jsonify({"success": True})


@kairos_bp.route('/api/kairos/dream/run', methods=['POST'])
def kairos_dream_run():
    from core.yuanfang_dream import DreamSystem
    result = DreamSystem().run()
    return jsonify(result)


@kairos_bp.route('/api/kairos/dream/status', methods=['GET'])
def kairos_dream_status():
    from core.yuanfang_dream import DreamSystem
    return jsonify(DreamSystem().status())


@kairos_bp.route('/api/kairos/insights', methods=['GET'])
def kairos_insights():
    from core.yuanfang_dream import DreamSystem
    insights = DreamSystem().get_consolidated_insights(20)
    return jsonify(insights)


@kairos_bp.route('/api/kairos/observations', methods=['GET'])
def kairos_observations():
    n = int(request.args.get('n', 20))
    if _kairos_daemon:
        return jsonify(_kairos_daemon.get_recent_observations(n))
    return jsonify([])


@kairos_bp.route('/api/kairos/notifications', methods=['GET'])
def kairos_notifications():
    n = int(request.args.get('n', 10))
    if _kairos_tools:
        return jsonify(_kairos_tools.get_notifications(n))
    return jsonify([])


@kairos_bp.route('/api/kairos/anomalies', methods=['GET'])
def kairos_anomalies():
    n = int(request.args.get('n', 20))
    severity = request.args.get('severity')
    if _kairos_tools:
        return jsonify(_kairos_tools.get_anomalies(n, severity))
    return jsonify([])


@kairos_bp.route('/api/kairos/environment', methods=['GET'])
def kairos_environment():
    if _kairos_tools:
        try:
            from core import app_state as state
            return jsonify(_kairos_tools.sense_environment(state.get_nodes_copy()))
        except Exception:
            return jsonify({})
    return jsonify({"error": "KAIROS tools not initialized"})


@kairos_bp.route('/api/kairos/logs', methods=['GET'])
def kairos_logs():
    date_str = request.args.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    if _kairos_daemon:
        return jsonify(_kairos_daemon.get_daily_log(date_str))
    return jsonify([])


@kairos_bp.route('/api/kairos/remedy/run', methods=['POST'])
def kairos_remedy_run():
    if not _kairos_tools:
        return jsonify({"error": "KAIROS tools not initialized"}), 400
    auto_exec = request.json.get("auto_execute", False) if request.json else False
    try:
        from core import app_state as state
        nodes_data = state.get_nodes_copy()
    except Exception:
        nodes_data = {}
    results = _kairos_tools.check_and_remedy_environment(
        nodes_data=nodes_data, auto_execute=auto_exec,
    )
    return jsonify({"results": results, "total": len(results)})


@kairos_bp.route('/api/kairos/remedy/strategies', methods=['GET'])
def kairos_remedy_strategies():
    from services.kairos_tools import KairosTools
    strategies = {}
    for key, val in KairosTools.AUTO_REMEDY_ACTIONS.items():
        strategies[key] = {
            "description": val["description"],
            "remedies_count": len(val["remedies"]),
            "remedies": [{"action": r["action"]} for r in val["remedies"]],
        }
    return jsonify(strategies)
