"""PII transformation functions for data protection.

This module provides functions to transform PII data:
- hash_value: SHA256 hash (consistent, one-way)
- redact_value: Replace with *** (category-aware)
- partial_mask_value: Keep last N characters visible
- apply_pii_transforms: Apply transforms to entire dataset
"""

import hashlib
import logging
import re
from typing import Any

from mysql_to_sheets.core.pii.types import (
    PIICategory,
    PIIColumn,
    PIIDetectionResult,
    PIITransform,
    PIITransformConfig,
)


def hash_value(value: Any, truncate_to: int = 16) -> str:
    """Hash a value using SHA256 and truncate.

    Args:
        value: Value to hash.
        truncate_to: Number of characters to keep (default: 16).

    Returns:
        Truncated SHA256 hash as hex string.
    """
    if value is None:
        return ""

    str_value = str(value)
    # Hash even empty strings - they still produce a consistent hash
    # Use UTF-8 encoding for consistent hashing
    hash_bytes = hashlib.sha256(str_value.encode("utf-8")).hexdigest()
    return hash_bytes[:truncate_to]


def redact_value(
    value: Any,
    category: PIICategory | None = None,
    placeholder: str = "***",
) -> str:
    """Redact a value, optionally with category-aware formatting.

    Category-aware redaction preserves some structure:
    - EMAIL: j***@domain.com
    - PHONE: ***-***-1234
    - CREDIT_CARD: ****-****-****-1234
    - SSN: ***-**-1234
    - Other: ***

    Args:
        value: Value to redact.
        category: Optional PII category for smart redaction.
        placeholder: Placeholder string for redaction.

    Returns:
        Redacted string.
    """
    if value is None:
        return ""

    str_value = str(value).strip()
    if not str_value:
        return ""

    if category is None:
        return placeholder

    # Category-aware redaction
    if category == PIICategory.EMAIL:
        return _redact_email(str_value, placeholder)
    elif category == PIICategory.PHONE:
        return _redact_phone(str_value)
    elif category == PIICategory.CREDIT_CARD:
        return _redact_credit_card(str_value)
    elif category == PIICategory.SSN:
        return _redact_ssn(str_value)
    elif category == PIICategory.IP_ADDRESS:
        return _redact_ip_address(str_value)
    else:
        return placeholder


def _redact_email(email: str, placeholder: str = "***") -> str:
    """Redact email while preserving domain.

    Args:
        email: Email address.
        placeholder: Placeholder for local part.

    Returns:
        Redacted email (e.g., j***@domain.com).
    """
    match = re.match(r"^([^@]+)@(.+)$", email)
    if not match:
        return placeholder

    local, domain = match.groups()
    if len(local) <= 1:
        return f"{placeholder}@{domain}"

    return f"{local[0]}{placeholder}@{domain}"


def _redact_phone(phone: str) -> str:
    """Redact phone number keeping last 4 digits.

    Args:
        phone: Phone number.

    Returns:
        Redacted phone (e.g., ***-***-1234).
    """
    # Extract digits
    digits = re.sub(r"[^\d]", "", phone)
    if len(digits) < 4:
        return "***"

    last_four = digits[-4:]
    return f"***-***-{last_four}"


def _redact_credit_card(card: str) -> str:
    """Redact credit card keeping last 4 digits.

    Args:
        card: Credit card number.

    Returns:
        Redacted card (e.g., ****-****-****-1234).
    """
    # Extract digits
    digits = re.sub(r"[^\d]", "", card)
    if len(digits) < 4:
        return "****-****-****-****"

    last_four = digits[-4:]
    return f"****-****-****-{last_four}"


def _redact_ssn(ssn: str) -> str:
    """Redact SSN keeping last 4 digits.

    Args:
        ssn: Social Security Number.

    Returns:
        Redacted SSN (e.g., ***-**-1234).
    """
    # Extract digits
    digits = re.sub(r"[^\d]", "", ssn)
    if len(digits) < 4:
        return "***-**-****"

    last_four = digits[-4:]
    return f"***-**-{last_four}"


def _redact_ip_address(ip: str) -> str:
    """Redact IP address keeping first octet.

    Args:
        ip: IP address.

    Returns:
        Redacted IP (e.g., 192.***.***.***)
    """
    parts = ip.split(".")
    if len(parts) != 4:
        return "***.***.***.***"

    return f"{parts[0]}.***.***"


def partial_mask_value(
    value: Any,
    visible_chars: int = 4,
    mask_char: str = "*",
    from_end: bool = True,
) -> str:
    """Mask a value keeping some characters visible.

    Args:
        value: Value to mask.
        visible_chars: Number of characters to keep visible.
        mask_char: Character to use for masking.
        from_end: If True, keep last N chars; if False, keep first N chars.

    Returns:
        Partially masked string.
    """
    if value is None:
        return ""

    str_value = str(value).strip()
    if not str_value:
        return ""

    if len(str_value) <= visible_chars:
        # Too short to mask meaningfully - return as-is
        return str_value

    if from_end:
        # Keep last N characters visible
        masked_len = len(str_value) - visible_chars
        return (mask_char * masked_len) + str_value[-visible_chars:]
    else:
        # Keep first N characters visible
        masked_len = len(str_value) - visible_chars
        return str_value[:visible_chars] + (mask_char * masked_len)


def transform_value(
    value: Any,
    transform: PIITransform,
    category: PIICategory | None = None,
) -> Any:
    """Apply a PII transform to a single value.

    Args:
        value: Value to transform.
        transform: Transform type to apply.
        category: Optional PII category for category-aware transforms.

    Returns:
        Transformed value.
    """
    if value is None:
        return ""

    if transform == PIITransform.NONE:
        return value
    elif transform == PIITransform.HASH:
        return hash_value(value)
    elif transform == PIITransform.REDACT:
        return redact_value(value, category)
    elif transform == PIITransform.PARTIAL_MASK:
        return partial_mask_value(value)
    else:
        return value


def apply_pii_transforms(
    headers: list[str],
    rows: list[list[Any]],
    config: PIITransformConfig,
    detection_result: PIIDetectionResult | None = None,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Apply PII transforms to entire dataset.

    Args:
        headers: Column headers.
        rows: Data rows.
        config: PII transform configuration.
        detection_result: Optional pre-computed detection result.
        logger: Optional logger.

    Returns:
        Tuple of (headers, transformed_rows).
    """
    if not config.is_active():
        return headers, rows

    # Build transform map for each column
    column_transforms: dict[int, tuple[PIITransform, PIICategory | None]] = {}

    for col_idx, header in enumerate(headers):
        # Check explicit transform first
        explicit_transform = config.get_transform_for_column(header)
        if explicit_transform is not None:
            column_transforms[col_idx] = (explicit_transform, None)
            if logger:
                logger.debug(f"Column '{header}' using explicit transform: {explicit_transform.value}")
            continue

        # Check if acknowledged (no transform)
        if config.is_acknowledged(header):
            continue

        # Check detection result
        if detection_result:
            pii_col = detection_result.get_column(header)
            if pii_col:
                # Use configured default or suggested transform
                transform = config.default_transform
                column_transforms[col_idx] = (transform, pii_col.category)
                if logger:
                    logger.debug(
                        f"Column '{header}' ({pii_col.category.value}) using transform: {transform.value}"
                    )

    if not column_transforms:
        if logger:
            logger.debug("No PII transforms to apply")
        return headers, rows

    # Apply transforms to each row
    transformed_rows = []
    for row in rows:
        new_row = list(row)
        for col_idx, (transform, category) in column_transforms.items():
            if col_idx < len(new_row):
                new_row[col_idx] = transform_value(new_row[col_idx], transform, category)
        transformed_rows.append(new_row)

    if logger:
        logger.info(f"Applied PII transforms to {len(column_transforms)} columns")

    return headers, transformed_rows


def get_transform_preview(
    headers: list[str],
    rows: list[list[Any]],
    config: PIITransformConfig,
    detection_result: PIIDetectionResult | None = None,
    max_preview_rows: int = 5,
) -> dict[str, Any]:
    """Generate a preview of PII transforms.

    Args:
        headers: Column headers.
        rows: Data rows.
        config: PII transform configuration.
        detection_result: Optional pre-computed detection result.
        max_preview_rows: Maximum rows to include in preview.

    Returns:
        Dictionary with preview information.
    """
    preview_rows = rows[:max_preview_rows] if rows else []
    _, transformed_preview = apply_pii_transforms(
        headers, preview_rows, config, detection_result
    )

    columns_info = []
    for col_idx, header in enumerate(headers):
        col_info: dict[str, Any] = {"column": header, "transform": "none"}

        explicit_transform = config.get_transform_for_column(header)
        if explicit_transform:
            col_info["transform"] = explicit_transform.value
            col_info["source"] = "explicit"
        elif detection_result:
            pii_col = detection_result.get_column(header)
            if pii_col:
                col_info["transform"] = config.default_transform.value
                col_info["source"] = "detected"
                col_info["category"] = pii_col.category.value
                col_info["confidence"] = pii_col.confidence

        # Add sample before/after
        if preview_rows and col_idx < len(preview_rows[0]):
            before = preview_rows[0][col_idx]
            after = transformed_preview[0][col_idx] if transformed_preview else before
            if before != after:
                col_info["sample_before"] = str(before)[:50]
                col_info["sample_after"] = str(after)[:50]

        if col_info["transform"] != "none":
            columns_info.append(col_info)

    return {
        "columns": columns_info,
        "total_rows": len(rows),
        "preview_rows": len(preview_rows),
        "transforms_applied": len(columns_info),
    }
