"""Context helpers for Flask templates and routes.

This module provides functions for accessing the current user context
and injecting user data into templates.
"""

from typing import Any

from flask import session

from mysql_to_sheets import __version__


def get_current_user() -> dict[str, Any] | None:
    """Get current user from session.

    Returns:
        User info dict with id, email, display_name, role,
        organization_id, and organization_name, or None if not logged in.
    """
    if not session.get("user_id"):
        return None
    return {
        "id": session.get("user_id"),
        "email": session.get("email"),
        "display_name": session.get("display_name"),
        "role": session.get("role"),
        "organization_id": session.get("organization_id"),
        "organization_name": session.get("organization_name"),
    }


def inject_user() -> dict[str, Any]:
    """Context processor to inject current_user and version into all templates.

    Returns:
        Dict with current_user and version keys for template context.
    """
    return {
        "current_user": get_current_user(),
        "version": __version__,
    }


def is_authenticated() -> bool:
    """Check if current user is authenticated.

    Returns:
        True if user is logged in, False otherwise.
    """
    return session.get("user_id") is not None


def has_role(required_roles: list[str] | str) -> bool:
    """Check if current user has one of the required roles.

    Args:
        required_roles: Single role string or list of acceptable roles.

    Returns:
        True if user has one of the required roles.
    """
    if not is_authenticated():
        return False

    if isinstance(required_roles, str):
        required_roles = [required_roles]

    user_role = session.get("role", "viewer")
    return user_role in required_roles


def is_admin() -> bool:
    """Check if current user is admin or owner.

    Returns:
        True if user has admin or owner role.
    """
    return has_role(["admin", "owner"])


def is_operator() -> bool:
    """Check if current user is operator or higher.

    Returns:
        True if user has operator, admin, or owner role.
    """
    return has_role(["operator", "admin", "owner"])


def get_organization_id() -> int | None:
    """Get current user's organization ID.

    Returns:
        Organization ID or None if not logged in.
    """
    return session.get("organization_id")


def get_effective_tier_from_license() -> str:
    """Get effective tier based on license validation.

    This takes precedence over organization tier in the session
    since the license is the authoritative source for self-hosted deployments.

    Returns:
        Tier string (e.g., 'free', 'pro', 'business', 'enterprise').
    """
    from mysql_to_sheets.core.config import get_config
    from mysql_to_sheets.core.license import (
        get_effective_tier,
        validate_license,
    )

    config = get_config()

    license_info = validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )

    # Get effective tier from license validation
    effective_tier = get_effective_tier(license_info)
    return effective_tier.value


def has_tier_access(feature: str) -> bool:
    """Check if current tier has access to a feature.

    Args:
        feature: Feature name to check.

    Returns:
        True if the effective tier allows access to the feature.
    """
    from mysql_to_sheets.core.tier import (
        Tier,
        get_feature_tier,
        tier_allows,
    )

    try:
        effective_tier_str = get_effective_tier_from_license()
        effective_tier = Tier(effective_tier_str)
        required_tier = get_feature_tier(feature)
        return tier_allows(effective_tier, required_tier)
    except ValueError:
        return True  # Unknown feature - allow by default
