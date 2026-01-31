"""Freshness/SLA tracking service for sync configurations.

Provides functions to calculate, update, and report on data freshness
relative to configured SLA thresholds.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from mysql_to_sheets.models.sync_configs import (
    SyncConfigDefinition,
    get_sync_config_repository,
)

logger = logging.getLogger(__name__)


# Freshness status values
FRESHNESS_FRESH = "fresh"
FRESHNESS_WARNING = "warning"
FRESHNESS_STALE = "stale"
FRESHNESS_UNKNOWN = "unknown"


@dataclass
class FreshnessStatus:
    """Freshness status for a sync configuration.

    Attributes:
        config_id: Sync configuration ID.
        config_name: Sync configuration name.
        status: Freshness status (fresh, warning, stale, unknown).
        last_success_at: Last successful sync timestamp.
        sla_minutes: SLA threshold in minutes.
        minutes_since_sync: Minutes since last successful sync.
        percent_of_sla: Percentage of SLA elapsed.
        organization_id: Organization ID.
    """

    config_id: int
    config_name: str
    status: str
    last_success_at: datetime | None
    sla_minutes: int
    minutes_since_sync: int | None
    percent_of_sla: float | None
    organization_id: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "config_id": self.config_id,
            "config_name": self.config_name,
            "status": self.status,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "sla_minutes": self.sla_minutes,
            "minutes_since_sync": self.minutes_since_sync,
            "percent_of_sla": self.percent_of_sla,
            "organization_id": self.organization_id,
        }


def calculate_freshness_status(
    last_success_at: datetime | None,
    sla_minutes: int,
    warning_percent: int | None = None,
) -> tuple[str, int | None, float | None]:
    """Calculate freshness status based on last sync time and SLA.

    Args:
        last_success_at: Last successful sync timestamp.
        sla_minutes: SLA threshold in minutes.
        warning_percent: Percentage of SLA before warning (default from config).

    Returns:
        Tuple of (status, minutes_since_sync, percent_of_sla).
    """
    if warning_percent is None:
        from mysql_to_sheets.core.config import get_config

        config = get_config()
        warning_percent = config.freshness_warning_percent

    if last_success_at is None:
        return FRESHNESS_UNKNOWN, None, None

    now = datetime.now(timezone.utc)
    # Ensure last_success_at is timezone-aware (assume UTC if naive)
    if last_success_at.tzinfo is None:
        last_success_at = last_success_at.replace(tzinfo=timezone.utc)
    delta = now - last_success_at
    minutes_since_sync = int(delta.total_seconds() / 60)
    percent_of_sla = (minutes_since_sync / sla_minutes) * 100 if sla_minutes > 0 else 100

    if minutes_since_sync >= sla_minutes:
        status = FRESHNESS_STALE
    elif percent_of_sla >= warning_percent:
        status = FRESHNESS_WARNING
    else:
        status = FRESHNESS_FRESH

    return status, minutes_since_sync, round(percent_of_sla, 1)


def update_freshness(
    config_id: int,
    organization_id: int,
    success: bool,
    row_count: int | None = None,
    db_path: str | None = None,
) -> bool:
    """Update freshness tracking after a sync.

    Args:
        config_id: Sync configuration ID.
        organization_id: Organization ID.
        success: Whether the sync was successful.
        row_count: Number of rows synced (if successful).
        db_path: Path to database.

    Returns:
        True if updated, False if config not found.
    """
    repo = get_sync_config_repository(db_path)
    updated = repo.update_freshness(
        config_id=config_id,
        organization_id=organization_id,
        success=success,
        row_count=row_count,
    )

    if updated:
        logger.debug(
            f"Updated freshness for config {config_id} (success={success}, rows={row_count})"
        )
    else:
        logger.warning(f"Failed to update freshness for config {config_id} - not found")

    return updated


def get_freshness_status(
    config_id: int,
    organization_id: int,
    db_path: str | None = None,
) -> FreshnessStatus | None:
    """Get freshness status for a sync configuration.

    Args:
        config_id: Sync configuration ID.
        organization_id: Organization ID.
        db_path: Path to database.

    Returns:
        FreshnessStatus if config found, None otherwise.
    """
    repo = get_sync_config_repository(db_path)
    config = repo.get_by_id(config_id, organization_id)

    if not config:
        return None

    return _config_to_freshness_status(config)


def check_all_freshness(
    organization_id: int,
    enabled_only: bool = True,
    db_path: str | None = None,
) -> list[FreshnessStatus]:
    """Check freshness for all sync configurations in an organization.

    Args:
        organization_id: Organization ID.
        enabled_only: Whether to only check enabled configs.
        db_path: Path to database.

    Returns:
        List of FreshnessStatus objects.
    """
    repo = get_sync_config_repository(db_path)
    configs = repo.get_all(organization_id=organization_id, enabled_only=enabled_only)

    return [_config_to_freshness_status(config) for config in configs]


def get_freshness_report(
    organization_id: int,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Get a freshness report for an organization.

    Args:
        organization_id: Organization ID.
        db_path: Path to database.

    Returns:
        Dictionary with summary statistics and individual statuses.
    """
    statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)

    # Count by status
    counts = {
        FRESHNESS_FRESH: 0,
        FRESHNESS_WARNING: 0,
        FRESHNESS_STALE: 0,
        FRESHNESS_UNKNOWN: 0,
    }
    for status in statuses:
        counts[status.status] = counts.get(status.status, 0) + 1

    # Calculate overall health
    total = len(statuses)
    if total == 0:
        health_percent = 100.0
    else:
        fresh_count = counts[FRESHNESS_FRESH]
        health_percent = round((fresh_count / total) * 100, 1)

    return {
        "organization_id": organization_id,
        "total_configs": total,
        "counts": counts,
        "health_percent": health_percent,
        "statuses": [s.to_dict() for s in statuses],
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


def get_stale_configs(
    organization_id: int,
    db_path: str | None = None,
) -> list[FreshnessStatus]:
    """Get all stale configurations for an organization.

    Args:
        organization_id: Organization ID.
        db_path: Path to database.

    Returns:
        List of FreshnessStatus objects for stale configs.
    """
    all_statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)
    return [s for s in all_statuses if s.status == FRESHNESS_STALE]


def get_warning_configs(
    organization_id: int,
    db_path: str | None = None,
) -> list[FreshnessStatus]:
    """Get all warning configurations for an organization.

    Args:
        organization_id: Organization ID.
        db_path: Path to database.

    Returns:
        List of FreshnessStatus objects for warning configs.
    """
    all_statuses = check_all_freshness(organization_id, enabled_only=True, db_path=db_path)
    return [s for s in all_statuses if s.status == FRESHNESS_WARNING]


def set_sla(
    config_id: int,
    organization_id: int,
    sla_minutes: int,
    db_path: str | None = None,
) -> bool:
    """Set the SLA threshold for a sync configuration.

    Args:
        config_id: Sync configuration ID.
        organization_id: Organization ID.
        sla_minutes: New SLA threshold in minutes.
        db_path: Path to database.

    Returns:
        True if updated, False if config not found.

    Raises:
        ValueError: If sla_minutes is invalid.
    """
    if sla_minutes < 1:
        raise ValueError("SLA must be at least 1 minute")

    repo = get_sync_config_repository(db_path)
    updated = repo.update_sla(config_id, organization_id, sla_minutes)

    if updated:
        logger.info(f"Set SLA for config {config_id} to {sla_minutes} minutes")
    else:
        logger.warning(f"Failed to set SLA for config {config_id} - not found")

    return updated


# Consecutive failure tracking for alerting
_failure_counts: dict[int, int] = {}  # config_id -> consecutive failure count


def track_sync_result(
    config_id: int,
    organization_id: int,
    success: bool,
    error_code: str | None = None,
    error_message: str | None = None,
    db_path: str | None = None,
    alert_threshold: int = 3,
) -> dict[str, Any] | None:
    """Track sync result and check for consecutive failure alerts.

    This function tracks sync success/failure and triggers alerts
    when consecutive failures exceed the threshold.

    Args:
        config_id: Sync configuration ID.
        organization_id: Organization ID.
        success: Whether the sync was successful.
        error_code: Error code if failed.
        error_message: Error message if failed.
        db_path: Path to database.
        alert_threshold: Number of consecutive failures before alerting.

    Returns:
        Alert dict if threshold exceeded, None otherwise.
    """
    global _failure_counts

    if success:
        # Reset on success
        _failure_counts[config_id] = 0
        return None

    # Increment failure count
    _failure_counts[config_id] = _failure_counts.get(config_id, 0) + 1
    current_count = _failure_counts[config_id]

    # Check if we should alert
    if current_count >= alert_threshold and current_count % alert_threshold == 0:
        # Log audit event for consecutive failures
        if db_path:
            from mysql_to_sheets.core.audit import log_consecutive_failures_alert

            log_consecutive_failures_alert(
                organization_id=organization_id,
                db_path=db_path,
                config_id=config_id,
                consecutive_count=current_count,
                threshold=alert_threshold,
                last_error=error_message,
            )

        # Record in metrics
        from mysql_to_sheets.core.metrics import get_registry

        registry = get_registry()
        gauge = registry.gauge(
            "mysql_to_sheets_consecutive_failures",
            "Current consecutive failure count",
            labels={"config_id": str(config_id)},
        )
        gauge.set(current_count)

        return {
            "alert_type": "consecutive_failures",
            "config_id": config_id,
            "consecutive_count": current_count,
            "threshold": alert_threshold,
            "error_code": error_code,
            "error_message": error_message,
        }

    return None


def get_consecutive_failure_count(config_id: int) -> int:
    """Get consecutive failure count for a config.

    Args:
        config_id: Sync configuration ID.

    Returns:
        Current consecutive failure count.
    """
    return _failure_counts.get(config_id, 0)


def reset_failure_tracking() -> None:
    """Reset all failure tracking (for testing)."""
    global _failure_counts
    _failure_counts = {}


def _config_to_freshness_status(config: SyncConfigDefinition) -> FreshnessStatus:
    """Convert a SyncConfigDefinition to FreshnessStatus.

    Args:
        config: Sync configuration.

    Returns:
        FreshnessStatus for the configuration.
    """
    status, minutes, percent = calculate_freshness_status(
        config.last_success_at,
        config.sla_minutes,
    )

    return FreshnessStatus(
        config_id=config.id or 0,
        config_name=config.name,
        status=status,
        last_success_at=config.last_success_at,
        sla_minutes=config.sla_minutes,
        minutes_since_sync=minutes,
        percent_of_sla=percent,
        organization_id=config.organization_id,
    )
