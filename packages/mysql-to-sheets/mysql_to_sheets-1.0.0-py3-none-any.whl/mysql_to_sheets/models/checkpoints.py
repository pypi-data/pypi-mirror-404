"""SQLAlchemy model and repository for streaming checkpoints.

Checkpoints enable resumable streaming syncs by preserving state
when a large sync fails partway through. The staging worksheet is
preserved and the sync can be resumed from the last successful chunk.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    pass


@dataclass
class StreamingCheckpoint:
    """Checkpoint state for resumable streaming syncs.

    Stores the state needed to resume a failed streaming sync from
    the last successful chunk rather than starting over.

    Attributes:
        job_id: Associated job ID (unique constraint).
        config_id: Sync configuration ID for lookup.
        staging_worksheet_name: Name of the staging worksheet.
        staging_worksheet_gid: GID of the staging worksheet for lookup by ID.
        chunks_completed: Number of chunks successfully written to staging.
        rows_pushed: Total rows written to staging worksheet.
        headers: Column headers from the query (JSON encoded in DB).
        created_at: When the checkpoint was first created.
        updated_at: When the checkpoint was last updated.
        id: Database primary key.
    """

    job_id: int
    config_id: int
    staging_worksheet_name: str
    staging_worksheet_gid: int
    chunks_completed: int = 0
    rows_pushed: int = 0
    headers: list[str] = field(default_factory=list)
    created_at: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the checkpoint.
        """
        return {
            "id": self.id,
            "job_id": self.job_id,
            "config_id": self.config_id,
            "staging_worksheet_name": self.staging_worksheet_name,
            "staging_worksheet_gid": self.staging_worksheet_gid,
            "chunks_completed": self.chunks_completed,
            "rows_pushed": self.rows_pushed,
            "headers": self.headers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StreamingCheckpoint":
        """Create checkpoint from dictionary.

        Args:
            data: Dictionary with checkpoint data.

        Returns:
            StreamingCheckpoint instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        headers = data.get("headers", [])
        if isinstance(headers, str):
            headers = json.loads(headers)

        return cls(
            id=data.get("id"),
            job_id=data["job_id"],
            config_id=data["config_id"],
            staging_worksheet_name=data["staging_worksheet_name"],
            staging_worksheet_gid=data["staging_worksheet_gid"],
            chunks_completed=data.get("chunks_completed", 0),
            rows_pushed=data.get("rows_pushed", 0),
            headers=headers,
            created_at=created_at,
            updated_at=updated_at,
        )


class StreamingCheckpointModel(Base):
    """SQLAlchemy model for streaming checkpoints.

    Stores checkpoint state for resumable streaming syncs.
    """

    __tablename__ = "streaming_checkpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, nullable=False, unique=True, index=True)
    config_id = Column(Integer, nullable=False, index=True)
    staging_worksheet_name = Column(String(100), nullable=False)
    staging_worksheet_gid = Column(Integer, nullable=False)
    chunks_completed = Column(Integer, nullable=False, default=0)
    rows_pushed = Column(Integer, nullable=False, default=0)
    headers_json = Column(Text, nullable=True)  # JSON-encoded list
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def to_dataclass(self) -> StreamingCheckpoint:
        """Convert model to StreamingCheckpoint dataclass.

        Returns:
            StreamingCheckpoint instance.
        """
        headers = []
        if self.headers_json:
            try:
                headers = json.loads(self.headers_json)  # type: ignore[arg-type]
            except (json.JSONDecodeError, TypeError):
                headers = []

        return StreamingCheckpoint(
            id=self.id,  # type: ignore[arg-type]
            job_id=self.job_id,  # type: ignore[arg-type]
            config_id=self.config_id,  # type: ignore[arg-type]
            staging_worksheet_name=self.staging_worksheet_name,  # type: ignore[arg-type]
            staging_worksheet_gid=self.staging_worksheet_gid,  # type: ignore[arg-type]
            chunks_completed=self.chunks_completed,  # type: ignore[arg-type]
            rows_pushed=self.rows_pushed,  # type: ignore[arg-type]
            headers=headers,
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, checkpoint: StreamingCheckpoint) -> "StreamingCheckpointModel":
        """Create model from StreamingCheckpoint dataclass.

        Args:
            checkpoint: StreamingCheckpoint instance.

        Returns:
            StreamingCheckpointModel instance.
        """
        return cls(
            id=checkpoint.id,
            job_id=checkpoint.job_id,
            config_id=checkpoint.config_id,
            staging_worksheet_name=checkpoint.staging_worksheet_name,
            staging_worksheet_gid=checkpoint.staging_worksheet_gid,
            chunks_completed=checkpoint.chunks_completed,
            rows_pushed=checkpoint.rows_pushed,
            headers_json=json.dumps(checkpoint.headers) if checkpoint.headers else None,
            created_at=checkpoint.created_at or datetime.now(timezone.utc),
            updated_at=checkpoint.updated_at or datetime.now(timezone.utc),
        )

    def __repr__(self) -> str:
        """String representation of checkpoint."""
        return (
            f"StreamingCheckpoint(id={self.id}, job_id={self.job_id}, "
            f"chunks={self.chunks_completed}, rows={self.rows_pushed})"
        )


class CheckpointRepository:
    """Repository for checkpoint CRUD operations.

    Provides data access methods for streaming checkpoints with SQLite persistence.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path

    def _get_session(self) -> Any:
        """Get a new database session."""
        return self._session_factory()

    def save_checkpoint(self, checkpoint: StreamingCheckpoint) -> StreamingCheckpoint:
        """Upsert checkpoint state.

        Creates a new checkpoint or updates existing one based on job_id.

        Args:
            checkpoint: Checkpoint to save.

        Returns:
            Saved checkpoint with ID.
        """
        session = self._get_session()
        try:
            # Check if checkpoint exists for this job
            existing = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.job_id == checkpoint.job_id)
                .first()
            )

            if existing:
                # Update existing checkpoint
                existing.config_id = checkpoint.config_id
                existing.staging_worksheet_name = checkpoint.staging_worksheet_name
                existing.staging_worksheet_gid = checkpoint.staging_worksheet_gid
                existing.chunks_completed = checkpoint.chunks_completed
                existing.rows_pushed = checkpoint.rows_pushed
                existing.headers_json = json.dumps(checkpoint.headers) if checkpoint.headers else None
                existing.updated_at = datetime.now(timezone.utc)
                session.commit()
                return existing.to_dataclass()
            else:
                # Create new checkpoint
                model = StreamingCheckpointModel.from_dataclass(checkpoint)
                session.add(model)
                session.commit()
                return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_checkpoint(self, job_id: int) -> StreamingCheckpoint | None:
        """Load checkpoint for a job.

        Args:
            job_id: Job ID to look up.

        Returns:
            Checkpoint if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.job_id == job_id)
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_checkpoint_by_config(self, config_id: int) -> StreamingCheckpoint | None:
        """Load most recent checkpoint for a config.

        Useful for finding resumable syncs by config rather than job.

        Args:
            config_id: Sync config ID to look up.

        Returns:
            Most recent checkpoint if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.config_id == config_id)
                .order_by(StreamingCheckpointModel.updated_at.desc())
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def delete_checkpoint(self, job_id: int) -> bool:
        """Remove checkpoint on completion.

        Args:
            job_id: Job ID whose checkpoint to delete.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.job_id == job_id)
                .first()
            )
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

    def get_stale_checkpoints(self, max_age_hours: int = 24) -> list[StreamingCheckpoint]:
        """Find abandoned checkpoints for cleanup.

        Checkpoints older than max_age_hours are considered stale and
        can be cleaned up along with their staging worksheets.

        Args:
            max_age_hours: Maximum age in hours before considered stale.

        Returns:
            List of stale checkpoints.
        """
        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            models = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.updated_at < cutoff)
                .all()
            )
            return [m.to_dataclass() for m in models]
        finally:
            session.close()

    def cleanup_stale(self, max_age_hours: int = 24) -> int:
        """Delete stale checkpoints.

        Args:
            max_age_hours: Maximum age in hours before deletion.

        Returns:
            Number of checkpoints deleted.
        """
        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
            deleted = (
                session.query(StreamingCheckpointModel)
                .filter(StreamingCheckpointModel.updated_at < cutoff)
                .delete(synchronize_session=False)
            )
            session.commit()
            return deleted  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self) -> int:
        """Count total checkpoints.

        Returns:
            Number of checkpoints in database.
        """
        session = self._get_session()
        try:
            return session.query(StreamingCheckpointModel).count()  # type: ignore[no-any-return]
        finally:
            session.close()


# Singleton instance
_checkpoint_repository: CheckpointRepository | None = None


def get_checkpoint_repository(db_path: str | None = None) -> CheckpointRepository:
    """Get or create checkpoint repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        CheckpointRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _checkpoint_repository
    if _checkpoint_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _checkpoint_repository = CheckpointRepository(db_path)
    return _checkpoint_repository


def reset_checkpoint_repository() -> None:
    """Reset checkpoint repository singleton. For testing."""
    global _checkpoint_repository
    _checkpoint_repository = None
