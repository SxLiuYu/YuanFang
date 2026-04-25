# routes/vision.py
"""
Local Vision API — 基于 mlx-vlm 的本地多模态模型
支持图片理解，不依赖云端 API
"""
from flask import Blueprint, request, jsonify, send_file
import tempfile
import os
import logging
import base64
from pathlib import Path

logger = logging.getLogger(__name__)
vision_bp = Blueprint("vision", __name__, url_prefix="/api/vision")

# 模型配置
DEFAULT_MODEL = "mlx-community/Qwen3-VL-4B-Instruct-4bit"
MODEL_DIR = Path("~/omlx-models/vision").expanduser()

# 全局模型实例（加载一次）
_model_cache = {"model": None, "processor": None, "tokenizer": None, "loaded": False}

def init_vision_routes(app):
    app.register_blueprint(vision_bp)
    logger.info("[Vision] 路由已注册: /api/vision")


# ==================== 模型加载 ====================

def ensure_model(model_id: str = DEFAULT_MODEL):
    """确保模型已加载"""
    if _model_cache["loaded"] and _model_cache.get("model_id") == model_id:
        return True
    
    try:
        from mlx_vlm import load
        from pathlib import Path
        
        # 本地模型路径
        local_model_path = MODEL_DIR / model_id.replace("/", "_")
        
        if local_model_path.exists() and any(local_model_path.iterdir()):
            # 本地已有，直接加载
            logger.info(f"[Vision] 从本地加载模型: {local_model_path}")
            result = load(str(local_model_path))
        else:
            # 需要下载
            logger.info(f"[Vision] 下载并加载模型: {model_id}...")
            result = load(model_id)
        
        # mlx_vlm.load 返回 (model, processor) 或 (model, processor, tokenizer)
        if isinstance(result, tuple) and len(result) >= 2:
            _model_cache["model"] = result[0]
            _model_cache["processor"] = result[1]
            _model_cache["tokenizer"] = result[2] if len(result) > 2 else None
        else:
            _model_cache["model"] = result
            _model_cache["processor"] = None
            _model_cache["tokenizer"] = None
        
        _model_cache["loaded"] = True
        _model_cache["model_id"] = model_id
        logger.info(f"[Vision] 模型加载成功!")
        return True
    except Exception as e:
        logger.error(f"[Vision] 模型加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


# ==================== 路由 ====================

@vision_bp.route("/status", methods=["GET"])
def status():
    """检查 vision 模型状态"""
    model = _model_cache.get("model")
    return jsonify({
        "loaded": _model_cache.get("loaded", False),
        "model_id": _model_cache.get("model_id", None),
        "default_model": DEFAULT_MODEL,
        "model_dir": str(MODEL_DIR),
    })


@vision_bp.route("/health", methods=["GET"])
def health():
    """健康检查 + 模型状态"""
    loaded = _model_cache.get("loaded", False)
    return jsonify({
        "status": "ok" if loaded else "model_not_loaded",
        "loaded": loaded,
        "model": _model_cache.get("model_id", None),
    })


@vision_bp.route("/describe", methods=["POST"])
def describe():
    """
    图片描述 — 上传图片，返回文字描述
    
    POST /api/vision/describe
    Content-Type: multipart/form-data
    - image: 图片文件
    - prompt: 可选提示词 (默认: "描述这张图片")
    """
    if "image" not in request.files:
        return jsonify({"error": "未提供图片文件"}), 400
    
    image_file = request.files["image"]
    prompt = request.form.get("prompt", "请描述这张图片的内容")
    
    # 保存临时图片
    suffix = os.path.splitext(image_file.filename)[1] if image_file.filename else ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        image_path = tmp.name
        image_file.save(image_path)
    
    try:
        # 确保模型加载
        if not ensure_model():
            return jsonify({"error": "模型加载失败，请先下载模型"}), 500
        
        from mlx_vlm import generate
        from PIL import Image
        
        model = _model_cache["model"]
        processor = _model_cache["processor"]
        
        image = Image.open(image_path).convert("RGB")
        
        logger.info(f"[Vision] 生成描述... (prompt={prompt})")
        response = generate(
            model=model,
            processor=processor,
            image=image,
            prompt=prompt,
            max_tokens=256,
            temperature=0.7,
        )
        
        logger.info(f"[Vision] 描述完成: {response[:80]}...")
        
        return jsonify({
            "description": response,
            "prompt": prompt,
            "success": True,
        })
    
    except Exception as e:
        logger.error(f"[Vision] 描述失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "success": False}), 500
    
    finally:
        os.unlink(image_path)


@vision_bp.route("/chat", methods=["POST"])
def chat():
    """
    图片问答 — 上传图片 + 问题，返回回答
    
    POST /api/vision/chat
    Content-Type: multipart/form-data
    - image: 图片文件
    - question: 问题
    - max_tokens: 最大token数 (默认 256)
    """
    if "image" not in request.files:
        return jsonify({"error": "未提供图片文件"}), 400
    
    image_file = request.files["image"]
    question = request.form.get("question", "")
    max_tokens = int(request.form.get("max_tokens", 256))
    
    if not question:
        return jsonify({"error": "问题不能为空"}), 400
    
    suffix = os.path.splitext(image_file.filename)[1] if image_file.filename else ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        image_path = tmp.name
        image_file.save(image_path)
    
    try:
        if not ensure_model():
            return jsonify({"error": "模型加载失败"}), 500
        
        from mlx_vlm import generate
        from PIL import Image
        
        model = _model_cache["model"]
        processor = _model_cache["processor"]
        
        image = Image.open(image_path).convert("RGB")
        
        prompt = f"用户问题: {question}\n请根据图片回答:"
        
        logger.info(f"[Vision] 问答... (Q={question[:50]})")
        response = generate(
            model=model,
            processor=processor,
            image=image,
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        
        logger.info(f"[Vision] 回答: {response[:80]}...")
        
        return jsonify({
            "question": question,
            "answer": response,
            "success": True,
        })
    
    except Exception as e:
        logger.error(f"[Vision] 问答失败: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    
    finally:
        os.unlink(image_path)


@vision_bp.route("/download", methods=["POST"])
def download_model():
    """
    触发模型下载
    
    POST /api/vision/download
    {"model_id": "mlx-community/llava-1.6-mistral-7b-4bit"}
    """
    data = request.get_json() or {}
    model_id = data.get("model_id", DEFAULT_MODEL)
    
    try:
        if ensure_model(model_id):
            return jsonify({
                "status": "loaded",
                "model_id": model_id,
                "success": True,
            })
        else:
            return jsonify({
                "status": "download_failed",
                "model_id": model_id,
                "success": False,
            }), 500
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500
