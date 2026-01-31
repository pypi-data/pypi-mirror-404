"""Standardized HTTP response utilities for Flask web dashboard.

This module provides consistent response formatting across all web blueprints,
matching the API layer patterns for error handling and success responses.

Example:
    >>> from mysql_to_sheets.web.responses import error_response, success_response
    >>>
    >>> # Return standardized error
    >>> return error_response("CONFIG_404", "Configuration not found", 404)
    >>>
    >>> # Return success with data
    >>> return success_response({"items": items, "total": len(items)})
"""

from typing import Any

from flask import Response, jsonify

from mysql_to_sheets.core.exceptions import SyncError


def error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: dict[str, Any] | None = None,
    error_type: str | None = None,
    remediation: str | None = None,
) -> tuple[Response, int]:
    """Create a standardized error response.

    Args:
        error_code: Error code (e.g., "CONFIG_404", "DB_201").
        message: Human-readable error message.
        status_code: HTTP status code (default: 400).
        details: Optional dictionary with additional error details.
        error_type: Optional error type classification.
        remediation: Optional remediation hint for the user.

    Returns:
        Tuple of (Flask Response, status code).

    Example:
        >>> return error_response(
        ...     "CONFIG_404",
        ...     "Configuration not found",
        ...     status_code=404,
        ...     details={"config_id": 123},
        ... )
    """
    response: dict[str, Any] = {
        "success": False,
        "error": error_code,
        "message": message,
    }
    if error_type:
        response["error_type"] = error_type
    if details:
        response["details"] = details
    if remediation:
        response["remediation"] = remediation
    return jsonify(response), status_code


def error_response_from_exception(
    exc: SyncError,
    status_code: int = 500,
) -> tuple[Response, int]:
    """Create a standardized error response from a SyncError exception.

    Args:
        exc: SyncError or subclass with error details.
        status_code: HTTP status code (default: 500).

    Returns:
        Tuple of (Flask Response, status code).

    Example:
        >>> except DatabaseError as e:
        ...     return error_response_from_exception(e)
    """
    response: dict[str, Any] = {
        "success": False,
        "error": exc.code or "UNKNOWN",
        "message": exc.message,
        "error_type": type(exc).__name__,
    }
    if exc.category:
        response["category"] = exc.category.value
    if exc.remediation:
        response["remediation"] = exc.remediation
    if exc.details:
        response["details"] = exc.details
    return jsonify(response), status_code


def success_response(
    data: dict[str, Any],
    status_code: int = 200,
) -> tuple[Response, int]:
    """Create a standardized success response.

    Args:
        data: Dictionary with response data (merged into response).
        status_code: HTTP status code (default: 200).

    Returns:
        Tuple of (Flask Response, status code).

    Example:
        >>> return success_response({"items": items, "total": len(items)})
    """
    return jsonify({"success": True, **data}), status_code


def validation_error_response(
    errors: list[str],
    message: str = "Validation failed",
    status_code: int = 400,
) -> tuple[Response, int]:
    """Create a standardized validation error response.

    Args:
        errors: List of validation error messages.
        message: Overall error message.
        status_code: HTTP status code (default: 400).

    Returns:
        Tuple of (Flask Response, status code).

    Example:
        >>> errors = ["Field 'name' is required", "Field 'query' is required"]
        >>> return validation_error_response(errors)
    """
    return jsonify({
        "success": False,
        "error": "VALIDATION_ERROR",
        "message": message,
        "errors": errors,
    }), status_code


def not_found_response(
    resource: str,
    resource_id: int | str | None = None,
) -> tuple[Response, int]:
    """Create a standardized 404 not found response.

    Args:
        resource: Type of resource (e.g., "Config", "User", "Schedule").
        resource_id: Optional ID of the resource.

    Returns:
        Tuple of (Flask Response, 404).

    Example:
        >>> return not_found_response("Config", config_id)
    """
    message = f"{resource} not found"
    if resource_id is not None:
        message = f"{resource} with ID {resource_id} not found"

    return jsonify({
        "success": False,
        "error": f"{resource.upper()}_404",
        "message": message,
    }), 404


def unauthorized_response(
    message: str = "Authentication required",
) -> tuple[Response, int]:
    """Create a standardized 401 unauthorized response.

    Args:
        message: Error message.

    Returns:
        Tuple of (Flask Response, 401).
    """
    return jsonify({
        "success": False,
        "error": "UNAUTHORIZED",
        "message": message,
    }), 401


def forbidden_response(
    message: str = "Permission denied",
    permission: str | None = None,
) -> tuple[Response, int]:
    """Create a standardized 403 forbidden response.

    Args:
        message: Error message.
        permission: Optional required permission name.

    Returns:
        Tuple of (Flask Response, 403).
    """
    response: dict[str, Any] = {
        "success": False,
        "error": "FORBIDDEN",
        "message": message,
    }
    if permission:
        response["required_permission"] = permission
    return jsonify(response), 403
