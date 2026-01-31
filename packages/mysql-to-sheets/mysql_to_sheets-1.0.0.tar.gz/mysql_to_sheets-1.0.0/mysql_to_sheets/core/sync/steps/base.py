"""Base class for sync pipeline steps.

This module provides the BaseSyncStep abstract base class that all pipeline
steps should inherit from. It provides common functionality like logging
and consistent error handling.
"""

from abc import ABC, abstractmethod
from typing import Any

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext


class BaseSyncStep(ABC):
    """Abstract base class for sync pipeline steps.

    Provides common functionality for all steps including:
    - Name property for identification
    - Logging helpers
    - Consistent error handling

    Subclasses must implement:
    - name property
    - should_run() method
    - execute() method

    Example:
        class DataFetchStep(BaseSyncStep):
            @property
            def name(self) -> str:
                return "fetch_data"

            def should_run(self, ctx: SyncContext) -> bool:
                return True

            def execute(self, ctx: SyncContext) -> StepResult:
                # Implementation here
                return StepResult(success=True)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifying this step."""
        ...

    @abstractmethod
    def should_run(self, ctx: SyncContext) -> bool:
        """Determine if this step should execute.

        Args:
            ctx: Current sync context.

        Returns:
            True if the step should execute, False to skip.
        """
        ...

    @abstractmethod
    def execute(self, ctx: SyncContext) -> StepResult:
        """Execute the step.

        Args:
            ctx: Sync context to read from and modify.

        Returns:
            StepResult indicating success/failure and any short-circuit.

        Raises:
            SyncError: If the step fails in a way that should abort the sync.
        """
        ...

    def log_debug(self, ctx: SyncContext, message: str) -> None:
        """Log a debug message with step name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.debug(f"[{self.name}] {message}")

    def log_info(self, ctx: SyncContext, message: str) -> None:
        """Log an info message with step name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.info(f"[{self.name}] {message}")

    def log_warning(self, ctx: SyncContext, message: str) -> None:
        """Log a warning message with step name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.warning(f"[{self.name}] {message}")

    def log_error(self, ctx: SyncContext, message: str) -> None:
        """Log an error message with step name prefix.

        Args:
            ctx: Current sync context.
            message: Message to log.
        """
        ctx.logger.error(f"[{self.name}] {message}")

    def success(
        self,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a successful step result.

        Args:
            message: Optional success message.
            data: Optional data to include in result.

        Returns:
            StepResult with success=True.
        """
        return StepResult(
            success=True,
            message=message,
            data=data or {},
        )

    def failure(
        self,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a failed step result.

        Args:
            message: Failure message.
            data: Optional data to include in result.

        Returns:
            StepResult with success=False.
        """
        return StepResult(
            success=False,
            message=message,
            data=data or {},
        )

    def short_circuit(
        self,
        message: str = "",
        data: dict[str, Any] | None = None,
    ) -> StepResult:
        """Create a result that short-circuits the pipeline.

        Use this when the step completes early (e.g., preview mode)
        and remaining steps should be skipped.

        Args:
            message: Optional message explaining short-circuit.
            data: Optional data to include in result.

        Returns:
            StepResult with short_circuit=True.
        """
        return StepResult(
            success=True,
            message=message,
            short_circuit=True,
            data=data or {},
        )
