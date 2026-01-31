"""Schema evolution policy handling for database schema changes.

This module provides configurable policies for handling database schema changes
during sync operations. When the database query returns different columns than
expected, apply a policy-based response.

Policies:
- strict: FAIL on any schema change (default, FREE tier)
- additive: ALLOW added columns, FAIL on removed columns (PRO+)
- flexible: ALLOW both added and removed columns (PRO+)
- notify_only: PROCEED with intersection, send notification (PRO+)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from mysql_to_sheets.core.exceptions import ErrorCategory, SyncError


class SchemaPolicy(str, Enum):
    """Schema evolution policy levels.

    Each policy determines how to handle schema changes during sync.
    """

    STRICT = "strict"  # FAIL on any schema change (default)
    ADDITIVE = "additive"  # ALLOW added columns, FAIL on removed
    FLEXIBLE = "flexible"  # ALLOW both added and removed columns
    NOTIFY_ONLY = "notify_only"  # PROCEED with intersection, notify

    @classmethod
    def from_string(cls, value: str) -> "SchemaPolicy":
        """Parse policy from string value.

        Args:
            value: Policy string (case-insensitive).

        Returns:
            SchemaPolicy enum value.

        Raises:
            ValueError: If value is not a valid policy.
        """
        try:
            return cls(value.lower())
        except ValueError:
            valid = ", ".join(p.value for p in cls)
            raise ValueError(f"Invalid schema policy '{value}'. Valid options: {valid}")


# Valid schema policies for validation
VALID_SCHEMA_POLICIES = tuple(p.value for p in SchemaPolicy)


@dataclass
class SchemaChange:
    """Result of comparing expected vs actual schema.

    Attributes:
        has_changes: Whether any schema changes were detected.
        added_columns: Columns present in actual but not in expected.
        removed_columns: Columns present in expected but not in actual.
        reordered: Whether column order changed (same columns, different order).
        expected_headers: The expected column headers.
        actual_headers: The actual column headers from query.
    """

    has_changes: bool = False
    added_columns: list[str] = field(default_factory=list)
    removed_columns: list[str] = field(default_factory=list)
    reordered: bool = False
    expected_headers: list[str] = field(default_factory=list)
    actual_headers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses.

        Returns:
            Dictionary representation of the schema change.
        """
        return {
            "has_changes": self.has_changes,
            "added_columns": self.added_columns,
            "removed_columns": self.removed_columns,
            "reordered": self.reordered,
            "expected_headers": self.expected_headers,
            "actual_headers": self.actual_headers,
        }

    def summary(self) -> str:
        """Get a human-readable summary of changes.

        Returns:
            Summary string describing the schema changes.
        """
        if not self.has_changes:
            return "No schema changes detected"

        parts = []
        if self.added_columns:
            parts.append(f"{len(self.added_columns)} column(s) added: {self.added_columns[:3]}")
            if len(self.added_columns) > 3:
                parts[-1] += f" (+{len(self.added_columns) - 3} more)"
        if self.removed_columns:
            parts.append(f"{len(self.removed_columns)} column(s) removed: {self.removed_columns[:3]}")
            if len(self.removed_columns) > 3:
                parts[-1] += f" (+{len(self.removed_columns) - 3} more)"
        if self.reordered and not self.added_columns and not self.removed_columns:
            parts.append("column order changed")

        return "; ".join(parts) if parts else "Schema changes detected"


class SchemaChangeError(SyncError):
    """Raised when schema change violates the configured policy.

    Examples:
        - Strict policy with any schema change
        - Additive policy with removed columns
    """

    def __init__(
        self,
        message: str,
        code: str,
        schema_change: SchemaChange | None = None,
        policy: str | None = None,
    ) -> None:
        """Initialize SchemaChangeError.

        Args:
            message: Human-readable error description.
            code: Error code (SCHEMA_001 or SCHEMA_002).
            schema_change: The detected schema change.
            policy: The policy that was violated.
        """
        details: dict[str, Any] = {}
        if schema_change:
            details["schema_change"] = schema_change.to_dict()
        if policy:
            details["policy"] = policy
        super().__init__(message, details, code=code)
        self.schema_change = schema_change
        self.policy = policy

    @property
    def category(self) -> ErrorCategory:
        """Get the error category."""
        return ErrorCategory.CONFIG


def detect_schema_change(
    expected_headers: list[str] | None,
    actual_headers: list[str],
) -> SchemaChange:
    """Detect differences between expected and actual schema.

    Args:
        expected_headers: The expected column headers from previous sync.
            If None, this is the first sync and no comparison is done.
        actual_headers: The actual column headers from current query.

    Returns:
        SchemaChange object describing any differences.
    """
    # First sync - no expected headers yet
    if expected_headers is None:
        return SchemaChange(
            has_changes=False,
            expected_headers=[],
            actual_headers=actual_headers,
        )

    expected_set = set(expected_headers)
    actual_set = set(actual_headers)

    added = sorted(actual_set - expected_set)
    removed = sorted(expected_set - actual_set)

    # Check for reorder (same columns but different order)
    reordered = (
        expected_set == actual_set
        and expected_headers != actual_headers
    )

    has_changes = bool(added or removed or reordered)

    return SchemaChange(
        has_changes=has_changes,
        added_columns=added,
        removed_columns=removed,
        reordered=reordered,
        expected_headers=expected_headers,
        actual_headers=actual_headers,
    )


def apply_schema_policy(
    change: SchemaChange,
    policy: SchemaPolicy | str,
    headers: list[str],
    rows: list[list[Any]],
) -> tuple[list[str], list[list[Any]], bool]:
    """Apply schema policy to handle detected changes.

    Args:
        change: The detected schema change.
        policy: The policy to apply.
        headers: Current column headers.
        rows: Current data rows.

    Returns:
        Tuple of (headers, rows, should_notify):
        - headers: Potentially filtered headers
        - rows: Potentially filtered rows
        - should_notify: Whether a notification should be sent

    Raises:
        SchemaChangeError: If the policy does not allow the detected changes.
    """
    # Normalize policy to enum
    if isinstance(policy, str):
        policy = SchemaPolicy.from_string(policy)

    # No changes - nothing to do
    if not change.has_changes:
        return headers, rows, False

    # STRICT: Fail on any change
    if policy == SchemaPolicy.STRICT:
        raise SchemaChangeError(
            message=(
                f"Schema change detected (policy: strict). {change.summary()}. "
                f"Use a less restrictive policy or update your sync configuration."
            ),
            code="SCHEMA_001",
            schema_change=change,
            policy=policy.value,
        )

    # ADDITIVE: Allow added columns, fail on removed
    if policy == SchemaPolicy.ADDITIVE:
        if change.removed_columns:
            raise SchemaChangeError(
                message=(
                    f"Columns removed from schema (policy: additive). "
                    f"Removed: {change.removed_columns}. "
                    f"Use 'flexible' policy to allow column removal, "
                    f"or update your sync configuration."
                ),
                code="SCHEMA_002",
                schema_change=change,
                policy=policy.value,
            )
        # Added columns are allowed - no filtering needed
        return headers, rows, True

    # FLEXIBLE: Allow both added and removed
    if policy == SchemaPolicy.FLEXIBLE:
        # No filtering needed - allow all changes
        return headers, rows, True

    # NOTIFY_ONLY: Proceed with intersection, notify
    if policy == SchemaPolicy.NOTIFY_ONLY:
        # Find common columns (intersection)
        if change.expected_headers:
            expected_set = set(change.expected_headers)
            # Filter to only columns that exist in both expected and actual
            common_columns = [h for h in headers if h in expected_set]

            if common_columns != headers:
                # Need to filter rows to match common columns
                column_indices = [headers.index(col) for col in common_columns]
                filtered_rows = [
                    [row[i] for i in column_indices]
                    for row in rows
                ]
                return common_columns, filtered_rows, True

        return headers, rows, True

    # Unknown policy - should not happen with enum
    raise ValueError(f"Unknown schema policy: {policy}")


def get_policy_tier_requirement(policy: SchemaPolicy | str) -> str | None:
    """Get the tier feature key required for a policy.

    Args:
        policy: The schema policy.

    Returns:
        Feature key for tier check, or None if no tier required (strict/free).
    """
    if isinstance(policy, str):
        policy = SchemaPolicy.from_string(policy)

    # Mapping of policies to tier feature keys
    policy_features = {
        SchemaPolicy.STRICT: None,  # Available in FREE tier
        SchemaPolicy.ADDITIVE: "schema_policy_additive",
        SchemaPolicy.FLEXIBLE: "schema_policy_flexible",
        SchemaPolicy.NOTIFY_ONLY: "schema_policy_notify_only",
    }

    return policy_features.get(policy)
