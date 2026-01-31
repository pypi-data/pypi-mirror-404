"""Webhook payload structures.

Defines the structure of webhook payloads for different event types.
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class WebhookPayload:
    """Standard webhook payload structure.

    All webhooks follow this structure for consistency.
    """

    event: str  # e.g., "sync.completed"
    timestamp: str  # ISO 8601
    delivery_id: str  # Unique per delivery attempt
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of payload.
        """
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "delivery_id": self.delivery_id,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookPayload":
        """Create WebhookPayload from dictionary.

        Args:
            data: Dictionary with payload data.

        Returns:
            WebhookPayload instance.
        """
        return cls(
            event=data["event"],
            timestamp=data["timestamp"],
            delivery_id=data["delivery_id"],
            data=data["data"],
        )


def generate_delivery_id() -> str:
    """Generate a unique delivery ID.

    Returns:
        Delivery ID in format "dlv_<hex>".
    """
    return f"dlv_{secrets.token_hex(12)}"


def create_sync_payload(
    event: str,
    sync_id: str | None = None,
    config_name: str | None = None,
    rows_synced: int = 0,
    duration_seconds: float = 0.0,
    sheet_id: str | None = None,
    sheet_url: str | None = None,
    triggered_by: str | None = None,
    user_email: str | None = None,
    error_type: str | None = None,
    error_message: str | None = None,
) -> WebhookPayload:
    """Create a webhook payload for sync events.

    Args:
        event: Event type (sync.started, sync.completed, sync.failed).
        sync_id: Unique sync operation ID.
        config_name: Name of the sync configuration.
        rows_synced: Number of rows synced.
        duration_seconds: Sync duration in seconds.
        sheet_id: Target Google Sheet ID.
        sheet_url: URL to the Google Sheet.
        triggered_by: How the sync was triggered (api, cli, web, schedule).
        user_email: Email of the user who triggered the sync.
        error_type: Type of error (for failed syncs).
        error_message: Error message (for failed syncs).

    Returns:
        WebhookPayload for the sync event.
    """
    data: dict[str, Any] = {}

    if sync_id:
        data["sync_id"] = sync_id
    if config_name:
        data["config_name"] = config_name
    if rows_synced > 0:
        data["rows_synced"] = rows_synced
    if duration_seconds > 0:
        data["duration_seconds"] = round(duration_seconds, 3)
    if sheet_id:
        data["sheet_id"] = sheet_id
    if sheet_url:
        data["sheet_url"] = sheet_url
    if triggered_by:
        data["triggered_by"] = triggered_by
    if user_email:
        data["user_email"] = user_email
    if error_type:
        data["error_type"] = error_type
    if error_message:
        data["error_message"] = error_message

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_config_payload(
    event: str,
    config_id: int | None = None,
    config_name: str | None = None,
    user_email: str | None = None,
    changes: dict[str, Any] | None = None,
) -> WebhookPayload:
    """Create a webhook payload for config events.

    Args:
        event: Event type (config.created, config.updated, config.deleted).
        config_id: Configuration ID.
        config_name: Configuration name.
        user_email: Email of the user who made the change.
        changes: Dictionary of changed fields (for updates).

    Returns:
        WebhookPayload for the config event.
    """
    data: dict[str, Any] = {}

    if config_id:
        data["config_id"] = config_id
    if config_name:
        data["config_name"] = config_name
    if user_email:
        data["user_email"] = user_email
    if changes:
        data["changes"] = changes

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_schedule_payload(
    event: str,
    job_id: int | None = None,
    job_name: str | None = None,
    schedule_type: str | None = None,
    next_run: datetime | None = None,
) -> WebhookPayload:
    """Create a webhook payload for schedule events.

    Args:
        event: Event type (schedule.triggered).
        job_id: Scheduled job ID.
        job_name: Scheduled job name.
        schedule_type: Type of schedule (cron, interval).
        next_run: Next scheduled run time.

    Returns:
        WebhookPayload for the schedule event.
    """
    data: dict[str, Any] = {}

    if job_id:
        data["job_id"] = job_id
    if job_name:
        data["job_name"] = job_name
    if schedule_type:
        data["schedule_type"] = schedule_type
    if next_run:
        data["next_run"] = next_run.isoformat()

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_user_payload(
    event: str,
    user_id: int | None = None,
    user_email: str | None = None,
    role: str | None = None,
    changed_by_email: str | None = None,
) -> WebhookPayload:
    """Create a webhook payload for user events.

    Args:
        event: Event type (user.created, user.updated).
        user_id: User ID.
        user_email: User's email.
        role: User's role.
        changed_by_email: Email of the user who made the change.

    Returns:
        WebhookPayload for the user event.
    """
    data: dict[str, Any] = {}

    if user_id:
        data["user_id"] = user_id
    if user_email:
        data["user_email"] = user_email
    if role:
        data["role"] = role
    if changed_by_email:
        data["changed_by_email"] = changed_by_email

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_test_payload() -> WebhookPayload:
    """Create a test webhook payload.

    Used to verify webhook endpoint connectivity.

    Returns:
        WebhookPayload for testing.
    """
    return WebhookPayload(
        event="webhook.test",
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data={
            "message": "This is a test webhook from MySQL to Sheets Sync",
            "test": True,
        },
    )


# ============================================================================
# Billing/Subscription Payloads (Phase 6)
# ============================================================================


def create_subscription_payload(
    event: str,
    organization_id: int | None = None,
    organization_slug: str | None = None,
    old_tier: str | None = None,
    new_tier: str | None = None,
    trial_ends_at: str | None = None,
    trial_days_remaining: int | None = None,
    billing_status: str | None = None,
) -> WebhookPayload:
    """Create a webhook payload for subscription events.

    Args:
        event: Event type (subscription.tier_changed, subscription.trial_started,
               subscription.trial_ending).
        organization_id: Organization ID.
        organization_slug: Organization slug.
        old_tier: Previous subscription tier.
        new_tier: New subscription tier.
        trial_ends_at: ISO timestamp when trial ends.
        trial_days_remaining: Days remaining in trial.
        billing_status: Current billing status.

    Returns:
        WebhookPayload for the subscription event.
    """
    data: dict[str, Any] = {}

    if organization_id:
        data["organization_id"] = organization_id
    if organization_slug:
        data["organization_slug"] = organization_slug
    if old_tier:
        data["old_tier"] = old_tier
    if new_tier:
        data["new_tier"] = new_tier
    if trial_ends_at:
        data["trial_ends_at"] = trial_ends_at
    if trial_days_remaining is not None:
        data["trial_days_remaining"] = trial_days_remaining
    if billing_status:
        data["billing_status"] = billing_status

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_agent_payload(
    event: str,
    agent_id: str | None = None,
    organization_id: int | None = None,
    hostname: str | None = None,
    version: str | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    last_seen_at: datetime | None = None,
    offline_reason: str | None = None,
) -> WebhookPayload:
    """Create a webhook payload for agent events.

    Args:
        event: Event type (agent.online, agent.offline, agent.stale).
        agent_id: Unique agent identifier.
        organization_id: Organization ID the agent belongs to.
        hostname: Hostname where agent is running.
        version: Agent software version.
        previous_status: Status before the change.
        new_status: Status after the change.
        last_seen_at: Last heartbeat timestamp.
        offline_reason: Reason agent went offline (graceful_shutdown, heartbeat_timeout).

    Returns:
        WebhookPayload for the agent event.
    """
    data: dict[str, Any] = {}

    if agent_id:
        data["agent_id"] = agent_id
    if organization_id:
        data["organization_id"] = organization_id
    if hostname:
        data["hostname"] = hostname
    if version:
        data["version"] = version
    if previous_status:
        data["previous_status"] = previous_status
    if new_status:
        data["new_status"] = new_status
    if last_seen_at:
        data["last_seen_at"] = last_seen_at.isoformat()
    if offline_reason:
        data["offline_reason"] = offline_reason

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )


def create_usage_payload(
    event: str,
    organization_id: int | None = None,
    organization_slug: str | None = None,
    threshold_type: str | None = None,
    threshold_percent: int | None = None,
    current_usage: int | None = None,
    limit: int | None = None,
    resource_type: str | None = None,
) -> WebhookPayload:
    """Create a webhook payload for usage events.

    Args:
        event: Event type (usage.threshold_reached).
        organization_id: Organization ID.
        organization_slug: Organization slug.
        threshold_type: Type of threshold (warning, critical, exceeded).
        threshold_percent: Percentage threshold reached (80, 90, 100).
        current_usage: Current usage count.
        limit: Usage limit.
        resource_type: Type of resource (rows_synced, sync_operations, api_calls).

    Returns:
        WebhookPayload for the usage event.
    """
    data: dict[str, Any] = {}

    if organization_id:
        data["organization_id"] = organization_id
    if organization_slug:
        data["organization_slug"] = organization_slug
    if threshold_type:
        data["threshold_type"] = threshold_type
    if threshold_percent is not None:
        data["threshold_percent"] = threshold_percent
    if current_usage is not None:
        data["current_usage"] = current_usage
    if limit is not None:
        data["limit"] = limit
    if resource_type:
        data["resource_type"] = resource_type

    return WebhookPayload(
        event=event,
        timestamp=datetime.now(timezone.utc).isoformat(),
        delivery_id=generate_delivery_id(),
        data=data,
    )
