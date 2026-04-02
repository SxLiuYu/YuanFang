"""
💬 对话路由（文�?+ 语音�?
包含：聊天、语音管线、HA 意图识别、对话持久化
"""
import os
import json
import struct
import re
import base64
import datetime
import logging
import mimetypes
from pathlib import Path
from flask import Blueprint, request, jsonify, Response
from flask_socketio import SocketIO

import app_state as state
from core.llm_adapter import get_llm, chat_with_ai
from core.personality import get_personality
from core.memory_system import get_memory
from core.skill_engine import get_skill_engine
from services.app_security import rate_limit

logger = logging.getLogger(__name__)

chat_bp = Blueprint("chat", __name__)

# ==================== 对话持久化（增量追加�?====================
CHAT_LOG_DIR = Path(__file__).parent.parent / "chat_logs"
CHAT_LOG_DIR.mkdir(exist_ok=True)
_persist_lock = __import__("threading").Lock()

# HA 意图识别 prompt
_HA_INTENT_PROMPT = """

【智能家居控制能力�?
你可以通过 [HA_CMD] 标签控制 Home Assistant 中的设备。当用户要求控制设备时：
1. 先用自然语言回复用户
2. 在回复末尾用以下格式输出控制指令�?
   [HA_CMD] entity_id=light.xxx action=on brightness=200 [/HA_CMD]
   [HA_CMD] entity_id=climate.xxx action=on temperature=26 hvac_mode=cool [/HA_CMD]
   [HA_CMD] entity_id=scene.xxx action=activate_scene [/HA_CMD]

可用设备（最近一次快照）�?
{ha_devices}

注意�?
- entity_id 格式�?domain.name（如 light.bedroom�?
- action 可以�?on/off/activate_scene
- 亮度 brightness 范围 0-255
- 温度 temperature 单位摄氏�?
- 模式 hvac_mode: cool/heat/auto/off/fan_only
- 不确定的操作，回复用户确认后再执�?
"""


# ==================== 公共辅助函数 ====================

def _get_chat_log_path():
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    return CHAT_LOG_DIR / f"{today}.json"


def _persist_chat(source, user_text, ai_response, extra=None):
    """增量追加对话记录（不再全量读写）"""
    record = {
        "ts": datetime.datetime.now().isoformat(),
        "source": source,
        "user": user_text,
        "ai": ai_response,
    }
    if extra:
        record["extra"] = extra

    with _persist_lock:
        log_path = _get_chat_log_path()
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"持久化写入失�? {e}")


def _load_recent_chats(source=None, n=20):
    """从日志文件加载最近的对话（JSONL 格式�?""
    with _persist_lock:
        try:
            log_path = _get_chat_log_path()
            if not log_path.exists():
                return []
            records = []
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            records.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            if source:
                records = [r for r in records if r.get("source") == source]
            return records[-n:]
        except Exception:
            return []


def _get_ha_devices_prompt() -> str:
    """获取 HA 设备列表�?prompt 片段（从 chat �?voice_chat 共用的重复逻辑中提取）"""
    try:
        from adapters.homeassistant import get_ha
        ha = get_ha()
        ha_devices_info = []
        for domain in ['light', 'climate', 'switch', 'scene', 'media_player']:
            states = ha.get_states(domain)
            for s in states[:10]:
                name = s.get('attributes', {}).get('friendly_name', s['entity_id'])
                st = s.get('state', 'unknown')
                ha_devices_info.append(f"- {s['entity_id']} ({name}): {st}")
        if ha_devices_info:
            return _HA_INTENT_PROMPT.format(ha_devices='\n'.join(ha_devices_info))
    except Exception:
        pass
    return ""


def _parse_ha_command(llm_response: str) -> list:
    """�?LLM 回复中提�?HA 控制指令"""
    commands = []
    pattern = r'\[HA_CMD\]\s*(.*?)\s*\[/HA_CMD\]'
    for match in re.finditer(pattern, llm_response, re.DOTALL):
        cmd_str = match.group(1).strip()
        cmd = {}
        for part in cmd_str.split():
            if '=' in part:
                k, v = part.split('=', 1)
                cmd[k] = v
        if 'entity_id' in cmd:
            commands.append({
                'entity_id': cmd['entity_id'],
                'action': cmd.get('action', 'on'),
                'params': {k: v for k, v in cmd.items() if k not in ('entity_id', 'action')},
            })
    return commands


def _strip_ha_tags(text: str) -> str:
    """�?LLM 回复中移�?[HA_CMD] 标签"""
    return re.sub(r'\[HA_CMD\].*?\[/HA_CMD\]', '', text, flags=re.DOTALL).strip()


def _try_num(v):
    """尝试将字符串转为数字"""
    try:
        return int(v)
    except (ValueError, TypeError):
        try:
            return float(v)
        except (ValueError, TypeError):
            return v


def _execute_ha_commands(commands: list) -> list:
    """执行 HA 设备控制指令"""
    from adapters.homeassistant import get_ha
    ha = get_ha()
    results = []
    for cmd in commands:
        try:
            entity_id = cmd['entity_id']
            action = cmd['action']
            params = cmd.get('params', {})
            logger.info(f"[意图执行] {entity_id} -> {action} {params}")
            if action == 'off':
                result = ha.turn_off(entity_id)
            elif action in ('scene', 'activate_scene'):
                result = ha.activate_scene(entity_id)
            elif 'temperature' in params or 'hvac_mode' in params:
                result = ha.set_climate(
                    entity_id,
                    float(params.get('temperature', 24)),
                    params.get('hvac_mode'),
                )
            elif 'brightness' in params or 'color_temp' in params or 'rgb_color' in params:
                result = ha.set_light(
                    entity_id,
                    brightness=int(params['brightness']) if 'brightness' in params else None,
                    color_temp=int(params['color_temp']) if 'color_temp' in params else None,
                )
            else:
                result = ha.turn_on(entity_id, **{k: _try_num(v) for k, v in params.items()})
            results.append({"entity_id": entity_id, "success": "error" not in result, "result": result})
        except Exception as e:
            results.append({"entity_id": cmd.get('entity_id', '?'), "success": False, "result": str(e)})
    return results


# ==================== 语音公共函数 ====================

def _pcm_to_wav(pcm_bytes, sample_rate=16000, channels=1, bits=16):
    """将原�?PCM 数据包装�?WAV 格式"""
    data_size = len(pcm_bytes)
    buf = bytearray()
    buf.extend(b"RIFF")
    buf.extend(struct.pack("<I", 36 + data_size))
    buf.extend(b"WAVE")
    buf.extend(b"fmt ")
    buf.extend(struct.pack("<I", 16))
    buf.extend(struct.pack("<H", 1))
    buf.extend(struct.pack("<H", channels))
    buf.extend(struct.pack("<I", sample_rate))
    buf.extend(struct.pack("<I", sample_rate * channels * bits // 8))
    buf.extend(struct.pack("<H", channels * bits // 8))
    buf.extend(struct.pack("<H", bits))
    buf.extend(b"data")
    buf.extend(struct.pack("<I", data_size))
    buf.extend(pcm_bytes)
    return bytes(buf)


def _stt_recognize(audio_bytes, filename="voice.wav", mime_type="audio/wav"):
    """语音转文�?""
    _llm = get_llm()
    stt_key = _llm._get_api_key("FunAudioLLM/CosyVoice2-0.5B")
    if not stt_key:
        logger.warning("[STT] API key 未配�?)
        return None

    boundary = '----WebKitFormBoundary' + ''.join(['-' if i % 2 else '' for i in range(16)])
    stt_body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {mime_type}\r\n\r\n'
    ).encode("utf-8") + audio_bytes + (
        f'\r\n--{boundary}\r\n'
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f'FunAudioLLM/CosyVoice2-0.5B\r\n'
        f'--{boundary}--\r\n'
    ).encode("utf-8")

    import urllib.request
    req = urllib.request.Request(
        f"{_llm.api_base}/audio/transcriptions",
        data=stt_body,
        headers={
            "Authorization": f"Bearer {stt_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("text", "")
    except Exception as e:
        logger.error(f"[STT] 识别失败: {e}")
        return None


def _tts_generate(text, api_key, voice="zh-CN-XiaoxiaoNeural", speed=1.0):
    """文本转语音，返回音频 bytes �?None"""
    import urllib.request
    payload = json.dumps({
        "model": "FunAudioLLM/CosyVoice2-0.5B",
        "input": text[:500],
        "voice": voice,
        "response_format": "wav",
        "speed": speed,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{get_llm().api_base}/audio/speech",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read()
    except Exception as e:
        logger.error(f"[TTS] 生成失败: {e}")
        return None


def _tts_generate_long(text, api_key, voice="zh-CN-XiaoxiaoNeural", speed=1.0):
    """长文本分�?TTS"""
    if len(text) <= 500:
        audio = _tts_generate(text, api_key, voice, speed)
        if audio:
            return base64.b64encode(audio).decode("utf-8")
        return None

    sentences = re.split(r'(?<=[。！？\n])', text)
    chunks = []
    current = ""
    for s in sentences:
        if len(current) + len(s) > 450:
            if current:
                chunks.append(current)
            current = s
        else:
            current += s
    if current:
        chunks.append(current)

    if not chunks:
        chunks = [text]

    audio_parts = []
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        logger.debug(f"[TTS] 分段 {i+1}/{len(chunks)} ({len(chunk)} �?")
        audio = _tts_generate(chunk.strip(), api_key, voice, speed)
        if audio and len(audio) > 44:
            audio_parts.append(audio[44:])

    if not audio_parts:
        return None

    pcm_data = b"".join(audio_parts)
    buf = bytearray()
    data_size = len(pcm_data)
    buf.extend(b"RIFF")
    buf.extend(struct.pack("<I", 36 + data_size))
    buf.extend(b"WAVE")
    buf.extend(b"fmt ")
    buf.extend(struct.pack("<I", 16))
    buf.extend(struct.pack("<H", 1))
    buf.extend(struct.pack("<H", 1))
    buf.extend(struct.pack("<I", 22050))
    buf.extend(struct.pack("<I", 22050 * 2))
    buf.extend(struct.pack("<H", 2))
    buf.extend(struct.pack("<H", 16))
    buf.extend(b"data")
    buf.extend(struct.pack("<I", data_size))
    buf.extend(pcm_data)
    return base64.b64encode(bytes(buf)).decode("utf-8")


def _simplify_for_voice(text: str) -> str:
    """将文字回复精简为适合语音播报的版�?""
    # 移除代码�?
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'#{1,6}\s*', '', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)

    lines = text.strip().split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        list_match = re.match(r'^[-*•]\s+(.*)', line)
        if list_match:
            cleaned_lines.append(list_match.group(1))
            continue
        ol_match = re.match(r'^\d+[.)]\s+(.*)', line)
        if ol_match:
            cleaned_lines.append(ol_match.group(1))
            continue
        cleaned_lines.append(line)

    text = ' '.join(cleaned_lines)
    text = re.sub(r'\s{2,}', ' ', text).strip()

    if len(text) > 150:
        truncated = text[:150]
        last_sentence_end = -1
        for sep in ['�?, '�?, '�?, '�?, '.', '!', '?']:
            pos = truncated.rfind(sep)
            if pos > last_sentence_end:
                last_sentence_end = pos
        if last_sentence_end > 80:
            text = truncated[:last_sentence_end + 1].strip()
        else:
            text = truncated.rstrip('，�?') + '，详细信息请查看面板�?

    return text.strip()


# ==================== 语音对话管线 ====================

# �?main.py 注入�?socketio 实例�?kairos_daemon
_socketio: SocketIO = None
_kairos_daemon = None


def init_chat(socketio, kairos_daemon):
    global _socketio, _kairos_daemon
    _socketio = socketio
    _kairos_daemon = kairos_daemon


def _voice_chat_pipeline(audio_bytes, filename="voice.wav", mime_type="audio/wav", node_id=None):
    """完整语音对话管线：STT �?LLM �?记录 �?TTS"""
    _llm = get_llm()

    # Step 1: STT
    user_text = _stt_recognize(audio_bytes, filename, mime_type)
    if not user_text:
        return {"text": "", "response": "听不清，请再说一�?, "audio_b64": None, "format": None}

    logger.info(f"[语音] 识别: {user_text}")

    # Step 2: LLM
    personality = get_personality()
    memory = get_memory()
    skill_engine = get_skill_engine()
    context = memory.get_context_summary()
    skill_context = skill_engine.get_skill_prompt_context()

    system_prompt = personality.get_system_prompt(
        context=context, voice_mode=True, skill_context=skill_context,
    )
    system_prompt += _get_ha_devices_prompt()

    # 构建含历史上下文�?messages
    source = node_id or "voice"
    history = state.get_chat_history(source)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-(state.CHAT_HISTORY_MAX - 2):]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_text})

    llm_result = chat_with_ai(messages)

    if "error" in llm_result:
        reply_text = f"思考出了点问题，请再说一�?
        logger.error(f"[语音] LLM 失败: {llm_result['error']}")
    else:
        reply_text = llm_result["choices"][0]["message"]["content"]

    # 记录到历�?
    state.add_to_history(source, "user", user_text)
    state.add_to_history(source, "assistant", reply_text)

    # 语音精简
    full_reply = reply_text
    voice_reply = _simplify_for_voice(reply_text)
    if voice_reply != full_reply:
        logger.debug(f"[语音] 精简: {len(full_reply)}�?�?{len(voice_reply)}�?)

    # 自动执行 HA 设备控制指令
    ha_commands = _parse_ha_command(reply_text)
    if ha_commands:
        logger.info(f"[意图] 检测到 {len(ha_commands)} �?HA 指令")
        ha_results = _execute_ha_commands(ha_commands)
        reply_text = _strip_ha_tags(reply_text)
        voice_reply = _simplify_for_voice(reply_text)
        if not reply_text:
            success_count = sum(1 for r in ha_results if r.get('success'))
            reply_text = f"已执�?{success_count}/{len(ha_commands)} 条指�?
        if _socketio:
            _socketio.emit("device_update", {
                "type": "device_update",
                "results": ha_results,
                "timestamp": datetime.datetime.now().isoformat(),
            })
        try:
            skill_engine.learn_from_interaction(
                user_text=user_text, ai_response=voice_reply, ha_commands=ha_commands,
            )
        except Exception as e:
            logger.debug(f"[技能学习] 失败: {e}")

    # 记录互动
    detected_emotion = personality.detect_emotion(user_text, reply_text, chat_with_ai)
    memory.record_interaction(user_text, reply_text, detected_emotion)
    personality.set_memory_summary(memory.get_context_summary())
    personality.update_mood(personality.state["emotion"]["mood"], energy_delta=-0.02)

    # 持久�?
    _persist_chat(source, user_text, reply_text)

    # KAIROS
    if _kairos_daemon:
        try:
            _kairos_daemon.record_activity()
        except Exception:
            pass

    # Step 3: TTS
    tts_key = _llm._get_api_key("FunAudioLLM/CosyVoice2-0.5B")
    audio_b64 = None
    if tts_key:
        tts_result = _tts_generate_long(voice_reply, tts_key)
        if tts_result:
            audio_b64 = tts_result

    return {
        "text": user_text,
        "response": reply_text,
        "voice_response": voice_reply,
        "audio_b64": audio_b64,
        "format": "wav" if audio_b64 else None,
    }


# ==================== HTTP 路由 ====================

@chat_bp.route('/api/chat', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def chat():
    """AI 聊天（文字对话）"""
    data = request.json
    message = data.get("message", "")
    model = data.get("model")
    clear_history = data.get("clear_history", False)

    if not message:
        return jsonify({"error": "message is required"}), 400

    if clear_history:
        state.clear_history("dashboard")

    personality = get_personality()
    memory = get_memory()
    skill_engine = get_skill_engine()
    context = memory.get_context_summary()
    skill_context = skill_engine.get_skill_prompt_context()

    # 技能匹�?
    skill_result = skill_engine.try_execute(message, ha_executor=_execute_ha_commands)
    if skill_result and skill_result.get("ha_executed"):
        detected_emotion = personality.detect_emotion(message, skill_result["response"], chat_with_ai)
        memory.record_interaction(message, skill_result["response"], detected_emotion)
        personality.set_memory_summary(memory.get_context_summary())
        _persist_chat("dashboard", message, skill_result["response"])
        return jsonify({
            "response": skill_result["response"],
            "skill_used": skill_result["skill_name"],
            "skill_confidence": skill_result.get("confidence"),
            "model": "skill_engine",
        })

    system_prompt = personality.get_system_prompt(context, skill_context=skill_context)
    system_prompt += _get_ha_devices_prompt()

    # 构建含历史的 messages
    history = state.get_chat_history("dashboard")
    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-(state.CHAT_HISTORY_MAX - 2):]:
        messages.append(msg)
    messages.append({"role": "user", "content": message})

    result = chat_with_ai(messages, model)

    if "error" in result:
        return jsonify({"error": result["error"]}), 400

    try:
        content = result["choices"][0]["message"]["content"]
        state.add_to_history("dashboard", "user", message)
        state.add_to_history("dashboard", "assistant", content)

        # 自动执行 HA 指令
        ha_commands = _parse_ha_command(content)
        if ha_commands:
            ha_results = _execute_ha_commands(ha_commands)
            content = _strip_ha_tags(content)
            if not content:
                success_count = sum(1 for r in ha_results if r.get('success'))
                content = f"已执�?{success_count}/{len(ha_commands)} 条指�?
            if _socketio:
                _socketio.emit("device_update", {
                    "type": "device_update", "results": ha_results,
                    "timestamp": datetime.datetime.now().isoformat(),
                })
            try:
                skill_engine.learn_from_interaction(message, content, ha_commands)
            except Exception:
                pass

        detected_emotion = personality.detect_emotion(message, content, chat_with_ai)
        memory.record_interaction(message, content, detected_emotion)
        personality.set_memory_summary(memory.get_context_summary())
        personality.update_mood(personality.state["emotion"]["mood"], energy_delta=-0.01)
        _persist_chat("dashboard", message, content)

        if _kairos_daemon:
            try:
                _kairos_daemon.record_activity()
            except Exception:
                pass

        return jsonify({
            "response": content,
            "model": result.get("model", model or get_llm().default_model)
        })
    except (KeyError, IndexError) as e:
        logger.error(f"解析 LLM 响应失败: {e}")
        return jsonify({"error": "AI 响应解析失败，请重试"}), 500


@chat_bp.route('/api/chat/history/clear', methods=['POST'])
def clear_chat_history():
    data = request.json or {}
    node_id = data.get("node_id")
    state.clear_history(node_id)
    return jsonify({"success": True})


@chat_bp.route('/api/chat/logs', methods=['GET'])
def chat_logs():
    date_str = request.args.get("date", datetime.datetime.now().strftime("%Y-%m-%d"))
    source = request.args.get("source")
    log_path = CHAT_LOG_DIR / f"{date_str}.json"
    if not log_path.exists():
        return jsonify([])
    try:
        records = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        if source:
            records = [r for r in records if r.get("source") == source]
        return jsonify(records[-50:])
    except Exception:
        return jsonify([])


@chat_bp.route('/api/voice/tts', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=60)
def text_to_speech():
    data = request.json
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "text is required"}), 400

    _llm = get_llm()
    api_key = _llm._get_api_key("FunAudioLLM/CosyVoice2-0.5B")
    if not api_key:
        return jsonify({"error": "CosyVoice API key not configured"}), 500

    audio_bytes = _tts_generate(text, api_key, voice=data.get("voice", "zh-CN-XiaoxiaoNeural"),
                                speed=data.get("speed", 1.0))
    if audio_bytes is None:
        return jsonify({"error": "TTS generation failed"}), 500

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return jsonify({"audio": audio_b64, "format": "wav"})


@chat_bp.route('/api/voice/chat', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def voice_chat():
    if 'file' not in request.files:
        return jsonify({"error": "audio file is required"}), 400

    audio_file = request.files['file']
    filename = audio_file.filename or "voice.wav"
    mime_type = mimetypes.guess_type(filename)[0] or "audio/wav"
    audio_data = audio_file.read()

    result = _voice_chat_pipeline(audio_data, filename, mime_type)

    if not result["text"]:
        return jsonify({"error": "无法识别语音内容"}), 400

    return jsonify({
        "text": result["text"],
        "response": result["response"],
        "audio": result["audio_b64"],
        "format": result["format"],
    })

