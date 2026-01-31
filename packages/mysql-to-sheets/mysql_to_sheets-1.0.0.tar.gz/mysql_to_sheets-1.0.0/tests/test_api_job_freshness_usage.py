"""Tests for job, freshness, and usage API routes."""

import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

from mysql_to_sheets.api.app import create_app
from mysql_to_sheets.core.config import reset_config


@pytest.fixture
def client():
    """Create test client with auth disabled and user context mocked."""
    with (
        patch.dict(
            os.environ,
            {
                "API_AUTH_ENABLED": "false",
                "JWT_SECRET_KEY": "test_secret_key",
            },
        ),
        patch("mysql_to_sheets.core.tenant.get_tenant_db_path", return_value="/tmp/test.db"),
    ):
        reset_config()

        # Mock the UserAuthMiddleware to inject a fake user into request.state
        from mysql_to_sheets.api.middleware.user_auth import UserAuthMiddleware

        original_dispatch = UserAuthMiddleware.dispatch

        async def mock_dispatch(middleware_self, request, call_next):
            # Inject fake user and org_id into request state
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user.email = "test@example.com"
            mock_user.role = "admin"
            mock_user.organization_id = 1

            request.state.user = mock_user
            request.state.organization_id = 1

            return await call_next(request)

        with patch.object(UserAuthMiddleware, "dispatch", mock_dispatch):
            app = create_app()
            yield TestClient(app)

        reset_config()


class TestJobRoutes:
    """Tests for /api/v1/jobs/* endpoints."""

    @patch("mysql_to_sheets.api.job_routes.list_jobs")
    def test_list_jobs(self, mock_list_jobs, client):
        """Test listing jobs."""
        from mysql_to_sheets.models.jobs import Job

        mock_list_jobs.return_value = [
            Job(
                id=1,
                organization_id=1,
                job_type="sync",
                payload={"config_id": 1},
                status="completed",
                created_at=datetime.now(timezone.utc),
            ),
        ]

        response = client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert len(data["jobs"]) == 1

    @patch("mysql_to_sheets.api.job_routes.get_job_status")
    def test_get_job_by_id(self, mock_get_job, client):
        """Test getting specific job."""
        from mysql_to_sheets.models.jobs import Job

        mock_get_job.return_value = Job(
            id=1,
            organization_id=1,
            job_type="sync",
            payload={"config_id": 1},
            status="running",
            created_at=datetime.now(timezone.utc),
        )

        response = client.get("/api/v1/jobs/1")
        assert response.status_code == 200
        data = response.json()
        assert data["job"]["id"] == 1
        assert data["job"]["status"] == "running"

    @patch("mysql_to_sheets.api.job_routes.cancel_job")
    def test_cancel_job(self, mock_cancel, client):
        """Test cancelling a job."""
        mock_cancel.return_value = True

        response = client.post("/api/v1/jobs/1/cancel")
        assert response.status_code == 200
        data = response.json()
        assert "success" in data

    @patch("mysql_to_sheets.api.job_routes.get_queue_stats")
    def test_get_job_stats(self, mock_get_stats, client):
        """Test getting job queue statistics."""
        mock_get_stats.return_value = {
            "pending": 5,
            "running": 2,
            "completed": 100,
            "failed": 3,
            "cancelled": 1,
        }

        response = client.get("/api/v1/jobs/stats")
        assert response.status_code == 200
        data = response.json()
        assert "pending" in data
        assert data["completed"] == 100


class TestFreshnessRoutes:
    """Tests for /api/v1/freshness/* endpoints."""

    @patch("mysql_to_sheets.api.freshness_routes.check_all_freshness")
    def test_get_freshness_status(self, mock_check_all, client):
        """Test getting freshness status."""
        from mysql_to_sheets.core.freshness import FreshnessStatus

        mock_check_all.return_value = [
            FreshnessStatus(
                config_id=1,
                config_name="test-config",
                organization_id=1,
                status="fresh",
                sla_minutes=60,
                last_success_at=datetime.now(timezone.utc),
                minutes_since_sync=30,
                percent_of_sla=50.0,
            ),
        ]

        response = client.get("/api/v1/freshness")
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        assert len(data["statuses"]) == 1
        assert data["statuses"][0]["status"] == "fresh"

    @patch("mysql_to_sheets.api.freshness_routes.get_freshness_report")
    def test_get_freshness_report(self, mock_get_report, client):
        """Test getting freshness report."""
        mock_get_report.return_value = {
            "organization_id": 1,
            "total_configs": 5,
            "counts": {
                "fresh": 3,
                "warning": 1,
                "stale": 1,
                "unknown": 0,
            },
            "health_percent": 60.0,
            "statuses": [],
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        response = client.get("/api/v1/freshness/report")
        assert response.status_code == 200
        data = response.json()
        assert data["total_configs"] == 5
        assert data["health_percent"] == 60.0

    @patch("mysql_to_sheets.api.freshness_routes.set_sla")
    def test_update_sla(self, mock_set_sla, client):
        """Test updating SLA threshold."""
        mock_set_sla.return_value = True

        response = client.put(
            "/api/v1/freshness/1/sla",
            json={
                "sla_minutes": 120,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "success" in data


class TestUsageRoutes:
    """Tests for /api/v1/usage/* endpoints."""

    @patch("mysql_to_sheets.api.usage_routes.get_current_usage")
    def test_get_current_usage(self, mock_get_usage, client):
        """Test getting current billing period usage."""
        from mysql_to_sheets.models.usage import UsageRecord

        now = datetime.now(timezone.utc)
        mock_get_usage.return_value = UsageRecord(
            organization_id=1,
            period_start=now.date(),
            period_end=now.date(),
            rows_synced=10000,
            sync_operations=50,
            api_calls=200,
            created_at=now,
            updated_at=now,
        )

        response = client.get("/api/v1/usage/current")
        assert response.status_code == 200
        data = response.json()
        assert data["usage"]["rows_synced"] == 10000
        assert data["usage"]["sync_operations"] == 50

    @patch("mysql_to_sheets.api.usage_routes.get_usage_history")
    def test_get_usage_history(self, mock_get_history, client):
        """Test getting usage history."""
        from mysql_to_sheets.models.usage import UsageRecord

        now = datetime.now(timezone.utc)
        mock_get_history.return_value = [
            UsageRecord(
                organization_id=1,
                period_start=now.date(),
                period_end=now.date(),
                rows_synced=5000,
                sync_operations=25,
                api_calls=100,
                created_at=now,
                updated_at=now,
            ),
        ]

        response = client.get("/api/v1/usage/history")
        assert response.status_code == 200
        data = response.json()
        assert "periods" in data
        assert len(data["periods"]) == 1

    @patch("mysql_to_sheets.api.usage_routes.get_usage_summary")
    def test_get_usage_summary(self, mock_get_summary, client):
        """Test getting usage summary."""
        mock_get_summary.return_value = {
            "current_period": {
                "rows_synced": 10000,
                "sync_operations": 50,
                "api_calls": 200,
            },
            "totals": {
                "rows_synced": 50000,
                "sync_operations": 250,
                "api_calls": 1000,
            },
            "periods_tracked": 5,
        }

        response = client.get("/api/v1/usage/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["totals"]["rows_synced"] == 50000


class TestAuditRoutes:
    """Tests for /api/v1/audit/* endpoints."""

    @patch("mysql_to_sheets.core.audit.log_action")
    @patch("mysql_to_sheets.api.audit_routes.get_audit_log_repository")
    def test_list_audit_logs(self, mock_get_repo, mock_log_action, client):
        """Test listing audit logs."""
        from mysql_to_sheets.models.audit_logs import AuditLog

        # The client fixture already injects a user with role="admin" via UserAuthMiddleware,
        # so we don't need to mock require_permission. The dependency will read from
        # request.state.user which the middleware sets up.
        # Note: We patch at the import location (audit_routes) not the source (models.audit_logs)

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [
            AuditLog(
                id=1,
                organization_id=1,
                user_id=1,
                action="sync.started",
                resource_type="config",
                resource_id="1",
                timestamp=datetime.now(timezone.utc),
                metadata={},
            ),
        ]
        mock_repo.count.return_value = 1
        mock_get_repo.return_value = mock_repo

        response = client.get("/api/v1/audit")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        # The count may be different due to audit middleware logging the request itself
        assert len(data["logs"]) >= 1

    @patch("mysql_to_sheets.core.audit.log_action")
    @patch("mysql_to_sheets.api.audit_routes.export_audit_logs")
    @patch("mysql_to_sheets.api.audit_routes.get_audit_log_repository")
    def test_export_audit_logs(
        self, mock_get_repo, mock_export, mock_log_action, client
    ):
        """Test exporting audit logs."""
        from mysql_to_sheets.core.audit_export import ExportResult
        from mysql_to_sheets.models.audit_logs import AuditLog

        # The client fixture already injects a user with role="admin" via UserAuthMiddleware,
        # so we don't need to mock require_permission.
        # Note: We patch at the import location (audit_routes) not the source

        mock_repo = MagicMock()
        mock_repo.get_all.return_value = [
            AuditLog(
                id=1,
                organization_id=1,
                user_id=1,
                action="sync.completed",
                resource_type="config",
                resource_id="1",
                timestamp=datetime.now(timezone.utc),
                metadata={},
            ),
        ]
        mock_get_repo.return_value = mock_repo

        # Mock export function
        mock_export.return_value = ExportResult(
            format="csv",
            record_count=1,
        )

        response = client.get("/api/v1/audit/export")
        assert response.status_code == 200
        # CSV export
        assert "text/csv" in response.headers.get("content-type", "")


class TestRollbackRoutes:
    """Tests for /api/v1/snapshots/* and rollback endpoints."""

    @patch("mysql_to_sheets.api.rollback_routes.list_snapshots")
    def test_list_snapshots(self, mock_list_snapshots, client):
        """Test listing snapshots."""
        from mysql_to_sheets.models.snapshots import Snapshot

        mock_list_snapshots.return_value = [
            Snapshot(
                id=1,
                organization_id=1,
                sync_config_id=1,
                sheet_id="abc123",
                worksheet_name="Sheet1",
                created_at=datetime.now(timezone.utc),
                row_count=100,
                column_count=5,
                size_bytes=1024,
                checksum="abc",
                headers=["A", "B", "C"],
            ),
        ]

        response = client.get("/api/v1/snapshots")
        assert response.status_code == 200
        data = response.json()
        assert "snapshots" in data
        assert len(data["snapshots"]) == 1

    @patch("mysql_to_sheets.api.rollback_routes.create_snapshot")
    def test_create_snapshot(self, mock_create, client):
        """Test creating a snapshot."""
        from mysql_to_sheets.models.snapshots import Snapshot

        mock_create.return_value = Snapshot(
            id=1,
            organization_id=1,
            sync_config_id=1,
            sheet_id="abc123",
            worksheet_name="Sheet1",
            created_at=datetime.now(timezone.utc),
            row_count=150,
            column_count=5,
            size_bytes=2048,
            checksum="def",
            headers=["A", "B", "C"],
        )

        response = client.post(
            "/api/v1/snapshots",
            json={
                "sheet_id": "abc123",
                "worksheet_name": "Sheet1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["snapshot"]["row_count"] == 150

    @patch("mysql_to_sheets.api.rollback_routes.rollback_to_snapshot")
    @patch("mysql_to_sheets.api.rollback_routes.get_snapshot")
    @patch("mysql_to_sheets.api.rollback_routes.can_rollback")
    def test_rollback_to_snapshot(
        self, mock_can_rollback, mock_get_snapshot, mock_rollback, client
    ):
        """Test rolling back to a snapshot."""
        from mysql_to_sheets.core.rollback import RollbackResult
        from mysql_to_sheets.models.snapshots import Snapshot

        # Mock get_snapshot
        mock_get_snapshot.return_value = Snapshot(
            id=1,
            organization_id=1,
            sync_config_id=1,
            sheet_id="abc123",
            worksheet_name="Sheet1",
            created_at=datetime.now(timezone.utc),
            row_count=100,
            column_count=5,
            size_bytes=1024,
            checksum="abc",
            headers=["A", "B", "C"],
        )

        # Mock can_rollback
        mock_can_rollback.return_value = (True, "Can rollback")

        # Mock rollback
        mock_rollback.return_value = RollbackResult(
            success=True,
            snapshot_id=1,
            rows_restored=100,
            columns_restored=5,
            message="Rollback successful",
        )

        response = client.post(
            "/api/v1/snapshots/1/rollback",
            json={
                "create_backup": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestBillingWebhookRoutes:
    """Tests for /api/v1/billing/webhook endpoint."""

    @patch("mysql_to_sheets.api.billing_webhook_routes._process_billing_event")
    @patch("mysql_to_sheets.api.billing_webhook_routes._verify_signature")
    @patch("mysql_to_sheets.core.config.get_config")
    def test_billing_webhook_success(self, mock_config, mock_verify, mock_process, client):
        """Test processing billing webhook."""
        # Mock config
        mock_cfg = MagicMock()
        mock_cfg.billing_enabled = True
        mock_cfg.billing_webhook_secret = "test_secret"
        mock_config.return_value = mock_cfg

        mock_verify.return_value = True
        mock_process.return_value = "Processed"

        response = client.post(
            "/api/v1/billing/webhook",
            json={
                "event": "subscription.created",
                "data": {
                    "organization_id": 1,
                    "tier": "pro",
                },
            },
            headers={
                "X-Webhook-Signature": "sha256=abc123",
            },
        )
        assert response.status_code == 200

    def test_billing_webhook_invalid_signature(self, client):
        """Test billing webhook with invalid signature."""
        # Patch at the route module level where get_config is called
        with (
            patch("mysql_to_sheets.api.billing_webhook_routes.get_config") as mock_config,
            patch(
                "mysql_to_sheets.models.organizations.get_organization_repository"
            ) as mock_get_repo,
        ):
            # Mock config
            mock_cfg = MagicMock()
            mock_cfg.billing_enabled = True
            mock_cfg.billing_webhook_secret = "test_secret"
            mock_config.return_value = mock_cfg

            # Mock the org repository to avoid DB access (but it shouldn't be called if sig fails)
            mock_org = MagicMock()
            mock_org.id = 1
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = mock_org
            mock_get_repo.return_value = mock_repo

            # Send with obviously wrong signature
            payload = {
                "event": "subscription.created",
                "data": {
                    "organization_id": 1,
                },
            }

            # Use a clearly invalid signature
            response = client.post(
                "/api/v1/billing/webhook",
                json=payload,
                headers={
                    "X-Webhook-Signature": "totally_bogus_signature_123",
                },
            )
            # Should fail signature validation and return 401
            assert response.status_code == 401, (
                f"Expected 401, got {response.status_code}. Response: {response.json()}"
            )
