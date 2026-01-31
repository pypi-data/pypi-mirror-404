"""Slack notification backend using incoming webhooks.

This module provides Slack notifications for sync completion alerts
using Slack's incoming webhook integration.
"""

import json
import urllib.error
import urllib.request
from typing import Any

from mysql_to_sheets.core.exceptions import NotificationError
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.notifications.base import (
    NotificationBackend,
    NotificationConfig,
    NotificationPayload,
)

logger = get_module_logger(__name__)


class SlackNotificationBackend(NotificationBackend):
    """Slack notification backend using incoming webhooks.

    Sends formatted Slack messages with blocks for rich display
    of sync results.
    """

    @property
    def name(self) -> str:
        """Get the backend name."""
        return "slack"

    def is_configured(self, config: NotificationConfig) -> bool:
        """Check if Slack notification is configured."""
        return config.has_slack_config()

    def send(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> bool:
        """Send Slack notification.

        Args:
            payload: Notification data.
            config: Notification configuration.

        Returns:
            True if notification was sent successfully.

        Raises:
            NotificationError: If sending fails.
        """
        if not self.is_configured(config):
            raise NotificationError(
                message="Slack notification not configured",
                backend=self.name,
            )

        slack_message = self._build_message(payload)

        try:
            data = json.dumps(slack_message).encode("utf-8")
            req = urllib.request.Request(
                config.slack_webhook_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    logger.info("Slack notification sent successfully")
                    return True
                else:
                    raise NotificationError(
                        message=f"Slack webhook returned status {response.status}",
                        backend=self.name,
                    )

        except urllib.error.HTTPError as e:
            raise NotificationError(
                message=f"Slack webhook HTTP error: {e.code} {e.reason}",
                backend=self.name,
                original_error=e,
            ) from e
        except urllib.error.URLError as e:
            raise NotificationError(
                message=f"Failed to connect to Slack: {e.reason}",
                backend=self.name,
                original_error=e,
            ) from e
        except OSError as e:
            raise NotificationError(
                message=f"Failed to send Slack notification: {e}",
                backend=self.name,
                original_error=e,
            ) from e

    def _build_message(self, payload: NotificationPayload) -> dict[str, Any]:
        """Build Slack message with blocks.

        Args:
            payload: Notification data.

        Returns:
            Slack message dictionary with blocks.
        """
        status_emoji = payload.status_emoji
        status_text = payload.status_text
        color = "#28a745" if payload.success else "#dc3545"

        # Build attachment fields
        fields = [
            {
                "title": "Rows Synced",
                "value": str(payload.rows_synced),
                "short": True,
            },
            {
                "title": "Duration",
                "value": f"{payload.duration_ms:.1f}ms",
                "short": True,
            },
        ]

        if payload.sheet_id:
            fields.append(
                {
                    "title": "Sheet ID",
                    "value": payload.sheet_id[:40] + ("..." if len(payload.sheet_id) > 40 else ""),
                    "short": True,
                }
            )

        if payload.worksheet:
            fields.append(
                {
                    "title": "Worksheet",
                    "value": payload.worksheet,
                    "short": True,
                }
            )

        fields.append(
            {
                "title": "Source",
                "value": payload.source.capitalize(),
                "short": True,
            }
        )

        fields.append(
            {
                "title": "Timestamp",
                "value": payload.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": True,
            }
        )

        # Build the message
        message: dict[str, Any] = {
            "text": f"{status_emoji} MySQL to Sheets: {status_text}",
            "attachments": [
                {
                    "color": color,
                    "fields": fields,
                }
            ],
        }

        # Add message if present
        if payload.message:
            message["attachments"][0]["text"] = payload.message

        # Add error block if present
        if payload.error:
            message["attachments"].append(
                {
                    "color": "#dc3545",
                    "title": "Error Details",
                    "text": f"```{payload.error}```",
                    "mrkdwn_in": ["text"],
                }
            )

        return message
