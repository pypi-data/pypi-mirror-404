"""SQLAlchemy model and repository for job queue.

Jobs represent async work items that can be processed by workers.
Supports priority-based scheduling and multi-tenant isolation.
"""

import json
from dataclasses import dataclass, field
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
    text,
)
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from mysql_to_sheets.models.repository import validate_tenant


class Base(DeclarativeBase):
    pass


# Valid job statuses
VALID_JOB_STATUSES = ("pending", "running", "completed", "failed", "cancelled", "dead_letter")

# Valid job types
VALID_JOB_TYPES = ("sync", "export")


@dataclass
class Job:
    """Job queue item.

    Represents an async work item with priority, status tracking,
    and retry support.
    """

    organization_id: int
    job_type: str
    payload: dict[str, Any]
    id: int | None = None
    user_id: int | None = None
    status: str = "pending"
    priority: int = 0
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempts: int = 0
    max_attempts: int = 3
    # Distributed worker fields (Phase 2B)
    worker_id: str | None = None
    heartbeat_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the job.
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "payload": self.payload,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "worker_id": self.worker_id,
            "heartbeat_at": self.heartbeat_at.isoformat() if self.heartbeat_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """Create Job from dictionary.

        Args:
            data: Dictionary with job data.

        Returns:
            Job instance.
        """
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at.replace("Z", "+00:00"))

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))

        heartbeat_at = data.get("heartbeat_at")
        if isinstance(heartbeat_at, str):
            heartbeat_at = datetime.fromisoformat(heartbeat_at.replace("Z", "+00:00"))

        payload = data.get("payload", {})
        if isinstance(payload, str):
            payload = json.loads(payload)

        result = data.get("result")
        if isinstance(result, str):
            result = json.loads(result)

        return cls(
            id=data.get("id"),
            organization_id=data["organization_id"],
            user_id=data.get("user_id"),
            job_type=data["job_type"],
            status=data.get("status", "pending"),
            priority=data.get("priority", 0),
            payload=payload,
            result=result,
            error=data.get("error"),
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            attempts=data.get("attempts", 0),
            max_attempts=data.get("max_attempts", 3),
            worker_id=data.get("worker_id"),
            heartbeat_at=heartbeat_at,
        )

    def validate(self) -> list[str]:
        """Validate the job.

        Returns:
            List of validation error messages.
        """
        errors = []

        if self.job_type not in VALID_JOB_TYPES:
            errors.append(f"Invalid job_type '{self.job_type}'. Must be one of: {VALID_JOB_TYPES}")

        if self.status not in VALID_JOB_STATUSES:
            errors.append(f"Invalid status '{self.status}'. Must be one of: {VALID_JOB_STATUSES}")

        if not isinstance(self.payload, dict):
            errors.append("payload must be a dictionary")

        if self.priority < 0:
            errors.append("priority must be non-negative")

        return errors

    @property
    def can_retry(self) -> bool:
        """Check if job can be retried.

        Returns:
            True if job hasn't exceeded max attempts.
        """
        return self.attempts < self.max_attempts

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state.

        Returns:
            True if completed, failed, cancelled, or dead_letter.
        """
        return self.status in ("completed", "failed", "cancelled", "dead_letter")


class JobModel(Base):
    """SQLAlchemy model for jobs.

    Stores job queue items with multi-tenant isolation.
    """

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    organization_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=True)
    job_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    priority = Column(Integer, nullable=False, default=0)
    payload = Column(Text, nullable=False)  # JSON-encoded dict
    result = Column(Text, nullable=True)  # JSON-encoded dict
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now(timezone.utc), index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    # Distributed worker fields (Phase 2B)
    worker_id = Column(String(100), nullable=True, index=True)
    heartbeat_at = Column(DateTime, nullable=True)

    # Composite index for efficient job claiming
    __table_args__ = (
        Index(
            "ix_jobs_claim",
            "status",
            "priority",
            "created_at",
        ),
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the job.
        """
        return {
            "id": self.id,
            "organization_id": self.organization_id,
            "user_id": self.user_id,
            "job_type": self.job_type,
            "status": self.status,
            "priority": self.priority,
            "payload": json.loads(self.payload) if self.payload else {},  # type: ignore[arg-type]
            "result": json.loads(self.result) if self.result else None,  # type: ignore[arg-type]
            "error": self.error,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "worker_id": self.worker_id,
            "heartbeat_at": self.heartbeat_at.isoformat() if self.heartbeat_at else None,
        }

    def to_dataclass(self) -> Job:
        """Convert model to Job dataclass.

        Returns:
            Job instance.
        """
        return Job(
            id=self.id,  # type: ignore[arg-type]
            organization_id=self.organization_id,  # type: ignore[arg-type]
            user_id=self.user_id,  # type: ignore[arg-type]
            job_type=self.job_type,  # type: ignore[arg-type]
            status=self.status,  # type: ignore[arg-type]
            priority=self.priority,  # type: ignore[arg-type]
            payload=json.loads(self.payload) if self.payload else {},  # type: ignore[arg-type]
            result=json.loads(self.result) if self.result else None,  # type: ignore[arg-type]
            error=self.error,  # type: ignore[arg-type]
            created_at=self.created_at,  # type: ignore[arg-type]
            started_at=self.started_at,  # type: ignore[arg-type]
            completed_at=self.completed_at,  # type: ignore[arg-type]
            attempts=self.attempts,  # type: ignore[arg-type]
            max_attempts=self.max_attempts,  # type: ignore[arg-type]
            worker_id=self.worker_id,  # type: ignore[arg-type]
            heartbeat_at=self.heartbeat_at,  # type: ignore[arg-type]
        )

    @classmethod
    def from_dataclass(cls, job: Job) -> "JobModel":
        """Create model from Job dataclass.

        Args:
            job: Job instance.

        Returns:
            JobModel instance.
        """
        return cls(
            id=job.id,
            organization_id=job.organization_id,
            user_id=job.user_id,
            job_type=job.job_type,
            status=job.status,
            priority=job.priority,
            payload=json.dumps(job.payload),
            result=json.dumps(job.result) if job.result else None,
            error=job.error,
            created_at=job.created_at or datetime.now(timezone.utc),
            started_at=job.started_at,
            completed_at=job.completed_at,
            attempts=job.attempts,
            max_attempts=job.max_attempts,
            worker_id=job.worker_id,
            heartbeat_at=job.heartbeat_at,
        )

    def __repr__(self) -> str:
        """String representation of job."""
        return f"Job(id={self.id}, type='{self.job_type}', status='{self.status}')"


class JobRepository:
    """Repository for job CRUD operations.

    Provides data access methods for jobs with SQLite persistence.
    All queries scoped to organization for multi-tenant isolation.
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

    def create(self, job: Job) -> Job:
        """Create a new job.

        Args:
            job: Job to create.

        Returns:
            Created job with ID.

        Raises:
            ValueError: If validation fails.
        """
        job.organization_id = validate_tenant(job.organization_id)  # type: ignore[assignment]
        errors = job.validate()
        if errors:
            raise ValueError(f"Invalid job: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = JobModel.from_dataclass(job)
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
        job_id: int,
        organization_id: int | None = None,
    ) -> Job | None:
        """Get job by ID.

        Args:
            job_id: Job ID.
            organization_id: Optional organization ID for multi-tenant isolation.

        Returns:
            Job if found, None otherwise.
        """
        if organization_id is not None:
            organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.id == job_id)
            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_next_pending(self) -> Job | None:
        """Get next pending job to process.

        Uses atomic claim with UPDATE...WHERE to prevent race conditions.
        Jobs are prioritized by priority (higher first) then created_at (older first).

        Returns:
            Job if available, None otherwise.
        """
        session = self._get_session()
        try:
            # Use BEGIN IMMEDIATE for SQLite write lock
            session.execute(text("BEGIN IMMEDIATE"))

            # Find the next pending job
            model = (
                session.query(JobModel)
                .filter(JobModel.status == "pending")
                .order_by(JobModel.priority.desc(), JobModel.created_at.asc())
                .with_for_update()
                .first()
            )

            if not model:
                session.rollback()
                return None

            # Atomically claim the job
            model.status = "running"
            model.started_at = datetime.now(timezone.utc)
            model.attempts += 1
            session.commit()

            return model.to_dataclass()  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def claim_job(self, job_id: int) -> Job | None:
        """Attempt to claim a specific job.

        Args:
            job_id: ID of job to claim.

        Returns:
            Claimed job if successful, None if not available.
        """
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.status == "pending",
                )
                .first()
            )

            if not model:
                return None

            model.status = "running"
            model.started_at = datetime.now(timezone.utc)
            model.attempts += 1
            session.commit()

            return model.to_dataclass()  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def complete(self, job_id: int, result: dict[str, Any]) -> bool:
        """Mark job as completed.

        Args:
            job_id: Job ID.
            result: Result data.

        Returns:
            True if updated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.status == "running",
                )
                .first()
            )
            if not model:
                return False

            model.status = "completed"
            model.result = json.dumps(result)
            model.completed_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def fail(
        self,
        job_id: int,
        error: str,
        requeue: bool = True,
        move_to_dlq: bool = True,
    ) -> bool:
        """Mark job as failed.

        Args:
            job_id: Job ID.
            error: Error message.
            requeue: Whether to requeue if retries available.
            move_to_dlq: Move to dead letter queue when max attempts exhausted.

        Returns:
            True if updated, False if not found.
        """
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.status == "running",
                )
                .first()
            )
            if not model:
                return False

            model.error = error
            model.completed_at = datetime.now(timezone.utc)

            # Requeue if retries available
            if requeue and model.attempts < model.max_attempts:
                model.status = "pending"
                model.started_at = None
                model.completed_at = None
            elif move_to_dlq:
                # Move to dead letter queue for permanent storage
                model.status = "dead_letter"
            else:
                model.status = "failed"

            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def cancel(self, job_id: int, organization_id: int) -> bool:
        """Cancel a pending job.

        Args:
            job_id: Job ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if cancelled, False if not found or not pending.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.organization_id == organization_id,
                    JobModel.status == "pending",
                )
                .first()
            )
            if not model:
                return False

            model.status = "cancelled"
            model.completed_at = datetime.now(timezone.utc)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def retry(self, job_id: int, organization_id: int) -> Job | None:
        """Retry a failed job.

        Args:
            job_id: Job ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            Updated job if retried, None if not found or not failed.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.organization_id == organization_id,
                    JobModel.status == "failed",
                )
                .first()
            )
            if not model:
                return None

            model.status = "pending"
            model.error = None
            model.started_at = None
            model.completed_at = None
            model.attempts = 0
            session.commit()
            return model.to_dataclass()  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_all(
        self,
        organization_id: int,
        status: str | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get all jobs in an organization.

        Args:
            organization_id: Organization ID.
            status: Optional status filter.
            job_type: Optional job type filter.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of jobs.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.organization_id == organization_id)

            if status:
                query = query.filter(JobModel.status == status)
            if job_type:
                query = query.filter(JobModel.job_type == job_type)

            query = query.order_by(JobModel.created_at.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def count(
        self,
        organization_id: int | None = None,
        status: str | None = None,
    ) -> int:
        """Count jobs.

        Args:
            organization_id: Optional organization filter.
            status: Optional status filter.

        Returns:
            Number of jobs matching criteria.
        """
        if organization_id is not None:
            organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(JobModel)

            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)
            if status:
                query = query.filter(JobModel.status == status)

            return query.count()  # type: ignore[no-any-return]
        finally:
            session.close()

    def cleanup_stale(self, timeout_seconds: int = 300) -> int:
        """Clean up stale running jobs.

        Marks jobs as failed if they've been running longer than timeout.

        Args:
            timeout_seconds: Maximum runtime before considering stale.

        Returns:
            Number of jobs cleaned up.
        """
        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc)
            from datetime import timedelta

            cutoff = cutoff - timedelta(seconds=timeout_seconds)

            stale_jobs = (
                session.query(JobModel)
                .filter(
                    JobModel.status == "running",
                    JobModel.started_at < cutoff,
                )
                .all()
            )

            count = 0
            for model in stale_jobs:
                model.status = "failed"
                model.error = f"Job timed out after {timeout_seconds} seconds"
                model.completed_at = datetime.now(timezone.utc)
                count += 1

            session.commit()
            return count
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_old(self, days: int = 30) -> int:
        """Delete old completed/failed/cancelled jobs.

        Note: Dead letter jobs are preserved and must be explicitly purged.

        Args:
            days: Number of days to retain.

        Returns:
            Number of jobs deleted.
        """
        session = self._get_session()
        try:
            from datetime import timedelta

            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            # Explicitly exclude dead_letter - they should be preserved
            deleted = (
                session.query(JobModel)
                .filter(
                    JobModel.status.in_(["completed", "failed", "cancelled"]),
                    JobModel.completed_at < cutoff,
                )
                .delete(synchronize_session=False)
            )

            session.commit()
            return deleted  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # Dead Letter Queue (DLQ) Operations

    def get_dead_letter_jobs(
        self,
        organization_id: int | None = None,
        job_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """Get jobs in the dead letter queue.

        Args:
            organization_id: Optional organization filter.
            job_type: Optional job type filter.
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            List of dead letter jobs.
        """
        if organization_id is not None:
            organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.status == "dead_letter")

            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)
            if job_type:
                query = query.filter(JobModel.job_type == job_type)

            query = query.order_by(JobModel.completed_at.desc())

            if offset > 0:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            return [model.to_dataclass() for model in query.all()]
        finally:
            session.close()

    def count_dead_letter(self, organization_id: int | None = None) -> int:
        """Count jobs in dead letter queue.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Number of dead letter jobs.
        """
        if organization_id is not None:
            organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.status == "dead_letter")

            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)

            return query.count()  # type: ignore[no-any-return]
        finally:
            session.close()

    def retry_dead_letter(self, job_id: int, organization_id: int) -> Job | None:
        """Retry a job from the dead letter queue.

        Resets the job to pending status with fresh attempt counter.

        Args:
            job_id: Job ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            Retried job if successful, None if not found or not in DLQ.
        """
        organization_id = validate_tenant(organization_id)  # type: ignore[assignment]
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.organization_id == organization_id,
                    JobModel.status == "dead_letter",
                )
                .first()
            )
            if not model:
                return None

            model.status = "pending"
            model.error = None
            model.started_at = None
            model.completed_at = None
            model.attempts = 0  # Reset attempts for DLQ retry
            session.commit()
            return model.to_dataclass()  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def purge_dead_letter(
        self,
        organization_id: int | None = None,
        older_than_days: int | None = None,
    ) -> int:
        """Purge jobs from the dead letter queue.

        Args:
            organization_id: Optional organization filter.
            older_than_days: Only purge jobs older than this many days.

        Returns:
            Number of jobs purged.
        """
        if organization_id is not None:
            organization_id = validate_tenant(organization_id)
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.status == "dead_letter")

            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)

            if older_than_days is not None:
                from datetime import timedelta

                cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
                query = query.filter(JobModel.completed_at < cutoff)

            deleted = query.delete(synchronize_session=False)
            session.commit()
            return deleted  # type: ignore[no-any-return]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


# Singleton instance
_job_repository: JobRepository | None = None


def get_job_repository(db_path: str | None = None) -> JobRepository:
    """Get or create job repository singleton.

    Args:
        db_path: Path to SQLite database. Required on first call.

    Returns:
        JobRepository instance.

    Raises:
        ValueError: If db_path not provided on first call.
    """
    global _job_repository
    if _job_repository is None:
        if db_path is None:
            raise ValueError("db_path is required on first call")
        _job_repository = JobRepository(db_path)
    return _job_repository


def reset_job_repository() -> None:
    """Reset job repository singleton. For testing."""
    global _job_repository
    _job_repository = None
