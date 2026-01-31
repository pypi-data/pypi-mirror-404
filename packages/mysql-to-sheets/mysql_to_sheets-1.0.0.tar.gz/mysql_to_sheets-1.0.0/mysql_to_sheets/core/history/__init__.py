"""History, snapshots, and rollback management.

This package consolidates history-related functionality:
- Sync history tracking (in-memory and SQLite backends)
- Sheet state snapshots (compressed storage)
- Rollback to previous states

Example:
    >>> from mysql_to_sheets.core.history import (
    ...     HistoryEntry, get_history_repository,
    ...     create_snapshot, rollback_to_snapshot,
    ... )
"""

# Re-export from history module
from mysql_to_sheets.core.history.history import (
    HistoryEntry,
    HistoryRepository,
    InMemoryHistoryRepository,
    SQLiteHistoryRepository,
    get_history_repository,
    reset_history_repository,
)

# Re-export from snapshots module
from mysql_to_sheets.core.history.snapshots import (
    create_snapshot,
    delete_snapshot,
    estimate_sheet_size,
    get_snapshot,
    get_snapshot_data,
    get_snapshot_stats,
    list_snapshots,
)

# Re-export from rollback module
from mysql_to_sheets.core.history.rollback import (
    RollbackPreview,
    RollbackResult,
    can_rollback,
    preview_rollback,
    rollback_to_snapshot,
)

__all__ = [
    # History
    "HistoryEntry",
    "HistoryRepository",
    "InMemoryHistoryRepository",
    "SQLiteHistoryRepository",
    "get_history_repository",
    "reset_history_repository",
    # Snapshots
    "create_snapshot",
    "get_snapshot",
    "list_snapshots",
    "delete_snapshot",
    "get_snapshot_data",
    "get_snapshot_stats",
    "estimate_sheet_size",
    # Rollback
    "RollbackResult",
    "RollbackPreview",
    "preview_rollback",
    "rollback_to_snapshot",
    "can_rollback",
]
