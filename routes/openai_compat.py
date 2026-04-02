"""
🤖 OpenAI 兼容接口 + 基础 API
"""
import os
import json
import base64
import datetime
import logging
import urllib.request
from flask import Blueprint, request, jsonify, Response

import app_state as state
from core.llm_adapter import get_llm, chat_with_ai
from services.app_security import rate_limit

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)

# ==================== OpenAI 兼容 ====================

@api_bp.route('/v1/chat/completions', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def openai_chat():
    """OpenAI 兼容格式"""
    data = request.json
    messages = data.get("messages", [])
    model = data.get("model", get_llm().default_model)

    if not messages:
        return jsonify({"error": {"message": "messages is required", "type": "invalid_request_error"}}), 400

    result = chat_with_ai(messages, model)

    if "error" in result:
        return jsonify({"error": {"message": result["error"], "type": "api_error"}}), 500

    try:
        content = result["choices"][0]["message"]["content"]
        return jsonify({
            "id": f"chatcmpl-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
            "object": "chat.completion",
            "created": int(datetime.datetime.now().timestamp()),
            "model": result.get("model", model),
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        })
    except (KeyError, IndexError) as e:
        logger.error(f"解析 OpenAI 响应失败: {e}")
        return jsonify({"error": {"message": "AI 响应解析失败", "type": "api_error"}}), 500


# ==================== 语音/Embedding API ====================

@api_bp.route('/v1/audio/transcriptions', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def audio_transcription():
    """语音转文�?- Whisper 兼容格式"""
    if 'file' not in request.files:
        return jsonify({"error": {"message": "file is required", "type": "invalid_request_error"}}), 400

    file = request.files['file']
    model_name = request.form.get('model', os.getenv('COSYVOICE_MODEL', 'FunAudioLLM/CosyVoice2-0.5B'))

    _llm = get_llm()
    api_key = _llm._get_api_key(model_name)
    if not api_key:
        return jsonify({"error": {"message": f"API key not configured for model: {model_name}"}}), 400

    url = f"{_llm.api_base}/audio/transcriptions"
    boundary = '----WebKitFormBoundary' + ''.join(['-' if i % 2 else '' for i in range(16)])

    audio_data = file.read()
    filename = file.filename or 'audio.wav'
    import mimetypes
    mime_type = mimetypes.guess_type(filename)[0] or 'audio/wav'

    body = (
        f'--{boundary}\r\n'
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f'Content-Type: {mime_type}\r\n\r\n'
    ).encode('utf-8') + audio_data + (
        f'\r\n--{boundary}\r\n'
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f'{model_name}\r\n'
        f'--{boundary}--\r\n'
    ).encode('utf-8')

    req = urllib.request.Request(
        url, data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            return jsonify(result)
    except Exception as e:
        logger.error(f"语音转文字失�? {e}")
        return jsonify({"error": {"message": "语音转文字服务暂时不可用", "type": "api_error"}}), 500


@api_bp.route('/v1/embeddings', methods=['POST'])
@rate_limit(max_requests=30, window_seconds=60)
def embeddings():
    """文本向量�?- OpenAI 兼容格式"""
    data = request.json
    model = data.get('model', os.getenv('EMBEDDING_MODEL', 'Qwen/Qwen3-Embedding-4B'))
    input_text = data.get('input', '')

    if not input_text:
        return jsonify({"error": {"message": "input is required", "type": "invalid_request_error"}}), 400

    _llm = get_llm()
    api_key = _llm._get_api_key(model)
    if not api_key:
        return jsonify({"error": {"message": f"API key not configured for model: {model}"}}), 400

    url = f"{_llm.api_base}/embeddings"
    req = urllib.request.Request(
        url, data=json.dumps({"model": model, "input": input_text}).encode('utf-8'),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            return jsonify(result)
    except Exception as e:
        logger.error(f"Embedding 失败: {e}")
        return jsonify({"error": {"message": "向量化服务暂时不可用", "type": "api_error"}}), 500


# ==================== 视觉分析 ====================

@api_bp.route('/api/vision/analyze', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def vision_analyze():
    """图片分析"""
    if 'file' not in request.files:
        return jsonify({"error": "file is required"}), 400

    file = request.files['file']
    question = request.form.get('question', '描述这张图片')
    model = request.form.get('model', 'Qwen/Qwen3-VL-32B-Instruct')

    api_key = os.getenv("QWEN_VL_API_KEY", "")
    if not api_key:
        return jsonify({"error": "视觉模型 API key 未配�?}), 500

    img_data = file.read()
    img_b64 = base64.b64encode(img_data).decode('utf-8')

    _llm = get_llm()
    url = f"{_llm.api_base}/chat/completions"

    payload = json.dumps({
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                {"type": "text", "text": question}
            ]
        }],
        "stream": False
    }).encode('utf-8')

    req = urllib.request.Request(
        url, data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            return jsonify({"response": content, "model": model})
    except Exception as e:
        logger.error(f"视觉分析失败: {e}")
        return jsonify({"error": "视觉分析服务暂时不可�?}), 500


# ==================== 模型列表 ====================

@api_bp.route('/api/models')
def list_models():
    available = get_llm().get_available_models()
    return jsonify({"models": available, "default": get_llm().default_model})


# ==================== 健康检�?& 节点 ====================

@api_bp.route('/api/health')
def health():
    return {"status": "ok", "nodes": len(state.nodes), "time": datetime.datetime.now().isoformat()}


@api_bp.route('/api/nodes')
def get_nodes():
    return jsonify(state.get_nodes_copy())


@api_bp.route('/api/nodes/<node_id>')
def get_node(node_id):
    return jsonify(state.get_node(node_id) or {})


@api_bp.route('/api/sensor', methods=['POST'])
def receive_sensor():
    data = request.json
    node_id = data.get("node_id")
    if not node_id:
        return jsonify({"error": "node_id is required"}), 400
    state.update_node(node_id, data)
    logger.info(f"收到节点 {node_id} 数据")

    if state.try_snapshot():
        try:
            from core.memory_system import get_memory
            mem = get_memory()
            scene_type = mem.scene.predict_next()
            mem.scene.snapshot(scene_type, state.get_nodes_copy(),
                               note=f"自动快照（节�?{node_id} 上报�?)
        except Exception as e:
            logger.error(f"场景快照失败: {e}")

    return {"success": True}


@api_bp.route('/api/presence')
def presence():
    import socketio as _sio
    nodes_data = state.get_nodes_copy()
    wifi_networks = []
    for nid, data in nodes_data.items():
        ssid = data.get("sensors", {}).get("wifi_ssid")
        if ssid:
            wifi_networks.append({"node": nid, "ssid": ssid})

    home_wifi = os.getenv("HOME_WIFI", "YourHomeWiFi")
    is_home = any(n.get("ssid") == home_wifi for n in wifi_networks)

    return jsonify({"is_home": is_home, "networks": wifi_networks})


# ==================== 命令队列 ====================

@api_bp.route('/api/commands/send', methods=['POST'])
def send_command():
    data = request.json
    node_id = data.get("node_id", "default")
    action = data.get("action", "")
    params = data.get("params", {})

    if not action:
        return jsonify({"error": "action is required"}), 400

    import uuid
    cmd_id = str(uuid.uuid4())[:8]

    cmd = {
        "id": cmd_id, "action": action, "params": params,
        "result": None, "status": "pending",
        "created": datetime.datetime.now().isoformat()
    }
    state.add_command(node_id, cmd)

    return jsonify({"success": True, "command_id": cmd_id})


@api_bp.route('/api/commands/pending/<node_id>', methods=['GET'])
def get_pending_commands(node_id):
    return jsonify(state.get_pending_commands(node_id))


@api_bp.route('/api/commands/complete', methods=['POST'])
def complete_command():
    data = request.json
    node_id = data.get("node_id", "default")
    command_id = data.get("command_id", "")
    result = data.get("result", {})
    success = data.get("success", True)
    state.complete_command(node_id, command_id, result, success)
    return jsonify({"success": True})

