"""SQLAlchemy model and repository for PII policies.

PII policies define organization-level settings for PII detection
and handling during sync operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for PII policy models."""

    pass


@dataclass
class PIIPolicy:
    """PII policy dataclass for business logic.

    Represents organization-level PII detection and transformation settings.
    """

    organization_id: int
    id: int | None = None
    auto_detect_enabled: bool = True
    default_transforms: dict[str, str] = field(default_factory=dict)
    require_acknowledgment: bool = True
    block_unacknowledged: bool = False  # ENTERPRISE only
    confidence_threshold: float = 0.7
    sample_size: int = 100
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the policy.
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "auto_detect_enabled": self.auto_detect_enabled,
            "default_transforms": self.default_transforms,
            "require_acknowledgment": self.require_acknowledgment,
            "block_unacknowledged": self.block_unacknowledged,
            "confidence_threshold": self.confidence_threshold,
            "sample_size": self.sample_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PIIPolicy":
        """Create PIIPolicy from dictionary.

        Args:
            data: Dictionary with policy data.

        Returns:
            PIIPolicy instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            organization_id=data["organization_id"],
            auto_detect_enabled=data.get("auto_detect_enabled", True),
            default_transforms=data.get("default_transforms", {}),
            require_acknowledgment=data.get("require_acknowledgment", True),
            block_unacknowledged=data.get("block_unacknowledged", False),
            confidence_threshold=data.get("confidence_threshold", 0.7),
            sample_size=data.get("sample_size", 100),
            created_at=created_at,
            updated_at=updated_at,
        )


class PIIPolicyModel(Base):
    """SQLAlchemy model for PII policies.

    Stores organization-level PII detection and transformation settings.
    """

    __tablename__ = "pii_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, unique=True, index=True)
    auto_detect_enabled = Column(Boolean, default=True, nullable=False)
    default_transforms = Column(Text, nullable=True)  # JSON-encoded dict
    require_acknowledgment = Column(Boolean, default=True, nullable=False)
    block_unacknowledged = Column(Boolean, default=False, nullable=False)
    confidence_threshold = Column(String(10), default="0.7", nullable=False)
    sample_size = Column(Integer, default=100, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the policy.
        """
        import json

        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "auto_detect_enabled": self.auto_detect_enabled,
            "default_transforms": (
                json.loads(str(self.default_transforms)) if self.default_transforms else {}
            ),
            "require_acknowledgment": self.require_acknowledgment,
            "block_unacknowledged": self.block_unacknowledged,
            "confidence_threshold": float(self.confidence_threshold or "0.7"),
            "sample_size": self.sample_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dataclass(self) -> PIIPolicy:
        """Convert model to PIIPolicy dataclass.

        Returns:
            PIIPolicy dataclass instance.
        """
        import json

        return PIIPolicy(
            id=self.id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            auto_detect_enabled=self.auto_detect_enabled,  # type: ignore[arg-type]
            default_transforms=(
                json.loads(str(self.default_transforms)) if self.default_transforms else {}
            ),
            require_acknowledgment=self.require_acknowledgment,  # type: ignore[arg-type]
            block_unacknowledged=self.block_unacknowledged,  # type: ignore[arg-type]
            confidence_threshold=float(self.confidence_threshold or "0.7"),
            sample_size=self.sample_size,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, policy: PIIPolicy) -> "PIIPolicyModel":
        """Create model from PIIPolicy dataclass.

        Args:
            policy: PIIPolicy dataclass instance.

        Returns:
            PIIPolicyModel instance.
        """
        import json

        return cls(
            id=policy.id,
            organization_id=policy.organization_id,
            auto_detect_enabled=policy.auto_detect_enabled,
            default_transforms=(
                json.dumps(policy.default_transforms) if policy.default_transforms else None
            ),
            require_acknowledgment=policy.require_acknowledgment,
            block_unacknowledged=policy.block_unacknowledged,
            confidence_threshold=str(policy.confidence_threshold),
            sample_size=policy.sample_size,
            created_at=policy.created_at or datetime.now(timezone.utc),
            updated_at=policy.updated_at,
        )

    def __repr__(self) -> str:
        """String representation of policy."""
        return f"PIIPolicyModel(id={self.id}, org={self.organization_id})"


class PIIPolicyRepository:
    """Repository for PII policy CRUD operations.

    Provides data access methods for PII policies with SQLite persistence.
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

    def create(self, policy: PIIPolicy) -> PIIPolicy:
        """Create a new PII policy.

        Args:
            policy: Policy to create.

        Returns:
            Created policy with ID.

        Raises:
            ValueError: If policy already exists for organization.
        """
        session = self._get_session()
        try:
            # Check for existing policy
            existing = (
                session.query(PIIPolicyModel)
                .filter(PIIPolicyModel.organization_id == policy.organization_id)
                .first()
            )
            if existing:
                raise ValueError(
                    f"PII policy already exists for organization {policy.organization_id}"
                )

            model = PIIPolicyModel.from_dataclass(policy)
            session.add(model)
            session.commit()
            policy.id = model.id  # type: ignore[assignment]
            policy.created_at = model.created_at  # type: ignore[assignment]
            return policy
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, policy_id: int) -> PIIPolicy | None:
        """Get policy by ID.

        Args:
            policy_id: Policy ID.

        Returns:
            Policy if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIPolicyModel).filter(PIIPolicyModel.id == policy_id).first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_organization(self, organization_id: int) -> PIIPolicy | None:
        """Get policy by organization ID.

        Args:
            organization_id: Organization ID.

        Returns:
            Policy if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIPolicyModel)
                .filter(PIIPolicyModel.organization_id == organization_id)
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def update(self, policy: PIIPolicy) -> PIIPolicy:
        """Update a PII policy.

        Args:
            policy: Policy with updated fields.

        Returns:
            Updated policy.

        Raises:
            ValueError: If policy not found.
        """
        if policy.id is None:
            raise ValueError("Policy ID is required for update")

        session = self._get_session()
        try:
            import json

            model = (
                session.query(PIIPolicyModel).filter(PIIPolicyModel.id == policy.id).first()
            )
            if not model:
                raise ValueError(f"Policy with ID {policy.id} not found")

            model.auto_detect_enabled = policy.auto_detect_enabled  # type: ignore[assignment]
            model.default_transforms = (  # type: ignore[assignment]
                json.dumps(policy.default_transforms) if policy.default_transforms else None
            )
            model.require_acknowledgment = policy.require_acknowledgment  # type: ignore[assignment]
            model.block_unacknowledged = policy.block_unacknowledged  # type: ignore[assignment]
            model.confidence_threshold = str(policy.confidence_threshold)  # type: ignore[assignment]
            model.sample_size = policy.sample_size  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, policy_id: int) -> bool:
        """Delete a PII policy.

        Args:
            policy_id: Policy ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(PIIPolicyModel).filter(PIIPolicyModel.id == policy_id).first()
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


# Singleton instance
_pii_policy_repository: PIIPolicyRepository | None = None


def get_pii_policy_repository(db_path: str | None = None) -> PIIPolicyRepository:
    """Get or create PII policy repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        PIIPolicyRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _pii_policy_repository
    if _pii_policy_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _pii_policy_repository = PIIPolicyRepository(db_path)
    return _pii_policy_repository


def reset_pii_policy_repository() -> None:
    """Reset PII policy repository singleton. For testing."""
    global _pii_policy_repository
    _pii_policy_repository = None
