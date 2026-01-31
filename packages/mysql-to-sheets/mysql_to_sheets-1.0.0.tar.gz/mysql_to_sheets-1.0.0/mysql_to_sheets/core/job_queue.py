"""Job queue service for async task processing.

Provides functions to enqueue, claim, and manage jobs. Uses SQLite
for persistence with atomic operations to prevent race conditions.
"""

import logging
from typing import Any

from mysql_to_sheets.models.jobs import (
    Job,
    get_job_repository,
    reset_job_repository,
)

logger = logging.getLogger(__name__)


def enqueue_job(
    job_type: str,
    payload: dict[str, Any],
    organization_id: int,
    user_id: int | None = None,
    priority: int = 0,
    max_attempts: int | None = None,
    db_path: str | None = None,
) -> Job:
    """Enqueue a new job for async processing.

    Args:
        job_type: Type of job ("sync", "export").
        payload: Job payload data.
        organization_id: Organization ID for multi-tenant isolation.
        user_id: Optional user who created the job.
        priority: Job priority (higher = processed first).
        max_attempts: Maximum retry attempts (default from config).
        db_path: Path to jobs database.

    Returns:
        Created job with ID.

    Raises:
        ValueError: If validation fails.
    """
    if max_attempts is None:
        from mysql_to_sheets.core.config import get_config

        config = get_config()
        max_attempts = config.job_max_attempts

    job = Job(
        organization_id=organization_id,
        user_id=user_id,
        job_type=job_type,
        payload=payload,
        priority=priority,
        max_attempts=max_attempts,
    )

    repo = get_job_repository(db_path)
    created_job = repo.create(job)

    logger.info(
        f"Enqueued job {created_job.id} (type={job_type}, org={organization_id}, "
        f"priority={priority})"
    )

    return created_job


def get_next_job(db_path: str | None = None) -> Job | None:
    """Get and claim the next pending job.

    Uses atomic claim to prevent race conditions between workers.

    Args:
        db_path: Path to jobs database.

    Returns:
        Claimed job if available, None otherwise.
    """
    repo = get_job_repository(db_path)
    job = repo.get_next_pending()

    if job:
        logger.debug(f"Claimed job {job.id} (type={job.job_type}, attempt={job.attempts})")

    return job


def complete_job(
    job_id: int,
    result: dict[str, Any],
    db_path: str | None = None,
) -> bool:
    """Mark a job as completed.

    Args:
        job_id: Job ID.
        result: Result data from job execution.
        db_path: Path to jobs database.

    Returns:
        True if updated, False if job not found or not running.
    """
    repo = get_job_repository(db_path)
    success = repo.complete(job_id, result)

    if success:
        logger.info(f"Completed job {job_id}")
    else:
        logger.warning(f"Failed to complete job {job_id} - not found or not running")

    return success


def fail_job(
    job_id: int,
    error: str,
    requeue: bool = True,
    move_to_dlq: bool = True,
    db_path: str | None = None,
) -> bool:
    """Mark a job as failed.

    Args:
        job_id: Job ID.
        error: Error message.
        requeue: Whether to requeue if retries available.
        move_to_dlq: Move to dead letter queue when max attempts exhausted.
        db_path: Path to jobs database.

    Returns:
        True if updated, False if job not found or not running.
    """
    repo = get_job_repository(db_path)
    success = repo.fail(job_id, error, requeue=requeue, move_to_dlq=move_to_dlq)

    if success:
        job = repo.get_by_id(job_id)
        if job and job.status == "pending":
            logger.info(f"Requeued job {job_id} (attempt {job.attempts}/{job.max_attempts})")
        else:
            logger.error(f"Failed job {job_id}: {error}")
    else:
        logger.warning(f"Failed to fail job {job_id} - not found or not running")

    return success


def cancel_job(
    job_id: int,
    organization_id: int,
    db_path: str | None = None,
) -> bool:
    """Cancel a pending job.

    Args:
        job_id: Job ID.
        organization_id: Organization ID for multi-tenant isolation.
        db_path: Path to jobs database.

    Returns:
        True if cancelled, False if not found or not pending.
    """
    repo = get_job_repository(db_path)
    success = repo.cancel(job_id, organization_id)

    if success:
        logger.info(f"Cancelled job {job_id}")
    else:
        logger.warning(f"Failed to cancel job {job_id} - not found or not pending")

    return success


def retry_job(
    job_id: int,
    organization_id: int,
    db_path: str | None = None,
) -> Job | None:
    """Retry a failed job.

    Args:
        job_id: Job ID.
        organization_id: Organization ID for multi-tenant isolation.
        db_path: Path to jobs database.

    Returns:
        Retried job if successful, None if not found or not failed.
    """
    repo = get_job_repository(db_path)
    job = repo.retry(job_id, organization_id)

    if job:
        logger.info(f"Retried job {job_id}")
    else:
        logger.warning(f"Failed to retry job {job_id} - not found or not failed")

    return job


def get_job_status(
    job_id: int,
    organization_id: int | None = None,
    db_path: str | None = None,
) -> Job | None:
    """Get job status.

    Args:
        job_id: Job ID.
        organization_id: Optional organization ID for multi-tenant isolation.
        db_path: Path to jobs database.

    Returns:
        Job if found, None otherwise.
    """
    repo = get_job_repository(db_path)
    return repo.get_by_id(job_id, organization_id)


def list_jobs(
    organization_id: int,
    status: str | None = None,
    job_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db_path: str | None = None,
) -> list[Job]:
    """List jobs for an organization.

    Args:
        organization_id: Organization ID.
        status: Optional status filter.
        job_type: Optional job type filter.
        limit: Maximum number of results.
        offset: Number of results to skip.
        db_path: Path to jobs database.

    Returns:
        List of jobs.
    """
    repo = get_job_repository(db_path)
    return repo.get_all(
        organization_id=organization_id,
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )


def count_jobs(
    organization_id: int | None = None,
    status: str | None = None,
    db_path: str | None = None,
) -> int:
    """Count jobs.

    Args:
        organization_id: Optional organization filter.
        status: Optional status filter.
        db_path: Path to jobs database.

    Returns:
        Number of jobs matching criteria.
    """
    repo = get_job_repository(db_path)
    return repo.count(organization_id=organization_id, status=status)


def cleanup_stale_jobs(
    timeout_seconds: int | None = None,
    db_path: str | None = None,
) -> int:
    """Clean up stale running jobs.

    Marks jobs as failed if they've been running longer than timeout.

    Args:
        timeout_seconds: Maximum runtime before considering stale.
        db_path: Path to jobs database.

    Returns:
        Number of jobs cleaned up.
    """
    if timeout_seconds is None:
        from mysql_to_sheets.core.config import get_config

        config = get_config()
        timeout_seconds = config.job_timeout_seconds

    repo = get_job_repository(db_path)
    count = repo.cleanup_stale(timeout_seconds)

    if count > 0:
        logger.warning(f"Cleaned up {count} stale jobs (timeout={timeout_seconds}s)")

    return count


def delete_old_jobs(
    days: int = 30,
    db_path: str | None = None,
) -> int:
    """Delete old completed/failed/cancelled jobs.

    Args:
        days: Number of days to retain.
        db_path: Path to jobs database.

    Returns:
        Number of jobs deleted.
    """
    repo = get_job_repository(db_path)
    count = repo.delete_old(days)

    if count > 0:
        logger.info(f"Deleted {count} old jobs (older than {days} days)")

    return count


def get_queue_stats(
    organization_id: int | None = None,
    db_path: str | None = None,
) -> dict[str, int]:
    """Get queue statistics.

    Args:
        organization_id: Optional organization filter.
        db_path: Path to jobs database.

    Returns:
        Dictionary with counts by status.
    """
    repo = get_job_repository(db_path)

    return {
        "pending": repo.count(organization_id=organization_id, status="pending"),
        "running": repo.count(organization_id=organization_id, status="running"),
        "completed": repo.count(organization_id=organization_id, status="completed"),
        "failed": repo.count(organization_id=organization_id, status="failed"),
        "cancelled": repo.count(organization_id=organization_id, status="cancelled"),
        "dead_letter": repo.count_dead_letter(organization_id=organization_id),
    }


def reset_queue() -> None:
    """Reset job queue singleton. For testing."""
    reset_job_repository()


# Dead Letter Queue (DLQ) Operations


def list_dead_letter_jobs(
    organization_id: int | None = None,
    job_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db_path: str | None = None,
) -> list[Job]:
    """List jobs in the dead letter queue.

    Args:
        organization_id: Optional organization filter.
        job_type: Optional job type filter.
        limit: Maximum number of results.
        offset: Number of results to skip.
        db_path: Path to jobs database.

    Returns:
        List of dead letter jobs.
    """
    repo = get_job_repository(db_path)
    return repo.get_dead_letter_jobs(
        organization_id=organization_id,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )


def count_dead_letter_jobs(
    organization_id: int | None = None,
    db_path: str | None = None,
) -> int:
    """Count jobs in dead letter queue.

    Args:
        organization_id: Optional organization filter.
        db_path: Path to jobs database.

    Returns:
        Number of dead letter jobs.
    """
    repo = get_job_repository(db_path)
    return repo.count_dead_letter(organization_id=organization_id)


def retry_dead_letter_job(
    job_id: int,
    organization_id: int,
    db_path: str | None = None,
) -> Job | None:
    """Retry a job from the dead letter queue.

    Resets the job to pending status with fresh attempt counter.

    Args:
        job_id: Job ID.
        organization_id: Organization ID for multi-tenant isolation.
        db_path: Path to jobs database.

    Returns:
        Retried job if successful, None if not found or not in DLQ.
    """
    repo = get_job_repository(db_path)
    job = repo.retry_dead_letter(job_id, organization_id)

    if job:
        logger.info(f"Retried dead letter job {job_id}")
    else:
        logger.warning(f"Failed to retry dead letter job {job_id} - not found or not in DLQ")

    return job


def purge_dead_letter_queue(
    organization_id: int | None = None,
    older_than_days: int | None = None,
    db_path: str | None = None,
) -> int:
    """Purge jobs from the dead letter queue.

    Args:
        organization_id: Optional organization filter.
        older_than_days: Only purge jobs older than this many days.
        db_path: Path to jobs database.

    Returns:
        Number of jobs purged.
    """
    repo = get_job_repository(db_path)
    count = repo.purge_dead_letter(
        organization_id=organization_id,
        older_than_days=older_than_days,
    )

    if count > 0:
        logger.info(f"Purged {count} dead letter job(s)")

    return count
