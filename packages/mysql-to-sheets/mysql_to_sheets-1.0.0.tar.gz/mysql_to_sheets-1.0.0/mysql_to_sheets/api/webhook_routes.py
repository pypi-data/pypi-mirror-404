"""Webhook subscription management API routes."""

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator

from mysql_to_sheets.api.middleware import (
    get_current_organization_id,
    require_permission,
)
from mysql_to_sheets.api.schemas import MessageResponse
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.core.webhooks import (
    get_webhook_delivery_service,
)
from mysql_to_sheets.core.webhooks.alerts import get_webhook_failure_tracker
from mysql_to_sheets.models.users import User
from mysql_to_sheets.models.webhooks import (
    VALID_EVENT_TYPES,
    WebhookDelivery,
    WebhookSubscription,
    get_webhook_repository,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# Request/Response Models


class CreateWebhookRequest(BaseModel):
    """Request body for creating a webhook subscription."""

    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=10, max_length=2048)
    events: list[str] = Field(..., min_length=1)
    secret: str | None = Field(default=None, description="Auto-generated if not provided")
    headers: dict[str, str] | None = Field(default=None)
    retry_count: int = Field(default=3, ge=0, le=10)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str]) -> list[str]:
        for event in v:
            if event not in VALID_EVENT_TYPES:
                raise ValueError(f"Invalid event type: {event}. Valid types: {VALID_EVENT_TYPES}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Slack Alert",
                "url": "https://hooks.slack.com/services/xxx/yyy/zzz",
                "events": ["sync.completed", "sync.failed"],
                "retry_count": 3,
            }
        }
    )


class UpdateWebhookRequest(BaseModel):
    """Request body for updating a webhook subscription."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    url: str | None = Field(default=None, min_length=10, max_length=2048)
    events: list[str] | None = Field(default=None, min_length=1)
    secret: str | None = Field(default=None)
    headers: dict[str, str] | None = Field(default=None)
    retry_count: int | None = Field(default=None, ge=0, le=10)
    is_active: bool | None = Field(default=None)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v

    @field_validator("events")
    @classmethod
    def validate_events(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for event in v:
                if event not in VALID_EVENT_TYPES:
                    raise ValueError(f"Invalid event type: {event}")
        return v


class WebhookResponse(BaseModel):
    """Response body for webhook subscription."""

    id: int
    name: str
    url: str
    events: list[str]
    is_active: bool
    headers: dict[str, str] | None
    retry_count: int
    created_at: str | None
    last_triggered_at: str | None
    failure_count: int
    organization_id: int


class WebhookListResponse(BaseModel):
    """Response body for webhook list."""

    webhooks: list[WebhookResponse]
    total: int
    limit: int
    offset: int


class DeliveryResponse(BaseModel):
    """Response body for webhook delivery."""

    id: int
    delivery_id: str
    event: str
    payload: dict[str, Any]
    status: str
    response_code: int | None
    response_body: str | None
    attempt_count: int
    created_at: str | None
    completed_at: str | None
    error_message: str | None


class DeliveryListResponse(BaseModel):
    """Response body for delivery list."""

    deliveries: list[DeliveryResponse]
    total: int
    limit: int
    offset: int


class TestWebhookResponse(BaseModel):
    """Response body for webhook test."""

    success: bool
    status_code: int | None
    response_body: str | None
    error_message: str | None
    duration_ms: float


class WebhookHealthStatus(BaseModel):
    """Health status for a single webhook."""

    webhook_id: int
    url: str
    consecutive_failures: int
    last_success_at: str | None
    last_failure_at: str | None
    last_error: str | None
    is_healthy: bool
    is_alerting: bool


class WebhookHealthSummaryResponse(BaseModel):
    """Response body for webhook health summary."""

    total_tracked: int
    healthy: int
    unhealthy: int
    alerting: int
    health_percent: float
    alert_threshold: int
    webhooks: list[WebhookHealthStatus]


# Helper functions


def webhook_to_response(webhook: WebhookSubscription) -> WebhookResponse:
    """Convert WebhookSubscription to WebhookResponse."""
    if webhook.id is None:
        raise ValueError("Webhook ID cannot be None")

    return WebhookResponse(
        id=webhook.id,
        name=webhook.name,
        url=webhook.url,
        events=webhook.events,
        is_active=webhook.is_active,
        headers=webhook.headers,
        retry_count=webhook.retry_count,
        created_at=webhook.created_at.isoformat() if webhook.created_at else None,
        last_triggered_at=webhook.last_triggered_at.isoformat()
        if webhook.last_triggered_at
        else None,
        failure_count=webhook.failure_count,
        organization_id=webhook.organization_id,
    )


def delivery_to_response(delivery: WebhookDelivery) -> DeliveryResponse:
    """Convert WebhookDelivery to DeliveryResponse."""
    if delivery.id is None:
        raise ValueError("Delivery ID cannot be None")

    return DeliveryResponse(
        id=delivery.id,
        delivery_id=delivery.delivery_id,
        event=delivery.event,
        payload=delivery.payload,
        status=delivery.status,
        response_code=delivery.response_code,
        response_body=delivery.response_body,
        attempt_count=delivery.attempt_count,
        created_at=delivery.created_at.isoformat() if delivery.created_at else None,
        completed_at=delivery.completed_at.isoformat() if delivery.completed_at else None,
        error_message=delivery.error_message,
    )


# Endpoints


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List webhook subscriptions",
    description="List all webhook subscriptions in the organization.",
)
async def list_webhooks(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    include_inactive: bool = Query(default=False),
    user: User = Depends(require_permission("VIEW_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> WebhookListResponse:
    """List webhook subscriptions.

    Args:
        limit: Maximum number of webhooks to return.
        offset: Number of webhooks to skip.
        include_inactive: Whether to include inactive webhooks.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        List of webhooks with pagination info.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhooks = webhook_repo.get_all_subscriptions(
        organization_id=org_id,
        include_inactive=include_inactive,
        limit=limit,
        offset=offset,
    )

    # Count total (approximate for now)
    all_webhooks = webhook_repo.get_all_subscriptions(
        organization_id=org_id,
        include_inactive=include_inactive,
    )
    total = len(all_webhooks)

    return WebhookListResponse(
        webhooks=[webhook_to_response(w) for w in webhooks],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=WebhookResponse,
    summary="Create webhook subscription",
    description="Create a new webhook subscription.",
)
async def create_webhook(
    request: CreateWebhookRequest,
    user: User = Depends(require_permission("MANAGE_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> WebhookResponse:
    """Create a new webhook subscription.

    Args:
        request: Webhook data.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Created webhook.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    # Generate secret if not provided
    secret = request.secret or secrets.token_urlsafe(32)

    webhook = WebhookSubscription(
        name=request.name,
        url=request.url,
        secret=secret,
        events=request.events,
        headers=request.headers,
        retry_count=request.retry_count,
        created_by_user_id=user.id,
        organization_id=org_id,
    )

    try:
        webhook = webhook_repo.create_subscription(webhook)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    return webhook_to_response(webhook)


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook subscription",
    description="Get a specific webhook subscription by ID.",
)
async def get_webhook(
    webhook_id: int,
    user: User = Depends(require_permission("VIEW_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> WebhookResponse:
    """Get a webhook subscription by ID.

    Args:
        webhook_id: Webhook ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Webhook data.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(webhook_id, org_id)
    if not webhook:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Webhook not found"},
        )

    return webhook_to_response(webhook)


@router.put(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook subscription",
    description="Update an existing webhook subscription.",
)
async def update_webhook(
    webhook_id: int,
    request: UpdateWebhookRequest,
    user: User = Depends(require_permission("MANAGE_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> WebhookResponse:
    """Update a webhook subscription.

    Args:
        webhook_id: Webhook ID.
        request: Update data.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Updated webhook.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(webhook_id, org_id)
    if not webhook:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Webhook not found"},
        )

    # Apply updates
    if request.name is not None:
        webhook.name = request.name
    if request.url is not None:
        webhook.url = request.url
    if request.events is not None:
        webhook.events = request.events
    if request.secret is not None:
        webhook.secret = request.secret
    if request.headers is not None:
        webhook.headers = request.headers
    if request.retry_count is not None:
        webhook.retry_count = request.retry_count
    if request.is_active is not None:
        webhook.is_active = request.is_active

    try:
        webhook = webhook_repo.update_subscription(webhook)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": "ValidationError", "message": str(e)},
        )

    return webhook_to_response(webhook)


@router.delete(
    "/{webhook_id}",
    response_model=MessageResponse,
    summary="Delete webhook subscription",
    description="Delete a webhook subscription.",
)
async def delete_webhook(
    webhook_id: int,
    user: User = Depends(require_permission("MANAGE_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> MessageResponse:
    """Delete a webhook subscription.

    Args:
        webhook_id: Webhook ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Success message.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(webhook_id, org_id)
    if not webhook:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Webhook not found"},
        )

    webhook_repo.delete_subscription(webhook_id, org_id)

    return MessageResponse(message=f"Webhook '{webhook.name}' has been deleted")


@router.post(
    "/{webhook_id}/test",
    response_model=TestWebhookResponse,
    summary="Test webhook",
    description="Send a test payload to verify webhook connectivity.",
)
async def test_webhook(
    webhook_id: int,
    user: User = Depends(require_permission("MANAGE_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> TestWebhookResponse:
    """Send a test webhook payload.

    Args:
        webhook_id: Webhook ID.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Test result with response details.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    webhook = webhook_repo.get_subscription_by_id(webhook_id, org_id)
    if not webhook:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Webhook not found"},
        )

    # Send test payload
    delivery_service = get_webhook_delivery_service(db_path)
    result = delivery_service.test_subscription(webhook)

    return TestWebhookResponse(
        success=result.success,
        status_code=result.status_code,
        response_body=result.response_body,
        error_message=result.error_message,
        duration_ms=result.duration_ms,
    )


@router.get(
    "/{webhook_id}/deliveries",
    response_model=DeliveryListResponse,
    summary="Get webhook deliveries",
    description="Get delivery history for a webhook.",
)
async def get_webhook_deliveries(
    webhook_id: int,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(
        default=None, description="Filter by status: pending, success, failed"
    ),
    user: User = Depends(require_permission("VIEW_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> DeliveryListResponse:
    """Get delivery history for a webhook.

    Args:
        webhook_id: Webhook ID.
        limit: Maximum number of deliveries to return.
        offset: Number of deliveries to skip.
        status: Filter by delivery status.
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        List of deliveries with pagination info.
    """
    db_path = get_tenant_db_path()
    webhook_repo = get_webhook_repository(db_path)

    # Verify webhook belongs to org
    webhook = webhook_repo.get_subscription_by_id(webhook_id, org_id)
    if not webhook:
        raise HTTPException(
            status_code=404,
            detail={"error": "NotFound", "message": "Webhook not found"},
        )

    deliveries = webhook_repo.get_deliveries_for_subscription(
        sub_id=webhook_id,
        limit=limit,
        offset=offset,
        status=status,
    )

    # Get total count
    all_deliveries = webhook_repo.get_deliveries_for_subscription(
        sub_id=webhook_id,
        limit=10000,  # Large limit to count
        status=status,
    )
    total = len(all_deliveries)

    return DeliveryListResponse(
        deliveries=[delivery_to_response(d) for d in deliveries],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/health",
    response_model=WebhookHealthSummaryResponse,
    summary="Get webhook health",
    description="Get health status for all tracked webhooks based on delivery failures.",
)
async def get_webhook_health(
    user: User = Depends(require_permission("VIEW_WEBHOOKS")),
    org_id: int = Depends(get_current_organization_id),
) -> WebhookHealthSummaryResponse:
    """Get health status for all tracked webhooks.

    Returns health metrics based on consecutive delivery failures tracked
    by the WebhookFailureTracker. Webhooks are considered unhealthy after
    consecutive failures, and alerting when the threshold is exceeded.

    Args:
        user: Current authenticated user.
        org_id: Current organization ID.

    Returns:
        Health summary with per-webhook status.
    """
    tracker = get_webhook_failure_tracker()
    summary = tracker.get_health_summary()
    all_statuses = tracker.get_all_statuses()

    return WebhookHealthSummaryResponse(
        total_tracked=summary["total_tracked"],
        healthy=summary["healthy"],
        unhealthy=summary["unhealthy"],
        alerting=summary["alerting"],
        health_percent=summary["health_percent"],
        alert_threshold=summary["alert_threshold"],
        webhooks=[
            WebhookHealthStatus(
                webhook_id=s.webhook_id,
                url=s.url,
                consecutive_failures=s.consecutive_failures,
                last_success_at=s.last_success_at.isoformat() if s.last_success_at else None,
                last_failure_at=s.last_failure_at.isoformat() if s.last_failure_at else None,
                last_error=s.last_error,
                is_healthy=s.is_healthy,
                is_alerting=s.is_alerting,
            )
            for s in all_statuses
        ],
    )


@router.get(
    "/events/types",
    response_model=list[str],
    summary="List event types",
    description="List all available webhook event types.",
)
async def list_event_types() -> list[str]:
    """List available webhook event types.

    Returns:
        List of valid event type strings.
    """
    return VALID_EVENT_TYPES
