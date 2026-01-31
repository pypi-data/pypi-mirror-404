"""Webhook delivery service with retry logic.

Handles HTTP delivery of webhook payloads with exponential
backoff retry and delivery logging.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from mysql_to_sheets.core.webhooks.alerts import get_webhook_failure_tracker
from mysql_to_sheets.core.webhooks.payload import WebhookPayload
from mysql_to_sheets.core.webhooks.signature import generate_webhook_headers
from mysql_to_sheets.models.webhooks import (
    WebhookDelivery,
    WebhookRepository,
    WebhookSubscription,
    get_webhook_repository,
)

# Default configuration
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_DISABLE_AFTER_FAILURES = 10


@dataclass
class WebhookDeliveryResult:
    """Result of a webhook delivery attempt.

    Contains the outcome of delivering a webhook payload
    to a subscription endpoint.
    """

    success: bool
    subscription_id: int
    delivery_id: str
    status_code: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    attempts: int = 1
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "subscription_id": self.subscription_id,
            "delivery_id": self.delivery_id,
            "status_code": self.status_code,
            "response_body": self.response_body,
            "error_message": self.error_message,
            "attempts": self.attempts,
            "duration_ms": self.duration_ms,
        }


class WebhookDeliveryService:
    """Service for delivering webhooks with retry logic.

    Handles HTTP POST delivery with HMAC signing, exponential
    backoff retries, and delivery logging.
    """

    def __init__(
        self,
        repository: WebhookRepository,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        disable_after_failures: int = DEFAULT_DISABLE_AFTER_FAILURES,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize delivery service.

        Args:
            repository: WebhookRepository for persistence.
            timeout_seconds: HTTP request timeout.
            max_retries: Maximum retry attempts.
            disable_after_failures: Disable subscription after N failures.
            logger: Optional logger.
        """
        self._repository = repository
        self._timeout = timeout_seconds
        self._max_retries = max_retries
        self._disable_after_failures = disable_after_failures
        self._logger = logger or logging.getLogger(__name__)

    def deliver(
        self,
        subscription: WebhookSubscription,
        payload: WebhookPayload,
    ) -> WebhookDeliveryResult:
        """Deliver a webhook payload to a subscription.

        Attempts delivery with exponential backoff retries.

        Args:
            subscription: Target subscription.
            payload: Payload to deliver.

        Returns:
            WebhookDeliveryResult with delivery outcome.
        """
        # Create delivery record
        delivery = WebhookDelivery(
            subscription_id=subscription.id or 0,
            delivery_id=payload.delivery_id,
            event=payload.event,
            payload=payload.to_dict(),
            status="pending",
        )
        delivery = self._repository.create_delivery(delivery)

        start_time = time.time()
        last_error: str | None = None
        status_code: int | None = None
        response_body: str | None = None

        # Retry with exponential backoff
        retry_delays = [1, 5, 30]  # seconds
        max_attempts = min(subscription.retry_count, self._max_retries) + 1

        for attempt in range(max_attempts):
            if attempt > 0:
                delay = retry_delays[min(attempt - 1, len(retry_delays) - 1)]
                self._logger.debug(
                    f"Retrying webhook {subscription.id} in {delay}s (attempt {attempt + 1})"
                )
                time.sleep(delay)

            try:
                status_code, response_body = self._send_request(
                    url=subscription.url,
                    payload=payload,
                    secret=subscription.secret,
                    custom_headers=subscription.headers,
                )

                if 200 <= status_code < 300:
                    # Success
                    duration_ms = (time.time() - start_time) * 1000

                    delivery.status = "success"
                    delivery.response_code = status_code
                    delivery.response_body = response_body[:1024] if response_body else None
                    delivery.attempt_count = attempt + 1
                    delivery.completed_at = datetime.now(timezone.utc)
                    self._repository.update_delivery(delivery)
                    if subscription.id is not None:
                        self._repository.update_subscription_triggered(subscription.id, True)

                    # Track successful delivery for health monitoring
                    tracker = get_webhook_failure_tracker()
                    tracker.record_success(
                        webhook_id=subscription.id or 0,
                        url=subscription.url,
                        organization_id=subscription.organization_id,
                    )

                    self._logger.info(f"Webhook delivered: {subscription.name} ({payload.event})")

                    return WebhookDeliveryResult(
                        success=True,
                        subscription_id=subscription.id or 0,
                        delivery_id=payload.delivery_id,
                        status_code=status_code,
                        response_body=response_body[:1024] if response_body else None,
                        attempts=attempt + 1,
                        duration_ms=duration_ms,
                    )

                # Non-2xx response
                last_error = f"HTTP {status_code}: {response_body[:200] if response_body else 'No response body'}"

            except HTTPError as e:
                status_code = e.code
                try:
                    response_body = e.read().decode("utf-8", errors="replace")
                except (OSError, RuntimeError):
                    response_body = None
                last_error = f"HTTP {e.code}: {e.reason}"

            except URLError as e:
                last_error = f"Connection error: {e.reason}"

            except OSError as e:
                last_error = f"Unexpected error: {str(e)}"

            self._logger.warning(f"Webhook delivery failed (attempt {attempt + 1}): {last_error}")

        # All retries exhausted
        duration_ms = (time.time() - start_time) * 1000

        delivery.status = "failed"
        delivery.response_code = status_code
        delivery.response_body = response_body[:1024] if response_body else None
        delivery.attempt_count = max_attempts
        delivery.completed_at = datetime.now(timezone.utc)
        delivery.error_message = last_error
        self._repository.update_delivery(delivery)
        if subscription.id is not None:
            self._repository.update_subscription_triggered(subscription.id, False)

        # Track failed delivery for health monitoring and alerting
        tracker = get_webhook_failure_tracker()
        alert = tracker.record_failure(
            webhook_id=subscription.id or 0,
            url=subscription.url,
            organization_id=subscription.organization_id,
            error=last_error,
        )
        if alert:
            self._logger.warning(
                f"Webhook alert triggered: {subscription.name} has {alert.consecutive_failures} "
                "consecutive failures"
            )

        self._logger.error(
            f"Webhook delivery failed after {max_attempts} attempts: {subscription.name}"
        )

        return WebhookDeliveryResult(
            success=False,
            subscription_id=subscription.id or 0,
            delivery_id=payload.delivery_id,
            status_code=status_code,
            response_body=response_body[:1024] if response_body else None,
            error_message=last_error,
            attempts=max_attempts,
            duration_ms=duration_ms,
        )

    def _send_request(
        self,
        url: str,
        payload: WebhookPayload,
        secret: str,
        custom_headers: dict[str, str] | None = None,
    ) -> tuple[int, str]:
        """Send HTTP POST request.

        Args:
            url: Target URL.
            payload: Payload to send.
            secret: HMAC signing secret.
            custom_headers: Additional headers.

        Returns:
            Tuple of (status_code, response_body).

        Raises:
            HTTPError: On HTTP error responses.
            URLError: On connection errors.
        """
        payload_dict = payload.to_dict()
        body = json.dumps(payload_dict).encode("utf-8")

        headers = generate_webhook_headers(
            payload=payload_dict,
            secret=secret,
            event=payload.event,
            delivery_id=payload.delivery_id,
            timestamp=payload.timestamp,
            custom_headers=custom_headers,
        )

        request = Request(url, data=body, headers=headers, method="POST")
        response = urlopen(request, timeout=self._timeout)

        status_code = response.status
        response_body = response.read().decode("utf-8", errors="replace")

        return status_code, response_body

    def deliver_to_all(
        self,
        event: str,
        organization_id: int,
        payload: WebhookPayload,
    ) -> list[WebhookDeliveryResult]:
        """Deliver webhook to all subscriptions for an event.

        Args:
            event: Event type to match.
            organization_id: Organization to filter by.
            payload: Payload to deliver.

        Returns:
            List of delivery results.
        """
        subscriptions = self._repository.get_subscriptions_for_event(event, organization_id)

        results = []
        for sub in subscriptions:
            # Skip subscriptions with too many failures
            if sub.failure_count >= self._disable_after_failures:
                self._logger.warning(
                    f"Skipping webhook {sub.name}: too many failures ({sub.failure_count})"
                )
                continue

            result = self.deliver(sub, payload)
            results.append(result)

        return results

    def test_subscription(
        self,
        subscription: WebhookSubscription,
    ) -> WebhookDeliveryResult:
        """Send a test webhook to verify connectivity.

        Args:
            subscription: Subscription to test.

        Returns:
            WebhookDeliveryResult with test outcome.
        """
        from mysql_to_sheets.core.webhooks.payload import create_test_payload

        payload = create_test_payload()
        return self.deliver(subscription, payload)


# Singleton instance
_delivery_service: WebhookDeliveryService | None = None


def get_webhook_delivery_service(
    db_path: str | None = None,
    logger: logging.Logger | None = None,
) -> WebhookDeliveryService:
    """Get or create webhook delivery service singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.
        logger: Optional logger.

    Returns:
        WebhookDeliveryService instance.
    """
    global _delivery_service
    if _delivery_service is None:
        if db_path is None:
            db_path = os.getenv("TENANT_DB_PATH", "./data/tenant.db")
        repository = get_webhook_repository(db_path)

        timeout = int(os.getenv("WEBHOOK_TIMEOUT_SECONDS", DEFAULT_TIMEOUT_SECONDS))
        max_retries = int(os.getenv("WEBHOOK_MAX_RETRIES", DEFAULT_MAX_RETRIES))
        disable_after = int(
            os.getenv("WEBHOOK_DISABLE_AFTER_FAILURES", DEFAULT_DISABLE_AFTER_FAILURES)
        )

        _delivery_service = WebhookDeliveryService(
            repository=repository,
            timeout_seconds=timeout,
            max_retries=max_retries,
            disable_after_failures=disable_after,
            logger=logger,
        )
    return _delivery_service


def reset_webhook_delivery_service() -> None:
    """Reset webhook delivery service singleton. For testing."""
    global _delivery_service
    _delivery_service = None
