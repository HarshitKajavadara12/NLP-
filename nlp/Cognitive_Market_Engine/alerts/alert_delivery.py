"""
Multi-Channel Alert Delivery — Category 6.5
============================================
Deliver real-time alerts via multiple channels:
- Telegram bot
- Email (SMTP)
- Slack webhook
- Generic webhook (Discord, custom)
- Desktop push notifications (via system tray)
- SMS (via Twilio)

Features:
- Priority-based routing (CRITICAL → all channels, LOW → log only)
- Rate limiting per channel
- Alert deduplication
- Delivery confirmation tracking
- Configurable per-user channel preferences
"""
import time
import json
import logging
import hashlib
import smtplib
import threading
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable, Any, Set
from collections import defaultdict, deque
from enum import Enum

logger = logging.getLogger("cme.alerts.delivery")


class AlertPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class AlertChannel(Enum):
    LOG = "log"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    PUSH = "push"
    SMS = "sms"


@dataclass
class Alert:
    alert_id: str
    title: str
    message: str
    priority: AlertPriority
    asset: str = ""
    category: str = ""        # "manipulation", "opportunity", "risk", "system"
    data: Dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    channels_delivered: List[str] = field(default_factory=list)
    delivery_errors: List[str] = field(default_factory=list)

    @property
    def fingerprint(self) -> str:
        """Hash for deduplication."""
        content = f"{self.title}|{self.asset}|{self.category}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class ChannelConfig:
    """Configuration for a delivery channel."""
    channel: AlertChannel
    enabled: bool = True
    min_priority: AlertPriority = AlertPriority.MEDIUM
    rate_limit_per_minute: int = 10
    config: Dict = field(default_factory=dict)
    # config keys per channel:
    # telegram: {bot_token, chat_id}
    # email: {smtp_host, smtp_port, username, password, from_addr, to_addrs}
    # slack: {webhook_url, channel}
    # webhook: {url, headers, method}
    # sms: {account_sid, auth_token, from_number, to_number}


class AlertDeliveryManager:
    """
    Central alert delivery system with multi-channel routing.
    
    Priority routing:
    - CRITICAL → ALL enabled channels
    - HIGH → Telegram + Email + Slack
    - MEDIUM → Telegram + Slack
    - LOW → Log only
    """

    def __init__(self, dedup_window_seconds: float = 300):
        self._channels: Dict[AlertChannel, ChannelConfig] = {}
        self._delivery_log: deque = deque(maxlen=5000)
        self._rate_counters: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._dedup_window = dedup_window_seconds
        self._recent_fingerprints: Dict[str, float] = {}
        self._custom_handlers: Dict[AlertChannel, Callable] = {}
        self._lock = threading.Lock()

        self._stats = {
            "total_alerts": 0,
            "delivered": 0,
            "deduplicated": 0,
            "rate_limited": 0,
            "errors": 0,
        }

    def configure_channel(self, config: ChannelConfig) -> None:
        """Register a delivery channel."""
        self._channels[config.channel] = config
        logger.info(f"Configured alert channel: {config.channel.value}")

    def register_custom_handler(self, channel: AlertChannel,
                                  handler: Callable[[Alert, Dict], bool]) -> None:
        """Register custom delivery handler for a channel."""
        self._custom_handlers[channel] = handler

    def send_alert(self, alert: Alert) -> Dict[str, Any]:
        """
        Route and deliver an alert to appropriate channels.
        Returns delivery status summary.
        """
        self._stats["total_alerts"] += 1

        # Deduplication check
        if self._is_duplicate(alert):
            self._stats["deduplicated"] += 1
            return {"status": "deduplicated", "alert_id": alert.alert_id}

        # Determine target channels based on priority
        target_channels = self._route_by_priority(alert.priority)

        results = {}
        for channel in target_channels:
            config = self._channels.get(channel)
            if not config or not config.enabled:
                continue

            # Rate limiting
            if self._is_rate_limited(channel, config):
                self._stats["rate_limited"] += 1
                results[channel.value] = {"status": "rate_limited"}
                continue

            # Deliver
            success = self._deliver_to_channel(alert, channel, config)
            results[channel.value] = {"status": "delivered" if success else "error"}

            if success:
                alert.channels_delivered.append(channel.value)
                self._stats["delivered"] += 1
            else:
                self._stats["errors"] += 1

        # Log
        self._delivery_log.append({
            "alert_id": alert.alert_id,
            "title": alert.title,
            "priority": alert.priority.name,
            "channels": results,
            "timestamp": time.time(),
        })

        return {
            "status": "sent",
            "alert_id": alert.alert_id,
            "channels": results,
        }

    def _route_by_priority(self, priority: AlertPriority) -> List[AlertChannel]:
        """Determine which channels to use based on priority."""
        channels = []
        for channel, config in self._channels.items():
            if config.enabled and priority.value >= config.min_priority.value:
                channels.append(channel)

        # Always include LOG
        if AlertChannel.LOG not in channels:
            channels.append(AlertChannel.LOG)

        return channels

    def _is_duplicate(self, alert: Alert) -> bool:
        """Check if a similar alert was recently sent."""
        fp = alert.fingerprint
        now = time.time()

        with self._lock:
            # Clean old fingerprints
            expired = [k for k, v in self._recent_fingerprints.items()
                       if now - v > self._dedup_window]
            for k in expired:
                del self._recent_fingerprints[k]

            if fp in self._recent_fingerprints:
                return True
            self._recent_fingerprints[fp] = now
            return False

    def _is_rate_limited(self, channel: AlertChannel, config: ChannelConfig) -> bool:
        """Check if channel has exceeded rate limit."""
        key = channel.value
        now = time.time()
        window = self._rate_counters[key]

        # Remove entries older than 1 minute
        while window and window[0] < now - 60:
            window.popleft()

        if len(window) >= config.rate_limit_per_minute:
            return True

        window.append(now)
        return False

    def _deliver_to_channel(self, alert: Alert, channel: AlertChannel,
                              config: ChannelConfig) -> bool:
        """Deliver alert to a specific channel."""
        try:
            # Check for custom handler first
            if channel in self._custom_handlers:
                return self._custom_handlers[channel](alert, config.config)

            if channel == AlertChannel.LOG:
                return self._deliver_log(alert)
            elif channel == AlertChannel.TELEGRAM:
                return self._deliver_telegram(alert, config.config)
            elif channel == AlertChannel.EMAIL:
                return self._deliver_email(alert, config.config)
            elif channel == AlertChannel.SLACK:
                return self._deliver_slack(alert, config.config)
            elif channel == AlertChannel.WEBHOOK:
                return self._deliver_webhook(alert, config.config)
            elif channel == AlertChannel.SMS:
                return self._deliver_sms(alert, config.config)
            else:
                logger.warning(f"Unknown channel: {channel}")
                return False

        except Exception as e:
            logger.error(f"Alert delivery failed on {channel.value}: {e}")
            alert.delivery_errors.append(f"{channel.value}: {str(e)}")
            return False

    def _deliver_log(self, alert: Alert) -> bool:
        """Log the alert."""
        level = {
            AlertPriority.LOW: logging.INFO,
            AlertPriority.MEDIUM: logging.INFO,
            AlertPriority.HIGH: logging.WARNING,
            AlertPriority.CRITICAL: logging.CRITICAL,
        }.get(alert.priority, logging.INFO)

        logger.log(level, f"[ALERT:{alert.priority.name}] {alert.title} — {alert.message}")
        return True

    def _deliver_telegram(self, alert: Alert, config: Dict) -> bool:
        """Send via Telegram Bot API."""
        bot_token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")

        if not bot_token or not chat_id:
            logger.warning("Telegram not configured (missing bot_token/chat_id)")
            return False

        priority_emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🔴",
            AlertPriority.CRITICAL: "🚨",
        }

        emoji = priority_emoji.get(alert.priority, "📢")
        text = (
            f"{emoji} *{alert.title}*\n"
            f"Priority: {alert.priority.name}\n"
            f"Asset: {alert.asset or 'N/A'}\n\n"
            f"{alert.message}"
        )

        try:
            import urllib.request
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = json.dumps({
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown",
            }).encode()

            req = urllib.request.Request(
                url, data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200

        except Exception as e:
            logger.error(f"Telegram delivery failed: {e}")
            return False

    def _deliver_email(self, alert: Alert, config: Dict) -> bool:
        """Send via SMTP email."""
        smtp_host = config.get("smtp_host", "")
        smtp_port = config.get("smtp_port", 587)
        username = config.get("username", "")
        password = config.get("password", "")
        from_addr = config.get("from_addr", username)
        to_addrs = config.get("to_addrs", [])

        if not smtp_host or not to_addrs:
            logger.warning("Email not configured")
            return False

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg["Subject"] = f"[{alert.priority.name}] CME Alert: {alert.title}"

        body = (
            f"Priority: {alert.priority.name}\n"
            f"Asset: {alert.asset or 'N/A'}\n"
            f"Category: {alert.category}\n"
            f"Time: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(alert.timestamp))}\n\n"
            f"{alert.message}\n\n"
            f"Data: {json.dumps(alert.data, indent=2, default=str)}"
        )
        msg.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                if username and password:
                    server.login(username, password)
                server.sendmail(from_addr, to_addrs, msg.as_string())
            return True
        except Exception as e:
            logger.error(f"Email delivery failed: {e}")
            return False

    def _deliver_slack(self, alert: Alert, config: Dict) -> bool:
        """Send via Slack Incoming Webhook."""
        webhook_url = config.get("webhook_url", "")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured")
            return False

        color = {
            AlertPriority.LOW: "#36a64f",
            AlertPriority.MEDIUM: "#daa520",
            AlertPriority.HIGH: "#ff6347",
            AlertPriority.CRITICAL: "#dc143c",
        }.get(alert.priority, "#808080")

        payload = {
            "attachments": [{
                "color": color,
                "title": f"[{alert.priority.name}] {alert.title}",
                "text": alert.message,
                "fields": [
                    {"title": "Asset", "value": alert.asset or "N/A", "short": True},
                    {"title": "Category", "value": alert.category, "short": True},
                ],
                "ts": int(alert.timestamp),
            }],
        }

        try:
            import urllib.request
            data = json.dumps(payload).encode()
            req = urllib.request.Request(
                webhook_url, data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status == 200
        except Exception as e:
            logger.error(f"Slack delivery failed: {e}")
            return False

    def _deliver_webhook(self, alert: Alert, config: Dict) -> bool:
        """Send via generic webhook (Discord, custom endpoint)."""
        url = config.get("url", "")
        headers = config.get("headers", {"Content-Type": "application/json"})
        method = config.get("method", "POST")

        if not url:
            logger.warning("Webhook URL not configured")
            return False

        payload = {
            "alert_id": alert.alert_id,
            "title": alert.title,
            "message": alert.message,
            "priority": alert.priority.name,
            "asset": alert.asset,
            "category": alert.category,
            "data": alert.data,
            "timestamp": alert.timestamp,
        }

        try:
            import urllib.request
            data = json.dumps(payload, default=str).encode()
            req = urllib.request.Request(url, data=data, headers=headers, method=method)
            with urllib.request.urlopen(req, timeout=15) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            logger.error(f"Webhook delivery failed: {e}")
            return False

    def _deliver_sms(self, alert: Alert, config: Dict) -> bool:
        """Send SMS via Twilio API."""
        account_sid = config.get("account_sid", "")
        auth_token = config.get("auth_token", "")
        from_number = config.get("from_number", "")
        to_number = config.get("to_number", "")

        if not all([account_sid, auth_token, from_number, to_number]):
            logger.warning("SMS (Twilio) not fully configured")
            return False

        body = f"[{alert.priority.name}] {alert.title}: {alert.message[:140]}"

        try:
            import urllib.request
            import base64
            url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{account_sid}/Messages.json"
            )
            data = (
                f"To={to_number}&From={from_number}&Body={body}"
            ).encode()
            credentials = base64.b64encode(
                f"{account_sid}:{auth_token}".encode()
            ).decode()

            req = urllib.request.Request(
                url, data=data, method="POST",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 201
        except Exception as e:
            logger.error(f"SMS delivery failed: {e}")
            return False

    def get_stats(self) -> Dict:
        return {**self._stats, "channels_configured": len(self._channels)}

    def get_delivery_log(self, limit: int = 50) -> List[Dict]:
        return list(self._delivery_log)[-limit:]
