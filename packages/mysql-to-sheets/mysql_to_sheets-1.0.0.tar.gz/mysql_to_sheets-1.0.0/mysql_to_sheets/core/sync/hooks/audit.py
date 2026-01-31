"""Audit logging hook for sync pipeline.

This module provides the AuditHook that logs audit events for
sync operations (started, completed, failed).
"""

import time
from typing import Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext


class AuditHook(BaseSyncHook):
    """Log audit events for sync operations.

    This hook records sync events to the audit log:
    - sync.started: When sync begins
    - sync.completed: When sync succeeds
    - sync.failed: When sync fails

    Events are only logged when organization_id is provided.
    """

    @property
    def name(self) -> str:
        return "audit"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if organization_id is provided and not dry-run/preview."""
        return (
            ctx.organization_id is not None
            and not ctx.dry_run
            and not ctx.preview
        )

    def on_start(self, ctx: SyncContext) -> None:
        """Log sync.started audit event.

        Args:
            ctx: Current sync context.
        """
        self._log_event(
            event="started",
            ctx=ctx,
        )

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Log sync.completed audit event.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        duration_seconds = time.time() - ctx.start_time if ctx.start_time else 0.0
        rows_synced = getattr(result, "rows_synced", 0)

        self._log_event(
            event="completed",
            ctx=ctx,
            rows_synced=rows_synced,
            duration_seconds=duration_seconds,
        )

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Log sync.failed audit event.

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        duration_seconds = time.time() - ctx.start_time if ctx.start_time else 0.0

        self._log_event(
            event="failed",
            ctx=ctx,
            error=str(error),
            duration_seconds=duration_seconds,
        )

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """No additional action on complete.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        pass  # Audit logging is handled in on_success/on_failure

    def _log_event(
        self,
        event: str,
        ctx: SyncContext,
        rows_synced: int | None = None,
        error: str | None = None,
        duration_seconds: float = 0.0,
    ) -> None:
        """Log an audit event.

        Args:
            event: Event type (started, completed, failed).
            ctx: Current sync context.
            rows_synced: Number of rows synced (for completed).
            error: Error message (for failed).
            duration_seconds: Operation duration.
        """
        try:
            from mysql_to_sheets.core.audit import log_sync_event

            log_sync_event(
                event=event,
                organization_id=ctx.organization_id,
                db_path=ctx.config.tenant_db_path,
                sync_id=ctx.sync_id,
                config_name=ctx.config_name,
                rows_synced=rows_synced,
                query=ctx.config.sql_query,
                error=error,
                duration_seconds=duration_seconds,
                source=ctx.source,
            )
            self.log_debug(ctx, f"Audit event logged: {event}")
        except (OSError, RuntimeError, ImportError) as e:
            self.log_debug(ctx, f"Audit logging skipped: {e}")
