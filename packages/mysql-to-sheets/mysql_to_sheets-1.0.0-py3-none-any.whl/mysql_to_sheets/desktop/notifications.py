"""Native desktop notifications for MySQL to Google Sheets sync.

This module provides cross-platform desktop notifications using plyer.
Notifications are shown for:
- Sync completed successfully
- Sync failed with error
- Schedule triggered
- Data freshness warnings
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Callable

logger = logging.getLogger(__name__)


class NotificationType(Enum):
    """Types of desktop notifications."""

    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class NotificationConfig:
    """Configuration for the notification system."""

    enabled: bool = True
    app_name: str = "MySQL to Sheets"
    timeout: int = 10  # Seconds to show notification


class DesktopNotifier:
    """Cross-platform desktop notification manager.

    Uses plyer for notifications, with graceful fallback when not available.
    """

    def __init__(self, config: NotificationConfig | None = None) -> None:
        """Initialize the notifier.

        Args:
            config: Optional notification configuration.
        """
        self.config = config or NotificationConfig()
        self._plyer_available = False
        self._notification_func: Callable[..., None] | None = None

        self._init_plyer()

    def _init_plyer(self) -> None:
        """Initialize plyer notification backend."""
        try:
            from plyer import notification

            self._notification_func = notification.notify
            self._plyer_available = True
            logger.debug("Plyer notifications initialized successfully")
        except ImportError:
            logger.warning(
                "Plyer not installed. Desktop notifications will be disabled. "
                "Install with: pip install plyer"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize plyer notifications: {e}")

    @property
    def is_available(self) -> bool:
        """Check if notifications are available."""
        return self._plyer_available and self.config.enabled

    def notify(
        self,
        title: str,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        timeout: int | None = None,
    ) -> bool:
        """Show a desktop notification.

        Args:
            title: Notification title.
            message: Notification body text.
            notification_type: Type of notification (affects icon on some platforms).
            timeout: Override default timeout in seconds.

        Returns:
            True if notification was shown, False otherwise.
        """
        if not self.is_available:
            logger.debug(f"Notification skipped (unavailable): {title}")
            return False

        if not self._notification_func:
            return False

        try:
            self._notification_func(
                title=title,
                message=message,
                app_name=self.config.app_name,
                timeout=timeout or self.config.timeout,
            )
            logger.debug(f"Notification shown: {title}")
            return True
        except Exception as e:
            logger.warning(f"Failed to show notification: {e}")
            return False

    def sync_success(self, rows_synced: int, duration_seconds: float) -> bool:
        """Show notification for successful sync.

        Args:
            rows_synced: Number of rows synced.
            duration_seconds: Time taken in seconds.

        Returns:
            True if notification was shown.
        """
        return self.notify(
            title="Sync Complete",
            message=f"Successfully synced {rows_synced:,} rows in {duration_seconds:.1f}s",
            notification_type=NotificationType.SUCCESS,
        )

    def sync_failed(self, error_message: str, error_code: str | None = None) -> bool:
        """Show notification for failed sync with remediation hint.

        Args:
            error_message: Brief error description.
            error_code: Optional error code (e.g., DB_201).

        Returns:
            True if notification was shown.
        """
        title = "Sync Failed"
        if error_code:
            title = f"Sync Failed ({error_code})"

        # Add remediation hint based on error code
        hint = self._get_error_hint(error_code)
        if hint:
            message = f"{error_message[:120]}\n\n💡 {hint}"
        else:
            message = error_message[:200]

        return self.notify(
            title=title,
            message=message,
            notification_type=NotificationType.ERROR,
        )

    def _get_error_hint(self, error_code: str | None) -> str | None:
        """Get a brief remediation hint for an error code.

        Args:
            error_code: Error code (e.g., DB_201).

        Returns:
            Brief remediation hint or None.
        """
        if not error_code:
            return None

        hints = {
            # Database errors
            "DB_201": "Check that the database server is running",
            "DB_202": "Verify your database credentials in .env",
            "DB_203": "Check your SQL query for syntax errors",
            "DB_204": "Database connection timed out - check network",
            "DB_205": "Database not found - verify DB_NAME",
            # Sheets errors
            "SHEETS_301": "Check your service account credentials",
            "SHEETS_302": "Verify the Google Sheet ID",
            "SHEETS_303": "Share the sheet with your service account email",
            "SHEETS_304": "Rate limited - wait and retry",
            "SHEETS_305": "Worksheet tab not found - check tab name",
            # Config errors
            "CONFIG_101": "Check .env file for missing fields",
            "CONFIG_103": "Create .env file from .env.example",
            "CONFIG_105": "Remove dangerous SQL statements",
        }

        return hints.get(error_code)

    def schedule_triggered(self, schedule_name: str) -> bool:
        """Show notification when a scheduled sync starts.

        Args:
            schedule_name: Name of the schedule.

        Returns:
            True if notification was shown.
        """
        return self.notify(
            title="Scheduled Sync Started",
            message=f"Running scheduled sync: {schedule_name}",
            notification_type=NotificationType.INFO,
        )

    def freshness_warning(
        self, config_name: str, minutes_stale: int, sla_minutes: int
    ) -> bool:
        """Show notification for data freshness warning.

        Args:
            config_name: Name of the sync configuration.
            minutes_stale: How many minutes since last sync.
            sla_minutes: The SLA threshold in minutes.

        Returns:
            True if notification was shown.
        """
        return self.notify(
            title="Data Freshness Warning",
            message=(
                f"'{config_name}' hasn't synced in {minutes_stale} minutes "
                f"(SLA: {sla_minutes} min)"
            ),
            notification_type=NotificationType.WARNING,
        )

    def freshness_critical(self, config_name: str, minutes_stale: int) -> bool:
        """Show notification for critical data staleness.

        Args:
            config_name: Name of the sync configuration.
            minutes_stale: How many minutes since last sync.

        Returns:
            True if notification was shown.
        """
        return self.notify(
            title="Data Stale - Action Required",
            message=f"'{config_name}' hasn't synced in {minutes_stale} minutes!",
            notification_type=NotificationType.ERROR,
        )

    def offline_detected(self, queued_count: int = 0) -> bool:
        """Show notification when app goes offline.

        Args:
            queued_count: Number of syncs in queue.

        Returns:
            True if notification was shown.
        """
        if queued_count > 0:
            message = (
                f"Network connectivity lost. {queued_count} sync(s) queued. "
                "Will resume when connection is restored."
            )
        else:
            message = (
                "Network connectivity lost. "
                "Syncs will be queued and executed when connection is restored."
            )

        return self.notify(
            title="Offline Mode",
            message=message,
            notification_type=NotificationType.WARNING,
        )

    def online_restored(self, queued_count: int = 0) -> bool:
        """Show notification when connectivity is restored.

        Args:
            queued_count: Number of queued syncs to process.

        Returns:
            True if notification was shown.
        """
        if queued_count > 0:
            message = f"Connection restored. Processing {queued_count} queued sync(s)..."
        else:
            message = "Connection restored. Ready to sync."

        return self.notify(
            title="Back Online",
            message=message,
            notification_type=NotificationType.SUCCESS,
        )

    def sync_queued(self, config_name: str, queue_position: int) -> bool:
        """Show notification when a sync is queued offline.

        Args:
            config_name: Name of the sync configuration.
            queue_position: Position in the queue.

        Returns:
            True if notification was shown.
        """
        return self.notify(
            title="Sync Queued",
            message=f"'{config_name}' queued (position {queue_position}). Will sync when online.",
            notification_type=NotificationType.INFO,
        )


# Global notifier instance (lazy initialization)
_notifier: DesktopNotifier | None = None


def get_notifier(config: NotificationConfig | None = None) -> DesktopNotifier:
    """Get the global notifier instance.

    Args:
        config: Optional configuration (used only on first call).

    Returns:
        The global DesktopNotifier instance.
    """
    global _notifier
    if _notifier is None:
        _notifier = DesktopNotifier(config)
    return _notifier


def notify_sync_success(rows_synced: int, duration_seconds: float) -> bool:
    """Convenience function for sync success notification."""
    return get_notifier().sync_success(rows_synced, duration_seconds)


def notify_sync_failed(error_message: str, error_code: str | None = None) -> bool:
    """Convenience function for sync failure notification."""
    return get_notifier().sync_failed(error_message, error_code)
