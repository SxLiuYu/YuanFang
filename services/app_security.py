"""
🛡️ 安全中间件
提供 API 认证、速率限制、统一错误处理。
"""
import os
import time
import functools
import logging
from flask import request, jsonify
from collections import defaultdict

logger = logging.getLogger(__name__)

# ==================== API 认证 ====================
# 从环境变量读取 API Key（支持多 key，用逗号分隔）
_API_KEYS = set()
_AUTH_ENABLED = False


def init_auth():
    """初始化认证配置"""
    global _API_KEYS, _AUTH_ENABLED
    keys = os.getenv("API_AUTH_KEYS", "")
    if keys:
        _API_KEYS = {k.strip() for k in keys.split(",") if k.strip()}
        _AUTH_ENABLED = len(_API_KEYS) > 0
    if _AUTH_ENABLED:
        logger.info(f"API 认证已启用，{len(_API_KEYS)} 个 key 已加载")
    else:
        logger.warning("API 认证未启用，所有接口公开访问")


def require_auth(f):
    """
    API 认证装饰器。
    通过 Header (X-API-Key) 或 Query (?key=xxx) 传递。
    健康检查和静态资源路由不需要认证。
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not _AUTH_ENABLED:
            return f(*args, **kwargs)
        api_key = request.headers.get("X-API-Key") or request.args.get("key", "")
        if not api_key or api_key not in _API_KEYS:
            return jsonify({"error": "unauthorized", "message": "Invalid or missing API key"}), 401
        return f(*args, **kwargs)
    return decorated


# ==================== 速率限制 ====================
# 简单的滑动窗口速率限制（基于客户端 IP）
_rate_limit_store: dict = defaultdict(list)  # { ip: [timestamp, ...] }
_rate_limit_lock = __import__("threading").Lock()


def _get_client_ip() -> str:
    """获取客户端真实 IP（支持反向代理）"""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def rate_limit(max_requests: int = 60, window_seconds: int = 60):
    """
    速率限制装饰器。
    默认：每个 IP 每分钟 60 次请求。
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            ip = _get_client_ip()
            now = time.time()

            with _rate_limit_lock:
                timestamps = _rate_limit_store[ip]
                # 清理过期记录
                _rate_limit_store[ip] = [t for t in timestamps if now - t < window_seconds]
                timestamps = _rate_limit_store[ip]

                if len(timestamps) >= max_requests:
                    return jsonify({
                        "error": "rate_limited",
                        "message": f"Rate limit exceeded: {max_requests} requests per {window_seconds}s",
                        "retry_after": window_seconds - (now - timestamps[0]),
                    }), 429

                timestamps.append(now)

            return f(*args, **kwargs)
        return decorated
    return decorator


# ==================== 统一错误处理 ====================
def register_error_handlers(app):
    """注册 Flask 全局错误处理器"""

    @app.errorhandler(400)
    def handle_400(e):
        return jsonify({"error": "bad_request", "message": "请求参数错误"}), 400

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "not_found", "message": "资源不存在"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "method_not_allowed", "message": "请求方法不允许"}), 405

    @app.errorhandler(500)
    def handle_500(e):
        logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({"error": "internal_error", "message": "服务器内部错误，请稍后重试"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        return jsonify({"error": "internal_error", "message": "服务器内部错误，请稍后重试"}), 500


# ==================== 安全响应头 ====================
def add_security_headers(response):
    """为所有响应添加安全头"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response
