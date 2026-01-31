"""FastAPI routes for audit log management.

Provides REST API endpoints for viewing and exporting audit logs.
All endpoints require admin role (VIEW_AUDIT_LOGS or EXPORT_AUDIT_LOGS permissions).
"""

import io
import logging
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    require_permission,
)
from mysql_to_sheets.core.audit import VALID_AUDIT_ACTIONS, AuditAction, log_action
from mysql_to_sheets.core.audit_export import (
    ExportOptions,
    export_audit_logs,
    get_supported_formats,
)
from mysql_to_sheets.core.audit_retention import get_retention_stats
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.audit_logs import get_audit_log_repository
from mysql_to_sheets.models.users import User

logger = logging.getLogger("mysql_to_sheets.api.audit")

router = APIRouter(prefix="/audit", tags=["audit"])


# Request/Response models
class AuditLogResponse(BaseModel):
    """Response model for a single audit log entry."""

    id: int
    timestamp: str
    user_id: int | None
    organization_id: int
    action: str
    resource_type: str
    resource_id: str | None
    source_ip: str | None
    user_agent: str | None
    query_executed: str | None
    rows_affected: int | None
    metadata: dict[str, Any] | None


class AuditLogsListResponse(BaseModel):
    """Response model for audit logs list."""

    success: bool = True
    logs: list[AuditLogResponse]
    total: int
    limit: int
    offset: int


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""

    success: bool = True
    total_logs: int
    oldest_log: str | None
    newest_log: str | None
    logs_to_delete: int
    retention_days: int
    by_action: dict[str, int]
    by_resource_type: dict[str, int]


class AuditActionsResponse(BaseModel):
    """Response model for listing valid audit actions."""

    success: bool = True
    actions: list[str]


@router.get("", response_model=AuditLogsListResponse)
async def list_audit_logs(
    user: User = Depends(require_permission("VIEW_AUDIT_LOGS")),
    organization_id: int = Depends(get_current_organization_id),
    from_date: Annotated[
        datetime | None,
        Query(description="Filter logs after this timestamp (ISO format)"),
    ] = None,
    to_date: Annotated[
        datetime | None,
        Query(description="Filter logs before this timestamp (ISO format)"),
    ] = None,
    action: Annotated[
        str | None,
        Query(description="Filter by action type"),
    ] = None,
    user_id: Annotated[
        int | None,
        Query(description="Filter by user ID"),
    ] = None,
    resource_type: Annotated[
        str | None,
        Query(description="Filter by resource type"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum results"),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0, description="Results to skip"),
    ] = 0,
) -> AuditLogsListResponse:
    """List audit logs with filters.

    Requires VIEW_AUDIT_LOGS permission (admin role).
    """
    db_path = get_tenant_db_path()

    # Log this access
    log_action(
        action=AuditAction.AUDIT_VIEWED,
        resource_type="audit",
        organization_id=organization_id,
        db_path=db_path,
        user_id=user.id,
        metadata={
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "action_filter": action,
        },
    )

    repo = get_audit_log_repository(db_path)
    logs = repo.get_all(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        limit=limit,
        offset=offset,
    )

    total = repo.count(
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
    )

    return AuditLogsListResponse(
        logs=[AuditLogResponse(**log.to_dict()) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/export")
async def export_audit_logs_endpoint(
    user: User = Depends(require_permission("EXPORT_AUDIT_LOGS")),
    organization_id: int = Depends(get_current_organization_id),
    format: Annotated[
        str,
        Query(description="Export format (csv, json, jsonl, cef)"),
    ] = "csv",
    from_date: Annotated[
        datetime | None,
        Query(description="Filter logs after this timestamp"),
    ] = None,
    to_date: Annotated[
        datetime | None,
        Query(description="Filter logs before this timestamp"),
    ] = None,
    action: Annotated[
        str | None,
        Query(description="Filter by action type"),
    ] = None,
    user_id: Annotated[
        int | None,
        Query(description="Filter by user ID"),
    ] = None,
) -> Response:
    """Export audit logs to file.

    Requires EXPORT_AUDIT_LOGS permission (admin role).
    Returns file download with appropriate content type.
    """
    db_path = get_tenant_db_path()

    if format.lower() not in get_supported_formats():
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {format}. Use one of: {get_supported_formats()}",
        )

    # Log this export
    log_action(
        action=AuditAction.AUDIT_EXPORTED,
        resource_type="audit",
        organization_id=organization_id,
        db_path=db_path,
        user_id=user.id,
        metadata={
            "format": format,
            "from_date": from_date.isoformat() if from_date else None,
            "to_date": to_date.isoformat() if to_date else None,
            "action_filter": action,
        },
    )

    options = ExportOptions(
        from_date=from_date,
        to_date=to_date,
        action=action,
        user_id=user_id,
    )

    # Export to string buffer
    output = io.StringIO()
    result = export_audit_logs(
        organization_id=organization_id,
        output=output,
        db_path=db_path,
        format=format.lower(),
        options=options,
    )

    content = output.getvalue()

    # Set content type and filename based on format
    content_types = {
        "csv": "text/csv",
        "json": "application/json",
        "jsonl": "application/x-ndjson",
        "cef": "text/plain",
    }
    extensions = {
        "csv": "csv",
        "json": "json",
        "jsonl": "jsonl",
        "cef": "cef",
    }

    content_type = content_types.get(format.lower(), "text/plain")
    extension = extensions.get(format.lower(), "txt")
    filename = f"audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.{extension}"

    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-Record-Count": str(result.record_count),
        },
    )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_stats(
    user: User = Depends(require_permission("VIEW_AUDIT_LOGS")),
    organization_id: int = Depends(get_current_organization_id),
) -> AuditStatsResponse:
    """Get audit log statistics.

    Requires VIEW_AUDIT_LOGS permission (admin role).
    """
    db_path = get_tenant_db_path()
    config = get_config()
    retention_days = config.audit_retention_days

    repo = get_audit_log_repository(db_path)
    stats = repo.get_stats(organization_id)
    retention = get_retention_stats(organization_id, db_path, retention_days)

    return AuditStatsResponse(
        total_logs=stats.get("total_logs", 0),
        oldest_log=stats.get("oldest_log"),
        newest_log=stats.get("newest_log"),
        logs_to_delete=retention.logs_to_delete,
        retention_days=retention_days,
        by_action=stats.get("by_action", {}),
        by_resource_type=stats.get("by_resource_type", {}),
    )


@router.get("/actions", response_model=AuditActionsResponse)
async def list_audit_actions() -> AuditActionsResponse:
    """List all valid audit action types.

    This endpoint is public (no authentication required).
    """
    return AuditActionsResponse(actions=VALID_AUDIT_ACTIONS)
