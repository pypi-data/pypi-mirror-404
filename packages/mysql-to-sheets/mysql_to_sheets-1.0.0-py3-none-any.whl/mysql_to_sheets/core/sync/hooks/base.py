"""Base class for sync lifecycle hooks.

This module provides the BaseSyncHook abstract base class that all
lifecycle hooks should inherit from.
"""

from abc import ABC, abstractmethod
from typing import Any

from mysql_to_sheets.core.sync.protocols import SyncContext


class BaseSyncHook(ABC):
    """Abstract base class for sync lifecycle hooks.

    Hooks are called at specific points in the sync lifecycle:
    - on_start: When sync operation begins
    - on_success: When sync completes successfully
    - on_failure: When sync fails with an error
    - on_complete: Always called after success/failure (cleanup)

    Hooks should be resilient - failures are logged but should not
    abort the sync operation.

    Example:
        class AuditHook(BaseSyncHook):
            @property
            def name(self) -> str:
                return "audit"

            def on_start(self, ctx: SyncContext) -> None:
                log_audit_event("sync.started", ...)

            def on_success(self, ctx: SyncContext, result: Any) -> None:
                log_audit_event("sync.completed", ...)

            def on_failure(self, ctx: SyncContext, error: Exception) -> None:
                log_audit_event("sync.failed", ...)

            def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
                pass  # No cleanup needed
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifying this hook."""
        ...

    def should_run(self, ctx: SyncContext) -> bool:
        """Determine if this hook should execute.

        Override this to conditionally enable/disable hooks.

        Args:
            ctx: Current sync context.

        Returns:
            True if the hook should execute, False to skip.
        """
        return True

    @abstractmethod
    def on_start(self, ctx: SyncContext) -> None:
        """Called when sync operation starts.

        Args:
            ctx: Current sync context.
        """
        ...

    @abstractmethod
    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Called when sync completes successfully.

        Args:
            ctx: Current sync context.
            result: SyncResult from the sync operation.
        """
        ...

    @abstractmethod
    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Called when sync fails with an error.

        Args:
            ctx: Current sync context.
            error: The exception that caused the failure.
        """
        ...

    @abstractmethod
    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """Called when sync completes (success or failure).

        This is always called after on_success or on_failure, useful
        for cleanup or unconditional logging.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        ...

    def log_debug(self, ctx: SyncContext, message: str) -> None:
        """Log a debug message with hook name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.debug(f"[{self.name}] {message}")

    def log_info(self, ctx: SyncContext, message: str) -> None:
        """Log an info message with hook name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.info(f"[{self.name}] {message}")

    def log_warning(self, ctx: SyncContext, message: str) -> None:
        """Log a warning message with hook name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.warning(f"[{self.name}] {message}")

    def log_error(self, ctx: SyncContext, message: str) -> None:
        """Log an error message with hook name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.error(f"[{self.name}] {message}")
