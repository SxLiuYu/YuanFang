# routes/ws_events.py
"""
WebSocket 事件处理 · WS Events
"""
from flask_socketio import emit, disconnect
import logging

logger = logging.getLogger(__name__)

_socketio = None
_voice_pipeline = None


def init_ws(socketio, voice_pipeline):
    global _socketio, _voice_pipeline
    _socketio = socketio
    _voice_pipeline = voice_pipeline


def register_handlers(socketio):
    """注册所有 WebSocket 事件处理器"""

    @socketio.on("connect")
    def on_connect():
        logger.info("Client connected")
        emit("connected", {"status": "ok"})

    @socketio.on("disconnect")
    def on_disconnect():
        logger.info("Client disconnected")

    @socketio.on("message")
    def on_message(data):
        logger.info(f"WS message: {data}")
        emit("response", {"echo": data})

    @socketio.on("voice_input")
    def on_voice(data):
        logger.info("Voice input received")
        # Forward to voice pipeline
        if _voice_pipeline:
            try:
                result = _voice_pipeline.process(data)
                emit("voice_result", result)
            except Exception as e:
                logger.error(f"Voice pipeline error: {e}")
                emit("voice_result", {"error": str(e)})

    @socketio.on("memory_event")
    def on_memory_event(data):
        logger.info(f"Memory event: {data}")
        emit("memory_ack", {"received": True})

    @socketio.on("skill_event")
    def on_skill_event(data):
        logger.info(f"Skill event: {data}")
        emit("skill_ack", {"received": True})

    @socketio.on("ping")
    def on_ping():
        emit("pong", {"ts": __import__("time").time()})
