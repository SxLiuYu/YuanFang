"""
🤖 元芳 - AI 智能家居助手（主入口�?

经过全面优化后的主入口文件，仅负责：
1. 初始�?Flask + SocketIO
2. 注册 Blueprint 路由
3. 初始化全局服务
4. 启动服务

所有业务逻辑已拆分到 routes/ 和独立模块中�?
"""
import os
import sys
import logging

from flask import Flask, Response
from flask_socketio import SocketIO
from dotenv import load_dotenv

# 初始化日志（替代 print�?
from core.app_logging import setup_logging
setup_logging()
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# CORS 配置：从环境变量读取，不再全开
_cors_origins = os.getenv("CORS_ORIGINS", "*")
socketio = SocketIO(app, cors_allowed_origins=_cors_origins)

# ==================== 注册安全中间�?====================
from services.app_security import init_auth, register_error_handlers, add_security_headers, rate_limit

init_auth()
register_error_handlers(app)

# 每个响应添加安全�?
@app.after_request
def _add_security_headers(response):
    return add_security_headers(response)


# ==================== 初始化全局服务 ====================

from core.llm_adapter import get_llm
from services.daemon_mode import KairosDaemon
from services.kairos_tools import get_kairos_tools
from core.rule_engine import get_rule_engine
from services.notification_hub import get_notification_hub
from routes.chat import _execute_ha_commands

_llm = get_llm()

# KAIROS 守护进程
_kairos_daemon = None
_kairos_tools = None
_rule_engine = None
_notification_hub = None


# ==================== 注册 Blueprint 路由 ====================

from routes.openai_compat import api_bp
from routes.chat import chat_bp, _voice_chat_pipeline, init_chat
from routes.ha import ha_bp
from routes.agent import agent_bp, init_agent
from routes.rules_users import sys_bp, init_sys

app.register_blueprint(api_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(ha_bp)
app.register_blueprint(agent_bp)
app.register_blueprint(sys_bp)

# 注册 WebSocket 事件
from routes.ws_events import register_handlers
register_handlers(socketio)


# ==================== 静态页�?====================

@app.route('/')
def index():
    """元芳控制台页�?""
    html_path = os.path.join(os.path.dirname(__file__), "static", "dashboard.html")
    with open(html_path, "rb") as f:
        return Response(f.read(), status=200, content_type="text/html; charset=utf-8")


@app.route('/pwa/<path:filename>')
def pwa_static(filename):
    """PWA 静态资�?""
    pwa_dir = os.path.join(os.path.dirname(__file__), 'pwa')
    from flask import send_from_directory
    return send_from_directory(pwa_dir, filename)


# ==================== 启动 ====================

def main():
    global _kairos_daemon, _kairos_tools, _rule_engine, _notification_hub

    port = int(os.getenv("PORT", 8000))

    logger.info("=" * 50)
    logger.info("🤖 元芳 AI 智能助手（优化版�?)
    logger.info("=" * 50)
    logger.info(f"API: {_llm.api_base}")
    logger.info(f"默认模型: {_llm.default_model}")
    logger.info(f"服务地址: http://localhost:{port}")
    logger.info(f"CORS: {_cors_origins}")
    logger.info("=" * 50)

    # 初始化通知中心
    _notification_hub = get_notification_hub(socketio)

    # 初始化规则引�?
    _rule_engine = get_rule_engine()
    _rule_engine.set_ha_executor(_execute_ha_commands)
    _rule_engine.set_notify_fn(
        lambda title, message, level, **kw: _notification_hub.notify(title, message, level)
        if _notification_hub else None
    )
    _rule_engine.set_skill_engine_fn(lambda: __import__("skill_engine", fromlist=["get_skill_engine"]).get_skill_engine())

    # 启动 KAIROS 守护进程（默认启用）
    kairos_enabled = os.getenv("KAIROS_ENABLED", "true").lower() == "true"
    if kairos_enabled:
        _kairos_daemon = KairosDaemon()
        _kairos_tools = get_kairos_tools(socketio)
        _kairos_daemon.set_tools(_kairos_tools)
        _kairos_daemon.set_rule_engine(_rule_engine)
        _kairos_daemon.start()
        logger.info("🌙 KAIROS 守护进程已启�?)

    # 注入依赖到各模块
    init_chat(socketio, _kairos_daemon)
    init_agent(_kairos_daemon, _kairos_tools, _rule_engine, _notification_hub)
    init_sys(_rule_engine, _notification_hub)
    from routes.ws_events import init_ws
    init_ws(socketio, _voice_chat_pipeline)

    # 启动 Telegram Bot
    tg_enabled = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"
    if tg_enabled:
        try:
            from telegram_bot import start_telegram_bot
            start_telegram_bot(background=True)
            logger.info("📱 Telegram Bot 已启�?)
        except Exception as e:
            logger.error(f"Telegram Bot 启动失败: {e}")

    # 连接 MQTT
    mqtt_enabled = os.getenv("MQTT_HOST", "")
    if mqtt_enabled:
        try:
            from adapters.mqtt_adapter import get_mqtt
            mqtt = get_mqtt()
            if mqtt.connect(timeout=5):
                mqtt_config = os.getenv("MQTT_DEVICES_CONFIG", "")
                if mqtt_config:
                    mqtt.load_devices_from_config(mqtt_config)
                logger.info(f"📡 MQTT 已连�?({mqtt.host}:{mqtt.port}), {len(mqtt.list_devices())} 设备")
            else:
                logger.warning(f"MQTT 连接失败 ({mqtt.host}:{mqtt.port})")
        except Exception as e:
            logger.error(f"MQTT 启动失败: {e}")

    logger.info(f"🚀 服务启动中，端口 {port}...")
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)


if __name__ == "__main__":
    main()


