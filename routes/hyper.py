# routes/hyper.py
"""
HyperAgent 路由
"""
from flask import Blueprint, request, jsonify
from core.personality import get_personality
from core.memory_system import get_memory
from services.app_security import rate_limit

hyper_bp = Blueprint("hyper", __name__)

# 全局实例
_hyper_agent = None


def get_hyper_agent():
    global _hyper_agent
    if _hyper_agent is None:
        from agents.hyper import HyperAgent
        _hyper_agent = HyperAgent()
    return _hyper_agent


@hyper_bp.route('/api/hyper/run', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
def hyper_run():
    data = request.json or {}
    task = data.get("task", "")
    enable_evolution = data.get("enable_evolution", True)
    if not task:
        return jsonify({"error": "task is required"}), 400

    personality = get_personality()
    memory = get_memory()
    context = memory.get_context_summary()
    personality_prompt = personality.get_system_prompt(context)

    agent = get_hyper_agent()
    result = agent.run(
        task,
        enable_evolution=enable_evolution,
        personality_context=personality_prompt,
        memory_system=memory
    )

    return jsonify({
        "response": result["response"],
        "model": result["model"],
        "improvement": result.get("improvement"),
        "evolution_count": result["evolution_count"],
        "timestamp": result["timestamp"]
    })


@hyper_bp.route('/api/hyper/batch', methods=['POST'])
@rate_limit(max_requests=3, window_seconds=60)
def hyper_batch():
    data = request.json or {}
    tasks = data.get("tasks", [])
    if not tasks:
        return jsonify({"error": "tasks is required"}), 400
    agent = get_hyper_agent()
    try:
        results = agent.evolve_batch(tasks)
    except AttributeError:
        # evolve_batch not implemented, run sequentially
        results = []
        for task in tasks:
            r = agent.run(task, enable_evolution=True, enable_reflection=True)
            results.append(r)
    return jsonify({
        "results": [
            {"task": r["task"], "response": r["response"][:500],
             "evolution_count": r["evolution_count"]}
            for r in results
        ],
        "total_evolution_count": agent.evolution_count
    })


@hyper_bp.route('/api/hyper/status', methods=['GET'])
def hyper_status():
    return jsonify(get_hyper_agent().status())


@hyper_bp.route('/api/hyper/memory', methods=['GET'])
def hyper_memory():
    return jsonify(get_hyper_agent().memory.evolution_report())
