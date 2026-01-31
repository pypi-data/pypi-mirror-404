"""Column mapping step for sync pipeline.

This module provides the ColumnMappingStep that applies column
transformations including:
- Column renaming
- Column filtering/reordering
- Case transformations
- Prefix/suffix stripping
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class ColumnMappingStep(BaseSyncStep):
    """Apply column mapping transformations.

    This step applies configured column transformations:
    - Rename columns via mapping
    - Filter columns to include only specified ones
    - Reorder columns
    - Apply case transformations (upper, lower, title)
    - Strip prefixes/suffixes from column names

    Configuration can come from:
    - ctx.column_mapping_config (explicit)
    - ctx.config column mapping settings (from env/config)
    """

    @property
    def name(self) -> str:
        return "column_mapping"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if column mapping is configured and active."""
        # Streaming mode handles column mapping differently (or not at all)
        if ctx.mode == "streaming":
            return False

        # Check for explicit config
        if ctx.column_mapping_config and ctx.column_mapping_config.is_active():
            return True

        # Check config-level settings
        return getattr(ctx.config, "column_mapping_enabled", False)

    def execute(self, ctx: SyncContext) -> StepResult:
        """Apply column mapping transformations.

        Args:
            ctx: Sync context with headers and cleaned_rows.

        Returns:
            StepResult indicating transformations applied.
        """
        from mysql_to_sheets.core.column_mapping import (
            apply_column_mapping,
            get_column_mapping_config,
        )

        self.log_info(ctx, "Applying column mapping transformations")

        # Build config if not provided
        col_mapping = ctx.column_mapping_config
        if col_mapping is None:
            col_mapping = get_column_mapping_config(
                enabled=ctx.config.column_mapping_enabled,
                rename_map=ctx.config.column_mapping if ctx.config.column_mapping else None,
                column_order=ctx.config.column_order if ctx.config.column_order else None,
                case_transform=ctx.config.column_case if ctx.config.column_case != "none" else None,
                strip_prefix=ctx.config.column_strip_prefix if ctx.config.column_strip_prefix else None,
                strip_suffix=ctx.config.column_strip_suffix if ctx.config.column_strip_suffix else None,
            )

        original_cols = len(ctx.headers)
        headers, cleaned_rows = apply_column_mapping(
            ctx.headers, ctx.cleaned_rows, col_mapping
        )
        ctx.headers = headers
        ctx.cleaned_rows = cleaned_rows

        self.log_debug(ctx, f"Column mapping: {original_cols} → {len(headers)} columns")

        return self.success(
            f"Column mapping applied: {len(headers)} columns",
            data={"original_columns": original_cols, "final_columns": len(headers)},
        )
