# services/notification_hub.py
"""
通知中心 · NotificationHub
多渠道推送：WebSocket / Telegram / 微信 / 邮件
"""
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationHub:
    """
    统一通知中心
    支持多渠道：WebSocket（实时）、Telegram（已配置时）
    """

    def __init__(self):
        self._socketio = None
        self._telegram = None
        self._queue = []

    def set_socketio(self, socketio):
        self._socketio = socketio

    def set_telegram(self, bot):
        self._telegram = bot

    def notify(self, title: str, message: str, level: str = "info",
                urgent: bool = False, **kwargs):
        """
        发送通知
        level: info | warning | error | success
        """
        payload = {
            "title": title,
            "message": message,
            "level": level,
            "urgent": urgent,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }

        # WebSocket 实时推送
        if self._socketio:
            try:
                self._socketio.emit("notification", payload, namespace="/")
            except Exception as e:
                logger.warning(f"WebSocket notify failed: {e}")

        # Telegram
        if self._telegram:
            try:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "🚨", "success": "✅"}.get(level, "ℹ️")
                self._telegram.send_message(f"{icon} {title}\n{message}")
            except Exception as e:
                logger.warning(f"Telegram notify failed: {e}")

        self._queue.append(payload)
        if len(self._queue) > 100:
            self._queue = self._queue[-100:]

        logger.info(f"[NotificationHub] {level}: {title} — {message}")
        return payload

    def info(self, title: str, message: str, **kwargs):
        return self.notify(title, message, "info", **kwargs)

    def warning(self, title: str, message: str, **kwargs):
        return self.notify(title, message, "warning", **kwargs)

    def error(self, title: str, message: str, **kwargs):
        return self.notify(title, message, "error", **kwargs)

    def success(self, title: str, message: str, **kwargs):
        return self.notify(title, message, "success", **kwargs)

    def recent(self, n: int = 20):
        return self._queue[-n:]


_hub: Optional[NotificationHub] = None


def get_notification_hub() -> NotificationHub:
    global _hub
    if _hub is None:
        _hub = NotificationHub()
    return _hub
