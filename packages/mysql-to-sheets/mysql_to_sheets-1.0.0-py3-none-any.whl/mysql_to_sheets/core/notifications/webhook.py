"""Generic webhook notification backend.

This module provides generic HTTP POST webhook notifications for
sync completion alerts. The webhook receives a JSON payload with
all sync details.
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


class WebhookNotificationBackend(NotificationBackend):
    """Generic webhook notification backend.

    Sends HTTP POST requests with JSON payloads containing sync
    results to configured webhook URLs.
    """

    @property
    def name(self) -> str:
        """Get the backend name."""
        return "webhook"

    def is_configured(self, config: NotificationConfig) -> bool:
        """Check if webhook notification is configured."""
        return config.has_webhook_config()

    def send(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> bool:
        """Send webhook notification.

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
                message="Webhook notification not configured",
                backend=self.name,
            )

        webhook_payload = self._build_payload(payload)

        try:
            data = json.dumps(webhook_payload).encode("utf-8")
            req = urllib.request.Request(
                config.notification_webhook_url,
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "mysql-to-sheets/1.0",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=30) as response:
                status_code = response.status
                if 200 <= status_code < 300:
                    logger.info(f"Webhook notification sent successfully (status {status_code})")
                    return True
                else:
                    raise NotificationError(
                        message=f"Webhook returned status {status_code}",
                        backend=self.name,
                    )

        except urllib.error.HTTPError as e:
            # Read error response body if available
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")[:500]
            except (OSError, UnicodeDecodeError):
                pass

            raise NotificationError(
                message=f"Webhook HTTP error: {e.code} {e.reason}. Response: {error_body}",
                backend=self.name,
                original_error=e,
            ) from e
        except urllib.error.URLError as e:
            raise NotificationError(
                message=f"Failed to connect to webhook: {e.reason}",
                backend=self.name,
                original_error=e,
            ) from e
        except OSError as e:
            raise NotificationError(
                message=f"Failed to send webhook notification: {e}",
                backend=self.name,
                original_error=e,
            ) from e

    def _build_payload(self, payload: NotificationPayload) -> dict[str, Any]:
        """Build webhook JSON payload.

        Args:
            payload: Notification data.

        Returns:
            Dictionary containing all sync data.
        """
        return {
            "event": "sync_complete",
            "success": payload.success,
            "status": payload.status_text,
            "data": {
                "rows_synced": payload.rows_synced,
                "sheet_id": payload.sheet_id,
                "worksheet": payload.worksheet,
                "duration_ms": payload.duration_ms,
                "dry_run": payload.dry_run,
                "headers": payload.headers,
            },
            "message": payload.message,
            "error": payload.error,
            "source": payload.source,
            "timestamp": payload.timestamp.isoformat(),
        }
