"""
🤖 Agent + 技�?+ KAIROS 路由
"""
import datetime
import logging
from flask import Blueprint, request, jsonify

from core.personality import get_personality
from core.memory_system import get_memory
from core.skill_engine import get_skill_engine
from core.rule_engine import get_rule_engine, Rule
from services.user_manager import get_user_manager
from services.notification_hub import get_notification_hub
from services.daemon_mode import KairosDaemon
from core.yuanfang_dream import DreamSystem
from services.kairos_tools import get_kairos_tools

from agents import LobsterArmyCrew
from core.hyper_agents import HyperAgent
from services.app_security import rate_limit

logger = logging.getLogger(__name__)

agent_bp = Blueprint("agent", __name__)

# 全局实例（由 main.py 注入�?
_kairos_daemon = None
_kairos_tools = None
_rule_engine = None
_notification_hub = None
_hyper_agent = None


def init_agent(kairos_daemon, kairos_tools, rule_engine, notification_hub):
    global _kairos_daemon, _kairos_tools, _rule_engine, _notification_hub
    _kairos_daemon = kairos_daemon
    _kairos_tools = kairos_tools
    _rule_engine = rule_engine
    _notification_hub = notification_hub


def get_hyper_agent():
    global _hyper_agent
    if _hyper_agent is None:
        _hyper_agent = HyperAgent()
    return _hyper_agent


# ==================== 人格引擎 ====================

@agent_bp.route('/api/personality/status', methods=['GET'])
def personality_status():
    return jsonify(get_personality().get_status())


@agent_bp.route('/api/personality/mood', methods=['POST'])
def update_mood():
    data = request.json
    pe = get_personality()
    pe.update_mood(data.get('mood', 'calm'), data.get('energy_delta', 0), data.get('stress_delta', 0))
    return jsonify({"success": True, "status": pe.get_status()})


@agent_bp.route('/api/personality/drift', methods=['POST'])
def drift_mood():
    new_mood = get_personality().drift_mood()
    return jsonify({"success": True, "new_mood": new_mood})


# ==================== 记忆系统 ====================

@agent_bp.route('/api/memory/report', methods=['GET'])
def memory_report():
    return jsonify(get_memory().full_report())


@agent_bp.route('/api/memory/emotional', methods=['GET'])
def memory_emotional():
    emotion = request.args.get('emotion')
    top_k = int(request.args.get('top_k', 10))
    return jsonify(get_memory().emotional.recall(emotion, top_k))


@agent_bp.route('/api/memory/scene/snapshot', methods=['POST'])
def scene_snapshot():
    data = request.json or {}
    scene_type = data.get('scene_type')
    note = data.get('note', '')
    mem = get_memory()
    import app_state as state
    st = state.get_nodes_copy()
    if not scene_type:
        scene_type = mem.scene.predict_next()
    entry = mem.scene.snapshot(scene_type, st, note)
    return jsonify({"success": True, "entry": entry})


@agent_bp.route('/api/memory/scene', methods=['GET'])
def scene_recall():
    scene_type = request.args.get('type')
    n = int(request.args.get('n', 5))
    if scene_type:
        return jsonify(get_memory().scene.recall_scene(scene_type, n))
    return jsonify(get_memory().scene.recent(n))


@agent_bp.route('/api/memory/search', methods=['GET'])
def memory_search():
    query = request.args.get('q', '')
    top_k = int(request.args.get('top_k', 5))
    if not query:
        return jsonify({"error": "q parameter required"}), 400
    results = get_memory().vector.search(query, top_k)
    return jsonify([{
        "id": r.get("id"), "text": r.get("text"),
        "score": round(r.get("score", 0), 3), "timestamp": r.get("timestamp"),
    } for r in results])


# ==================== Agent ====================

@agent_bp.route('/api/agent/crew', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def agent_crew():
    data = request.json
    task = data.get("task", "")
    if not task:
        return jsonify({"error": "task is required"}), 400
    crew = LobsterArmyCrew()
    result = crew.run(task)
    return jsonify(result)


@agent_bp.route('/api/agent/<agent_name>', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def agent_single(agent_name):
    data = request.json
    input_data = data.get("input", "")
    crew = LobsterArmyCrew()
    result = crew.run_agent(agent_name, input_data)
    return jsonify(result)


# ==================== 技能引�?====================

@agent_bp.route('/api/skills', methods=['GET'])
def skill_list():
    category = request.args.get("category")
    return jsonify(get_skill_engine().list_skills(category))


@agent_bp.route('/api/skills/report', methods=['GET'])
def skill_report():
    return jsonify(get_skill_engine().report())


@agent_bp.route('/api/skills/register', methods=['POST'])
def skill_register():
    data = request.json
    from core.skill_engine import Skill
    skill = Skill(
        name=data.get("name", ""), description=data.get("description", ""),
        category=data.get("category", "general"),
        trigger_patterns=data.get("trigger_patterns", []),
        ha_commands=data.get("ha_commands", []),
        response_template=data.get("response_template", ""),
        auto_learned=False, quality_score=data.get("quality_score", 5.0),
    )
    if not skill.name:
        return jsonify({"error": "name is required"}), 400
    skill_id = get_skill_engine().register(skill)
    return jsonify({"success": True, "skill_id": skill_id})


@agent_bp.route('/api/skills/<skill_id>', methods=['DELETE'])
def skill_delete(skill_id):
    ok = get_skill_engine().unregister(skill_id)
    if ok:
        return jsonify({"success": True})
    return jsonify({"error": "skill not found"}), 404


@agent_bp.route('/api/skills/abstract', methods=['POST'])
def skill_abstract():
    data = request.json or {}
    min_occurrences = int(data.get("min_occurrences", 3))
    from routes.chat import _load_recent_chats, _parse_ha_command
    chats = _load_recent_chats(n=100)
    interactions = []
    for chat in chats:
        user_text = chat.get("user", "")
        ha_cmds = _parse_ha_command(chat.get("ai", ""))
        if ha_cmds:
            interactions.append({"user_text": user_text, "ha_commands": ha_cmds})
    new_skills = get_skill_engine().abstract_from_history(interactions, min_occurrences)
    return jsonify({
        "analyzed": len(interactions),
        "new_skills": [s.to_dict() for s in new_skills],
        "message": f"分析�?{len(interactions)} 条交互，抽象�?{len(new_skills)} 个新技�?
    })


# ==================== 技能市�?& 沙箱 ====================

@agent_bp.route('/api/skills/marketplace/available', methods=['GET'])
def skill_marketplace_available():
    from core.skill_sandbox import SkillMarketplace
    return jsonify({"skills": SkillMarketplace.list_available()})


@agent_bp.route('/api/skills/marketplace/builtin', methods=['GET'])
def skill_marketplace_builtin():
    from core.skill_sandbox import SkillMarketplace
    return jsonify({"skills": SkillMarketplace.get_builtin_skills()})


@agent_bp.route('/api/skills/marketplace/install', methods=['POST'])
def skill_marketplace_install():
    from core.skill_sandbox import SkillMarketplace
    data = request.json or {}
    builtin_name = data.get("builtin_name")
    if builtin_name:
        builtin_skills = SkillMarketplace.get_builtin_skills()
        skill_data = next((s for s in builtin_skills if s["name"] == builtin_name), None)
        if not skill_data:
            return jsonify({"error": f"内置技�?'{builtin_name}' 不存�?}), 404
        result = SkillMarketplace.install_from_json(
            skill_data, get_skill_engine(), auto_approve=False
        )
    else:
        result = SkillMarketplace.install_from_json(
            data, get_skill_engine(), auto_approve=False
        )
    if not result["success"]:
        return jsonify(result), 400
    return jsonify(result)


@agent_bp.route('/api/skills/marketplace/validate', methods=['POST'])
def skill_marketplace_validate():
    from core.skill_sandbox import SkillMarketplace
    data = request.json or {}
    result = SkillMarketplace.validate_skill_definition(data)
    return jsonify(result)


@agent_bp.route('/api/skills/sandbox/execute', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def skill_sandbox_execute():
    from core.skill_sandbox import get_sandbox, SkillPermission
    from routes.chat import _execute_ha_commands
    data = request.json or {}
    commands = data.get("commands", [])

    # 安全：强�?allow_dangerous=False，忽略前端传入�?
    permission = SkillPermission(
        read_only=data.get("read_only", False),
        allowed_domains=data.get("allowed_domains", ["light", "switch", "climate", "scene"]),
        max_actions_per_run=data.get("max_actions", 5),
        require_approval=data.get("require_approval", False),
        allow_dangerous=False,  # 安全：始终禁用危险操�?
    )

    sandbox = get_sandbox()
    sandbox.set_ha_executor(_execute_ha_commands)
    results = sandbox.execute_safe(commands, permission)

    return jsonify({
        "results": results,
        "permission": {"read_only": permission.read_only, "allowed_domains": permission.allowed_domains},
    })


# ==================== KAIROS 守护进程 ====================

@agent_bp.route('/api/kairos/status', methods=['GET'])
def kairos_status():
    daemon_status = _kairos_daemon.status() if _kairos_daemon else {"running": False}
    dream_status = DreamSystem().status()
    tools_status = {
        "recent_notifications": len(_kairos_tools.get_notifications()) if _kairos_tools else 0,
        "recent_anomalies": len(_kairos_tools.get_anomalies()) if _kairos_tools else 0,
    } if _kairos_tools else {}
    return jsonify({"daemon": daemon_status, "dream": dream_status, "tools": tools_status})


@agent_bp.route('/api/kairos/start', methods=['POST'])
def kairos_start():
    global _kairos_daemon, _kairos_tools, _rule_engine, _notification_hub
    if not _kairos_daemon:
        _kairos_daemon = KairosDaemon()
        _kairos_tools = get_kairos_tools()  # socketio 注入�?main.py 完成
        _kairos_daemon.set_tools(_kairos_tools)
        _rule_engine = get_rule_engine()
        from routes.chat import _execute_ha_commands
        _rule_engine.set_ha_executor(_execute_ha_commands)
        _kairos_daemon.set_rule_engine(_rule_engine)
    return jsonify({"success": True, "status": _kairos_daemon.status()})


@agent_bp.route('/api/kairos/stop', methods=['POST'])
def kairos_stop():
    global _kairos_daemon
    if _kairos_daemon:
        _kairos_daemon.stop()
        _kairos_daemon = None
    return jsonify({"success": True})


@agent_bp.route('/api/kairos/dream/run', methods=['POST'])
def kairos_dream_run():
    result = DreamSystem().run()
    return jsonify(result)


@agent_bp.route('/api/kairos/dream/status', methods=['GET'])
def kairos_dream_status():
    return jsonify(DreamSystem().status())


@agent_bp.route('/api/kairos/insights', methods=['GET'])
def kairos_insights():
    insights = DreamSystem().get_consolidated_insights(20)
    return jsonify(insights)


@agent_bp.route('/api/kairos/observations', methods=['GET'])
def kairos_observations():
    n = int(request.args.get('n', 20))
    if _kairos_daemon:
        return jsonify(_kairos_daemon.get_recent_observations(n))
    return jsonify([])


@agent_bp.route('/api/kairos/notifications', methods=['GET'])
def kairos_notifications():
    n = int(request.args.get('n', 10))
    if _kairos_tools:
        return jsonify(_kairos_tools.get_notifications(n))
    return jsonify([])


@agent_bp.route('/api/kairos/anomalies', methods=['GET'])
def kairos_anomalies():
    n = int(request.args.get('n', 20))
    severity = request.args.get('severity')
    if _kairos_tools:
        return jsonify(_kairos_tools.get_anomalies(n, severity))
    return jsonify([])


@agent_bp.route('/api/kairos/environment', methods=['GET'])
def kairos_environment():
    import app_state as state
    if _kairos_tools:
        return jsonify(_kairos_tools.sense_environment(state.get_nodes_copy()))
    return jsonify({"error": "KAIROS tools not initialized"})


@agent_bp.route('/api/kairos/logs', methods=['GET'])
def kairos_logs():
    date_str = request.args.get('date', datetime.datetime.now().strftime('%Y-%m-%d'))
    if _kairos_daemon:
        return jsonify(_kairos_daemon.get_daily_log(date_str))
    return jsonify([])


@agent_bp.route('/api/kairos/remedy/run', methods=['POST'])
def kairos_remedy_run():
    if not _kairos_tools:
        return jsonify({"error": "KAIROS tools not initialized"}), 400
    auto_exec = request.json.get("auto_execute", False) if request.json else False
    import app_state as state
    results = _kairos_tools.check_and_remedy_environment(
        nodes_data=state.get_nodes_copy(), auto_execute=auto_exec,
    )
    return jsonify({"results": results, "total": len(results)})


@agent_bp.route('/api/kairos/remedy/strategies', methods=['GET'])
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


# ==================== HyperAgent ====================

@agent_bp.route('/api/hyper/run', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
def hyper_run():
    data = request.json
    task = data.get("task", "")
    enable_evolution = data.get("enable_evolution", True)
    if not task:
        return jsonify({"error": "task is required"}), 400

    personality = get_personality()
    memory = get_memory()
    context = memory.get_context_summary()
    personality_prompt = personality.get_system_prompt(context)

    agent = get_hyper_agent()
    result = agent.run(task, enable_evolution=enable_evolution,
                       personality_context=personality_prompt, memory_system=memory)

    return jsonify({
        "response": result["response"], "model": result["model"],
        "improvement": result.get("improvement"),
        "evolution_count": result["evolution_count"],
        "timestamp": result["timestamp"]
    })


@agent_bp.route('/api/hyper/batch', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=60)
def hyper_batch():
    data = request.json
    tasks = data.get("tasks", [])
    if not tasks:
        return jsonify({"error": "tasks is required"}), 400
    agent = get_hyper_agent()
    results = agent.evolve_batch(tasks)
    return jsonify({
        "results": [{"task": r["task"], "response": r["response"][:500],
                      "evolution_count": r["evolution_count"]} for r in results],
        "total_evolution_count": agent.evolution_count
    })


@agent_bp.route('/api/hyper/status', methods=['GET'])
def hyper_status():
    return jsonify(get_hyper_agent().status())


@agent_bp.route('/api/hyper/memory', methods=['GET'])
def hyper_memory():
    return jsonify(get_hyper_agent().memory.evolution_report())

