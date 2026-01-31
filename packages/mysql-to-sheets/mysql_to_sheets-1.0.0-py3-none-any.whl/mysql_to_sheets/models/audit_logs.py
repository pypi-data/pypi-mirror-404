"""SQLAlchemy models for audit logging.

Audit logs capture detailed trails of all system operations for
SOC2/HIPAA compliance. Logs are append-only (no update/delete via API).
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
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
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


# Use a separate Base for audit logs to avoid FK dependencies
# This makes audit logs independent and easier to test/maintain
class AuditBase(DeclarativeBase):
    pass


@dataclass
class AuditLog:
    """Audit log entry dataclass.

    Represents a single auditable event in the system. Audit logs are
    immutable after creation - they cannot be updated or deleted via API.
    """

    action: str
    resource_type: str
    organization_id: int
    id: int | None = None
    timestamp: datetime | None = None
    user_id: int | None = None
    resource_id: str | None = None
    source_ip: str | None = None
    user_agent: str | None = None
    query_executed: str | None = None
    rows_affected: int | None = None
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the audit log.
        """
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "query_executed": self.query_executed,
            "rows_affected": self.rows_affected,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditLog":
        """Create AuditLog from dictionary.

        Args:
            data: Dictionary with audit log data.

        Returns:
            AuditLog instance.
        """
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        return cls(
            id=data.get("id"),
            timestamp=timestamp,
            user_id=data.get("user_id"),
            organization_id=data["organization_id"],
            action=data["action"],
            resource_type=data["resource_type"],
            resource_id=data.get("resource_id"),
            source_ip=data.get("source_ip"),
            user_agent=data.get("user_agent"),
            query_executed=data.get("query_executed"),
            rows_affected=data.get("rows_affected"),
            metadata=data.get("metadata"),
        )


class AuditLogModel(AuditBase):
    """SQLAlchemy model for audit logs.

    Stores audit trail entries with indexes optimized for
    time-range and action-based queries.
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    user_id = Column(Integer, nullable=True, index=True)  # No FK - audit logs are independent
    organization_id = Column(
        Integer, nullable=False, index=True
    )  # No FK - audit logs are independent
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(100), nullable=True)
    source_ip = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    query_executed = Column(Text, nullable=True)  # Sanitized SQL
    rows_affected = Column(Integer, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON-encoded dict (renamed from metadata)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_audit_logs_org_timestamp", "organization_id", "timestamp"),
        Index("ix_audit_logs_org_action", "organization_id", "action"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "query_executed": self.query_executed,
            "rows_affected": self.rows_affected,
            "metadata": json.loads(self.extra_data) if self.extra_data else None,  # type: ignore[arg-type]
        }

    def to_dataclass(self) -> AuditLog:
        """Convert model to AuditLog dataclass."""
        return AuditLog(
            id=self.id,  # type: ignore[arg-type]
            timestamp=self.timestamp,  # type: ignore[arg-type]
            user_id=self.user_id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            action=self.action,  # type: ignore[arg-type]
            resource_type=self.resource_type,  # type: ignore[arg-type]
            resource_id=self.resource_id,  # type: ignore[arg-type]
            source_ip=self.source_ip,  # type: ignore[arg-type]
            user_agent=self.user_agent,  # type: ignore[arg-type]
            query_executed=self.query_executed,  # type: ignore[arg-type]
            rows_affected=self.rows_affected,  # type: ignore[arg-type]
            metadata=json.loads(self.extra_data) if self.extra_data else None,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, log: AuditLog) -> "AuditLogModel":
        """Create model from AuditLog dataclass."""
        return cls(
            id=log.id,
            timestamp=log.timestamp or datetime.now(timezone.utc),
            user_id=log.user_id,
            organization_id=log.organization_id,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            source_ip=log.source_ip,
            user_agent=log.user_agent,
            query_executed=log.query_executed,
            rows_affected=log.rows_affected,
            extra_data=json.dumps(log.metadata) if log.metadata else None,
        )

    def __repr__(self) -> str:
        return (
            f"AuditLog(id={self.id}, action='{self.action}', resource_type='{self.resource_type}')"
        )


class AuditLogRepository:
    """Repository for audit log operations.

    Provides append-only access to audit logs with filtering
    and pagination. All queries are scoped by organization_id.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository with database path.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        AuditBase.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def add(self, log: AuditLog) -> AuditLog:
        """Add a new audit log entry.

        Args:
            log: AuditLog to create.

        Returns:
            Created AuditLog with ID and timestamp.
        """
        log.organization_id = validate_tenant(log.organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = AuditLogModel.from_dataclass(log)
            session.add(model)
            session.commit()
            log.id = model.id  # type: ignore[assignment]
            log.timestamp = model.timestamp  # type: ignore[assignment]
            return log
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        action: str | None = None,
        user_id: int | None = None,
        resource_type: str | None = None,
        limit: int | None = 100,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Get audit logs with filters.

        Args:
            organization_id: Organization to query (required).
            from_date: Filter logs after this timestamp.
            to_date: Filter logs before this timestamp.
            action: Filter by action type.
            user_id: Filter by user ID.
            resource_type: Filter by resource type.
            limit: Maximum results (default 100).
            offset: Results to skip.

        Returns:
            List of matching audit logs.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(AuditLogModel).filter(
                AuditLogModel.organization_id == organization_id
            )

            if from_date:
                query = query.filter(AuditLogModel.timestamp >= from_date)
            if to_date:
                query = query.filter(AuditLogModel.timestamp <= to_date)
            if action:
                query = query.filter(AuditLogModel.action == action)
            if user_id is not None:
                query = query.filter(AuditLogModel.user_id == user_id)
            if resource_type:
                query = query.filter(AuditLogModel.resource_type == resource_type)

            query = query.order_by(AuditLogModel.timestamp.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def count(
        self,
        organization_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        action: str | None = None,
        user_id: int | None = None,
    ) -> int:
        """Count audit logs with filters.

        Args:
            organization_id: Organization to query.
            from_date: Filter logs after this timestamp.
            to_date: Filter logs before this timestamp.
            action: Filter by action type.
            user_id: Filter by user ID.

        Returns:
            Count of matching logs.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(AuditLogModel).filter(
                AuditLogModel.organization_id == organization_id
            )

            if from_date:
                query = query.filter(AuditLogModel.timestamp >= from_date)
            if to_date:
                query = query.filter(AuditLogModel.timestamp <= to_date)
            if action:
                query = query.filter(AuditLogModel.action == action)
            if user_id is not None:
                query = query.filter(AuditLogModel.user_id == user_id)

            result: int = query.count()
            return result
        finally:
            session.close()

    def delete_before(self, cutoff_date: datetime, organization_id: int | None = None) -> int:
        """Delete audit logs older than cutoff date.

        This is for retention management only - not exposed via API.

        Args:
            cutoff_date: Delete logs older than this date.
            organization_id: Optionally scope to specific org.

        Returns:
            Number of deleted records.
        """
        validated_org_id: int | None = None
        if organization_id is not None:
            validated_org_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(AuditLogModel).filter(AuditLogModel.timestamp < cutoff_date)

            if validated_org_id is not None:
                query = query.filter(AuditLogModel.organization_id == validated_org_id)

            count: int = query.delete(synchronize_session=False)
            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_stats(self, organization_id: int) -> dict[str, Any]:
        """Get audit log statistics for an organization.

        Args:
            organization_id: Organization to query.

        Returns:
            Dictionary with statistics.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            from sqlalchemy import func

            # Total count
            total = (
                session.query(func.count(AuditLogModel.id))
                .filter(AuditLogModel.organization_id == organization_id)
                .scalar()
            )

            # Oldest and newest logs
            oldest = (
                session.query(func.min(AuditLogModel.timestamp))
                .filter(AuditLogModel.organization_id == organization_id)
                .scalar()
            )
            newest = (
                session.query(func.max(AuditLogModel.timestamp))
                .filter(AuditLogModel.organization_id == organization_id)
                .scalar()
            )

            # Count by action
            action_counts = (
                session.query(
                    AuditLogModel.action,
                    func.count(AuditLogModel.id),
                )
                .filter(AuditLogModel.organization_id == organization_id)
                .group_by(AuditLogModel.action)
                .all()
            )

            # Count by resource type
            resource_counts = (
                session.query(
                    AuditLogModel.resource_type,
                    func.count(AuditLogModel.id),
                )
                .filter(AuditLogModel.organization_id == organization_id)
                .group_by(AuditLogModel.resource_type)
                .all()
            )

            return {
                "total_logs": total or 0,
                "oldest_log": oldest.isoformat() if oldest else None,
                "newest_log": newest.isoformat() if newest else None,
                "by_action": {action: count for action, count in action_counts},
                "by_resource_type": {rtype: count for rtype, count in resource_counts},
            }
        finally:
            session.close()

    def get_actions(self, organization_id: int) -> list[str]:
        """Get distinct action types for an organization.

        Args:
            organization_id: Organization to query.

        Returns:
            List of distinct action types.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            from sqlalchemy import distinct

            actions = (
                session.query(distinct(AuditLogModel.action))
                .filter(AuditLogModel.organization_id == organization_id)
                .all()
            )
            return [a[0] for a in actions]
        finally:
            session.close()

    def stream_logs(
        self,
        organization_id: int,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        action: str | None = None,
        user_id: int | None = None,
        batch_size: int = 1000,
    ) -> Any:  # Generator type
        """Stream audit logs in batches for export.

        Yields batches of logs to avoid loading everything into memory.

        Args:
            organization_id: Organization to query.
            from_date: Filter logs after this timestamp.
            to_date: Filter logs before this timestamp.
            action: Filter by action type.
            user_id: Filter by user ID.
            batch_size: Number of logs per batch.

        Yields:
            Batches of AuditLog instances.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        offset = 0
        while True:
            batch = self.get_all(
                organization_id=organization_id,
                from_date=from_date,
                to_date=to_date,
                action=action,
                user_id=user_id,
                limit=batch_size,
                offset=offset,
            )
            if not batch:
                break
            yield batch
            offset += batch_size


# Singleton instance
_audit_log_repository: AuditLogRepository | None = None


def get_audit_log_repository(db_path: str | None = None) -> AuditLogRepository:
    """Get or create audit log repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        AuditLogRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _audit_log_repository
    if _audit_log_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _audit_log_repository = AuditLogRepository(db_path)
    return _audit_log_repository


def reset_audit_log_repository() -> None:
    """Reset audit log repository singleton. For testing."""
    global _audit_log_repository
    _audit_log_repository = None
