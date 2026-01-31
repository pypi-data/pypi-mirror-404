"""Tests for dashboard blueprint (Flask web main dashboard)."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from mysql_to_sheets import __version__


class TestDashboardBlueprint:
    """Tests for main dashboard blueprint."""

    def setup_method(self):
        """Reset singletons before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @pytest.fixture
    def app(self):
        """Create Flask test app with dashboard blueprint."""
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["WTF_CSRF_ENABLED"] = False

        from mysql_to_sheets.web.blueprints.auth import auth_bp
        from mysql_to_sheets.web.blueprints.dashboard import dashboard_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)

        return app

    @pytest.fixture
    def client(self, app):
        """Create Flask test client."""
        return app.test_client()

    @pytest.fixture
    def mock_config(self):
        """Mock get_config."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_config") as mock:
            config = MagicMock()
            config.google_sheet_id = "test_sheet_123"
            config.google_worksheet_name = "Sheet1"
            config.sql_query = "SELECT * FROM users"
            config.db_type = "mysql"
            config.db_host = "localhost"
            config.db_name = "test_db"
            config.service_account_file = "/tmp/service_account.json"
            mock.return_value = config
            yield config

    @pytest.fixture
    def mock_current_user(self):
        """Mock get_current_user helper."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_current_user") as mock:
            mock.return_value = {
                "id": 1,
                "email": "test@example.com",
                "organization_id": 1,
                "role": "owner",
            }
            yield mock

    @pytest.fixture
    def mock_db_path(self):
        """Mock get_tenant_db_path."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_tenant_db_path") as mock:
            mock.return_value = "/tmp/test.db"
            yield mock

    @pytest.fixture
    def mock_sync_history(self):
        """Mock sync_history."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.sync_history") as mock:
            mock.get_all.return_value = [
                {
                    "id": 1,
                    "timestamp": "2024-01-01T10:00:00",
                    "success": True,
                    "rows_synced": 100,
                },
            ]
            yield mock

    def test_index_renders_main_dashboard(
        self,
        client,
        mock_config,
        mock_sync_history,
    ):
        """Test index page renders main dashboard."""
        # Set up authenticated session
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"

        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/")

            assert response.status_code == 200
            mock_render.assert_called_once()
            assert mock_render.call_args[0][0] == "index.html"

            # Verify context data
            context = mock_render.call_args[1]
            assert context["version"] == __version__
            assert "config" in context
            assert context["config"]["sheet_id"] == "test_sheet_123"

    def test_index_includes_sync_history(
        self,
        client,
        mock_config,
        mock_sync_history,
    ):
        """Test index page includes sync history."""
        # Set up authenticated session
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"

        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            client.get("/")

            context = mock_render.call_args[1]
            assert "history" in context
            assert len(context["history"]) == 1

    def test_history_page_renders(
        self,
        client,
        mock_sync_history,
    ):
        """Test history page renders."""
        # Set up authenticated session
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"

        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/history")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "history.html"

    def test_dismiss_banner_clears_first_run_session(self, client):
        """Test dismiss banner clears first run flag from session."""
        with client.session_transaction() as session:
            session["_first_run"] = True

        response = client.post("/dismiss-banner")

        assert response.status_code == 302

        with client.session_transaction() as session:
            assert "_first_run" not in session

    def test_setup_page_renders(self, client):
        """Test setup wizard page renders."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path") as mock_env:
            with patch(
                "mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path"
            ) as mock_sa:
                with patch("mysql_to_sheets.web.blueprints.dashboard.get_config_dir") as mock_dir:
                    mock_env.return_value = MagicMock(exists=MagicMock(return_value=False))
                    mock_sa.return_value = MagicMock(exists=MagicMock(return_value=False))
                    mock_dir.return_value = "/tmp/config"

                    with patch(
                        "mysql_to_sheets.web.blueprints.dashboard.render_template"
                    ) as mock_render:
                        mock_render.return_value = "rendered"

                        response = client.get("/setup")

                        assert response.status_code == 200
                        assert mock_render.call_args[0][0] == "setup.html"

    def test_schedules_page_renders(self, client):
        """Test schedules page renders with jobs."""
        with patch("mysql_to_sheets.core.scheduler.get_scheduler_service") as mock_sched:
            service = MagicMock()
            job = MagicMock()
            job.to_dict.return_value = {
                "id": 1,
                "name": "daily-sync",
                "enabled": True,
            }
            service.get_all_jobs.return_value = [job]
            service.get_status.return_value = "running"
            mock_sched.return_value = service

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/schedules")

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert len(context["jobs"]) == 1

    def test_users_page_requires_login(self, client):
        """Test users page requires authentication."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_current_user", return_value=None):
            response = client.get("/users")

            assert response.status_code == 302
            assert "/login" in response.location

    def test_users_page_renders_for_authenticated(
        self,
        client,
        mock_current_user,
        mock_db_path,
    ):
        """Test users page renders for authenticated user."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.models.users.get_user_repository") as mock_repo:
            repo = MagicMock()
            user = MagicMock()
            user.to_dict.return_value = {
                "id": 1,
                "email": "test@example.com",
                "role": "owner",
            }
            repo.get_all.return_value = [user]
            mock_repo.return_value = repo

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/users")

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert len(context["users"]) == 1

    def test_configs_page_requires_login(self, client):
        """Test configs page requires authentication."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_current_user", return_value=None):
            response = client.get("/configs")

            assert response.status_code == 302

    def test_configs_page_renders_configs_list(
        self,
        client,
        mock_current_user,
        mock_db_path,
    ):
        """Test configs page renders list of sync configurations."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.models.sync_configs.get_sync_config_repository") as mock_repo:
            repo = MagicMock()
            config = MagicMock()
            config.to_dict.return_value = {
                "id": 1,
                "name": "Daily Sales Sync",
                "sheet_id": "abc123",
            }
            repo.get_all.return_value = [config]
            mock_repo.return_value = repo

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/configs")

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert len(context["configs"]) == 1

    def test_webhooks_page_requires_admin(
        self,
        client,
        mock_db_path,
    ):
        """Test webhooks page requires admin role."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "viewer"  # Not admin

        with patch("mysql_to_sheets.web.blueprints.dashboard.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "organization_id": 1,
                "role": "viewer",  # Not admin
            }

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/webhooks")

                assert response.status_code == 403

    def test_webhooks_page_renders_for_admin(
        self,
        client,
        mock_current_user,
        mock_db_path,
    ):
        """Test webhooks page renders for admin users."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "owner"  # Admin role

        with patch("mysql_to_sheets.models.webhooks.get_webhook_repository") as mock_repo:
            repo = MagicMock()
            webhook = MagicMock()
            webhook.to_dict.return_value = {
                "id": 1,
                "url": "https://example.com/hook",
                "events": ["sync.completed"],
            }
            repo.get_all_subscriptions.return_value = [webhook]
            mock_repo.return_value = repo

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/webhooks")

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert len(context["webhooks"]) == 1

    def test_audit_page_requires_admin(
        self,
        client,
        mock_db_path,
    ):
        """Test audit page requires admin role."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["role"] = "operator"  # Not admin

        with patch("mysql_to_sheets.web.blueprints.dashboard.get_current_user") as mock_user:
            mock_user.return_value = {
                "id": 1,
                "organization_id": 1,
                "role": "operator",
            }

            with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.get("/audit")

                assert response.status_code == 403

    def test_jobs_page_renders(
        self,
        client,
        mock_current_user,
    ):
        """Test jobs page renders."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/jobs")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "jobs.html"

    def test_snapshots_page_renders(
        self,
        client,
        mock_current_user,
    ):
        """Test snapshots page renders."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/snapshots")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "snapshots.html"

    def test_favorites_page_renders_with_queries_and_sheets(
        self,
        client,
        mock_current_user,
        mock_db_path,
    ):
        """Test favorites page renders saved queries and sheets."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch(
            "mysql_to_sheets.models.favorites.get_favorite_query_repository"
        ) as mock_query_repo:
            with patch(
                "mysql_to_sheets.models.favorites.get_favorite_sheet_repository"
            ) as mock_sheet_repo:
                query_repo = MagicMock()
                sheet_repo = MagicMock()

                query = MagicMock()
                query.to_dict.return_value = {"id": 1, "name": "Daily Query"}
                query_repo.get_all.return_value = [query]

                sheet = MagicMock()
                sheet.to_dict.return_value = {"id": 1, "name": "Sales Sheet"}
                sheet_repo.get_all.return_value = [sheet]

                mock_query_repo.return_value = query_repo
                mock_sheet_repo.return_value = sheet_repo

                with patch(
                    "mysql_to_sheets.web.blueprints.dashboard.render_template"
                ) as mock_render:
                    mock_render.return_value = "rendered"

                    response = client.get("/favorites")

                    assert response.status_code == 200
                    context = mock_render.call_args[1]
                    assert len(context["queries"]) == 1
                    assert len(context["sheets"]) == 1

    def test_worksheets_page_renders(
        self,
        client,
        mock_config,
    ):
        """Test worksheets management page renders."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/worksheets")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "worksheets.html"

    def test_api_setup_status_returns_status(self, client):
        """Test /api/setup/status returns setup status."""
        with patch("mysql_to_sheets.web.blueprints.dashboard.get_default_env_path") as mock_env:
            with patch(
                "mysql_to_sheets.web.blueprints.dashboard.get_default_service_account_path"
            ) as mock_sa:
                env_path = MagicMock()
                env_path.exists.return_value = True
                env_path.read_text.return_value = "DB_HOST=localhost\nDB_USER=user"

                sa_path = MagicMock()
                sa_path.exists.return_value = True

                mock_env.return_value = env_path
                mock_sa.return_value = sa_path

                response = client.get("/api/setup/status")

                assert response.status_code == 200
                data = response.get_json()
                assert data["env_exists"] is True
                assert data["service_account_exists"] is True

    def test_api_setup_test_db_validates_connection(self, client):
        """Test /api/setup/test-db validates database connection."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.core.database.get_connection") as mock_conn:
            conn = MagicMock()
            conn.__enter__ = MagicMock(return_value=conn)
            conn.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value = None

            mock_conn.return_value = conn

            response = client.post(
                "/api/setup/test-db",
                json={
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "test",
                    "db_password": "pass",
                    "db_name": "testdb",
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True

    def test_api_setup_test_db_handles_errors(self, client):
        """Test /api/setup/test-db handles connection errors."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.core.database.get_connection") as mock_conn:
            mock_conn.side_effect = Exception("Connection refused")

            response = client.post(
                "/api/setup/test-db",
                json={
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is False
            assert "refused" in data["message"].lower()

    def test_api_setup_test_sheets_validates_access(self, client):
        """Test /api/setup/test-sheets validates Google Sheets access."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("google.oauth2.service_account.Credentials") as mock_creds:
            with patch("gspread.authorize") as mock_authorize:
                creds = MagicMock()
                mock_creds.from_service_account_info.return_value = creds

                client_obj = MagicMock()
                spreadsheet = MagicMock()
                spreadsheet.title = "Test Sheet"

                mock_authorize.return_value = client_obj
                client_obj.open_by_key.return_value = spreadsheet

                response = client.post(
                    "/api/setup/test-sheets",
                    json={
                        "service_account": {"type": "service_account"},
                        "sheet_id": "abc123",
                        "worksheet": "Sheet1",
                    },
                )

                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
                assert data["sheet_title"] == "Test Sheet"

    def test_api_setup_preview_query_returns_results(self, client):
        """Test /api/setup/preview-query returns query results."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.core.database.get_connection") as mock_conn:
            conn = MagicMock()
            conn.__enter__ = MagicMock(return_value=conn)
            conn.__exit__ = MagicMock(return_value=False)
            mock_result = MagicMock()
            mock_result.headers = ["id", "name"]
            mock_result.rows = [[1, "Alice"], [2, "Bob"]]
            conn.execute.return_value = mock_result

            mock_conn.return_value = conn

            response = client.post(
                "/api/setup/preview-query",
                json={
                    "sql_query": "SELECT id, name FROM users",
                    "db_type": "mysql",
                    "db_host": "localhost",
                    "db_port": 3306,
                    "db_user": "test",
                    "db_password": "pass",
                    "db_name": "testdb",
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["row_count"] == 2
            assert data["headers"] == ["id", "name"]

    def test_api_setup_parse_uri_parses_connection_string(self, client):
        """Test /api/setup/parse-uri parses database URI."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.core.config.parse_database_uri") as mock_parse:
            mock_parse.return_value = {
                "db_type": "postgres",
                "db_host": "dbhost",
                "db_port": 5432,
                "db_user": "user",
                "db_password": "pass",
                "db_name": "mydb",
            }

            response = client.post(
                "/api/setup/parse-uri",
                json={
                    "uri": "postgres://user:pass@dbhost:5432/mydb",
                },
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert data["db_type"] == "postgres"
            assert data["db_port"] == 5432

    def test_api_setup_demo_creates_demo_database(self, client):
        """Test /api/setup/demo creates demo database."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.core.demo.create_demo_database") as mock_create:
            with patch("mysql_to_sheets.core.demo.get_demo_queries") as mock_queries:
                mock_create.return_value = "/tmp/demo.db"
                mock_queries.return_value = ["SELECT * FROM sales"]

                response = client.post("/api/setup/demo")

                assert response.status_code == 200
                data = response.get_json()
                assert data["success"] is True
                assert data["db_type"] == "sqlite"
                assert "/tmp/demo.db" in data["db_name"]
