"""In-memory sync history storage for the web dashboard.

This module provides a simple in-memory history storage for sync
operations. In production, this should be replaced with database-backed
storage using the core.history module.
"""

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass
class SyncHistoryEntry:
    """A single entry in the sync history.

    Attributes:
        timestamp: ISO timestamp of the sync operation.
        success: Whether the sync succeeded.
        rows_synced: Number of rows synced.
        message: Status message.
        sheet_id: Google Sheet ID.
        worksheet: Target worksheet name.
        duration_ms: Duration in milliseconds.
        error_code: Error code if sync failed.
        error_category: Error category if sync failed.
    """

    timestamp: str
    success: bool
    rows_synced: int
    message: str
    sheet_id: str
    worksheet: str
    duration_ms: float = 0.0
    error_code: str | None = None
    error_category: str | None = None


class SyncHistory:
    """In-memory sync history storage.

    Stores the last N sync operations for display in the dashboard.
    In production, this should be backed by a database.
    """

    def __init__(self, max_entries: int = 50) -> None:
        """Initialize history storage.

        Args:
            max_entries: Maximum entries to keep (oldest are discarded).
        """
        self._entries: deque[SyncHistoryEntry] = deque(maxlen=max_entries)

    def add(self, entry: SyncHistoryEntry) -> None:
        """Add an entry to history.

        Args:
            entry: History entry to add.
        """
        self._entries.appendleft(entry)

    def get_all(self) -> list[dict[str, Any]]:
        """Get all history entries as dictionaries.

        Returns:
            List of history entries as dicts.
        """
        return [
            {
                "timestamp": e.timestamp,
                "success": e.success,
                "rows_synced": e.rows_synced,
                "message": e.message,
                "sheet_id": e.sheet_id,
                "worksheet": e.worksheet,
                "duration_ms": e.duration_ms,
                "error_code": e.error_code,
                "error_category": e.error_category,
            }
            for e in self._entries
        ]

    def get_error_stats(self, hours: int = 24) -> dict[str, Any]:
        """Get error statistics for the specified time period.

        Args:
            hours: Number of hours to look back.

        Returns:
            Dictionary with error counts by category and code.
        """
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        errors_by_category: dict[str, int] = {}
        errors_by_code: dict[str, int] = {}
        total_errors = 0

        for entry in self._entries:
            try:
                # Parse ISO timestamp
                ts = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                if ts.replace(tzinfo=None) < cutoff:
                    continue
            except (ValueError, AttributeError):
                continue

            if not entry.success:
                total_errors += 1
                if entry.error_category:
                    errors_by_category[entry.error_category] = (
                        errors_by_category.get(entry.error_category, 0) + 1
                    )
                if entry.error_code:
                    errors_by_code[entry.error_code] = errors_by_code.get(entry.error_code, 0) + 1

        return {
            "total_errors": total_errors,
            "errors_by_category": errors_by_category,
            "errors_by_code": errors_by_code,
            "hours": hours,
        }

    def clear(self) -> None:
        """Clear all history entries."""
        self._entries.clear()

    def count(self) -> int:
        """Get number of history entries.

        Returns:
            Number of entries in history.
        """
        return len(self._entries)


# Global history instance (replace with database in production)
sync_history = SyncHistory()
