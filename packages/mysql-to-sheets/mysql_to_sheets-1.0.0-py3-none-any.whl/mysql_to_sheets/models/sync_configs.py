"""SQLAlchemy model and repository for sync configurations.

Sync configurations allow multiple named sync jobs with different
queries and target sheets within an organization.
"""

from dataclasses import dataclass
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

from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    pass


# Valid sync modes
VALID_SYNC_MODES = ("replace", "append", "streaming")

# Valid column case transformations
VALID_COLUMN_CASES = ("none", "upper", "lower", "title")

# Valid schema evolution policies
VALID_SCHEMA_POLICIES = ("strict", "additive", "flexible", "notify_only")


@dataclass
class SyncConfigDefinition:
    """Individual sync job configuration.

    Defines a complete sync operation including the SQL query,
    target sheet, column mapping, and sync behavior.
    """

    name: str
    sql_query: str
    sheet_id: str
    organization_id: int
    id: int | None = None
    description: str = ""
    worksheet_name: str = "Sheet1"
    column_mapping: dict[str, str] | None = None
    column_order: list[str] | None = None
    column_case: str = "none"
    sync_mode: str = "replace"
    enabled: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by_user_id: int | None = None
    # Freshness tracking (Phase 4)
    last_sync_at: datetime | None = None
    last_success_at: datetime | None = None
    last_row_count: int | None = None
    sla_minutes: int = 60
    last_alert_at: datetime | None = None
    # Schema evolution policy
    schema_policy: str = "strict"
    expected_headers: list[str] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the config.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sql_query": self.sql_query,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "column_mapping": self.column_mapping,
            "column_order": self.column_order,
            "column_case": self.column_case,
            "sync_mode": self.sync_mode,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_user_id": self.created_by_user_id,
            "organization_id": self.organization_id,
            # Freshness tracking
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_row_count": self.last_row_count,
            "sla_minutes": self.sla_minutes,
            "last_alert_at": self.last_alert_at.isoformat() if self.last_alert_at else None,
            # Schema evolution
            "schema_policy": self.schema_policy,
            "expected_headers": self.expected_headers,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncConfigDefinition":
        """Create SyncConfigDefinition from dictionary.

        Args:
            data: Dictionary with config data.

        Returns:
            SyncConfigDefinition instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_sync_at = data.get("last_sync_at")
        if isinstance(last_sync_at, str):
            last_sync_at = datetime.fromisoformat(last_sync_at.replace("Z", "+00:00"))

        last_success_at = data.get("last_success_at")
        if isinstance(last_success_at, str):
            last_success_at = datetime.fromisoformat(last_success_at.replace("Z", "+00:00"))

        last_alert_at = data.get("last_alert_at")
        if isinstance(last_alert_at, str):
            last_alert_at = datetime.fromisoformat(last_alert_at.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            name=data["name"],
            description=data.get("description", ""),
            sql_query=data["sql_query"],
            sheet_id=data["sheet_id"],
            worksheet_name=data.get("worksheet_name", "Sheet1"),
            column_mapping=data.get("column_mapping"),
            column_order=data.get("column_order"),
            column_case=data.get("column_case", "none"),
            sync_mode=data.get("sync_mode", "replace"),
            enabled=data.get("enabled", True),
            created_at=created_at,
            updated_at=updated_at,
            created_by_user_id=data.get("created_by_user_id"),
            organization_id=data["organization_id"],
            last_sync_at=last_sync_at,
            last_success_at=last_success_at,
            last_row_count=data.get("last_row_count"),
            sla_minutes=data.get("sla_minutes", 60),
            last_alert_at=last_alert_at,
            schema_policy=data.get("schema_policy", "strict"),
            expected_headers=data.get("expected_headers"),
        )

    def validate(self) -> list[str]:
        """Validate the configuration.

        Returns:
            List of validation error messages.
        """
        errors = []

        if not self.name:
            errors.append("Name is required")
        if not self.sql_query:
            errors.append("SQL query is required")
        if not self.sheet_id:
            errors.append("Sheet ID is required")

        if self.sync_mode not in VALID_SYNC_MODES:
            errors.append(
                f"Invalid sync_mode '{self.sync_mode}'. Must be one of: {VALID_SYNC_MODES}"
            )

        if self.column_case not in VALID_COLUMN_CASES:
            errors.append(
                f"Invalid column_case '{self.column_case}'. Must be one of: {VALID_COLUMN_CASES}"
            )

        if self.schema_policy not in VALID_SCHEMA_POLICIES:
            errors.append(
                f"Invalid schema_policy '{self.schema_policy}'. Must be one of: {VALID_SCHEMA_POLICIES}"
            )

        return errors


class SyncConfigModel(Base):
    """SQLAlchemy model for sync configurations.

    Stores named sync configurations scoped to organizations.
    """

    __tablename__ = "sync_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sql_query = Column(Text, nullable=False)
    sheet_id = Column(String(100), nullable=False)
    worksheet_name = Column(String(100), default="Sheet1", nullable=False)
    column_mapping = Column(Text, nullable=True)  # JSON-encoded dict
    column_order = Column(Text, nullable=True)  # JSON-encoded list
    column_case = Column(String(20), default="none", nullable=False)
    sync_mode = Column(String(20), default="replace", nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.now(timezone.utc))
    created_by_user_id = Column(Integer, nullable=True)  # Soft FK to users.id
    organization_id = Column(Integer, nullable=False, index=True)  # Soft FK to organizations.id
    # Freshness tracking (Phase 4)
    last_sync_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_row_count = Column(Integer, nullable=True)
    sla_minutes = Column(Integer, default=60, nullable=False)
    last_alert_at = Column(DateTime, nullable=True)
    # Schema evolution policy
    schema_policy = Column(String(20), default="strict", nullable=False)
    expected_headers = Column(Text, nullable=True)  # JSON-encoded list

    # Unique config name per organization
    __table_args__ = (UniqueConstraint("name", "organization_id", name="uq_sync_config_name_org"),)

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        import json

        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "sql_query": self.sql_query,
            "sheet_id": self.sheet_id,
            "worksheet_name": self.worksheet_name,
            "column_mapping": json.loads(self.column_mapping) if self.column_mapping else None,  # type: ignore[arg-type]
            "column_order": json.loads(self.column_order) if self.column_order else None,  # type: ignore[arg-type]
            "column_case": self.column_case,
            "sync_mode": self.sync_mode,
            "enabled": self.enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by_user_id": self.created_by_user_id,
            "organization_id": self.organization_id,
            # Freshness tracking
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "last_success_at": self.last_success_at.isoformat() if self.last_success_at else None,
            "last_row_count": self.last_row_count,
            "sla_minutes": self.sla_minutes,
            "last_alert_at": self.last_alert_at.isoformat() if self.last_alert_at else None,
            # Schema evolution
            "schema_policy": self.schema_policy,
            "expected_headers": json.loads(self.expected_headers) if self.expected_headers else None,  # type: ignore[arg-type]
        }

    def to_dataclass(self) -> SyncConfigDefinition:
        """Convert model to SyncConfigDefinition dataclass.

        Returns:
            SyncConfigDefinition instance.
        """
        import json

        return SyncConfigDefinition(
            id=self.id,  # type: ignore[arg-type]
            name=self.name,  # type: ignore[arg-type]
            description=self.description or "",  # type: ignore[arg-type]
            sql_query=self.sql_query,  # type: ignore[arg-type]
            sheet_id=self.sheet_id,  # type: ignore[arg-type]
            worksheet_name=self.worksheet_name,  # type: ignore[arg-type]
            column_mapping=json.loads(self.column_mapping) if self.column_mapping else None,  # type: ignore[arg-type]
            column_order=json.loads(self.column_order) if self.column_order else None,  # type: ignore[arg-type]
            column_case=self.column_case,  # type: ignore[arg-type]
            sync_mode=self.sync_mode,  # type: ignore[arg-type]
            enabled=self.enabled,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            updated_at=self.updated_at,  # type: ignore[arg-type]
            created_by_user_id=self.created_by_user_id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            last_sync_at=self.last_sync_at,  # type: ignore[arg-type]
            last_success_at=self.last_success_at,  # type: ignore[arg-type]
            last_row_count=self.last_row_count,  # type: ignore[arg-type]
            sla_minutes=self.sla_minutes,  # type: ignore[arg-type]
            last_alert_at=self.last_alert_at,  # type: ignore[arg-type]
            schema_policy=self.schema_policy,  # type: ignore[arg-type]
            expected_headers=json.loads(self.expected_headers) if self.expected_headers else None,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SyncConfigModel":
        """Create model from dictionary.

        Args:
            data: Dictionary with config data.

        Returns:
            SyncConfigModel instance.
        """
        import json

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        last_sync_at = data.get("last_sync_at")
        if isinstance(last_sync_at, str):
            last_sync_at = datetime.fromisoformat(last_sync_at.replace("Z", "+00:00"))

        last_success_at = data.get("last_success_at")
        if isinstance(last_success_at, str):
            last_success_at = datetime.fromisoformat(last_success_at.replace("Z", "+00:00"))

        last_alert_at = data.get("last_alert_at")
        if isinstance(last_alert_at, str):
            last_alert_at = datetime.fromisoformat(last_alert_at.replace("Z", "+00:00"))

        column_mapping = data.get("column_mapping")
        if isinstance(column_mapping, dict):
            column_mapping = json.dumps(column_mapping)

        column_order = data.get("column_order")
        if isinstance(column_order, list):
            column_order = json.dumps(column_order)

        expected_headers = data.get("expected_headers")
        if isinstance(expected_headers, list):
            expected_headers = json.dumps(expected_headers)

        return cls(
            name=data["name"],
            description=data.get("description"),
            sql_query=data["sql_query"],
            sheet_id=data["sheet_id"],
            worksheet_name=data.get("worksheet_name", "Sheet1"),
            column_mapping=column_mapping,
            column_order=column_order,
            column_case=data.get("column_case", "none"),
            sync_mode=data.get("sync_mode", "replace"),
            enabled=data.get("enabled", True),
            created_at=created_at,
            updated_at=updated_at,
            created_by_user_id=data.get("created_by_user_id"),
            organization_id=data["organization_id"],
            last_sync_at=last_sync_at,
            last_success_at=last_success_at,
            last_row_count=data.get("last_row_count"),
            sla_minutes=data.get("sla_minutes", 60),
            last_alert_at=last_alert_at,
            schema_policy=data.get("schema_policy", "strict"),
            expected_headers=expected_headers,
        )

    @classmethod
    def from_dataclass(cls, config: SyncConfigDefinition) -> "SyncConfigModel":
        """Create model from SyncConfigDefinition dataclass.

        Args:
            config: SyncConfigDefinition instance.

        Returns:
            SyncConfigModel instance.
        """
        import json

        column_mapping = json.dumps(config.column_mapping) if config.column_mapping else None
        column_order = json.dumps(config.column_order) if config.column_order else None
        expected_headers = json.dumps(config.expected_headers) if config.expected_headers else None

        return cls(
            id=config.id,
            name=config.name,
            description=config.description,
            sql_query=config.sql_query,
            sheet_id=config.sheet_id,
            worksheet_name=config.worksheet_name,
            column_mapping=column_mapping,
            column_order=column_order,
            column_case=config.column_case,
            sync_mode=config.sync_mode,
            enabled=config.enabled,
            created_at=config.created_at or datetime.now(timezone.utc),
            updated_at=config.updated_at,
            created_by_user_id=config.created_by_user_id,
            organization_id=config.organization_id,
            last_sync_at=config.last_sync_at,
            last_success_at=config.last_success_at,
            last_row_count=config.last_row_count,
            sla_minutes=config.sla_minutes,
            last_alert_at=config.last_alert_at,
            schema_policy=config.schema_policy,
            expected_headers=expected_headers,
        )

    def __repr__(self) -> str:
        """String representation of sync config."""
        status = "enabled" if self.enabled else "disabled"
        return f"SyncConfig(id={self.id}, name='{self.name}', status={status})"


class SyncConfigRepository:
    """Repository for sync config CRUD operations.

    Provides data access methods for sync configurations with
    SQLite persistence. All queries scoped to organization.
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

    def create(self, config: SyncConfigDefinition) -> SyncConfigDefinition:
        """Create a new sync configuration.

        Args:
            config: Configuration to create.

        Returns:
            Created configuration with ID.

        Raises:
            ValueError: If name already exists in organization or validation fails.
        """
        config.organization_id = validate_tenant(config.organization_id)  # type: ignore[assignment]
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        session = self._get_session()
        try:
            # Check for existing name in org
            existing = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.name == config.name,
                    SyncConfigModel.organization_id == config.organization_id,
                )
                .first()
            )
            if existing:
                raise ValueError(
                    f"Config with name '{config.name}' already exists in this organization"
                )

            model = SyncConfigModel.from_dataclass(config)
            session.add(model)
            session.commit()
            config.id = model.id  # type: ignore[assignment]
            config.created_at = model.created_at  # type: ignore[assignment]
            return config
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        config_id: int,
        organization_id: int,
    ) -> SyncConfigDefinition | None:
        """Get configuration by ID.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            Configuration if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
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
    ) -> SyncConfigDefinition | None:
        """Get configuration by name.

        Args:
            name: Configuration name.
            organization_id: Organization ID.

        Returns:
            Configuration if found, None otherwise.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.name == name,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        enabled_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[SyncConfigDefinition]:
        """Get all configurations in an organization.

        Args:
            organization_id: Organization ID.
            enabled_only: Whether to return only enabled configs.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of configurations.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(SyncConfigModel).filter(
                SyncConfigModel.organization_id == organization_id
            )

            if enabled_only:
                query = query.filter(SyncConfigModel.enabled == True)

            query = query.order_by(SyncConfigModel.name.asc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update(self, config: SyncConfigDefinition) -> SyncConfigDefinition:
        """Update a configuration.

        Args:
            config: Configuration with updated fields.

        Returns:
            Updated configuration.

        Raises:
            ValueError: If configuration not found or name conflict.
        """
        config.organization_id = validate_tenant(config.organization_id)  # type: ignore[assignment]
        if config.id is None:
            raise ValueError("Configuration ID is required for update")

        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config.id,
                    SyncConfigModel.organization_id == config.organization_id,
                )
                .first()
            )
            if not model:
                raise ValueError(f"Configuration with ID {config.id} not found")

            # Check for name conflict if name changed
            if model.name != config.name:
                existing = (
                    session.query(SyncConfigModel)
                    .filter(
                        SyncConfigModel.name == config.name,
                        SyncConfigModel.organization_id == config.organization_id,
                        SyncConfigModel.id != config.id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(
                        f"Config with name '{config.name}' already exists in this organization"
                    )

            import json

            model.name = config.name  # type: ignore[assignment]
            model.description = config.description  # type: ignore[assignment]
            model.sql_query = config.sql_query  # type: ignore[assignment]
            model.sheet_id = config.sheet_id  # type: ignore[assignment]
            model.worksheet_name = config.worksheet_name  # type: ignore[assignment]
            column_mapping_value = json.dumps(config.column_mapping) if config.column_mapping else None
            model.column_mapping = column_mapping_value  # type: ignore[assignment]
            model.column_order = json.dumps(config.column_order) if config.column_order else None  # type: ignore[assignment]
            model.column_case = config.column_case  # type: ignore[assignment]
            model.sync_mode = config.sync_mode  # type: ignore[assignment]
            model.enabled = config.enabled  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            session.commit()
            result: SyncConfigDefinition = model.to_dataclass()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, config_id: int, organization_id: int) -> bool:
        """Delete a configuration.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if deleted, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
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

    def enable(self, config_id: int, organization_id: int) -> bool:
        """Enable a configuration.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID.

        Returns:
            True if enabled, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        return self._set_enabled(config_id, organization_id, True)

    def disable(self, config_id: int, organization_id: int) -> bool:
        """Disable a configuration.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID.

        Returns:
            True if disabled, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        return self._set_enabled(config_id, organization_id, False)

    def _set_enabled(
        self,
        config_id: int,
        organization_id: int,
        enabled: bool,
    ) -> bool:
        """Set enabled status for a configuration.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID.
            enabled: New enabled status.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.enabled = enabled  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(self, organization_id: int, enabled_only: bool = False) -> int:
        """Count configurations in an organization.

        Args:
            organization_id: Organization ID.
            enabled_only: Whether to count only enabled configs.

        Returns:
            Number of configurations.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(SyncConfigModel).filter(
                SyncConfigModel.organization_id == organization_id
            )
            if enabled_only:
                query = query.filter(SyncConfigModel.enabled == True)
            result: int = query.count()
            return result
        finally:
            session.close()

    def update_freshness(
        self,
        config_id: int,
        organization_id: int,
        success: bool,
        row_count: int | None = None,
    ) -> bool:
        """Update freshness tracking fields after a sync.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.
            success: Whether the sync was successful.
            row_count: Number of rows synced (if successful).

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            now = datetime.now(timezone.utc)
            model.last_sync_at = now  # type: ignore[assignment]

            if success:
                model.last_success_at = now  # type: ignore[assignment]
                if row_count is not None:
                    model.last_row_count = row_count  # type: ignore[assignment]

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_sla(
        self,
        config_id: int,
        organization_id: int,
        sla_minutes: int,
    ) -> bool:
        """Update SLA threshold for a configuration.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.
            sla_minutes: New SLA threshold in minutes.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        if sla_minutes < 1:
            raise ValueError("sla_minutes must be at least 1")

        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.sla_minutes = sla_minutes  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_alert(
        self,
        config_id: int,
        organization_id: int,
    ) -> bool:
        """Update last_alert_at timestamp to prevent alert spam.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if updated, False if not found.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.last_alert_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_expected_headers(
        self,
        config_id: int,
        organization_id: int,
        expected_headers: list[str],
    ) -> bool:
        """Update expected_headers after a successful sync.

        Args:
            config_id: Configuration ID.
            organization_id: Organization ID for multi-tenant isolation.
            expected_headers: The column headers from the successful sync.

        Returns:
            True if updated, False if not found.
        """
        import json

        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(SyncConfigModel)
                .filter(
                    SyncConfigModel.id == config_id,
                    SyncConfigModel.organization_id == organization_id,
                )
                .first()
            )
            if not model:
                return False

            model.expected_headers = json.dumps(expected_headers)  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance
_sync_config_repository: SyncConfigRepository | None = None


def get_sync_config_repository(db_path: str | None = None) -> SyncConfigRepository:
    """Get or create sync config repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        SyncConfigRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _sync_config_repository
    if _sync_config_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _sync_config_repository = SyncConfigRepository(db_path)
    return _sync_config_repository


def reset_sync_config_repository() -> None:
    """Reset sync config repository singleton. For testing."""
    global _sync_config_repository
    _sync_config_repository = None
