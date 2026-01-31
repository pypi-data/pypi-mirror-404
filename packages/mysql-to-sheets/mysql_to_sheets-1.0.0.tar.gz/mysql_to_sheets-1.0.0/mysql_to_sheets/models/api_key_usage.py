"""SQLAlchemy model for API key usage tracking.

Provides per-key daily usage aggregation for analytics and billing.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    Index,
    Integer,
    UniqueConstraint,
    create_engine,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for API key usage models."""

    pass


class APIKeyUsageModel(Base):
    """SQLAlchemy model for API key usage tracking.

    Stores daily aggregated usage metrics per API key.
    Uses upsert pattern for efficient increment operations.
    """

    __tablename__ = "api_key_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key_id = Column(Integer, nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    request_count = Column(Integer, nullable=False, default=0)
    bytes_transferred = Column(BigInteger, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("api_key_id", "date", name="uix_api_key_usage_day"),
        Index("ix_api_key_usage_key_date", "api_key_id", "date"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of usage record.
        """
        return {
            "id": self.id,
            "api_key_id": self.api_key_id,
            "date": self.date.isoformat() if self.date else None,
            "request_count": self.request_count,
            "bytes_transferred": self.bytes_transferred,
        }


class APIKeyUsageRepository:
    """Repository for API key usage operations.

    Provides efficient upsert operations for incrementing daily counters
    and aggregation queries for analytics.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize API key usage repository.

        Args:
            db_path: Path to SQLite database file.
        """
        from pathlib import Path

        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine: Engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory: sessionmaker[Session] = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def record_request(
        self,
        api_key_id: int,
        bytes_count: int = 0,
    ) -> None:
        """Increment daily request counter for an API key.

        Uses upsert pattern: tries UPDATE first (common case),
        falls back to INSERT if no existing row.

        Args:
            api_key_id: API key ID to record usage for.
            bytes_count: Optional bytes transferred in this request.
        """
        session = self._get_session()
        today = date.today()

        try:
            # Try update first (common case - row exists)
            result = session.execute(
                update(APIKeyUsageModel)
                .where(APIKeyUsageModel.api_key_id == api_key_id)
                .where(APIKeyUsageModel.date == today)
                .values(
                    request_count=APIKeyUsageModel.request_count + 1,
                    bytes_transferred=APIKeyUsageModel.bytes_transferred + bytes_count,
                )
            )

            if result.rowcount == 0:
                # No existing row, insert new one
                session.add(
                    APIKeyUsageModel(
                        api_key_id=api_key_id,
                        date=today,
                        request_count=1,
                        bytes_transferred=bytes_count,
                    )
                )

            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_usage_stats(
        self,
        api_key_id: int,
        days: int = 30,
    ) -> dict[str, Any]:
        """Get usage statistics for an API key.

        Args:
            api_key_id: API key ID to get stats for.
            days: Number of days to include (default 30).

        Returns:
            Dictionary with usage statistics.
        """
        session = self._get_session()
        cutoff = date.today() - timedelta(days=days)

        try:
            rows = (
                session.query(APIKeyUsageModel)
                .filter(
                    APIKeyUsageModel.api_key_id == api_key_id,
                    APIKeyUsageModel.date >= cutoff,
                )
                .order_by(APIKeyUsageModel.date)
                .all()
            )

            return {
                "api_key_id": api_key_id,
                "period_days": days,
                "total_requests": sum(r.request_count for r in rows),
                "total_bytes": sum(r.bytes_transferred for r in rows),
                "daily": [
                    {
                        "date": r.date.isoformat(),
                        "requests": r.request_count,
                        "bytes": r.bytes_transferred,
                    }
                    for r in rows
                ],
            }
        finally:
            session.close()

    def get_all_usage_stats(
        self,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get usage statistics for all API keys.

        Args:
            days: Number of days to include (default 30).

        Returns:
            List of usage statistics per API key.
        """
        session = self._get_session()
        cutoff = date.today() - timedelta(days=days)

        try:
            # Get all usage records in the period
            rows = (
                session.query(APIKeyUsageModel)
                .filter(APIKeyUsageModel.date >= cutoff)
                .order_by(APIKeyUsageModel.api_key_id, APIKeyUsageModel.date)
                .all()
            )

            # Group by api_key_id
            from collections import defaultdict

            by_key: dict[int, list[APIKeyUsageModel]] = defaultdict(list)
            for row in rows:
                by_key[row.api_key_id].append(row)

            return [
                {
                    "api_key_id": key_id,
                    "period_days": days,
                    "total_requests": sum(r.request_count for r in key_rows),
                    "total_bytes": sum(r.bytes_transferred for r in key_rows),
                    "daily": [
                        {
                            "date": r.date.isoformat(),
                            "requests": r.request_count,
                            "bytes": r.bytes_transferred,
                        }
                        for r in key_rows
                    ],
                }
                for key_id, key_rows in sorted(by_key.items())
            ]
        finally:
            session.close()

    def cleanup_old_records(self, older_than_days: int = 90) -> int:
        """Delete usage records older than specified days.

        Args:
            older_than_days: Delete records older than this many days.

        Returns:
            Number of records deleted.
        """
        session = self._get_session()
        cutoff = date.today() - timedelta(days=older_than_days)

        try:
            result = (
                session.query(APIKeyUsageModel)
                .filter(APIKeyUsageModel.date < cutoff)
                .delete()
            )
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def get_api_key_usage_repository(db_path: str) -> APIKeyUsageRepository:
    """Get an API key usage repository instance.

    Args:
        db_path: Path to SQLite database file.

    Returns:
        APIKeyUsageRepository instance.
    """
    return APIKeyUsageRepository(db_path)
