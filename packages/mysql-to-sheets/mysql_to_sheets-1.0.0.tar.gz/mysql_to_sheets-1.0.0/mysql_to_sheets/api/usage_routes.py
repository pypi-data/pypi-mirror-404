"""Usage tracking API endpoints.

Provides endpoints to query usage metrics for billing and analytics.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.core.usage_tracking import (
    check_usage_threshold,
    get_current_usage,
    get_usage_history,
    get_usage_summary,
)

logger = logging.getLogger("mysql_to_sheets.api.usage")

router = APIRouter(prefix="/usage", tags=["usage"])


class UsageRecordResponse(BaseModel):
    """Usage record response model."""

    organization_id: int
    period_start: str
    period_end: str
    rows_synced: int = 0
    sync_operations: int = 0
    api_calls: int = 0
    created_at: str | None = None
    updated_at: str | None = None


class CurrentUsageResponse(BaseModel):
    """Current period usage response."""

    success: bool
    usage: UsageRecordResponse
    thresholds: dict[str, Any] | None = None


class UsageHistoryResponse(BaseModel):
    """Usage history response."""

    success: bool
    periods: list[UsageRecordResponse]
    count: int


class UsageSummaryResponse(BaseModel):
    """Usage summary response."""

    success: bool
    current_period: dict[str, Any]
    totals: dict[str, int]
    periods_tracked: int
    thresholds: dict[str, Any] | None = None


def _get_organization_id(request: Request) -> int:
    """Get organization ID from request context.

    Args:
        request: FastAPI request.

    Returns:
        Organization ID.

    Raises:
        HTTPException: If no organization context.
    """
    org_id = getattr(request.state, "organization_id", None)
    if not org_id:
        # Try to get from user context
        user = getattr(request.state, "user", None)
        if user:
            org_id = getattr(user, "organization_id", None)

    if not org_id:
        raise HTTPException(
            status_code=401,
            detail="Organization context required",
        )

    return int(org_id)


@router.get("/current", response_model=CurrentUsageResponse)
async def get_current_period_usage(
    request: Request,
    include_thresholds: bool = Query(default=True, description="Include threshold status"),
) -> CurrentUsageResponse:
    """Get usage for the current billing period.

    Returns rows synced, sync operations, and API calls for
    the current calendar month.
    """
    org_id = _get_organization_id(request)
    db_path = get_tenant_db_path()

    record = get_current_usage(org_id, db_path)
    usage = UsageRecordResponse(
        organization_id=record.organization_id,
        period_start=record.period_start.isoformat(),
        period_end=record.period_end.isoformat(),
        rows_synced=record.rows_synced,
        sync_operations=record.sync_operations,
        api_calls=record.api_calls,
        created_at=record.created_at.isoformat() if record.created_at else None,
        updated_at=record.updated_at.isoformat() if record.updated_at else None,
    )

    thresholds = None
    if include_thresholds:
        thresholds = check_usage_threshold(org_id, db_path=db_path)

    return CurrentUsageResponse(
        success=True,
        usage=usage,
        thresholds=thresholds,
    )


@router.get("/history", response_model=UsageHistoryResponse)
async def get_usage_history_endpoint(
    request: Request,
    limit: int = Query(default=12, ge=1, le=36, description="Number of periods"),
) -> UsageHistoryResponse:
    """Get usage history for past billing periods.

    Returns usage records for the most recent billing periods.
    """
    org_id = _get_organization_id(request)
    db_path = get_tenant_db_path()

    records = get_usage_history(org_id, limit=limit, db_path=db_path)

    periods = [
        UsageRecordResponse(
            organization_id=r.organization_id,
            period_start=r.period_start.isoformat(),
            period_end=r.period_end.isoformat(),
            rows_synced=r.rows_synced,
            sync_operations=r.sync_operations,
            api_calls=r.api_calls,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in records
    ]

    return UsageHistoryResponse(
        success=True,
        periods=periods,
        count=len(periods),
    )


@router.get("/summary", response_model=UsageSummaryResponse)
async def get_usage_summary_endpoint(
    request: Request,
    include_thresholds: bool = Query(default=True, description="Include threshold status"),
) -> UsageSummaryResponse:
    """Get usage summary with current period and totals.

    Returns current period usage, historical totals, and optionally
    threshold status for usage alerts.
    """
    org_id = _get_organization_id(request)
    db_path = get_tenant_db_path()

    summary = get_usage_summary(org_id, db_path=db_path)

    thresholds = None
    if include_thresholds:
        thresholds = check_usage_threshold(org_id, db_path=db_path)

    return UsageSummaryResponse(
        success=True,
        current_period=summary["current_period"],
        totals=summary["totals"],
        periods_tracked=summary["periods_tracked"],
        thresholds=thresholds,
    )
