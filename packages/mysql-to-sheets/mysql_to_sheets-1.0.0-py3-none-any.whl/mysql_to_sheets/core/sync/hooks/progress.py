"""Progress hook for emitting real-time sync progress events.

This hook integrates the sync pipeline with the progress emitter
to provide real-time updates to connected clients.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from mysql_to_sheets.core.sync.protocols import SyncHook

if TYPE_CHECKING:
    from mysql_to_sheets.core.sync.dataclasses import SyncResult
    from mysql_to_sheets.core.sync.protocols import SyncContext


class ProgressHook(SyncHook):
    """Pipeline hook for emitting progress events.

    This hook:
    - Emits phase transitions (connecting → fetching → cleaning → pushing)
    - Emits log entries during sync
    - Emits completion event with final statistics
    """

    name = "progress"

    def __init__(self) -> None:
        """Initialize the progress hook."""
        self._logger = logging.getLogger(__name__)

    def should_run(self, ctx: "SyncContext") -> bool:
        """Always run for desktop and web syncs.

        Args:
            ctx: Sync context.

        Returns:
            True to emit progress events.
        """
        # Progress is useful for all sync sources
        return True

    def on_start(self, ctx: "SyncContext") -> None:
        """Emit start event when sync begins.

        Args:
            ctx: Sync context with sync_id.
        """
        try:
            from mysql_to_sheets.desktop.progress_emitter import (
                SyncPhase,
                get_progress_emitter,
            )

            emitter = get_progress_emitter()
            emitter.emit_progress(
                sync_id=ctx.sync_id,
                phase=SyncPhase.CONNECTING,
                percent=5,
                message="Starting sync operation...",
            )
            emitter.emit_log(ctx.sync_id, "info", f"Sync started: {ctx.sync_id}")

        except Exception as e:
            self._logger.debug(f"[progress] on_start error: {e}")

    def on_success(self, ctx: "SyncContext", result: "SyncResult") -> None:
        """Emit success completion event.

        Args:
            ctx: Sync context.
            result: Sync result with statistics.
        """
        try:
            import time

            from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

            emitter = get_progress_emitter()
            duration = time.time() - ctx.start_time if ctx.start_time else 0.0

            emitter.emit_complete(
                sync_id=ctx.sync_id,
                success=True,
                rows_synced=result.rows_synced,
                duration_seconds=duration,
            )
            emitter.emit_log(
                ctx.sync_id,
                "info",
                f"Sync completed: {result.rows_synced} rows in {duration:.1f}s",
            )

        except Exception as e:
            self._logger.debug(f"[progress] on_success error: {e}")

    def on_failure(self, ctx: "SyncContext", error: Exception) -> None:
        """Emit failure completion event.

        Args:
            ctx: Sync context.
            error: The exception that caused failure.
        """
        try:
            import time

            from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

            emitter = get_progress_emitter()
            duration = time.time() - ctx.start_time if ctx.start_time else 0.0

            error_code = None
            if hasattr(error, "code"):
                error_code = error.code

            emitter.emit_complete(
                sync_id=ctx.sync_id,
                success=False,
                rows_synced=0,
                duration_seconds=duration,
                error_message=str(error),
                error_code=error_code,
            )
            emitter.emit_log(
                ctx.sync_id,
                "error",
                f"Sync failed: {error}",
            )

        except Exception as e:
            self._logger.debug(f"[progress] on_failure error: {e}")

    def on_complete(self, ctx: "SyncContext", result: "SyncResult | None") -> None:
        """Clean up progress state after sync completes.

        Args:
            ctx: Sync context.
            result: Sync result if available.
        """
        # Cleanup is handled by on_success/on_failure
        pass


def emit_phase_progress(
    ctx: "SyncContext",
    phase: str,
    percent: int,
    message: str,
    rows_fetched: int = 0,
    rows_pushed: int = 0,
    total_rows: int = 0,
    chunk_current: int = 0,
    chunk_total: int = 0,
) -> None:
    """Utility function to emit progress from within pipeline steps.

    This can be called from any pipeline step to emit progress updates.

    Args:
        ctx: Sync context with sync_id.
        phase: Phase name ("connecting", "fetching", "cleaning", "pushing").
        percent: Progress percentage (0-100).
        message: Human-readable status message.
        rows_fetched: Rows fetched from database.
        rows_pushed: Rows pushed to sheets.
        total_rows: Total rows to process.
        chunk_current: Current chunk (streaming mode).
        chunk_total: Total chunks (streaming mode).
    """
    try:
        from mysql_to_sheets.desktop.progress_emitter import (
            SyncPhase,
            get_progress_emitter,
        )

        phase_map = {
            "connecting": SyncPhase.CONNECTING,
            "fetching": SyncPhase.FETCHING,
            "cleaning": SyncPhase.CLEANING,
            "pushing": SyncPhase.PUSHING,
            "complete": SyncPhase.COMPLETE,
            "failed": SyncPhase.FAILED,
        }

        emitter = get_progress_emitter()
        emitter.emit_progress(
            sync_id=ctx.sync_id,
            phase=phase_map.get(phase, SyncPhase.CONNECTING),
            percent=percent,
            message=message,
            rows_fetched=rows_fetched,
            rows_pushed=rows_pushed,
            total_rows=total_rows,
            chunk_current=chunk_current,
            chunk_total=chunk_total,
        )

    except Exception:
        pass  # Don't let progress errors affect sync


def emit_progress_log(ctx: "SyncContext", level: str, message: str) -> None:
    """Utility function to emit a log entry.

    Args:
        ctx: Sync context with sync_id.
        level: Log level ("info", "warning", "error", "debug").
        message: Log message.
    """
    try:
        from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

        emitter = get_progress_emitter()
        emitter.emit_log(ctx.sync_id, level, message)

    except Exception:
        pass  # Don't let log errors affect sync


def record_chunk_complete(ctx: "SyncContext") -> None:
    """Record chunk completion for ETA calculation.

    Call this after each chunk is processed in streaming mode.

    Args:
        ctx: Sync context with sync_id.
    """
    try:
        from mysql_to_sheets.desktop.progress_emitter import get_progress_emitter

        emitter = get_progress_emitter()
        emitter.record_chunk_time(ctx.sync_id)

    except Exception:
        pass
