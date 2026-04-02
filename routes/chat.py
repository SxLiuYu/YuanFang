# routes/chat.py
"""
Chat routes - 完整对话管线
Pipeline: 用户输入 → Skill 匹配 → 记忆上下文 → 人格注入 → LLM 生成 → 情感检测 → 记录 → 响应
"""
from flask import Blueprint, request, jsonify
import json
import logging
import datetime

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

_socketio = None
_kairos_daemon = None


def init_chat(socketio, kairos_daemon=None):
    global _socketio, _kairos_daemon
    _socketio = socketio
    _kairos_daemon = kairos_daemon


# ==================== HA 命令执行 ====================

def _parse_ha_command(text):
    """Parse HA commands from text"""
    import re
    if not text:
        return []
    pattern = r'\{[\s\S]*?\}'
    matches = re.findall(pattern, text)
    results = []
    for m in matches:
        try:
            results.append(json.loads(m))
        except Exception:
            pass
    return results


def _execute_ha_commands(commands):
    """
    Execute HomeAssistant commands
    Returns list of results with success status
    """
    if not commands:
        return []

    results = []
    for cmd in commands:
        if isinstance(cmd, str):
            try:
                cmd = json.loads(cmd)
            except Exception:
                results.append({"success": False, "result": f"Invalid command: {cmd}"})
                continue

        entity_id = cmd.get("entity_id", "")
        action = cmd.get("action", "")
        data = cmd.get("data", {})

        if not entity_id:
            results.append({"success": False, "result": "No entity_id specified"})
            continue

        try:
            from adapters.ha_adapter import get_ha_adapter
            ha = get_ha_adapter()
            if action == "activate_scene":
                result = ha.call_service("scene", "turn_on", {"entity_id": entity_id})
            elif action == "turn_on":
                result = ha.call_service("homeassistant", "turn_on", {"entity_id": entity_id, **data})
            elif action == "turn_off":
                result = ha.call_service("homeassistant", "turn_off", {"entity_id": entity_id})
            elif action == "toggle":
                result = ha.call_service("homeassistant", "toggle", {"entity_id": entity_id})
            elif action == "set_value":
                result = ha.call_service("input_number", "set_value",
                    {"entity_id": entity_id, "value": data.get("value", 0)})
            elif action == "select_option":
                result = ha.call_service("input_select", "select_option",
                    {"entity_id": entity_id, "option": data.get("option", "")})
            else:
                result = ha.call_service(action.split(".")[0] if "." in action else "homeassistant", action,
                    {"entity_id": entity_id, **data})
            results.append({"success": True, "result": result, "entity_id": entity_id, "action": action})
        except Exception as e:
            logger.error(f"HA command failed for {entity_id}: {e}")
            results.append({"success": False, "result": str(e), "entity_id": entity_id, "action": action})

    return results


# ==================== 对话历史 ====================

def _load_recent_chats(n=50):
    """Load recent chat history from Redis or memory"""
    try:
        import redis
        import os
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"),
                         port=int(os.getenv("REDIS_PORT", 6379)),
                         db=1, decode_responses=False)
        chats = []
        for key in r.keys("chat:*"):
            chat = r.hgetall(key)
            if chat:
                chats.append({k.decode() if isinstance(k, bytes) else k:
                              v.decode() if isinstance(v, bytes) else v for k, v in chat.items()})
        chats.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return chats[:n]
    except Exception:
        return []


def _save_chat(user_message, ai_response, emotion="neutral", skill_used=None):
    """Save chat interaction to Redis"""
    try:
        import redis
        import os
        import uuid
        r = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"),
                         port=int(os.getenv("REDIS_PORT", 6379)),
                         db=1, decode_responses=False)
        chat_id = f"chat:{uuid.uuid4().hex[:8]}"
        r.hset(chat_id, mapping={
            "user": user_message[:500],
            "ai": ai_response[:2000],
            "emotion": emotion,
            "skill_used": skill_used or "",
            "timestamp": datetime.datetime.now().isoformat(),
        })
    except Exception as e:
        logger.debug(f"Chat save failed (non-critical): {e}")


# ==================== 核心对话管线 ====================

def _build_conversation_pipeline(user_message: str, voice_mode: bool = False) -> dict:
    """
    完整对话管线
    
    Steps:
    1. Skill 匹配 — 如果命中高置信度技能，直接执行
    2. 记忆上下文 — 获取近期记忆摘要 + 相关历史
    3. 人格注入 — 生成 system prompt
    4. LLM 生成 — 调用 LLM 获取回复
    5. 情感检测 — 检测对话情感
    6. 记录 — 保存到情感记忆 + 向量记忆
    
    Returns: {"response": str, "skill_used": str|None, "emotion": str, "metadata": dict}
    """
    from core.llm_adapter import get_llm
    from core.skill_engine import get_skill_engine

    # Step 1: Skill 匹配
    skill_engine = get_skill_engine()
    skill_result = skill_engine.try_execute(user_message, _execute_ha_commands)

    if skill_result and skill_result.get("confidence", 0) >= 0.7:
        response = skill_result.get("response", "")
        skill_name = skill_result.get("skill_name", "")
        logger.info(f"[Pipeline] Skill matched: {skill_name} (confidence {skill_result.get('confidence', 0):.2f})")
        return {
            "response": response,
            "skill_used": skill_name,
            "emotion": "neutral",
            "metadata": {"mode": "skill", "skill_result": skill_result},
        }

    # Step 2: 记忆上下文
    context_parts = []
    try:
        from memory.system import get_memory
        mem = get_memory()
        memory_summary = mem.get_context_summary()
        if memory_summary:
            context_parts.append(memory_summary)
    except Exception as e:
        logger.debug(f"Memory context failed (non-critical): {e}")

    # Skill 提示（如果有相关技能但未直接执行）
    try:
        skill_context = skill_engine.get_skill_prompt_context()
        if skill_context:
            context_parts.append(skill_context)
    except Exception:
        pass

    context = "\n".join(context_parts)

    # Step 3: 人格注入
    try:
        from personality.engine import get_personality
        personality = get_personality()
        system_prompt = personality.get_system_prompt(
            context=context,
            voice_mode=voice_mode,
        )
    except Exception as e:
        logger.warning(f"Personality engine failed: {e}, using default prompt")
        system_prompt = "你是元芳，一个 AI 智能家居助手。回答用中文，简洁有条理。"

    # Step 4: LLM 生成
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        llm = get_llm()
        response = llm.chat_simple(messages)
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        response = "抱歉，我现在无法处理你的请求。请稍后再试。"

    # Step 5: 情感检测
    emotion = "neutral"
    try:
        from personality.engine import get_personality
        personality = get_personality()
        emotion = personality.detect_emotion(user_message, response)
    except Exception:
        pass

    # Step 6: 记录
    _save_chat(user_message, response, emotion)

    try:
        from memory.system import get_memory
        mem = get_memory()
        mem.record_interaction(user_message, response, emotion)
    except Exception as e:
        logger.debug(f"Memory record failed (non-critical): {e}")

    return {
        "response": response,
        "skill_used": None,
        "emotion": emotion,
        "metadata": {"mode": "llm"},
    }


# ==================== API 端点 ====================

@chat_bp.route('/api/chat', methods=['POST'])
def chat():
    """主对话接口"""
    data = request.json or {}
    message = data.get("message", "")
    voice_mode = data.get("voice_mode", False)

    if not message:
        return jsonify({"error": "message is required"}), 400

    result = _build_conversation_pipeline(message, voice_mode=voice_mode)

    return jsonify({
        "response": result["response"],
        "skill_used": result.get("skill_used"),
        "emotion": result.get("emotion", "neutral"),
        "metadata": result.get("metadata", {}),
    })


@chat_bp.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """流式对话接口"""
    data = request.json or {}
    message = data.get("message", "")
    voice_mode = data.get("voice_mode", False)

    if not message:
        return jsonify({"error": "message is required"}), 400

    # 技能直接匹配不走流式
    from core.skill_engine import get_skill_engine
    skill_engine = get_skill_engine()
    skill_result = skill_engine.try_execute(message, _execute_ha_commands)

    if skill_result and skill_result.get("confidence", 0) >= 0.7:
        return jsonify({
            "response": skill_result.get("response", ""),
            "skill_used": skill_result.get("skill_name"),
            "done": True,
        })

    # 流式生成
    def generate():
        try:
            # 构建上下文（同 _build_conversation_pipeline）
            context_parts = []
            try:
                from memory.system import get_memory
                mem = get_memory()
                summary = mem.get_context_summary()
                if summary:
                    context_parts.append(summary)
            except Exception:
                pass

            try:
                skill_ctx = skill_engine.get_skill_prompt_context()
                if skill_ctx:
                    context_parts.append(skill_ctx)
            except Exception:
                pass

            context = "\n".join(context_parts)

            try:
                from personality.engine import get_personality
                personality = get_personality()
                system_prompt = personality.get_system_prompt(context=context, voice_mode=voice_mode)
            except Exception:
                system_prompt = "你是元芳，一个 AI 智能家居助手。"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ]

            full_response = []

            from core.llm_adapter import get_llm
            llm = get_llm()

            def on_chunk(content):
                full_response.append(content)
                if _socketio:
                    _socketio.emit("chat_chunk", {"content": content})

            llm.chat_stream(messages, callback=on_chunk)

            response_text = "".join(full_response)

            # 情感检测 + 记录
            emotion = "neutral"
            try:
                from personality.engine import get_personality
                personality = get_personality()
                emotion = personality.detect_emotion(message, response_text)
            except Exception:
                pass

            _save_chat(message, response_text, emotion)

            try:
                from memory.system import get_memory
                get_memory().record_interaction(message, response_text, emotion)
            except Exception:
                pass

            if _socketio:
                _socketio.emit("chat_done", {"emotion": emotion})

        except Exception as e:
            logger.error(f"Stream error: {e}")
            if _socketio:
                _socketio.emit("chat_error", {"error": str(e)})

    generate()
    return jsonify({"status": "streaming"})


# Voice pipeline placeholder
_voice_chat_pipeline = None
