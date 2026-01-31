"""Sync pipeline protocols and interfaces.

This module defines the core protocols (interfaces) for the sync pipeline:
- SyncStep: Individual pipeline step that transforms or validates data
- SyncHook: Side-effect handler for audit, notifications, webhooks, etc.
- SyncContext: Shared state passed through the pipeline
- StepResult: Result from an individual step execution

Component dataclasses (for SyncContext refactoring):
- SyncOptions: Immutable execution options
- SyncMetadata: Immutable tracking/identification info
- SyncFeatureConfigs: Optional feature configurations
- SyncState: Mutable pipeline state (data, headers, etc.)

These protocols enable a composable pipeline architecture where steps
and hooks can be added, removed, or reordered without modifying the
core orchestration logic.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from mysql_to_sheets.core.column_mapping import ColumnMappingConfig
    from mysql_to_sheets.core.config import Config
    from mysql_to_sheets.core.incremental import IncrementalConfig
    from mysql_to_sheets.core.pii import PIITransformConfig


# =============================================================================
# Component Dataclasses for SyncContext Refactoring
# =============================================================================


@dataclass(frozen=True)
class SyncOptions:
    """Immutable execution options for a sync operation.

    These options control how the sync executes but don't change
    during the operation.

    Attributes:
        mode: Sync mode ('replace', 'append', 'streaming').
        chunk_size: Chunk size for streaming mode.
        dry_run: If True, validate without pushing to Sheets.
        preview: If True, show diff without pushing.
        atomic: Enable atomic staging for streaming mode.
        preserve_gid: Preserve worksheet GID during atomic swap.
        resumable: Enable checkpoint/resume for streaming.
        job_id: Job ID for checkpoint tracking.
        notify: Whether to send notifications.
        schema_policy: Schema evolution policy.
        expected_headers: Expected column headers from previous sync.
        detect_pii: Override PII detection setting.
        pii_acknowledged: Whether PII has been acknowledged.
        create_worksheet: If True, create worksheet if missing.
        skip_snapshot: If True, skip creating a pre-sync snapshot.
    """

    mode: str = "replace"
    chunk_size: int = 1000
    dry_run: bool = False
    preview: bool = False
    atomic: bool = True
    preserve_gid: bool = False
    resumable: bool = False
    job_id: int | None = None
    notify: bool | None = None
    schema_policy: str | None = None
    expected_headers: tuple[str, ...] | None = None  # tuple for hashability
    detect_pii: bool | None = None
    pii_acknowledged: bool = False
    create_worksheet: bool | None = None
    skip_snapshot: bool = False


@dataclass(frozen=True)
class SyncMetadata:
    """Immutable tracking/identification metadata for a sync operation.

    Used for logging, audit trails, and multi-tenant isolation.

    Attributes:
        sync_id: Unique identifier for this sync operation.
        organization_id: Optional organization ID for multi-tenant.
        config_name: Optional sync config name.
        config_id: Optional sync config ID for freshness tracking.
        source: Source of the sync (cli, api, web, scheduler).
        start_time: Start time of the sync operation (epoch seconds).
    """

    sync_id: str = ""
    organization_id: int | None = None
    config_name: str | None = None
    config_id: int | None = None
    source: str = "sync"
    start_time: float = 0.0

    @classmethod
    def generate(
        cls,
        *,
        organization_id: int | None = None,
        config_name: str | None = None,
        config_id: int | None = None,
        source: str = "sync",
    ) -> "SyncMetadata":
        """Generate metadata with auto-generated sync_id and start_time.

        Args:
            organization_id: Optional organization ID.
            config_name: Optional config name.
            config_id: Optional config ID.
            source: Source of the sync.

        Returns:
            SyncMetadata with generated sync_id and current start_time.
        """
        return cls(
            sync_id=str(uuid.uuid4()),
            organization_id=organization_id,
            config_name=config_name,
            config_id=config_id,
            source=source,
            start_time=time.time(),
        )


@dataclass
class SyncFeatureConfigs:
    """Optional feature configurations for a sync operation.

    These are complex configuration objects for optional features
    like incremental sync, column mapping, and PII handling.

    Attributes:
        incremental_config: Optional incremental sync configuration.
        column_mapping_config: Optional column mapping configuration.
        pii_config: Optional PII transform configuration.
    """

    incremental_config: IncrementalConfig | None = None
    column_mapping_config: ColumnMappingConfig | None = None
    pii_config: PIITransformConfig | None = None


@dataclass
class SyncState:
    """Mutable state that changes as data flows through the pipeline.

    Pipeline steps read and modify this state.

    Attributes:
        headers: Column headers from database query.
        rows: Data rows from database query.
        cleaned_rows: Rows after type conversion.
        schema_changes: Schema change information if detected.
        pii_detection_result: PII detection result if detection ran.
        step_warnings: Warnings collected from steps (EC-53, EC-56).
    """

    headers: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    cleaned_rows: list[list[Any]] = field(default_factory=list)
    schema_changes: dict[str, Any] | None = None
    pii_detection_result: Any = None
    step_warnings: list[str] = field(default_factory=list)

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the step warnings list.

        Args:
            warning: Warning message to add.
        """
        self.step_warnings.append(warning)

    def clear(self) -> None:
        """Clear all state (for reuse)."""
        self.headers = []
        self.rows = []
        self.cleaned_rows = []
        self.schema_changes = None
        self.pii_detection_result = None
        self.step_warnings = []


# =============================================================================
# Core Protocol Types
# =============================================================================


@dataclass
class StepResult:
    """Result from a pipeline step execution.

    Attributes:
        success: Whether the step completed successfully.
        message: Optional message describing the result.
        short_circuit: If True, skip remaining steps and return early.
            Used by preview mode and dry run to avoid pushing data.
        data: Optional data to pass to subsequent steps or include in result.
    """

    success: bool
    message: str = ""
    short_circuit: bool = False
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncContext:
    """Shared state passed through the sync pipeline.

    This context object carries all state needed by pipeline steps and hooks.
    Steps can read and modify this context as data flows through the pipeline.

    The context is composed of several component objects:
    - options: Immutable execution options (SyncOptions)
    - metadata: Immutable tracking info (SyncMetadata)
    - features: Optional feature configs (SyncFeatureConfigs)
    - state: Mutable pipeline state (SyncState)

    For backward compatibility, all fields from these components are also
    accessible as top-level attributes via property delegation. New code
    should prefer accessing via the component objects for clarity.

    Attributes:
        config: Main configuration object.
        logger: Logger instance for the sync operation.
        options: Immutable execution options.
        metadata: Immutable tracking/identification info.
        features: Optional feature configurations.
        state: Mutable pipeline state.

    Backward-compatible attributes (delegated to components):
        # From options
        mode, chunk_size, dry_run, preview, atomic, preserve_gid,
        resumable, job_id, notify, schema_policy, expected_headers,
        detect_pii, pii_acknowledged, create_worksheet, skip_snapshot

        # From metadata
        sync_id, organization_id, config_name, config_id, source, start_time

        # From features
        incremental_config, column_mapping_config, pii_config

        # From state
        headers, rows, cleaned_rows, schema_changes, pii_detection_result,
        step_warnings
    """

    # Required
    config: Config
    logger: logging.Logger

    # Component objects (new API)
    options: SyncOptions = field(default_factory=SyncOptions)
    metadata: SyncMetadata = field(default_factory=SyncMetadata)
    features: SyncFeatureConfigs = field(default_factory=SyncFeatureConfigs)
    state: SyncState = field(default_factory=SyncState)

    # ==========================================================================
    # Backward-compatible flat attributes
    # These are provided during transition period. New code should use
    # ctx.options.mode, ctx.state.headers, etc.
    # ==========================================================================

    # Sync parameters (backward compat - use options.* for new code)
    sync_id: str = ""
    dry_run: bool = False
    preview: bool = False
    mode: str = "replace"
    chunk_size: int = 1000
    notify: bool | None = None
    source: str = "sync"

    # Organization/tracking context (backward compat - use metadata.* for new code)
    organization_id: int | None = None
    config_name: str | None = None
    config_id: int | None = None

    # Feature configs (backward compat - use features.* for new code)
    incremental_config: IncrementalConfig | None = None
    column_mapping_config: ColumnMappingConfig | None = None
    pii_config: PIITransformConfig | None = None
    pii_acknowledged: bool = False
    detect_pii: bool | None = None

    # Schema evolution (backward compat - use options.* for new code)
    schema_policy: str | None = None
    expected_headers: list[str] | None = None

    # Worksheet options (backward compat - use options.* for new code)
    skip_snapshot: bool = False
    create_worksheet: bool | None = None

    # Atomic streaming options (backward compat - use options.* for new code)
    atomic: bool = True
    preserve_gid: bool = False
    resumable: bool = False
    job_id: int | None = None

    # Data (backward compat - use state.* for new code)
    headers: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    cleaned_rows: list[list[Any]] = field(default_factory=list)
    schema_changes: dict[str, Any] | None = None
    pii_detection_result: Any = None

    # EC-53 & EC-56: Warnings collected from steps (backward compat)
    step_warnings: list[str] = field(default_factory=list)

    # Timing (backward compat - use metadata.start_time for new code)
    start_time: float = 0.0

    def __post_init__(self) -> None:
        """Sync flat attributes with component objects after initialization."""
        # Sync options from flat attributes to options object if not default
        # This ensures backward compatibility when users set flat attributes
        if (
            self.mode != "replace"
            or self.chunk_size != 1000
            or self.dry_run
            or self.preview
            or not self.atomic
            or self.preserve_gid
            or self.resumable
            or self.job_id is not None
            or self.notify is not None
            or self.schema_policy is not None
            or self.expected_headers is not None
            or self.detect_pii is not None
            or self.pii_acknowledged
            or self.create_worksheet is not None
            or self.skip_snapshot
        ):
            expected_headers_tuple = (
                tuple(self.expected_headers) if self.expected_headers else None
            )
            object.__setattr__(
                self,
                "options",
                SyncOptions(
                    mode=self.mode,
                    chunk_size=self.chunk_size,
                    dry_run=self.dry_run,
                    preview=self.preview,
                    atomic=self.atomic,
                    preserve_gid=self.preserve_gid,
                    resumable=self.resumable,
                    job_id=self.job_id,
                    notify=self.notify,
                    schema_policy=self.schema_policy,
                    expected_headers=expected_headers_tuple,
                    detect_pii=self.detect_pii,
                    pii_acknowledged=self.pii_acknowledged,
                    create_worksheet=self.create_worksheet,
                    skip_snapshot=self.skip_snapshot,
                ),
            )

        # Sync metadata
        if (
            self.sync_id
            or self.organization_id is not None
            or self.config_name is not None
            or self.config_id is not None
            or self.source != "sync"
            or self.start_time != 0.0
        ):
            object.__setattr__(
                self,
                "metadata",
                SyncMetadata(
                    sync_id=self.sync_id,
                    organization_id=self.organization_id,
                    config_name=self.config_name,
                    config_id=self.config_id,
                    source=self.source,
                    start_time=self.start_time,
                ),
            )

        # Sync features
        if (
            self.incremental_config is not None
            or self.column_mapping_config is not None
            or self.pii_config is not None
        ):
            object.__setattr__(
                self,
                "features",
                SyncFeatureConfigs(
                    incremental_config=self.incremental_config,
                    column_mapping_config=self.column_mapping_config,
                    pii_config=self.pii_config,
                ),
            )

        # Sync state - state object shares references with flat attributes
        object.__setattr__(
            self,
            "state",
            SyncState(
                headers=self.headers,
                rows=self.rows,
                cleaned_rows=self.cleaned_rows,
                schema_changes=self.schema_changes,
                pii_detection_result=self.pii_detection_result,
                step_warnings=self.step_warnings,
            ),
        )

    @classmethod
    def create(
        cls,
        config: Config,
        logger: logging.Logger,
        *,
        options: SyncOptions | None = None,
        metadata: SyncMetadata | None = None,
        features: SyncFeatureConfigs | None = None,
    ) -> "SyncContext":
        """Create a SyncContext with component objects (new API).

        This is the preferred way to create SyncContext for new code.

        Args:
            config: Main configuration object.
            logger: Logger instance.
            options: Execution options (defaults created if None).
            metadata: Tracking metadata (auto-generated if None).
            features: Feature configurations (empty if None).

        Returns:
            Configured SyncContext.

        Example:
            ctx = SyncContext.create(
                config=config,
                logger=logger,
                options=SyncOptions(mode="streaming", chunk_size=500),
                metadata=SyncMetadata.generate(source="api"),
            )
        """
        _options = options or SyncOptions()
        _metadata = metadata or SyncMetadata.generate()
        _features = features or SyncFeatureConfigs()

        # Convert expected_headers tuple to list for backward compat
        expected_headers_list = (
            list(_options.expected_headers) if _options.expected_headers else None
        )

        return cls(
            config=config,
            logger=logger,
            # Component objects
            options=_options,
            metadata=_metadata,
            features=_features,
            state=SyncState(),
            # Flat attributes (synced from components)
            sync_id=_metadata.sync_id,
            dry_run=_options.dry_run,
            preview=_options.preview,
            mode=_options.mode,
            chunk_size=_options.chunk_size,
            notify=_options.notify,
            source=_metadata.source,
            organization_id=_metadata.organization_id,
            config_name=_metadata.config_name,
            config_id=_metadata.config_id,
            incremental_config=_features.incremental_config,
            column_mapping_config=_features.column_mapping_config,
            pii_config=_features.pii_config,
            pii_acknowledged=_options.pii_acknowledged,
            detect_pii=_options.detect_pii,
            schema_policy=_options.schema_policy,
            expected_headers=expected_headers_list,
            skip_snapshot=_options.skip_snapshot,
            create_worksheet=_options.create_worksheet,
            atomic=_options.atomic,
            preserve_gid=_options.preserve_gid,
            resumable=_options.resumable,
            job_id=_options.job_id,
            start_time=_metadata.start_time,
        )


@runtime_checkable
class SyncStep(Protocol):
    """Protocol for a pipeline step.

    Each step is responsible for one transformation or validation in the
    sync pipeline. Steps are executed in order, with each step receiving
    and potentially modifying the SyncContext.

    Steps should be idempotent where possible and should not have side
    effects (use SyncHook for side effects like notifications).

    Example implementation:
        class DataFetchStep:
            @property
            def name(self) -> str:
                return "fetch_data"

            def should_run(self, ctx: SyncContext) -> bool:
                return True  # Always runs

            def execute(self, ctx: SyncContext) -> StepResult:
                headers, rows = fetch_data(ctx.config, ctx.logger)
                ctx.headers = headers
                ctx.rows = rows
                return StepResult(success=True)
    """

    @property
    def name(self) -> str:
        """Unique name identifying this step."""
        ...

    def should_run(self, ctx: SyncContext) -> bool:
        """Determine if this step should execute.

        Args:
            ctx: Current sync context.

        Returns:
            True if the step should execute, False to skip.
        """
        ...

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


@runtime_checkable
class SyncHook(Protocol):
    """Protocol for sync lifecycle hooks.

    Hooks handle side effects like audit logging, notifications, webhooks,
    and usage tracking. They are called at specific points in the sync
    lifecycle but do not modify the data flow.

    Hooks should be resilient - failures should be logged but should not
    abort the sync operation.

    Example implementation:
        class AuditHook:
            @property
            def name(self) -> str:
                return "audit"

            def on_start(self, ctx: SyncContext) -> None:
                log_audit_event("sync.started", ctx.organization_id, ...)

            def on_success(self, ctx: SyncContext, result: SyncResult) -> None:
                log_audit_event("sync.completed", ctx.organization_id, ...)

            def on_failure(self, ctx: SyncContext, error: Exception) -> None:
                log_audit_event("sync.failed", ctx.organization_id, ...)

            def on_complete(self, ctx: SyncContext, result: SyncResult | None) -> None:
                pass  # No cleanup needed
    """

    @property
    def name(self) -> str:
        """Unique name identifying this hook."""
        ...

    def on_start(self, ctx: SyncContext) -> None:
        """Called when sync operation starts.

        Args:
            ctx: Current sync context.
        """
        ...

    def on_success(self, ctx: SyncContext, result: Any) -> None:
        """Called when sync completes successfully.

        Args:
            ctx: Current sync context.
            result: SyncResult from the sync operation.
        """
        ...

    def on_failure(self, ctx: SyncContext, error: Exception) -> None:
        """Called when sync fails with an error.

        Args:
            ctx: Current sync context.
            error: The exception that caused the failure.
        """
        ...

    def on_complete(self, ctx: SyncContext, result: Any | None) -> None:
        """Called when sync completes (success or failure).

        This is always called after on_success or on_failure, useful
        for cleanup or unconditional logging.

        Args:
            ctx: Current sync context.
            result: SyncResult if successful, None if failed.
        """
        ...
