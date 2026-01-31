"""FastAPI routes for snapshots and rollback.

Provides REST API endpoints for managing sheet snapshots and
performing rollbacks to restore previous sheet states.
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
from mysql_to_sheets.core.rollback import (
    can_rollback,
    preview_rollback,
    rollback_to_snapshot,
)
from mysql_to_sheets.core.snapshot_retention import (
    RetentionConfig,
    cleanup_old_snapshots,
    get_storage_stats,
)
from mysql_to_sheets.core.snapshots import (
    create_snapshot,
    delete_snapshot,
    get_snapshot,
    list_snapshots,
)
from mysql_to_sheets.core.tenant import get_tenant_db_path

logger = logging.getLogger("mysql_to_sheets.api.rollback")

router = APIRouter(prefix="/snapshots", tags=["snapshots"])


# Request/Response models
class SnapshotResponse(BaseModel):
    """Response model for a snapshot."""

    id: int
    organization_id: int
    sync_config_id: int | None
    sheet_id: str
    worksheet_name: str
    created_at: str | None
    row_count: int
    column_count: int
    size_bytes: int
    checksum: str
    headers: list[str]


class SnapshotListResponse(BaseModel):
    """Response model for snapshot list."""

    success: bool = True
    snapshots: list[SnapshotResponse]
    count: int


class SnapshotDetailResponse(BaseModel):
    """Response model for snapshot detail."""

    success: bool = True
    snapshot: SnapshotResponse


class DeleteSnapshotResponse(BaseModel):
    """Response model for snapshot deletion."""

    success: bool = True
    message: str


class RollbackPreviewResponse(BaseModel):
    """Response model for rollback preview."""

    success: bool = True
    snapshot_id: int
    snapshot_created_at: str | None
    current_row_count: int
    snapshot_row_count: int
    current_column_count: int
    snapshot_column_count: int
    message: str
    diff: dict[str, Any] | None


class RollbackExecuteRequest(BaseModel):
    """Request model for rollback execution."""

    create_backup: bool = Field(
        default=True,
        description="Whether to create a backup snapshot before rollback",
    )


class RollbackExecuteResponse(BaseModel):
    """Response model for rollback execution."""

    success: bool
    snapshot_id: int
    rows_restored: int
    columns_restored: int
    backup_snapshot_id: int | None
    message: str
    error: str | None = None


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics."""

    success: bool = True
    total_snapshots: int
    total_size_bytes: int
    total_size_mb: float
    by_sheet: dict[str, dict[str, Any]]
    oldest_snapshot: str | None
    newest_snapshot: str | None


class CleanupRequest(BaseModel):
    """Request model for cleanup operation."""

    retention_count: int | None = Field(
        default=None,
        ge=1,
        description="Maximum snapshots to keep per sheet",
    )
    retention_days: int | None = Field(
        default=None,
        ge=1,
        description="Delete snapshots older than this many days",
    )


class CleanupResponse(BaseModel):
    """Response model for cleanup operation."""

    success: bool = True
    deleted_by_count: int
    deleted_by_age: int
    total_deleted: int
    sheets_processed: int
    message: str


class CreateSnapshotRequest(BaseModel):
    """Request model for manual snapshot creation."""

    sheet_id: str = Field(..., description="Google Sheet ID")
    worksheet_name: str = Field(default="Sheet1", description="Worksheet tab name")


class CreateSnapshotResponse(BaseModel):
    """Response model for snapshot creation."""

    success: bool = True
    snapshot: SnapshotResponse
    message: str


@router.post("", response_model=CreateSnapshotResponse)
async def create_manual_snapshot(
    request: CreateSnapshotRequest,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> CreateSnapshotResponse:
    """Create a manual snapshot of the current sheet state."""
    db_path = get_tenant_db_path()
    config = get_config()

    # Create config with requested sheet info
    snapshot_config = config.with_overrides(
        google_sheet_id=request.sheet_id,
        google_worksheet_name=request.worksheet_name,
    )

    try:
        snapshot = create_snapshot(
            config=snapshot_config,
            organization_id=organization_id,
            db_path=db_path,
            logger=logger,
        )

        assert snapshot.id is not None, "Snapshot ID should not be None after creation"
        return CreateSnapshotResponse(
            snapshot=SnapshotResponse(
                id=snapshot.id,
                organization_id=snapshot.organization_id,
                sync_config_id=snapshot.sync_config_id,
                sheet_id=snapshot.sheet_id,
                worksheet_name=snapshot.worksheet_name,
                created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
                row_count=snapshot.row_count,
                column_count=snapshot.column_count,
                size_bytes=snapshot.size_bytes,
                checksum=snapshot.checksum,
                headers=snapshot.headers,
            ),
            message=f"Snapshot created: {snapshot.row_count} rows, {snapshot.column_count} columns",
        )

    except Exception as e:
        logger.error(f"Snapshot creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Snapshot creation failed: {e}")


@router.get("", response_model=SnapshotListResponse)
async def list_all_snapshots(
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
    sheet_id: Annotated[str | None, Query(description="Filter by sheet ID")] = None,
    worksheet_name: Annotated[str | None, Query(description="Filter by worksheet name")] = None,
    sync_config_id: Annotated[int | None, Query(description="Filter by sync config ID")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum results")] = 20,
    offset: Annotated[int, Query(ge=0, description="Results to skip")] = 0,
) -> SnapshotListResponse:
    """List available snapshots."""
    db_path = get_tenant_db_path()

    snapshots = list_snapshots(
        organization_id=organization_id,
        db_path=db_path,
        sheet_id=sheet_id,
        worksheet_name=worksheet_name,
        sync_config_id=sync_config_id,
        limit=limit,
        offset=offset,
    )

    return SnapshotListResponse(
        snapshots=[
            SnapshotResponse(
                id=s.id if s.id is not None else 0,
                organization_id=s.organization_id,
                sync_config_id=s.sync_config_id,
                sheet_id=s.sheet_id,
                worksheet_name=s.worksheet_name,
                created_at=s.created_at.isoformat() if s.created_at else None,
                row_count=s.row_count,
                column_count=s.column_count,
                size_bytes=s.size_bytes,
                checksum=s.checksum,
                headers=s.headers,
            )
            for s in snapshots
        ],
        count=len(snapshots),
    )


@router.get("/stats", response_model=StorageStatsResponse)
async def get_snapshot_storage_stats(
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> StorageStatsResponse:
    """Get snapshot storage statistics."""
    db_path = get_tenant_db_path()

    stats = get_storage_stats(
        organization_id=organization_id,
        db_path=db_path,
    )

    return StorageStatsResponse(**stats.to_dict())


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_snapshots(
    request: CleanupRequest,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> CleanupResponse:
    """Clean up old snapshots based on retention policy."""
    db_path = get_tenant_db_path()
    config = get_config()

    retention_config = RetentionConfig(
        retention_count=request.retention_count or config.snapshot_retention_count,
        retention_days=request.retention_days or config.snapshot_retention_days,
        max_size_mb=config.snapshot_max_size_mb,
    )

    result = cleanup_old_snapshots(
        organization_id=organization_id,
        db_path=db_path,
        retention_config=retention_config,
        logger=logger,
    )

    return CleanupResponse(**result.to_dict())


@router.get("/{snapshot_id}", response_model=SnapshotDetailResponse)
async def get_snapshot_by_id(
    snapshot_id: int,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> SnapshotDetailResponse:
    """Get snapshot details by ID."""
    db_path = get_tenant_db_path()

    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    if snapshot.id is None:
        raise HTTPException(status_code=500, detail="Snapshot ID is None")

    return SnapshotDetailResponse(
        snapshot=SnapshotResponse(
            id=snapshot.id,
            organization_id=snapshot.organization_id,
            sync_config_id=snapshot.sync_config_id,
            sheet_id=snapshot.sheet_id,
            worksheet_name=snapshot.worksheet_name,
            created_at=snapshot.created_at.isoformat() if snapshot.created_at else None,
            row_count=snapshot.row_count,
            column_count=snapshot.column_count,
            size_bytes=snapshot.size_bytes,
            checksum=snapshot.checksum,
            headers=snapshot.headers,
        ),
    )


@router.delete("/{snapshot_id}", response_model=DeleteSnapshotResponse)
async def delete_snapshot_by_id(
    snapshot_id: int,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> DeleteSnapshotResponse:
    """Delete a snapshot."""
    db_path = get_tenant_db_path()

    deleted = delete_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        logger=logger,
    )

    if not deleted:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    return DeleteSnapshotResponse(
        message=f"Snapshot {snapshot_id} deleted successfully",
    )


@router.post("/{snapshot_id}/preview", response_model=RollbackPreviewResponse)
async def preview_snapshot_rollback(
    snapshot_id: int,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> RollbackPreviewResponse:
    """Preview what changes a rollback would make."""
    db_path = get_tenant_db_path()
    config = get_config()

    # Get snapshot to retrieve sheet info
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    # Create config with snapshot's sheet info
    rollback_config = config.with_overrides(
        google_sheet_id=snapshot.sheet_id,
        google_worksheet_name=snapshot.worksheet_name,
    )

    try:
        preview = preview_rollback(
            snapshot_id=snapshot_id,
            organization_id=organization_id,
            config=rollback_config,
            db_path=db_path,
            logger=logger,
        )

        return RollbackPreviewResponse(
            snapshot_id=preview.snapshot_id,
            snapshot_created_at=preview.snapshot_created_at,
            current_row_count=preview.current_row_count,
            snapshot_row_count=preview.snapshot_row_count,
            current_column_count=preview.current_column_count,
            snapshot_column_count=preview.snapshot_column_count,
            message=preview.message,
            diff=preview.diff.to_dict() if preview.diff else None,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Preview failed: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {e}")


@router.post("/{snapshot_id}/rollback", response_model=RollbackExecuteResponse)
async def execute_rollback(
    snapshot_id: int,
    request: RollbackExecuteRequest,
    user: Any = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> RollbackExecuteResponse:
    """Execute a rollback to restore sheet from snapshot."""
    db_path = get_tenant_db_path()
    config = get_config()

    # Get snapshot to retrieve sheet info
    snapshot = get_snapshot(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        db_path=db_path,
        include_data=False,
    )

    if not snapshot:
        raise HTTPException(status_code=404, detail=f"Snapshot {snapshot_id} not found")

    # Create config with snapshot's sheet info
    rollback_config = config.with_overrides(
        google_sheet_id=snapshot.sheet_id,
        google_worksheet_name=snapshot.worksheet_name,
    )

    # Check if rollback is possible
    can_proceed, reason = can_rollback(
        snapshot_id=snapshot_id,
        organization_id=organization_id,
        config=rollback_config,
        db_path=db_path,
        logger=logger,
    )

    if not can_proceed:
        raise HTTPException(status_code=400, detail=f"Cannot rollback: {reason}")

    try:
        result = rollback_to_snapshot(
            snapshot_id=snapshot_id,
            organization_id=organization_id,
            config=rollback_config,
            db_path=db_path,
            create_backup=request.create_backup,
            logger=logger,
        )

        if not result.success:
            raise HTTPException(status_code=500, detail=result.error or "Rollback failed")

        return RollbackExecuteResponse(
            success=result.success,
            snapshot_id=result.snapshot_id,
            rows_restored=result.rows_restored,
            columns_restored=result.columns_restored,
            backup_snapshot_id=result.backup_snapshot_id,
            message=result.message,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Rollback failed: {e}")
