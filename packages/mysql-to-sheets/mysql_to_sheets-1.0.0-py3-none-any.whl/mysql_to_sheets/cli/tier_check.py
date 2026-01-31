"""CLI tier enforcement for premium features.

Provides utilities to check tier requirements before executing CLI commands.
This ensures CLI commands respect the same tier restrictions as the API.

Example:
    >>> from mysql_to_sheets.cli.tier_check import check_cli_tier, require_cli_tier
    >>>
    >>> # Manual check
    >>> allowed, error = check_cli_tier("scheduler")
    >>> if not allowed:
    ...     print(error["message"])
    >>>
    >>> # Decorator usage
    >>> @require_cli_tier("scheduler")
    ... def cmd_schedule_add(args):
    ...     # Only runs if tier allows scheduler feature
    ...     pass
"""

import functools
from typing import Any, Callable, TypeVar

from mysql_to_sheets.core.config import get_config
from mysql_to_sheets.core.license import (
    LicenseStatus,
    get_effective_tier,
    validate_license,
)
from mysql_to_sheets.core.tier import (
    FEATURE_TIERS,
    get_feature_tier,
    tier_allows,
)

F = TypeVar("F", bound=Callable[..., int])


def check_cli_tier(feature: str) -> tuple[bool, dict[str, Any] | None]:
    """Check if the current license tier allows a feature.

    Validates the license key from configuration and checks if the
    effective tier is sufficient for the requested feature.

    Args:
        feature: Feature name to check (e.g., "scheduler", "webhooks").

    Returns:
        Tuple of (allowed, error_dict).
        - If allowed: (True, None)
        - If not allowed: (False, dict with error details)

    Example:
        >>> allowed, error = check_cli_tier("scheduler")
        >>> if not allowed:
        ...     print(error["message"])
        ...     return 1  # Exit with error
    """
    config = get_config()

    # Validate the license
    license_info = validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )

    # Get effective tier (FREE if license is invalid/missing/expired)
    effective_tier = get_effective_tier(license_info)

    # Get required tier for this feature
    try:
        required_tier = get_feature_tier(feature)
    except ValueError:
        # Unknown feature - allow by default (fail-open for unknown features)
        return True, None

    # Check if tier is sufficient
    if tier_allows(effective_tier, required_tier):
        return True, None

    # Build helpful error message
    if license_info.status == LicenseStatus.MISSING:
        message = (
            f"This feature requires {required_tier.value.upper()} tier or higher.\n"
            f"Set LICENSE_KEY in your .env file with your subscription license key."
        )
        code = "LICENSE_001"
    elif license_info.status == LicenseStatus.EXPIRED:
        expires_str = (
            license_info.expires_at.strftime("%Y-%m-%d")
            if license_info.expires_at
            else "unknown date"
        )
        message = (
            f"License expired on {expires_str}.\n"
            f"Please renew your subscription to access {required_tier.value.upper()} features."
        )
        code = "LICENSE_003"
    elif license_info.status == LicenseStatus.INVALID:
        message = (
            f"Invalid license key: {license_info.error}\n"
            f"Check that LICENSE_KEY is correct and has not been modified."
        )
        code = "LICENSE_002"
    else:
        # Valid license but insufficient tier
        message = (
            f"This feature requires {required_tier.value.upper()} tier or higher.\n"
            f"Current tier: {effective_tier.value.upper()}\n"
            f"Upgrade your subscription to access this feature."
        )
        code = "LICENSE_004"

    return False, {
        "success": False,
        "message": message,
        "code": code,
        "feature": feature,
        "required_tier": required_tier.value,
        "current_tier": effective_tier.value,
        "license_status": license_info.status.value,
    }


def require_cli_tier(feature: str) -> Callable[[F], F]:
    """Decorator to require a specific tier for a CLI command.

    The decorated function should be a CLI command handler that
    takes args: argparse.Namespace and returns an exit code (int).

    If the tier check fails, the decorator prints an error message
    and returns exit code 1 without calling the original function.

    Args:
        feature: Feature name that requires tier check.

    Returns:
        Decorator function.

    Example:
        >>> @require_cli_tier("scheduler")
        ... def cmd_schedule_add(args: argparse.Namespace) -> int:
        ...     # Only runs if license allows scheduler feature
        ...     return 0
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> int:
            allowed, error = check_cli_tier(feature)

            if not allowed:
                # Check for output format preference in args
                output_format = "text"
                if args and hasattr(args[0], "output"):
                    output_format = getattr(args[0], "output", "text")
                elif args and hasattr(args[0], "json_output"):
                    output_format = "json" if getattr(args[0], "json_output", False) else "text"

                if output_format == "json":
                    import json

                    print(json.dumps(error, indent=2))
                else:
                    assert error is not None
                    print(f"Error: {error['message']}")
                    print()
                    print(f"  Code: {error['code']}")
                    print(f"  Required tier: {error['required_tier'].upper()}")
                    print(f"  Current tier: {error['current_tier'].upper()}")

                return 1

            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def get_tier_status_for_cli() -> dict[str, Any]:
    """Get current tier status for display in CLI.

    Returns information about the current license and tier for
    display in status commands.

    Returns:
        Dictionary with tier status information.
    """
    config = get_config()

    license_info = validate_license(
        config.license_key,
        config.license_public_key or None,
        config.license_offline_grace_days,
    )

    effective_tier = get_effective_tier(license_info)

    # Get available features for this tier
    available_features = [f for f, t in FEATURE_TIERS.items() if tier_allows(effective_tier, t)]

    return {
        "tier": effective_tier.value,
        "license_status": license_info.status.value,
        "customer_id": license_info.customer_id,
        "email": license_info.email,
        "expires_at": license_info.expires_at.isoformat() if license_info.expires_at else None,
        "days_until_expiry": license_info.days_until_expiry,
        "features": available_features,
        "is_licensed": license_info.status in (LicenseStatus.VALID, LicenseStatus.GRACE_PERIOD),
    }
