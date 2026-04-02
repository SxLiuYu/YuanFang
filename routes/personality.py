# routes/personality.py
"""
人格路由 · Personality Routes
"""
from flask import Blueprint, request, jsonify
from core.personality import get_personality

personality_bp = Blueprint("personality", __name__)


@personality_bp.route('/api/personality/status', methods=['GET'])
def personality_status():
    return jsonify(get_personality().get_status())


@personality_bp.route('/api/personality/mood', methods=['POST'])
def update_mood():
    data = request.json or {}
    pe = get_personality()
    pe.update_mood(
        data.get('mood', 'calm'),
        data.get('energy_delta', 0),
        data.get('stress_delta', 0)
    )
    return jsonify({"success": True, "status": pe.get_status()})


@personality_bp.route('/api/personality/drift', methods=['POST'])
def drift_mood():
    new_mood = get_personality().drift_mood()
    return jsonify({"success": True, "new_mood": new_mood})
