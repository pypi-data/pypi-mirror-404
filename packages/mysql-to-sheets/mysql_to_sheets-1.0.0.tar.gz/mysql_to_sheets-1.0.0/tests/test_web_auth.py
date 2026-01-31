"""Tests for auth blueprint (Flask web authentication)."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask


class TestAuthBlueprint:
    """Tests for authentication blueprint."""

    def setup_method(self):
        """Reset singletons before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()

    @pytest.fixture
    def app(self):
        """Create Flask test app with auth blueprint."""
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
    def mock_db_path(self):
        """Mock get_tenant_db_path."""
        with patch("mysql_to_sheets.web.blueprints.auth.get_tenant_db_path") as mock:
            mock.return_value = "/tmp/test.db"
            yield mock

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository."""
        with patch("mysql_to_sheets.models.users.get_user_repository") as mock:
            repo = MagicMock()
            mock.return_value = repo
            yield repo

    @pytest.fixture
    def mock_org_repo(self):
        """Mock organization repository."""
        with patch("mysql_to_sheets.models.organizations.get_organization_repository") as mock:
            repo = MagicMock()
            mock.return_value = repo
            yield repo

    @pytest.fixture
    def mock_rate_limiter(self):
        """Mock rate limiter."""
        with patch("mysql_to_sheets.web.blueprints.auth._auth_limiter") as mock:
            mock.is_allowed.return_value = True
            yield mock

    def test_login_page_renders_get(self, client):
        """Test login page renders on GET request."""
        with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/login")

            assert response.status_code == 200
            mock_render.assert_called_once()
            assert mock_render.call_args[0][0] == "login.html"

    def test_login_page_redirects_if_already_logged_in(self, client):
        """Test login page redirects to dashboard if already authenticated."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        response = client.get("/login")

        assert response.status_code == 302
        assert "/dashboard" in response.location or "/" in response.location

    def test_login_with_valid_credentials_succeeds(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_org_repo,
        mock_rate_limiter,
    ):
        """Test login with valid credentials sets session and redirects."""
        # Mock user
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.display_name = "Test User"
        user.role = "owner"
        user.organization_id = 1
        user.is_active = True
        user.password_hash = "hashed_password"
        user.force_password_change = False

        mock_user_repo.get_by_email_global.return_value = user

        # Mock organization
        org = MagicMock()
        org.id = 1
        org.name = "Test Org"
        org.is_active = True

        mock_org_repo.get_by_id.return_value = org

        with patch("mysql_to_sheets.core.auth.verify_password", return_value=True):
            response = client.post(
                "/login",
                data={
                    "email": "test@example.com",
                    "password": "correct_password",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/" in response.location

            # Verify session was set
            with client.session_transaction() as session:
                assert session.get("user_id") == 1
                assert session.get("email") == "test@example.com"
                assert session.get("organization_id") == 1

    def test_login_with_invalid_email_fails(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_rate_limiter,
    ):
        """Test login with invalid email shows error."""
        mock_user_repo.get_by_email_global.return_value = None

        with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.post(
                "/login",
                data={
                    "email": "nonexistent@example.com",
                    "password": "password",
                },
            )

            assert response.status_code == 200
            context = mock_render.call_args[1]
            assert "error" in context
            assert "Invalid" in context["error"]

    def test_login_with_invalid_password_fails(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_rate_limiter,
    ):
        """Test login with invalid password shows error."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.organization_id = 1
        user.password_hash = "hashed_password"

        mock_user_repo.get_by_email_global.return_value = user

        with patch("mysql_to_sheets.core.auth.verify_password", return_value=False):
            with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.post(
                    "/login",
                    data={
                        "email": "test@example.com",
                        "password": "wrong_password",
                    },
                )

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert "error" in context

    def test_login_with_inactive_user_fails(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_rate_limiter,
    ):
        """Test login with inactive user account fails."""
        user = MagicMock()
        user.is_active = False

        mock_user_repo.get_by_email_global.return_value = user

        with patch("mysql_to_sheets.core.auth.verify_password", return_value=True):
            with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.post(
                    "/login",
                    data={
                        "email": "test@example.com",
                        "password": "password",
                    },
                )

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert "deactivated" in context["error"].lower()

    def test_login_rate_limit_enforced(
        self,
        client,
        mock_db_path,
    ):
        """Test login rate limiting prevents brute force."""
        with patch("mysql_to_sheets.web.blueprints.auth._auth_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = False

            with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.post(
                    "/login",
                    data={
                        "email": "test@example.com",
                        "password": "password",
                    },
                )

                assert response.status_code == 429
                context = mock_render.call_args[1]
                assert "Too many" in context["error"]

    def test_login_with_force_password_change_redirects(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_org_repo,
        mock_rate_limiter,
    ):
        """Test login with force_password_change redirects to change password page."""
        user = MagicMock()
        user.id = 1
        user.email = "test@example.com"
        user.display_name = "Test User"
        user.role = "owner"
        user.organization_id = 1
        user.is_active = True
        user.password_hash = "hashed"
        user.force_password_change = True

        mock_user_repo.get_by_email_global.return_value = user

        org = MagicMock()
        org.id = 1
        org.name = "Test Org"
        org.is_active = True

        mock_org_repo.get_by_id.return_value = org

        with patch("mysql_to_sheets.core.auth.verify_password", return_value=True):
            response = client.post(
                "/login",
                data={
                    "email": "test@example.com",
                    "password": "password",
                },
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert "/change-password" in response.location

    def test_register_page_renders_get(self, client):
        """Test registration page renders on GET request."""
        with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/register")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "register.html"

    def test_register_creates_new_organization_and_user(
        self,
        client,
        mock_db_path,
        mock_user_repo,
        mock_org_repo,
        mock_rate_limiter,
    ):
        """Test registration creates new organization and owner user."""
        org = MagicMock()
        org.id = 1
        org.name = "New Org"
        org.slug = "new-org"

        mock_org_repo.create.return_value = org
        mock_org_repo.get_by_slug.return_value = None

        user = MagicMock()
        user.id = 1

        mock_user_repo.create.return_value = user
        mock_user_repo.get_by_email_global.return_value = None

        with patch("mysql_to_sheets.core.auth.hash_password", return_value="hashed"):
            with patch(
                "mysql_to_sheets.core.auth.validate_password_strength", return_value=(True, [])
            ):
                with patch("mysql_to_sheets.core.trial.start_trial"):
                    response = client.post(
                        "/register",
                        data={
                            "org_name": "New Org",
                            "display_name": "John Doe",
                            "email": "john@example.com",
                            "password": "SecureP@ss123",
                            "confirm_password": "SecureP@ss123",
                        },
                        follow_redirects=False,
                    )

                    assert response.status_code == 302
                    assert "/login" in response.location

                    mock_org_repo.create.assert_called_once()
                    mock_user_repo.create.assert_called_once()

    def test_register_validates_password_strength(
        self,
        client,
        mock_db_path,
        mock_rate_limiter,
    ):
        """Test registration validates password strength."""
        with patch("mysql_to_sheets.core.auth.validate_password_strength") as mock_validate:
            mock_validate.return_value = (False, ["Password too weak"])

            with patch("mysql_to_sheets.models.organizations.get_organization_repository"):
                with patch("mysql_to_sheets.models.users.get_user_repository"):
                    with patch(
                        "mysql_to_sheets.web.blueprints.auth.render_template"
                    ) as mock_render:
                        mock_render.return_value = "rendered"

                        response = client.post(
                            "/register",
                            data={
                                "org_name": "New Org",
                                "display_name": "John Doe",
                                "email": "john@example.com",
                                "password": "weak",
                                "confirm_password": "weak",
                            },
                        )

                        assert response.status_code == 200
                        context = mock_render.call_args[1]
                        assert "errors" in context

    def test_register_rejects_duplicate_organization(
        self,
        client,
        mock_db_path,
        mock_org_repo,
        mock_rate_limiter,
    ):
        """Test registration rejects duplicate organization slug."""
        existing_org = MagicMock()
        mock_org_repo.get_by_slug.return_value = existing_org

        with patch("mysql_to_sheets.models.users.get_user_repository"):
            with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.post(
                    "/register",
                    data={
                        "org_name": "Existing Org",
                        "display_name": "John Doe",
                        "email": "john@example.com",
                        "password": "SecureP@ss123",
                        "confirm_password": "SecureP@ss123",
                    },
                )

                assert response.status_code == 200
                context = mock_render.call_args[1]
                assert "already exists" in context["error"]

    def test_register_rejects_duplicate_email(
        self,
        client,
        mock_db_path,
        mock_org_repo,
        mock_user_repo,
        mock_rate_limiter,
    ):
        """Test registration rejects duplicate email."""
        mock_org_repo.get_by_slug.return_value = None

        existing_user = MagicMock()
        mock_user_repo.get_by_email_global.return_value = existing_user

        with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.post(
                "/register",
                data={
                    "org_name": "New Org",
                    "display_name": "John Doe",
                    "email": "existing@example.com",
                    "password": "SecureP@ss123",
                    "confirm_password": "SecureP@ss123",
                },
            )

            assert response.status_code == 200
            context = mock_render.call_args[1]
            assert "already exists" in context["error"]

    def test_register_rate_limit_enforced(
        self,
        client,
        mock_db_path,
    ):
        """Test registration rate limiting."""
        with patch("mysql_to_sheets.web.blueprints.auth._auth_limiter") as mock_limiter:
            mock_limiter.is_allowed.return_value = False

            with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
                mock_render.return_value = "rendered"

                response = client.post(
                    "/register",
                    data={
                        "org_name": "New Org",
                        "display_name": "John Doe",
                        "email": "john@example.com",
                        "password": "SecureP@ss123",
                        "confirm_password": "SecureP@ss123",
                    },
                )

                assert response.status_code == 429

    def test_change_password_requires_login(self, client):
        """Test change password page requires authentication."""
        response = client.get("/change-password")

        assert response.status_code == 302
        assert "/login" in response.location

    def test_change_password_renders_for_authenticated_user(self, client):
        """Test change password page renders for authenticated user."""
        with client.session_transaction() as session:
            session["user_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.auth.render_template") as mock_render:
            mock_render.return_value = "rendered"

            response = client.get("/change-password")

            assert response.status_code == 200
            assert mock_render.call_args[0][0] == "change_password.html"

    def test_change_password_updates_password(
        self,
        client,
        mock_db_path,
        mock_user_repo,
    ):
        """Test change password updates user password."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["force_password_change"] = False

        user = MagicMock()
        user.id = 1
        user.password_hash = "old_hash"

        mock_user_repo.get_by_id.return_value = user

        with patch("mysql_to_sheets.core.auth.verify_password", return_value=True):
            with patch("mysql_to_sheets.core.auth.hash_password", return_value="new_hash"):
                with patch(
                    "mysql_to_sheets.core.auth.validate_password_strength", return_value=(True, [])
                ):
                    response = client.post(
                        "/change-password",
                        data={
                            "current_password": "old_password",
                            "new_password": "NewSecure@123",
                            "confirm_password": "NewSecure@123",
                        },
                        follow_redirects=False,
                    )

                    assert response.status_code == 302
                    mock_user_repo.update_password.assert_called_once()

    def test_change_password_skips_current_check_for_forced(
        self,
        client,
        mock_db_path,
        mock_user_repo,
    ):
        """Test forced password change skips current password verification."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1
            session["force_password_change"] = True

        user = MagicMock()
        user.id = 1

        mock_user_repo.get_by_id.return_value = user

        with patch("mysql_to_sheets.core.auth.hash_password", return_value="new_hash"):
            with patch(
                "mysql_to_sheets.core.auth.validate_password_strength", return_value=(True, [])
            ):
                with patch("mysql_to_sheets.core.auth.verify_password") as mock_verify:
                    response = client.post(
                        "/change-password",
                        data={
                            "new_password": "NewSecure@123",
                            "confirm_password": "NewSecure@123",
                        },
                        follow_redirects=False,
                    )

                    # Should not verify current password
                    mock_verify.assert_not_called()
                    mock_user_repo.update_password.assert_called_once()

    def test_logout_clears_session(self, client):
        """Test logout clears session and redirects to login."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["email"] = "test@example.com"
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.auth.get_tenant_db_path"):
            response = client.get("/logout")

            assert response.status_code == 302
            assert "/login" in response.location

            # Verify session was cleared
            with client.session_transaction() as session:
                assert "user_id" not in session

    def test_logout_logs_audit_event(
        self,
        client,
        mock_db_path,
    ):
        """Test logout logs audit event."""
        with client.session_transaction() as session:
            session["user_id"] = 1
            session["organization_id"] = 1

        with patch("mysql_to_sheets.web.blueprints.auth._log_auth_audit") as mock_audit:
            response = client.get("/logout")

            mock_audit.assert_called_once()
            call_args = mock_audit.call_args[1]
            assert call_args["event"] == "logout"
            assert call_args["user_id"] == 1
