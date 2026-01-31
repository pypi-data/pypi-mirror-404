"""SQLAlchemy model for persistent webhook idempotency tracking.

Stores processed webhook idempotency keys to prevent duplicate event
processing, even across application restarts.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for webhook events models."""

    pass


class ProcessedWebhookEventModel(Base):
    """Tracks processed webhook idempotency keys.

    Each row represents a webhook event that has already been handled.
    Entries older than the TTL can be safely cleaned up.
    """

    __tablename__ = "processed_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    idempotency_key = Column(String(256), nullable=False, unique=True, index=True)
    processed_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )


_DEFAULT_TTL_DAYS = 7


def _get_engine(db_path: str) -> Engine:
    """Create or get SQLAlchemy engine for webhook events DB."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


def check_idempotency_key(key: str | None, db_path: str) -> bool:
    """Check if a webhook has already been processed.

    Args:
        key: Idempotency key from header or payload.
        db_path: Path to the SQLite database file.

    Returns:
        True if already processed (caller should skip).
    """
    if not key:
        return False

    engine = _get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        existing = (
            session.query(ProcessedWebhookEventModel)
            .filter(ProcessedWebhookEventModel.idempotency_key == key)
            .first()
        )
        if existing:
            return True

        # Record the key
        event = ProcessedWebhookEventModel(
            idempotency_key=key,
            processed_at=datetime.now(timezone.utc),
        )
        session.add(event)
        session.commit()
        return False
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def cleanup_old_events(db_path: str, ttl_days: int = _DEFAULT_TTL_DAYS) -> int:
    """Remove processed events older than the TTL.

    Args:
        db_path: Path to the SQLite database file.
        ttl_days: Number of days to retain entries.

    Returns:
        Number of entries deleted.
    """
    engine = _get_engine(db_path)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=ttl_days)
        count = (
            session.query(ProcessedWebhookEventModel)
            .filter(ProcessedWebhookEventModel.processed_at < cutoff)
            .delete()
        )
        session.commit()
        return count
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
