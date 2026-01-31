"""Notification manager for dispatching to multiple backends.

This module provides a singleton manager that dispatches notifications
to all configured backends. It handles graceful degradation when
individual backends fail.
"""

from typing import Any

from mysql_to_sheets.core.exceptions import NotificationError
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.notifications.base import (
    NotificationBackend,
    NotificationConfig,
    NotificationPayload,
)

logger = get_module_logger(__name__)


class NotificationManager:
    """Manager for dispatching notifications to multiple backends.

    This class manages a collection of notification backends and
    dispatches notifications to all configured backends. It handles
    failures gracefully by logging errors and continuing to other
    backends.

    Attributes:
        backends: List of registered notification backends.
    """

    def __init__(self) -> None:
        """Initialize the notification manager."""
        self._backends: list[NotificationBackend] = []

    def register_backend(self, backend: NotificationBackend) -> None:
        """Register a notification backend.

        Args:
            backend: Backend to register.
        """
        self._backends.append(backend)
        logger.debug(f"Registered notification backend: {backend.name}")

    def register_default_backends(self) -> None:
        """Register all default notification backends.

        This method registers email, Slack, and webhook backends.
        Call this after creating the manager to enable all backends.
        """
        from mysql_to_sheets.core.notifications.email import EmailNotificationBackend
        from mysql_to_sheets.core.notifications.slack import SlackNotificationBackend
        from mysql_to_sheets.core.notifications.webhook import WebhookNotificationBackend

        self.register_backend(EmailNotificationBackend())
        self.register_backend(SlackNotificationBackend())
        self.register_backend(WebhookNotificationBackend())

    @property
    def backends(self) -> list[NotificationBackend]:
        """Get all registered backends.

        Returns:
            List of registered backends.
        """
        return self._backends.copy()

    def get_configured_backends(
        self,
        config: NotificationConfig,
    ) -> list[NotificationBackend]:
        """Get backends that are properly configured.

        Args:
            config: Notification configuration.

        Returns:
            List of configured backends.
        """
        return [b for b in self._backends if b.is_configured(config)]

    def send_notification(
        self,
        payload: NotificationPayload,
        config: NotificationConfig,
    ) -> dict[str, Any]:
        """Send notification to all configured backends.

        This method attempts to send notifications to all backends
        that should receive this notification. Failures in individual
        backends are logged but do not prevent other backends from
        receiving the notification.

        Args:
            payload: Notification data.
            config: Notification configuration.

        Returns:
            Dictionary with results for each backend:
            {
                "sent": ["email", "slack"],
                "skipped": ["webhook"],
                "failed": [],
                "errors": {}
            }
        """
        results: dict[str, Any] = {
            "sent": [],
            "skipped": [],
            "failed": [],
            "errors": {},
        }

        for backend in self._backends:
            backend_name = backend.name

            if not backend.should_notify(payload, config):
                results["skipped"].append(backend_name)
                logger.debug(
                    f"Skipped notification for {backend_name} (not configured or not applicable)"
                )
                continue

            try:
                success = backend.send(payload, config)
                if success:
                    results["sent"].append(backend_name)
                    logger.info(f"Sent notification via {backend_name}")
                else:
                    results["failed"].append(backend_name)
                    logger.warning(f"Failed to send notification via {backend_name}")
            except NotificationError as e:
                results["failed"].append(backend_name)
                results["errors"][backend_name] = str(e)
                logger.error(f"Notification error for {backend_name}: {e}")
            except (OSError, RuntimeError, ImportError, ValueError) as e:
                results["failed"].append(backend_name)
                results["errors"][backend_name] = str(e)
                logger.exception(f"Unexpected error sending notification via {backend_name}: {e}")

        return results

    def test_backend(
        self,
        backend_name: str,
        config: NotificationConfig,
    ) -> bool:
        """Test a specific backend by sending a test notification.

        Args:
            backend_name: Name of the backend to test.
            config: Notification configuration.

        Returns:
            True if test notification was sent successfully.

        Raises:
            ValueError: If backend name is not found.
            NotificationError: If sending fails.
        """
        backend = None
        for b in self._backends:
            if b.name.lower() == backend_name.lower():
                backend = b
                break

        if backend is None:
            raise ValueError(f"Backend '{backend_name}' not found")

        if not backend.is_configured(config):
            raise NotificationError(
                message=f"Backend '{backend_name}' is not configured",
                backend=backend_name,
            )

        # Create a test payload
        test_payload = NotificationPayload(
            success=True,
            rows_synced=0,
            message="This is a test notification from MySQL to Sheets Sync",
            source="test",
        )

        return backend.send(test_payload, config)

    def get_status(
        self,
        config: NotificationConfig,
    ) -> dict[str, dict[str, Any]]:
        """Get status of all backends.

        Args:
            config: Notification configuration.

        Returns:
            Dictionary mapping backend name to status info.
        """
        status = {}
        for backend in self._backends:
            status[backend.name] = {
                "configured": backend.is_configured(config),
                "notify_on_success": config.notify_on_success,
                "notify_on_failure": config.notify_on_failure,
            }
        return status


# Singleton instance
_manager: NotificationManager | None = None


def get_notification_manager() -> NotificationManager:
    """Get the notification manager singleton.

    Returns:
        NotificationManager instance with default backends registered.
    """
    global _manager
    if _manager is None:
        _manager = NotificationManager()
        _manager.register_default_backends()
    return _manager


def reset_notification_manager() -> None:
    """Reset the notification manager singleton.

    Useful for testing.
    """
    global _manager
    _manager = None
