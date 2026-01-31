"""Factory function for creating destination connections.

This module provides the entry point for creating destination adapters
based on configuration, following the same pattern as core/database/factory.py.
"""

from __future__ import annotations

from mysql_to_sheets.core.exceptions import SyncError

from .base import DestinationConfig, DestinationConnection


class UnsupportedDestinationError(SyncError):
    """Raised when an unsupported destination type is requested.

    Examples:
        - Requesting a destination type that doesn't exist
        - Missing required dependencies for a destination
    """

    default_code = "DEST_001"

    def __init__(
        self,
        message: str,
        destination_type: str | None = None,
        code: str | None = None,
    ) -> None:
        """Initialize UnsupportedDestinationError.

        Args:
            message: Human-readable error description.
            destination_type: The unsupported destination type that was requested.
            code: Error code for troubleshooting.
        """
        details = {}
        if destination_type:
            details["destination_type"] = destination_type
        super().__init__(message, details, code=code)
        self.destination_type = destination_type


# Registry of supported destination types and their adapter classes
_DESTINATION_REGISTRY: dict[str, type[DestinationConnection]] = {}


def register_destination(
    destination_type: str,
    adapter_class: type[DestinationConnection],
) -> None:
    """Register a destination adapter class.

    This allows plugins to register custom destination adapters.

    Args:
        destination_type: The destination type identifier (e.g., 'excel_online').
        adapter_class: The adapter class implementing DestinationConnection.
    """
    _DESTINATION_REGISTRY[destination_type.lower()] = adapter_class


def get_destination(config: DestinationConfig) -> DestinationConnection:
    """Create a destination connection based on configuration.

    This is the main factory function for creating destination adapters.
    It uses lazy imports to avoid loading dependencies for unused destinations.

    Args:
        config: Destination configuration with type and credentials.

    Returns:
        A DestinationConnection instance for the specified destination type.

    Raises:
        UnsupportedDestinationError: If the destination type is not supported.

    Example:
        >>> config = DestinationConfig(
        ...     destination_type="google_sheets",
        ...     target_id="1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p",
        ...     target_name="Sheet1",
        ... )
        >>> dest = get_destination(config)
        >>> with dest:
        ...     result = dest.write(headers, rows)
    """
    dest_type = config.destination_type.lower()

    # Check registry first (for plugins)
    if dest_type in _DESTINATION_REGISTRY:
        return _DESTINATION_REGISTRY[dest_type](config)

    # Built-in destinations with lazy imports
    match dest_type:
        case "google_sheets" | "sheets" | "gsheets":
            from .google_sheets import GoogleSheetsDestination

            return GoogleSheetsDestination(config)

        # Future destinations can be added here:
        # case "excel_online" | "excel":
        #     from .excel_online import ExcelOnlineDestination
        #     return ExcelOnlineDestination(config)
        #
        # case "airtable":
        #     from .airtable import AirtableDestination
        #     return AirtableDestination(config)

        case _:
            supported = ["google_sheets"] + list(_DESTINATION_REGISTRY.keys())
            raise UnsupportedDestinationError(
                message=(
                    f"Unsupported destination type: '{config.destination_type}'. "
                    f"Supported types: {', '.join(supported)}"
                ),
                destination_type=config.destination_type,
            )


def list_supported_destinations() -> list[str]:
    """List all supported destination types.

    Returns:
        List of destination type identifiers.
    """
    builtin = ["google_sheets"]
    registered = list(_DESTINATION_REGISTRY.keys())
    return sorted(set(builtin + registered))
