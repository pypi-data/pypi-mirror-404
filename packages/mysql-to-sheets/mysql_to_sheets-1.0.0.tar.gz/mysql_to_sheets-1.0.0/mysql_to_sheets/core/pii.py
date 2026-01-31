"""Backward compatibility shim - import from core.pii instead.

This module re-exports all public APIs from the pii package.
New code should import directly from mysql_to_sheets.core.pii.

Example (preferred):
    >>> from mysql_to_sheets.core.pii import PIITransform, PIICategory

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.pii import PIITransform, PIICategory

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.pii.types instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.pii",
    "mysql_to_sheets.core.pii.types",
)

from mysql_to_sheets.core.pii.types import (
    PIICategory,
    PIIColumn,
    PIIDetectionResult,
    PIITransform,
    PIITransformConfig,
)

__all__ = [
    "PIITransform",
    "PIICategory",
    "PIIColumn",
    "PIIDetectionResult",
    "PIITransformConfig",
]
