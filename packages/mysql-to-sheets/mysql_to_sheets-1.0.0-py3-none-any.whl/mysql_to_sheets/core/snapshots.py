"""Backward compatibility shim - import from core.history package instead.

This module re-exports all public APIs from the history package.
New code should import directly from mysql_to_sheets.core.history.

Example (preferred):
    >>> from mysql_to_sheets.core.history import create_snapshot, get_snapshot

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.snapshots import create_snapshot, get_snapshot

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.history.snapshots instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.snapshots",
    "mysql_to_sheets.core.history.snapshots",
)

from mysql_to_sheets.core.history.snapshots import (
    create_snapshot,
    delete_snapshot,
    estimate_sheet_size,
    get_snapshot,
    get_snapshot_data,
    get_snapshot_stats,
    list_snapshots,
)

__all__ = [
    "create_snapshot",
    "get_snapshot",
    "list_snapshots",
    "delete_snapshot",
    "get_snapshot_data",
    "get_snapshot_stats",
    "estimate_sheet_size",
]
