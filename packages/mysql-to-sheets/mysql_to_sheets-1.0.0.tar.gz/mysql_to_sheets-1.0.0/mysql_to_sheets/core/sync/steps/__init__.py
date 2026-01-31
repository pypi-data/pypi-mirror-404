"""Sync pipeline steps.

Each step module provides a SyncStep implementation for one stage of the
ETL pipeline. Steps are executed in order by the SyncOrchestrator.

Steps available:
- ValidationStep: Config and batch size validation
- DataFetchStep: Fetch data from database
- DataCleanStep: Type conversion for Sheets compatibility
- PIIDetectionStep: Detect PII in columns
- PIITransformStep: Apply PII transformations
- ColumnMappingStep: Apply column mapping/filtering
- SchemaCheckStep: Schema evolution detection and policy
- PreviewStep: Compute diff for preview mode (short-circuits)
- SheetsPushStep: Push data to Google Sheets
"""

from mysql_to_sheets.core.sync.steps.base import BaseSyncStep
from mysql_to_sheets.core.sync.steps.clean import DataCleanStep
from mysql_to_sheets.core.sync.steps.column_mapping import ColumnMappingStep
from mysql_to_sheets.core.sync.steps.fetch import DataFetchStep, EmptyResultHandlerStep
from mysql_to_sheets.core.sync.steps.pii import PIIDetectionStep, PIITransformStep
from mysql_to_sheets.core.sync.steps.preview import DryRunStep, PreviewStep
from mysql_to_sheets.core.sync.steps.push import SheetsPushStep, StreamingPushStep
from mysql_to_sheets.core.sync.steps.schema_check import SchemaCheckStep
from mysql_to_sheets.core.sync.steps.validation import (
    BatchSizeValidationStep,
    ConfigValidationStep,
    QueryTypeValidationStep,
)

__all__ = [
    # Base
    "BaseSyncStep",
    # Validation
    "ConfigValidationStep",
    "QueryTypeValidationStep",
    "BatchSizeValidationStep",
    # Data processing
    "DataFetchStep",
    "EmptyResultHandlerStep",
    "DataCleanStep",
    # PII
    "PIIDetectionStep",
    "PIITransformStep",
    # Transformations
    "ColumnMappingStep",
    "SchemaCheckStep",
    # Output
    "PreviewStep",
    "DryRunStep",
    "SheetsPushStep",
    "StreamingPushStep",
]
