"""Incremental sync support for timestamp-based filtering.

This module provides utilities for building incremental sync queries
that only fetch data changed since a specific timestamp.
"""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

# Pattern for valid SQL column names: letters, digits, underscores, dots (for table.column)
_COLUMN_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_.]*$")


def _validate_column_name(name: str) -> None:
    """Validate a column name to prevent SQL injection.

    Args:
        name: Column name to validate.

    Raises:
        ValueError: If the column name contains unsafe characters.
    """
    if not name or not _COLUMN_NAME_RE.match(name):
        raise ValueError(
            f"Invalid column name: {name!r}. "
            "Column names must contain only letters, digits, underscores, and dots."
        )


@dataclass
class IncrementalConfig:
    """Configuration for incremental sync.

    Attributes:
        enabled: Whether incremental sync is enabled.
        timestamp_column: Column name to filter on (e.g., 'updated_at').
        since: Only fetch records modified after this timestamp.
        until: Only fetch records modified before this timestamp (optional).
    """

    enabled: bool = False
    timestamp_column: str = ""
    since: datetime | None = None
    until: datetime | None = None

    def is_active(self) -> bool:
        """Check if incremental sync should be applied.

        Returns:
            True if incremental sync is enabled and configured.
        """
        return self.enabled and bool(self.timestamp_column) and self.since is not None


def build_incremental_query(
    base_query: str,
    config: IncrementalConfig,
) -> str:
    """Modify a SQL query to add incremental filtering.

    Adds a WHERE clause (or AND condition) to filter by timestamp.

    Args:
        base_query: The original SQL query.
        config: Incremental sync configuration.

    Returns:
        Modified query with timestamp filter.

    Example:
        >>> config = IncrementalConfig(
        ...     enabled=True,
        ...     timestamp_column="updated_at",
        ...     since=datetime(2024, 1, 1)
        ... )
        >>> build_incremental_query("SELECT * FROM users", config)
        "SELECT * FROM users WHERE updated_at > '2024-01-01 00:00:00'"
    """
    if not config.is_active():
        return base_query

    # Format timestamps for SQL
    if config.since is None:
        return base_query

    # Validate column name to prevent SQL injection
    _validate_column_name(config.timestamp_column)

    since_str = config.since.strftime("%Y-%m-%d %H:%M:%S")

    # Build the filter condition
    conditions = [f"{config.timestamp_column} > '{since_str}'"]

    if config.until:
        until_str = config.until.strftime("%Y-%m-%d %H:%M:%S")
        conditions.append(f"{config.timestamp_column} <= '{until_str}'")

    filter_clause = " AND ".join(conditions)

    # Check if query already has WHERE clause
    query_upper = base_query.upper().strip()

    # Handle different query structures
    if has_where_clause(base_query):
        # Add to existing WHERE clause
        return add_to_where_clause(base_query, filter_clause)
    elif has_group_or_order(base_query):
        # Insert WHERE before GROUP BY/ORDER BY
        return insert_where_before_group_order(base_query, filter_clause)
    else:
        # Simple query - append WHERE clause
        return f"{base_query.rstrip(';')} WHERE {filter_clause}"


def has_where_clause(query: str) -> bool:
    """Check if a query has a WHERE clause.

    Args:
        query: The SQL query to check.

    Returns:
        True if query contains WHERE.
    """
    # Match WHERE that's not inside a subquery (simple heuristic)
    pattern = r"\bWHERE\b(?![^(]*\))"
    return bool(re.search(pattern, query, re.IGNORECASE))


def has_group_or_order(query: str) -> bool:
    """Check if a query has GROUP BY or ORDER BY.

    Args:
        query: The SQL query to check.

    Returns:
        True if query contains GROUP BY or ORDER BY.
    """
    pattern = r"\b(GROUP\s+BY|ORDER\s+BY)\b"
    return bool(re.search(pattern, query, re.IGNORECASE))


def add_to_where_clause(query: str, condition: str) -> str:
    """Add a condition to an existing WHERE clause.

    Args:
        query: The SQL query with existing WHERE.
        condition: The condition to add.

    Returns:
        Modified query with added condition.
    """
    # Find the WHERE clause position
    pattern = r"(\bWHERE\b)"
    match = re.search(pattern, query, re.IGNORECASE)

    if not match:
        return query

    # Insert after WHERE and wrap existing conditions
    where_pos = match.end()

    # Find what comes after WHERE (up to GROUP BY, ORDER BY, LIMIT, or end)
    remainder = query[where_pos:]
    end_pattern = r"\b(GROUP\s+BY|ORDER\s+BY|LIMIT|HAVING)\b"
    end_match = re.search(end_pattern, remainder, re.IGNORECASE)

    if end_match:
        existing_condition = remainder[: end_match.start()].strip()
        after_where = remainder[end_match.start() :]
    else:
        existing_condition = remainder.strip().rstrip(";")
        after_where = ""

    # Build new query
    new_query = f"{query[:where_pos]} ({existing_condition}) AND {condition}"
    if after_where:
        new_query += f" {after_where}"

    return new_query


def insert_where_before_group_order(query: str, condition: str) -> str:
    """Insert WHERE clause before GROUP BY or ORDER BY.

    Args:
        query: The SQL query without WHERE.
        condition: The WHERE condition to add.

    Returns:
        Modified query with WHERE clause.
    """
    pattern = r"\b(GROUP\s+BY|ORDER\s+BY)\b"
    match = re.search(pattern, query, re.IGNORECASE)

    if not match:
        return f"{query.rstrip(';')} WHERE {condition}"

    insert_pos = match.start()
    return f"{query[:insert_pos]}WHERE {condition} {query[insert_pos:]}"


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse a timestamp string in various formats.

    Supports:
    - ISO format: 2024-01-15T10:30:00
    - Date only: 2024-01-15
    - MySQL format: 2024-01-15 10:30:00
    - Relative: -1d, -7d, -1h, -30m

    Args:
        timestamp_str: The timestamp string to parse.

    Returns:
        Parsed datetime object.

    Raises:
        ValueError: If timestamp cannot be parsed.
    """

    timestamp_str = timestamp_str.strip()

    # Handle relative timestamps
    if timestamp_str.startswith("-"):
        return parse_relative_timestamp(timestamp_str)

    # Try various formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse timestamp: {timestamp_str}")


def parse_relative_timestamp(relative: str) -> datetime:
    """Parse a relative timestamp like -1d, -7d, -1h.

    Args:
        relative: Relative timestamp string.

    Returns:
        Datetime relative to now.

    Raises:
        ValueError: If format is invalid.
    """
    from datetime import timedelta

    pattern = r"^-(\d+)([dhms])$"
    match = re.match(pattern, relative.lower())

    if not match:
        raise ValueError(f"Invalid relative timestamp: {relative}")

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "d":
        delta = timedelta(days=amount)
    elif unit == "h":
        delta = timedelta(hours=amount)
    elif unit == "m":
        delta = timedelta(minutes=amount)
    elif unit == "s":
        delta = timedelta(seconds=amount)
    else:
        raise ValueError(f"Unknown time unit: {unit}")

    return datetime.now(timezone.utc) - delta


def get_last_sync_timestamp(
    sheet_id: str,
    history_repo: Any,
) -> datetime | None:
    """Get the timestamp of the last successful sync.

    Args:
        sheet_id: The Google Sheet ID.
        history_repo: History repository instance.

    Returns:
        Timestamp of last successful sync, or None if no history.
    """
    entries = history_repo.get_by_sheet_id(sheet_id, limit=1)

    for entry in entries:
        if entry.success and entry.timestamp:
            return entry.timestamp  # type: ignore[no-any-return]

    return None


def create_incremental_config(
    enabled: bool,
    timestamp_column: str,
    since: str | datetime | None = None,
    until: str | datetime | None = None,
    auto_from_history: bool = False,
    sheet_id: str | None = None,
    history_repo: Any = None,
) -> IncrementalConfig:
    """Create an incremental config with parsed timestamps.

    Args:
        enabled: Whether incremental sync is enabled.
        timestamp_column: Column name for timestamp filtering.
        since: Start timestamp (string or datetime).
        until: End timestamp (string or datetime).
        auto_from_history: If True, get since from last sync timestamp.
        sheet_id: Sheet ID for auto_from_history.
        history_repo: History repository for auto_from_history.

    Returns:
        Configured IncrementalConfig instance.
    """
    since_dt: datetime | None = None
    until_dt: datetime | None = None

    # Get since from history if requested
    if auto_from_history and sheet_id and history_repo:
        since_dt = get_last_sync_timestamp(sheet_id, history_repo)
    elif isinstance(since, str):
        since_dt = parse_timestamp(since)
    elif isinstance(since, datetime):
        since_dt = since

    # Parse until
    if isinstance(until, str):
        until_dt = parse_timestamp(until)
    elif isinstance(until, datetime):
        until_dt = until

    return IncrementalConfig(
        enabled=enabled,
        timestamp_column=timestamp_column,
        since=since_dt,
        until=until_dt,
    )
