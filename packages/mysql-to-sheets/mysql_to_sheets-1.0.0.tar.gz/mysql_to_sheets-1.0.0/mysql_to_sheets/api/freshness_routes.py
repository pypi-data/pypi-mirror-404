"""FastAPI routes for freshness/SLA monitoring.

Provides REST API endpoints for monitoring data freshness and SLA compliance.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    get_current_user,
)
from mysql_to_sheets.core.freshness import (
    check_all_freshness,
    get_freshness_report,
    get_freshness_status,
    set_sla,
)
from mysql_to_sheets.core.freshness_alerts import check_and_alert
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.users import User

logger = logging.getLogger("mysql_to_sheets.api.freshness")

router = APIRouter(prefix="/freshness", tags=["freshness"])


# Request/Response models
class FreshnessStatusResponse(BaseModel):
    """Response model for a single freshness status."""

    config_id: int
    config_name: str
    status: str
    last_success_at: str | None
    sla_minutes: int
    minutes_since_sync: int | None
    percent_of_sla: float | None
    organization_id: int


class FreshnessListResponse(BaseModel):
    """Response model for freshness list."""

    success: bool = True
    statuses: list[FreshnessStatusResponse]
    count: int


class FreshnessReportResponse(BaseModel):
    """Response model for freshness report."""

    success: bool = True
    organization_id: int
    total_configs: int
    counts: dict[str, int]
    health_percent: float
    statuses: list[dict[str, Any]]
    checked_at: str


class SetSlaRequest(BaseModel):
    """Request model for setting SLA."""

    sla_minutes: int = Field(ge=1, description="SLA threshold in minutes")


class SetSlaResponse(BaseModel):
    """Response model for SLA update."""

    success: bool = True
    message: str
    sla_minutes: int


class CheckAlertsResponse(BaseModel):
    """Response model for alert check."""

    success: bool = True
    alerts: list[dict[str, Any]]
    alert_count: int


@router.get("", response_model=FreshnessListResponse)
async def list_freshness(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
    enabled_only: Annotated[
        bool,
        Query(description="Only check enabled configs"),
    ] = True,
) -> FreshnessListResponse:
    """List freshness status for all sync configs."""
    db_path = get_tenant_db_path()
    statuses = check_all_freshness(
        organization_id=organization_id,
        enabled_only=enabled_only,
        db_path=db_path,
    )

    return FreshnessListResponse(
        statuses=[FreshnessStatusResponse(**s.to_dict()) for s in statuses],
        count=len(statuses),
    )


@router.get("/report", response_model=FreshnessReportResponse)
async def get_report(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> FreshnessReportResponse:
    """Get a freshness report for the organization."""
    db_path = get_tenant_db_path()
    report = get_freshness_report(organization_id=organization_id, db_path=db_path)

    return FreshnessReportResponse(**report)


@router.get("/{config_id}", response_model=FreshnessStatusResponse)
async def get_config_freshness(
    config_id: int,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> FreshnessStatusResponse:
    """Get freshness status for a specific config."""
    db_path = get_tenant_db_path()
    status = get_freshness_status(
        config_id=config_id,
        organization_id=organization_id,
        db_path=db_path,
    )

    if not status:
        raise HTTPException(status_code=404, detail="Config not found")

    return FreshnessStatusResponse(**status.to_dict())


@router.put("/{config_id}/sla", response_model=SetSlaResponse)
async def update_sla(
    config_id: int,
    request: SetSlaRequest,
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
) -> SetSlaResponse:
    """Update SLA threshold for a config."""
    db_path = get_tenant_db_path()

    try:
        success = set_sla(
            config_id=config_id,
            organization_id=organization_id,
            sla_minutes=request.sla_minutes,
            db_path=db_path,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not success:
        raise HTTPException(status_code=404, detail="Config not found")

    return SetSlaResponse(
        message=f"SLA for config {config_id} set to {request.sla_minutes} minutes",
        sla_minutes=request.sla_minutes,
    )


@router.post("/check", response_model=CheckAlertsResponse)
async def check_alerts(
    user: User = Depends(get_current_user),
    organization_id: int = Depends(get_current_organization_id),
    send_notifications: Annotated[
        bool,
        Query(description="Whether to send actual notifications"),
    ] = False,
) -> CheckAlertsResponse:
    """Check freshness and trigger alerts for stale configs.

    By default, this only returns alerts without sending notifications.
    Set send_notifications=true to actually send emails/Slack/webhooks.
    """
    db_path = get_tenant_db_path()
    alerts = check_and_alert(
        organization_id=organization_id,
        db_path=db_path,
        send_notifications=send_notifications,
    )

    return CheckAlertsResponse(
        alerts=alerts,
        alert_count=len(alerts),
    )
