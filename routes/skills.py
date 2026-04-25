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


# ==================== Vibe Coding — AI 原生开发模式 ====================
# Hey Tuya 启发：自然语言 → 可执行技能 → 自进化
# 触发词："帮我做个XX功能" "写个脚本来XX" "用自然语言编程"

import hashlib
import re

VIBE_CACHE_FILE = "/tmp/.yuanfang_vibe_cache.json"


def _vibe_generate_code(intent: str, context: dict = None) -> dict:
    """
    接收自然语言编程意图 → LLM 生成技能代码 → 存入 skill_engine
    返回生成的 skill 描述
    """
    import os, json as _json
    from core.llm_adapter import get_llm

    sys_prompt = """你是一个 AI 技能代码生成专家。用户用自然语言描述一个功能，
你需要生成一个完整的 Python 技能函数，遵循以下格式：

```python
def skill_vibe_{hash}(query: str) -> str:
    '''
    自动生成技能: {intent}
    '''
    # 实现逻辑
    return "结果描述"
```

要求：
1. 函数名用 skill_vibe_ + 8位hash
2. 代码完整可运行，包含必要的 import
3. 可以调用现有的 HomeAssistant 命令（用 routes.chat._execute_ha_commands）
4. 可以读取传感器数据（从 app_state.nodes_copy()）
5. 生成后用 json_mode 返回完整 JSON
6. JSON 格式：{"name": "技能名", "description": "描述", "code": "完整代码", "trigger_patterns": ["匹配模式1", "匹配模式2"], "category": "vibe"}

只返回 JSON，不要有其他内容。"""

    llm = get_llm()
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"用户需求：{intent}\n当前上下文：{context or {}}"},
    ]

    try:
        raw = llm.chat_simple(messages, json_mode=True, temperature=0.3, max_tokens=4096)
        # 提取 JSON
        match = re.search(r'\{[\s\S]*\}', raw)
        if not match:
            return {"success": False, "error": "LLM 未返回有效 JSON"}
        result = _json.loads(match.group())
        return {**result, "success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _vibe_learn_from_chat(user_text: str, ai_response: str) -> str:
    """
    从对话历史中学习模式：用户这样说时，AI 这样回复 → 沉淀为 trigger_pattern
    """
    import os, _json
    from core.skill_engine import get_skill_engine

    if not os.path.exists(VIBE_CACHE_FILE):
        return "无历史数据可学习"

    try:
        with open(VIBE_CACHE_FILE) as f:
            cache = _json.load(f)
    except Exception:
        return "读取缓存失败"

    # 从缓存中找相似 query
    similar = [c for c in cache if user_text in c.get("user", "") or c.get("user", "") in user_text]
    if not similar:
        return "未找到相似模式"

    # 抽象 trigger pattern
    patterns = set()
    for item in similar:
        patterns.update(item.get("trigger_patterns", []))

    learned = f"从 {len(similar)} 条历史中学习了 {len(patterns)} 个触发模式：{', '.join(list(patterns)[:5])}"
    return learned


@skills_bp.route('/api/vibe/generate', methods=['POST'])
def vibe_generate():
    """
    POST /api/vibe/generate
    Body: {"intent": "自然语言功能描述", "context": {}}
    触发 AI 生成技能代码并存入 skill_engine
    """
    data = request.json or {}
    intent = data.get("intent", "")
    context = data.get("context", {})

    if not intent:
        return jsonify({"success": False, "error": "intent 不能为空"}), 400

    result = _vibe_generate_code(intent, context)
    if not result.get("success"):
        return jsonify(result), 500

    # 注册为 skill
    from core.skill_engine import Skill, get_skill_engine
    skill = Skill(
        name=result["name"],
        description=result["description"],
        category=result.get("category", "vibe"),
        trigger_patterns=result.get("trigger_patterns", []),
        ha_commands=[],
        response_template=result["code"],
        auto_learned=True,
        quality_score=6.0,
    )
    skill_id = get_skill_engine().register(skill)

    return jsonify({
        "success": True,
        "skill_id": skill_id,
        "name": result["name"],
        "description": result["description"],
        "message": f"成功生成并注册技能：{result['name']}",
    })


@skills_bp.route('/api/vibe/learn', methods=['POST'])
def vibe_learn():
    """
    POST /api/vibe/learn
    Body: {"user_text": "用户说了什么", "ai_response": "AI 怎么回复的"}
    从对话历史中学习模式
    """
    data = request.json or {}
    user_text = data.get("user_text", "")
    ai_response = data.get("ai_response", "")

    if not user_text:
        return jsonify({"success": False, "error": "user_text 不能为空"}), 400

    result = _vibe_learn_from_chat(user_text, ai_response)
    return jsonify({"success": True, "result": result})


@skills_bp.route('/api/vibe/history', methods=['GET'])
def vibe_history():
    """查询 vibe learning 缓存记录"""
    import json as _json
    if not os.path.exists(VIBE_CACHE_FILE):
        return jsonify({"records": []})
    try:
        with open(VIBE_CACHE_FILE) as f:
            cache = _json.load(f)
        return jsonify({"records": cache[-50:]})  # 最近50条
    except Exception:
        return jsonify({"records": [], "error": "读取失败"})


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
