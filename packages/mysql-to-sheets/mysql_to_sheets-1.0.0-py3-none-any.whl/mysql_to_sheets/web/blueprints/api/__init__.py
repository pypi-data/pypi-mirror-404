"""API blueprints for AJAX operations.

This package contains JSON API endpoints used by the web dashboard
for dynamic operations like sync, schedule management, etc.
"""

from typing import Any

from flask import jsonify

from mysql_to_sheets.web.blueprints.api.configs import configs_api_bp
from mysql_to_sheets.web.blueprints.api.schedules import schedules_api_bp
from mysql_to_sheets.web.blueprints.api.sync import sync_api_bp
from mysql_to_sheets.web.blueprints.api.users import users_api_bp
from mysql_to_sheets.web.blueprints.api.webhooks import webhooks_api_bp


def success_response(
    data: dict[str, Any] | None = None,
    message: str = "Success",
    status_code: int = 200,
) -> tuple[Any, int]:
    """Return a standardized success response.

    Args:
        data: Additional data to include in the response.
        message: Success message.
        status_code: HTTP status code.

    Returns:
        Tuple of (jsonify response, status code).
    """
    response = {"success": True, "message": message}
    if data:
        response.update(data)
    return jsonify(response), status_code


def error_response(
    error: str,
    message: str | None = None,
    status_code: int = 400,
    **extra: Any,
) -> tuple[Any, int]:
    """Return a standardized error response.

    ALWAYS includes both 'error' and 'message' fields to prevent
    "Error:undefined" in frontend.

    Args:
        error: Error description.
        message: Human-readable message (defaults to error if not provided).
        status_code: HTTP status code.
        **extra: Additional fields to include in the response.

    Returns:
        Tuple of (jsonify response, status code).
    """
    response = {
        "success": False,
        "error": error,
        "message": message or error,  # Fallback message to error
        **extra,
    }
    return jsonify(response), status_code


__all__ = [
    "sync_api_bp",
    "schedules_api_bp",
    "users_api_bp",
    "configs_api_bp",
    "webhooks_api_bp",
    "success_response",
    "error_response",
]
