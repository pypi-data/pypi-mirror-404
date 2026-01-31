"""SQLAlchemy model and repository for usage tracking.

Usage records track rows synced, sync operations, and API calls per organization
per billing period. This data is used for billing integration and usage analytics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Column, Date, DateTime, Index, Integer, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    """Declarative base for usage models."""

    pass


@dataclass
class UsageRecord:
    """Usage tracking record for billing.

    Tracks usage metrics for an organization during a billing period.
    Each organization has one record per billing period.

    Attributes:
        organization_id: Organization this usage belongs to.
        period_start: First day of the billing period.
        period_end: Last day of the billing period.
        id: Primary key (auto-generated).
        rows_synced: Total rows synced during the period.
        sync_operations: Number of sync operations performed.
        api_calls: Number of API calls made.
        created_at: When the record was created.
        updated_at: When the record was last updated.
    """

    organization_id: int
    period_start: date
    period_end: date
    id: int | None = None
    rows_synced: int = 0
    sync_operations: int = 0
    api_calls: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the usage record.
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "rows_synced": self.rows_synced,
            "sync_operations": self.sync_operations,
            "api_calls": self.api_calls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UsageRecord":
        """Create UsageRecord from dictionary.

        Args:
            data: Dictionary with usage data.

        Returns:
            UsageRecord instance.
        """
        period_start_raw = data.get("period_start")
        if isinstance(period_start_raw, str):
            period_start_val: date | Any | None = date.fromisoformat(period_start_raw)
        else:
            period_start_val = period_start_raw

        period_end_raw = data.get("period_end")
        if isinstance(period_end_raw, str):
            period_end_val: date | Any | None = date.fromisoformat(period_end_raw)
        else:
            period_end_val = period_end_raw

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        # Cast to satisfy type checker
        period_start_date = period_start_val if isinstance(period_start_val, date) else date.today()
        period_end_date = period_end_val if isinstance(period_end_val, date) else date.today()

        return cls(
            id=data.get("id"),
            organization_id=data["organization_id"],
            period_start=period_start_date,
            period_end=period_end_date,
            rows_synced=data.get("rows_synced", 0),
            sync_operations=data.get("sync_operations", 0),
            api_calls=data.get("api_calls", 0),
            created_at=created_at,
            updated_at=updated_at,
        )


class UsageRecordModel(Base):
    """SQLAlchemy model for usage records.

    Stores usage metrics per organization per billing period.
    """

    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    rows_synced = Column(Integer, nullable=False, default=0)
    sync_operations = Column(Integer, nullable=False, default=0)
    api_calls = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc))

    # Composite index for efficient period lookups
    __table_args__ = (
        Index("ix_usage_records_org_period", "organization_id", "period_start", "period_end"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the usage record.
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None,
            "rows_synced": self.rows_synced,
            "sync_operations": self.sync_operations,
            "api_calls": self.api_calls,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dataclass(self) -> UsageRecord:
        """Convert model to UsageRecord dataclass.

        Returns:
            UsageRecord dataclass instance.
        """
        return UsageRecord(
            id=self.id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            period_start=self.period_start,  # type: ignore[arg-type]
            period_end=self.period_end,  # type: ignore[arg-type]
            rows_synced=self.rows_synced,  # type: ignore[arg-type]
            sync_operations=self.sync_operations,  # type: ignore[arg-type]
            api_calls=self.api_calls,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, record: UsageRecord) -> "UsageRecordModel":
        """Create model from UsageRecord dataclass.

        Args:
            record: UsageRecord dataclass instance.

        Returns:
            UsageRecordModel instance.
        """
        return cls(
            id=record.id,
            organization_id=record.organization_id,
            period_start=record.period_start,
            period_end=record.period_end,
            rows_synced=record.rows_synced,
            sync_operations=record.sync_operations,
            api_calls=record.api_calls,
            created_at=record.created_at or datetime.now(timezone.utc),
            updated_at=record.updated_at,
        )

    def __repr__(self) -> str:
        """String representation of usage record."""
        return (
            f"UsageRecord(org={self.organization_id}, "
            f"period={self.period_start} to {self.period_end}, "
            f"rows={self.rows_synced}, ops={self.sync_operations})"
        )


def get_current_period() -> tuple[date, date]:
    """Get the current billing period (calendar month).

    Returns:
        Tuple of (period_start, period_end) dates.
    """
    today = date.today()
    period_start = today.replace(day=1)

    # Calculate last day of month
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    period_end = next_month - timedelta(days=1)

    return period_start, period_end


class UsageRepository:
    """Repository for usage record CRUD operations.

    Provides data access methods for usage tracking with
    SQLite persistence.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine: Engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def get_or_create_current(self, organization_id: int) -> UsageRecord:
        """Get or create usage record for current billing period.

        Args:
            organization_id: Organization ID.

        Returns:
            UsageRecord for the current period.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        period_start, period_end = get_current_period()
        return self.get_or_create(organization_id, period_start, period_end)

    def get_or_create(
        self,
        organization_id: int,
        period_start: date,
        period_end: date,
    ) -> UsageRecord:
        """Get or create usage record for a specific period.

        Args:
            organization_id: Organization ID.
            period_start: Period start date.
            period_end: Period end date.

        Returns:
            UsageRecord for the period.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(UsageRecordModel)
                .filter(
                    UsageRecordModel.organization_id == organization_id,
                    UsageRecordModel.period_start == period_start,
                    UsageRecordModel.period_end == period_end,
                )
                .first()
            )

            if model:
                return model.to_dataclass()

            # Create new record
            model = UsageRecordModel(
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                rows_synced=0,
                sync_operations=0,
                api_calls=0,
            )
            session.add(model)
            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_rows_synced(
        self,
        organization_id: int,
        rows: int,
        increment_operations: bool = True,
    ) -> UsageRecord:
        """Increment rows synced counter for current period.

        Args:
            organization_id: Organization ID.
            rows: Number of rows to add.
            increment_operations: Also increment sync_operations by 1.

        Returns:
            Updated UsageRecord.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        period_start, period_end = get_current_period()
        session = self._get_session()
        try:
            model = (
                session.query(UsageRecordModel)
                .filter(
                    UsageRecordModel.organization_id == organization_id,
                    UsageRecordModel.period_start == period_start,
                    UsageRecordModel.period_end == period_end,
                )
                .first()
            )

            if not model:
                # Create new record
                model = UsageRecordModel(
                    organization_id=organization_id,
                    period_start=period_start,
                    period_end=period_end,
                    rows_synced=rows,
                    sync_operations=1 if increment_operations else 0,
                    api_calls=0,
                )
                session.add(model)
            else:
                model.rows_synced += rows  # type: ignore[assignment]
                if increment_operations:
                    model.sync_operations += 1  # type: ignore[assignment]
                model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_api_calls(
        self,
        organization_id: int,
        count: int = 1,
    ) -> UsageRecord:
        """Increment API call counter for current period.

        Args:
            organization_id: Organization ID.
            count: Number of calls to add (default 1).

        Returns:
            Updated UsageRecord.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        period_start, period_end = get_current_period()
        session = self._get_session()
        try:
            model = (
                session.query(UsageRecordModel)
                .filter(
                    UsageRecordModel.organization_id == organization_id,
                    UsageRecordModel.period_start == period_start,
                    UsageRecordModel.period_end == period_end,
                )
                .first()
            )

            if not model:
                # Create new record
                model = UsageRecordModel(
                    organization_id=organization_id,
                    period_start=period_start,
                    period_end=period_end,
                    rows_synced=0,
                    sync_operations=0,
                    api_calls=count,
                )
                session.add(model)
            else:
                model.api_calls += count  # type: ignore[assignment]
                model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_period(
        self,
        organization_id: int,
        period_start: date,
        period_end: date,
    ) -> UsageRecord | None:
        """Get usage record for a specific period.

        Args:
            organization_id: Organization ID.
            period_start: Period start date.
            period_end: Period end date.

        Returns:
            UsageRecord if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(UsageRecordModel)
                .filter(
                    UsageRecordModel.organization_id == organization_id,
                    UsageRecordModel.period_start == period_start,
                    UsageRecordModel.period_end == period_end,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_history(
        self,
        organization_id: int,
        limit: int = 12,
    ) -> list[UsageRecord]:
        """Get usage history for an organization.

        Args:
            organization_id: Organization ID.
            limit: Maximum number of periods to return.

        Returns:
            List of UsageRecords, most recent first.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            models = (
                session.query(UsageRecordModel)
                .filter(UsageRecordModel.organization_id == organization_id)
                .order_by(UsageRecordModel.period_start.desc())
                .limit(limit)
                .all()
            )
            return [m.to_dataclass() for m in models]
        finally:
            session.close()

    def get_summary(self, organization_id: int) -> dict[str, Any]:
        """Get usage summary for current period.

        Args:
            organization_id: Organization ID.

        Returns:
            Dictionary with current period usage and totals.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        current = self.get_or_create_current(organization_id)
        history = self.get_history(organization_id, limit=12)

        total_rows = sum(r.rows_synced for r in history)
        total_operations = sum(r.sync_operations for r in history)
        total_api_calls = sum(r.api_calls for r in history)

        return {
            "current_period": current.to_dict(),
            "totals": {
                "rows_synced": total_rows,
                "sync_operations": total_operations,
                "api_calls": total_api_calls,
            },
            "periods_tracked": len(history),
        }


# Singleton instance
_usage_repository: UsageRepository | None = None


def get_usage_repository(db_path: str | None = None) -> UsageRepository:
    """Get or create usage repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        UsageRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _usage_repository
    if _usage_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _usage_repository = UsageRepository(db_path)
    return _usage_repository


def reset_usage_repository() -> None:
    """Reset usage repository singleton. For testing."""
    global _usage_repository
    _usage_repository = None
