"""SQLAlchemy model and repository for PII acknowledgments.

PII acknowledgments record when users have reviewed and approved
syncing columns that contain personally identifiable information.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for PII acknowledgment models."""

    pass


@dataclass
class PIIAcknowledgment:
    """PII acknowledgment dataclass for business logic.

    Records that a user has reviewed and approved a PII column
    for syncing with a specific transformation applied.
    """

    sync_config_id: int
    column_name: str
    category: str  # email, phone, ssn, etc.
    transform: str  # none, hash, redact, partial_mask
    acknowledged_by_user_id: int
    id: int | None = None
    acknowledged_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the acknowledgment.
        """
        return {
            "id": self.id,
            "sync_config_id": self.sync_config_id,
            "column_name": self.column_name,
            "category": self.category,
            "transform": self.transform,
            "acknowledged_by_user_id": self.acknowledged_by_user_id,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PIIAcknowledgment":
        """Create PIIAcknowledgment from dictionary.

        Args:
            data: Dictionary with acknowledgment data.

        Returns:
            PIIAcknowledgment instance.
        """
        acknowledged_at = data.get("acknowledged_at")
        if isinstance(acknowledged_at, str):
            acknowledged_at = datetime.fromisoformat(acknowledged_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            sync_config_id=data["sync_config_id"],
            column_name=data["column_name"],
            category=data["category"],
            transform=data["transform"],
            acknowledged_by_user_id=data["acknowledged_by_user_id"],
            acknowledged_at=acknowledged_at,
        )


class PIIAcknowledgmentModel(Base):
    """SQLAlchemy model for PII acknowledgments.

    Stores records of user acknowledgments for PII columns.
    """

    __tablename__ = "pii_acknowledgments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_config_id = Column(Integer, nullable=False, index=True)
    column_name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # email, phone, ssn, etc.
    transform = Column(String(50), nullable=False)  # none, hash, redact, partial_mask
    acknowledged_by_user_id = Column(Integer, nullable=False, index=True)
    acknowledged_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the acknowledgment.
        """
        return {
            "id": self.id,
            "sync_config_id": self.sync_config_id,
            "column_name": self.column_name,
            "category": self.category,
            "transform": self.transform,
            "acknowledged_by_user_id": self.acknowledged_by_user_id,
            "acknowledged_at": (
                self.acknowledged_at.isoformat() if self.acknowledged_at else None
            ),
        }

    def to_dataclass(self) -> PIIAcknowledgment:
        """Convert model to PIIAcknowledgment dataclass.

        Returns:
            PIIAcknowledgment dataclass instance.
        """
        return PIIAcknowledgment(
            id=self.id,  # type: ignore[arg-type]
            sync_config_id=self.sync_config_id,  # type: ignore[arg-type]
            column_name=self.column_name,  # type: ignore[arg-type]
            category=self.category,  # type: ignore[arg-type]
            transform=self.transform,  # type: ignore[arg-type]
            acknowledged_by_user_id=self.acknowledged_by_user_id,  # type: ignore[arg-type]
            acknowledged_at=self.acknowledged_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, ack: PIIAcknowledgment) -> "PIIAcknowledgmentModel":
        """Create model from PIIAcknowledgment dataclass.

        Args:
            ack: PIIAcknowledgment dataclass instance.

        Returns:
            PIIAcknowledgmentModel instance.
        """
        return cls(
            id=ack.id,
            sync_config_id=ack.sync_config_id,
            column_name=ack.column_name,
            category=ack.category,
            transform=ack.transform,
            acknowledged_by_user_id=ack.acknowledged_by_user_id,
            acknowledged_at=ack.acknowledged_at or datetime.now(timezone.utc),
        )

    def __repr__(self) -> str:
        """String representation of acknowledgment."""
        return (
            f"PIIAcknowledgmentModel(id={self.id}, config={self.sync_config_id}, "
            f"column='{self.column_name}')"
        )


class PIIAcknowledgmentRepository:
    """Repository for PII acknowledgment CRUD operations.

    Provides data access methods for PII acknowledgments with SQLite persistence.
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

    def create(self, ack: PIIAcknowledgment) -> PIIAcknowledgment:
        """Create a new PII acknowledgment.

        If an acknowledgment already exists for the same config+column,
        it will be updated instead.

        Args:
            ack: Acknowledgment to create.

        Returns:
            Created or updated acknowledgment with ID.
        """
        session = self._get_session()
        try:
            # Check for existing acknowledgment (upsert behavior)
            existing = (
                session.query(PIIAcknowledgmentModel)
                .filter(
                    PIIAcknowledgmentModel.sync_config_id == ack.sync_config_id,
                    PIIAcknowledgmentModel.column_name == ack.column_name,
                )
                .first()
            )

            if existing:
                # Update existing acknowledgment
                existing.category = ack.category  # type: ignore[assignment]
                existing.transform = ack.transform  # type: ignore[assignment]
                existing.acknowledged_by_user_id = ack.acknowledged_by_user_id  # type: ignore[assignment]
                existing.acknowledged_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                session.commit()
                return existing.to_dataclass()

            model = PIIAcknowledgmentModel.from_dataclass(ack)
            session.add(model)
            session.commit()
            ack.id = model.id  # type: ignore[assignment]
            ack.acknowledged_at = model.acknowledged_at  # type: ignore[assignment]
            return ack
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, ack_id: int) -> PIIAcknowledgment | None:
        """Get acknowledgment by ID.

        Args:
            ack_id: Acknowledgment ID.

        Returns:
            Acknowledgment if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.id == ack_id)
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_config(self, sync_config_id: int) -> list[PIIAcknowledgment]:
        """Get all acknowledgments for a sync config.

        Args:
            sync_config_id: Sync configuration ID.

        Returns:
            List of acknowledgments for the config.
        """
        session = self._get_session()
        try:
            models = (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.sync_config_id == sync_config_id)
                .order_by(PIIAcknowledgmentModel.column_name)
                .all()
            )
            return [model.to_dataclass() for model in models]
        finally:
            session.close()

    def get_by_config_and_column(
        self, sync_config_id: int, column_name: str
    ) -> PIIAcknowledgment | None:
        """Get acknowledgment for a specific column in a config.

        Args:
            sync_config_id: Sync configuration ID.
            column_name: Column name.

        Returns:
            Acknowledgment if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIAcknowledgmentModel)
                .filter(
                    PIIAcknowledgmentModel.sync_config_id == sync_config_id,
                    PIIAcknowledgmentModel.column_name == column_name,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> list[PIIAcknowledgment]:
        """Get all acknowledgments made by a user.

        Args:
            user_id: User ID.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of acknowledgments by the user.
        """
        session = self._get_session()
        try:
            query = (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.acknowledged_by_user_id == user_id)
                .order_by(PIIAcknowledgmentModel.acknowledged_at.desc())
            )

            if offset > 0:
                query = query.offset(offset)
            query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def delete(self, ack_id: int) -> bool:
        """Delete an acknowledgment.

        Args:
            ack_id: Acknowledgment ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.id == ack_id)
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

    def delete_by_config(self, sync_config_id: int) -> int:
        """Delete all acknowledgments for a sync config.

        Args:
            sync_config_id: Sync configuration ID.

        Returns:
            Number of acknowledgments deleted.
        """
        session = self._get_session()
        try:
            count = (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.sync_config_id == sync_config_id)
                .delete()
            )
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def is_acknowledged(self, sync_config_id: int, column_name: str) -> bool:
        """Check if a column is acknowledged for a config.

        Args:
            sync_config_id: Sync configuration ID.
            column_name: Column name.

        Returns:
            True if acknowledged, False otherwise.
        """
        return self.get_by_config_and_column(sync_config_id, column_name) is not None

    def get_acknowledged_columns(self, sync_config_id: int) -> set[str]:
        """Get set of acknowledged column names for a config.

        Args:
            sync_config_id: Sync configuration ID.

        Returns:
            Set of acknowledged column names.
        """
        acks = self.get_by_config(sync_config_id)
        return {ack.column_name for ack in acks}

    def count_by_config(self, sync_config_id: int) -> int:
        """Count acknowledgments for a sync config.

        Args:
            sync_config_id: Sync configuration ID.

        Returns:
            Number of acknowledgments.
        """
        session = self._get_session()
        try:
            return (
                session.query(PIIAcknowledgmentModel)
                .filter(PIIAcknowledgmentModel.sync_config_id == sync_config_id)
                .count()
            )
        finally:
            session.close()


# Singleton instance
_pii_acknowledgment_repository: PIIAcknowledgmentRepository | None = None


def get_pii_acknowledgment_repository(db_path: str | None = None) -> PIIAcknowledgmentRepository:
    """Get or create PII acknowledgment repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        PIIAcknowledgmentRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _pii_acknowledgment_repository
    if _pii_acknowledgment_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _pii_acknowledgment_repository = PIIAcknowledgmentRepository(db_path)
    return _pii_acknowledgment_repository


def reset_pii_acknowledgment_repository() -> None:
    """Reset PII acknowledgment repository singleton. For testing."""
    global _pii_acknowledgment_repository
    _pii_acknowledgment_repository = None
