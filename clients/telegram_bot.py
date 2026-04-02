# clients/telegram_bot.py
"""
Telegram Bot 客户端
"""
import os
import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# 尝试导入 python-telegram-bot
try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed, Telegram bot unavailable")


class TelegramBot:
    def __init__(self, token: str = None):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.app: Optional["Application"] = None
        self._running = False
        self._chat_ids = set()

    def start(self, background: bool = False):
        if not TELEGRAM_AVAILABLE or not self.token:
            logger.warning("Telegram bot not available (token or library missing)")
            return

        self.app = Application.builder().token(self.token).build()

        self.app.add_handler(CommandHandler("start", self._on_start))
        self.app.add_handler(CommandHandler("status", self._on_status))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._on_message))

        if background:
            threading.Thread(target=self._run, daemon=True).start()
            self._running = True
            logger.info("Telegram bot started in background")
        else:
            self._run()

    def _run(self):
        if self.app:
            self.app.run_polling()

    def stop(self):
        if self.app:
            self.app.stop()
            self._running = False

    async def _on_start(self, update: "Update"):
        await update.message.reply_text("元芳 Telegram Bot 已连接！发送消息即可与我对话。")
        self._chat_ids.add(update.effective_chat.id)

    async def _on_status(self, update: "Update"):
        from core.personality import get_personality
        from core.memory_system import get_memory
        personality = get_personality()
        memory = get_memory()
        status = personality.get_status()
        report = memory.full_report()
        await update.message.reply_text(
            f"元芳状态\n"
            f"心情: {status['mood']}\n"
            f"精力: {status['energy']:.0%}\n"
            f"记忆: {report['emotional']['total']} 条情感记录"
        )

    async def _on_message(self, update: "Update"):
        text = update.message.text
        logger.info(f"Telegram message: {text}")
        self._chat_ids.add(update.effective_chat.id)
        # Forward to chat pipeline
        try:
            from routes.chat import _execute_ha_commands
            response = f"[Echo] {text}"
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Telegram message error: {e}")
            await update.message.reply_text(f"Error: {e}")

    def send_message(self, text: str, chat_id: int = None):
        """发送消息到 Telegram"""
        if not self.app or not self._running:
            logger.warning("Telegram bot not running")
            return

        async def _send():
            chat_ids = [chat_id] if chat_id else list(self._chat_ids)
            for cid in chat_ids:
                try:
                    await self.app.bot.send_message(chat_id=cid, text=text)
                except Exception as e:
                    logger.error(f"Telegram send failed: {e}")

        import asyncio
        asyncio.run(_send())


_bot: Optional[TelegramBot] = None


def start_telegram_bot(background: bool = False) -> Optional[TelegramBot]:
    global _bot
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram library not available")
        return None
    _bot = TelegramBot()
    _bot.start(background=background)
    return _bot


def get_telegram_bot() -> Optional[TelegramBot]:
    return _bot
