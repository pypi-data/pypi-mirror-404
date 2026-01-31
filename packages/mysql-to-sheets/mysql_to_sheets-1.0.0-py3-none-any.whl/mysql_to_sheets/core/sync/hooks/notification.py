"""Notification hook for sync pipeline.

This module provides the NotificationHook that sends notifications
via email, Slack, and webhooks based on sync results.
"""

import time
from typing import TYPE_CHECKING, Any

from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.protocols import SyncContext

if TYPE_CHECKING:
    from mysql_to_sheets.core.notifications.base import NotificationConfig


class NotificationHook(BaseSyncHook):
    """Send notifications for sync results.

    This hook sends notifications via configured backends:
    - Email (SMTP)
    - Slack webhooks
    - Generic webhooks

    Notifications are sent based on sync result and configuration:
    - NOTIFY_ON_SUCCESS: Send on successful syncs
    - NOTIFY_ON_FAILURE: Send on failed syncs
    """

    @property
    def name(self) -> str:
        return "notification"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if notify is not explicitly disabled."""
        return ctx.notify is not False

    def on_start(self, ctx: SyncContext) -> None:
        """No notification on start.

        Args:
            ctx: Current sync context.
        """
        pass  # Notifications only sent on completion

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Send success notification if configured.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
        """
        # Handled in on_complete
        pass

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Send failure notification if configured.

        Args:
            ctx: Current sync context.
            error: The exception that caused failure.
        """
        # Handled in on_complete
        pass

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """Send notification based on result.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        if result is None:
            return

        duration_ms = (time.time() - ctx.start_time) * 1000 if ctx.start_time else 0.0
        self._send_notification(ctx, result, duration_ms)

        # Also handle schema change notifications
        if ctx.schema_changes and ctx.schema_changes.get("should_notify"):
            self._send_schema_change_notification(ctx)

    def _get_notification_config(self, ctx: SyncContext) -> "NotificationConfig":
        """Build notification config from main config.

        Args:
            ctx: Current sync context.

        Returns:
            NotificationConfig with notification settings.
        """
        from mysql_to_sheets.core.notifications.base import NotificationConfig

        return NotificationConfig(
            notify_on_success=ctx.config.notify_on_success,
            notify_on_failure=ctx.config.notify_on_failure,
            smtp_host=ctx.config.smtp_host,
            smtp_port=ctx.config.smtp_port,
            smtp_user=ctx.config.smtp_user,
            smtp_password=ctx.config.smtp_password,
            smtp_from=ctx.config.smtp_from,
            smtp_to=ctx.config.smtp_to,
            smtp_use_tls=ctx.config.smtp_use_tls,
            slack_webhook_url=ctx.config.slack_webhook_url,
            notification_webhook_url=ctx.config.notification_webhook_url,
        )

    def _send_notification(
        self, ctx: SyncContext, result: Any, duration_ms: float
    ) -> None:
        """Send notification for sync result.

        Args:
            ctx: Current sync context.
            result: SyncResult from the operation.
            duration_ms: Sync duration in milliseconds.
        """
        try:
            from mysql_to_sheets.core.notifications import (
                NotificationPayload,
                get_notification_manager,
            )

            notification_config = self._get_notification_config(ctx)

            # Check if any notification is configured
            manager = get_notification_manager()
            configured_backends = manager.get_configured_backends(notification_config)
            if not configured_backends:
                self.log_debug(ctx, "No notification backends configured")
                return

            # Build notification payload
            payload = NotificationPayload(
                success=result.success,
                rows_synced=result.rows_synced,
                sheet_id=ctx.config.google_sheet_id,
                worksheet=ctx.config.google_worksheet_name,
                message=result.message,
                error=result.error,
                duration_ms=duration_ms,
                dry_run=ctx.dry_run,
                headers=result.headers,
                source=ctx.source,
            )

            # Send notification
            results = manager.send_notification(payload, notification_config)
            if results["sent"]:
                self.log_info(ctx, f"Notifications sent via: {', '.join(results['sent'])}")
            if results["failed"]:
                self.log_warning(ctx, f"Notification failures: {results['errors']}")

        except (OSError, RuntimeError, KeyError) as e:
            self.log_warning(ctx, f"Failed to send notifications: {e}")

    def _send_schema_change_notification(self, ctx: SyncContext) -> None:
        """Send notification for schema change.

        Args:
            ctx: Current sync context with schema_changes populated.
        """
        try:
            from mysql_to_sheets.core.notifications import (
                NotificationPayload,
                get_notification_manager,
            )

            notification_config = self._get_notification_config(ctx)

            manager = get_notification_manager()
            configured_backends = manager.get_configured_backends(notification_config)
            if not configured_backends:
                return

            # Build schema change message
            schema_change = ctx.schema_changes or {}
            policy = schema_change.get("policy_applied", "unknown")
            message_parts = [f"Schema change detected (policy: {policy})"]
            if schema_change.get("added_columns"):
                message_parts.append(f"Added columns: {schema_change['added_columns']}")
            if schema_change.get("removed_columns"):
                message_parts.append(f"Removed columns: {schema_change['removed_columns']}")
            if schema_change.get("reordered"):
                message_parts.append("Column order changed")

            payload = NotificationPayload(
                success=True,
                rows_synced=0,
                sheet_id=ctx.config.google_sheet_id,
                worksheet=ctx.config.google_worksheet_name,
                message=" | ".join(message_parts),
                error=None,
                duration_ms=0.0,
                dry_run=False,
                headers=[],
                source="schema_change",
                schema_change=schema_change,
            )

            results = manager.send_notification(payload, notification_config)
            if results["sent"]:
                self.log_info(ctx, f"Schema change notifications sent via: {', '.join(results['sent'])}")

        except (OSError, RuntimeError, KeyError) as e:
            self.log_warning(ctx, f"Failed to send schema change notification: {e}")
