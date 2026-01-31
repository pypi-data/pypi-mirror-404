"""Data cleaning step for sync pipeline.

This module provides the DataCleanStep that converts database types
to Google Sheets compatible types.
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class DataCleanStep(BaseSyncStep):
    """Clean data for Google Sheets compatibility.

    This step converts database-specific types to types that Google Sheets
    can handle:
    - Decimal → float
    - datetime → formatted string (YYYY-MM-DD HH:MM:SS)
    - date → formatted string (YYYY-MM-DD)
    - None → empty string
    - bytes → decoded UTF-8 string
    - dict/list → string representation
    - PostgreSQL UUID → string
    - PostgreSQL arrays → comma-separated string

    The cleaned data is stored in ctx.cleaned_rows.
    """

    @property
    def name(self) -> str:
        return "clean_data"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if we have rows to clean."""
        return bool(ctx.rows)

    def execute(self, ctx: SyncContext) -> StepResult:
        """Clean data for Sheets compatibility.

        Reads ctx.rows and populates ctx.cleaned_rows with type-converted data.
        After cleaning, ctx.rows is cleared to free memory (avoids holding both
        raw and cleaned data in memory simultaneously).

        Args:
            ctx: Sync context with rows populated.

        Returns:
            StepResult indicating success.
        """
        from mysql_to_sheets.core.sync_legacy import clean_data

        db_type = ctx.config.db_type.lower()
        row_count = len(ctx.rows)
        self.log_debug(ctx, f"Cleaning {row_count} rows for {db_type}")

        ctx.cleaned_rows = clean_data(ctx.rows, ctx.logger, db_type=db_type)

        # Memory optimization: Free raw data after cleaning to avoid 2x memory usage.
        # The raw rows are no longer needed after type conversion.
        ctx.rows = []

        self.log_debug(ctx, f"Cleaned {len(ctx.cleaned_rows)} rows")

        return self.success(f"Cleaned {len(ctx.cleaned_rows)} rows")
