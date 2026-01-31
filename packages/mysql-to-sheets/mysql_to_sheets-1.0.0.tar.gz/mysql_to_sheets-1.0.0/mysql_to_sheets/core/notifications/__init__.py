"""Notification backends for sync completion alerts.

This module provides pluggable notification backends for alerting users
when sync operations complete or fail. Supported backends:
- Email (SMTP)
- Slack (Webhook)
- Generic Webhook (HTTP POST)
"""

from mysql_to_sheets.core.notifications.base import (
    NotificationBackend,
    NotificationConfig,
    NotificationPayload,
)
from mysql_to_sheets.core.notifications.email import EmailNotificationBackend
from mysql_to_sheets.core.notifications.manager import (
    NotificationManager,
    get_notification_manager,
    reset_notification_manager,
)
from mysql_to_sheets.core.notifications.slack import SlackNotificationBackend
from mysql_to_sheets.core.notifications.webhook import WebhookNotificationBackend

__all__ = [
    # Base classes
    "NotificationBackend",
    "NotificationConfig",
    "NotificationPayload",
    # Manager
    "NotificationManager",
    "get_notification_manager",
    "reset_notification_manager",
    # Backends
    "EmailNotificationBackend",
    "SlackNotificationBackend",
    "WebhookNotificationBackend",
]
