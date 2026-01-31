"""Backward compatibility shim - import from core.pii instead.

This module re-exports all public APIs from the pii transform module.
New code should import directly from mysql_to_sheets.core.pii.

Example (preferred):
    >>> from mysql_to_sheets.core.pii import apply_pii_transforms, hash_value

Example (deprecated but supported):
    >>> from mysql_to_sheets.core.pii_transform import apply_pii_transforms

.. deprecated::
    This module is deprecated and will be removed in a future release.
    Import from mysql_to_sheets.core.pii.transform instead.
"""

from mysql_to_sheets.core._compat import emit_deprecation_warning

emit_deprecation_warning(
    "mysql_to_sheets.core.pii_transform",
    "mysql_to_sheets.core.pii.transform",
)

from mysql_to_sheets.core.pii.transform import (
    apply_pii_transforms,
    get_transform_preview,
    hash_value,
    partial_mask_value,
    redact_value,
    transform_value,
)

__all__ = [
    "hash_value",
    "redact_value",
    "partial_mask_value",
    "transform_value",
    "apply_pii_transforms",
    "get_transform_preview",
]
