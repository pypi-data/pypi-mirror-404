"""Validation steps for sync pipeline.

This module provides validation steps that run early in the pipeline:
- ConfigValidationStep: Validates configuration before sync starts
- BatchSizeValidationStep: Validates data fits within Google Sheets limits
- QueryTypeValidationStep: Validates SQL query is a SELECT statement
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class ConfigValidationStep(BaseSyncStep):
    """Validate configuration before sync starts.

    This step runs early to catch configuration errors before any
    database or API calls are made.
    """

    @property
    def name(self) -> str:
        return "config_validation"

    def should_run(self, ctx: SyncContext) -> bool:
        """Always run config validation."""
        return True

    def execute(self, ctx: SyncContext) -> StepResult:
        """Validate the sync configuration.

        Args:
            ctx: Sync context containing the config to validate.

        Returns:
            StepResult indicating validation success or failure.

        Raises:
            ConfigError: If configuration is invalid.
        """
        self.log_debug(ctx, "Validating configuration")

        # This raises ConfigError if invalid
        ctx.config.validate_or_raise()

        self.log_debug(ctx, f"Configuration validated: {ctx.config}")
        return self.success("Configuration valid")


class QueryTypeValidationStep(BaseSyncStep):
    """Validate that SQL query is a SELECT statement.

    Non-SELECT queries (INSERT, UPDATE, DELETE) don't return data and
    would result in a "successful" sync with 0 rows, potentially
    clearing the sheet.
    """

    @property
    def name(self) -> str:
        return "query_type_validation"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if SQL validation is enabled in config."""
        return getattr(ctx.config, "sql_validation_enabled", True)

    def execute(self, ctx: SyncContext) -> StepResult:
        """Validate the query is a SELECT statement.

        Args:
            ctx: Sync context containing the config with SQL query.

        Returns:
            StepResult indicating validation success or failure.

        Raises:
            ConfigError: If query is not a SELECT and strict mode is enabled.
        """
        from mysql_to_sheets.core.sync_legacy import validate_query_type

        self.log_debug(ctx, "Validating query type")
        validate_query_type(
            ctx.config.sql_query,
            ctx.logger,
            strict=ctx.config.sql_validation_enabled,
        )

        return self.success("Query type validated")


class BatchSizeValidationStep(BaseSyncStep):
    """Validate data fits within Google Sheets limits.

    This step runs after data is fetched but before pushing to Sheets.
    It validates:
    - Column count <= 18,278 (column ZZZ)
    - Row count <= 10,000,000
    - Total cells <= 10,000,000
    - Cell content <= 50,000 characters
    - Consistent column counts (ragged row detection)
    """

    @property
    def name(self) -> str:
        return "batch_size_validation"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if we have data to validate."""
        return bool(ctx.headers) and bool(ctx.rows or ctx.cleaned_rows)

    def execute(self, ctx: SyncContext) -> StepResult:
        """Validate data fits within Sheets limits.

        Args:
            ctx: Sync context with headers and rows populated.

        Returns:
            StepResult indicating validation success or failure.

        Raises:
            SheetsError: If data exceeds Sheets limits.
            ConfigError: If data has ragged rows.
        """
        from mysql_to_sheets.core.sync_legacy import validate_batch_size

        # Use cleaned_rows if available, otherwise raw rows
        rows = ctx.cleaned_rows if ctx.cleaned_rows else ctx.rows

        self.log_debug(
            ctx, f"Validating batch: {len(ctx.headers)} cols x {len(rows)} rows"
        )

        validate_batch_size(ctx.headers, rows, ctx.logger)

        total_cells = len(ctx.headers) * (len(rows) + 1)  # +1 for header
        return self.success(f"Batch validated: {total_cells:,} cells")
