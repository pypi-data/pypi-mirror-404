"""SQLAlchemy model and repository for integrations (database/sheets connections).

Integrations store connection configurations with encrypted credentials,
allowing sync configs to reference them instead of embedding credentials.
"""

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
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mysql_to_sheets.core.encryption import decrypt_credentials, encrypt_credentials
from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    pass


# Valid integration types
VALID_INTEGRATION_TYPES = ("mysql", "postgres", "sqlite", "mssql", "google_sheets")


@dataclass
class IntegrationCredentials:
    """Credentials for a database or sheets integration.

    Only the relevant fields are populated based on integration_type.
    All credential fields are stored encrypted in the database.
    """

    # Database credentials
    user: str | None = None
    password: str | None = None

    # Google Sheets credentials
    service_account_json: str | None = None

    # Generic API key (for future use)
    api_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        if self.user is not None:
            result["user"] = self.user
        if self.password is not None:
            result["password"] = self.password
        if self.service_account_json is not None:
            result["service_account_json"] = self.service_account_json
        if self.api_key is not None:
            result["api_key"] = self.api_key
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntegrationCredentials":
        """Create from dictionary."""
        return cls(
            user=data.get("user"),
            password=data.get("password"),
            service_account_json=data.get("service_account_json"),
            api_key=data.get("api_key"),
        )

    def is_empty(self) -> bool:
        """Check if all credential fields are empty."""
        return all(
            v is None
            for v in [self.user, self.password, self.service_account_json, self.api_key]
        )


# Valid health status values
VALID_HEALTH_STATUSES = ("connected", "disconnected", "error", "unknown")


@dataclass
class Integration:
    """Integration (connection) definition.

    Represents a database or Google Sheets connection that can be
    referenced by sync configs.
    """

    name: str
    integration_type: str
    organization_id: int
    id: int | None = None
    description: str = ""
    is_active: bool = True

    # Connection settings (non-sensitive)
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    ssl_mode: str | None = None

    # Google Sheets settings (non-sensitive)
    sheet_id: str | None = None
    worksheet_name: str | None = None

    # Credentials (encrypted in database)
    credentials: IntegrationCredentials = field(default_factory=IntegrationCredentials)

    # Encryption metadata
    encryption_key_id: str | None = None

    # Health monitoring
    last_health_check_at: datetime | None = None
    health_status: str = "unknown"
    health_error_message: str | None = None
    health_latency_ms: float | None = None

    # Timestamps
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_verified_at: datetime | None = None

    def to_dict(self, include_credentials: bool = False) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Args:
            include_credentials: Whether to include decrypted credentials.
                Defaults to False for security.

        Returns:
            Dictionary representation.
        """
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "integration_type": self.integration_type,
            "is_active": self.is_active,
            "host": self.host,
            "port": self.port,
            "database_name": self.database_name,
            "ssl_mode": self.ssl_mode,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "organization_id": self.organization_id,
            "health_status": self.health_status,
            "health_error_message": self.health_error_message,
            "health_latency_ms": self.health_latency_ms,
            "last_health_check_at": self.last_health_check_at.isoformat() if self.last_health_check_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_verified_at": self.last_verified_at.isoformat() if self.last_verified_at else None,
        }

        if include_credentials:
            result["credentials"] = self.credentials.to_dict()
        else:
            # Indicate credentials are present without exposing them
            result["has_credentials"] = not self.credentials.is_empty()

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Integration":
        """Create Integration from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_verified_at = data.get("last_verified_at")
        if isinstance(last_verified_at, str):
            last_verified_at = datetime.fromisoformat(last_verified_at.replace("Z", "+00:00"))

        last_health_check_at = data.get("last_health_check_at")
        if isinstance(last_health_check_at, str):
            last_health_check_at = datetime.fromisoformat(last_health_check_at.replace("Z", "+00:00"))

        credentials_data = data.get("credentials", {})
        credentials = IntegrationCredentials.from_dict(credentials_data)

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            integration_type=data["integration_type"],
            is_active=data.get("is_active", True),
            host=data.get("host"),
            port=data.get("port"),
            database_name=data.get("database_name"),
            ssl_mode=data.get("ssl_mode"),
            sheet_id=data.get("sheet_id"),
            worksheet_name=data.get("worksheet_name"),
            credentials=credentials,
            encryption_key_id=data.get("encryption_key_id"),
            organization_id=data["organization_id"],
            health_status=data.get("health_status", "unknown"),
            health_error_message=data.get("health_error_message"),
            health_latency_ms=data.get("health_latency_ms"),
            last_health_check_at=last_health_check_at,
            created_at=created_at,
            updated_at=updated_at,
            last_verified_at=last_verified_at,
        )

    def validate(self) -> list[str]:
        """Validate the integration.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.name:
            errors.append("Name is required")

        if self.integration_type not in VALID_INTEGRATION_TYPES:
            errors.append(
                f"Invalid integration_type '{self.integration_type}'. "
                f"Must be one of: {VALID_INTEGRATION_TYPES}"
            )

        # Type-specific validation
        if self.integration_type in ("mysql", "postgres", "mssql"):
            if not self.host:
                errors.append("Host is required for database integrations")
            if not self.database_name:
                errors.append("Database name is required for database integrations")

        if self.integration_type == "sqlite":
            if not self.database_name:
                errors.append("Database path is required for SQLite integrations")

        if self.integration_type == "google_sheets":
            if not self.credentials.service_account_json:
                errors.append("Service account JSON is required for Google Sheets integrations")

        return errors


class IntegrationModel(Base):
    """SQLAlchemy model for integrations.

    Stores connection configurations with encrypted credentials.
    """

    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    integration_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Connection settings (non-sensitive)
    host = Column(String(255), nullable=True)
    port = Column(Integer, nullable=True)
    database_name = Column(String(255), nullable=True)
    ssl_mode = Column(String(50), nullable=True)

    # Encrypted credentials blob
    credentials_encrypted = Column(Text, nullable=False)
    encryption_key_id = Column(String(64), nullable=True)

    # Google Sheets settings (non-sensitive)
    sheet_id = Column(String(100), nullable=True)
    worksheet_name = Column(String(100), nullable=True)

    # Health monitoring
    last_health_check_at = Column(DateTime, nullable=True)
    health_status = Column(String(50), nullable=False, default="unknown", index=True)
    health_error_message = Column(Text, nullable=True)
    health_latency_ms = Column(Integer, nullable=True)

    # Multi-tenant
    organization_id = Column(Integer, nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc))
    last_verified_at = Column(DateTime, nullable=True)

    # Unique name per organization
    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_integration_name_org"),
    )

    def to_dataclass(self) -> Integration:
        """Convert model to Integration dataclass.

        Returns:
            Integration instance with decrypted credentials.
        """
        # Decrypt credentials
        if self.credentials_encrypted:
            creds_dict = decrypt_credentials(self.credentials_encrypted)  # type: ignore[arg-type]
            credentials = IntegrationCredentials.from_dict(creds_dict)
        else:
            credentials = IntegrationCredentials()

        return Integration(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            description=self.description or "",  # type: ignore[arg-type]
            integration_type=self.integration_type,  # type: ignore[arg-type]
            is_active=self.is_active,  # type: ignore[arg-type]
            host=self.host,  # type: ignore[arg-type]
            port=self.port,  # type: ignore[arg-type]
            database_name=self.database_name,  # type: ignore[arg-type]
            ssl_mode=self.ssl_mode,  # type: ignore[arg-type]
            sheet_id=self.sheet_id,  # type: ignore[arg-type]
            worksheet_name=self.worksheet_name,  # type: ignore[arg-type]
            credentials=credentials,
            encryption_key_id=self.encryption_key_id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            health_status=self.health_status or "unknown",  # type: ignore[arg-type]
            health_error_message=self.health_error_message,  # type: ignore[arg-type]
            health_latency_ms=self.health_latency_ms,  # type: ignore[arg-type]
            last_health_check_at=self.last_health_check_at,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
            last_verified_at=self.last_verified_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, integration: Integration) -> "IntegrationModel":
        """Create model from Integration dataclass.

        Args:
            integration: Integration instance.

        Returns:
            IntegrationModel instance with encrypted credentials.
        """
        # Encrypt credentials
        creds_dict = integration.credentials.to_dict()
        credentials_encrypted = encrypt_credentials(creds_dict) if creds_dict else ""

        return cls(
            id=integration.id,
            name=integration.name,
            description=integration.description,
            integration_type=integration.integration_type,
            is_active=integration.is_active,
            host=integration.host,
            port=integration.port,
            database_name=integration.database_name,
            ssl_mode=integration.ssl_mode,
            credentials_encrypted=credentials_encrypted,
            encryption_key_id=integration.encryption_key_id,
            sheet_id=integration.sheet_id,
            worksheet_name=integration.worksheet_name,
            organization_id=integration.organization_id,
            created_at=integration.created_at or datetime.now(timezone.utc),
            updated_at=integration.updated_at,
            last_verified_at=integration.last_verified_at,
        )

    def __repr__(self) -> str:
        """String representation of integration."""
        status = "active" if self.is_active else "inactive"
        return f"Integration(id={self.id}, name='{self.name}', type={self.integration_type}, status={status})"


class IntegrationRepository:
    """Repository for integration CRUD operations.

    Provides data access methods for integrations with SQLite persistence.
    All queries are scoped to organization for multi-tenant isolation.
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

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def create(self, integration: Integration) -> Integration:
        """Create a new integration.

        Args:
            integration: Integration to create.

        Returns:
            Created integration with ID.

        Raises:
            ValueError: If name already exists or validation fails.
        """
        integration.organization_id = validate_tenant(integration.organization_id)  # type: ignore[assignment]
        errors = integration.validate()
        if errors:
            raise ValueError(f"Invalid integration: {', '.join(errors)}")

        session = self._get_session()
        try:
            # Check for existing name in org
            existing = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.name == integration.name,
                    IntegrationModel.organization_id == integration.organization_id,
                )
                .first()
            )
            if existing:
                raise ValueError(
                    f"Integration with name '{integration.name}' already exists in this organization"
                )

            model = IntegrationModel.from_dataclass(integration)
            session.add(model)
            session.commit()
            integration.id = model.id  # type: ignore[assignment]
            integration.created_at = model.created_at  # type: ignore[assignment]
            return integration
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        integration_id: int,
        organization_id: int,
    ) -> Integration | None:
        """Get integration by ID.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            Integration if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration_id,
                    IntegrationModel.organization_id == organization_id,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_name(
        self,
        name: str,
        organization_id: int,
    ) -> Integration | None:
        """Get integration by name.

        Args:
            name: Integration name.
            organization_id: Organization ID.

        Returns:
            Integration if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.name == name,
                    IntegrationModel.organization_id == organization_id,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        integration_type: str | None = None,
        active_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Integration]:
        """Get all integrations in an organization.

        Args:
            organization_id: Organization ID.
            integration_type: Optional filter by type.
            active_only: Whether to return only active integrations.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of integrations.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(IntegrationModel).filter(
                IntegrationModel.organization_id == organization_id
            )

            if integration_type:
                query = query.filter(IntegrationModel.integration_type == integration_type)

            if active_only:
                query = query.filter(IntegrationModel.is_active == True)

            query = query.order_by(IntegrationModel.name.asc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, integration: Integration) -> Integration:
        """Update an integration.

        Args:
            integration: Integration with updated fields.

        Returns:
            Updated integration.

        Raises:
            ValueError: If integration not found or name conflict.
        """
        integration.organization_id = validate_tenant(integration.organization_id)  # type: ignore[assignment]
        if integration.id is None:
            raise ValueError("Integration ID is required for update")

        errors = integration.validate()
        if errors:
            raise ValueError(f"Invalid integration: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration.id,
                    IntegrationModel.organization_id == integration.organization_id,
                )
                .first()
            )
            if not model:
                raise ValueError(f"Integration with ID {integration.id} not found")

            # Check for name conflict if name changed
            if model.name != integration.name:
                existing = (
                    session.query(IntegrationModel)
                    .filter(
                        IntegrationModel.name == integration.name,
                        IntegrationModel.organization_id == integration.organization_id,
                        IntegrationModel.id != integration.id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(
                        f"Integration with name '{integration.name}' already exists"
                    )

            # Update fields
            model.name = integration.name  # type: ignore[assignment]
            model.description = integration.description  # type: ignore[assignment]
            model.integration_type = integration.integration_type  # type: ignore[assignment]
            model.is_active = integration.is_active  # type: ignore[assignment]
            model.host = integration.host  # type: ignore[assignment]
            model.port = integration.port  # type: ignore[assignment]
            model.database_name = integration.database_name  # type: ignore[assignment]
            model.ssl_mode = integration.ssl_mode  # type: ignore[assignment]
            model.sheet_id = integration.sheet_id  # type: ignore[assignment]
            model.worksheet_name = integration.worksheet_name  # type: ignore[assignment]

            # Re-encrypt credentials
            creds_dict = integration.credentials.to_dict()
            model.credentials_encrypted = encrypt_credentials(creds_dict) if creds_dict else ""  # type: ignore[assignment]
            model.encryption_key_id = integration.encryption_key_id  # type: ignore[assignment]

            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, integration_id: int, organization_id: int) -> bool:
        """Delete an integration.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID.

        Returns:
            True if deleted, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration_id,
                    IntegrationModel.organization_id == organization_id,
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

    def deactivate(self, integration_id: int, organization_id: int) -> bool:
        """Deactivate (soft-delete) an integration.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID.

        Returns:
            True if deactivated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        return self._set_active(integration_id, organization_id, False)

    def activate(self, integration_id: int, organization_id: int) -> bool:
        """Activate an integration.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID.

        Returns:
            True if activated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        return self._set_active(integration_id, organization_id, True)

    def _set_active(
        self,
        integration_id: int,
        organization_id: int,
        active: bool,
    ) -> bool:
        """Set active status for an integration."""
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration_id,
                    IntegrationModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.is_active = active  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_verified_at(
        self,
        integration_id: int,
        organization_id: int,
    ) -> bool:
        """Update last_verified_at timestamp after successful connection test.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration_id,
                    IntegrationModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.last_verified_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_health_status(
        self,
        integration_id: int,
        organization_id: int,
        health_status: str,
        error_message: str | None = None,
        latency_ms: float | None = None,
    ) -> bool:
        """Update health status for an integration.

        Args:
            integration_id: Integration ID.
            organization_id: Organization ID.
            health_status: New health status (connected, disconnected, error, unknown).
            error_message: Optional error message if status is error/disconnected.
            latency_ms: Optional connection latency in milliseconds.

        Returns:
            True if updated, False if not found.
        """
        if health_status not in VALID_HEALTH_STATUSES:
            raise ValueError(
                f"Invalid health_status '{health_status}'. "
                f"Must be one of: {VALID_HEALTH_STATUSES}"
            )

        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(IntegrationModel)
                .filter(
                    IntegrationModel.id == integration_id,
                    IntegrationModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.health_status = health_status  # type: ignore[assignment]
            model.health_error_message = error_message  # type: ignore[assignment]
            model.health_latency_ms = latency_ms  # type: ignore[assignment]
            model.last_health_check_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_health_status(
        self,
        organization_id: int,
        health_status: str,
        active_only: bool = True,
    ) -> list[Integration]:
        """Get integrations by health status.

        Args:
            organization_id: Organization ID.
            health_status: Health status to filter by.
            active_only: Whether to return only active integrations.

        Returns:
            List of integrations with the specified health status.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(IntegrationModel).filter(
                IntegrationModel.organization_id == organization_id,
                IntegrationModel.health_status == health_status,
            )
            if active_only:
                query = query.filter(IntegrationModel.is_active == True)
            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def count(
        self,
        organization_id: int,
        integration_type: str | None = None,
        active_only: bool = False,
    ) -> int:
        """Count integrations in an organization.

        Args:
            organization_id: Organization ID.
            integration_type: Optional filter by type.
            active_only: Whether to count only active integrations.

        Returns:
            Number of integrations.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(IntegrationModel).filter(
                IntegrationModel.organization_id == organization_id
            )
            if integration_type:
                query = query.filter(IntegrationModel.integration_type == integration_type)
            if active_only:
                query = query.filter(IntegrationModel.is_active == True)
            return query.count()
        finally:
            session.close()


# Singleton instance
_integration_repository: IntegrationRepository | None = None


def get_integration_repository(db_path: str | None = None) -> IntegrationRepository:
    """Get or create integration repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        IntegrationRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _integration_repository
    if _integration_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _integration_repository = IntegrationRepository(db_path)
    return _integration_repository


def reset_integration_repository() -> None:
    """Reset integration repository singleton. For testing."""
    global _integration_repository
    _integration_repository = None
