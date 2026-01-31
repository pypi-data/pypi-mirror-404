"""PII (Personally Identifiable Information) detection and transformation.

This package provides comprehensive PII handling capabilities:
- Detection: Pattern-based and content-based PII detection
- Transformation: Hash, redact, and partial masking transforms
- Configuration: Flexible configuration for detection and handling

Example usage:
    >>> from mysql_to_sheets.core.pii import (
    ...     detect_pii_in_columns,
    ...     apply_pii_transforms,
    ...     PIITransformConfig,
    ... )
    >>> config = PIITransformConfig(enabled=True)
    >>> result = detect_pii_in_columns(headers, rows, config)
    >>> if result.has_pii:
    ...     headers, rows = apply_pii_transforms(headers, rows, config, result)
"""

# Core types
from mysql_to_sheets.core.pii.types import (
    PIICategory,
    PIIColumn,
    PIIDetectionResult,
    PIITransform,
    PIITransformConfig,
)

# Detection functions
from mysql_to_sheets.core.pii.detection import (
    COLUMN_NAME_PATTERNS,
    CONTENT_PATTERNS,
    detect_pii_by_column_name,
    detect_pii_by_content,
    detect_pii_in_columns,
    merge_detection_results,
    validate_luhn,
)

# Transform functions
from mysql_to_sheets.core.pii.transform import (
    apply_pii_transforms,
    get_transform_preview,
    hash_value,
    partial_mask_value,
    redact_value,
    transform_value,
)

__all__ = [
    # Types
    "PIITransform",
    "PIICategory",
    "PIIColumn",
    "PIIDetectionResult",
    "PIITransformConfig",
    # Detection
    "COLUMN_NAME_PATTERNS",
    "CONTENT_PATTERNS",
    "detect_pii_by_column_name",
    "detect_pii_by_content",
    "detect_pii_in_columns",
    "merge_detection_results",
    "validate_luhn",
    # Transform
    "hash_value",
    "redact_value",
    "partial_mask_value",
    "transform_value",
    "apply_pii_transforms",
    "get_transform_preview",
]
