"""Audit log retention management.

Provides functions for managing audit log retention including
automated cleanup of old logs and retention statistics.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.models.audit_logs import get_audit_log_repository

logger = get_module_logger(__name__)


@dataclass
class RetentionStats:
    """Statistics about audit log retention.

    Attributes:
        total_logs: Total number of audit logs.
        oldest_log: Timestamp of oldest log.
        newest_log: Timestamp of newest log.
        logs_to_delete: Number of logs eligible for deletion.
        retention_days: Current retention period in days.
    """

    total_logs: int
    oldest_log: datetime | None
    newest_log: datetime | None
    logs_to_delete: int
    retention_days: int

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_logs": self.total_logs,
            "oldest_log": self.oldest_log.isoformat() if self.oldest_log else None,
            "newest_log": self.newest_log.isoformat() if self.newest_log else None,
            "logs_to_delete": self.logs_to_delete,
            "retention_days": self.retention_days,
        }


@dataclass
class CleanupResult:
    """Result of audit log cleanup operation.

    Attributes:
        deleted_count: Number of logs deleted.
        cutoff_date: Logs older than this were deleted.
        dry_run: Whether this was a dry run.
        organization_id: Organization scope (None for all).
    """

    deleted_count: int
    cutoff_date: datetime
    dry_run: bool
    organization_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "deleted_count": self.deleted_count,
            "cutoff_date": self.cutoff_date.isoformat(),
            "dry_run": self.dry_run,
            "organization_id": self.organization_id,
        }


def cleanup_old_logs(
    retention_days: int,
    db_path: str,
    organization_id: int | None = None,
    dry_run: bool = False,
) -> CleanupResult:
    """Delete audit logs older than retention period.

    Args:
        retention_days: Delete logs older than this many days.
        db_path: Path to audit log database.
        organization_id: Optionally scope to specific organization.
        dry_run: If True, only report what would be deleted.

    Returns:
        CleanupResult with deletion count.

    Raises:
        ValueError: If retention_days is invalid.
    """
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1")

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    repo = get_audit_log_repository(db_path)

    if dry_run:
        # Count how many would be deleted
        count = (
            repo.count(
                organization_id=organization_id or 0,
                to_date=cutoff_date,
            )
            if organization_id
            else _count_all_before(repo, cutoff_date)
        )

        logger.info(
            f"Dry run: would delete {count} audit logs older than {cutoff_date.isoformat()}"
        )
        return CleanupResult(
            deleted_count=count,
            cutoff_date=cutoff_date,
            dry_run=True,
            organization_id=organization_id,
        )

    # Actually delete
    deleted_count = repo.delete_before(cutoff_date, organization_id)

    logger.info(f"Deleted {deleted_count} audit logs older than {cutoff_date.isoformat()}")
    return CleanupResult(
        deleted_count=deleted_count,
        cutoff_date=cutoff_date,
        dry_run=False,
        organization_id=organization_id,
    )


def _count_all_before(repo: Any, cutoff_date: datetime) -> int:
    """Count all logs before cutoff date across all organizations.

    Args:
        repo: AuditLogRepository instance.
        cutoff_date: Cutoff timestamp.

    Returns:
        Total count.
    """
    # This is a bit hacky but avoids adding a new method
    # We'll count logs without org filter
    from sqlalchemy import func

    from mysql_to_sheets.models.audit_logs import AuditLogModel

    session = repo._get_session()
    try:
        count = (
            session.query(func.count(AuditLogModel.id))
            .filter(AuditLogModel.timestamp < cutoff_date)
            .scalar()
        )
        return count or 0
    finally:
        session.close()


def get_retention_stats(
    organization_id: int,
    db_path: str,
    retention_days: int = 90,
) -> RetentionStats:
    """Get audit log retention statistics for an organization.

    Args:
        organization_id: Organization to query.
        db_path: Path to audit log database.
        retention_days: Retention period for calculating eligible deletions.

    Returns:
        RetentionStats with volume and age information.
    """
    repo = get_audit_log_repository(db_path)
    stats = repo.get_stats(organization_id)

    # Calculate logs eligible for deletion
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    logs_to_delete = repo.count(
        organization_id=organization_id,
        to_date=cutoff_date,
    )

    oldest = None
    newest = None
    if stats.get("oldest_log"):
        oldest = datetime.fromisoformat(stats["oldest_log"])
    if stats.get("newest_log"):
        newest = datetime.fromisoformat(stats["newest_log"])

    return RetentionStats(
        total_logs=stats.get("total_logs", 0),
        oldest_log=oldest,
        newest_log=newest,
        logs_to_delete=logs_to_delete,
        retention_days=retention_days,
    )


def get_global_retention_stats(
    db_path: str,
    retention_days: int = 90,
) -> dict[str, Any]:
    """Get global audit log statistics across all organizations.

    Args:
        db_path: Path to audit log database.
        retention_days: Retention period for calculating eligible deletions.

    Returns:
        Dictionary with global statistics.
    """
    from sqlalchemy import func

    from mysql_to_sheets.models.audit_logs import AuditLogModel

    repo = get_audit_log_repository(db_path)
    session = repo._get_session()

    try:
        # Total count
        total = session.query(func.count(AuditLogModel.id)).scalar()

        # Oldest and newest
        oldest = session.query(func.min(AuditLogModel.timestamp)).scalar()
        newest = session.query(func.max(AuditLogModel.timestamp)).scalar()

        # Logs eligible for deletion
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        to_delete = (
            session.query(func.count(AuditLogModel.id))
            .filter(AuditLogModel.timestamp < cutoff_date)
            .scalar()
        )

        # Count by organization
        org_counts = (
            session.query(
                AuditLogModel.organization_id,
                func.count(AuditLogModel.id),
            )
            .group_by(AuditLogModel.organization_id)
            .all()
        )

        return {
            "total_logs": total or 0,
            "oldest_log": oldest.isoformat() if oldest else None,
            "newest_log": newest.isoformat() if newest else None,
            "logs_to_delete": to_delete or 0,
            "retention_days": retention_days,
            "by_organization": {org_id: count for org_id, count in org_counts},
        }
    finally:
        session.close()


def schedule_cleanup(
    retention_days: int,
    db_path: str,
) -> None:
    """Schedule automated cleanup of old audit logs.

    This is a placeholder for integration with APScheduler.
    The actual scheduling should be done in the scheduler module.

    Args:
        retention_days: Days to retain logs.
        db_path: Path to audit log database.
    """
    # This would integrate with the existing scheduler system
    # For now, just log the intent
    logger.info(f"Audit log cleanup scheduled: delete logs older than {retention_days} days")
