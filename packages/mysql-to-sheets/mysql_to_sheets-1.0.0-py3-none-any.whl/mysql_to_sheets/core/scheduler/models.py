"""Data models for the scheduler module.

This module defines the ScheduledJob dataclass and related types
for representing scheduled sync operations.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from mysql_to_sheets.models.utils import parse_datetime


class JobStatus(Enum):
    """Status of a scheduled job."""

    PENDING = "pending"  # Job created but never run
    RUNNING = "running"  # Job currently executing
    SUCCESS = "success"  # Last run succeeded
    FAILED = "failed"  # Last run failed
    DISABLED = "disabled"  # Job is disabled


@dataclass
class ScheduledJob:
    """A scheduled sync job.

    Attributes:
        id: Unique job identifier.
        name: Human-readable name for the job.
        cron_expression: Cron expression for scheduling (e.g., "0 6 * * *").
        interval_minutes: Alternative to cron - run every N minutes.
        sheet_id: Override Google Sheet ID (None = use config).
        worksheet_name: Override worksheet name (None = use config).
        sql_query: Override SQL query (None = use config).
        notify_on_success: Override success notification (None = use config).
        notify_on_failure: Override failure notification (None = use config).
        enabled: Whether the job is active.
        created_at: When the job was created.
        updated_at: When the job was last modified.
        last_run_at: When the job last executed.
        last_run_success: Whether the last run succeeded.
        last_run_message: Status message from last run.
        last_run_rows: Rows synced in last run.
        last_run_duration_ms: Duration of last run in milliseconds.
        next_run_at: When the job will next execute.
    """

    id: int | None = None
    name: str = ""
    cron_expression: str | None = None
    interval_minutes: int | None = None
    sheet_id: str | None = None
    worksheet_name: str | None = None
    sql_query: str | None = None
    notify_on_success: bool | None = None
    notify_on_failure: bool | None = None
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = None
    last_run_at: datetime | None = None
    last_run_success: bool | None = None
    last_run_message: str | None = None
    last_run_rows: int | None = None
    last_run_duration_ms: float | None = None
    next_run_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert job to dictionary.

        Returns:
            Dictionary representation of the job.
        """
        return {
            "id": self.id,
            "name": self.name,
            "cron_expression": self.cron_expression,
            "interval_minutes": self.interval_minutes,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "sql_query": self.sql_query,
            "notify_on_success": self.notify_on_success,
            "notify_on_failure": self.notify_on_failure,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "last_run_success": self.last_run_success,
            "last_run_message": self.last_run_message,
            "last_run_rows": self.last_run_rows,
            "last_run_duration_ms": self.last_run_duration_ms,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduledJob":
        """Create job from dictionary.

        Args:
            data: Dictionary with job data.

        Returns:
            ScheduledJob instance.
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            cron_expression=data.get("cron_expression"),
            interval_minutes=data.get("interval_minutes"),
            sheet_id=data.get("sheet_id"),
            worksheet_name=data.get("worksheet_name"),
            sql_query=data.get("sql_query"),
            notify_on_success=data.get("notify_on_success"),
            notify_on_failure=data.get("notify_on_failure"),
            enabled=data.get("enabled", True),
            created_at=parse_datetime(data.get("created_at")) or datetime.now(timezone.utc),
            updated_at=parse_datetime(data.get("updated_at")),
            last_run_at=parse_datetime(data.get("last_run_at")),
            last_run_success=data.get("last_run_success"),
            last_run_message=data.get("last_run_message"),
            last_run_rows=data.get("last_run_rows"),
            last_run_duration_ms=data.get("last_run_duration_ms"),
            next_run_at=parse_datetime(data.get("next_run_at")),
        )

    @property
    def status(self) -> JobStatus:
        """Get the current status of the job.

        Returns:
            JobStatus enum value.
        """
        if not self.enabled:
            return JobStatus.DISABLED
        if self.last_run_at is None:
            return JobStatus.PENDING
        if self.last_run_success:
            return JobStatus.SUCCESS
        return JobStatus.FAILED

    @property
    def schedule_type(self) -> str:
        """Get the schedule type (cron or interval).

        Returns:
            'cron' or 'interval'.
        """
        if self.cron_expression:
            return "cron"
        return "interval"

    @property
    def schedule_display(self) -> str:
        """Get human-readable schedule description.

        Returns:
            Schedule description string.
        """
        if self.cron_expression:
            return f"Cron: {self.cron_expression}"
        if self.interval_minutes:
            if self.interval_minutes < 60:
                return f"Every {self.interval_minutes} minutes"
            hours = self.interval_minutes // 60
            minutes = self.interval_minutes % 60
            if minutes == 0:
                return f"Every {hours} hour(s)"
            return f"Every {hours}h {minutes}m"
        return "Not scheduled"

    def validate(self) -> list[str]:
        """Validate job configuration.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        if not self.name:
            errors.append("Job name is required")

        if not self.cron_expression and not self.interval_minutes:
            errors.append("Either cron_expression or interval_minutes is required")

        if self.cron_expression and self.interval_minutes:
            errors.append("Cannot specify both cron_expression and interval_minutes")

        if self.interval_minutes is not None and self.interval_minutes < 1:
            errors.append("interval_minutes must be at least 1")

        return errors

    def __repr__(self) -> str:
        """String representation of job."""
        return (
            f"ScheduledJob(id={self.id}, name={self.name!r}, "
            f"schedule={self.schedule_display!r}, enabled={self.enabled})"
        )
