"""Backward compatibility shim - import from core.history package instead.

This module re-exports all public APIs from the history package.
New code should import directly from mysql_to_sheets.core.history.

Example (preferred):
    >>> from mysql_to_sheets.core.history import rollback_to_snapshot

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.rollback import rollback_to_snapshot

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.history.rollback instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.rollback",
    "mysql_to_sheets.core.history.rollback",
)

from mysql_to_sheets.core.history.rollback import (
    RollbackPreview,
    RollbackResult,
    can_rollback,
    preview_rollback,
    rollback_to_snapshot,
)

__all__ = [
    "RollbackResult",
    "RollbackPreview",
    "preview_rollback",
    "rollback_to_snapshot",
    "can_rollback",
]
