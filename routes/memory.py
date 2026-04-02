# routes/memory.py
"""
记忆路由 · Memory Routes
"""
from flask import Blueprint, request, jsonify
from core.memory_system import get_memory

memory_bp = Blueprint("memory", __name__)


@memory_bp.route('/api/memory/report', methods=['GET'])
def memory_report():
    return jsonify(get_memory().full_report())


@memory_bp.route('/api/memory/emotional', methods=['GET'])
def memory_emotional():
    emotion = request.args.get('emotion')
    top_k = int(request.args.get('top_k', 10))
    return jsonify(get_memory().emotional.recall(emotion, top_k))


@memory_bp.route('/api/memory/scene/snapshot', methods=['POST'])
def scene_snapshot():
    data = request.json or {}
    scene_type = data.get('scene_type')
    note = data.get('note', '')
    mem = get_memory()
    try:
        from core import app_state as state
        st = state.get_nodes_copy()
    except Exception:
        st = {}
    if not scene_type:
        scene_type = mem.scene.predict_next()
    entry = mem.scene.snapshot(scene_type, st, note)
    return jsonify({"success": True, "entry": entry})


@memory_bp.route('/api/memory/scene', methods=['GET'])
def scene_recall():
    scene_type = request.args.get('type')
    n = int(request.args.get('n', 5))
    mem = get_memory()
    if scene_type:
        return jsonify(mem.scene.recall_scene(scene_type, n))
    return jsonify(mem.scene.recent(n))


@memory_bp.route('/api/memory/search', methods=['GET'])
def memory_search():
    query = request.args.get('q', '')
    top_k = int(request.args.get('top_k', 5))
    if not query:
        return jsonify({"error": "q parameter required"}), 400
    results = get_memory().vector.search(query, top_k)
    return jsonify([{
        "id": r.get("id"),
        "text": r.get("text"),
        "score": round(r.get("score", 0), 3),
        "timestamp": r.get("timestamp"),
    } for r in results])
