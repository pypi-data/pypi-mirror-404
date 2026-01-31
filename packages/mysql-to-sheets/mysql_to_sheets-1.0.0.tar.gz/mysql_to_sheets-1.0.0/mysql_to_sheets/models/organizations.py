"""SQLAlchemy model and repository for organizations.

Organizations are the top-level entity for multi-tenant isolation.
All users, configs, webhooks, and sync history are scoped to an organization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mysql_to_sheets.core.tier import Tier, TierLimits, enforce_quota, get_tier_limits


class Base(DeclarativeBase):
    """Declarative base for organization models."""

    pass


@dataclass
class Organization:
    """Organization dataclass for business logic.

    Represents a tenant in the multi-tenant system. Each organization
    has its own users, sync configurations, and isolated data.
    """

    name: str
    slug: str
    id: int | None = None
    is_active: bool = True
    created_at: datetime | None = None
    settings: dict[str, Any] | None = None
    subscription_tier: str = "free"
    max_users: int = 5
    max_configs: int = 10
    # Billing integration fields (Phase 6)
    billing_customer_id: str | None = None  # External billing system customer ID (e.g., Stripe)
    billing_status: str = "active"  # active, past_due, canceled, trialing
    trial_ends_at: datetime | None = None
    subscription_period_end: datetime | None = None
    # Hybrid Agent fields
    agent_enabled: bool = False  # Whether hybrid agents are enabled for this org
    link_token_hash: str | None = None  # SHA256 hash of the LINK_TOKEN for tracking

    @property
    def tier(self) -> Tier:
        """Get the subscription tier as a Tier enum.

        Returns:
            Tier enum value for the organization's subscription.
        """
        try:
            return Tier(self.subscription_tier.lower())
        except ValueError:
            return Tier.FREE

    @property
    def tier_limits(self) -> TierLimits:
        """Get the resource limits for this organization's tier.

        Returns:
            TierLimits for the organization's subscription tier.
        """
        return get_tier_limits(self.tier)

    def check_config_quota(self, current_count: int) -> None:
        """Check if the organization can create another config.

        Args:
            current_count: Current number of configs.

        Raises:
            TierError: If quota is exceeded.
        """
        enforce_quota(self.tier, "configs", current_count, self.id)

    def check_user_quota(self, current_count: int) -> None:
        """Check if the organization can add another user.

        Args:
            current_count: Current number of users.

        Raises:
            TierError: If quota is exceeded.
        """
        enforce_quota(self.tier, "users", current_count, self.id)

    def check_schedule_quota(self, current_count: int) -> None:
        """Check if the organization can create another schedule.

        Args:
            current_count: Current number of schedules.

        Raises:
            TierError: If quota is exceeded.
        """
        enforce_quota(self.tier, "schedules", current_count, self.id)

    def check_webhook_quota(self, current_count: int) -> None:
        """Check if the organization can create another webhook.

        Args:
            current_count: Current number of webhooks.

        Raises:
            TierError: If quota is exceeded.
        """
        enforce_quota(self.tier, "webhooks", current_count, self.id)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the organization.
        """

        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "settings": self.settings,
            "subscription_tier": self.subscription_tier,
            "max_users": self.max_users,
            "max_configs": self.max_configs,
            "billing_customer_id": self.billing_customer_id,
            "billing_status": self.billing_status,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "subscription_period_end": (
                self.subscription_period_end.isoformat() if self.subscription_period_end else None
            ),
            "agent_enabled": self.agent_enabled,
            "link_token_hash": self.link_token_hash,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Organization":
        """Create Organization from dictionary.

        Args:
            data: Dictionary with organization data.

        Returns:
            Organization instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        trial_ends_at = data.get("trial_ends_at")
        if isinstance(trial_ends_at, str):
            trial_ends_at = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))

        subscription_period_end = data.get("subscription_period_end")
        if isinstance(subscription_period_end, str):
            subscription_period_end = datetime.fromisoformat(
                subscription_period_end.replace("Z", "+00:00")
            )

        return cls(
            id=data.get("id"),
            name=data["name"],
            slug=data["slug"],
            is_active=data.get("is_active", True),
            created_at=created_at,
            settings=data.get("settings"),
            subscription_tier=data.get("subscription_tier", "free"),
            max_users=data.get("max_users", 5),
            max_configs=data.get("max_configs", 10),
            billing_customer_id=data.get("billing_customer_id"),
            billing_status=data.get("billing_status", "active"),
            trial_ends_at=trial_ends_at,
            subscription_period_end=subscription_period_end,
            agent_enabled=data.get("agent_enabled", False),
            link_token_hash=data.get("link_token_hash"),
        )


class OrganizationModel(Base):
    """SQLAlchemy model for organizations.

    Stores organization data for multi-tenant isolation.
    """

    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    settings = Column(Text, nullable=True)  # JSON-encoded dict
    subscription_tier = Column(String(50), default="free", nullable=False)
    max_users = Column(Integer, default=5, nullable=False)
    max_configs = Column(Integer, default=10, nullable=False)
    # Billing integration fields (Phase 6)
    billing_customer_id = Column(String(255), nullable=True, index=True)
    billing_status = Column(String(50), default="active", nullable=False)
    trial_ends_at = Column(DateTime, nullable=True)
    subscription_period_end = Column(DateTime, nullable=True)
    # Hybrid Agent fields
    agent_enabled = Column(Boolean, default=False, nullable=False)
    link_token_hash = Column(String(64), nullable=True)  # SHA256 hash

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the organization.
        """
        import json

        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "settings": json.loads(str(self.settings)) if self.settings else None,
            "subscription_tier": self.subscription_tier,
            "max_users": self.max_users,
            "max_configs": self.max_configs,
            "billing_customer_id": self.billing_customer_id,
            "billing_status": self.billing_status,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "subscription_period_end": (
                self.subscription_period_end.isoformat() if self.subscription_period_end else None
            ),
            "agent_enabled": self.agent_enabled,
            "link_token_hash": self.link_token_hash,
        }

    def to_dataclass(self) -> Organization:
        """Convert model to Organization dataclass.

        Returns:
            Organization dataclass instance.
        """
        import json

        return Organization(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            slug=self.slug,  # type: ignore[arg-type]
            is_active=self.is_active,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            settings=json.loads(str(self.settings)) if self.settings else None,
            subscription_tier=self.subscription_tier,  # type: ignore[arg-type]
            max_users=self.max_users,  # type: ignore[arg-type]
            max_configs=self.max_configs,  # type: ignore[arg-type]
            billing_customer_id=self.billing_customer_id,  # type: ignore[arg-type]
            billing_status=self.billing_status,  # type: ignore[arg-type]
            trial_ends_at=self.trial_ends_at,  # type: ignore[arg-type]
            subscription_period_end=self.subscription_period_end,  # type: ignore[arg-type]
            agent_enabled=self.agent_enabled,  # type: ignore[arg-type]
            link_token_hash=self.link_token_hash,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OrganizationModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with organization data.

        Returns:
            OrganizationModel instance.
        """
        import json

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        settings = data.get("settings")
        if isinstance(settings, dict):
            settings = json.dumps(settings)

        trial_ends_at = data.get("trial_ends_at")
        if isinstance(trial_ends_at, str):
            trial_ends_at = datetime.fromisoformat(trial_ends_at.replace("Z", "+00:00"))

        subscription_period_end = data.get("subscription_period_end")
        if isinstance(subscription_period_end, str):
            subscription_period_end = datetime.fromisoformat(
                subscription_period_end.replace("Z", "+00:00")
            )

        return cls(
            name=data["name"],
            slug=data["slug"],
            is_active=data.get("is_active", True),
            created_at=created_at,
            settings=settings,
            subscription_tier=data.get("subscription_tier", "free"),
            max_users=data.get("max_users", 5),
            max_configs=data.get("max_configs", 10),
            billing_customer_id=data.get("billing_customer_id"),
            billing_status=data.get("billing_status", "active"),
            trial_ends_at=trial_ends_at,
            subscription_period_end=subscription_period_end,
            agent_enabled=data.get("agent_enabled", False),
            link_token_hash=data.get("link_token_hash"),
        )

    @classmethod
    def from_dataclass(cls, org: Organization) -> "OrganizationModel":
        """Create model from Organization dataclass.

        Args:
            org: Organization dataclass instance.

        Returns:
            OrganizationModel instance.
        """
        import json

        settings = json.dumps(org.settings) if org.settings else None

        return cls(
            id=org.id,
            name=org.name,
            slug=org.slug,
            is_active=org.is_active,
            created_at=org.created_at or datetime.now(timezone.utc),
            settings=settings,
            subscription_tier=org.subscription_tier,
            max_users=org.max_users,
            max_configs=org.max_configs,
            billing_customer_id=org.billing_customer_id,
            billing_status=org.billing_status,
            trial_ends_at=org.trial_ends_at,
            subscription_period_end=org.subscription_period_end,
            agent_enabled=org.agent_enabled,
            link_token_hash=org.link_token_hash,
        )

    def __repr__(self) -> str:
        """String representation of organization."""
        status = "active" if self.is_active else "inactive"
        return f"Organization(id={self.id}, slug='{self.slug}', status={status})"


class OrganizationRepository:
    """Repository for organization CRUD operations.

    Provides data access methods for organizations with
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

    def create(self, org: Organization) -> Organization:
        """Create a new organization.

        Args:
            org: Organization to create.

        Returns:
            Created organization with ID.

        Raises:
            ValueError: If slug already exists.
        """
        session = self._get_session()
        try:
            # Check for existing slug
            existing = (
                session.query(OrganizationModel).filter(OrganizationModel.slug == org.slug).first()
            )
            if existing:
                raise ValueError(f"Organization with slug '{org.slug}' already exists")

            model = OrganizationModel.from_dataclass(org)
            session.add(model)
            session.commit()
            org.id = model.id  # type: ignore[assignment]
            org.created_at = model.created_at  # type: ignore[assignment]
            return org
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, org_id: int) -> Organization | None:
        """Get organization by ID.

        Args:
            org_id: Organization ID.

        Returns:
            Organization if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = session.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_slug(self, slug: str) -> Organization | None:
        """Get organization by slug.

        Args:
            slug: Organization slug (URL-safe identifier).

        Returns:
            Organization if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = session.query(OrganizationModel).filter(OrganizationModel.slug == slug).first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        include_inactive: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Organization]:
        """Get all organizations.

        Args:
            include_inactive: Whether to include inactive organizations.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of organizations.
        """
        session = self._get_session()
        try:
            query = session.query(OrganizationModel).order_by(OrganizationModel.created_at.desc())

            if not include_inactive:
                query = query.filter(OrganizationModel.is_active == True)

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, org: Organization) -> Organization:
        """Update an organization.

        Args:
            org: Organization with updated fields.

        Returns:
            Updated organization.

        Raises:
            ValueError: If organization not found or slug conflict.
        """
        if org.id is None:
            raise ValueError("Organization ID is required for update")

        session = self._get_session()
        try:
            model = session.query(OrganizationModel).filter(OrganizationModel.id == org.id).first()
            if not model:
                raise ValueError(f"Organization with ID {org.id} not found")

            # Check for slug conflict if slug changed
            if model.slug != org.slug:
                existing = (
                    session.query(OrganizationModel)
                    .filter(
                        OrganizationModel.slug == org.slug,
                        OrganizationModel.id != org.id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(f"Organization with slug '{org.slug}' already exists")

            import json

            model.name = org.name  # type: ignore[assignment]
            model.slug = org.slug  # type: ignore[assignment]
            model.is_active = org.is_active  # type: ignore[assignment]
            model.settings = json.dumps(org.settings) if org.settings else None  # type: ignore[assignment]
            model.subscription_tier = org.subscription_tier  # type: ignore[assignment]
            model.max_users = org.max_users  # type: ignore[assignment]
            model.max_configs = org.max_configs  # type: ignore[assignment]
            model.billing_customer_id = org.billing_customer_id  # type: ignore[assignment]
            model.billing_status = org.billing_status  # type: ignore[assignment]
            model.trial_ends_at = org.trial_ends_at  # type: ignore[assignment]
            model.subscription_period_end = org.subscription_period_end  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, org_id: int) -> bool:
        """Delete an organization.

        Args:
            org_id: Organization ID.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
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

    def deactivate(self, org_id: int) -> bool:
        """Deactivate an organization (soft delete).

        Args:
            org_id: Organization ID.

        Returns:
            True if deactivated, False if not found.
        """
        session = self._get_session()
        try:
            model = session.query(OrganizationModel).filter(OrganizationModel.id == org_id).first()
            if not model:
                return False

            model.is_active = False  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self, include_inactive: bool = False) -> int:
        """Count organizations.

        Args:
            include_inactive: Whether to include inactive organizations.

        Returns:
            Number of organizations.
        """
        session = self._get_session()
        try:
            query = session.query(OrganizationModel)
            if not include_inactive:
                query = query.filter(OrganizationModel.is_active == True)
            return query.count()
        finally:
            session.close()


# Singleton instance
_organization_repository: OrganizationRepository | None = None


def get_organization_repository(db_path: str | None = None) -> OrganizationRepository:
    """Get or create organization repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        OrganizationRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _organization_repository
    if _organization_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _organization_repository = OrganizationRepository(db_path)
    return _organization_repository


def reset_organization_repository() -> None:
    """Reset organization repository singleton. For testing."""
    global _organization_repository
    _organization_repository = None
