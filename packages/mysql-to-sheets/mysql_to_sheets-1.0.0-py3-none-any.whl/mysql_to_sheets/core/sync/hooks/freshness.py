"""Freshness tracking hook for sync pipeline.

This module provides the FreshnessHook that updates SLA/freshness
tracking after sync operations.
"""

from typing import Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext


class FreshnessHook(BaseSyncHook):
    """Update freshness/SLA tracking after sync.

    This hook updates the freshness status of sync configurations
    to track SLA compliance and data staleness.

    Freshness is updated on_complete (for both success and failure)
    when config_id and organization_id are provided.
    """

    @property
    def name(self) -> str:
        return "freshness"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if config_id and organization_id are provided."""
        return (
            ctx.config_id is not None
            and ctx.organization_id is not None
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
        """No action on success (handled in on_complete).

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        pass

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """No action on failure (handled in on_complete).

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        pass

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """Update freshness tracking.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        if result is None:
            return

        self._update_freshness(ctx, result)

    def _update_freshness(self, ctx: SyncContext, result: Any) -> None:
        """Update freshness tracking for the sync config.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        try:
            from mysql_to_sheets.core.freshness import update_freshness

            success = getattr(result, "success", False)
            row_count = getattr(result, "rows_synced", 0) if success else None

            update_freshness(
                config_id=ctx.config_id,
                organization_id=ctx.organization_id,
                success=success,
                row_count=row_count,
                db_path=ctx.config.tenant_db_path,
            )
            self.log_debug(ctx, f"Freshness updated for config {ctx.config_id}")

        except (OSError, RuntimeError, ImportError) as e:
            self.log_debug(ctx, f"Freshness update failed: {e}")
