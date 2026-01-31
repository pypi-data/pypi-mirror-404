"""PII (Personally Identifiable Information) core dataclasses.

This module provides the core data structures for PII detection and transformation:
- PIITransform: Enum of available transformation types
- PIICategory: Categories of PII (email, phone, SSN, etc.)
- PIIColumn: Detection result for a single column
- PIIDetectionResult: Aggregated detection results
- PIITransformConfig: Configuration for PII handling
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PIITransform(str, Enum):
    """Available PII transformation types.

    Each transform provides a different level of data protection:
    - NONE: No transformation (requires acknowledgment)
    - HASH: SHA256 hash (one-way, consistent)
    - REDACT: Replace with *** (category-aware)
    - PARTIAL_MASK: Keep last N characters visible
    """

    NONE = "none"
    HASH = "hash"
    REDACT = "redact"
    PARTIAL_MASK = "partial_mask"

    @classmethod
    def from_string(cls, value: str) -> "PIITransform":
        """Convert string to PIITransform.

        Args:
            value: Transform name as string.

        Returns:
            Corresponding PIITransform enum value.

        Raises:
            ValueError: If value is not a valid transform.
        """
        try:
            return cls(value.lower())
        except ValueError as e:
            valid = ", ".join(t.value for t in cls)
            raise ValueError(f"Invalid PII transform '{value}'. Valid: {valid}") from e


class PIICategory(str, Enum):
    """Categories of personally identifiable information.

    Each category has specific detection patterns and may have
    category-aware redaction formats.
    """

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"
    IP_ADDRESS = "ip_address"
    DATE_OF_BIRTH = "date_of_birth"
    PASSPORT = "passport"
    DRIVER_LICENSE = "driver_license"
    NATIONAL_ID = "national_id"
    BANK_ACCOUNT = "bank_account"
    UNKNOWN = "unknown"

    @classmethod
    def from_string(cls, value: str) -> "PIICategory":
        """Convert string to PIICategory.

        Args:
            value: Category name as string.

        Returns:
            Corresponding PIICategory enum value.

        Raises:
            ValueError: If value is not a valid category.
        """
        try:
            return cls(value.lower())
        except ValueError as e:
            valid = ", ".join(c.value for c in cls)
            raise ValueError(f"Invalid PII category '{value}'. Valid: {valid}") from e


@dataclass
class PIIColumn:
    """Detection result for a single column.

    Attributes:
        column_name: Name of the column.
        category: Detected PII category.
        confidence: Detection confidence (0.0-1.0).
        suggested_transform: Recommended transformation.
        detection_method: How PII was detected ('pattern', 'content', 'both').
        sample_matches: Number of rows with PII matches in content sample.
    """

    column_name: str
    category: PIICategory
    confidence: float
    suggested_transform: PIITransform = PIITransform.HASH
    detection_method: str = "pattern"
    sample_matches: int = 0

    def __post_init__(self) -> None:
        """Validate confidence is in valid range."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "column_name": self.column_name,
            "category": self.category.value,
            "confidence": self.confidence,
            "suggested_transform": self.suggested_transform.value,
            "detection_method": self.detection_method,
            "sample_matches": self.sample_matches,
        }


@dataclass
class PIIDetectionResult:
    """Aggregated PII detection results.

    Attributes:
        columns: List of detected PII columns.
        has_pii: Whether any PII was detected.
        requires_acknowledgment: Whether sync requires user acknowledgment.
        sample_size: Number of rows sampled for content detection.
        detection_time_ms: Time taken for detection in milliseconds.
    """

    columns: list[PIIColumn] = field(default_factory=list)
    has_pii: bool = False
    requires_acknowledgment: bool = False
    sample_size: int = 0
    detection_time_ms: float = 0.0

    def __post_init__(self) -> None:
        """Update derived fields."""
        self.has_pii = len(self.columns) > 0
        # Requires acknowledgment if any PII column doesn't have an explicit transform
        self.requires_acknowledgment = self.has_pii

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "columns": [col.to_dict() for col in self.columns],
            "has_pii": self.has_pii,
            "requires_acknowledgment": self.requires_acknowledgment,
            "sample_size": self.sample_size,
            "detection_time_ms": self.detection_time_ms,
        }

    def get_column(self, column_name: str) -> PIIColumn | None:
        """Get PII column by name.

        Args:
            column_name: Column name to look up.

        Returns:
            PIIColumn if found, None otherwise.
        """
        for col in self.columns:
            if col.column_name == column_name:
                return col
        return None

    def get_columns_by_category(self, category: PIICategory) -> list[PIIColumn]:
        """Get all columns with a specific category.

        Args:
            category: PII category to filter by.

        Returns:
            List of matching PIIColumn objects.
        """
        return [col for col in self.columns if col.category == category]

    def summary(self) -> str:
        """Generate human-readable summary.

        Returns:
            Summary string.
        """
        if not self.has_pii:
            return "No PII detected"

        categories = {}
        for col in self.columns:
            cat = col.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(col.column_name)

        parts = []
        for cat, cols in categories.items():
            parts.append(f"{cat}: {', '.join(cols)}")

        return f"PII detected ({len(self.columns)} columns) - {'; '.join(parts)}"


@dataclass
class PIITransformConfig:
    """Configuration for PII detection and transformation.

    Attributes:
        enabled: Whether PII detection is enabled.
        auto_detect: Whether to auto-detect PII in columns.
        transform_map: Explicit column-to-transform mapping.
        default_transform: Default transform for detected PII.
        acknowledged_columns: Columns acknowledged to sync without transform.
        confidence_threshold: Minimum confidence for PII detection.
        sample_size: Number of rows to sample for content detection.
        categories_to_detect: Categories to detect (None = all).
    """

    enabled: bool = False
    auto_detect: bool = True
    transform_map: dict[str, PIITransform] = field(default_factory=dict)
    default_transform: PIITransform = PIITransform.HASH
    acknowledged_columns: list[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    sample_size: int = 100
    categories_to_detect: list[PIICategory] | None = None

    def __post_init__(self) -> None:
        """Validate configuration."""
        if not 0.0 <= self.confidence_threshold <= 1.0:
            raise ValueError(
                f"confidence_threshold must be 0.0-1.0, got {self.confidence_threshold}"
            )
        if self.sample_size < 1:
            raise ValueError(f"sample_size must be >= 1, got {self.sample_size}")

        # Convert string values in transform_map to PIITransform enum
        if self.transform_map:
            converted = {}
            for col, transform in self.transform_map.items():
                if isinstance(transform, str):
                    converted[col] = PIITransform.from_string(transform)
                else:
                    converted[col] = transform
            self.transform_map = converted

    def is_active(self) -> bool:
        """Check if PII handling is active.

        Returns:
            True if enabled and has auto_detect or explicit transforms.
        """
        return self.enabled and (self.auto_detect or bool(self.transform_map))

    def get_transform_for_column(self, column_name: str) -> PIITransform | None:
        """Get explicit transform for a column.

        Args:
            column_name: Column name.

        Returns:
            PIITransform if explicitly configured, None otherwise.
        """
        return self.transform_map.get(column_name)

    def is_acknowledged(self, column_name: str) -> bool:
        """Check if column is acknowledged to sync without transform.

        Args:
            column_name: Column name.

        Returns:
            True if column is in acknowledged list.
        """
        return column_name in self.acknowledged_columns

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "enabled": self.enabled,
            "auto_detect": self.auto_detect,
            "transform_map": {k: v.value for k, v in self.transform_map.items()},
            "default_transform": self.default_transform.value,
            "acknowledged_columns": self.acknowledged_columns,
            "confidence_threshold": self.confidence_threshold,
            "sample_size": self.sample_size,
            "categories_to_detect": (
                [c.value for c in self.categories_to_detect]
                if self.categories_to_detect
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PIITransformConfig":
        """Create from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            PIITransformConfig instance.
        """
        # Convert string transforms to enum
        transform_map = {}
        if "transform_map" in data and data["transform_map"]:
            for col, transform in data["transform_map"].items():
                transform_map[col] = PIITransform.from_string(transform)

        # Convert default transform
        default_transform = PIITransform.HASH
        if "default_transform" in data and data["default_transform"]:
            default_transform = PIITransform.from_string(data["default_transform"])

        # Convert categories
        categories = None
        if "categories_to_detect" in data and data["categories_to_detect"]:
            categories = [PIICategory.from_string(c) for c in data["categories_to_detect"]]

        return cls(
            enabled=data.get("enabled", False),
            auto_detect=data.get("auto_detect", True),
            transform_map=transform_map,
            default_transform=default_transform,
            acknowledged_columns=data.get("acknowledged_columns", []),
            confidence_threshold=data.get("confidence_threshold", 0.7),
            sample_size=data.get("sample_size", 100),
            categories_to_detect=categories,
        )
