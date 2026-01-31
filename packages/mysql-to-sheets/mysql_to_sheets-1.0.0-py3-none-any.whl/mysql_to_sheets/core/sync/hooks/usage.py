"""Usage tracking hook for sync pipeline.

This module provides the UsageHook that records usage metrics
for billing purposes.
"""

from typing import Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext


class UsageHook(BaseSyncHook):
    """Record usage metrics for billing.

    This hook records sync usage metrics:
    - rows_synced: Total rows synced
    - sync_operations: Number of sync operations
    - api_calls: API calls made

    Usage is recorded on_success for successful syncs.
    """

    @property
    def name(self) -> str:
        return "usage"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if organization_id is provided and not dry-run/preview."""
        return (
            ctx.organization_id is not None
            and not ctx.dry_run
            and not ctx.preview
        )

    def on_start(self, ctx: SyncContext) -> None:
        """No action on start.

        Args:
            ctx: Current sync context.
        """
        pass

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Record usage metrics for successful sync.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        self._record_usage(ctx, result)

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """No usage recorded for failed syncs.

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        pass  # Don't charge for failed syncs

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """No action on complete.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        pass

    def _record_usage(self, ctx: SyncContext, result: Any) -> None:
        """Record usage metrics for billing.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        try:
            from mysql_to_sheets.core.usage_tracking import record_sync_usage

            rows_synced = getattr(result, "rows_synced", 0)

            record_sync_usage(
                organization_id=ctx.organization_id,
                rows_synced=rows_synced,
                db_path=ctx.config.tenant_db_path,
            )
            self.log_debug(ctx, f"Usage recorded: {rows_synced} rows")

        except (OSError, RuntimeError, ImportError) as e:
            self.log_debug(ctx, f"Usage tracking failed: {e}")
