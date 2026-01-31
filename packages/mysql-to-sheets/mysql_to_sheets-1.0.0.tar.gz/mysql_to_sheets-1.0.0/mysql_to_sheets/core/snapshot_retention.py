"""Snapshot retention management.

This module provides functions to manage snapshot storage by enforcing
retention policies based on count and age limits.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from mysql_to_sheets.models.snapshots import (
    get_snapshot_repository,
)


@dataclass
class RetentionConfig:
    """Configuration for snapshot retention.

    Attributes:
        retention_count: Maximum snapshots to keep per sheet (default 10).
        retention_days: Delete snapshots older than this (default 30).
        max_size_mb: Skip snapshot if sheet exceeds this size (default 50).
    """

    retention_count: int = 10
    retention_days: int = 30
    max_size_mb: int = 50

    @property
    def max_size_bytes(self) -> int:
        """Get max size in bytes."""
        return self.max_size_mb * 1024 * 1024


@dataclass
class CleanupResult:
    """Result of a cleanup operation.

    Attributes:
        deleted_by_count: Snapshots deleted due to count limit.
        deleted_by_age: Snapshots deleted due to age limit.
        total_deleted: Total snapshots deleted.
        sheets_processed: Number of unique sheets processed.
        message: Human-readable summary.
    """

    deleted_by_count: int = 0
    deleted_by_age: int = 0
    total_deleted: int = 0
    sheets_processed: int = 0
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "deleted_by_count": self.deleted_by_count,
            "deleted_by_age": self.deleted_by_age,
            "total_deleted": self.total_deleted,
            "sheets_processed": self.sheets_processed,
            "message": self.message,
        }


@dataclass
class StorageStats:
    """Storage statistics for snapshots.

    Attributes:
        total_snapshots: Total number of snapshots.
        total_size_bytes: Total storage used in bytes.
        total_size_mb: Total storage used in megabytes.
        by_sheet: Breakdown by sheet ID.
        oldest_snapshot: Timestamp of oldest snapshot.
        newest_snapshot: Timestamp of newest snapshot.
    """

    total_snapshots: int = 0
    total_size_bytes: int = 0
    total_size_mb: float = 0.0
    by_sheet: dict[str, dict[str, Any]] = field(default_factory=dict)
    oldest_snapshot: str | None = None
    newest_snapshot: str | None = None

    def __post_init__(self) -> None:
        if self.by_sheet is None:
            self.by_sheet = {}
        self.total_size_mb = self.total_size_bytes / (1024 * 1024)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "total_snapshots": self.total_snapshots,
            "total_size_bytes": self.total_size_bytes,
            "total_size_mb": round(self.total_size_mb, 2),
            "by_sheet": self.by_sheet,
            "oldest_snapshot": self.oldest_snapshot,
            "newest_snapshot": self.newest_snapshot,
        }


def cleanup_old_snapshots(
    organization_id: int,
    db_path: str,
    retention_config: RetentionConfig | None = None,
    logger: logging.Logger | None = None,
) -> CleanupResult:
    """Clean up old snapshots based on retention policy.

    Applies two rules:
    1. Keep at most `retention_count` snapshots per sheet (delete oldest)
    2. Delete all snapshots older than `retention_days`

    Args:
        organization_id: Organization to clean up.
        db_path: Path to snapshot database.
        retention_config: Retention settings. Uses defaults if None.
        logger: Optional logger instance.

    Returns:
        CleanupResult with deletion statistics.
    """
    config = retention_config or RetentionConfig()
    repo = get_snapshot_repository(db_path)

    if logger:
        logger.info(
            f"Running snapshot cleanup (keep={config.retention_count}, "
            f"max_age={config.retention_days} days)"
        )

    # Get stats to find all sheets with snapshots
    stats = repo.get_stats(organization_id)
    sheets = list(stats.get("by_sheet", {}).keys())

    deleted_by_count = 0
    deleted_by_age = 0

    # Apply count limit per sheet
    for sheet_id in sheets:
        deleted = repo.delete_oldest(
            organization_id=organization_id,
            sheet_id=sheet_id,
            keep_count=config.retention_count,
        )
        deleted_by_count += deleted
        if deleted > 0 and logger:
            logger.debug(f"Deleted {deleted} old snapshots for sheet {sheet_id}")

    # Apply age limit
    cutoff_date = datetime.now(tz=None) - timedelta(days=config.retention_days)
    deleted_by_age = repo.delete_before(cutoff_date, organization_id)

    if deleted_by_age > 0 and logger:
        logger.debug(f"Deleted {deleted_by_age} snapshots older than {cutoff_date}")

    total_deleted = deleted_by_count + deleted_by_age
    result = CleanupResult(
        deleted_by_count=deleted_by_count,
        deleted_by_age=deleted_by_age,
        total_deleted=total_deleted,
        sheets_processed=len(sheets),
        message=f"Cleaned up {total_deleted} snapshots from {len(sheets)} sheets",
    )

    if logger:
        logger.info(result.message)

    return result


def get_storage_stats(
    organization_id: int,
    db_path: str,
    logger: logging.Logger | None = None,
) -> StorageStats:
    """Get storage statistics for an organization's snapshots.

    Args:
        organization_id: Organization to query.
        db_path: Path to snapshot database.
        logger: Optional logger instance.

    Returns:
        StorageStats with total and per-sheet breakdown.
    """
    repo = get_snapshot_repository(db_path)
    raw_stats = repo.get_stats(organization_id)

    stats = StorageStats(
        total_snapshots=raw_stats.get("total_snapshots", 0),
        total_size_bytes=raw_stats.get("total_size_bytes", 0),
        by_sheet=raw_stats.get("by_sheet", {}),
        oldest_snapshot=raw_stats.get("oldest_snapshot"),
        newest_snapshot=raw_stats.get("newest_snapshot"),
    )

    if logger:
        logger.debug(
            f"Storage stats: {stats.total_snapshots} snapshots, {stats.total_size_mb:.2f} MB"
        )

    return stats


def should_create_snapshot(
    estimated_size_bytes: int,
    retention_config: RetentionConfig | None = None,
    logger: logging.Logger | None = None,
) -> tuple[bool, str]:
    """Check if a snapshot should be created based on size limits.

    Args:
        estimated_size_bytes: Estimated size of the sheet data.
        retention_config: Retention settings with max size limit.
        logger: Optional logger instance.

    Returns:
        Tuple of (should_create, reason_message).
    """
    config = retention_config or RetentionConfig()
    max_bytes = config.max_size_bytes

    if estimated_size_bytes > max_bytes:
        reason = (
            f"Sheet size ({estimated_size_bytes / (1024 * 1024):.1f} MB) "
            f"exceeds limit ({config.max_size_mb} MB)"
        )
        if logger:
            logger.info(f"Skipping snapshot: {reason}")
        return False, reason

    return True, "Sheet size within limits"


def get_retention_config_from_config(config: Any) -> RetentionConfig:
    """Create RetentionConfig from main Config object.

    Args:
        config: Main application Config object.

    Returns:
        RetentionConfig with values from config or defaults.
    """
    return RetentionConfig(
        retention_count=getattr(config, "snapshot_retention_count", 10),
        retention_days=getattr(config, "snapshot_retention_days", 30),
        max_size_mb=getattr(config, "snapshot_max_size_mb", 50),
    )
