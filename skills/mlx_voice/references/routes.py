# skills/mlx_voice/references/routes.py
"""
MLX Voice API Routes — 接入 YuanFang Flask app
"""
from flask import Blueprint, request, jsonify, send_file
import logging
from pathlib import Path
import base64

logger = logging.getLogger(__name__)

mlx_voice_bp = Blueprint("mlx_voice", __name__, url_prefix="/api/mlx-voice")


def init_mlx_voice_routes(app):
    """注册 MLX Voice 路由"""
    app.register_blueprint(mlx_voice_bp)
    logger.info("[MLX Voice] 路由已注册: /api/mlx-voice")


# ==================== 健康检查 ====================

@mlx_voice_bp.route("/health", methods=["GET"])
def health():
    """检查 MLX Voice 各组件状态"""
    from .mlx_voice import health_check
    return jsonify(health_check())


# ==================== 语音管线 ====================

@mlx_voice_bp.route("/transcribe", methods=["POST"])
def transcribe_route():
    """
    语音转文字
    
    POST /api/mlx-voice/transcribe
    Content-Type: multipart/form-data
    
    参数:
        audio: 音频文件
    """
    if "audio" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400
    
    audio_file = request.files["audio"]
    
    # 保存临时文件
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)
    
    try:
        from .mlx_voice import transcribe
        text = transcribe(audio_path)
        return jsonify({"text": text, "success": True})
    except Exception as e:
        logger.error(f"[MLX Voice] 转写失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        os.unlink(audio_path)


@mlx_voice_bp.route("/chat", methods=["POST"])
def chat_route():
    """
    LLM 对话 (通过 OMLX Server)
    
    POST /api/mlx-voice/chat
    Content-Type: application/json
    
    {
        "message": "用户消息",
        "system_prompt": "系统提示词 (可选)",
        "model": "模型名 (可选)",
        "max_tokens": 512,
        "temperature": 0.7
    }
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "未提供消息"}), 400
    
    try:
        from .mlx_voice import chat
        response = chat(
            message=data["message"],
            system_prompt=data.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。"),
            model=data.get("model", "gemma-4-E4B-it-4bit"),
            max_tokens=data.get("max_tokens", 512),
            temperature=data.get("temperature", 0.7),
        )
        return jsonify({"response": response, "success": True})
    except Exception as e:
        logger.error(f"[MLX Voice] LLM 失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@mlx_voice_bp.route("/tts", methods=["POST"])
def tts_route():
    """
    文字转语音
    
    POST /api/mlx-voice/tts
    Content-Type: application/json
    
    {
        "text": "要朗读的文字",
        "voice": "af_heart (可选)"
    }
    """
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "未提供文字"}), 400
    
    try:
        from .mlx_voice import speak
        audio_file = speak(
            text=data["text"],
            voice=data.get("voice", "af_heart"),
        )
        return send_file(audio_file, mimetype="audio/wav")
    except Exception as e:
        logger.error(f"[MLX Voice] TTS 失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@mlx_voice_bp.route("/fast", methods=["POST"])
def fast_route():
    """
    快速语音管线: STT → LLM → 只返回文字（无 TTS）
    延迟约 5-8 秒，比完整管线快 2-3 倍
    
    POST /api/mlx-voice/fast
    Content-Type: multipart/form-data
    
    参数:
        audio: 音频文件
        system_prompt: 系统提示词 (可选)
        max_tokens: 最大 token 数 (可选，默认 128)
    
    返回:
        {
            "text": "用户说的话",
            "response": "LLM 回复",
            "success": true
        }
    """
    if "audio" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400
    
    audio_file = request.files["audio"]
    system_prompt = request.form.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。")
    max_tokens = int(request.form.get("max_tokens", 128))
    
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)
    
    try:
        from .mlx_voice import transcribe, chat
        
        # STT
        user_text = transcribe(audio_path)
        logger.info(f"[MLX Voice Fast] 用户: {user_text}")
        
        # LLM（限制 max_tokens 加速）
        llm_response = chat(user_text, system_prompt=system_prompt, max_tokens=max_tokens)
        logger.info(f"[MLX Voice Fast] 助手: {llm_response[:50]}...")
        
        return jsonify({
            "text": user_text,
            "response": llm_response,
            "success": True,
        })
    except Exception as e:
        logger.error(f"[MLX Voice Fast] 失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        os.unlink(audio_path)


@mlx_voice_bp.route("/pipeline", methods=["POST"])
def pipeline_route():
    """
    完整语音管线: STT → LLM → TTS
    
    POST /api/mlx-voice/pipeline
    Content-Type: multipart/form-data
    
    参数:
        audio: 音频文件
        system_prompt: 系统提示词 (可选)
        voice: TTS 声音 (可选)
        use_tts: 是否生成语音 (默认 True)
    
    返回:
        {
            "text": "用户说的话",
            "response": "LLM 回复",
            "audio_file": "语音文件路径 (base64)",
            "success": true
        }
    """
    if "audio" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400
    
    audio_file = request.files["audio"]
    system_prompt = request.form.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。")
    voice = request.form.get("voice", "af_heart")
    use_tts = request.form.get("use_tts", "true").lower() != "false"
    
    # 保存临时文件
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)
    
    try:
        from .mlx_voice import voice_pipeline
        
        result = voice_pipeline(
            audio_path=audio_path,
            system_prompt=system_prompt,
            use_tts=use_tts,
            voice=voice,
        )
        
        if result["success"]:
            response = {
                "text": result["text"],
                "response": result["response"],
                "success": True,
            }
            if result["audio_file"]:
                # 返回 base64 编码的音频
                with open(result["audio_file"], "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                response["audio_file"] = result["audio_file"]
                response["audio_data"] = audio_b64
            return jsonify(response)
        else:
            return jsonify({"error": result["error"], "success": False}), 500
            
    except Exception as e:
        logger.error(f"[MLX Voice] 管线失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        os.unlink(audio_path)