# routes/openai_compat.py
"""
OpenAI 兼容 API · OpenAI Compatible Endpoints
/api/v1/* 端点模拟 OpenAI Chat Completions API
"""
from flask import Blueprint, request, jsonify
import logging

logger = logging.getLogger(__name__)

openai_bp = Blueprint("openai", __name__, url_prefix="/api/v1")
api_bp = openai_bp  # Alias for backward compatibility


@openai_bp.route("/chat/completions", methods=["POST"])
def chat_completions():
    """
    兼容 OpenAI Chat Completions API
    POST /api/v1/chat/completions
    Body: {"model": "...", "messages": [...], "stream": false}
    """
    data = request.json or {}
    model = data.get("model", "Pro/deepseek-ai/DeepSeek-V3.1-Terminus")
    messages = data.get("messages", [])
    stream = data.get("stream", False)

    if not messages:
        return jsonify({"error": {"message": "messages is required", "type": "invalid_request_error"}}), 400

    try:
        from core.llm_adapter import get_llm
        llm = get_llm()
        response = llm.chat_simple(messages, model=model)

        return jsonify({
            "id": f"chatcmpl-{__import__('uuid').uuid4().hex[:8]}",
            "object": "chat.completion",
            "created": __import__("time").time(),
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": response},
                "finish_reason": "stop",
            }],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        })
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        return jsonify({"error": {"message": str(e), "type": "api_error"}}), 500


@openai_bp.route("/models", methods=["GET"])
def list_models():
    """列出可用模型"""
    try:
        from core.llm_adapter import get_llm
        llm = get_llm()
        models = llm.models()
        return jsonify({
            "object": "list",
            "data": [{"id": m, "object": "model"} for m in models],
        })
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500
