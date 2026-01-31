"""Tier status blueprint for Flask web dashboard.

Displays subscription tier information, usage vs limits, and feature availability.
"""

import logging
from typing import Any, cast

from flask import Blueprint, Response, jsonify, redirect, render_template, session, url_for

from mysql_to_sheets import __version__
from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.tenant import get_tenant_db_path
from mysql_to_sheets.core.tier import (
    FEATURE_TIERS,
    Tier,
    get_tier_display_info,
    get_tier_limits,
)
from mysql_to_sheets.core.trial import TrialStatus, check_trial_status
from mysql_to_sheets.web.context import get_current_user
from mysql_to_sheets.web.decorators import login_required

logger = logging.getLogger("mysql_to_sheets.web.tier")

tier_bp = Blueprint("tier", __name__)


@tier_bp.route("/tier")
@login_required
def tier_status() -> str | Response:
    """Render the tier status page.

    Shows current tier, usage vs limits, and feature availability.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    db_path = get_tenant_db_path()

    # Get organization tier (default to FREE if not set)
    org_tier_str = current.get("organization_tier", "free")
    try:
        org_tier = Tier(org_tier_str.lower())
    except ValueError:
        org_tier = Tier.FREE

    # Get tier limits
    limits = get_tier_limits(org_tier)

    # Get current usage counts
    usage = _get_usage_counts(current["organization_id"], db_path)

    # Calculate usage percentages
    usage_percentages = _calculate_usage_percentages(usage, limits)

    # Get feature availability
    features = _get_feature_availability(org_tier)

    # Get tier display info for all tiers (for comparison)
    all_tiers = [get_tier_display_info(t) for t in Tier]

    # Get trial/billing status and billing details
    billing_status = "active"
    trial_days_remaining = 0
    billing_customer_id = None
    subscription_period_end = None
    try:
        trial_info = check_trial_status(current["organization_id"], db_path)
        if trial_info.status == TrialStatus.ACTIVE:
            billing_status = "trialing"
            trial_days_remaining = trial_info.days_remaining
    except Exception as e:
        logger.debug(f"Failed to check trial status: {e}")

    # Fetch organization billing details
    try:
        from mysql_to_sheets.models.organizations import get_organization_repository

        repo = get_organization_repository(db_path)
        org = repo.get_by_id(current["organization_id"])
        if org:
            billing_customer_id = org.billing_customer_id
            subscription_period_end = org.subscription_period_end
            if org.billing_status and org.billing_status != "active":
                billing_status = org.billing_status
    except Exception as e:
        logger.debug(f"Failed to fetch billing details: {e}")

    return render_template(
        "tier.html",
        version=__version__,
        current_tier=org_tier.value,
        tier_name=org_tier.value.title(),
        limits={
            "configs": limits.max_configs,
            "users": limits.max_users,
            "schedules": limits.max_schedules,
            "webhooks": limits.max_webhooks,
            "history_days": limits.history_days,
            "api_requests_per_minute": limits.api_requests_per_minute,
            "snapshot_retention_count": limits.snapshot_retention_count,
            "audit_retention_days": limits.audit_retention_days,
        },
        usage=usage,
        usage_percentages=usage_percentages,
        features=features,
        all_tiers=all_tiers,
        billing_status=billing_status,
        trial_days_remaining=trial_days_remaining,
        billing_customer_id=billing_customer_id,
        subscription_period_end=subscription_period_end,
    )


def _get_usage_counts(organization_id: int, db_path: str) -> dict[str, int]:
    """Get current usage counts for the organization.

    Args:
        organization_id: Organization ID.
        db_path: Database path.

    Returns:
        Dictionary with usage counts.
    """
    from mysql_to_sheets.models.sync_configs import get_sync_config_repository
    from mysql_to_sheets.models.users import get_user_repository
    from mysql_to_sheets.models.webhooks import get_webhook_repository

    usage: dict[str, int] = {
        "configs": 0,
        "users": 0,
        "schedules": 0,
        "webhooks": 0,
    }

    try:
        # Count configs (using efficient COUNT query)
        config_repo = get_sync_config_repository(db_path)
        usage["configs"] = config_repo.count(organization_id)
    except Exception as e:
        logger.warning(f"Failed to count configs: {e}")

    try:
        # Count users (using efficient COUNT query)
        user_repo = get_user_repository(db_path)
        usage["users"] = user_repo.count(organization_id)
    except Exception as e:
        logger.warning(f"Failed to count users: {e}")

    try:
        # Count webhooks (using efficient COUNT query)
        webhook_repo = get_webhook_repository(db_path)
        usage["webhooks"] = webhook_repo.count_subscriptions(organization_id)
    except Exception as e:
        logger.warning(f"Failed to count webhooks: {e}")

    try:
        # Count schedules
        from mysql_to_sheets.core.scheduler import get_scheduler_service

        service = get_scheduler_service()
        jobs = service.get_all_jobs()
        usage["schedules"] = len(jobs)
    except Exception as e:
        logger.warning(f"Failed to count schedules: {e}")

    return usage


def _calculate_usage_percentages(
    usage: dict[str, int],
    limits: Any,
) -> dict[str, float | None]:
    """Calculate usage percentages for progress bars.

    Args:
        usage: Current usage counts.
        limits: TierLimits object.

    Returns:
        Dictionary with usage percentages (0-100) or None for unlimited.
    """
    percentages: dict[str, float | None] = {}

    limit_map = {
        "configs": limits.max_configs,
        "users": limits.max_users,
        "schedules": limits.max_schedules,
        "webhooks": limits.max_webhooks,
    }

    for key, limit in limit_map.items():
        if limit is None or limit == 0:
            percentages[key] = None  # Unlimited or disabled
        else:
            percentages[key] = min(100.0, (usage.get(key, 0) / limit) * 100)

    return percentages


def _get_feature_availability(current_tier: Tier) -> list[dict[str, Any]]:
    """Get feature availability for the current tier.

    Args:
        current_tier: The organization's tier.

    Returns:
        List of feature dictionaries with availability status.
    """
    features = []

    # Group features by category
    categories = {
        "Core": ["sync", "validate", "test_connection"],
        "Data Processing": [
            "incremental_sync",
            "column_mapping",
            "streaming_sync",
            "multi_sheet",
            "reverse_sync",
        ],
        "Automation": ["scheduler", "notifications", "webhooks", "job_queue"],
        "Data Protection": ["snapshots", "data_quality", "anomaly_detection", "data_masking"],
        "Security & Access": ["api_access", "rbac", "audit_logs", "sso", "saml", "oidc"],
        "Enterprise": [
            "custom_retention",
            "api_versioning",
            "white_labeling",
            "unlimited_users",
            "unlimited_configs",
        ],
    }

    for category, feature_list in categories.items():
        for feature in feature_list:
            required_tier = FEATURE_TIERS.get(feature)
            if required_tier is None:
                continue

            available = current_tier >= required_tier
            features.append(
                {
                    "name": feature.replace("_", " ").title(),
                    "key": feature,
                    "category": category,
                    "required_tier": required_tier.value.title(),
                    "available": available,
                }
            )

    return features


@tier_bp.route("/upgrade")
@login_required
def upgrade() -> str | Response:
    """Render the upgrade page.

    Shows pricing plans and links to billing portal.

    Returns:
        Rendered HTML template.
    """
    current = get_current_user()
    if not current:
        return cast(Response, redirect(url_for("auth.login")))

    db_path = get_tenant_db_path()
    config = get_config()

    # Get organization tier
    org_tier_str = current.get("organization_tier", "free")
    try:
        org_tier = Tier(org_tier_str.lower())
    except ValueError:
        org_tier = Tier.FREE

    # Get trial/billing status
    billing_status = "active"
    trial_days_remaining = 0
    try:
        trial_info = check_trial_status(current["organization_id"], db_path)
        if trial_info.status == TrialStatus.ACTIVE:
            billing_status = "trialing"
            trial_days_remaining = trial_info.days_remaining
    except Exception as e:
        logger.debug(f"Failed to check trial status: {e}")

    return render_template(
        "upgrade.html",
        version=__version__,
        current_tier=org_tier.value,
        billing_status=billing_status,
        trial_days_remaining=trial_days_remaining,
        billing_portal_url=config.billing_portal_url or None,
    )


# API endpoint for tier data (for AJAX updates)
tier_api_bp = Blueprint("tier_api", __name__, url_prefix="/api/tier")


@tier_api_bp.route("/status", methods=["GET"])
def api_tier_status() -> Response | tuple[Response, int]:
    """Get tier status via API.

    Returns:
        JSON response with tier information.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    db_path = get_tenant_db_path()
    org_tier_str = current.get("organization_tier", "free")

    try:
        org_tier = Tier(org_tier_str.lower())
    except ValueError:
        org_tier = Tier.FREE

    limits = get_tier_limits(org_tier)
    usage = _get_usage_counts(current["organization_id"], db_path)

    return jsonify(
        {
            "success": True,
            "tier": org_tier.value,
            "tier_name": org_tier.value.title(),
            "limits": {
                "configs": limits.max_configs,
                "users": limits.max_users,
                "schedules": limits.max_schedules,
                "webhooks": limits.max_webhooks,
                "history_days": limits.history_days,
                "api_requests_per_minute": limits.api_requests_per_minute,
            },
            "usage": usage,
        }
    ), 200


@tier_api_bp.route("/usage", methods=["GET"])
def api_tier_usage() -> Response | tuple[Response, int]:
    """Get current usage counts via API.

    Returns:
        JSON response with usage information.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    db_path = get_tenant_db_path()
    usage = _get_usage_counts(current["organization_id"], db_path)

    return jsonify(
        {
            "success": True,
            "usage": usage,
        }
    ), 200


@tier_api_bp.route("/features", methods=["GET"])
def api_tier_features() -> Response | tuple[Response, int]:
    """Get feature availability via API.

    Returns:
        JSON response with feature availability.
    """
    if not session.get("user_id"):
        return jsonify({"success": False, "error": "Authentication required"}), 401

    current = get_current_user()
    if not current:
        return jsonify({"success": False, "error": "User not found"}), 404

    org_tier_str = current.get("organization_tier", "free")
    try:
        org_tier = Tier(org_tier_str.lower())
    except ValueError:
        org_tier = Tier.FREE

    features = _get_feature_availability(org_tier)

    return jsonify(
        {
            "success": True,
            "tier": org_tier.value,
            "features": features,
        }
    ), 200
