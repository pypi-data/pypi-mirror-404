"""Sync pipeline hooks for side effects.

Each hook module provides a SyncHook implementation for handling side effects
during the sync lifecycle. Hooks are called at specific points:
- on_start: When sync begins
- on_success: When sync completes successfully
- on_failure: When sync fails with an error
- on_complete: Always called after success/failure (for cleanup)

Hooks should be resilient - failures are logged but don't abort the sync.

Hooks available:
- ProgressHook: Emit real-time progress events via SSE
- AuditHook: Log audit events for sync operations
- NotificationHook: Send email/Slack/webhook notifications
- WebhookHook: Deliver webhooks for sync events
- SnapshotHook: Create pre-sync snapshots for rollback
- FreshnessHook: Update freshness/SLA tracking
- UsageHook: Record usage metrics for billing
"""

from mysql_to_sheets.core.sync.hooks.audit import AuditHook
from mysql_to_sheets.core.sync.hooks.base import BaseSyncHook
from mysql_to_sheets.core.sync.hooks.freshness import FreshnessHook
from mysql_to_sheets.core.sync.hooks.notification import NotificationHook
from mysql_to_sheets.core.sync.hooks.progress import ProgressHook
from mysql_to_sheets.core.sync.hooks.snapshot import SnapshotHook
from mysql_to_sheets.core.sync.hooks.usage import UsageHook
from mysql_to_sheets.core.sync.hooks.webhook import WebhookHook

__all__ = [
    "BaseSyncHook",
    "ProgressHook",
    "AuditHook",
    "NotificationHook",
    "WebhookHook",
    "SnapshotHook",
    "FreshnessHook",
    "UsageHook",
]
