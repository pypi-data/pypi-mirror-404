"""Authentication and authorization decorators for Flask routes.

This module contains decorators used to protect routes with
authentication, role-based access control, and tier-based feature gates.
"""

import functools
from collections.abc import Callable as CallableABC
from typing import Any, Callable, TypeVar, cast

from flask import Response, jsonify, redirect, render_template, request, session, url_for
from werkzeug.wrappers.response import Response as WerkzeugResponse

from mysql_to_sheets import __version__

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


def login_required(f: F) -> F:
    """Decorator to require login for protected routes.

    Redirects to login page if user is not authenticated.

    Args:
        f: The route function to protect.

    Returns:
        Wrapped function that checks for authentication.
    """

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get("user_id"):
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)

    return cast(F, decorated_function)


def admin_required(f: F) -> F:
    """Decorator to require admin role for protected routes.

    Requires user to be logged in with admin or owner role.

    Args:
        f: The route function to protect.

    Returns:
        Wrapped function that checks for admin role.
    """

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get("user_id"):
            # redirect returns a werkzeug Response which is compatible with Flask Response
            return cast(Response, redirect(url_for("auth.login", next=request.url)))
        role = session.get("role", "viewer")
        if role not in ("admin", "owner"):
            return render_template(
                "error.html",
                version=__version__,
                error="Access Denied",
                message="You do not have permission to access this page.",
            ), 403
        return f(*args, **kwargs)

    return cast(F, decorated_function)


def operator_required(f: F) -> F:
    """Decorator to require operator or higher role.

    Requires user to be logged in with operator, admin, or owner role.

    Args:
        f: The route function to protect.

    Returns:
        Wrapped function that checks for operator role.
    """

    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if not session.get("user_id"):
            return cast(Response, redirect(url_for("auth.login", next=request.url)))
        role = session.get("role", "viewer")
        if role not in ("admin", "owner", "operator"):
            return render_template(
                "error.html",
                version=__version__,
                error="Access Denied",
                message="You do not have permission to access this page.",
            ), 403
        return f(*args, **kwargs)

    return cast(F, decorated_function)


def tier_required(feature: str) -> Callable[[F], F]:
    """Decorator to require a specific tier for a route.

    Validates the license key and checks if the effective tier
    is sufficient for the requested feature.

    Args:
        feature: Feature name to check (e.g., "scheduler", "webhooks").

    Returns:
        Decorator function.

    Example:
        >>> @tier_required("scheduler")
        ... @login_required
        ... def schedule_page():
        ...     return render_template("schedule.html")
    """

    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            from mysql_to_sheets.core.config import get_config
            from mysql_to_sheets.core.license import (
                LicenseStatus,
                get_effective_tier,
                validate_license,
            )
            from mysql_to_sheets.core.tier import get_feature_tier, tier_allows

            config = get_config()

            # Validate the license
            license_info = validate_license(
                config.license_key,
                config.license_public_key or None,
                config.license_offline_grace_days,
            )

            # Get effective tier
            effective_tier = get_effective_tier(license_info)

            # Get required tier for this feature
            try:
                required_tier = get_feature_tier(feature)
            except ValueError:
                # Unknown feature - allow by default
                return f(*args, **kwargs)

            # Check if tier is sufficient
            if tier_allows(effective_tier, required_tier):
                return f(*args, **kwargs)

            # Build error message
            if license_info.status == LicenseStatus.MISSING:
                message = (
                    f"This feature requires {required_tier.value.upper()} tier or higher. "
                    "Please configure a license key to access this feature."
                )
            elif license_info.status == LicenseStatus.EXPIRED:
                message = "Your license has expired. Please renew to access premium features."
            elif license_info.status == LicenseStatus.INVALID:
                message = f"Invalid license key: {license_info.error}"
            else:
                message = (
                    f"This feature requires {required_tier.value.upper()} tier. "
                    f"Your current tier is {effective_tier.value.upper()}. "
                    "Please upgrade your subscription to access this feature."
                )

            # Check if this is an API request
            if request.is_json or request.path.startswith("/api/"):
                return jsonify(
                    {
                        "success": False,
                        "error": "tier_required",
                        "message": message,
                        "required_tier": required_tier.value,
                        "current_tier": effective_tier.value,
                    }
                ), 403

            # Render error page for browser requests
            return render_template(
                "error.html",
                version=__version__,
                error="Upgrade Required",
                message=message,
            ), 403

        return cast(F, decorated_function)

    return decorator
