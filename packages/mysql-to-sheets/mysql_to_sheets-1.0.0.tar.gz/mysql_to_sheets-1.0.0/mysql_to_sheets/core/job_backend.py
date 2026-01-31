"""Abstract base class for job queue backends.

Defines the interface that all job queue backends must implement,
allowing for pluggable storage backends (SQLite, Redis, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any

from mysql_to_sheets.models.jobs import Job


class JobQueueBackend(ABC):
    """Abstract base class for job queue storage backends.

    All job queue backends must implement these methods to provide
    consistent job storage and retrieval semantics.
    """

    @abstractmethod
    def create(self, job: Job) -> Job:
        """Create a new job.

        Args:
            job: Job to create (id will be assigned).

        Returns:
            Created job with assigned ID.

        Raises:
            ValueError: If job validation fails.
        """
        pass

    @abstractmethod
    def get_by_id(
        self,
        job_id: int,
        organization_id: int | None = None,
    ) -> Job | None:
        """Get a job by ID.

        Args:
            job_id: Job ID to retrieve.
            organization_id: Optional org filter for multi-tenant isolation.

        Returns:
            Job if found, None otherwise.
        """
        pass

    @abstractmethod
    def get_next_pending(self, worker_id: str | None = None) -> Job | None:
        """Get and claim the next pending job.

        Atomically claims a job to prevent race conditions between workers.
        Jobs are prioritized by priority (higher first) then created_at (older first).

        Args:
            worker_id: Optional worker ID to associate with the claimed job.

        Returns:
            Claimed job if available, None otherwise.
        """
        pass

    @abstractmethod
    def claim_job(self, job_id: int, worker_id: str | None = None) -> Job | None:
        """Attempt to claim a specific pending job.

        Args:
            job_id: ID of job to claim.
            worker_id: Optional worker ID to associate with the job.

        Returns:
            Claimed job if successful, None if not available.
        """
        pass

    @abstractmethod
    def complete(self, job_id: int, result: dict[str, Any]) -> bool:
        """Mark a job as completed.

        Args:
            job_id: Job ID.
            result: Result data from job execution.

        Returns:
            True if updated, False if job not found or not running.
        """
        pass

    @abstractmethod
    def fail(self, job_id: int, error: str, requeue: bool = True) -> bool:
        """Mark a job as failed.

        Args:
            job_id: Job ID.
            error: Error message.
            requeue: If True and retries available, requeue as pending.

        Returns:
            True if updated, False if job not found or not running.
        """
        pass

    @abstractmethod
    def cancel(self, job_id: int, organization_id: int) -> bool:
        """Cancel a pending job.

        Args:
            job_id: Job ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            True if cancelled, False if not found or not pending.
        """
        pass

    @abstractmethod
    def retry(self, job_id: int, organization_id: int) -> Job | None:
        """Retry a failed job.

        Args:
            job_id: Job ID.
            organization_id: Organization ID for multi-tenant isolation.

        Returns:
            Retried job if successful, None if not found or not failed.
        """
        pass

    @abstractmethod
    def release_job(self, job_id: int) -> bool:
        """Release a running job back to pending state.

        Used for graceful shutdown when a worker needs to release
        a job it was processing.

        Args:
            job_id: Job ID to release.

        Returns:
            True if released, False if not found or not running.
        """
        pass

    @abstractmethod
    def heartbeat(self, job_id: int, worker_id: str) -> bool:
        """Update heartbeat timestamp for a running job.

        Args:
            job_id: Job ID.
            worker_id: Worker ID that is processing the job.

        Returns:
            True if updated, False if job not found or not running.
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def count(
        self,
        organization_id: int | None = None,
        status: str | None = None,
    ) -> int:
        """Count jobs matching criteria.

        Args:
            organization_id: Optional organization filter.
            status: Optional status filter.

        Returns:
            Number of matching jobs.
        """
        pass

    @abstractmethod
    def cleanup_stale(
        self,
        timeout_seconds: int = 300,
        steal_for_worker: str | None = None,
    ) -> int:
        """Clean up stale running jobs.

        Marks jobs as failed (or requeues) if they've been running longer
        than timeout or if their worker hasn't sent a heartbeat.

        Args:
            timeout_seconds: Maximum runtime before considering stale.
            steal_for_worker: If provided, reassign stale jobs to this worker
                instead of marking them as failed.

        Returns:
            Number of jobs cleaned up.
        """
        pass

    @abstractmethod
    def delete_old(self, days: int = 30) -> int:
        """Delete old completed/failed/cancelled jobs.

        Args:
            days: Number of days to retain.

        Returns:
            Number of jobs deleted.
        """
        pass

    def get_stats(self, organization_id: int | None = None) -> dict[str, int]:
        """Get queue statistics.

        Args:
            organization_id: Optional organization filter.

        Returns:
            Dictionary with counts by status.
        """
        return {
            "pending": self.count(organization_id=organization_id, status="pending"),
            "running": self.count(organization_id=organization_id, status="running"),
            "completed": self.count(organization_id=organization_id, status="completed"),
            "failed": self.count(organization_id=organization_id, status="failed"),
            "cancelled": self.count(organization_id=organization_id, status="cancelled"),
        }
