"""PII detection logic using pattern and content analysis.

This module provides PII detection capabilities:
- Pattern-based detection: Match column names against known PII patterns
- Content-based detection: Sample rows and match against PII regex patterns
- Combined detection: Merge pattern and content detection results
"""

import logging
import re
import time
from typing import Any

from mysql_to_sheets.core.pii.types import (
    PIICategory,
    PIIColumn,
    PIIDetectionResult,
    PIITransform,
    PIITransformConfig,
)

# Column name patterns for PII detection
# Format: (compiled_regex, PIICategory, suggested_transform)
COLUMN_NAME_PATTERNS: list[tuple[re.Pattern[str], PIICategory, PIITransform]] = [
    # Email patterns
    (re.compile(r"(?i)e[-_]?mail", re.IGNORECASE), PIICategory.EMAIL, PIITransform.HASH),
    (re.compile(r"(?i)email[-_]?addr", re.IGNORECASE), PIICategory.EMAIL, PIITransform.HASH),
    (re.compile(r"(?i)user[-_]?email", re.IGNORECASE), PIICategory.EMAIL, PIITransform.HASH),
    (re.compile(r"(?i)contact[-_]?email", re.IGNORECASE), PIICategory.EMAIL, PIITransform.HASH),
    # Phone patterns
    (re.compile(r"(?i)phone", re.IGNORECASE), PIICategory.PHONE, PIITransform.PARTIAL_MASK),
    (re.compile(r"(?i)mobile", re.IGNORECASE), PIICategory.PHONE, PIITransform.PARTIAL_MASK),
    (re.compile(r"(?i)cell[-_]?(phone)?", re.IGNORECASE), PIICategory.PHONE, PIITransform.PARTIAL_MASK),
    (re.compile(r"(?i)tel(ephone)?", re.IGNORECASE), PIICategory.PHONE, PIITransform.PARTIAL_MASK),
    (re.compile(r"(?i)fax", re.IGNORECASE), PIICategory.PHONE, PIITransform.PARTIAL_MASK),
    # SSN patterns
    (re.compile(r"(?i)ssn", re.IGNORECASE), PIICategory.SSN, PIITransform.REDACT),
    (re.compile(r"(?i)social[-_]?sec", re.IGNORECASE), PIICategory.SSN, PIITransform.REDACT),
    (re.compile(r"(?i)tax[-_]?id", re.IGNORECASE), PIICategory.SSN, PIITransform.REDACT),
    (re.compile(r"(?i)tin$", re.IGNORECASE), PIICategory.SSN, PIITransform.REDACT),
    # Credit card patterns
    (re.compile(r"(?i)credit[-_]?card", re.IGNORECASE), PIICategory.CREDIT_CARD, PIITransform.REDACT),
    (re.compile(r"(?i)card[-_]?num", re.IGNORECASE), PIICategory.CREDIT_CARD, PIITransform.REDACT),
    (re.compile(r"(?i)cc[-_]?num", re.IGNORECASE), PIICategory.CREDIT_CARD, PIITransform.REDACT),
    (re.compile(r"(?i)pan$", re.IGNORECASE), PIICategory.CREDIT_CARD, PIITransform.REDACT),
    # Name patterns
    (re.compile(r"(?i)^name$", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)first[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)last[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)full[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)customer[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)user[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)given[-_]?name", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    (re.compile(r"(?i)surname", re.IGNORECASE), PIICategory.NAME, PIITransform.HASH),
    # IP address patterns (must be before ADDRESS to match "ip_address" correctly)
    (re.compile(r"(?i)ip[-_]?addr", re.IGNORECASE), PIICategory.IP_ADDRESS, PIITransform.HASH),
    (re.compile(r"(?i)client[-_]?ip", re.IGNORECASE), PIICategory.IP_ADDRESS, PIITransform.HASH),
    (re.compile(r"(?i)user[-_]?ip", re.IGNORECASE), PIICategory.IP_ADDRESS, PIITransform.HASH),
    (re.compile(r"(?i)remote[-_]?addr", re.IGNORECASE), PIICategory.IP_ADDRESS, PIITransform.HASH),
    # Address patterns
    (re.compile(r"(?i)address", re.IGNORECASE), PIICategory.ADDRESS, PIITransform.REDACT),
    (re.compile(r"(?i)street", re.IGNORECASE), PIICategory.ADDRESS, PIITransform.REDACT),
    (re.compile(r"(?i)city$", re.IGNORECASE), PIICategory.ADDRESS, PIITransform.REDACT),
    (re.compile(r"(?i)zip[-_]?code", re.IGNORECASE), PIICategory.ADDRESS, PIITransform.REDACT),
    (re.compile(r"(?i)postal[-_]?code", re.IGNORECASE), PIICategory.ADDRESS, PIITransform.REDACT),
    # Date of birth patterns
    (re.compile(r"(?i)dob$", re.IGNORECASE), PIICategory.DATE_OF_BIRTH, PIITransform.REDACT),
    (re.compile(r"(?i)birth[-_]?date", re.IGNORECASE), PIICategory.DATE_OF_BIRTH, PIITransform.REDACT),
    (re.compile(r"(?i)date[-_]?of[-_]?birth", re.IGNORECASE), PIICategory.DATE_OF_BIRTH, PIITransform.REDACT),
    (re.compile(r"(?i)birthday", re.IGNORECASE), PIICategory.DATE_OF_BIRTH, PIITransform.REDACT),
    # Passport patterns
    (re.compile(r"(?i)passport", re.IGNORECASE), PIICategory.PASSPORT, PIITransform.REDACT),
    # Driver's license patterns
    (re.compile(r"(?i)driver[-_]?li[cs]", re.IGNORECASE), PIICategory.DRIVER_LICENSE, PIITransform.REDACT),
    (re.compile(r"(?i)dl[-_]?num", re.IGNORECASE), PIICategory.DRIVER_LICENSE, PIITransform.REDACT),
    # National ID patterns
    (re.compile(r"(?i)national[-_]?id", re.IGNORECASE), PIICategory.NATIONAL_ID, PIITransform.REDACT),
    (re.compile(r"(?i)citizen[-_]?id", re.IGNORECASE), PIICategory.NATIONAL_ID, PIITransform.REDACT),
    # Bank account patterns
    (re.compile(r"(?i)bank[-_]?acc", re.IGNORECASE), PIICategory.BANK_ACCOUNT, PIITransform.REDACT),
    (re.compile(r"(?i)account[-_]?num", re.IGNORECASE), PIICategory.BANK_ACCOUNT, PIITransform.PARTIAL_MASK),
    (re.compile(r"(?i)iban", re.IGNORECASE), PIICategory.BANK_ACCOUNT, PIITransform.REDACT),
    (re.compile(r"(?i)routing[-_]?num", re.IGNORECASE), PIICategory.BANK_ACCOUNT, PIITransform.REDACT),
]


# Content patterns for PII detection (compiled regex)
CONTENT_PATTERNS: dict[PIICategory, re.Pattern[str]] = {
    # Email: standard email format
    PIICategory.EMAIL: re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    ),
    # Phone: various formats (US-centric with international support)
    PIICategory.PHONE: re.compile(
        r"(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}"
    ),
    # SSN: XXX-XX-XXXX format
    PIICategory.SSN: re.compile(r"\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b"),
    # Credit card: 13-19 digits with optional separators
    PIICategory.CREDIT_CARD: re.compile(
        r"\b(?:\d{4}[-\s]?){3,4}\d{1,4}\b"
    ),
    # IP address: IPv4 format
    PIICategory.IP_ADDRESS: re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    ),
    # Date of birth: various date formats (MM/DD/YYYY, YYYY-MM-DD, etc.)
    PIICategory.DATE_OF_BIRTH: re.compile(
        r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b"
    ),
}


def detect_pii_by_column_name(
    column_name: str,
    categories_to_detect: list[PIICategory] | None = None,
) -> PIIColumn | None:
    """Detect PII by matching column name against known patterns.

    Args:
        column_name: Column name to check.
        categories_to_detect: Optional list of categories to detect.

    Returns:
        PIIColumn if PII detected, None otherwise.
    """
    for pattern, category, suggested_transform in COLUMN_NAME_PATTERNS:
        # Skip if category not in detection list
        if categories_to_detect and category not in categories_to_detect:
            continue

        if pattern.search(column_name):
            return PIIColumn(
                column_name=column_name,
                category=category,
                confidence=0.9,  # High confidence for name pattern match
                suggested_transform=suggested_transform,
                detection_method="pattern",
            )

    return None


def detect_pii_by_content(
    column_name: str,
    values: list[Any],
    categories_to_detect: list[PIICategory] | None = None,
    confidence_threshold: float = 0.7,
) -> PIIColumn | None:
    """Detect PII by sampling content and matching against patterns.

    Args:
        column_name: Column name being checked.
        values: Sample of column values to analyze.
        categories_to_detect: Optional list of categories to detect.
        confidence_threshold: Minimum confidence threshold.

    Returns:
        PIIColumn if PII detected, None otherwise.
    """
    if not values:
        return None

    # Count matches for each category
    category_matches: dict[PIICategory, int] = {}
    total_non_empty = 0

    for value in values:
        if value is None:
            continue

        str_value = str(value).strip()
        if not str_value:
            continue

        total_non_empty += 1

        for category, pattern in CONTENT_PATTERNS.items():
            # Skip if category not in detection list
            if categories_to_detect and category not in categories_to_detect:
                continue

            if pattern.search(str_value):
                category_matches[category] = category_matches.get(category, 0) + 1

    if total_non_empty == 0:
        return None

    # Find the category with highest match rate
    best_category: PIICategory | None = None
    best_confidence = 0.0
    best_matches = 0

    for category, matches in category_matches.items():
        confidence = matches / total_non_empty
        if confidence > best_confidence and confidence >= confidence_threshold:
            best_confidence = confidence
            best_category = category
            best_matches = matches

    if best_category is None:
        return None

    # Determine suggested transform based on category
    suggested_transform = _get_suggested_transform(best_category)

    return PIIColumn(
        column_name=column_name,
        category=best_category,
        confidence=best_confidence,
        suggested_transform=suggested_transform,
        detection_method="content",
        sample_matches=best_matches,
    )


def _get_suggested_transform(category: PIICategory) -> PIITransform:
    """Get suggested transform for a PII category.

    Args:
        category: PII category.

    Returns:
        Suggested PIITransform.
    """
    # High-risk categories should be redacted
    if category in (
        PIICategory.SSN,
        PIICategory.CREDIT_CARD,
        PIICategory.DATE_OF_BIRTH,
        PIICategory.PASSPORT,
        PIICategory.DRIVER_LICENSE,
        PIICategory.NATIONAL_ID,
        PIICategory.BANK_ACCOUNT,
        PIICategory.ADDRESS,
    ):
        return PIITransform.REDACT

    # Phone numbers benefit from partial masking (last 4 visible)
    if category == PIICategory.PHONE:
        return PIITransform.PARTIAL_MASK

    # Email, names, IPs - hash for consistent linking
    return PIITransform.HASH


def detect_pii_in_columns(
    headers: list[str],
    rows: list[list[Any]],
    config: PIITransformConfig | None = None,
    logger: logging.Logger | None = None,
) -> PIIDetectionResult:
    """Detect PII in columns using pattern and content analysis.

    Args:
        headers: Column headers.
        rows: Data rows.
        config: Optional PII configuration.
        logger: Optional logger.

    Returns:
        PIIDetectionResult with detection results.
    """
    start_time = time.time()

    if config is None:
        config = PIITransformConfig(enabled=True, auto_detect=True)

    detected_columns: list[PIIColumn] = []
    sample_size = min(config.sample_size, len(rows))

    if logger:
        logger.debug(f"Running PII detection on {len(headers)} columns (sample: {sample_size} rows)")

    for col_idx, header in enumerate(headers):
        # Skip if column has explicit transform (already handled)
        if config.get_transform_for_column(header) is not None:
            continue

        # Skip if column is acknowledged
        if config.is_acknowledged(header):
            continue

        pii_col: PIIColumn | None = None

        # Try pattern-based detection first
        pii_col = detect_pii_by_column_name(header, config.categories_to_detect)

        if pii_col:
            if logger:
                logger.debug(
                    f"PII detected by name pattern: {header} -> {pii_col.category.value} "
                    f"(confidence: {pii_col.confidence:.2f})"
                )
            detected_columns.append(pii_col)
            continue

        # Try content-based detection
        if rows and sample_size > 0:
            # Extract sample of column values
            sample_values = [
                rows[i][col_idx] for i in range(sample_size) if col_idx < len(rows[i])
            ]

            pii_col = detect_pii_by_content(
                header,
                sample_values,
                config.categories_to_detect,
                config.confidence_threshold,
            )

            if pii_col:
                if logger:
                    logger.debug(
                        f"PII detected by content: {header} -> {pii_col.category.value} "
                        f"(confidence: {pii_col.confidence:.2f}, matches: {pii_col.sample_matches})"
                    )
                detected_columns.append(pii_col)

    detection_time = (time.time() - start_time) * 1000

    result = PIIDetectionResult(
        columns=detected_columns,
        sample_size=sample_size,
        detection_time_ms=detection_time,
    )

    if logger:
        if result.has_pii:
            logger.info(result.summary())
        else:
            logger.debug("No PII detected")

    return result


def merge_detection_results(
    pattern_result: PIIColumn | None,
    content_result: PIIColumn | None,
) -> PIIColumn | None:
    """Merge pattern and content detection results for a column.

    If both methods detected PII, uses the higher confidence result
    and marks detection method as 'both'.

    Args:
        pattern_result: Result from pattern detection.
        content_result: Result from content detection.

    Returns:
        Merged PIIColumn or None if no detection.
    """
    if pattern_result is None and content_result is None:
        return None

    if pattern_result is None:
        return content_result

    if content_result is None:
        return pattern_result

    # Both detected - use higher confidence, mark as 'both'
    if pattern_result.confidence >= content_result.confidence:
        return PIIColumn(
            column_name=pattern_result.column_name,
            category=pattern_result.category,
            confidence=pattern_result.confidence,
            suggested_transform=pattern_result.suggested_transform,
            detection_method="both",
            sample_matches=content_result.sample_matches,
        )
    else:
        return PIIColumn(
            column_name=content_result.column_name,
            category=content_result.category,
            confidence=content_result.confidence,
            suggested_transform=content_result.suggested_transform,
            detection_method="both",
            sample_matches=content_result.sample_matches,
        )


def validate_luhn(number: str) -> bool:
    """Validate a number using the Luhn algorithm (credit card checksum).

    Args:
        number: String of digits to validate.

    Returns:
        True if valid Luhn checksum.
    """
    digits = [int(d) for d in number if d.isdigit()]
    if len(digits) < 13:
        return False

    # Luhn algorithm
    checksum = 0
    for i, digit in enumerate(reversed(digits)):
        if i % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit

    return checksum % 10 == 0
