"""Webhook delivery failure monitoring and alerting.

Tracks consecutive webhook delivery failures and emits alerts
when thresholds are exceeded.
"""

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from mysql_to_sheets.core.logging_utils import get_module_logger

logger = get_module_logger(__name__)

# Default threshold for consecutive failures before alerting
DEFAULT_ALERT_THRESHOLD = 3


@dataclass
class WebhookHealthStatus:
    """Health status for a single webhook.

    Attributes:
        webhook_id: The webhook's unique identifier.
        url: The webhook URL (masked for security).
        consecutive_failures: Number of consecutive delivery failures.
        last_success_at: Timestamp of last successful delivery.
        last_failure_at: Timestamp of last failed delivery.
        last_error: Most recent error message.
        is_healthy: Whether the webhook is considered healthy.
        is_alerting: Whether an alert has been triggered.
    """

    webhook_id: int
    url: str
    consecutive_failures: int = 0
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    last_error: str | None = None
    is_healthy: bool = True
    is_alerting: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "webhook_id": self.webhook_id,
            "url": self.url,
            "consecutive_failures": self.consecutive_failures,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_failure_at": self.last_failure_at.isoformat() if self.last_failure_at else None,
            "last_error": self.last_error,
            "is_healthy": self.is_healthy,
            "is_alerting": self.is_alerting,
        }


@dataclass
class WebhookAlert:
    """Alert emitted when webhook failure threshold is exceeded.

    Attributes:
        webhook_id: The webhook's unique identifier.
        organization_id: Organization owning the webhook.
        url: The webhook URL (masked).
        consecutive_failures: Number of consecutive failures.
        last_error: Most recent error message.
        triggered_at: When the alert was triggered.
    """

    webhook_id: int
    organization_id: int
    url: str
    consecutive_failures: int
    last_error: str | None
    triggered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for webhook event payload."""
        return {
            "event": "webhook.failing",
            "webhook_id": self.webhook_id,
            "organization_id": self.organization_id,
            "url": self.url,
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error,
            "triggered_at": self.triggered_at.isoformat(),
        }


def _mask_url(url: str) -> str:
    """Mask a webhook URL for logging/display.

    Shows scheme and host but masks path details.

    Args:
        url: The full webhook URL.

    Returns:
        Masked URL string.
    """
    try:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/***"
    except Exception:
        return "***"


class WebhookFailureTracker:
    """Tracks webhook delivery failures and emits alerts.

    Thread-safe tracker that monitors consecutive failures per webhook
    and triggers alerts when thresholds are exceeded.

    Attributes:
        alert_threshold: Number of consecutive failures before alerting.
    """

    def __init__(self, alert_threshold: int | None = None) -> None:
        """Initialize the failure tracker.

        Args:
            alert_threshold: Failures before alerting. Defaults to
                WEBHOOK_ALERT_THRESHOLD env var or 3.
        """
        if alert_threshold is None:
            alert_threshold = int(os.getenv("WEBHOOK_ALERT_THRESHOLD", str(DEFAULT_ALERT_THRESHOLD)))
        self.alert_threshold = alert_threshold
        self._status: dict[int, WebhookHealthStatus] = {}
        self._lock = Lock()
        self._alert_callbacks: list[callable] = []

    def register_alert_callback(self, callback: callable) -> None:
        """Register a callback to be called when alerts are triggered.

        Args:
            callback: Function accepting a WebhookAlert argument.
        """
        with self._lock:
            self._alert_callbacks.append(callback)

    def record_success(
        self,
        webhook_id: int,
        url: str,
        organization_id: int | None = None,
    ) -> None:
        """Record a successful webhook delivery.

        Resets the failure counter and marks the webhook as healthy.

        Args:
            webhook_id: The webhook's unique identifier.
            url: The webhook URL.
            organization_id: Organization owning the webhook.
        """
        with self._lock:
            masked_url = _mask_url(url)
            now = datetime.now(timezone.utc)

            if webhook_id not in self._status:
                self._status[webhook_id] = WebhookHealthStatus(
                    webhook_id=webhook_id,
                    url=masked_url,
                )

            status = self._status[webhook_id]

            # Reset failure state on success
            was_alerting = status.is_alerting
            status.consecutive_failures = 0
            status.last_success_at = now
            status.last_error = None
            status.is_healthy = True
            status.is_alerting = False

            if was_alerting:
                logger.info(
                    "Webhook %d recovered after %d consecutive failures",
                    webhook_id,
                    status.consecutive_failures,
                )

            # Emit metrics
            self._emit_metrics(webhook_id, organization_id, success=True)

    def record_failure(
        self,
        webhook_id: int,
        url: str,
        organization_id: int,
        error: str | None = None,
    ) -> WebhookAlert | None:
        """Record a failed webhook delivery.

        Increments the failure counter and may trigger an alert.

        Args:
            webhook_id: The webhook's unique identifier.
            url: The webhook URL.
            organization_id: Organization owning the webhook.
            error: Error message from the failed delivery.

        Returns:
            WebhookAlert if threshold exceeded, None otherwise.
        """
        with self._lock:
            masked_url = _mask_url(url)
            now = datetime.now(timezone.utc)

            if webhook_id not in self._status:
                self._status[webhook_id] = WebhookHealthStatus(
                    webhook_id=webhook_id,
                    url=masked_url,
                )

            status = self._status[webhook_id]
            status.consecutive_failures += 1
            status.last_failure_at = now
            status.last_error = error
            status.is_healthy = False

            # Check if we should trigger an alert
            alert = None
            if status.consecutive_failures >= self.alert_threshold and not status.is_alerting:
                status.is_alerting = True
                alert = WebhookAlert(
                    webhook_id=webhook_id,
                    organization_id=organization_id,
                    url=masked_url,
                    consecutive_failures=status.consecutive_failures,
                    last_error=error,
                    triggered_at=now,
                )

                logger.warning(
                    "Webhook %d failing: %d consecutive failures (threshold: %d)",
                    webhook_id,
                    status.consecutive_failures,
                    self.alert_threshold,
                )

                # Call registered callbacks
                for callback in self._alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error("Alert callback failed: %s", e)

            # Emit metrics
            self._emit_metrics(
                webhook_id,
                organization_id,
                success=False,
                consecutive_failures=status.consecutive_failures,
            )

            return alert

    def _emit_metrics(
        self,
        webhook_id: int,
        organization_id: int | None,
        success: bool,
        consecutive_failures: int = 0,
    ) -> None:
        """Emit Prometheus metrics for webhook delivery.

        Args:
            webhook_id: The webhook's unique identifier.
            organization_id: Organization owning the webhook.
            success: Whether the delivery succeeded.
            consecutive_failures: Current consecutive failure count.
        """
        try:
            from mysql_to_sheets.core.metrics import (
                record_webhook_delivery,
                update_webhook_health_metrics,
            )

            record_webhook_delivery(
                webhook_id=webhook_id,
                success=success,
                organization_id=organization_id,
            )

            update_webhook_health_metrics(
                webhook_id=webhook_id,
                consecutive_failures=consecutive_failures,
                is_healthy=success or consecutive_failures == 0,
            )
        except ImportError:
            pass  # Metrics module not available
        except Exception as e:
            logger.debug("Failed to emit webhook metrics: %s", e)

    def get_status(self, webhook_id: int) -> WebhookHealthStatus | None:
        """Get the health status for a specific webhook.

        Args:
            webhook_id: The webhook's unique identifier.

        Returns:
            WebhookHealthStatus or None if not tracked.
        """
        with self._lock:
            return self._status.get(webhook_id)

    def get_all_statuses(self) -> list[WebhookHealthStatus]:
        """Get health statuses for all tracked webhooks.

        Returns:
            List of WebhookHealthStatus objects.
        """
        with self._lock:
            return list(self._status.values())

    def get_unhealthy_webhooks(self) -> list[WebhookHealthStatus]:
        """Get all webhooks currently in unhealthy state.

        Returns:
            List of unhealthy WebhookHealthStatus objects.
        """
        with self._lock:
            return [s for s in self._status.values() if not s.is_healthy]

    def get_alerting_webhooks(self) -> list[WebhookHealthStatus]:
        """Get all webhooks currently in alerting state.

        Returns:
            List of alerting WebhookHealthStatus objects.
        """
        with self._lock:
            return [s for s in self._status.values() if s.is_alerting]

    def clear(self, webhook_id: int | None = None) -> None:
        """Clear tracked state.

        Args:
            webhook_id: Specific webhook to clear, or None for all.
        """
        with self._lock:
            if webhook_id is None:
                self._status.clear()
            elif webhook_id in self._status:
                del self._status[webhook_id]

    def get_health_summary(self) -> dict[str, Any]:
        """Get a summary of webhook health for the /health endpoint.

        Returns:
            Dictionary with health summary information.
        """
        with self._lock:
            total = len(self._status)
            healthy = sum(1 for s in self._status.values() if s.is_healthy)
            unhealthy = total - healthy
            alerting = sum(1 for s in self._status.values() if s.is_alerting)

            return {
                "total_tracked": total,
                "healthy": healthy,
                "unhealthy": unhealthy,
                "alerting": alerting,
                "health_percent": (healthy / total * 100) if total > 0 else 100.0,
                "alert_threshold": self.alert_threshold,
            }


# Global tracker instance
_tracker: WebhookFailureTracker | None = None
_tracker_lock = Lock()


def get_webhook_failure_tracker() -> WebhookFailureTracker:
    """Get the global webhook failure tracker instance.

    Returns:
        The singleton WebhookFailureTracker instance.
    """
    global _tracker
    with _tracker_lock:
        if _tracker is None:
            _tracker = WebhookFailureTracker()
        return _tracker


def reset_webhook_failure_tracker() -> None:
    """Reset the global tracker (for testing)."""
    global _tracker
    with _tracker_lock:
        _tracker = None


__all__ = [
    "WebhookHealthStatus",
    "WebhookAlert",
    "WebhookFailureTracker",
    "get_webhook_failure_tracker",
    "reset_webhook_failure_tracker",
    "DEFAULT_ALERT_THRESHOLD",
]
