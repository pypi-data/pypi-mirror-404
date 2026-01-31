"""PII detection and transformation steps for sync pipeline.

This module provides steps for:
- PIIDetectionStep: Detect PII in column data
- PIITransformStep: Apply PII transformations (hash, redact, mask)
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class PIIDetectionStep(BaseSyncStep):
    """Detect PII in query results.

    This step analyzes column names and data patterns to detect
    personally identifiable information (PII) such as:
    - Email addresses
    - Phone numbers
    - Social security numbers
    - Names, addresses

    Detection results are stored in ctx.pii_detection_result.
    """

    @property
    def name(self) -> str:
        return "pii_detection"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if PII detection is enabled."""
        should_detect = ctx.detect_pii if ctx.detect_pii is not None else getattr(
            ctx.config, "pii_detect_enabled", False
        )
        has_active_pii_config = ctx.pii_config and ctx.pii_config.is_active()
        return should_detect or has_active_pii_config

    def execute(self, ctx: SyncContext) -> StepResult:
        """Detect PII in column data.

        Args:
            ctx: Sync context with headers and cleaned_rows populated.

        Returns:
            StepResult indicating detection results.

        Raises:
            PIIAcknowledgmentRequired: If PII detected and not acknowledged.
        """
        from mysql_to_sheets.core.exceptions import PIIAcknowledgmentRequired
        from mysql_to_sheets.core.pii import PIITransformConfig
        from mysql_to_sheets.core.pii_detection import detect_pii_in_columns

        self.log_info(ctx, "Running PII detection")

        # Build PII config from settings if not provided
        pii_config = ctx.pii_config
        if pii_config is None:
            pii_config = PIITransformConfig(
                enabled=True,
                auto_detect=True,
                confidence_threshold=getattr(ctx.config, "pii_confidence_threshold", 0.7),
                sample_size=getattr(ctx.config, "pii_sample_size", 100),
            )
            ctx.pii_config = pii_config

        # Detect PII in columns
        if pii_config.auto_detect:
            pii_result = detect_pii_in_columns(
                ctx.headers, ctx.cleaned_rows, pii_config, ctx.logger
            )
            ctx.pii_detection_result = pii_result

            if pii_result.has_pii:
                self.log_info(ctx, pii_result.summary())

                # Check if acknowledgment is required
                if pii_result.requires_acknowledgment and not ctx.pii_acknowledged:
                    # Check for explicit transforms for all detected columns
                    unhandled_columns = [
                        col.column_name
                        for col in pii_result.columns
                        if (
                            pii_config.get_transform_for_column(col.column_name) is None
                            and not pii_config.is_acknowledged(col.column_name)
                        )
                    ]

                    if unhandled_columns:
                        self.log_warning(
                            ctx,
                            f"PII detected in {len(unhandled_columns)} columns "
                            f"without transforms: {unhandled_columns}",
                        )
                        raise PIIAcknowledgmentRequired(pii_result=pii_result)

                return self.success(
                    f"PII detected in {len(pii_result.columns)} columns",
                    data={"pii_columns": [c.column_name for c in pii_result.columns]},
                )

        return self.success("No PII detected")


class PIITransformStep(BaseSyncStep):
    """Apply PII transformations to data.

    This step applies configured transformations to PII columns:
    - hash: SHA256 hash truncated to 16 characters
    - redact: Replace with category-aware redaction
    - partial_mask: Keep last N characters visible
    """

    @property
    def name(self) -> str:
        return "pii_transform"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if PII config has active transforms."""
        return ctx.pii_config is not None and ctx.pii_config.is_active()

    def execute(self, ctx: SyncContext) -> StepResult:
        """Apply PII transforms to data.

        Args:
            ctx: Sync context with cleaned_rows and pii_config.

        Returns:
            StepResult indicating transforms applied.
        """
        from mysql_to_sheets.core.pii_transform import apply_pii_transforms

        self.log_info(ctx, "Applying PII transformations")

        headers, cleaned_rows = apply_pii_transforms(
            ctx.headers,
            ctx.cleaned_rows,
            ctx.pii_config,
            ctx.pii_detection_result,
            ctx.logger,
        )

        ctx.headers = headers
        ctx.cleaned_rows = cleaned_rows

        transform_count = len(ctx.pii_config.column_transforms) if ctx.pii_config else 0
        return self.success(f"Applied {transform_count} PII transforms")
