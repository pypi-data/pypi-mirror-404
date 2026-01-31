"""Tests for usage tracking module."""

import os
import tempfile
from datetime import date, timedelta

from mysql_to_sheets.core.config import reset_config
from mysql_to_sheets.models.usage import (
    UsageRecord,
    UsageRecordModel,
    UsageRepository,
    get_current_period,
    reset_usage_repository,
)


class TestUsageRecord:
    """Tests for UsageRecord dataclass."""

    def test_usage_record_creation(self):
        """Test creating a usage record."""
        period_start, period_end = get_current_period()
        record = UsageRecord(
            organization_id=1,
            period_start=period_start,
            period_end=period_end,
            rows_synced=100,
            sync_operations=5,
            api_calls=25,
        )

        assert record.organization_id == 1
        assert record.rows_synced == 100
        assert record.sync_operations == 5
        assert record.api_calls == 25

    def test_usage_record_defaults(self):
        """Test usage record default values."""
        period_start, period_end = get_current_period()
        record = UsageRecord(
            organization_id=1,
            period_start=period_start,
            period_end=period_end,
        )

        assert record.rows_synced == 0
        assert record.sync_operations == 0
        assert record.api_calls == 0
        assert record.id is None

    def test_usage_record_to_dict(self):
        """Test converting usage record to dictionary."""
        period_start, period_end = get_current_period()
        record = UsageRecord(
            id=1,
            organization_id=1,
            period_start=period_start,
            period_end=period_end,
            rows_synced=100,
            sync_operations=5,
            api_calls=25,
        )

        d = record.to_dict()
        assert d["id"] == 1
        assert d["organization_id"] == 1
        assert d["rows_synced"] == 100
        assert d["sync_operations"] == 5
        assert d["api_calls"] == 25
        assert d["period_start"] == period_start.isoformat()

    def test_usage_record_from_dict(self):
        """Test creating usage record from dictionary."""
        data = {
            "id": 1,
            "organization_id": 1,
            "period_start": "2026-01-01",
            "period_end": "2026-01-31",
            "rows_synced": 100,
            "sync_operations": 5,
            "api_calls": 25,
        }

        record = UsageRecord.from_dict(data)
        assert record.id == 1
        assert record.organization_id == 1
        assert record.period_start == date(2026, 1, 1)
        assert record.period_end == date(2026, 1, 31)
        assert record.rows_synced == 100


class TestGetCurrentPeriod:
    """Tests for get_current_period function."""

    def test_returns_first_and_last_of_month(self):
        """Test period starts at first of month and ends at last."""
        period_start, period_end = get_current_period()

        assert period_start.day == 1
        # Last day should be in same month as start
        assert period_end.month == period_start.month
        # Next day should be in next month
        next_day = period_end + timedelta(days=1)
        assert next_day.day == 1

    def test_period_end_correct_for_different_months(self):
        """Test period end is correct for months with different lengths."""
        # This test verifies the logic handles month boundaries correctly
        period_start, period_end = get_current_period()

        # period_end should be the last day of the month
        if period_start.month == 12:
            expected_next = period_start.replace(year=period_start.year + 1, month=1, day=1)
        else:
            expected_next = period_start.replace(month=period_start.month + 1, day=1)

        assert period_end == expected_next - timedelta(days=1)


class TestUsageRepository:
    """Tests for UsageRepository."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_config()
        reset_usage_repository()

    def test_get_or_create_current_creates_new_record(self):
        """Test get_or_create_current creates a record if none exists."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)
            record = repo.get_or_create_current(organization_id=1)

            assert record.organization_id == 1
            assert record.rows_synced == 0
            assert record.sync_operations == 0
            assert record.api_calls == 0
            assert record.id is not None
        finally:
            os.unlink(db_path)

    def test_get_or_create_current_returns_existing(self):
        """Test get_or_create_current returns existing record."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            # Create first record
            record1 = repo.get_or_create_current(organization_id=1)

            # Get it again
            record2 = repo.get_or_create_current(organization_id=1)

            assert record1.id == record2.id
        finally:
            os.unlink(db_path)

    def test_increment_rows_synced(self):
        """Test incrementing rows synced counter."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            # First increment creates record
            record = repo.increment_rows_synced(organization_id=1, rows=100)
            assert record.rows_synced == 100
            assert record.sync_operations == 1

            # Second increment adds to existing
            record = repo.increment_rows_synced(organization_id=1, rows=50)
            assert record.rows_synced == 150
            assert record.sync_operations == 2
        finally:
            os.unlink(db_path)

    def test_increment_rows_synced_without_operations(self):
        """Test incrementing rows without incrementing operations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            record = repo.increment_rows_synced(
                organization_id=1,
                rows=100,
                increment_operations=False,
            )
            assert record.rows_synced == 100
            assert record.sync_operations == 0
        finally:
            os.unlink(db_path)

    def test_increment_api_calls(self):
        """Test incrementing API calls counter."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            # First increment creates record
            record = repo.increment_api_calls(organization_id=1)
            assert record.api_calls == 1

            # Increment by multiple
            record = repo.increment_api_calls(organization_id=1, count=5)
            assert record.api_calls == 6
        finally:
            os.unlink(db_path)

    def test_get_history(self):
        """Test getting usage history."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            # Create records for current period
            repo.increment_rows_synced(organization_id=1, rows=100)

            # Create records for previous period
            last_month_start = (date.today().replace(day=1) - timedelta(days=1)).replace(day=1)
            if last_month_start.month == 12:
                last_month_end = last_month_start.replace(day=31)
            else:
                last_month_end = last_month_start.replace(
                    month=last_month_start.month + 1
                ) - timedelta(days=1)

            repo.get_or_create(1, last_month_start, last_month_end)

            history = repo.get_history(organization_id=1)
            assert len(history) >= 1
        finally:
            os.unlink(db_path)

    def test_get_summary(self):
        """Test getting usage summary."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            # Create some usage
            repo.increment_rows_synced(organization_id=1, rows=100)
            repo.increment_api_calls(organization_id=1, count=10)

            summary = repo.get_summary(organization_id=1)

            assert "current_period" in summary
            assert "totals" in summary
            assert "periods_tracked" in summary
            assert summary["current_period"]["rows_synced"] == 100
            assert summary["current_period"]["api_calls"] == 10
        finally:
            os.unlink(db_path)

    def test_different_organizations_isolated(self):
        """Test that different organizations have isolated usage."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            repo = UsageRepository(db_path)

            repo.increment_rows_synced(organization_id=1, rows=100)
            repo.increment_rows_synced(organization_id=2, rows=200)

            record1 = repo.get_or_create_current(organization_id=1)
            record2 = repo.get_or_create_current(organization_id=2)

            assert record1.rows_synced == 100
            assert record2.rows_synced == 200
        finally:
            os.unlink(db_path)


class TestUsageTracking:
    """Tests for usage tracking service functions."""

    def setup_method(self):
        """Reset singletons before each test."""
        reset_config()
        reset_usage_repository()

    def test_record_sync_usage(self):
        """Test recording sync usage."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from mysql_to_sheets.core.usage_tracking import record_sync_usage

            record = record_sync_usage(
                organization_id=1,
                rows_synced=500,
                db_path=db_path,
            )

            assert record.organization_id == 1
            assert record.rows_synced == 500
            assert record.sync_operations == 1
        finally:
            reset_usage_repository()
            os.unlink(db_path)

    def test_record_api_call(self):
        """Test recording API call."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from mysql_to_sheets.core.usage_tracking import record_api_call

            record = record_api_call(
                organization_id=1,
                db_path=db_path,
            )

            assert record is not None
            assert record.api_calls == 1
        finally:
            reset_usage_repository()
            os.unlink(db_path)

    def test_get_usage_summary(self):
        """Test getting usage summary."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from mysql_to_sheets.core.usage_tracking import (
                get_usage_summary,
                record_sync_usage,
            )

            record_sync_usage(organization_id=1, rows_synced=100, db_path=db_path)

            summary = get_usage_summary(organization_id=1, db_path=db_path)

            assert "current_period" in summary
            assert "totals" in summary
            assert summary["current_period"]["rows_synced"] == 100
        finally:
            reset_usage_repository()
            os.unlink(db_path)

    def test_get_current_usage(self):
        """Test getting current usage."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from mysql_to_sheets.core.usage_tracking import (
                get_current_usage,
                record_sync_usage,
            )

            record_sync_usage(organization_id=1, rows_synced=250, db_path=db_path)

            current = get_current_usage(organization_id=1, db_path=db_path)

            assert current.rows_synced == 250
            assert current.sync_operations == 1
        finally:
            reset_usage_repository()
            os.unlink(db_path)

    def test_check_usage_threshold_within_limit(self):
        """Test checking usage threshold when within limit."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            from mysql_to_sheets.core.usage_tracking import (
                check_usage_threshold,
                record_sync_usage,
            )

            # Record some usage
            record_sync_usage(organization_id=1, rows_synced=100, db_path=db_path)

            # Check thresholds (will use default limits since no org exists)
            thresholds = check_usage_threshold(
                organization_id=1,
                threshold_percent=80,
                db_path=db_path,
            )

            assert "rows_synced" in thresholds
            assert thresholds["rows_synced"]["current"] == 100
            # Default limit is 10000 for free tier
            assert thresholds["rows_synced"]["exceeded"] is False
        finally:
            reset_usage_repository()
            os.unlink(db_path)


class TestUsageRecordModel:
    """Tests for UsageRecordModel SQLAlchemy model."""

    def test_model_to_dataclass(self):
        """Test converting model to dataclass."""
        model = UsageRecordModel(
            id=1,
            organization_id=1,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            rows_synced=100,
            sync_operations=5,
            api_calls=25,
        )

        record = model.to_dataclass()

        assert isinstance(record, UsageRecord)
        assert record.id == 1
        assert record.organization_id == 1
        assert record.rows_synced == 100

    def test_model_from_dataclass(self):
        """Test creating model from dataclass."""
        record = UsageRecord(
            organization_id=1,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            rows_synced=100,
            sync_operations=5,
            api_calls=25,
        )

        model = UsageRecordModel.from_dataclass(record)

        assert isinstance(model, UsageRecordModel)
        assert model.organization_id == 1
        assert model.rows_synced == 100

    def test_model_repr(self):
        """Test model string representation."""
        model = UsageRecordModel(
            organization_id=1,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            rows_synced=100,
            sync_operations=5,
        )

        repr_str = repr(model)
        assert "org=1" in repr_str
        assert "rows=100" in repr_str
