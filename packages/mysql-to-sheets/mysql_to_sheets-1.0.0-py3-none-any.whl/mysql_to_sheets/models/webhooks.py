"""SQLAlchemy models for webhook subscriptions and deliveries.

Webhooks allow users to receive HTTP callbacks when events occur
in the system (sync completed, sync failed, config changed, etc.).
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import Session, sessionmaker

# Import Base from organizations to share metadata with foreign key targets
from mysql_to_sheets.models.organizations import Base
from mysql_to_sheets.models.repository import validate_tenant


class WebhookEventType(str, Enum):
    """Types of events that can trigger webhooks."""

    # Sync events
    SYNC_STARTED = "sync.started"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"

    # Config events
    CONFIG_CREATED = "config.created"
    CONFIG_UPDATED = "config.updated"
    CONFIG_DELETED = "config.deleted"

    # Schedule events
    SCHEDULE_TRIGGERED = "schedule.triggered"

    # User events (optional, for audit purposes)
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"


# All valid event types as strings for validation
VALID_EVENT_TYPES = [e.value for e in WebhookEventType]


@dataclass
class WebhookSubscription:
    """Webhook subscription dataclass.

    Defines a webhook endpoint and the events it should receive.
    """

    name: str
    url: str
    secret: str
    events: list[str]
    organization_id: int
    id: int | None = None
    is_active: bool = True
    created_by_user_id: int | None = None
    headers: dict[str, str] | None = None
    retry_count: int = 3
    created_at: datetime | None = None
    last_triggered_at: datetime | None = None
    failure_count: int = 0

    def to_dict(self, include_secret: bool = False) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Args:
            include_secret: Whether to include the secret.

        Returns:
            Dictionary representation.
        """
        result = {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "events": self.events,
            "is_active": self.is_active,
            "created_by_user_id": self.created_by_user_id,
            "headers": self.headers,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered_at": self.last_triggered_at.isoformat()
            if self.last_triggered_at
            else None,
            "failure_count": self.failure_count,
            "organization_id": self.organization_id,
        }
        if include_secret:
            result["secret"] = self.secret
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebhookSubscription":
        """Create WebhookSubscription from dictionary.

        Args:
            data: Dictionary with subscription data.

        Returns:
            WebhookSubscription instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        last_triggered_at = data.get("last_triggered_at")
        if isinstance(last_triggered_at, str):
            last_triggered_at = datetime.fromisoformat(last_triggered_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            name=data["name"],
            url=data["url"],
            secret=data.get("secret", ""),
            events=data.get("events", []),
            is_active=data.get("is_active", True),
            created_by_user_id=data.get("created_by_user_id"),
            headers=data.get("headers"),
            retry_count=data.get("retry_count", 3),
            created_at=created_at,
            last_triggered_at=last_triggered_at,
            failure_count=data.get("failure_count", 0),
            organization_id=data["organization_id"],
        )

    def validate(self) -> list[str]:
        """Validate the subscription.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.name:
            errors.append("Name is required")
        if not self.url:
            errors.append("URL is required")
        if not self.url.startswith(("http://", "https://")):
            errors.append("URL must start with http:// or https://")
        if not self.events:
            errors.append("At least one event type is required")

        for event in self.events:
            if event not in VALID_EVENT_TYPES:
                errors.append(f"Invalid event type: {event}")

        if self.retry_count < 0 or self.retry_count > 10:
            errors.append("retry_count must be between 0 and 10")

        return errors


class WebhookSubscriptionModel(Base):
    """SQLAlchemy model for webhook subscriptions."""

    __tablename__ = "webhook_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    url = Column(String(2048), nullable=False)
    secret = Column(String(255), nullable=False)
    events = Column(Text, nullable=False)  # JSON-encoded list
    is_active = Column(Boolean, default=True, nullable=False)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=False, index=True)
    headers = Column(Text, nullable=True)  # JSON-encoded dict
    retry_count = Column(Integer, default=3, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_triggered_at = Column(DateTime, nullable=True)
    failure_count = Column(Integer, default=0, nullable=False)

    def to_dict(self, include_secret: bool = False) -> dict[str, Any]:
        """Convert model to dictionary."""
        import json

        result = {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "events": json.loads(self.events) if self.events else [],  # type: ignore[arg-type]
            "is_active": self.is_active,
            "created_by_user_id": self.created_by_user_id,
            "headers": json.loads(self.headers) if self.headers else None,  # type: ignore[arg-type]
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_triggered_at": self.last_triggered_at.isoformat()
            if self.last_triggered_at
            else None,
            "failure_count": self.failure_count,
            "organization_id": self.organization_id,
        }
        if include_secret:
            result["secret"] = self.secret
        return result

    def to_dataclass(self) -> WebhookSubscription:
        """Convert model to WebhookSubscription dataclass."""
        import json

        return WebhookSubscription(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            url=self.url,  # type: ignore[arg-type]
            secret=self.secret,  # type: ignore[arg-type]
            events=json.loads(self.events) if self.events else [],  # type: ignore[arg-type]
            is_active=self.is_active,  # type: ignore[arg-type]
            created_by_user_id=self.created_by_user_id,  # type: ignore[arg-type]
            headers=json.loads(self.headers) if self.headers else None,  # type: ignore[arg-type]
            retry_count=self.retry_count,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            last_triggered_at=self.last_triggered_at,  # type: ignore[arg-type]
            failure_count=self.failure_count,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, sub: WebhookSubscription) -> "WebhookSubscriptionModel":
        """Create model from WebhookSubscription dataclass."""
        import json

        return cls(
            id=sub.id,
            name=sub.name,
            url=sub.url,
            secret=sub.secret,
            events=json.dumps(sub.events),
            is_active=sub.is_active,
            created_by_user_id=sub.created_by_user_id,
            organization_id=sub.organization_id,
            headers=json.dumps(sub.headers) if sub.headers else None,
            retry_count=sub.retry_count,
            created_at=sub.created_at or datetime.now(timezone.utc),
            last_triggered_at=sub.last_triggered_at,
            failure_count=sub.failure_count,
        )

    def __repr__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return f"WebhookSubscription(id={self.id}, name='{self.name}', status={status})"


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt record.

    Tracks each attempt to deliver a webhook payload.
    """

    subscription_id: int
    delivery_id: str
    event: str
    payload: dict[str, Any]
    id: int | None = None
    status: str = "pending"  # pending, success, failed
    response_code: int | None = None
    response_body: str | None = None
    attempt_count: int = 1
    created_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "delivery_id": self.delivery_id,
            "event": self.event,
            "payload": self.payload,
            "status": self.status,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


class WebhookDeliveryModel(Base):
    """SQLAlchemy model for webhook delivery logs."""

    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    subscription_id = Column(
        Integer, ForeignKey("webhook_subscriptions.id"), nullable=False, index=True
    )
    delivery_id = Column(String(50), unique=True, nullable=False, index=True)
    event = Column(String(50), nullable=False)
    payload = Column(Text, nullable=False)  # JSON-encoded dict
    status = Column(String(20), default="pending", nullable=False)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)  # First 1KB
    attempt_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        import json

        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "delivery_id": self.delivery_id,
            "event": self.event,
            "payload": json.loads(self.payload) if self.payload else {},  # type: ignore[arg-type]
            "status": self.status,
            "response_code": self.response_code,
            "response_body": self.response_body,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }

    def to_dataclass(self) -> WebhookDelivery:
        """Convert model to WebhookDelivery dataclass."""
        import json

        return WebhookDelivery(
            id=self.id,  # type: ignore[arg-type]
            subscription_id=self.subscription_id,  # type: ignore[arg-type]
            delivery_id=self.delivery_id,  # type: ignore[arg-type]
            event=self.event,  # type: ignore[arg-type]
            payload=json.loads(self.payload) if self.payload else {},  # type: ignore[arg-type]
            status=self.status,  # type: ignore[arg-type]
            response_code=self.response_code,  # type: ignore[arg-type]
            response_body=self.response_body,  # type: ignore[arg-type]
            attempt_count=self.attempt_count,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            completed_at=self.completed_at,  # type: ignore[arg-type]
            error_message=self.error_message,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, delivery: WebhookDelivery) -> "WebhookDeliveryModel":
        """Create model from WebhookDelivery dataclass."""
        import json

        return cls(
            id=delivery.id,
            subscription_id=delivery.subscription_id,
            delivery_id=delivery.delivery_id,
            event=delivery.event,
            payload=json.dumps(delivery.payload),
            status=delivery.status,
            response_code=delivery.response_code,
            response_body=delivery.response_body,
            attempt_count=delivery.attempt_count,
            created_at=delivery.created_at or datetime.now(timezone.utc),
            completed_at=delivery.completed_at,
            error_message=delivery.error_message,
        )


class WebhookRepository:
    """Repository for webhook CRUD operations.

    Manages webhook subscriptions and delivery logs with
    SQLite persistence. All queries scoped to organization.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path."""
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    # Subscription methods

    def create_subscription(self, sub: WebhookSubscription) -> WebhookSubscription:
        """Create a new webhook subscription."""
        sub.organization_id = validate_tenant(sub.organization_id)  # type: ignore[assignment]
        errors = sub.validate()
        if errors:
            raise ValueError(f"Invalid subscription: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = WebhookSubscriptionModel.from_dataclass(sub)
            session.add(model)
            session.commit()
            sub.id = model.id  # type: ignore[assignment]
            sub.created_at = model.created_at  # type: ignore[assignment]
            return sub
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_subscription_by_id(
        self,
        sub_id: int,
        organization_id: int,
    ) -> WebhookSubscription | None:
        """Get subscription by ID."""
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(WebhookSubscriptionModel)
                .filter(
                    WebhookSubscriptionModel.id == sub_id,
                    WebhookSubscriptionModel.organization_id == organization_id,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_subscriptions_for_event(
        self,
        event: str,
        organization_id: int,
    ) -> list[WebhookSubscription]:
        """Get all active subscriptions for an event type."""
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            # Query all active subscriptions for the org
            models = (
                session.query(WebhookSubscriptionModel)
                .filter(
                    WebhookSubscriptionModel.organization_id == organization_id,
                    WebhookSubscriptionModel.is_active == True,
                )
                .all()
            )

            # Filter by event type (events is stored as JSON list)
            import json

            subscriptions = []
            for model in models:
                events = json.loads(model.events) if model.events else []  # type: ignore[arg-type]
                if event in events:
                    subscriptions.append(model.to_dataclass())

            return subscriptions
        finally:
            session.close()

    def get_all_subscriptions(
        self,
        organization_id: int,
        include_inactive: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[WebhookSubscription]:
        """Get all subscriptions in an organization."""
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(WebhookSubscriptionModel).filter(
                WebhookSubscriptionModel.organization_id == organization_id
            )

            if not include_inactive:
                query = query.filter(WebhookSubscriptionModel.is_active == True)

            query = query.order_by(WebhookSubscriptionModel.created_at.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def count_subscriptions(
        self,
        organization_id: int,
        include_inactive: bool = False,
    ) -> int:
        """Count subscriptions in an organization.

        Args:
            organization_id: Organization ID.
            include_inactive: Whether to count inactive subscriptions.

        Returns:
            Number of subscriptions.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(WebhookSubscriptionModel).filter(
                WebhookSubscriptionModel.organization_id == organization_id
            )

            if not include_inactive:
                query = query.filter(WebhookSubscriptionModel.is_active == True)

            result: int = query.count()
            return result
        finally:
            session.close()

    def update_subscription(self, sub: WebhookSubscription) -> WebhookSubscription:
        """Update a subscription."""
        sub.organization_id = validate_tenant(sub.organization_id)  # type: ignore[assignment]
        if sub.id is None:
            raise ValueError("Subscription ID is required for update")

        errors = sub.validate()
        if errors:
            raise ValueError(f"Invalid subscription: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = (
                session.query(WebhookSubscriptionModel)
                .filter(
                    WebhookSubscriptionModel.id == sub.id,
                    WebhookSubscriptionModel.organization_id == sub.organization_id,
                )
                .first()
            )
            if not model:
                raise ValueError(f"Subscription with ID {sub.id} not found")

            import json

            model.name = sub.name  # type: ignore[assignment]
            model.url = sub.url  # type: ignore[assignment]
            model.secret = sub.secret  # type: ignore[assignment]
            model.events = json.dumps(sub.events)  # type: ignore[assignment]
            model.is_active = sub.is_active  # type: ignore[assignment]
            model.headers = json.dumps(sub.headers) if sub.headers else None  # type: ignore[assignment]
            model.retry_count = sub.retry_count  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_subscription(self, sub_id: int, organization_id: int) -> bool:
        """Delete a subscription."""
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(WebhookSubscriptionModel)
                .filter(
                    WebhookSubscriptionModel.id == sub_id,
                    WebhookSubscriptionModel.organization_id == organization_id,
                )
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

    def update_subscription_triggered(
        self,
        sub_id: int,
        success: bool,
    ) -> None:
        """Update subscription after a delivery attempt."""
        session = self._get_session()
        try:
            model = (
                session.query(WebhookSubscriptionModel)
                .filter(WebhookSubscriptionModel.id == sub_id)
                .first()
            )
            if model:
                model.last_triggered_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                if success:
                    model.failure_count = 0  # type: ignore[assignment]
                else:
                    model.failure_count += 1  # type: ignore[assignment]
                session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Delivery methods

    def create_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Create a new delivery record."""
        session = self._get_session()
        try:
            model = WebhookDeliveryModel.from_dataclass(delivery)
            session.add(model)
            session.commit()
            delivery.id = model.id  # type: ignore[assignment]
            delivery.created_at = model.created_at  # type: ignore[assignment]
            return delivery
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_delivery(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """Update a delivery record."""
        if delivery.id is None:
            raise ValueError("Delivery ID is required for update")

        session = self._get_session()
        try:
            model = (
                session.query(WebhookDeliveryModel)
                .filter(WebhookDeliveryModel.id == delivery.id)
                .first()
            )
            if not model:
                raise ValueError(f"Delivery with ID {delivery.id} not found")

            model.status = delivery.status  # type: ignore[assignment]
            model.response_code = delivery.response_code  # type: ignore[assignment]
            model.response_body = delivery.response_body  # type: ignore[assignment]
            model.attempt_count = delivery.attempt_count  # type: ignore[assignment]
            model.completed_at = delivery.completed_at  # type: ignore[assignment]
            model.error_message = delivery.error_message  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_deliveries_for_subscription(
        self,
        sub_id: int,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
    ) -> list[WebhookDelivery]:
        """Get delivery history for a subscription."""
        session = self._get_session()
        try:
            query = session.query(WebhookDeliveryModel).filter(
                WebhookDeliveryModel.subscription_id == sub_id
            )

            if status:
                query = query.filter(WebhookDeliveryModel.status == status)

            query = query.order_by(WebhookDeliveryModel.created_at.desc())

            if offset > 0:
                query = query.offset(offset)
            query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def get_delivery_by_id(self, delivery_id: str) -> WebhookDelivery | None:
        """Get delivery by delivery_id."""
        session = self._get_session()
        try:
            model = (
                session.query(WebhookDeliveryModel)
                .filter(WebhookDeliveryModel.delivery_id == delivery_id)
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()


# Singleton instance
_webhook_repository: WebhookRepository | None = None


def get_webhook_repository(db_path: str | None = None) -> WebhookRepository:
    """Get or create webhook repository singleton."""
    global _webhook_repository
    if _webhook_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _webhook_repository = WebhookRepository(db_path)
    return _webhook_repository


def reset_webhook_repository() -> None:
    """Reset webhook repository singleton. For testing."""
    global _webhook_repository
    _webhook_repository = None
