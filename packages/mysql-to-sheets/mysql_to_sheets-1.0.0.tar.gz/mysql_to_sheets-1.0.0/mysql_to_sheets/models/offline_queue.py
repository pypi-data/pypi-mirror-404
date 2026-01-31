"""SQLAlchemy model and repository for offline sync queue.

When the desktop app is offline, syncs are queued to SQLite and
automatically processed when connectivity is restored.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


@dataclass
class QueuedSync:
    """A sync operation queued for offline execution."""

    id: int | None = None
    config_id: int | None = None
    config_name: str = "Default"
    sync_options: dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher = processed first
    attempts: int = 0
    max_attempts: int = 3
    status: str = "pending"  # pending, processing, completed, failed
    error_message: str | None = None
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "config_name": self.config_name,
            "sync_options": self.sync_options,
            "priority": self.priority,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class QueuedSyncModel(Base):
    """SQLAlchemy model for offline sync queue."""

    __tablename__ = "offline_queue"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_id = Column(Integer, nullable=True)
    config_name = Column(String(255), nullable=False, default="Default")
    sync_options_json = Column(Text, nullable=True)
    priority = Column(Integer, nullable=False, default=0)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    status = Column(String(50), nullable=False, default="pending")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    def to_dataclass(self) -> QueuedSync:
        """Convert model to QueuedSync dataclass."""
        sync_options = {}
        if self.sync_options_json:
            try:
                sync_options = json.loads(self.sync_options_json)
            except json.JSONDecodeError:
                pass

        return QueuedSync(
            id=self.id,
            config_id=self.config_id,
            config_name=self.config_name or "Default",
            sync_options=sync_options,
            priority=self.priority or 0,
            attempts=self.attempts or 0,
            max_attempts=self.max_attempts or 3,
            status=self.status or "pending",
            error_message=self.error_message,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    @classmethod
    def from_dataclass(cls, queued: QueuedSync) -> "QueuedSyncModel":
        """Create model from QueuedSync dataclass."""
        sync_options_json = None
        if queued.sync_options:
            sync_options_json = json.dumps(queued.sync_options)

        return cls(
            id=queued.id,
            config_id=queued.config_id,
            config_name=queued.config_name,
            sync_options_json=sync_options_json,
            priority=queued.priority,
            attempts=queued.attempts,
            max_attempts=queued.max_attempts,
            status=queued.status,
            error_message=queued.error_message,
            created_at=queued.created_at or datetime.now(timezone.utc),
            started_at=queued.started_at,
            completed_at=queued.completed_at,
        )


class OfflineQueueRepository:
    """Repository for offline sync queue operations."""

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def enqueue(self, queued: QueuedSync) -> QueuedSync:
        """Add a sync to the queue.

        Args:
            queued: QueuedSync to add.

        Returns:
            Created QueuedSync with ID.
        """
        session = self._get_session()
        try:
            model = QueuedSyncModel.from_dataclass(queued)
            session.add(model)
            session.commit()
            queued.id = model.id
            queued.created_at = model.created_at
            return queued
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_next(self) -> QueuedSync | None:
        """Get the next pending sync to process.

        Returns syncs in order of:
        1. Higher priority first
        2. Earlier created_at first (FIFO within priority)

        Returns:
            Next QueuedSync or None if queue is empty.
        """
        session = self._get_session()
        try:
            model = (
                session.query(QueuedSyncModel)
                .filter(QueuedSyncModel.status == "pending")
                .order_by(
                    QueuedSyncModel.priority.desc(),
                    QueuedSyncModel.created_at.asc(),
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_id(self, queue_id: int) -> QueuedSync | None:
        """Get a queued sync by ID.

        Args:
            queue_id: Queue entry ID.

        Returns:
            QueuedSync or None.
        """
        session = self._get_session()
        try:
            model = session.query(QueuedSyncModel).filter(
                QueuedSyncModel.id == queue_id
            ).first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def mark_processing(self, queue_id: int) -> bool:
        """Mark a queued sync as processing.

        Args:
            queue_id: Queue entry ID.

        Returns:
            True if marked, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(QueuedSyncModel).filter(
                QueuedSyncModel.id == queue_id
            ).first()
            if not model:
                return False

            model.status = "processing"
            model.started_at = datetime.now(timezone.utc)
            model.attempts = (model.attempts or 0) + 1
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def mark_completed(self, queue_id: int) -> bool:
        """Mark a queued sync as completed.

        Args:
            queue_id: Queue entry ID.

        Returns:
            True if marked, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(QueuedSyncModel).filter(
                QueuedSyncModel.id == queue_id
            ).first()
            if not model:
                return False

            model.status = "completed"
            model.completed_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def mark_failed(self, queue_id: int, error_message: str) -> bool:
        """Mark a queued sync as failed.

        If attempts < max_attempts, status returns to pending for retry.

        Args:
            queue_id: Queue entry ID.
            error_message: Error description.

        Returns:
            True if marked, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(QueuedSyncModel).filter(
                QueuedSyncModel.id == queue_id
            ).first()
            if not model:
                return False

            model.error_message = error_message
            if (model.attempts or 0) >= (model.max_attempts or 3):
                model.status = "failed"
                model.completed_at = datetime.now(timezone.utc)
            else:
                model.status = "pending"  # Will retry

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all_pending(self) -> list[QueuedSync]:
        """Get all pending syncs in priority order.

        Returns:
            List of pending QueuedSync objects.
        """
        session = self._get_session()
        try:
            models = (
                session.query(QueuedSyncModel)
                .filter(QueuedSyncModel.status == "pending")
                .order_by(
                    QueuedSyncModel.priority.desc(),
                    QueuedSyncModel.created_at.asc(),
                )
                .all()
            )
            return [m.to_dataclass() for m in models]
        finally:
            session.close()

    def count_pending(self) -> int:
        """Count pending syncs in queue.

        Returns:
            Number of pending syncs.
        """
        session = self._get_session()
        try:
            return session.query(QueuedSyncModel).filter(
                QueuedSyncModel.status == "pending"
            ).count()
        finally:
            session.close()

    def delete(self, queue_id: int) -> bool:
        """Delete a queued sync.

        Args:
            queue_id: Queue entry ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(QueuedSyncModel).filter(
                QueuedSyncModel.id == queue_id
            ).first()
            if not model:
                return False

            session.delete(model)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """Clear completed/failed syncs older than specified hours.

        Args:
            older_than_hours: Age threshold in hours.

        Returns:
            Number of entries deleted.
        """
        from datetime import timedelta

        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=older_than_hours)
            count = (
                session.query(QueuedSyncModel)
                .filter(
                    QueuedSyncModel.status.in_(["completed", "failed"]),
                    QueuedSyncModel.completed_at < cutoff,
                )
                .delete(synchronize_session=False)
            )
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance
_repository: OfflineQueueRepository | None = None


def get_offline_queue_repository(db_path: str | None = None) -> OfflineQueueRepository:
    """Get or create offline queue repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        OfflineQueueRepository instance.
    """
    global _repository
    if _repository is None:
        if db_path is None:
            # Default to data directory
            from mysql_to_sheets.core.paths import get_data_dir

            data_dir = get_data_dir()
            db_path = str(data_dir / "offline_queue.db")
        _repository = OfflineQueueRepository(db_path)
    return _repository


def reset_offline_queue_repository() -> None:
    """Reset repository singleton. For testing."""
    global _repository
    _repository = None
