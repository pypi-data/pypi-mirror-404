"""Tests for the freshness/SLA tracking system."""

import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from mysql_to_sheets.core.freshness import (
    FRESHNESS_FRESH,
    FRESHNESS_STALE,
    FRESHNESS_UNKNOWN,
    FRESHNESS_WARNING,
    FreshnessStatus,
    calculate_freshness_status,
    check_all_freshness,
    get_freshness_report,
    get_freshness_status,
    set_sla,
    update_freshness,
)
from mysql_to_sheets.core.freshness_alerts import (
    _create_alert,
    check_and_alert,
    get_stale_syncs,
)
from mysql_to_sheets.models.organizations import (
    Organization,
    OrganizationRepository,
)
from mysql_to_sheets.models.sync_configs import (
    SyncConfigDefinition,
    SyncConfigRepository,
    reset_sync_config_repository,
)


class TestFreshnessCalculation:
    """Tests for freshness status calculation."""

    def test_unknown_when_no_last_sync(self):
        """Test unknown status when there's no last sync."""
        status, minutes, percent = calculate_freshness_status(
            last_success_at=None,
            sla_minutes=60,
        )

        assert status == FRESHNESS_UNKNOWN
        assert minutes is None
        assert percent is None

    def test_fresh_when_within_sla(self):
        """Test fresh status when sync is within SLA."""
        last_sync = datetime.now(timezone.utc) - timedelta(minutes=30)

        status, minutes, percent = calculate_freshness_status(
            last_success_at=last_sync,
            sla_minutes=60,
            warning_percent=80,
        )

        assert status == FRESHNESS_FRESH
        assert minutes == 30
        assert percent == 50.0

    def test_warning_when_approaching_sla(self):
        """Test warning status when approaching SLA threshold."""
        last_sync = datetime.now(timezone.utc) - timedelta(minutes=50)

        status, minutes, percent = calculate_freshness_status(
            last_success_at=last_sync,
            sla_minutes=60,
            warning_percent=80,
        )

        assert status == FRESHNESS_WARNING
        assert minutes == 50
        assert abs(percent - 83.3) < 1  # Approximately 83.3%

    def test_stale_when_past_sla(self):
        """Test stale status when past SLA."""
        last_sync = datetime.now(timezone.utc) - timedelta(minutes=90)

        status, minutes, percent = calculate_freshness_status(
            last_success_at=last_sync,
            sla_minutes=60,
            warning_percent=80,
        )

        assert status == FRESHNESS_STALE
        assert minutes == 90
        assert percent == 150.0

    def test_exact_sla_boundary(self):
        """Test exactly at SLA boundary."""
        last_sync = datetime.now(timezone.utc) - timedelta(minutes=60)

        status, minutes, percent = calculate_freshness_status(
            last_success_at=last_sync,
            sla_minutes=60,
        )

        assert status == FRESHNESS_STALE
        assert minutes == 60
        assert percent == 100.0


class TestFreshnessStatus:
    """Tests for FreshnessStatus dataclass."""

    def test_to_dict(self):
        """Test converting status to dictionary."""
        status = FreshnessStatus(
            config_id=1,
            config_name="test-sync",
            status=FRESHNESS_FRESH,
            last_success_at=datetime(2024, 1, 1, 12, 0, 0),
            sla_minutes=60,
            minutes_since_sync=30,
            percent_of_sla=50.0,
            organization_id=1,
        )

        data = status.to_dict()

        assert data["config_id"] == 1
        assert data["config_name"] == "test-sync"
        assert data["status"] == FRESHNESS_FRESH
        assert "2024-01-01" in data["last_success_at"]
        assert data["sla_minutes"] == 60
        assert data["minutes_since_sync"] == 30
        assert data["percent_of_sla"] == 50.0


class TestFreshnessService:
    """Tests for freshness service functions."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def org_repo(self, db_path):
        """Create an organization repository."""
        return OrganizationRepository(db_path)

    @pytest.fixture
    def config_repo(self, db_path, org_repo):
        """Create a sync config repository.

        Depends on org_repo to ensure organizations table is created first.
        """
        return SyncConfigRepository(db_path)

    @pytest.fixture
    def org(self, org_repo):
        """Create a test organization."""
        org = Organization(name="Test Org", slug="test-org")
        return org_repo.create(org)

    @pytest.fixture
    def sync_config(self, config_repo, org):
        """Create a test sync config."""
        config = SyncConfigDefinition(
            name="test-sync",
            sql_query="SELECT * FROM users",
            sheet_id="sheet123",
            organization_id=org.id,
            sla_minutes=60,
        )
        return config_repo.create(config)

    def test_update_freshness_success(self, db_path, sync_config, org):
        """Test updating freshness after successful sync."""
        result = update_freshness(
            config_id=sync_config.id,
            organization_id=org.id,
            success=True,
            row_count=100,
            db_path=db_path,
        )

        assert result is True

        # Check updated values
        repo = SyncConfigRepository(db_path)
        updated = repo.get_by_id(sync_config.id, org.id)
        assert updated.last_sync_at is not None
        assert updated.last_success_at is not None
        assert updated.last_row_count == 100

    def test_update_freshness_failure(self, db_path, sync_config, org):
        """Test updating freshness after failed sync."""
        result = update_freshness(
            config_id=sync_config.id,
            organization_id=org.id,
            success=False,
            db_path=db_path,
        )

        assert result is True

        # Check updated values
        repo = SyncConfigRepository(db_path)
        updated = repo.get_by_id(sync_config.id, org.id)
        assert updated.last_sync_at is not None
        assert updated.last_success_at is None  # Not updated on failure

    def test_get_freshness_status(self, db_path, sync_config, org):
        """Test getting freshness status for a config."""
        # First update freshness
        update_freshness(
            config_id=sync_config.id,
            organization_id=org.id,
            success=True,
            row_count=50,
            db_path=db_path,
        )

        status = get_freshness_status(
            config_id=sync_config.id,
            organization_id=org.id,
            db_path=db_path,
        )

        assert status is not None
        assert status.config_id == sync_config.id
        assert status.config_name == "test-sync"
        assert status.status == FRESHNESS_FRESH
        assert status.sla_minutes == 60

    def test_check_all_freshness(self, db_path, org, config_repo):
        """Test checking freshness for all configs."""
        # Create multiple configs
        config1 = SyncConfigDefinition(
            name="config-1",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
        )
        config2 = SyncConfigDefinition(
            name="config-2",
            sql_query="SELECT 2",
            sheet_id="sheet2",
            organization_id=org.id,
            sla_minutes=60,
        )
        config_repo.create(config1)
        config_repo.create(config2)

        statuses = check_all_freshness(
            organization_id=org.id,
            db_path=db_path,
        )

        assert len(statuses) == 2
        names = {s.config_name for s in statuses}
        assert "config-1" in names
        assert "config-2" in names

    def test_get_freshness_report(self, db_path, org, config_repo):
        """Test getting a freshness report."""
        # Create a config
        config = SyncConfigDefinition(
            name="report-test",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
        )
        config_repo.create(config)

        report = get_freshness_report(
            organization_id=org.id,
            db_path=db_path,
        )

        assert report["organization_id"] == org.id
        assert report["total_configs"] == 1
        assert "counts" in report
        assert "health_percent" in report
        assert "statuses" in report
        assert "checked_at" in report

    def test_set_sla(self, db_path, sync_config, org):
        """Test setting SLA for a config."""
        result = set_sla(
            config_id=sync_config.id,
            organization_id=org.id,
            sla_minutes=120,
            db_path=db_path,
        )

        assert result is True

        # Verify update
        repo = SyncConfigRepository(db_path)
        updated = repo.get_by_id(sync_config.id, org.id)
        assert updated.sla_minutes == 120

    def test_set_sla_invalid(self, db_path, sync_config, org):
        """Test that invalid SLA is rejected."""
        with pytest.raises(ValueError):
            set_sla(
                config_id=sync_config.id,
                organization_id=org.id,
                sla_minutes=0,
                db_path=db_path,
            )


class TestFreshnessAlerts:
    """Tests for freshness alerting."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def org_repo(self, db_path):
        """Create an organization repository."""
        return OrganizationRepository(db_path)

    @pytest.fixture
    def config_repo(self, db_path, org_repo):
        """Create a sync config repository.

        Depends on org_repo to ensure organizations table is created first.
        """
        return SyncConfigRepository(db_path)

    @pytest.fixture
    def org(self, org_repo):
        """Create a test organization."""
        org = Organization(name="Test Org", slug="test-org")
        return org_repo.create(org)

    def test_create_alert_stale(self):
        """Test creating a stale alert."""
        status = FreshnessStatus(
            config_id=1,
            config_name="stale-sync",
            status=FRESHNESS_STALE,
            last_success_at=datetime.now(timezone.utc) - timedelta(hours=2),
            sla_minutes=60,
            minutes_since_sync=120,
            percent_of_sla=200.0,
            organization_id=1,
        )

        alert = _create_alert(status)

        assert alert["type"] == "freshness_alert"
        assert alert["severity"] == "critical"
        assert alert["status"] == FRESHNESS_STALE
        assert alert["config_id"] == 1
        assert "stale" in alert["message"].lower()

    def test_create_alert_warning(self):
        """Test creating a warning alert."""
        status = FreshnessStatus(
            config_id=1,
            config_name="warning-sync",
            status=FRESHNESS_WARNING,
            last_success_at=datetime.now(timezone.utc) - timedelta(minutes=50),
            sla_minutes=60,
            minutes_since_sync=50,
            percent_of_sla=83.3,
            organization_id=1,
        )

        alert = _create_alert(status)

        assert alert["severity"] == "warning"
        assert alert["status"] == FRESHNESS_WARNING
        assert "approaching" in alert["message"].lower()

    def test_check_and_alert_no_alerts(self, db_path, org, config_repo):
        """Test check and alert with no alerts needed."""
        # Create a fresh config
        config = SyncConfigDefinition(
            name="fresh-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=datetime.now(timezone.utc),
        )
        config_repo.create(config)

        alerts = check_and_alert(
            organization_id=org.id,
            db_path=db_path,
            send_notifications=False,
        )

        assert len(alerts) == 0

    def test_get_stale_syncs(self, db_path, org, config_repo):
        """Test getting stale syncs."""
        # Create a stale config
        stale_time = datetime.now(timezone.utc) - timedelta(hours=2)
        config = SyncConfigDefinition(
            name="stale-sync",
            sql_query="SELECT 1",
            sheet_id="sheet1",
            organization_id=org.id,
            sla_minutes=60,
            last_success_at=stale_time,
        )
        config_repo.create(config)

        stale = get_stale_syncs(
            organization_id=org.id,
            db_path=db_path,
        )

        assert len(stale) == 1
        assert stale[0]["config_name"] == "stale-sync"


class TestIntegration:
    """Integration tests for freshness tracking."""

    @pytest.fixture
    def db_path(self):
        """Create a temporary database file."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            path = f.name
        yield path
        try:
            os.unlink(path)
        except OSError:
            pass
        reset_sync_config_repository()

    @pytest.fixture
    def setup_org_and_config(self, db_path):
        """Set up organization and config for integration tests."""
        org_repo = OrganizationRepository(db_path)
        config_repo = SyncConfigRepository(db_path)

        org = Organization(name="Integration Org", slug="int-org")
        org = org_repo.create(org)

        config = SyncConfigDefinition(
            name="int-sync",
            sql_query="SELECT * FROM test",
            sheet_id="sheet123",
            organization_id=org.id,
            sla_minutes=60,
        )
        config = config_repo.create(config)

        return org, config

    def test_sync_to_freshness_flow(self, db_path, setup_org_and_config):
        """Test the flow from sync to freshness update."""
        org, config = setup_org_and_config

        # Simulate a successful sync updating freshness
        updated = update_freshness(
            config_id=config.id,
            organization_id=org.id,
            success=True,
            row_count=500,
            db_path=db_path,
        )

        assert updated is True

        # Check freshness status
        status = get_freshness_status(
            config_id=config.id,
            organization_id=org.id,
            db_path=db_path,
        )

        assert status.status == FRESHNESS_FRESH
        assert status.minutes_since_sync is not None
        assert status.minutes_since_sync < 1  # Just updated

        # Get report
        report = get_freshness_report(
            organization_id=org.id,
            db_path=db_path,
        )

        assert report["total_configs"] == 1
        assert report["counts"][FRESHNESS_FRESH] == 1
        assert report["health_percent"] == 100.0
