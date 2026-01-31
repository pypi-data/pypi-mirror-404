"""Sync pipeline package.

This package provides the sync pipeline architecture for MySQL to Google Sheets
synchronization. It maintains full backward compatibility with the original
monolithic sync.py module.

Public API (backward compatible):
    from mysql_to_sheets.core.sync import (
        run_sync,
        SyncResult,
        SyncService,
        fetch_data,
        clean_data,
        clean_value,
        push_to_sheets,
        validate_batch_size,
        setup_logging,
    )

New pipeline API:
    from mysql_to_sheets.core.sync import (
        SyncContext,
        SyncStep,
        SyncHook,
        StepResult,
        SyncOrchestrator,
    )

Package Structure:
    sync/
    ├── __init__.py           # This file - public API
    ├── protocols.py          # SyncStep, SyncHook, SyncContext protocols
    ├── dataclasses.py        # SyncResult, StepResult dataclasses
    ├── orchestrator.py       # SyncOrchestrator for pipeline execution
    ├── pipeline.py           # Step registry and pipeline builder
    ├── steps/                # Pipeline steps
    │   ├── base.py           # BaseSyncStep ABC
    │   ├── validation.py     # Config/batch validation steps
    │   ├── fetch.py          # DataFetchStep
    │   ├── clean.py          # DataCleanStep
    │   ├── pii.py            # PII detection/transform steps
    │   ├── column_mapping.py # ColumnMappingStep
    │   ├── schema_check.py   # SchemaEvolutionStep
    │   ├── preview.py        # PreviewStep
    │   └── push.py           # SheetsPushStep
    └── hooks/                # Side-effect hooks
        ├── base.py           # BaseSyncHook ABC
        ├── audit.py          # AuditHook
        ├── notification.py   # NotificationHook
        ├── webhook.py        # WebhookHook
        ├── freshness.py      # FreshnessHook
        ├── usage.py          # UsageTrackingHook
        └── snapshot.py       # SnapshotHook
"""

# Import from legacy module for backward compatibility
# This ensures all existing imports continue to work:
#   from mysql_to_sheets.core.sync import run_sync, SyncResult, etc.
# Re-export config functions for backward compatibility with tests
from mysql_to_sheets.core.config import get_config

# Re-export database functions for backward compatibility with tests
# that patch mysql_to_sheets.core.sync.get_connection
from mysql_to_sheets.core.database import get_connection

# Import new pipeline components
from mysql_to_sheets.core.sync.converters import (
    SyncResultConverter,
    diff_result_to_dict,
    schema_changes_to_dict,
    sync_result_to_api_response,
    sync_result_to_dict,
    sync_result_to_web_dict,
)
from mysql_to_sheets.core.sync.dataclasses import StepResult
from mysql_to_sheets.core.sync.orchestrator import (
    SyncOrchestrator,
    get_orchestrator,
    reset_orchestrator,
)
from mysql_to_sheets.core.sync.pipeline import SyncPipeline, create_default_pipeline
from mysql_to_sheets.core.sync.protocols import (
    SyncContext,
    SyncFeatureConfigs,
    SyncHook,
    SyncMetadata,
    SyncOptions,
    SyncState,
    SyncStep,
)
from mysql_to_sheets.core.sync_legacy import (
    # Constants
    SHEETS_CELL_SIZE_LIMIT,
    SHEETS_MAX_CELLS,
    SHEETS_MAX_COLUMNS,
    SHEETS_MAX_ROWS_PER_SHEET,
    # Classes
    SyncResult,
    SyncService,
    # Internal functions needed by multi_sheet_sync
    _build_column_mapping_config,
    _build_database_config,
    # Main functions
    clean_data,
    clean_value,
    fetch_data,
    push_to_sheets,
    run_sync,
    setup_logging,
    validate_batch_size,
    validate_query_type,
)

__all__ = [
    # Constants (backward compat)
    "SHEETS_CELL_SIZE_LIMIT",
    "SHEETS_MAX_CELLS",
    "SHEETS_MAX_COLUMNS",
    "SHEETS_MAX_ROWS_PER_SHEET",
    # Main API (backward compat)
    "run_sync",
    "SyncResult",
    "SyncService",
    "fetch_data",
    "clean_data",
    "clean_value",
    "push_to_sheets",
    "validate_batch_size",
    "validate_query_type",
    "setup_logging",
    # New pipeline API
    "SyncContext",
    "SyncOptions",
    "SyncMetadata",
    "SyncFeatureConfigs",
    "SyncState",
    "SyncStep",
    "SyncHook",
    "StepResult",
    "SyncOrchestrator",
    "SyncPipeline",
    "create_default_pipeline",
    "get_orchestrator",
    "reset_orchestrator",
    # Result converters
    "SyncResultConverter",
    "sync_result_to_dict",
    "sync_result_to_api_response",
    "sync_result_to_web_dict",
    "diff_result_to_dict",
    "schema_changes_to_dict",
    # Re-exported for backward compat with tests
    "get_connection",
    # Internal functions (used by multi_sheet_sync, etc.)
    "_build_column_mapping_config",
    "_build_database_config",
    # Re-exported config functions
    "get_config",
]
