"""Schema evolution step for sync pipeline.

This module provides the SchemaCheckStep that detects schema changes
between syncs and applies the configured policy.
"""

from typing import Any

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class SchemaCheckStep(BaseSyncStep):
    """Detect and handle schema evolution.

    This step compares current headers with expected headers from the
    previous sync and applies the configured policy:

    - strict: Fail if any columns change (default, FREE tier)
    - additive: Allow new columns (PRO+)
    - flexible: Allow all changes (PRO+)
    - notify_only: Proceed with intersection and notify (PRO+)

    Schema change info is stored in ctx.schema_changes.
    """

    @property
    def name(self) -> str:
        return "schema_check"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run if schema policy or expected headers are provided."""
        return ctx.schema_policy is not None or ctx.expected_headers is not None

    def execute(self, ctx: SyncContext) -> StepResult:
        """Detect schema changes and apply policy.

        Args:
            ctx: Sync context with headers and schema configuration.

        Returns:
            StepResult indicating schema check results.

        Raises:
            SchemaChangeError: If strict policy and columns changed.
        """
        from mysql_to_sheets.core.schema_evolution import (
            SchemaPolicy,
            apply_schema_policy,
            detect_schema_change,
            get_policy_tier_requirement,
        )
        from mysql_to_sheets.core.tier import check_feature_access, get_tier_from_license

        # Default to strict policy
        policy = ctx.schema_policy or "strict"
        policy_enum = SchemaPolicy.from_string(policy)

        # Check tier access for non-strict policies
        feature_key = get_policy_tier_requirement(policy_enum)
        if feature_key is not None:
            current_tier = get_tier_from_license()
            if not check_feature_access(current_tier, feature_key):
                self.log_warning(
                    ctx,
                    f"Schema policy '{policy}' requires PRO tier or higher. "
                    f"Current tier: {current_tier.value}. Using 'strict' policy.",
                )
                policy = "strict"
                policy_enum = SchemaPolicy.STRICT

        # Detect schema changes
        schema_change = detect_schema_change(ctx.expected_headers, ctx.headers)

        if not schema_change.has_changes:
            self.log_debug(ctx, "No schema changes detected")
            return self.success("Schema unchanged")

        self.log_info(ctx, f"Schema change detected: {schema_change.summary()}")

        # Apply policy (may raise SchemaChangeError)
        headers, cleaned_rows, should_notify = apply_schema_policy(
            schema_change, policy_enum, ctx.headers, ctx.cleaned_rows
        )

        ctx.headers = headers
        ctx.cleaned_rows = cleaned_rows

        # Record schema change info for result
        schema_change_info: dict[str, Any] = schema_change.to_dict()
        schema_change_info["policy_applied"] = policy
        ctx.schema_changes = schema_change_info

        # Handle notification if needed (delegated to notification hook)
        if should_notify and ctx.notify is not False:
            # Store for notification hook to pick up
            if ctx.schema_changes:
                ctx.schema_changes["should_notify"] = True

        return self.success(
            f"Schema change handled with policy '{policy}'",
            data={
                "added_columns": schema_change.added_columns,
                "removed_columns": schema_change.removed_columns,
                "policy": policy,
            },
        )
