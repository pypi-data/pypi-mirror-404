"""Tests for tier_bp module (Flask web tier status pages)."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from mysql_to_sheets import __version__


class TestTierBlueprint:
    """Tests for tier status blueprint."""

    def setup_method(self):
        """Reset singletons before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @pytest.fixture
    def app(self):
        """Create Flask test app with tier blueprint."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["WTF_CSRF_ENABLED"] = False

        from mysql_to_sheets.web.blueprints.auth import auth_bp
        from mysql_to_sheets.web.blueprints.dashboard import dashboard_bp
        from mysql_to_sheets.web.blueprints.tier_bp import tier_api_bp, tier_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(tier_bp)
        app.register_blueprint(tier_api_bp)

        return app

    @pytest.fixture
    def client(self, app):
        """Create Flask test client."""
        return app.test_client()

    @pytest.fixture
    def mock_current_user(self):
        """Mock get_current_user helper."""
        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_current_user") as mock:
            mock.return_value = {
                "id": 1,
                "email": "test@example.com",
                "organization_id": 1,
                "organization_tier": "pro",
                "role": "owner",
            }
            yield mock

    @pytest.fixture
    def mock_db_path(self):
        """Mock get_tenant_db_path."""
        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_tenant_db_path") as mock:
            mock.return_value = "/tmp/test.db"
            yield mock

    @pytest.fixture
    def mock_repos(self):
        """Mock all repository factories."""
        with (
            patch("mysql_to_sheets.models.sync_configs.get_sync_config_repository") as config_repo,
            patch("mysql_to_sheets.models.users.get_user_repository") as user_repo,
            patch("mysql_to_sheets.models.webhooks.get_webhook_repository") as webhook_repo,
        ):
            # Mock config repository
            mock_config_repo = MagicMock()
            mock_config_repo.get_all.return_value = [MagicMock(), MagicMock()]  # 2 configs
            mock_config_repo.count.return_value = 2  # For _get_usage_counts
            config_repo.return_value = mock_config_repo

            # Mock user repository
            mock_user_repo = MagicMock()
            mock_user_repo.get_all.return_value = [MagicMock()]  # 1 user
            mock_user_repo.count.return_value = 1  # For _get_usage_counts
            user_repo.return_value = mock_user_repo

            # Mock webhook repository
            mock_webhook_repo = MagicMock()
            mock_webhook_repo.get_all_subscriptions.return_value = []  # 0 webhooks
            mock_webhook_repo.count_subscriptions.return_value = 0  # For _get_usage_counts
            webhook_repo.return_value = mock_webhook_repo

            yield {
                "config": mock_config_repo,
                "user": mock_user_repo,
                "webhook": mock_webhook_repo,
            }

    @pytest.fixture
    def mock_scheduler(self):
        """Mock scheduler service."""
        with patch("mysql_to_sheets.core.scheduler.get_scheduler_service") as mock:
            service = MagicMock()
            service.get_all_jobs.return_value = [
                MagicMock(),
                MagicMock(),
                MagicMock(),
            ]  # 3 schedules
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_trial_status(self):
        """Mock check_trial_status."""
        with patch("mysql_to_sheets.web.blueprints.tier_bp.check_trial_status") as mock:
            trial_info = MagicMock()
            trial_info.status = MagicMock()
            trial_info.status.name = "INACTIVE"
            trial_info.days_remaining = 0
            mock.return_value = trial_info
            yield mock

    def test_tier_status_redirects_when_not_logged_in(self, client):
        """Test tier status page redirects to login when not authenticated."""
        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_current_user", return_value=None):
            response = client.get("/tier")
            assert response.status_code == 302
            assert "/login" in response.location

    def test_tier_status_renders_for_authenticated_user(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
        mock_trial_status,
    ):
        """Test tier status page renders for authenticated user."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/tier")

            assert response.status_code == 200
            mock_render.assert_called_once()

            # Verify template name
            call_args = mock_render.call_args
            assert call_args[0][0] == "tier.html"

            # Verify context data
            context = call_args[1]
            assert context["version"] == __version__
            assert context["current_tier"] == "pro"
            assert context["tier_name"] == "Pro"
            assert "limits" in context
            assert "usage" in context
            assert "features" in context

    def test_tier_status_calculates_usage(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
        mock_trial_status,
    ):
        """Test tier status page calculates usage counts."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
            mock_render.return_value = "rendered"

            client.get("/tier")

            context = mock_render.call_args[1]
            usage = context["usage"]

            assert usage["configs"] == 2
            assert usage["users"] == 1
            assert usage["webhooks"] == 0
            assert usage["schedules"] == 3

    def test_tier_status_handles_invalid_tier(
        self,
        client,
        mock_db_path,
        mock_repos,
        mock_scheduler,
        mock_trial_status,
    ):
        """Test tier status page defaults to FREE for invalid tier."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "organization_id": 1,
                "organization_tier": "invalid_tier",
            }

            with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
                mock_render.return_value = "rendered"

                client.get("/tier")

                context = mock_render.call_args[1]
                assert context["current_tier"] == "free"

    def test_tier_status_shows_trial_info(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
    ):
        """Test tier status page shows trial information."""
        from mysql_to_sheets.core.trial import TrialStatus

        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.check_trial_status") as mock_trial:
            trial_info = MagicMock()
            trial_info.status = TrialStatus.ACTIVE
            trial_info.days_remaining = 7
            mock_trial.return_value = trial_info

            with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
                mock_render.return_value = "rendered"

                client.get("/tier")

                context = mock_render.call_args[1]
                assert context["billing_status"] == "trialing"
                assert context["trial_days_remaining"] == 7

    def test_tier_status_handles_repo_errors(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_trial_status,
    ):
        """Test tier status page handles repository errors gracefully."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.models.sync_configs.get_sync_config_repository") as mock_repo:
            mock_repo.side_effect = RuntimeError("Database error")

            with patch("mysql_to_sheets.core.scheduler.get_scheduler_service") as mock_sched:
                mock_sched.return_value.get_all_jobs.return_value = []

                with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
                    mock_render.return_value = "rendered"

                    client.get("/tier")

                    # Should still render, with usage counts at 0
                    context = mock_render.call_args[1]
                    assert context["usage"]["configs"] == 0

    def test_upgrade_page_renders(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_trial_status,
    ):
        """Test upgrade page renders with pricing plans."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_config") as mock_config:
            config = MagicMock()
            config.billing_portal_url = "https://billing.example.com"
            mock_config.return_value = config

            with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/upgrade")

                assert response.status_code == 200
                call_args = mock_render.call_args
                assert call_args[0][0] == "upgrade.html"
                assert call_args[1]["billing_portal_url"] == "https://billing.example.com"

    def test_api_tier_status_requires_auth(self, client):
        """Test /api/tier/status requires authentication."""
        # Don't set session - should fail auth
        response = client.get("/api/tier/status")

        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert "Authentication required" in data["error"]

    def test_api_tier_status_returns_data(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
    ):
        """Test /api/tier/status returns tier data."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        response = client.get("/api/tier/status")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["tier"] == "pro"
        assert data["tier_name"] == "Pro"
        assert "limits" in data
        assert "usage" in data

    def test_api_tier_status_handles_missing_user(
        self,
        client,
        mock_db_path,
    ):
        """Test /api/tier/status handles missing user gracefully."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_current_user", return_value=None):
            response = client.get("/api/tier/status")

            assert response.status_code == 404
            data = response.get_json()
            assert data["success"] is False
            assert "User not found" in data["error"]

    def test_api_tier_usage_returns_counts(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
    ):
        """Test /api/tier/usage returns usage counts."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        response = client.get("/api/tier/usage")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["usage"]["configs"] == 2
        assert data["usage"]["users"] == 1
        assert data["usage"]["schedules"] == 3

    def test_api_tier_features_returns_availability(
        self,
        client,
        mock_current_user,
    ):
        """Test /api/tier/features returns feature availability."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        response = client.get("/api/tier/features")

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["tier"] == "pro"
        assert "features" in data
        assert isinstance(data["features"], list)

    def test_api_tier_features_marks_available_features(
        self,
        client,
        mock_current_user,
    ):
        """Test /api/tier/features marks features as available based on tier."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        response = client.get("/api/tier/features")
        data = response.get_json()

        features = data["features"]

        # PRO tier should have scheduler available
        scheduler_features = [f for f in features if f["key"] == "scheduler"]
        if scheduler_features:
            assert scheduler_features[0]["available"] is True

        # Should have some features marked as unavailable (enterprise-only)
        unavailable = [f for f in features if not f["available"]]
        assert len(unavailable) > 0

    def test_usage_percentages_calculated_correctly(
        self,
        client,
        mock_current_user,
        mock_db_path,
        mock_repos,
        mock_scheduler,
        mock_trial_status,
    ):
        """Test usage percentages are calculated correctly."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
            mock_render.return_value = "rendered"

            client.get("/tier")

            context = mock_render.call_args[1]
            percentages = context["usage_percentages"]

            # PRO tier has max_configs=10, usage=2 => 20%
            assert percentages["configs"] == pytest.approx(20.0)

            # PRO tier has max_users=1, usage=1 => 100%
            assert percentages["users"] == pytest.approx(100.0)

    def test_unlimited_resources_show_none_percentage(
        self,
        client,
        mock_db_path,
        mock_repos,
        mock_scheduler,
        mock_trial_status,
    ):
        """Test unlimited resources show None for percentage."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.tier_bp.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "organization_id": 1,
                "organization_tier": "enterprise",  # Unlimited configs
            }

            with patch("mysql_to_sheets.web.blueprints.tier_bp.render_template") as mock_render:
                mock_render.return_value = "rendered"

                client.get("/tier")

                context = mock_render.call_args[1]
                percentages = context["usage_percentages"]

                # ENTERPRISE tier has unlimited configs
                assert percentages["configs"] is None

    def test_feature_availability_grouped_by_category(
        self,
        client,
        mock_current_user,
    ):
        """Test features are grouped by category."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        response = client.get("/api/tier/features")
        data = response.get_json()

        features = data["features"]
        categories = {f["category"] for f in features}

        # Should have multiple categories
        assert "Core" in categories or "Automation" in categories
        assert len(categories) > 1
