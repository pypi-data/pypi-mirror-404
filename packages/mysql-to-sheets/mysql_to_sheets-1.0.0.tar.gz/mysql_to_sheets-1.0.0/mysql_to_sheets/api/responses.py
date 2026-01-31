"""Standardized API response utilities.

This module provides consistent response envelope patterns for the REST API.
All endpoints should use these utilities to ensure consistent response formats.

Response Envelope Pattern:
    Success: {"success": true, "data": ..., "message": "..."}
    Error: {"success": false, "error": {...}, "message": "..."}
    Paginated: {"success": true, "data": [...], "pagination": {...}}
"""

from datetime import datetime, timezone
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# =============================================================================
# Response Models
# =============================================================================


class ErrorDetail(BaseModel):
    """Error detail model for structured error responses."""

    code: str = Field(..., description="Error code (e.g., 'DB_201')")
    message: str = Field(..., description="Human-readable error message")
    category: str | None = Field(
        default=None,
        description="Error category: transient, permanent, config, permission, quota",
    )
    remediation: str | None = Field(
        default=None,
        description="Suggested action to fix the error",
    )
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error context",
    )


class PaginationInfo(BaseModel):
    """Pagination metadata for list responses."""

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether more items exist")


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(..., description="Whether the operation succeeded")
    message: str | None = Field(default=None, description="Human-readable status message")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 timestamp of the response",
    )


class SuccessResponse(BaseResponse):
    """Standard success response."""

    success: bool = True
    data: Any | None = Field(default=None, description="Response payload")


class ErrorResponse(BaseResponse):
    """Standard error response."""

    success: bool = False
    error: ErrorDetail = Field(..., description="Error details")


class PaginatedResponse(BaseResponse):
    """Paginated list response."""

    success: bool = True
    data: list[Any] = Field(default_factory=list, description="List of items")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


# =============================================================================
# Response Builder Functions
# =============================================================================


def success_response(
    data: Any = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Build a standardized success response.

    Args:
        data: The response payload (any JSON-serializable data).
        message: Optional human-readable message.

    Returns:
        Response dictionary.

    Example:
        >>> success_response({"user": {"id": 1}}, "User created")
        {
            "success": true,
            "data": {"user": {"id": 1}},
            "message": "User created",
            "timestamp": "2024-01-15T10:30:00+00:00"
        }
    """
    response = {
        "success": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if data is not None:
        response["data"] = data

    if message:
        response["message"] = message

    return response


def error_response(
    code: str,
    message: str,
    category: str | None = None,
    remediation: str | None = None,
    details: dict[str, Any] | None = None,
    status_code: int = 400,
) -> tuple[dict[str, Any], int]:
    """Build a standardized error response.

    Args:
        code: Error code (e.g., 'DB_201', 'SHEETS_303').
        message: Human-readable error message.
        category: Error category (transient, permanent, config, permission, quota).
        remediation: Suggested fix for the error.
        details: Additional error context.
        status_code: HTTP status code for the response.

    Returns:
        Tuple of (response dict, status code).

    Example:
        >>> error_response("DB_201", "Connection refused", category="transient")
        ({
            "success": false,
            "error": {
                "code": "DB_201",
                "message": "Connection refused",
                "category": "transient"
            },
            "timestamp": "..."
        }, 400)
    """
    error_detail: dict[str, Any] = {
        "code": code,
        "message": message,
    }

    if category:
        error_detail["category"] = category

    if remediation:
        error_detail["remediation"] = remediation

    if details:
        error_detail["details"] = details

    response = {
        "success": False,
        "error": error_detail,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    return response, status_code


def paginated_response(
    items: list[Any],
    total: int,
    limit: int,
    offset: int,
    message: str | None = None,
) -> dict[str, Any]:
    """Build a standardized paginated response.

    Args:
        items: List of items for this page.
        total: Total number of items across all pages.
        limit: Maximum items per page.
        offset: Number of items skipped.
        message: Optional status message.

    Returns:
        Response dictionary.

    Example:
        >>> paginated_response([{"id": 1}], total=100, limit=10, offset=0)
        {
            "success": true,
            "data": [{"id": 1}],
            "pagination": {
                "total": 100,
                "limit": 10,
                "offset": 0,
                "has_more": true
            },
            "timestamp": "..."
        }
    """
    response = {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if message:
        response["message"] = message

    return response


def validation_error_response(errors: list[dict[str, Any]]) -> tuple[dict[str, Any], int]:
    """Build a validation error response.

    Args:
        errors: List of validation errors with field and message.

    Returns:
        Tuple of (response dict, 422 status code).

    Example:
        >>> validation_error_response([{"field": "email", "message": "Invalid format"}])
        ({
            "success": false,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": [...]}
            }
        }, 422)
    """
    return error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        category="permanent",
        details={"errors": errors},
        status_code=422,
    )


def not_found_response(resource: str, resource_id: Any = None) -> tuple[dict[str, Any], int]:
    """Build a not found error response.

    Args:
        resource: Name of the resource (e.g., 'User', 'Config').
        resource_id: Optional ID of the missing resource.

    Returns:
        Tuple of (response dict, 404 status code).
    """
    message = f"{resource} not found"
    if resource_id is not None:
        message = f"{resource} with ID '{resource_id}' not found"

    return error_response(
        code="NOT_FOUND",
        message=message,
        category="permanent",
        status_code=404,
    )


def unauthorized_response(message: str = "Authentication required") -> tuple[dict[str, Any], int]:
    """Build an unauthorized error response.

    Args:
        message: Error message.

    Returns:
        Tuple of (response dict, 401 status code).
    """
    return error_response(
        code="UNAUTHORIZED",
        message=message,
        category="permission",
        remediation="Provide a valid API key or authentication token",
        status_code=401,
    )


def forbidden_response(message: str = "Permission denied") -> tuple[dict[str, Any], int]:
    """Build a forbidden error response.

    Args:
        message: Error message.

    Returns:
        Tuple of (response dict, 403 status code).
    """
    return error_response(
        code="FORBIDDEN",
        message=message,
        category="permission",
        remediation="Contact your administrator for access",
        status_code=403,
    )


def from_sync_error(exc: Exception) -> tuple[dict[str, Any], int]:
    """Build an error response from a SyncError exception.

    Args:
        exc: A SyncError exception (or subclass).

    Returns:
        Tuple of (response dict, HTTP status code).
    """
    # Import here to avoid circular imports
    from mysql_to_sheets.core.exceptions import ConfigError, DatabaseError, SheetsError, SyncError

    if isinstance(exc, SyncError):
        # Determine HTTP status code based on error type
        if isinstance(exc, ConfigError):
            status_code = 400
        elif isinstance(exc, (DatabaseError, SheetsError)):
            status_code = 500
        else:
            status_code = 500

        return error_response(
            code=exc.code or "UNKNOWN_ERROR",
            message=exc.message,
            category=exc.category.value if exc.category else None,
            remediation=exc.remediation,
            details=exc.to_dict().get("details"),
            status_code=status_code,
        )

    # Generic exception handling
    return error_response(
        code="INTERNAL_ERROR",
        message=str(exc),
        category="transient",
        status_code=500,
    )
