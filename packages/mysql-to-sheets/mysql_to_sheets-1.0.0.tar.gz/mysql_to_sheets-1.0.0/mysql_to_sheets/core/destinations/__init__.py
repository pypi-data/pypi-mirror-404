"""Destination adapters for syncing data to various targets.

This package provides a unified interface for writing data to different
destinations (Google Sheets, Excel Online, etc.) through the
DestinationConnection protocol.

Example usage:
    >>> from mysql_to_sheets.core.destinations import (
    ...     DestinationConfig,
    ...     get_destination,
    ... )
    >>> config = DestinationConfig(
    ...     destination_type="google_sheets",
    ...     target_id="1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p",
    ...     target_name="Sheet1",
    ...     credentials_file="./service_account.json",
    ... )
    >>> with get_destination(config) as dest:
    ...     result = dest.write(["Name", "Age"], [["Alice", 30]])
    ...     print(f"Wrote {result.rows_written} rows")
"""

from .base import (
    BaseDestinationConnection,
    DestinationConfig,
    DestinationConnection,
    WriteResult,
)
from .factory import (
    UnsupportedDestinationError,
    get_destination,
    list_supported_destinations,
    register_destination,
)

__all__ = [
    # Base classes and protocols
    "BaseDestinationConnection",
    "DestinationConfig",
    "DestinationConnection",
    "WriteResult",
    # Factory and utilities
    "get_destination",
    "list_supported_destinations",
    "register_destination",
    "UnsupportedDestinationError",
]
