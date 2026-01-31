"""SQLAlchemy model and repository for Hybrid Agents.

Agents are remote workers that execute sync jobs within customer
infrastructure. They poll the control plane for jobs and report
results back.

Security:
- Agents authenticate using LINK_TOKENs (RS256 JWTs)
- Database credentials never leave customer network
- Link token hash stored for audit/revocation tracking
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for agent models."""

    pass


@dataclass
class Agent:
    """Agent dataclass for business logic.

    Represents a Hybrid Agent that executes sync jobs within
    customer infrastructure.

    Attributes:
        agent_id: Unique identifier for the agent.
        organization_id: Organization this agent belongs to.
        version: Agent software version.
        hostname: Hostname where agent is running.
        capabilities: List of capabilities (e.g., ["sync"]).
        status: Current status (online, offline, busy).
        last_seen_at: Last heartbeat timestamp.
        current_job_id: ID of job currently being processed.
    """

    agent_id: str
    organization_id: int
    id: int | None = None
    version: str = "unknown"
    hostname: str = "unknown"
    capabilities: list[str] = field(default_factory=list)
    status: str = "offline"
    is_active: bool = True
    last_seen_at: datetime | None = None
    current_job_id: int | None = None
    jobs_completed: int = 0
    jobs_failed: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "organization_id": self.organization_id,
            "version": self.version,
            "hostname": self.hostname,
            "capabilities": self.capabilities,
            "status": self.status,
            "is_active": self.is_active,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "current_job_id": self.current_job_id,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Agent:
        """Create Agent from dictionary."""
        last_seen_at = data.get("last_seen_at")
        if isinstance(last_seen_at, str):
            last_seen_at = datetime.fromisoformat(last_seen_at.replace("Z", "+00:00"))

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))

        capabilities = data.get("capabilities", [])
        if isinstance(capabilities, str):
            capabilities = json.loads(capabilities)

        return cls(
            id=data.get("id"),
            agent_id=data["agent_id"],
            organization_id=data["organization_id"],
            version=data.get("version", "unknown"),
            hostname=data.get("hostname", "unknown"),
            capabilities=capabilities,
            status=data.get("status", "offline"),
            is_active=data.get("is_active", True),
            last_seen_at=last_seen_at,
            current_job_id=data.get("current_job_id"),
            jobs_completed=data.get("jobs_completed", 0),
            jobs_failed=data.get("jobs_failed", 0),
            created_at=created_at,
            updated_at=updated_at,
        )


class AgentModel(Base):
    """SQLAlchemy model for agents.

    Stores agent registration and status information.
    """

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(100), nullable=False, unique=True, index=True)
    organization_id = Column(Integer, nullable=False, index=True)
    version = Column(String(50), default="unknown")
    hostname = Column(String(255), default="unknown")
    capabilities = Column(Text, nullable=True)  # JSON array
    status = Column(String(20), default="offline")  # online, offline, busy
    is_active = Column(Boolean, default=True)
    last_seen_at = Column(DateTime, nullable=True)
    current_job_id = Column(Integer, nullable=True)
    jobs_completed = Column(Integer, default=0)
    jobs_failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "organization_id": self.organization_id,
            "version": self.version,
            "hostname": self.hostname,
            "capabilities": json.loads(self.capabilities) if self.capabilities else [],  # type: ignore
            "status": self.status,
            "is_active": self.is_active,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "current_job_id": self.current_job_id,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_dataclass(self) -> Agent:
        """Convert model to Agent dataclass."""
        return Agent(
            id=self.id,  # type: ignore
            agent_id=self.agent_id,  # type: ignore
            organization_id=self.organization_id,  # type: ignore
            version=self.version,  # type: ignore
            hostname=self.hostname,  # type: ignore
            capabilities=json.loads(self.capabilities) if self.capabilities else [],  # type: ignore
            status=self.status,  # type: ignore
            is_active=self.is_active,  # type: ignore
            last_seen_at=self.last_seen_at,  # type: ignore
            current_job_id=self.current_job_id,  # type: ignore
            jobs_completed=self.jobs_completed,  # type: ignore
            jobs_failed=self.jobs_failed,  # type: ignore
            created_at=self.created_at,  # type: ignore
            updated_at=self.updated_at,  # type: ignore
        )

    @classmethod
    def from_dataclass(cls, agent: Agent) -> AgentModel:
        """Create model from Agent dataclass."""
        return cls(
            id=agent.id,
            agent_id=agent.agent_id,
            organization_id=agent.organization_id,
            version=agent.version,
            hostname=agent.hostname,
            capabilities=json.dumps(agent.capabilities),
            status=agent.status,
            is_active=agent.is_active,
            last_seen_at=agent.last_seen_at,
            current_job_id=agent.current_job_id,
            jobs_completed=agent.jobs_completed,
            jobs_failed=agent.jobs_failed,
            created_at=agent.created_at or datetime.now(timezone.utc),
            updated_at=agent.updated_at or datetime.now(timezone.utc),
        )


class AgentRepository:
    """Repository for agent CRUD operations.

    Provides data access methods for agents with SQLite persistence.
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

    def upsert(
        self,
        agent_id: str,
        organization_id: int,
        version: str = "unknown",
        hostname: str = "unknown",
        capabilities: list[str] | None = None,
    ) -> Agent:
        """Create or update an agent registration.

        Args:
            agent_id: Unique agent identifier.
            organization_id: Organization ID.
            version: Agent software version.
            hostname: Hostname where agent is running.
            capabilities: List of capabilities.

        Returns:
            Agent dataclass.
        """
        session = self._get_session()
        try:
            model = (
                session.query(AgentModel)
                .filter(AgentModel.agent_id == agent_id)
                .first()
            )

            now = datetime.now(timezone.utc)

            if model:
                # Update existing
                model.organization_id = organization_id  # type: ignore
                model.version = version  # type: ignore
                model.hostname = hostname  # type: ignore
                model.capabilities = json.dumps(capabilities or [])  # type: ignore
                model.status = "online"  # type: ignore
                model.last_seen_at = now  # type: ignore
                model.updated_at = now  # type: ignore
            else:
                # Create new
                model = AgentModel(
                    agent_id=agent_id,
                    organization_id=organization_id,
                    version=version,
                    hostname=hostname,
                    capabilities=json.dumps(capabilities or []),
                    status="online",
                    is_active=True,
                    last_seen_at=now,
                    created_at=now,
                    updated_at=now,
                )
                session.add(model)

            session.commit()
            return model.to_dataclass()

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_agent_id(
        self,
        agent_id: str,
        organization_id: int | None = None,
    ) -> Agent | None:
        """Get agent by agent_id.

        Args:
            agent_id: Agent identifier.
            organization_id: Optional organization filter.

        Returns:
            Agent if found, None otherwise.
        """
        session = self._get_session()
        try:
            query = session.query(AgentModel).filter(AgentModel.agent_id == agent_id)
            if organization_id is not None:
                query = query.filter(AgentModel.organization_id == organization_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        include_inactive: bool = False,
        status: str | None = None,
    ) -> list[Agent]:
        """Get all agents for an organization.

        Args:
            organization_id: Organization ID.
            include_inactive: Whether to include inactive agents.
            status: Optional status filter.

        Returns:
            List of agents.
        """
        session = self._get_session()
        try:
            query = session.query(AgentModel).filter(
                AgentModel.organization_id == organization_id
            )

            if not include_inactive:
                query = query.filter(AgentModel.is_active == True)
            if status:
                query = query.filter(AgentModel.status == status)

            query = query.order_by(AgentModel.last_seen_at.desc())
            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def update_status(
        self,
        agent_id: str,
        organization_id: int,
        status: str,
    ) -> bool:
        """Update agent status.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.
            status: New status (online, offline, busy).

        Returns:
            True if updated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(AgentModel)
                .filter(
                    AgentModel.agent_id == agent_id,
                    AgentModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.status = status  # type: ignore
            model.updated_at = datetime.now(timezone.utc)  # type: ignore
            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_seen(
        self,
        agent_id: str,
        organization_id: int,
    ) -> bool:
        """Update agent last_seen timestamp.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.

        Returns:
            True if updated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(AgentModel)
                .filter(
                    AgentModel.agent_id == agent_id,
                    AgentModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            now = datetime.now(timezone.utc)
            model.last_seen_at = now  # type: ignore
            model.status = "online"  # type: ignore
            model.updated_at = now  # type: ignore
            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_heartbeat(
        self,
        agent_id: str,
        organization_id: int,
        current_job_id: int | None = None,
        status: dict[str, Any] | None = None,
    ) -> bool:
        """Update agent heartbeat with job progress.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.
            current_job_id: ID of job being processed.
            status: Status dict with metrics.

        Returns:
            True if updated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(AgentModel)
                .filter(
                    AgentModel.agent_id == agent_id,
                    AgentModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            now = datetime.now(timezone.utc)
            model.last_seen_at = now  # type: ignore
            model.current_job_id = current_job_id  # type: ignore
            model.status = "busy" if current_job_id else "online"  # type: ignore
            model.updated_at = now  # type: ignore

            # Update counters from status dict
            if status:
                if "jobs_completed" in status:
                    model.jobs_completed = status["jobs_completed"]  # type: ignore
                if "jobs_failed" in status:
                    model.jobs_failed = status["jobs_failed"]  # type: ignore

            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def deactivate(self, agent_id: str, organization_id: int) -> bool:
        """Deactivate an agent.

        Args:
            agent_id: Agent identifier.
            organization_id: Organization ID.

        Returns:
            True if deactivated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(AgentModel)
                .filter(
                    AgentModel.agent_id == agent_id,
                    AgentModel.organization_id == organization_id,
                )
                .first()
            )

            if not model:
                return False

            model.is_active = False  # type: ignore
            model.status = "offline"  # type: ignore
            model.updated_at = datetime.now(timezone.utc)  # type: ignore
            session.commit()
            return True

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def count(
        self,
        organization_id: int | None = None,
        status: str | None = None,
    ) -> int:
        """Count agents.

        Args:
            organization_id: Optional organization filter.
            status: Optional status filter.

        Returns:
            Number of agents.
        """
        session = self._get_session()
        try:
            query = session.query(AgentModel).filter(AgentModel.is_active == True)

            if organization_id is not None:
                query = query.filter(AgentModel.organization_id == organization_id)
            if status:
                query = query.filter(AgentModel.status == status)

            return query.count()
        finally:
            session.close()

    def cleanup_stale(self, timeout_seconds: int = 300) -> int:
        """Mark stale agents as offline.

        Agents that haven't sent a heartbeat within timeout are
        marked offline.

        Args:
            timeout_seconds: Seconds before considering stale.

        Returns:
            Number of agents marked offline.
        """
        return len(self.cleanup_stale_with_list(timeout_seconds))

    def cleanup_stale_with_list(self, timeout_seconds: int = 300) -> list[Agent]:
        """Mark stale agents as offline and return the list.

        Agents that haven't sent a heartbeat within timeout are
        marked offline. Returns the list of agents that were marked
        offline for webhook notification.

        Args:
            timeout_seconds: Seconds before considering stale.

        Returns:
            List of Agent dataclasses that were marked offline.
        """
        from datetime import timedelta

        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

            stale = (
                session.query(AgentModel)
                .filter(
                    AgentModel.status.in_(["online", "busy"]),
                    AgentModel.last_seen_at < cutoff,
                )
                .all()
            )

            stale_agents: list[Agent] = []
            for model in stale:
                # Capture current state before updating for webhook payload
                agent = model.to_dataclass()
                model.status = "offline"  # type: ignore
                model.current_job_id = None  # type: ignore
                stale_agents.append(agent)

            session.commit()
            return stale_agents

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_fleet_stats(self, organization_id: int) -> dict[str, Any]:
        """Get fleet health statistics for an organization.

        Args:
            organization_id: Organization ID.

        Returns:
            Dictionary with fleet stats:
            - total: Total number of agents
            - online: Number of online agents
            - offline: Number of offline agents
            - busy: Number of busy agents
            - jobs_completed: Total jobs completed
            - jobs_failed: Total jobs failed
        """
        session = self._get_session()
        try:
            agents = (
                session.query(AgentModel)
                .filter(
                    AgentModel.organization_id == organization_id,
                    AgentModel.is_active == True,
                )
                .all()
            )

            stats = {
                "total": len(agents),
                "online": 0,
                "offline": 0,
                "busy": 0,
                "jobs_completed": 0,
                "jobs_failed": 0,
            }

            for agent in agents:
                if agent.status == "online":
                    stats["online"] += 1
                elif agent.status == "offline":
                    stats["offline"] += 1
                elif agent.status == "busy":
                    stats["busy"] += 1
                stats["jobs_completed"] += agent.jobs_completed or 0
                stats["jobs_failed"] += agent.jobs_failed or 0

            return stats
        finally:
            session.close()


# Singleton instance
_agent_repository: AgentRepository | None = None


def get_agent_repository(db_path: str | None = None) -> AgentRepository:
    """Get or create agent repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        AgentRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _agent_repository
    if _agent_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _agent_repository = AgentRepository(db_path)
    return _agent_repository


def reset_agent_repository() -> None:
    """Reset agent repository singleton. For testing."""
    global _agent_repository
    _agent_repository = None
