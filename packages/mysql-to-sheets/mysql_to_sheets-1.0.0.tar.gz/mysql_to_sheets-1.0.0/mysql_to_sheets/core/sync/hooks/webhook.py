"""Webhook delivery hook for sync pipeline.

This module provides the WebhookHook that delivers webhook events
for sync operations to registered subscribers.
"""

import time
from typing import Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext


class WebhookHook(BaseSyncHook):
    """Deliver webhooks for sync events.

    This hook delivers webhook events to registered subscribers:
    - sync.started: When sync begins
    - sync.completed: When sync succeeds
    - sync.failed: When sync fails

    Webhooks are signed with HMAC-SHA256 and delivered asynchronously.
    """

    @property
    def name(self) -> str:
        return "webhook"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if organization_id is provided and not dry-run/preview."""
        return (
            ctx.organization_id is not None
            and not ctx.dry_run
            and not ctx.preview
        )

    def on_start(self, ctx: SyncContext) -> None:
        """Deliver sync.started webhook.

        Args:
            ctx: Current sync context.
        """
        self._trigger_webhook(
            event="sync.started",
            ctx=ctx,
        )

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Deliver sync.completed webhook.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        duration_seconds = time.time() - ctx.start_time if ctx.start_time else 0.0

        self._trigger_webhook(
            event="sync.completed",
            ctx=ctx,
            result=result,
            duration_seconds=duration_seconds,
        )

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Deliver sync.failed webhook.

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        duration_seconds = time.time() - ctx.start_time if ctx.start_time else 0.0
        error_type = type(error).__name__
        error_message = str(error)

        self._trigger_webhook(
            event="sync.failed",
            ctx=ctx,
            duration_seconds=duration_seconds,
            error_type=error_type,
            error_message=error_message,
        )

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """No additional action on complete.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        pass  # Webhook delivery handled in on_success/on_failure

    def _trigger_webhook(
        self,
        event: str,
        ctx: SyncContext,
        result: Any | None = None,
        duration_seconds: float = 0.0,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Trigger webhook delivery.

        Args:
            event: Webhook event type.
            ctx: Current sync context.
            result: Optional sync result.
            duration_seconds: Operation duration.
            error_type: Type of error (for failed events).
            error_message: Error message (for failed events).
        """
        try:
            from mysql_to_sheets.core.webhooks.delivery import get_webhook_delivery_service
            from mysql_to_sheets.core.webhooks.payload import create_sync_payload

            rows_synced = getattr(result, "rows_synced", 0) if result else 0
            sheet_url = (
                f"https://docs.google.com/spreadsheets/d/{ctx.config.google_sheet_id}"
                if ctx.config.google_sheet_id
                else None
            )

            payload = create_sync_payload(
                event=event,
                sync_id=ctx.sync_id,
                config_name=ctx.config_name,
                rows_synced=rows_synced,
                duration_seconds=duration_seconds,
                sheet_id=ctx.config.google_sheet_id,
                sheet_url=sheet_url,
                triggered_by=ctx.source,
                error_type=error_type,
                error_message=error_message,
            )

            delivery_service = get_webhook_delivery_service(ctx.config.tenant_db_path)
            results = delivery_service.deliver_to_all(
                event, ctx.organization_id, payload
            )

            if results:
                successful = sum(1 for r in results if r.success)
                failed = len(results) - successful
                if successful > 0:
                    self.log_debug(ctx, f"Webhook '{event}' delivered to {successful} subscriptions")
                if failed > 0:
                    self.log_warning(ctx, f"Webhook '{event}' failed for {failed} subscriptions")

        except (OSError, RuntimeError, ImportError) as e:
            self.log_debug(ctx, f"Webhook delivery skipped: {e}")
