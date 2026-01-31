"""Tests for core/usage_tracking.py — billing usage metering."""

from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.usage_tracking import (
    _get_operations_limit,
    _get_rows_limit,
    get_current_usage,
    get_usage_history,
    get_usage_summary,
    record_api_call,
    record_sync_usage,
)


@pytest.fixture
def mock_repo():
    """Patch get_usage_repository and get_tenant_db_path."""
    repo = MagicMock()
    with (
        patch("mysql_to_sheets.core.billing.usage_tracking.get_usage_repository", return_value=repo),
        patch("mysql_to_sheets.core.billing.usage_tracking.get_tenant_db_path", return_value="/tmp/t.db"),
    ):
        yield repo


class TestRecordSyncUsage:
    @patch("mysql_to_sheets.core.billing.usage_tracking._check_usage_thresholds")
    def test_records_and_returns(self, mock_check, mock_repo):
        record = MagicMock()
        record.rows_synced = 500
        mock_repo.increment_rows_synced.return_value = record

        result = record_sync_usage(organization_id=1, rows_synced=500)
        assert result is record
        mock_repo.increment_rows_synced.assert_called_once_with(
            organization_id=1,
            rows=500,
            increment_operations=True,
        )

    def test_raises_on_failure(self, mock_repo):
        mock_repo.increment_rows_synced.side_effect = RuntimeError("db fail")
        with pytest.raises(RuntimeError):
            record_sync_usage(organization_id=1, rows_synced=100)


class TestRecordApiCall:
    def test_records(self, mock_repo):
        record = MagicMock()
        record.api_calls = 5
        mock_repo.increment_api_calls.return_value = record

        result = record_api_call(organization_id=1)
        assert result is record

    def test_returns_none_on_failure(self, mock_repo):
        mock_repo.increment_api_calls.side_effect = RuntimeError("db fail")
        result = record_api_call(organization_id=1)
        assert result is None


class TestGetCurrentUsage:
    def test_delegates(self, mock_repo):
        mock_repo.get_or_create_current.return_value = "record"
        assert get_current_usage(1) == "record"


class TestGetUsageHistory:
    def test_delegates(self, mock_repo):
        mock_repo.get_history.return_value = ["a", "b"]
        assert get_usage_history(1, limit=5) == ["a", "b"]
        mock_repo.get_history.assert_called_once_with(1, limit=5)


class TestGetUsageSummary:
    def test_delegates(self, mock_repo):
        mock_repo.get_summary.return_value = {"total": 100}
        assert get_usage_summary(1) == {"total": 100}


class TestTierLimits:
    def test_rows_limit(self):
        from mysql_to_sheets.core.tier import Tier

        assert _get_rows_limit(Tier.FREE) == 10000
        assert _get_rows_limit(Tier.PRO) == 100000
        assert _get_rows_limit(Tier.ENTERPRISE) is None

    def test_operations_limit(self):
        from mysql_to_sheets.core.tier import Tier

        assert _get_operations_limit(Tier.FREE) == 100
        assert _get_operations_limit(Tier.BUSINESS) == 10000
        assert _get_operations_limit(Tier.ENTERPRISE) is None
