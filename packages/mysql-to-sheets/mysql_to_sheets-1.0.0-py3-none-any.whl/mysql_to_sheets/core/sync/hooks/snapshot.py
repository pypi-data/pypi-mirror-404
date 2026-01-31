"""Snapshot hook for sync pipeline.

This module provides the SnapshotHook that creates pre-sync snapshots
for rollback capability.
"""

from typing import Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext


class SnapshotHook(BaseSyncHook):
    """Create pre-sync snapshots for rollback.

    This hook creates a snapshot of the current sheet state before
    sync operations, enabling rollback if needed.

    Snapshots are created on_start and retained based on configuration:
    - snapshot_retention_count: Max number of snapshots
    - snapshot_retention_days: Max age of snapshots
    - snapshot_max_size_mb: Skip if sheet is too large
    """

    @property
    def name(self) -> str:
        return "snapshot"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if snapshots are enabled and conditions are met."""
        return (
            ctx.organization_id is not None
            and not ctx.dry_run
            and not ctx.preview
            and not ctx.skip_snapshot
            and getattr(ctx.config, "snapshot_enabled", False)
        )

    def on_start(self, ctx: SyncContext) -> None:
        """Create pre-sync snapshot.

        Args:
            ctx: Current sync context.
        """
        self._create_snapshot(ctx)

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """No action on success.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        pass

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """No action on failure.

        Snapshot was created on_start, available for rollback.

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        pass

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """No action on complete.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        pass

    def _create_snapshot(self, ctx: SyncContext) -> None:
        """Create a snapshot of the current sheet state.

        Args:
            ctx: Current sync context.
        """
        try:
            from mysql_to_sheets.core.snapshot_retention import (
                RetentionConfig,
                cleanup_old_snapshots,
                should_create_snapshot,
            )
            from mysql_to_sheets.core.snapshots import create_snapshot, estimate_sheet_size

            # Build retention config
            retention_config = RetentionConfig(
                retention_count=ctx.config.snapshot_retention_count,
                retention_days=ctx.config.snapshot_retention_days,
                max_size_mb=ctx.config.snapshot_max_size_mb,
            )

            # Check size limit before creating snapshot
            try:
                estimated_size = estimate_sheet_size(ctx.config, ctx.logger)
                should_create, reason = should_create_snapshot(
                    estimated_size, retention_config, ctx.logger
                )
                if not should_create:
                    self.log_info(ctx, f"Skipping snapshot: {reason}")
                    return
            except (OSError, ValueError) as size_error:
                # If we can't estimate size, try to create snapshot anyway
                self.log_debug(ctx, f"Could not estimate sheet size: {size_error}")

            # Create the snapshot
            snapshot = create_snapshot(
                config=ctx.config,
                organization_id=ctx.organization_id,
                db_path=ctx.config.tenant_db_path,
                sync_config_id=ctx.config_id,
                logger=ctx.logger,
            )
            self.log_info(ctx, f"Pre-sync snapshot created: ID {snapshot.id}")

            # Run cleanup to enforce retention limits
            cleanup_old_snapshots(
                organization_id=ctx.organization_id,
                db_path=ctx.config.tenant_db_path,
                retention_config=retention_config,
                logger=ctx.logger,
            )

        except (OSError, RuntimeError, ImportError) as e:
            self.log_warning(ctx, f"Failed to create pre-sync snapshot: {e}")
