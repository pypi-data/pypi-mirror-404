"""API routes for MySQL to Google Sheets sync."""

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response

from mysql_to_sheets.api.schemas import (
    CheckpointResponse,
    DeepHealthResponse,
    DiffResponse,
    ErrorResponse,
    ErrorStatsResponse,
    HealthResponse,
    HistoryEntryResponse,
    HistoryResponse,
    NotificationStatusResponse,
    NotificationTestRequest,
    NotificationTestResponse,
    ResumeSyncResponse,
    ScheduleCreateRequest,
    ScheduleListResponse,
    ScheduleResponse,
    ScheduleUpdateRequest,
    SyncRequest,
    SyncResponse,
    ValidateRequest,
    ValidateResponse,
)
from mysql_to_sheets.core.config import get_config, reset_config
from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError
from mysql_to_sheets.core.history import (
    get_history_repository,
)
from mysql_to_sheets.core.metrics import get_registry
from mysql_to_sheets.core.sync import SyncService, run_sync

router = APIRouter()


# Dependency for optional API key authentication
async def verify_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> str | None:
    """Verify API key header for optional per-route authentication.

    Args:
        x_api_key: API key from header.

    Returns:
        The API key if provided, None otherwise.
    """
    return x_api_key


# Endpoints


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running and healthy.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()


@router.get(
    "/health/deep",
    response_model=DeepHealthResponse,
    summary="Deep health check",
    description="Check API and dependency health (database, file system).",
)
async def deep_health_check() -> DeepHealthResponse:
    """Deep health check that verifies database connectivity."""
    import os

    from mysql_to_sheets.core.tenant import get_tenant_db_path

    checks: dict[str, dict[str, Any]] = {}

    # Check tenant database
    try:
        db_path = get_tenant_db_path()
        db_exists = os.path.exists(db_path) if db_path else False

        if db_exists:
            from sqlalchemy import create_engine, text

            engine = create_engine(f"sqlite:///{db_path}", echo=False)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))

            checks["database"] = {
                "status": "healthy",
                "path": db_path,
            }
        else:
            checks["database"] = {
                "status": "healthy",
                "message": "Database not yet initialized",
                "path": db_path,
            }
    except Exception as e:
        checks["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check data directory writable
    try:
        data_dir = os.path.dirname(get_tenant_db_path()) or "./data"
        os.makedirs(data_dir, exist_ok=True)
        test_file = os.path.join(data_dir, ".health_check")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        checks["filesystem"] = {
            "status": "healthy",
            "writable": True,
            "path": data_dir,
        }
    except Exception as e:
        checks["filesystem"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check webhook delivery health
    try:
        from mysql_to_sheets.core.webhooks.alerts import get_webhook_failure_tracker

        tracker = get_webhook_failure_tracker()
        webhook_health = tracker.get_health_summary()

        if webhook_health["alerting"] > 0:
            checks["webhooks"] = {
                "status": "degraded",
                **webhook_health,
            }
        elif webhook_health["unhealthy"] > 0:
            checks["webhooks"] = {
                "status": "warning",
                **webhook_health,
            }
        else:
            checks["webhooks"] = {
                "status": "healthy",
                **webhook_health,
            }
    except Exception as e:
        checks["webhooks"] = {
            "status": "unknown",
            "error": str(e),
        }

    # Determine overall status
    overall_status = "healthy"
    for check in checks.values():
        check_status = check.get("status")
        if check_status == "unhealthy":
            overall_status = "degraded"
            break
        elif check_status == "degraded" and overall_status == "healthy":
            overall_status = "degraded"
        elif check_status == "warning" and overall_status == "healthy":
            overall_status = "warning"

    return DeepHealthResponse(
        status=overall_status,
        checks=checks,
    )


@router.get(
    "/errors/stats",
    response_model=ErrorStatsResponse,
    summary="Get error statistics",
    description="Get error statistics for the last N hours.",
)
async def get_error_stats(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
) -> ErrorStatsResponse:
    """Get error statistics."""
    registry = get_registry()

    errors_by_category: dict[str, int] = {}
    errors_by_code: dict[str, int] = {}
    total_errors = 0

    with registry._lock:
        for key, counter in registry._counters.items():
            if "mysql_to_sheets_errors_total" in counter.name:
                count = int(counter.value)
                total_errors += count

                if counter.labels:
                    category = counter.labels.get("category")
                    code = counter.labels.get("code")
                    if category:
                        errors_by_category[category] = errors_by_category.get(category, 0) + count
                    if code:
                        errors_by_code[code] = errors_by_code.get(code, 0) + count

    retry_attempts = 0
    retry_successes = 0
    with registry._lock:
        for key, counter in registry._counters.items():
            if "mysql_to_sheets_retry_attempts_total" in counter.name:
                retry_attempts += int(counter.value)
            if "mysql_to_sheets_retry_success_total" in counter.name:
                retry_successes += int(counter.value)

    retry_success_rate = None
    if retry_attempts > 0:
        retry_success_rate = round(retry_successes / retry_attempts, 2)

    top_codes = sorted(
        errors_by_code.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:5]

    return ErrorStatsResponse(
        total_errors_24h=total_errors,
        errors_by_category=errors_by_category,
        top_error_codes=[{"code": code, "count": count} for code, count in top_codes],
        retry_success_rate=retry_success_rate,
        hours=hours,
    )


@router.post(
    "/sync",
    response_model=SyncResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Configuration error"},
        500: {"model": ErrorResponse, "description": "Sync error"},
    },
    summary="Execute sync",
    description="Sync data from MySQL to Google Sheets.",
)
async def execute_sync(
    request: SyncRequest,
    api_key: str | None = Depends(verify_api_key),
) -> SyncResponse:
    """Execute sync from MySQL to Google Sheets."""
    reset_config()
    config = get_config()

    overrides = {}
    if request.sheet_id:
        overrides["google_sheet_id"] = request.sheet_id
    if request.worksheet_name:
        overrides["google_worksheet_name"] = request.worksheet_name
    if request.sql_query:
        overrides["sql_query"] = request.sql_query
    if request.db_type:
        overrides["db_type"] = request.db_type

    if request.column_map:
        import json

        overrides["column_mapping_enabled"] = "true"
        overrides["column_mapping"] = json.dumps(request.column_map)
    if request.columns:
        overrides["column_mapping_enabled"] = "true"
        overrides["column_order"] = ",".join(request.columns)
    if request.column_case:
        overrides["column_mapping_enabled"] = "true"
        overrides["column_case"] = request.column_case
    if request.mode:
        overrides["sync_mode"] = request.mode
    if request.chunk_size:
        overrides["sync_chunk_size"] = request.chunk_size

    if overrides:
        config = config.with_overrides(**overrides)

    # Determine atomic streaming mode
    atomic = request.atomic if request.atomic is not None else True
    preserve_gid = request.preserve_gid if request.preserve_gid is not None else False

    try:
        result = run_sync(
            config,
            dry_run=request.dry_run,
            preview=request.preview,
            atomic=atomic,
            preserve_gid=preserve_gid,
        )

        diff_response = None
        if result.diff:
            diff_response = DiffResponse(
                has_changes=result.diff.has_changes,
                sheet_row_count=result.diff.sheet_row_count,
                query_row_count=result.diff.query_row_count,
                rows_to_add=result.diff.rows_to_add,
                rows_to_remove=result.diff.rows_to_remove,
                rows_unchanged=result.diff.rows_unchanged,
                header_changes={
                    "added": result.diff.header_changes.added,
                    "removed": result.diff.header_changes.removed,
                    "reordered": result.diff.header_changes.reordered,
                },
                summary=result.diff.summary(),
            )

        return SyncResponse(
            success=result.success,
            rows_synced=result.rows_synced,
            columns=result.columns,
            headers=result.headers,
            message=result.message,
            error=result.error,
            preview=result.preview,
            diff=diff_response,
        )
    except ConfigError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=e.to_dict(),
        )
    except SheetsError as e:
        raise HTTPException(
            status_code=500,
            detail=e.to_dict(),
        )


@router.post(
    "/sync/{job_id}/resume",
    response_model=ResumeSyncResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
        400: {"model": ErrorResponse, "description": "Resume failed"},
        500: {"model": ErrorResponse, "description": "Sync error"},
    },
    summary="Resume failed sync",
    description="Resume a failed resumable streaming sync from its checkpoint.",
)
async def resume_sync(
    job_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> ResumeSyncResponse:
    """Resume a failed resumable sync from its checkpoint.

    Loads the checkpoint for the given job, verifies the staging worksheet
    still exists, and resumes streaming from the last successful chunk.
    """
    from mysql_to_sheets.core.atomic_streaming import (
        AtomicStreamingConfig,
        resume_atomic_streaming_sync,
    )
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.checkpoints import get_checkpoint_repository

    # Get checkpoint for job
    db_path = get_tenant_db_path()
    checkpoint_repo = get_checkpoint_repository(db_path)
    checkpoint = checkpoint_repo.get_checkpoint(job_id)

    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NotFound",
                "message": f"No checkpoint found for job {job_id}",
            },
        )

    # Load config
    reset_config()
    config = get_config()

    # Create atomic config for resume
    ac = AtomicStreamingConfig(
        chunk_size=config.sync_chunk_size,
        resumable=True,
    )

    try:
        result = resume_atomic_streaming_sync(
            config=config,
            checkpoint=checkpoint,
            atomic_config=ac,
            job_id=job_id,
        )

        return ResumeSyncResponse(
            success=result.success,
            rows_synced=result.total_rows,
            message=result.message or f"Resumed sync completed with {result.total_rows} rows",
            error=result.error,
            resumed_from_chunk=checkpoint.chunks_completed,
            resumed_from_rows=checkpoint.rows_pushed,
            total_chunks=result.successful_chunks,
        )

    except ConfigError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )
    except DatabaseError as e:
        raise HTTPException(
            status_code=500,
            detail=e.to_dict(),
        )
    except SheetsError as e:
        raise HTTPException(
            status_code=500,
            detail=e.to_dict(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "ResumeError",
                "message": f"Failed to resume sync: {e!s}",
            },
        )


@router.get(
    "/sync/{job_id}/checkpoint",
    response_model=CheckpointResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
    },
    summary="Get sync checkpoint",
    description="Get the checkpoint status for a resumable streaming sync.",
)
async def get_checkpoint(
    job_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> CheckpointResponse:
    """Get checkpoint status for a job.

    Returns the current checkpoint state including staging worksheet info,
    chunks completed, and rows pushed.
    """
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.checkpoints import get_checkpoint_repository

    db_path = get_tenant_db_path()
    checkpoint_repo = get_checkpoint_repository(db_path)
    checkpoint = checkpoint_repo.get_checkpoint(job_id)

    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NotFound",
                "message": f"No checkpoint found for job {job_id}",
            },
        )

    return CheckpointResponse(
        job_id=checkpoint.job_id,
        config_id=checkpoint.config_id,
        staging_worksheet_name=checkpoint.staging_worksheet_name,
        staging_worksheet_gid=checkpoint.staging_worksheet_gid,
        chunks_completed=checkpoint.chunks_completed,
        rows_pushed=checkpoint.rows_pushed,
        headers=checkpoint.headers,
        created_at=checkpoint.created_at.isoformat() if checkpoint.created_at else "",
        updated_at=checkpoint.updated_at.isoformat() if checkpoint.updated_at else "",
    )


@router.delete(
    "/sync/{job_id}/checkpoint",
    responses={
        404: {"model": ErrorResponse, "description": "Checkpoint not found"},
    },
    summary="Delete sync checkpoint",
    description="Delete the checkpoint for a sync job (e.g., to abandon resume).",
)
async def delete_checkpoint(
    job_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> dict[str, Any]:
    """Delete checkpoint for a job.

    Use this to abandon a failed sync and clean up the checkpoint.
    Note: This does not clean up the staging worksheet in Google Sheets.
    """
    from mysql_to_sheets.core.tenant import get_tenant_db_path
    from mysql_to_sheets.models.checkpoints import get_checkpoint_repository

    db_path = get_tenant_db_path()
    checkpoint_repo = get_checkpoint_repository(db_path)
    deleted = checkpoint_repo.delete_checkpoint(job_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "NotFound",
                "message": f"No checkpoint found for job {job_id}",
            },
        )

    return {"success": True, "message": f"Checkpoint for job {job_id} deleted"}


@router.post(
    "/validate",
    response_model=ValidateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
    summary="Validate configuration",
    description="Validate configuration without executing sync.",
)
async def validate_config(
    request: ValidateRequest,
    api_key: str | None = Depends(verify_api_key),
) -> ValidateResponse:
    """Validate configuration and optionally test connections."""
    reset_config()
    config = get_config()

    overrides = {}
    if request.sheet_id:
        overrides["google_sheet_id"] = request.sheet_id
    if request.worksheet_name:
        overrides["google_worksheet_name"] = request.worksheet_name
    if request.sql_query:
        overrides["sql_query"] = request.sql_query

    if overrides:
        config = config.with_overrides(**overrides)

    errors = config.validate()
    valid = len(errors) == 0

    response = ValidateResponse(
        valid=valid,
        errors=errors,
    )

    if request.test_connections and valid:
        service = SyncService(config)

        try:
            service.test_database_connection()
            response.database_ok = True
        except DatabaseError as e:
            response.database_ok = False
            response.valid = False
            response.errors.append(f"Database: {e.message}")

        try:
            service.test_sheets_connection()
            response.sheets_ok = True
        except SheetsError as e:
            response.sheets_ok = False
            response.valid = False
            response.errors.append(f"Sheets: {e.message}")

    return response


@router.get(
    "/history",
    response_model=HistoryResponse,
    summary="Get sync history",
    description="Retrieve sync history with optional filtering and pagination.",
)
async def get_history(
    limit: int = Query(default=50, ge=1, le=500, description="Max entries to return"),
    offset: int = Query(default=0, ge=0, description="Number of entries to skip"),
    sheet_id: str | None = Query(default=None, description="Filter by sheet ID"),
    api_key: str | None = Depends(verify_api_key),
) -> HistoryResponse:
    """Get sync history entries."""
    config = get_config()
    repo = get_history_repository(
        backend=config.history_backend,
        db_path=config.history_db_path if config.history_backend == "sqlite" else None,
    )

    if sheet_id:
        entries = repo.get_by_sheet_id(sheet_id, limit=limit)
        total = len(entries)
    else:
        entries = repo.get_all(limit=limit, offset=offset)
        total = repo.count()

    return HistoryResponse(
        entries=[
            HistoryEntryResponse(
                id=e.id,
                timestamp=e.timestamp.isoformat() if e.timestamp else "",
                success=e.success,
                rows_synced=e.rows_synced,
                columns=e.columns,
                headers=e.headers,
                message=e.message,
                error=e.error,
                sheet_id=e.sheet_id,
                worksheet=e.worksheet,
                duration_ms=e.duration_ms,
                request_id=e.request_id,
                source=e.source,
            )
            for e in entries
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/history/{entry_id}",
    response_model=HistoryEntryResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Entry not found"},
    },
    summary="Get history entry by ID",
    description="Retrieve a specific sync history entry.",
)
async def get_history_entry(
    entry_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> HistoryEntryResponse:
    """Get a specific history entry."""
    config = get_config()
    repo = get_history_repository(
        backend=config.history_backend,
        db_path=config.history_db_path if config.history_backend == "sqlite" else None,
    )

    entry = repo.get_by_id(entry_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"History entry {entry_id} not found"},
        )

    return HistoryEntryResponse(
        id=entry.id,
        timestamp=entry.timestamp.isoformat() if entry.timestamp else "",
        success=entry.success,
        rows_synced=entry.rows_synced,
        columns=entry.columns,
        headers=entry.headers,
        message=entry.message,
        error=entry.error,
        sheet_id=entry.sheet_id,
        worksheet=entry.worksheet,
        duration_ms=entry.duration_ms,
        request_id=entry.request_id,
        source=entry.source,
    )


@router.get(
    "/metrics",
    summary="Get Prometheus metrics",
    description="Retrieve metrics in Prometheus exposition format.",
    response_class=Response,
)
async def get_metrics() -> Response:
    """Get metrics in Prometheus format."""
    config = get_config()
    if not config.metrics_enabled:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Metrics endpoint is disabled"},
        )

    registry = get_registry()
    content = registry.to_prometheus()

    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# Schedule endpoints


def _job_to_response(job: Any) -> ScheduleResponse:
    """Convert ScheduledJob to ScheduleResponse."""
    return ScheduleResponse(
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
        created_at=job.created_at.isoformat() if job.created_at else None,
        updated_at=job.updated_at.isoformat() if job.updated_at else None,
        last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
        last_run_success=job.last_run_success,
        last_run_message=job.last_run_message,
        last_run_rows=job.last_run_rows,
        last_run_duration_ms=job.last_run_duration_ms,
        next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
        status=job.status.value,
        schedule_display=job.schedule_display,
    )


@router.post(
    "/schedules",
    response_model=ScheduleResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
    },
    summary="Create scheduled job",
    description="Create a new scheduled sync job.",
)
async def create_schedule(
    request: ScheduleCreateRequest,
    api_key: str | None = Depends(verify_api_key),
) -> ScheduleResponse:
    """Create a new scheduled job."""
    from mysql_to_sheets.core.exceptions import SchedulerError
    from mysql_to_sheets.core.scheduler import ScheduledJob, get_scheduler_service

    # Validate schedule parameters
    if not request.cron_expression and not request.interval_minutes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": "Either cron_expression or interval_minutes is required",
            },
        )

    # Mutual exclusivity: cannot provide both cron and interval
    if request.cron_expression and request.interval_minutes:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": "Cannot specify both cron_expression and interval_minutes. Choose one scheduling method.",
            },
        )

    # Validate interval bounds
    if request.interval_minutes is not None and request.interval_minutes <= 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ValidationError",
                "message": f"interval_minutes must be positive, got {request.interval_minutes}",
            },
        )

    try:
        service = get_scheduler_service()

        job = ScheduledJob(
            name=request.name,
            cron_expression=request.cron_expression,
            interval_minutes=request.interval_minutes,
            sheet_id=request.sheet_id,
            worksheet_name=request.worksheet_name,
            sql_query=request.sql_query,
            notify_on_success=request.notify_on_success,
            notify_on_failure=request.notify_on_failure,
        )

        created = service.add_job(job)
        return _job_to_response(created)

    except SchedulerError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )


@router.get(
    "/schedules",
    response_model=ScheduleListResponse,
    summary="List scheduled jobs",
    description="List all scheduled sync jobs.",
)
async def list_schedules(
    include_disabled: bool = Query(default=False, description="Include disabled jobs"),
    api_key: str | None = Depends(verify_api_key),
) -> ScheduleListResponse:
    """List all scheduled jobs."""
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    jobs = service.get_all_jobs(include_disabled=include_disabled)

    return ScheduleListResponse(
        schedules=[_job_to_response(j) for j in jobs],
        total=len(jobs),
    )


@router.get(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Schedule not found"},
    },
    summary="Get scheduled job",
    description="Get a specific scheduled job by ID.",
)
async def get_schedule(
    schedule_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> ScheduleResponse:
    """Get a scheduled job by ID."""
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Schedule {schedule_id} not found"},
        )

    return _job_to_response(job)


@router.put(
    "/schedules/{schedule_id}",
    response_model=ScheduleResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Schedule not found"},
    },
    summary="Update scheduled job",
    description="Update a scheduled sync job.",
)
async def update_schedule(
    schedule_id: int,
    request: ScheduleUpdateRequest,
    api_key: str | None = Depends(verify_api_key),
) -> ScheduleResponse:
    """Update a scheduled job."""
    from mysql_to_sheets.core.exceptions import SchedulerError
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Schedule {schedule_id} not found"},
        )

    if request.name is not None:
        job.name = request.name
    if request.cron_expression is not None:
        job.cron_expression = request.cron_expression
        job.interval_minutes = None
    if request.interval_minutes is not None:
        job.interval_minutes = request.interval_minutes
        job.cron_expression = None
    if request.sheet_id is not None:
        job.sheet_id = request.sheet_id
    if request.worksheet_name is not None:
        job.worksheet_name = request.worksheet_name
    if request.sql_query is not None:
        job.sql_query = request.sql_query
    if request.notify_on_success is not None:
        job.notify_on_success = request.notify_on_success
    if request.notify_on_failure is not None:
        job.notify_on_failure = request.notify_on_failure
    if request.enabled is not None:
        job.enabled = request.enabled

    try:
        updated = service.update_job(job)
        return _job_to_response(updated)
    except SchedulerError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )


@router.delete(
    "/schedules/{schedule_id}",
    responses={
        404: {"model": ErrorResponse, "description": "Schedule not found"},
    },
    summary="Delete scheduled job",
    description="Delete a scheduled sync job.",
)
async def delete_schedule(
    schedule_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> dict[str, Any]:
    """Delete a scheduled job."""
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    deleted = service.delete_job(schedule_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Schedule {schedule_id} not found"},
        )

    return {"success": True, "message": f"Schedule {schedule_id} deleted"}


@router.post(
    "/schedules/{schedule_id}/trigger",
    response_model=ScheduleResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Schedule not found"},
    },
    summary="Trigger scheduled job",
    description="Manually trigger a scheduled job to run immediately.",
)
async def trigger_schedule(
    schedule_id: int,
    api_key: str | None = Depends(verify_api_key),
) -> ScheduleResponse:
    """Manually trigger a scheduled job."""
    from mysql_to_sheets.core.exceptions import SchedulerError
    from mysql_to_sheets.core.scheduler import get_scheduler_service

    service = get_scheduler_service()
    job = service.get_job(schedule_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": f"Schedule {schedule_id} not found"},
        )

    try:
        service.trigger_job(schedule_id)
        job = service.get_job(schedule_id)
        return _job_to_response(job)
    except SchedulerError as e:
        raise HTTPException(
            status_code=400,
            detail=e.to_dict(),
        )


# Notification endpoints


@router.get(
    "/notifications/status",
    response_model=NotificationStatusResponse,
    summary="Get notification status",
    description="Get configuration status of all notification backends.",
)
async def get_notification_status(
    api_key: str | None = Depends(verify_api_key),
) -> NotificationStatusResponse:
    """Get notification backend status."""
    from mysql_to_sheets.core.notifications import get_notification_manager
    from mysql_to_sheets.core.notifications.base import NotificationConfig

    config = get_config()

    notification_config = NotificationConfig(
        notify_on_success=config.notify_on_success,
        notify_on_failure=config.notify_on_failure,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_user=config.smtp_user,
        smtp_password=config.smtp_password,
        smtp_from=config.smtp_from,
        smtp_to=config.smtp_to,
        smtp_use_tls=config.smtp_use_tls,
        slack_webhook_url=config.slack_webhook_url,
        notification_webhook_url=config.notification_webhook_url,
    )

    manager = get_notification_manager()
    status = manager.get_status(notification_config)

    return NotificationStatusResponse(backends=status)


@router.post(
    "/notifications/test",
    response_model=NotificationTestResponse,
    summary="Test notifications",
    description="Send a test notification to verify configuration.",
)
async def test_notification(
    request: NotificationTestRequest,
    api_key: str | None = Depends(verify_api_key),
) -> NotificationTestResponse:
    """Send a test notification."""
    from mysql_to_sheets.core.exceptions import NotificationError
    from mysql_to_sheets.core.notifications import get_notification_manager
    from mysql_to_sheets.core.notifications.base import NotificationConfig, NotificationPayload

    config = get_config()

    notification_config = NotificationConfig(
        notify_on_success=True,
        notify_on_failure=True,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_user=config.smtp_user,
        smtp_password=config.smtp_password,
        smtp_from=config.smtp_from,
        smtp_to=config.smtp_to,
        smtp_use_tls=config.smtp_use_tls,
        slack_webhook_url=config.slack_webhook_url,
        notification_webhook_url=config.notification_webhook_url,
    )

    manager = get_notification_manager()

    if request.backend.lower() == "all":
        payload = NotificationPayload(
            success=True,
            rows_synced=0,
            message="This is a test notification from MySQL to Sheets Sync",
            source="test",
        )
        results = manager.send_notification(payload, notification_config)
        return NotificationTestResponse(
            success=len(results["failed"]) == 0 and len(results["sent"]) > 0,
            results=results,
        )
    else:
        try:
            success = manager.test_backend(request.backend, notification_config)
            return NotificationTestResponse(
                success=success,
                results={"backend": request.backend, "status": "sent" if success else "failed"},
            )
        except (ValueError, NotificationError) as e:
            return NotificationTestResponse(
                success=False,
                results={"backend": request.backend, "error": str(e)},
            )
