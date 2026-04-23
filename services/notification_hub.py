# services/notification_hub.py
"""
Notification Hub - 统一通知中心
WebSocket / Telegram / Dashboard / Log 多通道推送
"""
import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationHub:
    """
    统一通知中心
    
    支持通道：
    - WebSocket (dashboard / voice_nodes)
    - Telegram Bot
    - 系统日志
    """

    def __init__(self, socketio=None, telegram_bot=None):
        self._socketio = socketio
        self._telegram = telegram_bot
        self._queue = []
        self._max_queue = 100
        self._channels = {
            "websocket": {"enabled": True, "name": "WebSocket"},
            "telegram": {"enabled": telegram_bot is not None, "name": "Telegram"},
            "log": {"enabled": True, "name": "System Log"},
        }

    def notify(self, title: str, message: str, level: str = "info",
               target: str = "all") -> dict:
        """
        发送通知
        
        Args:
            title: 通知标题
            message: 通知内容
            level: info / warning / success / error
            target: all / dashboard / voice_nodes / telegram
        
        Returns:
            {"success": bool, "channels": [sent, failed]}
        """
        notification = {
            "type": "notification",
            "title": title,
            "message": message,
            "level": level,
            "target": target,
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self._queue.append(notification)
        if len(self._queue) > self._max_queue:
            self._queue = self._queue[-self._max_queue:]

        sent = []
        failed = []

        # WebSocket
        if self._channels.get("websocket", {}).get("enabled"):
            if target in ("all", "dashboard"):
                try:
                    if self._socketio:
                        self._socketio.emit("notification", notification)
                    sent.append("websocket")
                except Exception as e:
                    logger.warning(f"WebSocket send failed: {e}")
                    failed.append("websocket")

        # Telegram
        if self._channels.get("telegram", {}).get("enabled"):
            if target in ("all", "telegram"):
                try:
                    if self._telegram:
                        self._telegram.send_message(f"[{level.upper()}] {title}\n{message}")
                    sent.append("telegram")
                except Exception as e:
                    logger.warning(f"Telegram send failed: {e}")
                    failed.append("telegram")

        # Log
        if self._channels.get("log", {}).get("enabled"):
            log_fn = logger.info
            if level == "warning":
                log_fn = logger.warning
            elif level == "error":
                log_fn = logger.error
            log_fn(f"[Notification] {title}: {message}")
            sent.append("log")

        return {"success": len(failed) == 0, "channels": {"sent": sent, "failed": failed}}

    def get_recent(self, n: int = 20) -> list:
        """获取最近 n 条通知"""
        return self._queue[-n:]

    def clear(self):
        """清空通知队列"""
        self._queue.clear()

    def set_channel(self, channel: str, enabled: bool):
        """启用/禁用某个通道"""
        if channel in self._channels:
            self._channels[channel]["enabled"] = enabled

    def broadcast(self, event: str, data: dict):
        """广播消息给所有WebSocket连接（包括Termux语音节点）"""
        if self._socketio is None:
            logger.warning("No socketio instance, broadcast skipped")
            return {"success": False, "error": "no socketio"}
        
        try:
            self._socketio.emit(event, data)
            logger.info(f"[Broadcast] {event} → all connections")
            return {"success": True}
        except Exception as e:
            logger.warning(f"Broadcast failed: {e}")
            return {"success": False, "error": str(e)}


_notification_hub = None


def get_notification_hub(socketio=None, telegram_bot=None) -> NotificationHub:
    global _notification_hub
    if _notification_hub is None:
        _notification_hub = NotificationHub(socketio=socketio, telegram_bot=telegram_bot)
    return _notification_hub
