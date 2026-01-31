"""Backward compatibility shim - import from core.history package instead.

This module re-exports all public APIs from the history package.
New code should import directly from mysql_to_sheets.core.history.

Example (preferred):
    >>> from mysql_to_sheets.core.history import HistoryEntry, get_history_repository

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.history import HistoryEntry

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.history.history instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.history",
    "mysql_to_sheets.core.history.history",
)

from mysql_to_sheets.core.history.history import (
    HistoryEntry,
    HistoryRepository,
    InMemoryHistoryRepository,
    SQLiteHistoryRepository,
    get_history_repository,
    reset_history_repository,
)

__all__ = [
    "HistoryEntry",
    "HistoryRepository",
    "InMemoryHistoryRepository",
    "SQLiteHistoryRepository",
    "get_history_repository",
    "reset_history_repository",
]
