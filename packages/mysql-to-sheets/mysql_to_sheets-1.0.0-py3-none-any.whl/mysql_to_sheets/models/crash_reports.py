"""SQLAlchemy model and repository for Crash Reports.

Crash reports are sent by Hybrid Agents when they encounter unhandled
exceptions. This provides "glass-box" visibility into agent failures
without requiring customers to share logs manually.

Security:
- Tracebacks are sanitized to remove sensitive data (passwords, tokens)
- Reports are stored in the tenant database
- Retention is configurable (default 30 days)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for crash report models."""

    pass


@dataclass
class CrashReport:
    """Crash report dataclass for business logic.

    Represents an unhandled exception from a Hybrid Agent.

    Attributes:
        agent_id: Agent that reported the crash.
        organization_id: Organization the agent belongs to.
        exception_type: Type of exception (e.g., "DatabaseError").
        exception_message: Exception message.
        traceback: Full traceback (sanitized).
        job_id: Job that was being processed, if any.
        version: Agent software version.
        context: Additional context (config_id, sync_mode, etc.).
    """

    agent_id: str
    organization_id: int
    exception_type: str
    exception_message: str
    id: int | None = None
    traceback: str | None = None
    job_id: int | None = None
    version: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "organization_id": self.organization_id,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "traceback": self.traceback,
            "job_id": self.job_id,
            "version": self.version,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CrashReport:
        """Create CrashReport from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        context = data.get("context", {})
        if isinstance(context, str):
            context = json.loads(context)

        return cls(
            id=data.get("id"),
            agent_id=data["agent_id"],
            organization_id=data["organization_id"],
            exception_type=data["exception_type"],
            exception_message=data["exception_message"],
            traceback=data.get("traceback"),
            job_id=data.get("job_id"),
            version=data.get("version"),
            context=context,
            created_at=created_at,
        )


class CrashReportModel(Base):
    """SQLAlchemy model for crash reports.

    Stores crash report information from Hybrid Agents.
    """

    __tablename__ = "crash_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(255), nullable=False, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    exception_type = Column(String(255), nullable=False)
    exception_message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    job_id = Column(Integer, nullable=True)
    version = Column(String(50), nullable=True)
    context = Column(Text, nullable=True)  # JSON object
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "organization_id": self.organization_id,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "traceback": self.traceback,
            "job_id": self.job_id,
            "version": self.version,
            "context": json.loads(self.context) if self.context else {},  # type: ignore
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def to_dataclass(self) -> CrashReport:
        """Convert model to CrashReport dataclass."""
        return CrashReport(
            id=self.id,  # type: ignore
            agent_id=self.agent_id,  # type: ignore
            organization_id=self.organization_id,  # type: ignore
            exception_type=self.exception_type,  # type: ignore
            exception_message=self.exception_message,  # type: ignore
            traceback=self.traceback,  # type: ignore
            job_id=self.job_id,  # type: ignore
            version=self.version,  # type: ignore
            context=json.loads(self.context) if self.context else {},  # type: ignore
            created_at=self.created_at,  # type: ignore
        )

    @classmethod
    def from_dataclass(cls, report: CrashReport) -> CrashReportModel:
        """Create model from CrashReport dataclass."""
        return cls(
            id=report.id,
            agent_id=report.agent_id,
            organization_id=report.organization_id,
            exception_type=report.exception_type,
            exception_message=report.exception_message,
            traceback=report.traceback,
            job_id=report.job_id,
            version=report.version,
            context=json.dumps(report.context) if report.context else None,
            created_at=report.created_at or datetime.now(timezone.utc),
        )


class CrashReportRepository:
    """Repository for crash report CRUD operations.

    Provides data access methods for crash reports with SQLite persistence.
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

    def create(self, report: CrashReport) -> CrashReport:
        """Create a new crash report.

        Args:
            report: CrashReport dataclass to create.

        Returns:
            Created CrashReport with ID populated.
        """
        session = self._get_session()
        try:
            model = CrashReportModel.from_dataclass(report)
            session.add(model)
            session.commit()
            return model.to_dataclass()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        report_id: int,
        organization_id: int | None = None,
    ) -> CrashReport | None:
        """Get crash report by ID.

        Args:
            report_id: Report ID.
            organization_id: Optional organization filter.

        Returns:
            CrashReport if found, None otherwise.
        """
        session = self._get_session()
        try:
            query = session.query(CrashReportModel).filter(
                CrashReportModel.id == report_id
            )
            if organization_id is not None:
                query = query.filter(
                    CrashReportModel.organization_id == organization_id
                )
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_by_agent(
        self,
        agent_id: str,
        organization_id: int,
        limit: int = 10,
    ) -> list[CrashReport]:
        """Get crash reports for an agent.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.
            limit: Maximum number of reports to return.

        Returns:
            List of crash reports, most recent first.
        """
        session = self._get_session()
        try:
            models = (
                session.query(CrashReportModel)
                .filter(
                    CrashReportModel.agent_id == agent_id,
                    CrashReportModel.organization_id == organization_id,
                )
                .order_by(CrashReportModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [model.to_dataclass() for model in models]
        finally:
            session.close()

    def get_by_organization(
        self,
        organization_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CrashReport]:
        """Get crash reports for an organization.

        Args:
            organization_id: Organization ID.
            limit: Maximum number of reports to return.
            offset: Number of reports to skip.

        Returns:
            List of crash reports, most recent first.
        """
        session = self._get_session()
        try:
            models = (
                session.query(CrashReportModel)
                .filter(CrashReportModel.organization_id == organization_id)
                .order_by(CrashReportModel.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [model.to_dataclass() for model in models]
        finally:
            session.close()

    def count(
        self,
        organization_id: int | None = None,
        agent_id: str | None = None,
    ) -> int:
        """Count crash reports.

        Args:
            organization_id: Optional organization filter.
            agent_id: Optional agent filter.

        Returns:
            Number of crash reports.
        """
        session = self._get_session()
        try:
            query = session.query(CrashReportModel)
            if organization_id is not None:
                query = query.filter(
                    CrashReportModel.organization_id == organization_id
                )
            if agent_id is not None:
                query = query.filter(CrashReportModel.agent_id == agent_id)
            return query.count()
        finally:
            session.close()

    def cleanup_old(self, retention_days: int = 30) -> int:
        """Delete crash reports older than retention period.

        Args:
            retention_days: Number of days to retain reports.

        Returns:
            Number of reports deleted.
        """
        from datetime import timedelta

        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
            deleted = (
                session.query(CrashReportModel)
                .filter(CrashReportModel.created_at < cutoff)
                .delete()
            )
            session.commit()
            return deleted  # type: ignore
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance
_crash_report_repository: CrashReportRepository | None = None


def get_crash_report_repository(db_path: str | None = None) -> CrashReportRepository:
    """Get or create crash report repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        CrashReportRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _crash_report_repository
    if _crash_report_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _crash_report_repository = CrashReportRepository(db_path)
    return _crash_report_repository


def reset_crash_report_repository() -> None:
    """Reset crash report repository singleton. For testing."""
    global _crash_report_repository
    _crash_report_repository = None
