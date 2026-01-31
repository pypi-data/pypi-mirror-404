"""Repository for scheduled job persistence.

This module provides CRUD operations for scheduled jobs with
SQLite backend.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from mysql_to_sheets.core.scheduler.models import ScheduledJob
from mysql_to_sheets.models.schedules import Base, ScheduledJobModel


class ScheduleRepository(ABC):
    """Abstract base class for schedule repositories."""

    @abstractmethod
    def create(self, job: ScheduledJob) -> ScheduledJob:
        """Create a new scheduled job."""
        pass

    @abstractmethod
    def get_by_id(self, job_id: int) -> ScheduledJob | None:
        """Get a job by ID."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> ScheduledJob | None:
        """Get a job by name."""
        pass

    @abstractmethod
    def get_all(self, include_disabled: bool = False) -> list[ScheduledJob]:
        """Get all jobs."""
        pass

    @abstractmethod
    def update(self, job: ScheduledJob) -> ScheduledJob:
        """Update a job."""
        pass

    @abstractmethod
    def delete(self, job_id: int) -> bool:
        """Delete a job."""
        pass

    @abstractmethod
    def update_last_run(
        self,
        job_id: int,
        success: bool,
        message: str | None = None,
        rows: int | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Update job's last run information."""
        pass

    @abstractmethod
    def update_next_run(self, job_id: int, next_run_at: datetime | None) -> None:
        """Update job's next run time."""
        pass


class SQLiteScheduleRepository(ScheduleRepository):
    """SQLite-backed schedule repository.

    Provides persistent storage for scheduled jobs.
    """

    def __init__(self, db_path: str) -> None:
        """Initialize repository.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self._engine = create_engine(f"sqlite:///{db_path}", echo=False)
        Base.metadata.create_all(self._engine)
        self._session_factory = sessionmaker(bind=self._engine)

    def _get_session(self) -> Session:
        """Get a new database session."""
        return self._session_factory()

    def _model_to_job(self, model: ScheduledJobModel) -> ScheduledJob:
        """Convert SQLAlchemy model to dataclass.

        Args:
            model: SQLAlchemy model instance.

        Returns:
            ScheduledJob dataclass instance.
        """
        return ScheduledJob(
            id=model.id,  # type: ignore[arg-type]
            name=model.name,  # type: ignore[arg-type]
            cron_expression=model.cron_expression,  # type: ignore[arg-type]
            interval_minutes=model.interval_minutes,  # type: ignore[arg-type]
            sheet_id=model.sheet_id,  # type: ignore[arg-type]
            worksheet_name=model.worksheet_name,  # type: ignore[arg-type]
            sql_query=model.sql_query,  # type: ignore[arg-type]
            notify_on_success=model.notify_on_success,  # type: ignore[arg-type]
            notify_on_failure=model.notify_on_failure,  # type: ignore[arg-type]
            enabled=model.enabled,  # type: ignore[arg-type]
            created_at=model.created_at,  # type: ignore[arg-type]
            updated_at=model.updated_at,  # type: ignore[arg-type]
            last_run_at=model.last_run_at,  # type: ignore[arg-type]
            last_run_success=model.last_run_success,  # type: ignore[arg-type]
            last_run_message=model.last_run_message,  # type: ignore[arg-type]
            last_run_rows=model.last_run_rows,  # type: ignore[arg-type]
            last_run_duration_ms=model.last_run_duration_ms,  # type: ignore[arg-type]
            next_run_at=model.next_run_at,  # type: ignore[arg-type]
        )

    def _job_to_model(self, job: ScheduledJob) -> ScheduledJobModel:
        """Convert dataclass to SQLAlchemy model.

        Args:
            job: ScheduledJob dataclass instance.

        Returns:
            SQLAlchemy model instance.
        """
        return ScheduledJobModel(
            id=job.id,
            name=job.name,
            cron_expression=job.cron_expression,
            interval_minutes=job.interval_minutes,
            sheet_id=job.sheet_id,
            worksheet_name=job.worksheet_name,
            sql_query=job.sql_query,
            notify_on_success=job.notify_on_success,
            notify_on_failure=job.notify_on_failure,
            enabled=job.enabled,
            created_at=job.created_at,
            updated_at=job.updated_at,
            last_run_at=job.last_run_at,
            last_run_success=job.last_run_success,
            last_run_message=job.last_run_message,
            last_run_rows=job.last_run_rows,
            last_run_duration_ms=job.last_run_duration_ms,
            next_run_at=job.next_run_at,
        )

    def create(self, job: ScheduledJob) -> ScheduledJob:
        """Create a new scheduled job.

        Args:
            job: Job to create.

        Returns:
            Created job with ID assigned.
        """
        session = self._get_session()
        try:
            model = self._job_to_model(job)
            model.id = None  # type: ignore[assignment]  # Ensure we create new
            session.add(model)
            session.commit()
            session.refresh(model)
            return self._model_to_job(model)
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def get_by_id(self, job_id: int) -> ScheduledJob | None:
        """Get a job by ID.

        Args:
            job_id: Job ID.

        Returns:
            ScheduledJob if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = session.query(ScheduledJobModel).filter_by(id=job_id).first()
            if model is None:
                return None
            return self._model_to_job(model)
        finally:
            session.close()

    def get_by_name(self, name: str) -> ScheduledJob | None:
        """Get a job by name.

        Args:
            name: Job name.

        Returns:
            ScheduledJob if found, None otherwise.
        """
        session = self._get_session()
        try:
            model = session.query(ScheduledJobModel).filter_by(name=name).first()
            if model is None:
                return None
            return self._model_to_job(model)
        finally:
            session.close()

    def get_all(self, include_disabled: bool = False) -> list[ScheduledJob]:
        """Get all jobs.

        Args:
            include_disabled: Whether to include disabled jobs.

        Returns:
            List of scheduled jobs.
        """
        session = self._get_session()
        try:
            query = session.query(ScheduledJobModel)
            if not include_disabled:
                query = query.filter_by(enabled=True)
            models = query.order_by(ScheduledJobModel.name).all()
            return [self._model_to_job(m) for m in models]
        finally:
            session.close()

    def update(self, job: ScheduledJob) -> ScheduledJob:
        """Update a job.

        Args:
            job: Job with updated values.

        Returns:
            Updated job.
        """
        if job.id is None:
            raise ValueError("Cannot update job without ID")

        session = self._get_session()
        try:
            model = session.query(ScheduledJobModel).filter_by(id=job.id).first()
            if model is None:
                raise ValueError(f"Job with ID {job.id} not found")

            # Update fields
            model.name = job.name  # type: ignore[assignment]
            model.cron_expression = job.cron_expression  # type: ignore[assignment]
            model.interval_minutes = job.interval_minutes  # type: ignore[assignment]
            model.sheet_id = job.sheet_id  # type: ignore[assignment]
            model.worksheet_name = job.worksheet_name  # type: ignore[assignment]
            model.sql_query = job.sql_query  # type: ignore[assignment]
            model.notify_on_success = job.notify_on_success  # type: ignore[assignment]
            model.notify_on_failure = job.notify_on_failure  # type: ignore[assignment]
            model.enabled = job.enabled  # type: ignore[assignment]
            model.updated_at = datetime.now(timezone.utc)  # type: ignore[assignment]
            model.next_run_at = job.next_run_at  # type: ignore[assignment]

            session.commit()
            session.refresh(model)
            return self._model_to_job(model)
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, job_id: int) -> bool:
        """Delete a job.

        Args:
            job_id: Job ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        session = self._get_session()
        try:
            result = session.query(ScheduledJobModel).filter_by(id=job_id).delete()
            session.commit()
            return bool(result and result > 0)
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def update_last_run(
        self,
        job_id: int,
        success: bool,
        message: str | None = None,
        rows: int | None = None,
        duration_ms: float | None = None,
    ) -> None:
        """Update job's last run information.

        Args:
            job_id: Job ID.
            success: Whether the run succeeded.
            message: Status message.
            rows: Rows synced.
            duration_ms: Duration in milliseconds.
        """
        session = self._get_session()
        try:
            model = session.query(ScheduledJobModel).filter_by(id=job_id).first()
            if model:
                model.last_run_at = datetime.now(timezone.utc)  # type: ignore[assignment]
                model.last_run_success = success  # type: ignore[assignment]
                model.last_run_message = message  # type: ignore[assignment]
                model.last_run_rows = rows  # type: ignore[assignment]
                model.last_run_duration_ms = duration_ms  # type: ignore[assignment]
                session.commit()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def update_next_run(self, job_id: int, next_run_at: datetime | None) -> None:
        """Update job's next run time.

        Args:
            job_id: Job ID.
            next_run_at: Next scheduled run time.
        """
        session = self._get_session()
        try:
            model = session.query(ScheduledJobModel).filter_by(id=job_id).first()
            if model:
                model.next_run_at = next_run_at  # type: ignore[assignment]
                session.commit()
        except (SQLAlchemyError, ValueError):
            session.rollback()
            raise
        finally:
            session.close()

    def count(self, include_disabled: bool = False) -> int:
        """Get total number of jobs.

        Args:
            include_disabled: Whether to count disabled jobs.

        Returns:
            Total count.
        """
        session = self._get_session()
        try:
            query = session.query(ScheduledJobModel)
            if not include_disabled:
                query = query.filter_by(enabled=True)
            count = query.count()
            return count if count is not None else 0
        finally:
            session.close()


# Singleton instance
_repository: SQLiteScheduleRepository | None = None


def get_schedule_repository(db_path: str | None = None) -> SQLiteScheduleRepository:
    """Get the schedule repository singleton.

    Args:
        db_path: Path to SQLite database. If None, uses default.

    Returns:
        SQLiteScheduleRepository instance.
    """
    global _repository
    if _repository is None:
        if db_path is None:
            from mysql_to_sheets.core.config import get_config

            db_path = get_config().scheduler_db_path
        _repository = SQLiteScheduleRepository(db_path)
    return _repository


def reset_schedule_repository() -> None:
    """Reset the repository singleton.

    Useful for testing.
    """
    global _repository
    _repository = None
