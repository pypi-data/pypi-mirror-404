"""SQLite-based job queue backend.

Provides a SQLite implementation of the JobQueueBackend interface,
wrapping the existing JobRepository for backward compatibility.
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from mysql_to_sheets.core.job_backend import JobQueueBackend
from mysql_to_sheets.core.metadata_db import get_engine_for_jobs
from mysql_to_sheets.models.jobs import (
    Base,
    Job,
    JobModel,
)

logger = logging.getLogger(__name__)


class SQLiteJobQueue(JobQueueBackend):
    """SQLite-based job queue backend.

    Uses SQLAlchemy with SQLite for job storage. Provides atomic
    operations via database transactions.

    Attributes:
        db_path: Path to SQLite database file.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize SQLite job queue.

        Args:
            db_path: Path to SQLite database file.
        """
        self._db_path = db_path
        self._engine = get_engine_for_jobs(db_path=db_path)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    @property
    def db_path(self) -> str:
        """Get the database path."""
        return self._db_path

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def create(self, job: Job) -> Job:
        """Create a new job."""
        errors = job.validate()
        if errors:
            raise ValueError(f"Invalid job: {', '.join(errors)}")

        session = self._get_session()
        try:
            model = JobModel.from_dataclass(job)
            session.add(model)
            session.commit()
            return model.to_dataclass()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(
        self,
        job_id: int,
        organization_id: int | None = None,
    ) -> Job | None:
        """Get a job by ID."""
        session = self._get_session()
        try:
            query = session.query(JobModel).filter(JobModel.id == job_id)
            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)
            model = query.first()
            return model.to_dataclass() if model else None
        finally:
            session.close()

    def get_next_pending(self, worker_id: str | None = None) -> Job | None:
        """Get and claim the next pending job."""
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
            model.status = "running"  # type: ignore[assignment]
            model.started_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            model.attempts += 1  # type: ignore[assignment]
            if worker_id:
                model.worker_id = worker_id  # type: ignore[assignment]
            model.heartbeat_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()

            return model.to_dataclass()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def claim_job(self, job_id: int, worker_id: str | None = None) -> Job | None:
        """Attempt to claim a specific job atomically.

        Uses BEGIN IMMEDIATE to acquire a write lock before the
        SELECT+UPDATE, preventing two workers from claiming the same job.
        """
        session = self._get_session()
        try:
            # Acquire exclusive write lock before reading
            session.execute(text("BEGIN IMMEDIATE"))

            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.status == "pending",
                )
                .with_for_update()
                .first()
            )

            if not model:
                session.rollback()
                return None

            model.status = "running"  # type: ignore[assignment]
            model.started_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            model.attempts += 1  # type: ignore[assignment]
            if worker_id:
                model.worker_id = worker_id  # type: ignore[assignment]
            model.heartbeat_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()

            return model.to_dataclass()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def complete(self, job_id: int, result: dict[str, Any]) -> bool:
        """Mark a job as completed."""
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

            model.status = "completed"  # type: ignore[assignment]
            model.result = json.dumps(result)  # type: ignore[assignment]
            model.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def fail(self, job_id: int, error: str, requeue: bool = True) -> bool:
        """Mark a job as failed."""
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

            model.error = error  # type: ignore[assignment]
            model.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]

            # Requeue if retries available
            if requeue and model.attempts < model.max_attempts:
                model.status = "pending"  # type: ignore[assignment]
                model.started_at = None  # type: ignore[assignment]
                model.completed_at = None  # type: ignore[assignment]
                model.worker_id = None  # type: ignore[assignment]
                model.heartbeat_at = None  # type: ignore[assignment]
            else:
                model.status = "failed"  # type: ignore[assignment]

            session.commit()
            return True
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def cancel(self, job_id: int, organization_id: int) -> bool:
        """Cancel a pending job."""
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

            model.status = "cancelled"  # type: ignore[assignment]
            model.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def retry(self, job_id: int, organization_id: int) -> Job | None:
        """Retry a failed job."""
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

            model.status = "pending"  # type: ignore[assignment]
            model.error = None  # type: ignore[assignment]
            model.started_at = None  # type: ignore[assignment]
            model.completed_at = None  # type: ignore[assignment]
            model.attempts = 0  # type: ignore[assignment]
            model.worker_id = None  # type: ignore[assignment]
            model.heartbeat_at = None  # type: ignore[assignment]
            session.commit()
            return model.to_dataclass()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def release_job(self, job_id: int) -> bool:
        """Release a running job back to pending state."""
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

            model.status = "pending"  # type: ignore[assignment]
            model.started_at = None  # type: ignore[assignment]
            model.worker_id = None  # type: ignore[assignment]
            model.heartbeat_at = None  # type: ignore[assignment]
            session.commit()

            logger.debug(f"Released job {job_id} back to pending")
            return True
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def heartbeat(self, job_id: int, worker_id: str) -> bool:
        """Update heartbeat timestamp for a running job."""
        session = self._get_session()
        try:
            model = (
                session.query(JobModel)
                .filter(
                    JobModel.id == job_id,
                    JobModel.status == "running",
                    JobModel.worker_id == worker_id,
                )
                .first()
            )
            if not model:
                return False

            model.heartbeat_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            session.commit()
            return True
        except (SQLAlchemyError, ValueError):
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
        """Get all jobs in an organization."""
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
        """Count jobs matching criteria."""
        session = self._get_session()
        try:
            query = session.query(JobModel)

            if organization_id is not None:
                query = query.filter(JobModel.organization_id == organization_id)
            if status:
                query = query.filter(JobModel.status == status)

            count = query.count()
            return count if count is not None else 0
        finally:
            session.close()

    def cleanup_stale(
        self,
        timeout_seconds: int = 300,
        steal_for_worker: str | None = None,
    ) -> int:
        """Clean up stale running jobs."""
        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(seconds=timeout_seconds)

            # Find stale jobs by heartbeat (if set) or started_at
            stale_jobs = (
                session.query(JobModel)
                .filter(
                    JobModel.status == "running",
                )
                .all()
            )

            count = 0
            for model in stale_jobs:
                # Check heartbeat first, then started_at
                last_seen = model.heartbeat_at or model.started_at
                # Ensure last_seen is timezone-aware (assume UTC if naive)
                if last_seen and last_seen.tzinfo is None:
                    last_seen = last_seen.replace(tzinfo=timezone.utc)
                if last_seen and last_seen < cutoff:
                    if steal_for_worker:
                        model.worker_id = steal_for_worker  # type: ignore[assignment]
                        model.heartbeat_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                    elif model.attempts < model.max_attempts:
                        # Release back to pending
                        model.status = "pending"  # type: ignore[assignment]
                        model.started_at = None  # type: ignore[assignment]
                        model.worker_id = None  # type: ignore[assignment]
                        model.heartbeat_at = None  # type: ignore[assignment]
                    else:
                        model.status = "failed"  # type: ignore[assignment]
                        model.error = f"Job timed out after {timeout_seconds} seconds"  # type: ignore[assignment]
                        model.completed_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                    count += 1

            session.commit()
            return count
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def delete_old(self, days: int = 30) -> int:
        """Delete old completed/failed/cancelled jobs."""
        session = self._get_session()
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=days)

            deleted = (
                session.query(JobModel)
                .filter(
                    JobModel.status.in_(["completed", "failed", "cancelled"]),
                    JobModel.completed_at < cutoff,
                )
                .delete(synchronize_session=False)
            )

            session.commit()
            return deleted if deleted is not None else 0
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()
