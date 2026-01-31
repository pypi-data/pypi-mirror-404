"""SQLAlchemy model for scheduled job persistence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase

from mysql_to_sheets.models.utils import parse_datetime


class Base(DeclarativeBase):
    """Declarative base for scheduled jobs models."""

    pass


class ScheduledJobModel(Base):
    """SQLAlchemy model for scheduled sync jobs.

    Stores scheduled job configuration and execution history.
    """

    __tablename__ = "scheduled_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    cron_expression = Column(String(100), nullable=True)
    interval_minutes = Column(Integer, nullable=True)
    sheet_id = Column(String(100), nullable=True)
    worksheet_name = Column(String(100), nullable=True)
    sql_query = Column(Text, nullable=True)
    notify_on_success = Column(Boolean, nullable=True)  # None = use config
    notify_on_failure = Column(Boolean, nullable=True)  # None = use config
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True)
    last_run_at = Column(DateTime, nullable=True)
    last_run_success = Column(Boolean, nullable=True)
    last_run_message = Column(String(500), nullable=True)
    last_run_rows = Column(Integer, nullable=True)
    last_run_duration_ms = Column(Float, nullable=True)
    next_run_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the scheduled job.
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
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScheduledJobModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with job data.

        Returns:
            ScheduledJobModel instance.
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

    def __repr__(self) -> str:
        """String representation of scheduled job."""
        schedule = self.cron_expression or f"every {self.interval_minutes}m"
        status = "enabled" if self.enabled else "disabled"
        return f"ScheduledJob(id={self.id}, name={self.name!r}, schedule={schedule!r}, {status})"
