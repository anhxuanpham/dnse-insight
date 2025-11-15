"""
Notification Manager for sending alerts via Telegram
"""
import asyncio
from typing import Optional
from loguru import logger
from utils.config import settings

try:
    from telegram import Bot
    from telegram.error import TelegramError

    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed, notifications disabled")


class NotificationManager:
    """
    Manages notifications to Telegram
    Supports sending trading alerts, signals, and portfolio updates
    """

    def __init__(self):
        self.enabled = settings.telegram_enabled and TELEGRAM_AVAILABLE
        self.bot: Optional[Bot] = None
        self.chat_id = settings.telegram_chat_id

        if self.enabled:
            if not settings.telegram_bot_token:
                logger.warning("Telegram bot token not configured")
                self.enabled = False
            elif not self.chat_id:
                logger.warning("Telegram chat ID not configured")
                self.enabled = False
            else:
                try:
                    self.bot = Bot(token=settings.telegram_bot_token)
                    logger.info("Telegram notification manager initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Telegram bot: {e}")
                    self.enabled = False

    def send_notification(self, message: str, parse_mode: str = None) -> bool:
        """
        Send a notification message
        Returns True if successful, False otherwise
        """
        if not self.enabled:
            logger.debug(f"Notification (disabled): {message}")
            return False

        try:
            # Run async in sync context
            asyncio.run(self._send_async(message, parse_mode))
            logger.debug(f"Notification sent: {message[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    async def _send_async(self, message: str, parse_mode: str = None):
        """
        Send message asynchronously
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id, text=message, parse_mode=parse_mode
            )
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
            raise

    def send_trade_alert(
        self, action: str, symbol: str, quantity: int, price: float, reason: str = ""
    ):
        """
        Send a trade alert notification
        """
        emoji_map = {
            "BUY": "✅",
            "SELL": "📤",
            "CUTLOSS": "⚠️",
            "DCA": "🔄",
        }

        emoji = emoji_map.get(action.upper(), "📊")

        message = (
            f"{emoji} {action.upper()} {symbol}\n"
            f"Quantity: {quantity}\n"
            f"Price: {price:,.2f} VND\n"
            f"Total: {quantity * price:,.0f} VND"
        )

        if reason:
            message += f"\nReason: {reason}"

        return self.send_notification(message)

    def send_portfolio_update(self, summary: dict):
        """
        Send portfolio summary notification
        """
        message = (
            f"📊 Portfolio Update\n\n"
            f"Total Value: {summary['total_value']:,.0f} VND\n"
            f"P&L: {summary['total_pnl']:+,.0f} VND ({summary['total_return']:+.2%})\n"
            f"Positions: {summary['num_positions']}\n"
            f"Max Drawdown: {summary['max_drawdown']:.2%}"
        )

        return self.send_notification(message)

    def send_error_alert(self, error_message: str):
        """
        Send error alert notification
        """
        message = f"❌ Error Alert\n\n{error_message}"
        return self.send_notification(message)
