"""Freshness alerting for stale sync configurations.

Provides functions to check freshness and send alerts via the
existing notification system (email, Slack, webhooks).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from mysql_to_sheets.core.freshness import (
    FRESHNESS_STALE,
    FRESHNESS_WARNING,
    FreshnessStatus,
    check_all_freshness,
)
from mysql_to_sheets.models.sync_configs import (
    get_sync_config_repository,
)

logger = logging.getLogger(__name__)


def check_and_alert(
    organization_id: int,
    db_path: str,
    send_notifications: bool = True,
) -> list[dict[str, Any]]:
    """Check freshness for all configs and send alerts for stale ones.

    Only sends alerts if enough time has passed since the last alert
    (based on SLA period) to prevent alert spam.

    Args:
        organization_id: Organization ID.
        db_path: Path to database.
        send_notifications: Whether to actually send notifications.

    Returns:
        List of alert dictionaries that were triggered.
    """
    alerts = []
    repo = get_sync_config_repository(db_path)

    # Get all freshness statuses
    statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)

    for status in statuses:
        if status.status not in (FRESHNESS_STALE, FRESHNESS_WARNING):
            continue

        # Check if we should alert (avoid spam)
        if not _should_alert(status, repo, organization_id):
            continue

        # Create alert
        alert = _create_alert(status)
        alerts.append(alert)

        # Send notification
        if send_notifications:
            try:
                _send_alert(alert, organization_id)
                # Update last_alert_at to prevent spam
                repo.update_last_alert(status.config_id, organization_id)
            except (OSError, RuntimeError, ImportError) as e:
                logger.error(f"Failed to send alert for config {status.config_id}: {e}")

    if alerts:
        logger.info(f"Generated {len(alerts)} freshness alerts for org {organization_id}")

    return alerts


def get_stale_syncs(
    organization_id: int,
    db_path: str,
) -> list[dict[str, Any]]:
    """Get all stale sync configurations for an organization.

    Args:
        organization_id: Organization ID.
        db_path: Path to database.

    Returns:
        List of stale sync info dictionaries.
    """
    statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)

    stale = []
    for status in statuses:
        if status.status == FRESHNESS_STALE:
            stale.append(
                {
                    "config_id": status.config_id,
                    "config_name": status.config_name,
                    "last_success_at": status.last_success_at.isoformat()
                    if status.last_success_at
                    else None,
                    "sla_minutes": status.sla_minutes,
                    "minutes_overdue": (
                        status.minutes_since_sync - status.sla_minutes
                        if status.minutes_since_sync
                        else None
                    ),
                }
            )

    return stale


def check_and_alert_all(
    db_path: str,
    send_notifications: bool = True,
) -> dict[int, list[dict[str, Any]]]:
    """Check freshness and alert for all organizations.

    Args:
        db_path: Path to database.
        send_notifications: Whether to actually send notifications.

    Returns:
        Dictionary mapping organization_id to list of alerts.
    """
    from mysql_to_sheets.models.organizations import OrganizationRepository

    try:
        org_repo = OrganizationRepository(db_path)
        orgs = org_repo.get_all()
    except (ImportError, OSError, RuntimeError) as e:
        logger.error(f"Failed to get organizations: {e}")
        return {}

    all_alerts = {}
    for org in orgs:
        if not org.is_active:
            continue

        alerts = check_and_alert(
            organization_id=org.id,  # type: ignore[arg-type]
            db_path=db_path,
            send_notifications=send_notifications,
        )

        if alerts and org.id is not None:
            all_alerts[org.id] = alerts

    return all_alerts


def _should_alert(
    status: FreshnessStatus,
    repo: Any,
    organization_id: int,
) -> bool:
    """Check if we should send an alert for this status.

    Prevents alert spam by only alerting once per SLA period.

    Args:
        status: Freshness status.
        repo: SyncConfigRepository instance.
        organization_id: Organization ID.

    Returns:
        True if we should alert, False otherwise.
    """
    # Get the full config to check last_alert_at
    config = repo.get_by_id(status.config_id, organization_id)
    if not config:
        return False

    # If never alerted, should alert
    if not config.last_alert_at:
        return True

    # Only alert again if SLA period has passed since last alert
    now = datetime.now(timezone.utc)
    alert_cooldown = timedelta(minutes=config.sla_minutes)
    # Ensure last_alert_at is timezone-aware (assume UTC if naive)
    last_alert = config.last_alert_at
    if last_alert.tzinfo is None:
        last_alert = last_alert.replace(tzinfo=timezone.utc)
    return now - last_alert >= alert_cooldown  # type: ignore[no-any-return]


def _create_alert(status: FreshnessStatus) -> dict[str, Any]:
    """Create an alert dictionary from a freshness status.

    Args:
        status: Freshness status.

    Returns:
        Alert dictionary.
    """
    severity = "critical" if status.status == FRESHNESS_STALE else "warning"

    if status.status == FRESHNESS_STALE:
        message = (
            f"Sync '{status.config_name}' is stale. "
            f"Last successful sync was {status.minutes_since_sync} minutes ago "
            f"(SLA: {status.sla_minutes} minutes)."
        )
    else:
        message = (
            f"Sync '{status.config_name}' is approaching SLA threshold. "
            f"Last successful sync was {status.minutes_since_sync} minutes ago "
            f"({status.percent_of_sla:.0f}% of {status.sla_minutes} minute SLA)."
        )

    return {
        "type": "freshness_alert",
        "severity": severity,
        "status": status.status,
        "config_id": status.config_id,
        "config_name": status.config_name,
        "organization_id": status.organization_id,
        "message": message,
        "last_success_at": status.last_success_at.isoformat() if status.last_success_at else None,
        "sla_minutes": status.sla_minutes,
        "minutes_since_sync": status.minutes_since_sync,
        "percent_of_sla": status.percent_of_sla,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _send_alert(alert: dict[str, Any], organization_id: int) -> None:
    """Send an alert via the notification system.

    Args:
        alert: Alert dictionary.
        organization_id: Organization ID.
    """
    from mysql_to_sheets.core.config import get_config

    config = get_config()

    # Format message for notifications
    subject = f"[{alert['severity'].upper()}] Data Freshness Alert: {alert['config_name']}"
    body = alert["message"]

    # Send via available channels
    notifications_sent = False

    # Email
    if config.smtp_host and config.smtp_to:
        try:
            from mysql_to_sheets.core.notifications.email import (
                send_email,  # type: ignore[attr-defined]
            )

            send_email(
                subject=subject,
                body=body,
                config=config,
            )
            notifications_sent = True
            logger.debug(f"Sent email alert for config {alert['config_id']}")
        except (OSError, RuntimeError, ImportError) as e:
            logger.warning(f"Failed to send email alert: {e}")

    # Slack
    if config.slack_webhook_url:
        try:
            from mysql_to_sheets.core.notifications.slack import (
                send_slack_message,  # type: ignore[attr-defined]
            )

            # Color based on severity
            color = "#dc3545" if alert["severity"] == "critical" else "#ffc107"

            send_slack_message(
                text=subject,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{subject}*\n{body}"},
                    },
                    {
                        "type": "context",
                        "elements": [
                            {"type": "mrkdwn", "text": f"Config ID: {alert['config_id']}"},
                            {"type": "mrkdwn", "text": f"SLA: {alert['sla_minutes']} min"},
                        ],
                    },
                ],
                config=config,
            )
            notifications_sent = True
            logger.debug(f"Sent Slack alert for config {alert['config_id']}")
        except (OSError, RuntimeError, ImportError) as e:
            logger.warning(f"Failed to send Slack alert: {e}")

    # Webhook
    if config.notification_webhook_url:
        try:
            from mysql_to_sheets.core.notifications.webhook import (
                send_webhook,  # type: ignore[attr-defined]
            )

            send_webhook(
                url=config.notification_webhook_url,
                payload=alert,
            )
            notifications_sent = True
            logger.debug(f"Sent webhook alert for config {alert['config_id']}")
        except (OSError, RuntimeError, ImportError) as e:
            logger.warning(f"Failed to send webhook alert: {e}")

    if not notifications_sent:
        logger.warning(
            f"No notification channels configured for alert on config {alert['config_id']}"
        )
