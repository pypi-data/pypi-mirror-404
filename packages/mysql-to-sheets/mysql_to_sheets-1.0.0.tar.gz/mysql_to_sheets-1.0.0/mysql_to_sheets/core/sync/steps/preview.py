"""Preview and dry-run steps for sync pipeline.

This module provides steps that handle preview and dry-run modes,
short-circuiting the pipeline before data is pushed.
"""

from mysql_to_sheets.core.sync.protocols import StepResult, SyncContext
from mysql_to_sheets.core.sync.steps.base import BaseSyncStep


class PreviewStep(BaseSyncStep):
    """Compute diff for preview mode.

    This step compares the data to be synced with the current sheet
    contents and returns a diff without actually pushing changes.

    This step short-circuits the pipeline - no subsequent steps run.
    """

    @property
    def name(self) -> str:
        return "preview"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run only if preview mode is enabled."""
        return ctx.preview

    def execute(self, ctx: SyncContext) -> StepResult:
        """Compute diff with current sheet data.

        Args:
            ctx: Sync context with headers and cleaned_rows.

        Returns:
            StepResult that short-circuits with diff data.
        """
        from mysql_to_sheets.core.diff import run_preview

        self.log_info(
            ctx, f"Preview mode: comparing {len(ctx.cleaned_rows)} rows with current sheet"
        )

        diff = run_preview(ctx.config, ctx.headers, ctx.cleaned_rows, ctx.logger)

        return self.short_circuit(
            message=f"Preview: {diff.summary()}",
            data={
                "preview": True,
                "diff": diff.to_dict(),
                "row_count": len(ctx.cleaned_rows),
                "column_count": len(ctx.headers),
            },
        )


class DryRunStep(BaseSyncStep):
    """Handle dry-run mode.

    This step validates the data without pushing to Sheets.
    It short-circuits the pipeline after validation.
    """

    @property
    def name(self) -> str:
        return "dry_run"

    def should_run(self, ctx: SyncContext) -> bool:
        """Run only if dry-run mode is enabled and not preview."""
        # Preview takes precedence over dry-run
        return ctx.dry_run and not ctx.preview

    def execute(self, ctx: SyncContext) -> StepResult:
        """Validate without pushing.

        Args:
            ctx: Sync context with headers and cleaned_rows.

        Returns:
            StepResult that short-circuits with validation results.
        """
        row_count = len(ctx.cleaned_rows)
        col_count = len(ctx.headers)

        self.log_info(
            ctx, f"Dry run: would push {row_count} rows to sheet (mode={ctx.mode})"
        )

        return self.short_circuit(
            message=f"Dry run: validated {row_count} rows",
            data={
                "dry_run": True,
                "row_count": row_count,
                "column_count": col_count,
                "mode": ctx.mode,
            },
        )
