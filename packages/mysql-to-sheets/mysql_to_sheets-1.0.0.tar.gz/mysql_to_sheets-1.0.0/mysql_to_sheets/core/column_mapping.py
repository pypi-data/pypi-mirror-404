"""Column mapping and transformation for sync data.

This module provides utilities for renaming, filtering, and transforming
column headers before pushing data to Google Sheets.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ColumnMappingConfig:
    """Configuration for column mapping and transformation.

    Attributes:
        enabled: Whether column mapping is enabled.
        rename_map: Dictionary mapping original column names to new names.
        column_order: List of columns to include and their order. None means all columns.
        case_transform: Case transformation to apply (none, upper, lower, title).
        strip_prefix: Prefix to strip from column names.
        strip_suffix: Suffix to strip from column names.
        strict: If True, raise ValueError for non-existent columns in column_order.
    """

    enabled: bool = False
    rename_map: dict[str, str] = field(default_factory=dict)
    column_order: list[str] | None = None
    case_transform: str = "none"
    strip_prefix: str = ""
    strip_suffix: str = ""
    strict: bool = False

    def is_active(self) -> bool:
        """Check if any column mapping should be applied.

        Returns:
            True if column mapping is enabled and any transformation is configured.
        """
        if not self.enabled:
            return False

        return (
            bool(self.rename_map)
            or self.column_order is not None
            or self.case_transform != "none"
            or bool(self.strip_prefix)
            or bool(self.strip_suffix)
        )

    @classmethod
    def from_env(cls) -> "ColumnMappingConfig":
        """Create ColumnMappingConfig from environment variables.

        Environment variables:
            COLUMN_MAPPING_ENABLED: Enable column mapping (true/false).
            COLUMN_MAPPING: JSON or key=value mapping for column renames.
            COLUMN_ORDER: Comma-separated list of columns to include.
            COLUMN_CASE: Case transformation (none, upper, lower, title).
            COLUMN_STRIP_PREFIX: Prefix to strip from column names.
            COLUMN_STRIP_SUFFIX: Suffix to strip from column names.
            COLUMN_MAPPING_STRICT: Raise error for non-existent columns (true/false).

        Returns:
            ColumnMappingConfig instance.
        """
        enabled = os.getenv("COLUMN_MAPPING_ENABLED", "false").lower() == "true"
        mapping_str = os.getenv("COLUMN_MAPPING", "")
        order_str = os.getenv("COLUMN_ORDER", "")
        case_transform = os.getenv("COLUMN_CASE", "none").lower()
        strip_prefix = os.getenv("COLUMN_STRIP_PREFIX", "")
        strip_suffix = os.getenv("COLUMN_STRIP_SUFFIX", "")
        strict = os.getenv("COLUMN_MAPPING_STRICT", "false").lower() == "true"

        # Parse rename map
        rename_map = _parse_rename_map(mapping_str)

        # Parse column order
        column_order = None
        if order_str.strip():
            column_order = [col.strip() for col in order_str.split(",") if col.strip()]

        return cls(
            enabled=enabled,
            rename_map=rename_map,
            column_order=column_order,
            case_transform=case_transform,
            strip_prefix=strip_prefix,
            strip_suffix=strip_suffix,
            strict=strict,
        )


def _parse_rename_map(mapping_str: str) -> dict[str, str]:
    """Parse column rename mapping from string.

    Supports two formats:
    1. JSON: '{"old_name": "New Name", "other_col": "Other Column"}'
    2. Key=Value: 'old_name=New Name,other_col=Other Column'

    Args:
        mapping_str: Mapping string in JSON or key=value format.

    Returns:
        Dictionary mapping original names to new names.
    """
    if not mapping_str or not mapping_str.strip():
        return {}

    mapping_str = mapping_str.strip()

    # Try JSON format first
    if mapping_str.startswith("{"):
        try:
            return json.loads(mapping_str)  # type: ignore[no-any-return]
        except json.JSONDecodeError:
            pass

    # Try key=value format
    result = {}
    for pair in mapping_str.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            result[key.strip()] = value.strip()

    return result


def _apply_case_transform(name: str, transform: str) -> str:
    """Apply case transformation to a column name.

    Args:
        name: Original column name.
        transform: Transformation type (none, upper, lower, title).

    Returns:
        Transformed column name.
    """
    if transform == "upper":
        return name.upper()
    elif transform == "lower":
        return name.lower()
    elif transform == "title":
        return name.title()
    return name


def _transform_column_name(
    name: str,
    config: ColumnMappingConfig,
) -> str:
    """Transform a single column name according to configuration.

    Applies transformations in order:
    1. Strip prefix
    2. Strip suffix
    3. Apply rename map
    4. Apply case transformation

    Args:
        name: Original column name.
        config: Column mapping configuration.

    Returns:
        Transformed column name.
    """
    result = name

    # Strip prefix
    if config.strip_prefix and result.startswith(config.strip_prefix):
        result = result[len(config.strip_prefix) :]

    # Strip suffix
    if config.strip_suffix and result.endswith(config.strip_suffix):
        result = result[: -len(config.strip_suffix)]

    # Apply rename map (use the post-strip name as key)
    if result in config.rename_map:
        result = config.rename_map[result]
    elif name in config.rename_map:
        # Also check original name in case strip happened after rename
        result = config.rename_map[name]

    # Apply case transformation
    result = _apply_case_transform(result, config.case_transform)

    return result


def apply_column_mapping(
    headers: list[str],
    rows: list[list[Any]],
    config: ColumnMappingConfig,
    logger: logging.Logger | None = None,
) -> tuple[list[str], list[list[Any]]]:
    """Apply column mapping configuration to headers and rows.

    This function transforms column headers and optionally filters/reorders
    columns based on the configuration.

    Args:
        headers: List of original column headers.
        rows: List of data rows.
        config: Column mapping configuration.
        logger: Optional logger for warnings about missing columns.

    Returns:
        Tuple of (transformed_headers, transformed_rows).

    Raises:
        ValueError: If config.strict is True and column_order contains
            columns not found in headers.

    Example:
        >>> config = ColumnMappingConfig(
        ...     enabled=True,
        ...     rename_map={"cust_id": "Customer ID"},
        ...     column_order=["Customer ID", "name"],
        ... )
        >>> headers = ["cust_id", "name", "email"]
        >>> rows = [[1, "Alice", "alice@example.com"]]
        >>> new_headers, new_rows = apply_column_mapping(headers, rows, config)
        >>> new_headers
        ['Customer ID', 'name']
        >>> new_rows
        [[1, 'Alice']]
    """
    if not config.is_active():
        return headers, rows

    # Validate rename_map keys exist in headers
    if config.rename_map:
        header_set = set(headers)
        missing_rename_keys = [
            key for key in config.rename_map.keys() if key not in header_set
        ]
        if missing_rename_keys:
            msg = f"Column mapping key(s) not found in data: {missing_rename_keys}"
            if config.strict:
                raise ValueError(msg)
            elif logger:
                logger.warning(
                    f"{msg}. Available columns: {headers}. "
                    "These mappings will be ignored."
                )

    # Transform all header names
    transformed_headers = [_transform_column_name(h, config) for h in headers]

    # Check for duplicate transformed names (would cause silent data loss)
    seen_names: dict[str, int] = {}
    duplicates: list[str] = []
    for i, name in enumerate(transformed_headers):
        if name in seen_names:
            duplicates.append(f"'{name}' (columns {seen_names[name] + 1} and {i + 1})")
        else:
            seen_names[name] = i

    if duplicates:
        msg = (
            f"Column transformation resulted in duplicate column names: "
            f"{', '.join(duplicates)}. This would cause data loss. "
            f"Use rename_map to give unique names or adjust case_transform."
        )
        raise ValueError(msg)

    # Build mapping of transformed name to original index
    name_to_index: dict[str, int] = {}
    for i, (orig, trans) in enumerate(zip(headers, transformed_headers)):
        name_to_index[trans] = i
        # Also keep original name for lookup
        name_to_index[orig] = i

    # Determine which columns to include and in what order
    if config.column_order is not None:
        # Check for missing columns first
        missing_columns = [col for col in config.column_order if col not in name_to_index]

        if missing_columns:
            msg = f"Column(s) not found in data: {missing_columns}"
            if config.strict:
                raise ValueError(msg)
            elif logger:
                logger.warning(
                    f"{msg}. Available columns: {list(name_to_index.keys())}. "
                    "Skipping missing columns."
                )

        # Filter and reorder based on column_order
        selected_indices = []
        final_headers = []

        for col_name in config.column_order:
            if col_name in name_to_index:
                idx = name_to_index[col_name]
                selected_indices.append(idx)
                final_headers.append(transformed_headers[idx])

        # Transform rows to match selected columns
        transformed_rows = [[row[i] for i in selected_indices] for row in rows]

        return final_headers, transformed_rows
    else:
        # Keep all columns with transformed names
        return transformed_headers, rows


def get_column_mapping_config(
    enabled: bool | None = None,
    rename_map: dict[str, str] | str | None = None,
    column_order: list[str] | str | None = None,
    case_transform: str | None = None,
    strip_prefix: str | None = None,
    strip_suffix: str | None = None,
    strict: bool | None = None,
) -> ColumnMappingConfig:
    """Create a ColumnMappingConfig with optional overrides from env.

    Args:
        enabled: Override enabled setting.
        rename_map: Override rename map (dict or string format).
        column_order: Override column order (list or comma-separated string).
        case_transform: Override case transformation.
        strip_prefix: Override strip prefix.
        strip_suffix: Override strip suffix.
        strict: Override strict mode (raise error for missing columns).

    Returns:
        ColumnMappingConfig with overrides applied.
    """
    # Start with env defaults
    config = ColumnMappingConfig.from_env()

    # Apply overrides
    if enabled is not None:
        config.enabled = enabled

    if rename_map is not None:
        if isinstance(rename_map, str):
            config.rename_map = _parse_rename_map(rename_map)
        else:
            config.rename_map = rename_map

    if column_order is not None:
        if isinstance(column_order, str):
            config.column_order = [col.strip() for col in column_order.split(",") if col.strip()]
        else:
            config.column_order = column_order

    if case_transform is not None:
        config.case_transform = case_transform.lower()

    if strip_prefix is not None:
        config.strip_prefix = strip_prefix

    if strip_suffix is not None:
        config.strip_suffix = strip_suffix

    if strict is not None:
        config.strict = strict

    return config
