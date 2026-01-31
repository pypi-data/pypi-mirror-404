"""Sheets push step for sync pipeline.

This module provides the SheetsPushStep that pushes data to Google Sheets.
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class SheetsPushStep(BaseSyncStep):
    """Push data to Google Sheets.

    This step pushes the cleaned and transformed data to the configured
    Google Sheet. It supports two modes:

    - replace: Clear sheet and push all data
    - append: Add rows without clearing

    Streaming mode is handled separately by the streaming module.
    """

    @property
    def name(self) -> str:
        return "push_to_sheets"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if not dry-run, preview, or streaming mode."""
        # Don't run for dry-run or preview (handled by earlier steps)
        if ctx.dry_run or ctx.preview:
            return False
        # Streaming mode handles its own pushing
        if ctx.mode == "streaming":
            return False
        return True

    def execute(self, ctx: SyncContext) -> StepResult:
        """Push data to Google Sheets.

        Args:
            ctx: Sync context with headers and cleaned_rows.

        Returns:
            StepResult indicating push success.

        Raises:
            SheetsError: If Google Sheets API call fails.
        """
        from mysql_to_sheets.core.sync_legacy import push_to_sheets

        row_count = len(ctx.cleaned_rows)
        col_count = len(ctx.headers)

        self.log_info(ctx, f"Pushing {row_count} rows to sheet (mode={ctx.mode})")

        push_to_sheets(
            ctx.config,
            ctx.headers,
            ctx.cleaned_rows,
            ctx.logger,
            mode=ctx.mode,
            create_worksheet=ctx.create_worksheet,
        )

        self.log_info(
            ctx, f"Successfully pushed {row_count} rows (mode={ctx.mode})"
        )

        return self.success(
            message=f"Pushed {row_count} rows",
            data={
                "rows_synced": row_count,
                "columns": col_count,
                "mode": ctx.mode,
            },
        )


class StreamingPushStep(BaseSyncStep):
    """Handle streaming mode sync.

    This step delegates to the streaming module for memory-efficient
    sync of large datasets using chunked processing.
    """

    @property
    def name(self) -> str:
        return "streaming_push"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run only for streaming mode."""
        return ctx.mode == "streaming"

    def execute(self, ctx: SyncContext) -> StepResult:
        """Execute streaming sync.

        Args:
            ctx: Sync context with config for streaming.

        Returns:
            StepResult with streaming results.

        Raises:
            SyncError: If streaming sync fails.
        """
        from mysql_to_sheets.core.streaming import StreamingConfig, run_streaming_sync

        # Warn if column mapping is configured (not supported in streaming)
        # EC-56: Store warning in ctx.step_warnings for propagation to SyncResult
        if ctx.column_mapping_config and ctx.column_mapping_config.is_active():
            warning_msg = (
                "Column mapping is configured but will be ignored in streaming mode. "
                "Use 'replace' or 'append' mode to apply column transformations."
            )
            self.log_warning(ctx, warning_msg)
            ctx.step_warnings.append(warning_msg)

        self.log_info(ctx, f"Starting streaming sync with chunk size {ctx.chunk_size}")

        streaming_config = StreamingConfig(chunk_size=ctx.chunk_size)
        streaming_result = run_streaming_sync(
            ctx.config,
            streaming_config=streaming_config,
            logger_instance=ctx.logger,
            dry_run=ctx.dry_run,
            atomic=ctx.atomic,
            preserve_gid=ctx.preserve_gid,
            resumable=ctx.resumable,
            job_id=ctx.job_id,
            config_id=ctx.config_id,
        )

        self.log_info(
            ctx,
            f"Streaming complete: {streaming_result.total_rows} rows in "
            f"{streaming_result.total_chunks} chunks",
        )

        # Short-circuit since streaming handles everything
        return self.short_circuit(
            message=(
                f"Streamed {streaming_result.total_rows} rows "
                f"in {streaming_result.total_chunks} chunks"
            ),
            data={
                "streaming": True,
                "total_rows": streaming_result.total_rows,
                "total_chunks": streaming_result.total_chunks,
                "failed_chunks": streaming_result.failed_chunks,
                "success": streaming_result.success,
            },
        )
