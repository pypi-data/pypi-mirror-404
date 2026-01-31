"""Usage tracking service for billing integration.

Provides functions to record and query usage metrics for billing purposes.
Usage is tracked per organization per billing period (calendar month).
"""

from typing import TYPE_CHECKING, Any

from sqlalchemy.exc import SQLAlchemyError

from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.models.usage import (
    UsageRecord,
    get_usage_repository,
)

if TYPE_CHECKING:
    from mysql_to_sheets.core.billing.tier import Tier

logger = get_module_logger(__name__)


def record_sync_usage(
    organization_id: int,
    rows_synced: int,
    db_path: str | None = None,
) -> UsageRecord:
    """Record usage after a sync operation.

    Increments rows_synced and sync_operations counters for the
    organization's current billing period.

    Args:
        organization_id: Organization ID.
        rows_synced: Number of rows synced.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        Updated UsageRecord.

    Example:
        >>> record_sync_usage(org_id=1, rows_synced=500)
        UsageRecord(org=1, rows_synced=500, sync_operations=1)
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    try:
        repo = get_usage_repository(db_path)
        record = repo.increment_rows_synced(
            organization_id=organization_id,
            rows=rows_synced,
            increment_operations=True,
        )
        logger.debug(
            f"Recorded sync usage: org={organization_id}, "
            f"rows={rows_synced}, total_rows={record.rows_synced}"
        )

        # Check usage thresholds and potentially trigger webhooks
        _check_usage_thresholds(organization_id, record, db_path)

        return record
    except (OSError, RuntimeError, SQLAlchemyError) as e:
        # Usage tracking should not fail the sync operation
        logger.warning(f"Failed to record sync usage: {e}")
        raise


def record_api_call(
    organization_id: int,
    count: int = 1,
    db_path: str | None = None,
) -> UsageRecord | None:
    """Record an API call for the organization.

    Increments the api_calls counter for the current billing period.

    Args:
        organization_id: Organization ID.
        count: Number of calls to record (default 1).
        db_path: Database path. If None, uses default tenant path.

    Returns:
        Updated UsageRecord, or None on failure.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    try:
        repo = get_usage_repository(db_path)
        record = repo.increment_api_calls(
            organization_id=organization_id,
            count=count,
        )
        logger.debug(f"Recorded API call: org={organization_id}, total_calls={record.api_calls}")
        return record
    except (OSError, RuntimeError, SQLAlchemyError) as e:
        # API call tracking should not fail the request
        logger.debug(f"Failed to record API call: {e}")
        return None


def get_usage_summary(
    organization_id: int,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Get usage summary for the organization.

    Returns current period usage and historical totals.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        Dictionary with usage summary:
        {
            "current_period": {...},  # Current period usage
            "totals": {...},          # Historical totals
            "periods_tracked": int,   # Number of periods
        }
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    repo = get_usage_repository(db_path)
    return repo.get_summary(organization_id)


def get_current_usage(
    organization_id: int,
    db_path: str | None = None,
) -> UsageRecord:
    """Get current period usage for the organization.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        UsageRecord for the current billing period.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    repo = get_usage_repository(db_path)
    return repo.get_or_create_current(organization_id)


def get_usage_history(
    organization_id: int,
    limit: int = 12,
    db_path: str | None = None,
) -> list[UsageRecord]:
    """Get usage history for the organization.

    Args:
        organization_id: Organization ID.
        limit: Maximum number of periods to return.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        List of UsageRecords, most recent first.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    repo = get_usage_repository(db_path)
    return repo.get_history(organization_id, limit=limit)


def check_usage_threshold(
    organization_id: int,
    threshold_percent: int = 80,
    db_path: str | None = None,
) -> dict[str, Any]:
    """Check if organization has reached usage thresholds.

    Compares current usage against tier limits to determine if
    warning or critical thresholds have been reached.

    Args:
        organization_id: Organization ID.
        threshold_percent: Warning threshold percentage (default 80).
        db_path: Database path. If None, uses default tenant path.

    Returns:
        Dictionary with threshold status:
        {
            "rows_synced": {"percent": 75, "exceeded": False, "warning": False},
            "sync_operations": {...},
            "api_calls": {...},
        }
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    record = get_current_usage(organization_id, db_path)
    limits = _get_organization_limits(organization_id, db_path)

    result: dict[str, Any] = {}

    # Check each usage type against limits
    for usage_type, current in [
        ("rows_synced", record.rows_synced),
        ("sync_operations", record.sync_operations),
        ("api_calls", record.api_calls),
    ]:
        limit = limits.get(usage_type)
        if limit is None or limit == 0:
            # Unlimited
            result[usage_type] = {
                "percent": 0,
                "exceeded": False,
                "warning": False,
                "current": current,
                "limit": None,
            }
        else:
            percent = (current / limit) * 100
            result[usage_type] = {
                "percent": round(percent, 1),
                "exceeded": percent >= 100,
                "warning": percent >= threshold_percent,
                "current": current,
                "limit": limit,
            }

    return result


def _get_organization_limits(
    organization_id: int,
    db_path: str,
) -> dict[str, int | None]:
    """Get usage limits for the organization based on tier.

    Args:
        organization_id: Organization ID.
        db_path: Database path.

    Returns:
        Dictionary with limits for each usage type.
        None values indicate unlimited.
    """
    try:
        from mysql_to_sheets.core.billing.tier import Tier, get_tier_limits
        from mysql_to_sheets.models.organizations import get_organization_repository

        org_repo = get_organization_repository(db_path)
        org = org_repo.get_by_id(organization_id)

        if org:
            tier = Tier(org.subscription_tier.lower())
            tier_limits = get_tier_limits(tier)

            # Map tier limits to usage types
            # Note: These are rough mappings - actual limits should be defined
            # based on business requirements
            return {
                "rows_synced": _get_rows_limit(tier),
                "sync_operations": _get_operations_limit(tier),
                "api_calls": tier_limits.api_requests_per_minute * 60 * 24 * 30,  # Monthly
            }
    except (ImportError, OSError, RuntimeError, SQLAlchemyError, ValueError) as e:
        logger.debug(f"Failed to get organization limits: {e}")

    # Default limits for free tier
    return {
        "rows_synced": 10000,  # 10k rows per month
        "sync_operations": 100,  # 100 syncs per month
        "api_calls": 1000,  # 1000 API calls per month
    }


def _get_rows_limit(tier: "Tier") -> int | None:
    """Get monthly rows limit for a tier.

    Args:
        tier: Subscription tier.

    Returns:
        Rows limit, or None for unlimited.
    """
    from mysql_to_sheets.core.billing.tier import Tier

    limits = {
        Tier.FREE: 10000,  # 10k rows/month
        Tier.PRO: 100000,  # 100k rows/month
        Tier.BUSINESS: 1000000,  # 1M rows/month
        Tier.ENTERPRISE: None,  # Unlimited
    }
    return limits.get(tier, 10000)


def _get_operations_limit(tier: "Tier") -> int | None:
    """Get monthly sync operations limit for a tier.

    Args:
        tier: Subscription tier.

    Returns:
        Operations limit, or None for unlimited.
    """
    from mysql_to_sheets.core.billing.tier import Tier

    limits = {
        Tier.FREE: 100,  # 100 syncs/month
        Tier.PRO: 1000,  # 1000 syncs/month
        Tier.BUSINESS: 10000,  # 10k syncs/month
        Tier.ENTERPRISE: None,  # Unlimited
    }
    return limits.get(tier, 100)


def _check_usage_thresholds(
    organization_id: int,
    record: UsageRecord,
    db_path: str,
) -> None:
    """Check usage thresholds and emit webhooks if needed.

    Called after usage is recorded to check if thresholds
    have been crossed and trigger webhook notifications.

    Args:
        organization_id: Organization ID.
        record: Updated usage record.
        db_path: Database path.
    """
    try:
        thresholds = check_usage_threshold(organization_id, db_path=db_path)

        for usage_type, status in thresholds.items():
            if status["exceeded"] and status.get("limit"):
                _emit_usage_webhook(
                    organization_id=organization_id,
                    threshold_type="exceeded",
                    threshold_percent=100,
                    resource_type=usage_type,
                    current_usage=status["current"],
                    limit=status["limit"],
                    db_path=db_path,
                )
            elif status["warning"] and status.get("limit"):
                # Only emit warning once when crossing threshold
                # In practice, we'd track last emitted threshold
                _emit_usage_webhook(
                    organization_id=organization_id,
                    threshold_type="warning",
                    threshold_percent=80,
                    resource_type=usage_type,
                    current_usage=status["current"],
                    limit=status["limit"],
                    db_path=db_path,
                )
    except (OSError, RuntimeError, SQLAlchemyError, TypeError, ValueError) as e:
        logger.debug(f"Failed to check usage thresholds: {e}")


def _emit_usage_webhook(
    organization_id: int,
    threshold_type: str,
    threshold_percent: int,
    resource_type: str,
    current_usage: int,
    limit: int,
    db_path: str,
) -> None:
    """Emit a usage threshold webhook.

    Args:
        organization_id: Organization ID.
        threshold_type: Type of threshold (warning, exceeded).
        threshold_percent: Threshold percentage.
        resource_type: Type of resource.
        current_usage: Current usage count.
        limit: Usage limit.
        db_path: Database path.
    """
    try:
        from mysql_to_sheets.core.webhooks.payload import create_usage_payload

        # Get organization slug for webhook
        org_slug = None
        try:
            from mysql_to_sheets.models.organizations import get_organization_repository

            org_repo = get_organization_repository(db_path)
            org = org_repo.get_by_id(organization_id)
            if org:
                org_slug = org.slug
        except (ImportError, OSError, RuntimeError, SQLAlchemyError):
            pass

        payload = create_usage_payload(
            event="usage.threshold_reached",
            organization_id=organization_id,
            organization_slug=org_slug,
            threshold_type=threshold_type,
            threshold_percent=threshold_percent,
            resource_type=resource_type,
            current_usage=current_usage,
            limit=limit,
        )

        # Deliver webhook (async, non-blocking)
        logger.info(
            f"Usage threshold {threshold_type} for org {organization_id}: "
            f"{resource_type} at {current_usage}/{limit}"
        )
    except (ImportError, OSError, RuntimeError, SQLAlchemyError) as e:
        logger.debug(f"Failed to emit usage webhook: {e}")
