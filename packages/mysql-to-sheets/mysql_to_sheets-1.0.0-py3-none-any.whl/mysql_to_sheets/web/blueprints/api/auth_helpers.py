"""Shared authentication helpers for web API blueprints.

Provides JSON-based authentication checks for API endpoints.
These differ from web/decorators.py which use redirects for HTML pages.
"""

from typing import Any

from flask import session


def _get_user_or_401(
    current: dict[str, Any] | None,
) -> tuple[dict[str, Any], int] | dict[str, Any]:
    """Check if user is None and return error response or the user dict.

    Args:
        current: User dict from get_current_user() or None.

    Returns:
        If current is None: tuple of (error_dict, 401)
        If current is valid: the user dict
    """
    if current is None:
        return {"success": False, "error": "Unauthorized", "message": "Unauthorized"}, 401
    return current


def _require_login() -> tuple[dict[str, Any], int] | None:
    """Check if user is logged in, return error response if not.

    Returns:
        None if authenticated, or tuple of (error_dict, 401) if not.
    """
    if not session.get("user_id"):
        return {
            "success": False,
            "error": "Authentication required",
            "message": "Authentication required",
        }, 401
    return None


def _require_admin() -> tuple[dict[str, Any], int] | None:
    """Check if user is admin or owner, return error response if not.

    Returns:
        None if admin/owner, or tuple of (error_dict, status_code) if not.
    """
    if not session.get("user_id"):
        return {
            "success": False,
            "error": "Authentication required",
            "message": "Authentication required",
        }, 401
    if session.get("role") not in ("admin", "owner"):
        return {
            "success": False,
            "error": "Admin access required",
            "message": "Admin access required",
        }, 403
    return None


def _require_operator() -> tuple[dict[str, Any], int] | None:
    """Check if user is operator or higher, return error response if not.

    Returns:
        None if operator/admin/owner, or tuple of (error_dict, status_code) if not.
    """
    auth_error = _require_login()
    if auth_error:
        return auth_error
    if session.get("role") not in ("admin", "owner", "operator"):
        return {
            "success": False,
            "error": "Operator access required",
            "message": "Operator access required",
        }, 403
    return None
