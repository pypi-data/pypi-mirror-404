"""Sync orchestrator for pipeline execution.

This module provides the SyncOrchestrator that coordinates the execution
of pipeline steps and hooks.
"""

from __future__ import annotations

import logging
import secrets
import time
from typing import TYPE_CHECKING, Any

from mysql_to_sheets.core.sync.dataclasses import SyncResult
from mysql_to_sheets.core.sync.pipeline import SyncPipeline, create_default_pipeline
from mysql_to_sheets.core.sync.protocols import SyncContext

if TYPE_CHECKING:
    from mysql_to_sheets.core.column_mapping import ColumnMappingConfig
    from mysql_to_sheets.core.config import Config
    from mysql_to_sheets.core.incremental import IncrementalConfig
    from mysql_to_sheets.core.pii import PIITransformConfig


class SyncOrchestrator:
    """Orchestrator for executing sync pipeline.

    The orchestrator coordinates:
    1. Creating SyncContext from parameters
    2. Calling hooks.on_start()
    3. Executing steps in order, checking should_run()
    4. Handling short-circuits and errors
    5. Calling hooks.on_success() / on_failure() / on_complete()
    6. Building and returning SyncResult

    Example:
        orchestrator = SyncOrchestrator()
        result = orchestrator.run(config=my_config)

        # Or with custom pipeline
        pipeline = create_default_pipeline()
        pipeline.add_step(MyCustomStep(), after="clean_data")
        orchestrator = SyncOrchestrator(pipeline=pipeline)
        result = orchestrator.run(config=my_config)
    """

    def __init__(self, pipeline: SyncPipeline | None = None) -> None:
        """Initialize orchestrator with optional custom pipeline.

        Args:
            pipeline: Custom pipeline. If None, uses default pipeline.
        """
        self.pipeline = pipeline or create_default_pipeline()

    def run(
        self,
        config: "Config | None" = None,
        logger: logging.Logger | None = None,
        dry_run: bool = False,
        preview: bool = False,
        mode: str | None = None,
        chunk_size: int | None = None,
        incremental_config: "IncrementalConfig | None" = None,
        column_mapping_config: "ColumnMappingConfig | None" = None,
        notify: bool | None = None,
        source: str = "sync",
        organization_id: int | None = None,
        config_name: str | None = None,
        sync_id: str | None = None,
        config_id: int | None = None,
        skip_snapshot: bool = False,
        create_worksheet: bool | None = None,
        atomic: bool = True,
        preserve_gid: bool = False,
        schema_policy: str | None = None,
        expected_headers: list[str] | None = None,
        pii_config: "PIITransformConfig | None" = None,
        pii_acknowledged: bool = False,
        detect_pii: bool | None = None,
        resumable: bool = False,
        job_id: int | None = None,
    ) -> SyncResult:
        """Execute the sync pipeline.

        This method has the same signature as run_sync() for backward
        compatibility.

        Args:
            config: Configuration object. If None, loads from environment.
            logger: Logger instance. If None, creates one from config.
            dry_run: If True, fetch and validate but don't push to Sheets.
            preview: If True, show diff with current sheet data without pushing.
            mode: Sync mode ('replace', 'append', 'streaming'). Defaults to config.
            chunk_size: Chunk size for streaming mode. Defaults to config.
            incremental_config: Optional incremental sync configuration.
            column_mapping_config: Optional column mapping configuration.
            notify: Whether to send notifications. If None, uses config settings.
            source: Source of the sync (cli, api, web, scheduler).
            organization_id: Optional organization ID for webhook delivery.
            config_name: Optional config name for webhook payloads.
            sync_id: Optional unique sync ID for webhook payloads.
            config_id: Optional sync config ID for freshness tracking.
            skip_snapshot: If True, skip creating a pre-sync snapshot.
            create_worksheet: If True, create worksheet if missing.
            atomic: Enable atomic staging for streaming mode.
            preserve_gid: Preserve worksheet GID during atomic swap.
            schema_policy: Schema evolution policy.
            expected_headers: Expected column headers from previous sync.
            pii_config: Optional PII transform configuration.
            pii_acknowledged: Whether PII has been acknowledged.
            detect_pii: Override PII detection setting.
            resumable: Enable checkpoint/resume for streaming.
            job_id: Job ID for checkpoint tracking.

        Returns:
            SyncResult with operation status and statistics.

        Raises:
            ConfigError: If configuration is invalid.
            DatabaseError: If database operations fail.
            SheetsError: If Google Sheets operations fail.
        """
        from mysql_to_sheets.core.config import get_config
        from mysql_to_sheets.core.exceptions import SyncError
        from mysql_to_sheets.core.sync_legacy import setup_logging

        start_time = time.time()

        # Generate sync ID if not provided
        if sync_id is None:
            sync_id = f"sync_{secrets.token_hex(8)}"

        # Load config if not provided
        if config is None:
            config = get_config()

        # Setup logging if not provided
        if logger is None:
            logger = setup_logging(config)

        # Use config defaults if not overridden
        sync_mode = mode or config.sync_mode
        sync_chunk_size = chunk_size or config.sync_chunk_size

        # Use config defaults for atomic streaming settings
        if atomic is True:
            atomic = getattr(config, "streaming_atomic_enabled", True)
        if preserve_gid is False:
            preserve_gid = getattr(config, "streaming_preserve_gid", False)

        db_type = config.db_type.lower()
        logger.info(f"Starting {db_type.upper()} to Google Sheets sync (mode={sync_mode})")

        # Create sync context
        ctx = SyncContext(
            config=config,
            logger=logger,
            sync_id=sync_id,
            dry_run=dry_run,
            preview=preview,
            mode=sync_mode,
            chunk_size=sync_chunk_size,
            notify=notify,
            source=source,
            organization_id=organization_id,
            config_name=config_name,
            config_id=config_id,
            incremental_config=incremental_config,
            column_mapping_config=column_mapping_config,
            pii_config=pii_config,
            pii_acknowledged=pii_acknowledged,
            detect_pii=detect_pii,
            schema_policy=schema_policy,
            expected_headers=expected_headers,
            skip_snapshot=skip_snapshot,
            create_worksheet=create_worksheet,
            atomic=atomic,
            preserve_gid=preserve_gid,
            resumable=resumable,
            job_id=job_id,
            start_time=start_time,
        )

        result: SyncResult | None = None
        error: Exception | None = None

        try:
            # Call hook.on_start() for all hooks
            self._call_hooks_on_start(ctx)

            # Execute pipeline steps
            result = self._execute_steps(ctx)
            return result

        except SyncError as e:
            error = e
            result = SyncResult(
                success=False,
                rows_synced=0,
                message=str(e),
                error=str(e),
            )
            raise

        except (OSError, ValueError, TypeError, RuntimeError, KeyError) as e:
            error = e
            result = SyncResult(
                success=False,
                rows_synced=0,
                message=str(e),
                error=str(e),
            )
            raise SyncError(
                message=f"Unexpected error during sync: {e}",
                details={"original_exception": type(e).__name__},
            ) from e

        finally:
            # Call hooks based on result
            if error is not None:
                self._call_hooks_on_failure(ctx, error)
            elif result is not None and result.success:
                self._call_hooks_on_success(ctx, result)

            # Always call on_complete
            self._call_hooks_on_complete(ctx, result)

    def _execute_steps(self, ctx: SyncContext) -> SyncResult:
        """Execute pipeline steps in order.

        Args:
            ctx: Sync context.

        Returns:
            SyncResult from the pipeline execution.
        """
        step_data: dict[str, Any] = {}

        for step in self.pipeline.steps:
            # Check if step should run
            if not step.should_run(ctx):
                ctx.logger.debug(f"[orchestrator] Skipping step: {step.name}")
                continue

            ctx.logger.debug(f"[orchestrator] Executing step: {step.name}")

            # Execute step
            result = step.execute(ctx)

            # Collect step data
            if result.data:
                step_data.update(result.data)

            # Check for short-circuit
            if result.short_circuit:
                ctx.logger.debug(f"[orchestrator] Short-circuit at step: {step.name}")
                return self._build_result_from_step(ctx, result, step_data)

            # Check for failure
            if not result.success:
                ctx.logger.warning(f"[orchestrator] Step failed: {step.name}")
                return SyncResult(
                    success=False,
                    message=result.message,
                    error=result.message,
                )

        # All steps completed successfully
        return self._build_final_result(ctx, step_data)

    def _build_result_from_step(
        self, ctx: SyncContext, step_result: Any, step_data: dict[str, Any]
    ) -> SyncResult:
        """Build SyncResult from a short-circuited step result.

        Args:
            ctx: Sync context.
            step_result: StepResult from the short-circuiting step.
            step_data: Accumulated data from all steps.

        Returns:
            SyncResult for the sync operation.
        """
        data = step_data

        # Handle streaming results
        if data.get("streaming"):
            return SyncResult(
                success=data.get("success", True),
                rows_synced=data.get("total_rows", 0),
                columns=0,
                headers=[],
                message=step_result.message,
                error=None if data.get("success", True) else f"{data.get('failed_chunks', 0)} chunks failed",
            )

        # Handle preview results
        if data.get("preview"):
            from mysql_to_sheets.core.diff import DiffResult
            diff_data = data.get("diff")
            diff = DiffResult.from_dict(diff_data) if diff_data else None
            return SyncResult(
                success=True,
                rows_synced=data.get("row_count", len(ctx.cleaned_rows)),
                columns=data.get("column_count", len(ctx.headers)),
                headers=ctx.headers,
                message=step_result.message,
                preview=True,
                diff=diff,
            )

        # Handle dry-run results
        if data.get("dry_run"):
            return SyncResult(
                success=True,
                rows_synced=data.get("row_count", len(ctx.cleaned_rows)),
                columns=data.get("column_count", len(ctx.headers)),
                headers=ctx.headers,
                message=step_result.message,
            )

        # Handle empty result handler
        # EC-53: Include warnings and empty_result_skipped in result
        if data.get("action") in ("clear", "skip"):
            return SyncResult(
                success=True,
                rows_synced=0,
                columns=len(ctx.headers),
                headers=ctx.headers,
                message="Sync completed (empty dataset)",
                warnings=data.get("warnings", []),
                empty_result_skipped=data.get("empty_result_skipped", False),
            )

        # Default result
        return SyncResult(
            success=True,
            rows_synced=len(ctx.cleaned_rows),
            columns=len(ctx.headers),
            headers=ctx.headers,
            message=step_result.message,
            schema_changes=ctx.schema_changes,
        )

    def _build_final_result(
        self, ctx: SyncContext, step_data: dict[str, Any]
    ) -> SyncResult:
        """Build final SyncResult after all steps complete.

        Args:
            ctx: Sync context.
            step_data: Accumulated data from all steps.

        Returns:
            SyncResult for successful sync.
        """
        rows_synced = step_data.get("rows_synced", len(ctx.cleaned_rows))
        columns = step_data.get("columns", len(ctx.headers))

        ctx.logger.info(
            f"Sync completed successfully: {rows_synced} rows pushed (mode={ctx.mode})"
        )

        # EC-53 & EC-56: Collect warnings from step_data and ctx.step_warnings
        warnings = list(step_data.get("warnings", []))
        warnings.extend(ctx.step_warnings)

        return SyncResult(
            success=True,
            rows_synced=rows_synced,
            columns=columns,
            headers=ctx.headers,
            message=f"Successfully synced {rows_synced} rows",
            schema_changes=ctx.schema_changes,
            warnings=warnings,
        )

    def _call_hooks_on_start(self, ctx: SyncContext) -> None:
        """Call on_start for all hooks.

        Args:
            ctx: Sync context.
        """
        for hook in self.pipeline.hooks:
            if hook.should_run(ctx):
                try:
                    hook.on_start(ctx)
                except Exception as e:
                    ctx.logger.debug(f"[{hook.name}] on_start failed: {e}")

    def _call_hooks_on_success(self, ctx: SyncContext, result: SyncResult) -> None:
        """Call on_success for all hooks.

        Args:
            ctx: Sync context.
            result: SyncResult from successful sync.
        """
        for hook in self.pipeline.hooks:
            if hook.should_run(ctx):
                try:
                    hook.on_success(ctx, result)
                except Exception as e:
                    ctx.logger.debug(f"[{hook.name}] on_success failed: {e}")

    def _call_hooks_on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Call on_failure for all hooks.

        Args:
            ctx: Sync context.
            error: Exception that caused failure.
        """
        for hook in self.pipeline.hooks:
            if hook.should_run(ctx):
                try:
                    hook.on_failure(ctx, error)
                except Exception as e:
                    ctx.logger.debug(f"[{hook.name}] on_failure failed: {e}")

    def _call_hooks_on_complete(
        self, ctx: SyncContext, result: SyncResult | None
    ) -> None:
        """Call on_complete for all hooks.

        Args:
            ctx: Sync context.
            result: SyncResult if available.
        """
        for hook in self.pipeline.hooks:
            if hook.should_run(ctx):
                try:
                    hook.on_complete(ctx, result)
                except Exception as e:
                    ctx.logger.debug(f"[{hook.name}] on_complete failed: {e}")


# Global orchestrator instance for convenience
_default_orchestrator: SyncOrchestrator | None = None


def get_orchestrator() -> SyncOrchestrator:
    """Get the default sync orchestrator.

    Returns:
        Default SyncOrchestrator instance.
    """
    global _default_orchestrator
    if _default_orchestrator is None:
        _default_orchestrator = SyncOrchestrator()
    return _default_orchestrator


def reset_orchestrator() -> None:
    """Reset the default orchestrator.

    Use this for testing or to refresh the pipeline configuration.
    """
    global _default_orchestrator
    _default_orchestrator = None
