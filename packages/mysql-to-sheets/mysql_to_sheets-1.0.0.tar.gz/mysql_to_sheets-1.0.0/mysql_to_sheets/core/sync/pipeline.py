"""Pipeline builder and step registry for sync operations.

This module provides the SyncPipeline class that manages the collection
of steps and hooks that execute during a sync operation.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mysql_to_sheets.core.sync.protocols import SyncHook, SyncStep


class SyncPipeline:
    """Pipeline builder and registry for sync steps and hooks.

    The pipeline maintains ordered lists of steps and hooks that are
    executed during sync operations. Steps can be added, removed, or
    reordered without modifying the orchestrator.

    Example:
        pipeline = SyncPipeline()
        pipeline.add_step(ConfigValidationStep())
        pipeline.add_step(DataFetchStep())
        pipeline.add_hook(AuditHook())

        # Insert a custom step after fetch
        pipeline.add_step(MyCustomStep(), after="fetch_data")
    """

    def __init__(self) -> None:
        """Initialize empty pipeline."""
        self._steps: list[SyncStep] = []
        self._hooks: list[SyncHook] = []

    @property
    def steps(self) -> list["SyncStep"]:
        """Get ordered list of pipeline steps."""
        return self._steps.copy()

    @property
    def hooks(self) -> list["SyncHook"]:
        """Get list of lifecycle hooks."""
        return self._hooks.copy()

    def add_step(
        self,
        step: "SyncStep",
        before: str | None = None,
        after: str | None = None,
    ) -> "SyncPipeline":
        """Add a step to the pipeline.

        Args:
            step: The step to add.
            before: Optional step name to insert before.
            after: Optional step name to insert after.

        Returns:
            Self for chaining.

        Raises:
            ValueError: If before/after step not found.
        """
        if before is not None:
            idx = self._find_step_index(before)
            self._steps.insert(idx, step)
        elif after is not None:
            idx = self._find_step_index(after)
            self._steps.insert(idx + 1, step)
        else:
            self._steps.append(step)
        return self

    def remove_step(self, name: str) -> "SyncPipeline":
        """Remove a step by name.

        Args:
            name: Name of the step to remove.

        Returns:
            Self for chaining.
        """
        self._steps = [s for s in self._steps if s.name != name]
        return self

    def add_hook(self, hook: "SyncHook") -> "SyncPipeline":
        """Add a lifecycle hook.

        Args:
            hook: The hook to add.

        Returns:
            Self for chaining.
        """
        self._hooks.append(hook)
        return self

    def remove_hook(self, name: str) -> "SyncPipeline":
        """Remove a hook by name.

        Args:
            name: Name of the hook to remove.

        Returns:
            Self for chaining.
        """
        self._hooks = [h for h in self._hooks if h.name != name]
        return self

    def _find_step_index(self, name: str) -> int:
        """Find index of step by name.

        Args:
            name: Step name to find.

        Returns:
            Index of the step.

        Raises:
            ValueError: If step not found.
        """
        for i, step in enumerate(self._steps):
            if step.name == name:
                return i
        raise ValueError(f"Step '{name}' not found in pipeline")


def create_default_pipeline() -> SyncPipeline:
    """Create the default sync pipeline with all standard steps and hooks.

    Returns:
        Configured SyncPipeline ready for execution.
    """
    from mysql_to_sheets.core.sync.hooks import (
        AuditHook,
        FreshnessHook,
        NotificationHook,
        ProgressHook,
        SnapshotHook,
        UsageHook,
        WebhookHook,
    )
    from mysql_to_sheets.core.sync.steps import (
        BatchSizeValidationStep,
        ColumnMappingStep,
        ConfigValidationStep,
        DataCleanStep,
        DataFetchStep,
        DryRunStep,
        EmptyResultHandlerStep,
        PIIDetectionStep,
        PIITransformStep,
        PreviewStep,
        SchemaCheckStep,
        SheetsPushStep,
        StreamingPushStep,
    )

    pipeline = SyncPipeline()

    # Add steps in order
    # 1. Validation
    pipeline.add_step(ConfigValidationStep())

    # 2. Streaming mode shortcut (handles its own flow)
    pipeline.add_step(StreamingPushStep())

    # 3. Data fetching
    pipeline.add_step(DataFetchStep())
    pipeline.add_step(EmptyResultHandlerStep())

    # 4. Data transformation
    pipeline.add_step(DataCleanStep())
    pipeline.add_step(PIIDetectionStep())
    pipeline.add_step(PIITransformStep())
    pipeline.add_step(ColumnMappingStep())
    pipeline.add_step(SchemaCheckStep())

    # 5. Validation of transformed data
    pipeline.add_step(BatchSizeValidationStep())

    # 6. Output modes
    pipeline.add_step(PreviewStep())  # Short-circuits if preview mode
    pipeline.add_step(DryRunStep())   # Short-circuits if dry-run mode
    pipeline.add_step(SheetsPushStep())

    # Add hooks
    pipeline.add_hook(ProgressHook())     # Emit real-time progress events
    pipeline.add_hook(SnapshotHook())     # Create pre-sync snapshot
    pipeline.add_hook(AuditHook())        # Log audit events
    pipeline.add_hook(WebhookHook())      # Deliver webhooks
    pipeline.add_hook(NotificationHook()) # Send notifications
    pipeline.add_hook(FreshnessHook())    # Update freshness tracking
    pipeline.add_hook(UsageHook())        # Record usage for billing

    return pipeline
