"""
Multi-Channel Alert System
Sends alerts via Telegram, Discord, Email, SMS, Webhook
"""
from typing import List, Dict, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from loguru import logger

from utils.config import settings
from utils.notifications import NotificationManager


class AlertChannel(Enum):
    """Alert delivery channels"""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    SMS = "sms"
    WEBHOOK = "webhook"


class AlertPriority(Enum):
    """Alert priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Alert:
    """Alert model"""
    title: str
    message: str
    priority: AlertPriority
    channels: List[AlertChannel]
    timestamp: datetime = None
    metadata: Dict = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class AlertRule:
    """Base class for alert rules"""

    def __init__(self, name: str, priority: AlertPriority, channels: List[AlertChannel]):
        self.name = name
        self.priority = priority
        self.channels = channels
        self.enabled = True

    def evaluate(self, **kwargs) -> Optional[Alert]:
        """
        Evaluate if alert should be triggered
        Must be implemented by subclasses
        """
        raise NotImplementedError


class PriceAlert(AlertRule):
    """Alert when price crosses threshold"""

    def __init__(
        self,
        symbol: str,
        threshold: float,
        condition: str,  # "above" or "below"
        channels: List[AlertChannel] = None,
    ):
        channels = channels or [AlertChannel.TELEGRAM]
        super().__init__(
            f"Price Alert: {symbol}",
            AlertPriority.MEDIUM,
            channels,
        )
        self.symbol = symbol
        self.threshold = threshold
        self.condition = condition

    def evaluate(self, price: float) -> Optional[Alert]:
        """Evaluate price alert"""
        if self.condition == "above" and price > self.threshold:
            return Alert(
                title=f"{self.symbol} Price Alert",
                message=f"{self.symbol} price {price:.2f} is above threshold {self.threshold:.2f}",
                priority=self.priority,
                channels=self.channels,
                metadata={"symbol": self.symbol, "price": price, "threshold": self.threshold},
            )
        elif self.condition == "below" and price < self.threshold:
            return Alert(
                title=f"{self.symbol} Price Alert",
                message=f"{self.symbol} price {price:.2f} is below threshold {self.threshold:.2f}",
                priority=self.priority,
                channels=self.channels,
                metadata={"symbol": self.symbol, "price": price, "threshold": self.threshold},
            )
        return None


class PortfolioAlert(AlertRule):
    """Alert on portfolio P&L thresholds"""

    def __init__(
        self,
        threshold_pct: float,
        condition: str,  # "gain" or "loss"
        channels: List[AlertChannel] = None,
    ):
        channels = channels or [AlertChannel.TELEGRAM, AlertChannel.EMAIL]
        priority = AlertPriority.CRITICAL if condition == "loss" else AlertPriority.HIGH
        super().__init__(f"Portfolio {condition.capitalize()} Alert", priority, channels)
        self.threshold_pct = threshold_pct
        self.condition = condition

    def evaluate(self, pnl_percent: float) -> Optional[Alert]:
        """Evaluate portfolio alert"""
        if self.condition == "loss" and pnl_percent < -self.threshold_pct:
            return Alert(
                title="Portfolio Loss Alert",
                message=f"Portfolio loss {pnl_percent:.2f}% exceeds threshold {self.threshold_pct:.2f}%",
                priority=self.priority,
                channels=self.channels,
                metadata={"pnl_percent": pnl_percent, "threshold": self.threshold_pct},
            )
        elif self.condition == "gain" and pnl_percent > self.threshold_pct:
            return Alert(
                title="Portfolio Gain Alert",
                message=f"Portfolio gain {pnl_percent:.2f}% exceeds threshold {self.threshold_pct:.2f}%",
                priority=self.priority,
                channels=self.channels,
                metadata={"pnl_percent": pnl_percent, "threshold": self.threshold_pct},
            )
        return None


class AlertSystem:
    """
    Multi-Channel Alert System

    Supports:
    - Telegram
    - Discord
    - Email
    - SMS (via Twilio)
    - Webhook
    """

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.alert_history: List[Alert] = []
        self.notification_manager = NotificationManager()

        # Discord webhook
        self.discord_webhook_url = None

        # Email settings
        self.email_smtp_server = None
        self.email_smtp_port = None
        self.email_from = None
        self.email_password = None
        self.email_to = []

        # SMS settings (Twilio)
        self.twilio_account_sid = None
        self.twilio_auth_token = None
        self.twilio_from_number = None
        self.twilio_to_numbers = []

        # Custom webhook
        self.custom_webhook_url = None

    def add_rule(self, rule: AlertRule):
        """Add alert rule"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove alert rule"""
        self.rules = [r for r in self.rules if r.name != rule_name]

    def configure_discord(self, webhook_url: str):
        """Configure Discord webhook"""
        self.discord_webhook_url = webhook_url
        logger.info("Discord webhook configured")

    def configure_email(
        self,
        smtp_server: str,
        smtp_port: int,
        from_email: str,
        password: str,
        to_emails: List[str],
    ):
        """Configure email alerts"""
        self.email_smtp_server = smtp_server
        self.email_smtp_port = smtp_port
        self.email_from = from_email
        self.email_password = password
        self.email_to = to_emails
        logger.info("Email alerts configured")

    def send_alert(self, alert: Alert):
        """Send alert via configured channels"""
        logger.info(f"Sending alert: {alert.title} via {[c.value for c in alert.channels]}")

        for channel in alert.channels:
            try:
                if channel == AlertChannel.TELEGRAM:
                    self._send_telegram(alert)
                elif channel == AlertChannel.DISCORD:
                    self._send_discord(alert)
                elif channel == AlertChannel.EMAIL:
                    self._send_email(alert)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook(alert)
            except Exception as e:
                logger.error(f"Failed to send alert via {channel.value}: {e}")

        self.alert_history.append(alert)

    def _send_telegram(self, alert: Alert):
        """Send via Telegram"""
        emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔔",
            AlertPriority.CRITICAL: "🚨",
        }

        message = f"{emoji[alert.priority]} {alert.title}\n\n{alert.message}"
        self.notification_manager.send_notification(message)

    def _send_discord(self, alert: Alert):
        """Send via Discord webhook"""
        if not self.discord_webhook_url:
            logger.warning("Discord webhook not configured")
            return

        color = {
            AlertPriority.LOW: 0x00FF00,
            AlertPriority.MEDIUM: 0xFFFF00,
            AlertPriority.HIGH: 0xFF9900,
            AlertPriority.CRITICAL: 0xFF0000,
        }

        payload = {
            "embeds": [
                {
                    "title": alert.title,
                    "description": alert.message,
                    "color": color[alert.priority],
                    "timestamp": alert.timestamp.isoformat(),
                    "footer": {"text": "DNSE Insight Alert System"},
                }
            ]
        }

        response = requests.post(self.discord_webhook_url, json=payload)
        response.raise_for_status()

    def _send_email(self, alert: Alert):
        """Send via email"""
        if not self.email_smtp_server:
            logger.warning("Email not configured")
            return

        msg = MIMEMultipart()
        msg["From"] = self.email_from
        msg["To"] = ", ".join(self.email_to)
        msg["Subject"] = f"[{alert.priority.name}] {alert.title}"

        body = f"""
        {alert.title}

        {alert.message}

        Priority: {alert.priority.name}
        Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

        ---
        DNSE Insight Alert System
        """

        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self.email_smtp_server, self.email_smtp_port) as server:
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.send_message(msg)

    def _send_webhook(self, alert: Alert):
        """Send via custom webhook"""
        if not self.custom_webhook_url:
            logger.warning("Custom webhook not configured")
            return

        payload = {
            "title": alert.title,
            "message": alert.message,
            "priority": alert.priority.name,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }

        response = requests.post(self.custom_webhook_url, json=payload)
        response.raise_for_status()

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get recent alerts"""
        return self.alert_history[-limit:]


# Global instance
alert_system = AlertSystem()
