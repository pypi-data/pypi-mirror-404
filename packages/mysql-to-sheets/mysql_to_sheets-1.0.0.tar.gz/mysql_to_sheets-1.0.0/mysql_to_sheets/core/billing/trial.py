"""Trial period management for subscription trials.

Provides functions to manage trial periods for organizations,
including starting trials, checking status, and enforcing
trial access to premium features.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.logging_utils import get_module_logger
from mysql_to_sheets.core.tenant import get_tenant_db_path

logger = get_module_logger(__name__)


class TrialStatus(str, Enum):
    """Trial period status values."""

    ACTIVE = "active"  # Trial is currently active
    EXPIRED = "expired"  # Trial has ended without conversion
    CONVERTED = "converted"  # Trial converted to paid subscription
    NONE = "none"  # No trial (never started or not applicable)


@dataclass
class TrialInfo:
    """Information about an organization's trial status.

    Attributes:
        organization_id: Organization ID.
        status: Current trial status.
        trial_ends_at: When the trial ends (or ended).
        days_remaining: Days left in trial (0 if expired/none).
        billing_status: Current billing status.
        subscription_tier: Current subscription tier.
    """

    organization_id: int
    status: TrialStatus
    trial_ends_at: datetime | None = None
    days_remaining: int = 0
    billing_status: str = "active"
    subscription_tier: str = "free"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "organization_id": self.organization_id,
            "status": self.status.value,
            "trial_ends_at": self.trial_ends_at.isoformat() if self.trial_ends_at else None,
            "days_remaining": self.days_remaining,
            "billing_status": self.billing_status,
            "subscription_tier": self.subscription_tier,
        }


def start_trial(
    organization_id: int,
    days: int | None = None,
    db_path: str | None = None,
) -> TrialInfo:
    """Start a trial period for an organization.

    Sets the organization's billing_status to 'trialing' and
    subscription_tier to 'pro' for the trial period.

    Args:
        organization_id: Organization ID.
        days: Trial duration in days. If None, uses TRIAL_PERIOD_DAYS config.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        TrialInfo with updated trial status.

    Raises:
        ValueError: If organization not found or already has active trial.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    if days is None:
        config = get_config()
        days = config.trial_period_days

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    org = repo.get_by_id(organization_id)

    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    # Prevent trial restart: if org has ever had a trial, reject
    if org.trial_ends_at is not None:
        if org.trial_ends_at > datetime.now(timezone.utc):
            raise ValueError("Organization already has an active trial")
        else:
            raise ValueError("Organization has already used its trial period")

    # Start trial
    now = datetime.now(timezone.utc)
    trial_end = now + timedelta(days=days)

    org.billing_status = "trialing"
    org.subscription_tier = "pro"  # Trial gets PRO features
    org.trial_ends_at = trial_end

    repo.update(org)

    logger.info(f"Started trial for org {organization_id}: ends {trial_end.isoformat()}")

    # Emit webhook for trial started
    _emit_trial_webhook(
        event="subscription.trial_started",
        organization_id=organization_id,
        organization_slug=org.slug,
        trial_ends_at=trial_end,
        trial_days_remaining=days,
        db_path=db_path,
    )

    return TrialInfo(
        organization_id=organization_id,
        status=TrialStatus.ACTIVE,
        trial_ends_at=trial_end,
        days_remaining=days,
        billing_status="trialing",
        subscription_tier="pro",
    )


def check_trial_status(
    organization_id: int,
    db_path: str | None = None,
) -> TrialInfo:
    """Check the trial status for an organization.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        TrialInfo with current trial status.

    Raises:
        ValueError: If organization not found.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    org = repo.get_by_id(organization_id)

    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    # Determine trial status
    status = TrialStatus.NONE
    days_remaining = 0

    if org.trial_ends_at:
        now = datetime.now(timezone.utc)
        # Handle naive datetime
        trial_end = org.trial_ends_at
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=timezone.utc)

        if org.billing_status == "trialing":
            if trial_end > now:
                status = TrialStatus.ACTIVE
                days_remaining = max(0, (trial_end - now).days)
            else:
                status = TrialStatus.EXPIRED
        elif org.subscription_tier in ("pro", "business", "enterprise"):
            # Has paid tier, trial converted
            status = TrialStatus.CONVERTED
        else:
            # Trial ended without conversion
            status = TrialStatus.EXPIRED

    return TrialInfo(
        organization_id=organization_id,
        status=status,
        trial_ends_at=org.trial_ends_at,
        days_remaining=days_remaining,
        billing_status=org.billing_status,
        subscription_tier=org.subscription_tier,
    )


def get_trial_days_remaining(
    organization_id: int,
    db_path: str | None = None,
) -> int:
    """Get the number of days remaining in the trial.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        Days remaining (0 if no trial or expired).
    """
    info = check_trial_status(organization_id, db_path)
    return info.days_remaining


def is_trial_active(
    organization_id: int,
    db_path: str | None = None,
) -> bool:
    """Check if the organization has an active trial.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        True if trial is currently active.
    """
    info = check_trial_status(organization_id, db_path)
    return info.status == TrialStatus.ACTIVE


def expire_trial(
    organization_id: int,
    db_path: str | None = None,
) -> TrialInfo:
    """Manually expire an organization's trial.

    Reverts the organization to FREE tier if not converted.

    Args:
        organization_id: Organization ID.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        TrialInfo with updated status.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    org = repo.get_by_id(organization_id)

    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    if org.billing_status == "trialing":
        org.billing_status = "active"
        org.subscription_tier = "free"  # Revert to free tier
        repo.update(org)

        logger.info(f"Expired trial for org {organization_id}")

    return check_trial_status(organization_id, db_path)


def convert_trial(
    organization_id: int,
    new_tier: str,
    billing_customer_id: str | None = None,
    subscription_period_end: datetime | None = None,
    db_path: str | None = None,
) -> TrialInfo:
    """Convert a trial to a paid subscription.

    Args:
        organization_id: Organization ID.
        new_tier: New subscription tier (pro, business, enterprise).
        billing_customer_id: External billing customer ID.
        subscription_period_end: When the subscription period ends.
        db_path: Database path. If None, uses default tenant path.

    Returns:
        TrialInfo with updated status.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    org = repo.get_by_id(organization_id)

    if not org:
        raise ValueError(f"Organization {organization_id} not found")

    old_tier = org.subscription_tier
    org.subscription_tier = new_tier
    org.billing_status = "active"
    if billing_customer_id:
        org.billing_customer_id = billing_customer_id
    if subscription_period_end:
        org.subscription_period_end = subscription_period_end

    repo.update(org)

    logger.info(f"Converted trial for org {organization_id}: {old_tier} -> {new_tier}")

    # Emit webhook for tier change
    _emit_trial_webhook(
        event="subscription.tier_changed",
        organization_id=organization_id,
        organization_slug=org.slug,
        old_tier=old_tier,
        new_tier=new_tier,
        db_path=db_path,
    )

    return check_trial_status(organization_id, db_path)


def check_expiring_trials(
    days_threshold: int = 3,
    db_path: str | None = None,
) -> list[TrialInfo]:
    """Find trials that are expiring soon.

    Used by scheduled job to send reminders.

    Args:
        days_threshold: Days before expiry to consider "expiring soon".
        db_path: Database path. If None, uses default tenant path.

    Returns:
        List of TrialInfo for expiring trials.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    from mysql_to_sheets.models.organizations import get_organization_repository

    repo = get_organization_repository(db_path)
    orgs = repo.get_all(include_inactive=False)

    expiring = []
    now = datetime.now(timezone.utc)
    threshold = now + timedelta(days=days_threshold)

    for org in orgs:
        if org.billing_status == "trialing" and org.trial_ends_at:
            trial_end = org.trial_ends_at
            if trial_end.tzinfo is None:
                trial_end = trial_end.replace(tzinfo=timezone.utc)

            if now < trial_end <= threshold:
                if org.id is None:
                    continue
                days_remaining = (trial_end - now).days
                expiring.append(
                    TrialInfo(
                        organization_id=org.id,
                        status=TrialStatus.ACTIVE,
                        trial_ends_at=org.trial_ends_at,
                        days_remaining=days_remaining,
                        billing_status=org.billing_status,
                        subscription_tier=org.subscription_tier,
                    )
                )

                # Emit webhook for trial ending
                _emit_trial_webhook(
                    event="subscription.trial_ending",
                    organization_id=org.id,
                    organization_slug=org.slug,
                    trial_ends_at=org.trial_ends_at,
                    trial_days_remaining=days_remaining,
                    db_path=db_path,
                )

    return expiring


def _emit_trial_webhook(
    event: str,
    organization_id: int,
    organization_slug: str | None = None,
    trial_ends_at: datetime | None = None,
    trial_days_remaining: int | None = None,
    old_tier: str | None = None,
    new_tier: str | None = None,
    db_path: str | None = None,
) -> None:
    """Emit a trial/subscription webhook.

    Args:
        event: Event type.
        organization_id: Organization ID.
        organization_slug: Organization slug.
        trial_ends_at: When trial ends.
        trial_days_remaining: Days remaining.
        old_tier: Previous tier (for tier changes).
        new_tier: New tier (for tier changes).
        db_path: Database path.
    """
    try:
        from mysql_to_sheets.core.webhooks.payload import create_subscription_payload

        payload = create_subscription_payload(
            event=event,
            organization_id=organization_id,
            organization_slug=organization_slug,
            old_tier=old_tier,
            new_tier=new_tier,
            trial_ends_at=trial_ends_at.isoformat() if trial_ends_at else None,
            trial_days_remaining=trial_days_remaining,
        )

        logger.info(f"Trial webhook: {event} for org {organization_id}")
    except (OSError, RuntimeError, ImportError) as e:
        logger.debug(f"Failed to emit trial webhook: {e}")


def get_trial_tier_for_feature_check(
    organization_id: int,
    db_path: str | None = None,
) -> str:
    """Get the effective tier for feature checking.

    Organizations in active trial get PRO tier features.

    Args:
        organization_id: Organization ID.
        db_path: Database path.

    Returns:
        Effective tier for feature access.
    """
    if db_path is None:
        db_path = get_tenant_db_path()

    try:
        from mysql_to_sheets.models.organizations import get_organization_repository

        repo = get_organization_repository(db_path)
        org = repo.get_by_id(organization_id)

        if org:
            # If on active trial, return pro tier
            if org.billing_status == "trialing" and org.trial_ends_at:
                trial_end = org.trial_ends_at
                if trial_end.tzinfo is None:
                    trial_end = trial_end.replace(tzinfo=timezone.utc)
                if trial_end > datetime.now(timezone.utc):
                    return "pro"

            return org.subscription_tier
    except (ImportError, OSError, RuntimeError) as e:
        logger.debug(f"Failed to get trial tier: {e}")

    return "free"
