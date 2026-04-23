# routes/skills.py
"""
技能路由 · Skills Routes
"""
from flask import Blueprint, request, jsonify
from core.skill_engine import get_skill_engine, Skill
from services.app_security import rate_limit

skills_bp = Blueprint("skills", __name__)


@skills_bp.route('/api/skills', methods=['GET'])
def skill_list():
    category = request.args.get("category")
    return jsonify(get_skill_engine().list_skills(category))


@skills_bp.route('/api/skills/report', methods=['GET'])
def skill_report():
    return jsonify(get_skill_engine().report())


@skills_bp.route('/api/skills/register', methods=['POST'])
def skill_register():
    data = request.json or {}
    skill = Skill(
        name=data.get("name", ""),
        description=data.get("description", ""),
        category=data.get("category", "general"),
        trigger_patterns=data.get("trigger_patterns", []),
        ha_commands=data.get("ha_commands", []),
        response_template=data.get("response_template", ""),
        auto_learned=False,
        quality_score=data.get("quality_score", 5.0),
    )
    if not skill.name:
        return jsonify({"error": "name is required"}), 400
    skill_id = get_skill_engine().register(skill)
    return jsonify({"success": True, "skill_id": skill_id})


@skills_bp.route('/api/skills/<skill_id>', methods=['DELETE'])
def skill_delete(skill_id):
    ok = get_skill_engine().unregister(skill_id)
    if ok:
        return jsonify({"success": True})
    return jsonify({"error": "skill not found"}), 404


@skills_bp.route('/api/skills/abstract', methods=['POST'])
def skill_abstract():
    data = request.json or {}
    min_occurrences = int(data.get("min_occurrences", 3))
    try:
        from routes.chat import _load_recent_chats, _parse_ha_command
        chats = _load_recent_chats(n=100)
        interactions = []
        for chat in chats:
            user_text = chat.get("user", "")
            ha_cmds = _parse_ha_command(chat.get("ai", ""))
            if ha_cmds:
                interactions.append({"user_text": user_text, "ha_commands": ha_cmds})
    except Exception:
        interactions = []
    new_skills = get_skill_engine().abstract_from_history(interactions, min_occurrences)
    return jsonify({
        "analyzed": len(interactions),
        "new_skills": [s.to_dict() for s in new_skills],
        "message": f"分析了 {len(interactions)} 条交互，抽象了 {len(new_skills)} 个新技能",
    })


# ==================== 技能市场 ====================

@skills_bp.route('/api/skills/marketplace/available', methods=['GET'])
def skill_marketplace_available():
    from core.skill_sandbox import SkillMarketplace
    return jsonify({"skills": SkillMarketplace.list_available()})


@skills_bp.route('/api/skills/marketplace/builtin', methods=['GET'])
def skill_marketplace_builtin():
    from core.skill_sandbox import SkillMarketplace
    return jsonify({"skills": SkillMarketplace.get_builtin_skills()})


@skills_bp.route('/api/skills/marketplace/install', methods=['POST'])
def skill_marketplace_install():
    from core.skill_sandbox import SkillMarketplace
    data = request.json or {}
    builtin_name = data.get("builtin_name")
    if builtin_name:
        builtin_skills = SkillMarketplace.get_builtin_skills()
        skill_data = next((s for s in builtin_skills if s["name"] == builtin_name), None)
        if not skill_data:
            return jsonify({"error": f"内置技能 '{builtin_name}' 不存在"}), 404
        result = SkillMarketplace.install_from_json(skill_data, get_skill_engine(), auto_approve=False)
    else:
        result = SkillMarketplace.install_from_json(data, get_skill_engine(), auto_approve=False)
    if not result["success"]:
        return jsonify(result), 400
    return jsonify(result)


@skills_bp.route('/api/skills/marketplace/validate', methods=['POST'])
def skill_marketplace_validate():
    from core.skill_sandbox import SkillMarketplace
    data = request.json or {}
    result = SkillMarketplace.validate_skill_definition(data)
    return jsonify(result)


# ==================== 技能沙箱 ====================

@skills_bp.route('/api/skills/sandbox/execute', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def skill_sandbox_execute():
    from core.skill_sandbox import get_sandbox, SkillPermission
    from routes.chat import _execute_ha_commands
    data = request.json or {}
    commands = data.get("commands", [])

    permission = SkillPermission(
        read_only=data.get("read_only", False),
        allowed_domains=data.get("allowed_domains", ["light", "switch", "climate", "scene"]),
        max_actions_per_run=data.get("max_actions", 5),
        require_approval=data.get("require_approval", False),
        allow_dangerous=False,
    )

    sandbox = get_sandbox()
    sandbox.set_ha_executor(_execute_ha_commands)
    results = sandbox.execute_safe(commands, permission)

    return jsonify({
        "results": results,
        "permission": {"read_only": permission.read_only, "allowed_domains": permission.allowed_domains},
    })
