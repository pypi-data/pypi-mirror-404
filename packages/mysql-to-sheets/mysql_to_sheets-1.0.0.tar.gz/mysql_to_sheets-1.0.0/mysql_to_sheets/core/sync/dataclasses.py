"""Sync result dataclasses.

This module provides dataclasses for sync results. For backward compatibility,
SyncResult is re-exported from the legacy sync module.

New code should import from this module:
    from mysql_to_sheets.core.sync.dataclasses import SyncResult, StepResult

Legacy imports still work:
    from mysql_to_sheets.core.sync import SyncResult
"""

# Re-export StepResult from protocols
# Note: SyncResult is defined in sync_legacy.py (the original sync.py)
# We import it here and re-export so the package __init__ can provide it
# This avoids circular imports since sync_legacy is at the core level
#
# For type checking and direct definition (to avoid import during refactoring):
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from mysql_to_sheets.core.sync.protocols import StepResult

if TYPE_CHECKING:
    from mysql_to_sheets.core.diff import DiffResult


@dataclass
class SyncResult:
    """Result of a sync operation.

    Attributes:
        success: Whether the sync completed successfully.
        rows_synced: Number of data rows synced (excluding header).
        columns: Number of columns in the synced data.
        headers: List of column headers.
        message: Human-readable status message.
        error: Error details if sync failed.
        preview: Whether this was a preview-only run.
        diff: Diff result if preview mode was used.
        schema_changes: Schema change information if detected.
        warnings: List of warning messages (EC-53, EC-56).
        empty_result_skipped: Whether sync was skipped due to empty result (EC-53).
    """

    success: bool
    rows_synced: int = 0
    columns: int = 0
    headers: list[str] = field(default_factory=list)
    message: str = ""
    error: str | None = None
    preview: bool = False
    diff: "DiffResult | None" = None
    schema_changes: dict[str, Any] | None = None
    # EC-53: Make empty result and warnings visible in result
    warnings: list[str] = field(default_factory=list)
    empty_result_skipped: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary for API responses.

        Returns:
            Dictionary representation of the result.
        """
        result = {
            "success": self.success,
            "rows_synced": self.rows_synced,
            "columns": self.columns,
            "headers": self.headers,
            "message": self.message,
            "error": self.error,
            "preview": self.preview,
        }
        if self.diff is not None:
            result["diff"] = self.diff.to_dict()
        if self.schema_changes is not None:
            result["schema_changes"] = self.schema_changes
        # EC-53: Include warnings and empty_result_skipped in output
        if self.warnings:
            result["warnings"] = self.warnings
        if self.empty_result_skipped:
            result["empty_result_skipped"] = True
        return result

__all__ = [
    "SyncResult",
    "StepResult",
]
