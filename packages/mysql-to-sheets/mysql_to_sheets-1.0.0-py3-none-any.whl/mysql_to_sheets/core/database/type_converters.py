"""Type conversion utilities for database values.

This module provides a registry-based type conversion system that handles
the conversion of database-specific types to Google Sheets compatible values.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Callable
from uuid import UUID

# Type converter registry: {(db_type, python_type): converter_function}
_converters: dict[tuple[str, type], Callable[[Any], Any]] = {}

# Default converters (applied to all database types)
_default_converters: dict[type, Callable[[Any], Any]] = {}


def register_converter(
    db_type: str | None,
    python_type: type,
    converter: Callable[[Any], Any],
) -> None:
    """Register a type converter.

    Args:
        db_type: Database type ('mysql', 'postgres') or None for default.
        python_type: The Python type to convert.
        converter: Function that converts the value to Sheets-compatible type.

    Example:
        >>> register_converter("postgres", UUID, lambda v: str(v))
        >>> register_converter(None, Decimal, lambda v: float(v))
    """
    if db_type is None:
        _default_converters[python_type] = converter
    else:
        _converters[(db_type, python_type)] = converter


def get_converter(
    db_type: str,
    python_type: type,
) -> Callable[[Any], Any] | None:
    """Get the converter for a specific type.

    Args:
        db_type: Database type ('mysql', 'postgres').
        python_type: The Python type to find a converter for.

    Returns:
        Converter function or None if not found.
    """
    # Try database-specific converter first
    converter = _converters.get((db_type, python_type))
    if converter:
        return converter

    # Fall back to default converter
    return _default_converters.get(python_type)


def clean_value(value: Any, db_type: str = "mysql") -> Any:
    """Convert a database value to a Google Sheets compatible type.

    This function handles type conversions for values fetched from databases
    to ensure they can be properly serialized to Google Sheets.

    Args:
        value: Raw value from database.
        db_type: Database type for type-specific conversions.

    Returns:
        Cleaned value suitable for Google Sheets.

    Example:
        >>> clean_value(Decimal("123.45"))
        123.45
        >>> clean_value(datetime(2024, 1, 15, 10, 30, 0))
        '2024-01-15 10:30:00'
        >>> clean_value(None)
        ''
    """
    if value is None:
        return ""

    value_type = type(value)

    # Check for registered converter
    converter = get_converter(db_type, value_type)
    if converter:
        return converter(value)

    # Handle common types with inline conversion
    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, (dict, list)):
        return str(value)

    if isinstance(value, UUID):
        return str(value)

    # Handle PostgreSQL-specific tuple type (arrays)
    if isinstance(value, tuple):
        # Convert tuple elements and join with comma separator
        # Output: "value1, value2" instead of "['value1', 'value2']"
        converted = [clean_value(v, db_type) for v in value]
        return ", ".join(str(item) for item in converted)

    return value


def clean_row(row: list[Any], db_type: str = "mysql") -> list[Any]:
    """Convert all values in a row to Google Sheets compatible types.

    Args:
        row: List of values from a database row.
        db_type: Database type for type-specific conversions.

    Returns:
        List of cleaned values.
    """
    return [clean_value(v, db_type) for v in row]


def clean_rows(rows: list[list[Any]], db_type: str = "mysql") -> list[list[Any]]:
    """Convert all values in multiple rows to Google Sheets compatible types.

    Args:
        rows: List of rows, each row is a list of values.
        db_type: Database type for type-specific conversions.

    Returns:
        List of cleaned rows.
    """
    return [clean_row(row, db_type) for row in rows]


# Register default converters (applied to all database types)
register_converter(None, type(None), lambda v: "")
register_converter(None, Decimal, lambda v: float(v))
register_converter(None, datetime, lambda v: v.strftime("%Y-%m-%d %H:%M:%S"))
register_converter(None, date, lambda v: v.strftime("%Y-%m-%d"))
register_converter(None, bytes, lambda v: v.decode("utf-8", errors="replace"))
register_converter(None, UUID, lambda v: str(v))


# Register PostgreSQL-specific converters
def _convert_postgres_array(value: tuple[Any, ...] | list[Any]) -> str:
    """Convert PostgreSQL array to comma-separated string.

    Produces "value1, value2" instead of "['value1', 'value2']" for
    better readability in Google Sheets.
    """
    # psycopg2 returns arrays as Python lists or tuples
    items = [clean_value(v, "postgres") for v in value]
    return ", ".join(str(item) for item in items)


register_converter("postgres", tuple, _convert_postgres_array)
register_converter("postgres", list, _convert_postgres_array)


def _convert_postgres_json(value: dict[str, Any] | list[Any]) -> str:
    """Convert PostgreSQL JSON/JSONB to string."""
    import json

    return json.dumps(value)


# JSON/JSONB types come as Python dicts
register_converter("postgres", dict, _convert_postgres_json)


# Register IP address converters (stdlib types)
try:
    from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network

    def _convert_ipv4_address(value: IPv4Address) -> str:
        """Convert IPv4Address to string."""
        return str(value)

    def _convert_ipv6_address(value: IPv6Address) -> str:
        """Convert IPv6Address to string."""
        return str(value)

    def _convert_ipv4_network(value: IPv4Network) -> str:
        """Convert IPv4Network (CIDR) to string."""
        return str(value)

    def _convert_ipv6_network(value: IPv6Network) -> str:
        """Convert IPv6Network (CIDR) to string."""
        return str(value)

    register_converter("postgres", IPv4Address, _convert_ipv4_address)
    register_converter("postgres", IPv6Address, _convert_ipv6_address)
    register_converter("postgres", IPv4Network, _convert_ipv4_network)
    register_converter("postgres", IPv6Network, _convert_ipv6_network)

except ImportError:
    pass  # ipaddress should always be available in Python 3.10+


# Register psycopg2-specific converters (optional dependency)
try:
    from psycopg2.extras import Range

    def _convert_postgres_range(value: Range) -> str:
        """Convert PostgreSQL range type to string representation.

        Formats ranges as "[lower,upper)" with proper bound notation:
        - ( or [ for lower bound
        - ) or ] for upper bound
        - empty for empty ranges
        """
        if value.isempty:
            return "empty"

        lower_bracket = "[" if value.lower_inc else "("
        upper_bracket = "]" if value.upper_inc else ")"
        lower_val = str(value.lower) if value.lower is not None else ""
        upper_val = str(value.upper) if value.upper is not None else ""

        return f"{lower_bracket}{lower_val},{upper_val}{upper_bracket}"

    register_converter("postgres", Range, _convert_postgres_range)

except ImportError:
    pass  # psycopg2 not installed


# Register psycopg2 geometric type converters (optional dependency)
try:
    from psycopg2.extensions import (
        AsIs,
        QuotedString,
    )

    # Point type
    try:
        from psycopg2.extras import Point

        def _convert_postgres_point(value: Point) -> str:
            """Convert PostgreSQL POINT to string."""
            return f"({value.x},{value.y})"

        register_converter("postgres", Point, _convert_postgres_point)
    except ImportError:
        pass  # Point not available in this psycopg2 version

except ImportError:
    pass  # psycopg2 not installed


# Fallback handlers for geometric types returned as strings or tuples
def _is_geometric_string(value: str) -> bool:
    """Check if a string looks like a PostgreSQL geometric type."""
    return (
        isinstance(value, str)
        and len(value) > 2
        and (value.startswith("(") or value.startswith("[") or value.startswith("<"))
    )


# Register memoryview converter (used by some PostgreSQL bytea operations)
def _convert_memoryview(value: memoryview) -> str:
    """Convert memoryview to string."""
    return value.tobytes().decode("utf-8", errors="replace")


register_converter("postgres", memoryview, _convert_memoryview)
register_converter(None, memoryview, _convert_memoryview)


# Register timedelta converter for INTERVAL types
try:
    from datetime import timedelta

    def _convert_timedelta(value: timedelta) -> str:
        """Convert timedelta (PostgreSQL INTERVAL) to string.

        Formats as 'X days, HH:MM:SS.ffffff' or shorter variants.
        """
        total_seconds = int(value.total_seconds())
        days = value.days
        hours, remainder = divmod(abs(total_seconds) - abs(days * 86400), 3600)
        minutes, seconds = divmod(remainder, 60)
        microseconds = value.microseconds

        parts = []
        if days:
            parts.append(f"{days} day{'s' if abs(days) != 1 else ''}")
        if hours or minutes or seconds or microseconds:
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            if microseconds:
                time_str += f".{microseconds:06d}"
            parts.append(time_str)

        return ", ".join(parts) if parts else "0:00:00"

    register_converter("postgres", timedelta, _convert_timedelta)
    register_converter(None, timedelta, _convert_timedelta)

except ImportError:
    pass  # timedelta should always be available
