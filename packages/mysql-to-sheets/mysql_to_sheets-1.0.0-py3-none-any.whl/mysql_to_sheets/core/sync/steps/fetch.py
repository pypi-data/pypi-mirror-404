"""Data fetch step for sync pipeline.

This module provides the DataFetchStep that connects to the database
and executes the configured SQL query to retrieve data.
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class DataFetchStep(BaseSyncStep):
    """Fetch data from the configured database.

    This step connects to the database (MySQL, PostgreSQL, SQLite, or MSSQL)
    and executes the SQL query to retrieve data. It populates ctx.headers
    and ctx.rows.

    Features:
    - Supports incremental sync via timestamp filtering
    - Supports query caching
    - Supports connection pooling (MySQL, PostgreSQL)
    - Validates query type (warns on non-SELECT)
    """

    @property
    def name(self) -> str:
        return "fetch_data"

    def should_run(self, ctx: SyncContext) -> bool:
        """Always run data fetch for non-streaming modes."""
        # Streaming mode handles its own data fetching
        return ctx.mode != "streaming"

    def execute(self, ctx: SyncContext) -> StepResult:
        """Fetch data from the database.

        Populates ctx.headers and ctx.rows with the query results.

        Args:
            ctx: Sync context with config containing database credentials.

        Returns:
            StepResult indicating success or failure.

        Raises:
            DatabaseError: If database connection or query fails.
        """
        from mysql_to_sheets.core.sync_legacy import fetch_data

        db_type = ctx.config.db_type.lower()
        self.log_info(
            ctx,
            f"Connecting to {db_type.upper()}: "
            f"{ctx.config.db_host}:{ctx.config.db_port}/{ctx.config.db_name}",
        )

        # Fetch data from database
        headers, rows = fetch_data(
            ctx.config,
            ctx.logger,
            incremental_config=ctx.incremental_config,
            use_pool=getattr(ctx.config, "db_pool_enabled", False),
        )

        # Store in context
        ctx.headers = headers
        ctx.rows = rows

        self.log_info(ctx, f"Fetched {len(rows)} rows with {len(headers)} columns")

        return self.success(
            message=f"Fetched {len(rows)} rows",
            data={"row_count": len(rows), "column_count": len(headers)},
        )


class EmptyResultHandlerStep(BaseSyncStep):
    """Handle empty query results based on configuration.

    This step checks if the query returned no data and handles it
    according to the sync_empty_result_action setting:
    - 'warn': Log warning and skip update (default)
    - 'error': Raise an error
    - 'clear': Push headers only to clear existing data
    """

    @property
    def name(self) -> str:
        return "empty_result_handler"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if data fetch returned no rows."""
        return not ctx.rows and bool(ctx.headers)

    def execute(self, ctx: SyncContext) -> StepResult:
        """Handle empty query results.

        Args:
            ctx: Sync context with headers but empty rows.

        Returns:
            StepResult, potentially short-circuiting the pipeline.

        Raises:
            SyncError: If empty_result_action is 'error'.
        """
        from mysql_to_sheets.core.exceptions import ErrorCode, SyncError
        from mysql_to_sheets.core.sync_legacy import push_to_sheets

        empty_action = getattr(ctx.config, "sync_empty_result_action", "warn") or "warn"

        # EC-37: Provide helpful warning when query returns zero rows
        self.log_warning(
            ctx,
            f"Query returned 0 rows (action={empty_action}). "
            "This usually means:\n"
            "  1. The WHERE clause filtered out all data\n"
            "  2. The table is empty\n"
            "  3. The table name has different capitalization\n\n"
            f"Try: SELECT * FROM your_table LIMIT 10  — to verify data exists\n"
            f"Error code: {ErrorCode.CONFIG_QUERY_NO_RESULTS}",
        )

        if empty_action == "error":
            raise SyncError(
                message="Query returned no rows; aborting to protect sheet data",
                code="CONFIG_106",
            )

        if empty_action == "clear" and not ctx.dry_run and ctx.mode == "replace":
            # Explicitly requested: push headers to clear old data
            self.log_info(ctx, "Pushing empty dataset to clear sheet")
            push_to_sheets(
                ctx.config,
                ctx.headers,
                [],
                ctx.logger,
                mode=ctx.mode,
                create_worksheet=ctx.create_worksheet,
            )
            return self.short_circuit(
                "Empty result: sheet cleared",
                data={"action": "clear"},
            )

        # Default: warn and skip
        # EC-53: Include warning message in step data for SyncResult
        warning_msg = (
            "Empty result set in replace mode — skipping sheet update "
            "to prevent data loss. Set SYNC_EMPTY_RESULT_ACTION=clear to allow."
        )
        self.log_warning(ctx, warning_msg)

        return self.short_circuit(
            "Empty result: skipped update",
            data={
                "action": "skip",
                "empty_result_skipped": True,
                "warnings": [warning_msg],
            },
        )
