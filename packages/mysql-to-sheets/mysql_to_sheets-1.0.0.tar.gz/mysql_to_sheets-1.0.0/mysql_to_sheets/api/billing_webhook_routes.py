"""Billing webhook receiver endpoint.

Receives webhook events from external billing services (e.g., Stripe)
and updates organization subscription status accordingly.
"""

import hashlib
import hmac
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel, Field

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.webhook_events import check_idempotency_key, cleanup_old_events

logger = logging.getLogger("mysql_to_sheets.api.billing_webhook")

router = APIRouter(prefix="/billing", tags=["billing"])


class BillingWebhookPayload(BaseModel):
    """Incoming billing webhook payload structure."""

    event: str = Field(description="Event type (e.g., subscription.created)")
    timestamp: str | None = Field(default=None, description="ISO timestamp")
    idempotency_key: str | None = Field(default=None, description="Idempotency key")
    data: dict[str, Any] = Field(description="Event-specific data")


class WebhookResponse(BaseModel):
    """Response to webhook delivery."""

    success: bool
    message: str = ""
    event_processed: str | None = None


def _verify_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify HMAC-SHA256 webhook signature.

    Args:
        payload: Raw request body.
        signature: Signature from X-Webhook-Signature header.
        secret: Webhook secret key.

    Returns:
        True if signature is valid.
    """
    if not signature or not secret:
        return False

    # Support both "sha256=..." and raw signature formats
    if signature.startswith("sha256="):
        signature = signature[7:]

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def _check_idempotency(key: str | None) -> bool:
    """Check if this webhook has already been processed.

    Uses persistent SQLite storage so idempotency survives restarts.

    Args:
        key: Idempotency key from header or payload.

    Returns:
        True if already processed (should skip).
    """
    if not key:
        return False

    db_path = get_tenant_db_path()
    already_processed = check_idempotency_key(key, db_path)

    if already_processed:
        logger.debug(f"Skipping duplicate webhook: {key}")

    return already_processed


@router.post("/webhook", response_model=WebhookResponse)
async def receive_billing_webhook(
    request: Request,
    payload: BillingWebhookPayload,
    x_webhook_signature: str | None = Header(default=None),
    x_idempotency_key: str | None = Header(default=None),
) -> WebhookResponse:
    """Receive and process billing webhook from external billing service.

    Accepts events from billing services like Stripe and updates
    organization subscription status accordingly.

    Supported events:
    - subscription.created: New subscription created
    - subscription.updated: Subscription tier or status changed
    - subscription.canceled: Subscription canceled
    - payment.failed: Payment failed, set status to past_due
    - payment.succeeded: Payment succeeded, set status to active

    Headers:
    - X-Webhook-Signature: HMAC-SHA256 signature
    - X-Idempotency-Key: Unique key for idempotent processing

    Returns:
        WebhookResponse indicating success or failure.
    """
    config = get_config()

    # Check if billing features are enabled
    if not config.billing_enabled:
        logger.debug("Billing webhook received but billing is disabled")
        return WebhookResponse(
            success=True,
            message="Billing not enabled, webhook ignored",
        )

    # Get raw body for signature verification
    raw_body = await request.body()

    # Signature verification is mandatory when billing is enabled.
    # Without a shared secret, any caller could modify organization tiers.
    if not config.billing_webhook_secret:
        logger.error("BILLING_WEBHOOK_SECRET not set but billing is enabled")
        raise HTTPException(
            status_code=500,
            detail="Billing webhook secret not configured",
        )

    if not x_webhook_signature:
        logger.warning("Billing webhook missing signature")
        raise HTTPException(
            status_code=401,
            detail="Missing webhook signature",
        )

    if not _verify_signature(raw_body, x_webhook_signature, config.billing_webhook_secret):
        logger.warning("Billing webhook signature verification failed")
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    # Check idempotency
    idempotency_key = x_idempotency_key or payload.idempotency_key
    if _check_idempotency(idempotency_key):
        return WebhookResponse(
            success=True,
            message="Already processed",
            event_processed=payload.event,
        )

    # Process the event
    try:
        result = _process_billing_event(payload.event, payload.data)
        return WebhookResponse(
            success=True,
            message=result,
            event_processed=payload.event,
        )
    except ValueError as e:
        logger.warning(f"Invalid billing webhook data: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process billing webhook: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal error processing webhook",
        )


def _process_billing_event(event: str, data: dict[str, Any]) -> str:
    """Process a billing event and update organization.

    Args:
        event: Event type.
        data: Event data.

    Returns:
        Status message.

    Raises:
        ValueError: If required data is missing.
    """
    handlers = {
        "subscription.created": _handle_subscription_created,
        "subscription.updated": _handle_subscription_updated,
        "subscription.canceled": _handle_subscription_canceled,
        "payment.failed": _handle_payment_failed,
        "payment.succeeded": _handle_payment_succeeded,
    }

    handler = handlers.get(event)
    if not handler:
        logger.debug(f"Unhandled billing event: {event}")
        return f"Event {event} not handled"

    return handler(data)


def _handle_subscription_created(data: dict[str, Any]) -> str:
    """Handle subscription.created event.

    Sets organization tier and billing customer ID.
    """
    org_id = data.get("organization_id")
    billing_customer_id = data.get("customer_id") or data.get("billing_customer_id")
    tier = data.get("tier") or data.get("plan")

    if not org_id:
        raise ValueError("Missing organization_id")
    if not tier:
        raise ValueError("Missing tier/plan")

    _update_organization(
        organization_id=org_id,
        billing_customer_id=billing_customer_id,
        subscription_tier=tier,
        billing_status="active",
    )

    logger.info(f"Subscription created: org={org_id}, tier={tier}")
    return f"Subscription created for org {org_id}"


def _handle_subscription_updated(data: dict[str, Any]) -> str:
    """Handle subscription.updated event.

    Updates organization tier and/or status.
    """
    org_id = data.get("organization_id")
    tier = data.get("tier") or data.get("plan")
    status = data.get("status")

    if not org_id:
        raise ValueError("Missing organization_id")

    updates: dict[str, Any] = {}
    if tier:
        updates["subscription_tier"] = tier
    if status:
        updates["billing_status"] = status

    if not updates:
        return "No changes to apply"

    _update_organization(organization_id=org_id, **updates)

    logger.info(f"Subscription updated: org={org_id}, updates={updates}")
    return f"Subscription updated for org {org_id}"


def _handle_subscription_canceled(data: dict[str, Any]) -> str:
    """Handle subscription.canceled event.

    Sets organization status to canceled and reverts to free tier.
    """
    org_id = data.get("organization_id")

    if not org_id:
        raise ValueError("Missing organization_id")

    _update_organization(
        organization_id=org_id,
        subscription_tier="free",
        billing_status="canceled",
    )

    logger.info(f"Subscription canceled: org={org_id}")
    return f"Subscription canceled for org {org_id}"


def _handle_payment_failed(data: dict[str, Any]) -> str:
    """Handle payment.failed event.

    Sets organization status to past_due.
    """
    org_id = data.get("organization_id")

    if not org_id:
        raise ValueError("Missing organization_id")

    _update_organization(
        organization_id=org_id,
        billing_status="past_due",
    )

    logger.info(f"Payment failed: org={org_id}")
    return f"Payment failed for org {org_id}"


def _handle_payment_succeeded(data: dict[str, Any]) -> str:
    """Handle payment.succeeded event.

    Sets organization status to active.
    """
    org_id = data.get("organization_id")
    period_end = data.get("period_end") or data.get("subscription_period_end")

    if not org_id:
        raise ValueError("Missing organization_id")

    updates: dict[str, Any] = {"billing_status": "active"}

    if period_end:
        if isinstance(period_end, str):
            period_end = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
        updates["subscription_period_end"] = period_end

    _update_organization(organization_id=org_id, **updates)

    logger.info(f"Payment succeeded: org={org_id}")
    return f"Payment succeeded for org {org_id}"


def _update_organization(
    organization_id: int,
    billing_customer_id: str | None = None,
    subscription_tier: str | None = None,
    billing_status: str | None = None,
    subscription_period_end: datetime | None = None,
) -> None:
    """Update organization with billing information.

    Args:
        organization_id: Organization ID.
        billing_customer_id: External billing customer ID.
        subscription_tier: Subscription tier.
        billing_status: Billing status.
        subscription_period_end: When subscription period ends.

    Raises:
        ValueError: If organization not found.
    """
    db_path = get_tenant_db_path()

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    org = repo.get_by_id(organization_id)

    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    old_tier = org.subscription_tier

    if billing_customer_id:
        org.billing_customer_id = billing_customer_id
    if subscription_tier:
        org.subscription_tier = subscription_tier
    if billing_status:
        org.billing_status = billing_status
    if subscription_period_end:
        org.subscription_period_end = subscription_period_end

    repo.update(org)

    # Invalidate tier cache after update
    try:
        from mysql_to_sheets.core.tier_cache import get_tier_cache

        get_tier_cache().invalidate(organization_id)
        logger.debug(f"Tier cache invalidated for org {organization_id}")
    except Exception as e:
        logger.debug(f"Failed to invalidate tier cache: {e}")

    # Emit tier change webhook if tier changed
    if subscription_tier and subscription_tier != old_tier:
        try:
            from mysql_to_sheets.core.webhooks.payload import create_subscription_payload

            payload = create_subscription_payload(
                event="subscription.tier_changed",
                organization_id=organization_id,
                organization_slug=org.slug,
                old_tier=old_tier,
                new_tier=subscription_tier,
            )
            logger.info(
                f"Tier changed for org {organization_id}: {old_tier} -> {subscription_tier}"
            )
        except Exception as e:
            logger.debug(f"Failed to emit tier change webhook: {e}")
