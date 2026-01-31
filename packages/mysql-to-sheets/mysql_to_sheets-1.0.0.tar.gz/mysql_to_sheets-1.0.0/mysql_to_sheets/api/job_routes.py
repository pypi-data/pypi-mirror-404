"""FastAPI routes for job queue management.

Provides REST API endpoints for managing async jobs.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    get_current_user,
)
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.job_queue import (
    cancel_job,
    count_dead_letter_jobs,
    enqueue_job,
    get_job_status,
    get_queue_stats,
    list_dead_letter_jobs,
    list_jobs,
    purge_dead_letter_queue,
    retry_dead_letter_job,
    retry_job,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.jobs import VALID_JOB_STATUSES, VALID_JOB_TYPES
from mysql_to_sheets.models.users import User

logger = logging.getLogger("mysql_to_sheets.api.jobs")

router = APIRouter(prefix="/jobs", tags=["jobs"])


# Request/Response models
class JobResponse(BaseModel):
    """Response model for a single job."""

    id: int
    organization_id: int
    user_id: int | None
    job_type: str
    status: str
    priority: int
    payload: dict[str, Any]
    result: dict[str, Any] | None
    error: str | None
    created_at: str | None
    started_at: str | None
    completed_at: str | None
    attempts: int
    max_attempts: int


class JobListResponse(BaseModel):
    """Response model for job list."""

    success: bool = True
    jobs: list[JobResponse]
    count: int


class JobCreateRequest(BaseModel):
    """Request model for creating a job."""

    job_type: str = Field(description="Job type (sync, export)")
    payload: dict[str, Any] = Field(description="Job payload data")
    priority: int = Field(default=0, ge=0, description="Job priority (higher = first)")


class JobCreateResponse(BaseModel):
    """Response model for job creation."""

    success: bool = True
    job_id: int
    message: str


class JobStatusResponse(BaseModel):
    """Response model for job status."""

    success: bool = True
    job: JobResponse


class JobCancelResponse(BaseModel):
    """Response model for job cancellation."""

    success: bool = True
    message: str


class JobRetryResponse(BaseModel):
    """Response model for job retry."""

    success: bool = True
    message: str
    job: JobResponse | None = None


class QueueStatsResponse(BaseModel):
    """Response model for queue statistics."""

    success: bool = True
    pending: int
    running: int
    completed: int
    failed: int
    cancelled: int
    dead_letter: int = 0
    total: int


class DLQPurgeRequest(BaseModel):
    """Request model for DLQ purge."""

    older_than_days: int | None = Field(
        default=None,
        ge=1,
        description="Only purge jobs older than this many days",
    )


class DLQPurgeResponse(BaseModel):
    """Response model for DLQ purge."""

    success: bool = True
    purged_count: int
    message: str


@router.post("", response_model=JobCreateResponse, status_code=201)
async def create_job(
    request: JobCreateRequest,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> JobCreateResponse:
    """Create a new job.

    Enqueues a job for async processing by the job worker.
    """
    if request.job_type not in VALID_JOB_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type. Must be one of: {VALID_JOB_TYPES}",
        )

    db_path = get_tenant_db_path()
    config = get_config()

    job = enqueue_job(
        job_type=request.job_type,
        payload=request.payload,
        organization_id=organization_id,
        user_id=user.id if user else None,
        priority=request.priority,
        max_attempts=config.job_max_attempts,
        db_path=db_path,
    )

    if job.id is None:
        raise HTTPException(
            status_code=500,
            detail="Job creation failed - no job ID assigned",
        )

    return JobCreateResponse(
        job_id=job.id,
        message=f"Job {job.id} created",
    )


@router.get("", response_model=JobListResponse)
async def list_jobs_endpoint(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
    status: Annotated[
        str | None,
        Query(description="Filter by status"),
    ] = None,
    job_type: Annotated[
        str | None,
        Query(description="Filter by job type"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum results"),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0, description="Results to skip"),
    ] = 0,
) -> JobListResponse:
    """List jobs for the organization."""
    if status and status not in VALID_JOB_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {VALID_JOB_STATUSES}",
        )

    if job_type and job_type not in VALID_JOB_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type. Must be one of: {VALID_JOB_TYPES}",
        )

    db_path = get_tenant_db_path()
    jobs = list_jobs(
        organization_id=organization_id,
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset,
        db_path=db_path,
    )

    return JobListResponse(
        jobs=[JobResponse(**j.to_dict()) for j in jobs],
        count=len(jobs),
    )


@router.get("/stats", response_model=QueueStatsResponse)
async def get_stats(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> QueueStatsResponse:
    """Get queue statistics for the organization."""
    db_path = get_tenant_db_path()
    stats = get_queue_stats(organization_id=organization_id, db_path=db_path)
    dlq_count = count_dead_letter_jobs(organization_id=organization_id, db_path=db_path)

    return QueueStatsResponse(
        pending=stats["pending"],
        running=stats["running"],
        completed=stats["completed"],
        failed=stats["failed"],
        cancelled=stats["cancelled"],
        dead_letter=dlq_count,
        total=sum(stats.values()) + dlq_count,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job(
    job_id: int,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> JobStatusResponse:
    """Get status of a specific job."""
    db_path = get_tenant_db_path()
    job = get_job_status(job_id, organization_id=organization_id, db_path=db_path)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(job=JobResponse(**job.to_dict()))


@router.post("/{job_id}/cancel", response_model=JobCancelResponse)
async def cancel_job_endpoint(
    job_id: int,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> JobCancelResponse:
    """Cancel a pending job."""
    db_path = get_tenant_db_path()
    success = cancel_job(job_id, organization_id, db_path=db_path)

    if not success:
        raise HTTPException(
            status_code=400,
            detail="Job not found or not in pending status",
        )

    return JobCancelResponse(message=f"Job {job_id} cancelled")


@router.post("/{job_id}/retry", response_model=JobRetryResponse)
async def retry_job_endpoint(
    job_id: int,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> JobRetryResponse:
    """Retry a failed job."""
    db_path = get_tenant_db_path()
    job = retry_job(job_id, organization_id, db_path=db_path)

    if not job:
        raise HTTPException(
            status_code=400,
            detail="Job not found or not in failed status",
        )

    return JobRetryResponse(
        message=f"Job {job_id} requeued for retry",
        job=JobResponse(**job.to_dict()),
    )


# Dead Letter Queue endpoints


@router.get("/dlq", response_model=JobListResponse)
async def list_dlq_jobs(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
    job_type: Annotated[
        str | None,
        Query(description="Filter by job type"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum results"),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0, description="Results to skip"),
    ] = 0,
) -> JobListResponse:
    """List jobs in the dead letter queue.

    Dead letter jobs are those that have exceeded max retry attempts
    and are no longer being processed.
    """
    if job_type and job_type not in VALID_JOB_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type. Must be one of: {VALID_JOB_TYPES}",
        )

    db_path = get_tenant_db_path()
    jobs = list_dead_letter_jobs(
        organization_id=organization_id,
        job_type=job_type,
        limit=limit,
        offset=offset,
        db_path=db_path,
    )

    return JobListResponse(
        jobs=[JobResponse(**j.to_dict()) for j in jobs],
        count=len(jobs),
    )


@router.post("/{job_id}/retry-dlq", response_model=JobRetryResponse)
async def retry_dlq_job(
    job_id: int,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> JobRetryResponse:
    """Retry a job from the dead letter queue.

    Resets the job to pending status with fresh attempt count.
    """
    db_path = get_tenant_db_path()
    job = retry_dead_letter_job(job_id, organization_id, db_path=db_path)

    if not job:
        raise HTTPException(
            status_code=400,
            detail="Job not found or not in dead_letter status",
        )

    return JobRetryResponse(
        message=f"Dead letter job {job_id} requeued for retry",
        job=JobResponse(**job.to_dict()),
    )


@router.post("/dlq/purge", response_model=DLQPurgeResponse)
async def purge_dlq(
    request: DLQPurgeRequest,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> DLQPurgeResponse:
    """Purge jobs from the dead letter queue.

    Permanently deletes dead letter jobs. Use older_than_days to only
    purge jobs older than a certain age.
    """
    db_path = get_tenant_db_path()
    purged = purge_dead_letter_queue(
        organization_id=organization_id,
        older_than_days=request.older_than_days,
        db_path=db_path,
    )

    message = f"Purged {purged} dead letter job(s)"
    if request.older_than_days:
        message += f" older than {request.older_than_days} days"

    return DLQPurgeResponse(
        purged_count=purged,
        message=message,
    )
