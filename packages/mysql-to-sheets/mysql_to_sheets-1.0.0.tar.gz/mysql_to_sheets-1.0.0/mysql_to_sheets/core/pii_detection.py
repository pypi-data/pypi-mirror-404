"""Backward compatibility shim - import from core.pii instead.

This module re-exports all public APIs from the pii detection module.
New code should import directly from mysql_to_sheets.core.pii.

Example (preferred):
    >>> from mysql_to_sheets.core.pii import detect_pii_in_columns

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.pii_detection import detect_pii_in_columns

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.pii.detection instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.pii_detection",
    "mysql_to_sheets.core.pii.detection",
)

from mysql_to_sheets.core.pii.detection import (
    COLUMN_NAME_PATTERNS,
    CONTENT_PATTERNS,
    detect_pii_by_column_name,
    detect_pii_by_content,
    detect_pii_in_columns,
    merge_detection_results,
    validate_luhn,
)

__all__ = [
    "COLUMN_NAME_PATTERNS",
    "CONTENT_PATTERNS",
    "detect_pii_by_column_name",
    "detect_pii_by_content",
    "detect_pii_in_columns",
    "merge_detection_results",
    "validate_luhn",
]
