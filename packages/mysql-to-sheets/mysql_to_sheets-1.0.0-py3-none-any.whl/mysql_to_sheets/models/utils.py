"""Shared utilities for model serialization and parsing.

This module provides common helper functions used across multiple
model files for consistent data parsing and serialization.
"""

from datetime import datetime, timezone
from typing import Any


def parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime value from various input types.

    Handles datetime objects, ISO format strings (including 'Z' suffix),
    and None values. Returns None for unparseable inputs.

    Args:
        value: The value to parse. Can be datetime, str, or None.

    Returns:
        Parsed datetime object or None.

    Examples:
        >>> parse_datetime("2024-01-15T10:30:00Z")
        datetime.datetime(2024, 1, 15, 10, 30, tzinfo=datetime.timezone.utc)
        >>> parse_datetime(datetime.now())
        datetime.datetime(...)
        >>> parse_datetime(None)
        None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        if not value:
            return None
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return None


def parse_int(value: Any, default: int = 0) -> int:
    """Parse an integer value with a default fallback.

    Args:
        value: The value to parse.
        default: Default value if parsing fails.

    Returns:
        Parsed integer or default value.
    """
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        if not value:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    return default


def format_datetime(value: datetime | None) -> str | None:
    """Format a datetime value for storage/serialization.

    Args:
        value: The datetime to format.

    Returns:
        ISO format string with 'Z' suffix for UTC, or None.
    """
    if value is None:
        return None
    # Use isoformat but replace +00:00 with Z for consistency
    iso_str = value.isoformat()
    if iso_str.endswith("+00:00"):
        iso_str = iso_str[:-6] + "Z"
    return iso_str


def now_utc() -> datetime:
    """Get current UTC datetime.

    Returns:
        Current datetime with UTC timezone.
    """
    return datetime.now(timezone.utc)
