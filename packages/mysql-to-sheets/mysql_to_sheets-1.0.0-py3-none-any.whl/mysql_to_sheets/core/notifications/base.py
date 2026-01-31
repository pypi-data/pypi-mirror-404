"""Base classes for notification backends.

This module defines the abstract base class and data structures for
notification backends. All concrete backends (email, Slack, webhook)
must implement the NotificationBackend interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class NotificationPayload:
    """Data payload for notifications.

    Attributes:
        success: Whether the sync succeeded.
        rows_synced: Number of rows synced.
        sheet_id: Google Sheet ID.
        worksheet: Worksheet name.
        message: Status message.
        error: Error message if failed.
        duration_ms: Sync duration in milliseconds.
        timestamp: When the sync occurred.
        dry_run: Whether this was a dry run.
        headers: Column headers from the sync.
        source: Source of the sync (cli, api, web, scheduler, schema_change).
        schema_change: Schema change information if detected.
    """

    success: bool
    rows_synced: int = 0
    sheet_id: str = ""
    worksheet: str = ""
    message: str = ""
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    dry_run: bool = False
    headers: list[str] = field(default_factory=list)
    source: str = "unknown"
    schema_change: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert payload to dictionary.

        Returns:
            Dictionary representation of the payload.
        """
        result = {
            "success": self.success,
            "rows_synced": self.rows_synced,
            "sheet_id": self.sheet_id,
            "worksheet": self.worksheet,
            "message": self.message,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "dry_run": self.dry_run,
            "headers": self.headers,
            "source": self.source,
        }
        if self.schema_change is not None:
            result["schema_change"] = self.schema_change
        return result

    @property
    def status_emoji(self) -> str:
        """Get a status emoji for display.

        Returns:
            Emoji representing the sync status.
        """
        if self.dry_run:
            return "🔍"  # Dry run
        elif self.success:
            return "✅"  # Success
        else:
            return "❌"  # Failure

    @property
    def status_text(self) -> str:
        """Get status text for display.

        Returns:
            Human-readable status text.
        """
        if self.dry_run:
            return "Dry Run Complete"
        elif self.success:
            return "Sync Successful"
        else:
            return "Sync Failed"


@dataclass
class NotificationConfig:
    """Configuration for notification backends.

    This is a subset of the main Config that contains only
    notification-related settings.

    Attributes:
        notify_on_success: Whether to send notifications on successful syncs.
        notify_on_failure: Whether to send notifications on failed syncs.
        smtp_host: SMTP server hostname.
        smtp_port: SMTP server port.
        smtp_user: SMTP username.
        smtp_password: SMTP password.
        smtp_from: Sender email address.
        smtp_to: Comma-separated recipient email addresses.
        smtp_use_tls: Whether to use TLS.
        slack_webhook_url: Slack incoming webhook URL.
        notification_webhook_url: Generic webhook URL.
    """

    notify_on_success: bool = False
    notify_on_failure: bool = True

    # Email (SMTP) settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_to: str = ""  # Comma-separated
    smtp_use_tls: bool = True

    # Slack settings
    slack_webhook_url: str = ""

    # Generic webhook settings
    notification_webhook_url: str = ""

    def has_email_config(self) -> bool:
        """Check if email notification is configured.

        Returns:
            True if all required email settings are present.
        """
        return bool(
            self.smtp_host
            and self.smtp_user
            and self.smtp_password
            and self.smtp_from
            and self.smtp_to
        )

    def has_slack_config(self) -> bool:
        """Check if Slack notification is configured.

        Returns:
            True if Slack webhook URL is present.
        """
        return bool(self.slack_webhook_url)

    def has_webhook_config(self) -> bool:
        """Check if generic webhook is configured.

        Returns:
            True if webhook URL is present.
        """
        return bool(self.notification_webhook_url)

    def get_email_recipients(self) -> list[str]:
        """Get list of email recipients.

        Returns:
            List of email addresses.
        """
        if not self.smtp_to:
            return []
        return [email.strip() for email in self.smtp_to.split(",") if email.strip()]


class NotificationBackend(ABC):
    """Abstract base class for notification backends.

    All concrete backends must implement the send() method to deliver
    notifications to their respective channels.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the backend name.

        Returns:
            Human-readable name for this backend.
        """
        pass

    @abstractmethod
    def is_configured(self, config: NotificationConfig) -> bool:
        """Check if this backend is properly configured.

        Args:
            config: Notification configuration.

        Returns:
            True if all required settings are present.
        """
        pass

    @abstractmethod
    def send(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> bool:
        """Send a notification.

        Args:
            payload: Notification data.
            config: Notification configuration.

        Returns:
            True if notification was sent successfully.

        Raises:
            NotificationError: If sending fails.
        """
        pass

    def should_notify(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> bool:
        """Check if a notification should be sent for this payload.

        Args:
            payload: Notification data.
            config: Notification configuration.

        Returns:
            True if notification should be sent.
        """
        if not self.is_configured(config):
            return False

        # Don't notify for dry runs
        if payload.dry_run:
            return False

        if payload.success and config.notify_on_success:
            return True
        if not payload.success and config.notify_on_failure:
            return True

        return False
