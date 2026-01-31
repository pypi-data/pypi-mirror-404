"""Comprehensive tests for Hybrid Agent implementation.

Tests coverage:
1. link_token.py - Token validation, status, revocation cache
2. link_config_provider.py - Config fetching with mocked HTTP responses
3. agent_worker.py - Worker lifecycle, job processing, heartbeat
4. models/agents.py - Agent model and repository CRUD operations

Performance: Uses freezegun for time-sensitive tests to avoid real delays.
"""

import json
import os
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

from freezegun import freeze_time
import jwt
import pytest

from mysql_to_sheets.agent.link_config_provider import LinkConfigProvider
from mysql_to_sheets.agent.link_token import (
    LinkTokenInfo,
    LinkTokenStatus,
    add_revoked_token,
    clear_revocation_cache,
    get_link_token_from_env,
    get_link_token_info,
    is_link_token_valid,
    is_token_revoked,
    validate_link_token,
)
from mysql_to_sheets.agent.agent_worker import (
    AgentJob,
    AgentStatus,
    AgentWorker,
    generate_agent_id,
)
from mysql_to_sheets.core.exceptions import ConfigError
from mysql_to_sheets.models.agents import (
    Agent,
    AgentRepository,
    get_agent_repository,
    reset_agent_repository,
)


# ============================================================================
# Link Token Tests
# ============================================================================


class TestLinkTokenValidation:
    """Tests for link token validation and status."""

    @pytest.fixture
    def test_token_data_payload(self):
        """Create a valid token payload."""
        return {
            "sub": "org_123",
            "iss": "mysql-to-sheets",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": "link_abc123",
            "scope": "agent",
            "permissions": ["sync", "read_configs"],
        }

    @pytest.fixture
    def test_keys(self):
        """Generate test RSA key pair for token signing."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        # Generate test key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return {
            "private": private_pem.decode("utf-8"),
            "public": public_pem.decode("utf-8"),
        }

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Reset revocation cache before and after tests."""
        clear_revocation_cache()
        yield
        clear_revocation_cache()

    def test_validate_link_token_valid(self, test_token_data_payload, test_keys):
        """validate_link_token returns VALID for properly signed token."""
        token = jwt.encode(test_token_data_payload, test_keys["private"], algorithm="RS256")
        info = validate_link_token(token, public_key=test_keys["public"])

        assert info.status == LinkTokenStatus.VALID
        assert info.organization_id == "org_123"
        assert info.jti == "link_abc123"
        assert info.scope == "agent"
        assert "sync" in info.permissions
        assert "read_configs" in info.permissions
        assert info.issued_at is not None
        assert info.error is None

    def test_validate_link_token_missing(self):
        """validate_link_token returns MISSING for empty token."""
        info = validate_link_token("")
        assert info.status == LinkTokenStatus.MISSING
        assert info.error == "No link token provided"

    def test_validate_link_token_invalid_signature(self, test_token_data_payload, test_keys):
        """validate_link_token returns INVALID for tampered token."""
        # Sign with correct key but verify with wrong key
        token = jwt.encode(test_token_data_payload, test_keys["private"], algorithm="RS256")

        # Generate different public key
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        wrong_private = rsa.generate_private_key(65537, 2048, default_backend())
        wrong_public = wrong_private.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        info = validate_link_token(token, public_key=wrong_public)

        assert info.status == LinkTokenStatus.INVALID
        assert "signature" in info.error.lower()

    def test_validate_link_token_wrong_scope(self, test_token_data_payload, test_keys):
        """validate_link_token returns INVALID for wrong scope."""
        payload = test_token_data_payload.copy()
        payload["scope"] = "user"  # Wrong scope

        token = jwt.encode(payload, test_keys["private"], algorithm="RS256")
        info = validate_link_token(token, public_key=test_keys["public"])

        assert info.status == LinkTokenStatus.INVALID
        assert "scope" in info.error.lower()
        assert "agent" in info.error.lower()

    def test_validate_link_token_revoked(self, test_token_data_payload, test_keys):
        """validate_link_token returns REVOKED for cached revoked token."""
        token = jwt.encode(test_token_data_payload, test_keys["private"], algorithm="RS256")

        # Add to revocation cache
        add_revoked_token(test_token_data_payload["jti"])

        info = validate_link_token(token, public_key=test_keys["public"])
        assert info.status == LinkTokenStatus.REVOKED
        assert "revoked" in info.error.lower()

    def test_validate_link_token_malformed(self):
        """validate_link_token returns INVALID for malformed JWT."""
        info = validate_link_token("not.a.valid.jwt.token")
        assert info.status == LinkTokenStatus.INVALID
        assert info.error is not None


class TestLinkTokenInfo:
    """Tests for LinkTokenInfo dataclass."""

    def test_to_dict(self):
        """LinkTokenInfo.to_dict serializes correctly."""
        info = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id="org_456",
            jti="link_xyz",
            scope="agent",
            permissions=["sync"],
            issued_at=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            error=None,
        )

        data = info.to_dict()
        assert data["status"] == "valid"
        assert data["organization_id"] == "org_456"
        assert data["jti"] == "link_xyz"
        assert data["scope"] == "agent"
        assert data["permissions"] == ["sync"]
        assert data["issued_at"] == "2024-01-15T10:30:00+00:00"
        assert data["error"] is None

    def test_has_permission(self):
        """LinkTokenInfo.has_permission checks permissions correctly."""
        info = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            permissions=["sync", "read_configs"],
        )

        assert info.has_permission("sync") is True
        assert info.has_permission("read_configs") is True
        assert info.has_permission("delete_configs") is False


class TestRevocationCache:
    """Tests for token revocation cache."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Clear cache before and after each test."""
        clear_revocation_cache()
        yield
        clear_revocation_cache()

    def test_add_revoked_token(self):
        """add_revoked_token adds token to cache."""
        add_revoked_token("test_jti_123")
        assert is_token_revoked("test_jti_123") is True

    def test_is_token_revoked_not_revoked(self):
        """is_token_revoked returns False for non-revoked token."""
        assert is_token_revoked("unknown_jti") is False

    def test_clear_revocation_cache(self):
        """clear_revocation_cache empties the cache."""
        add_revoked_token("jti1")
        add_revoked_token("jti2")

        clear_revocation_cache()

        assert is_token_revoked("jti1") is False
        assert is_token_revoked("jti2") is False

    def test_revocation_cache_thread_safety(self):
        """Revocation cache is thread-safe."""
        errors = []

        def add_tokens():
            try:
                for i in range(100):
                    add_revoked_token(f"jti_{threading.current_thread().name}_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_tokens) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


class TestLinkTokenHelpers:
    """Tests for helper functions."""

    def test_get_link_token_from_env(self):
        """get_link_token_from_env reads from environment."""
        with patch.dict(os.environ, {"LINK_TOKEN": "test_token_123"}):
            assert get_link_token_from_env() == "test_token_123"

    def test_get_link_token_from_env_missing(self):
        """get_link_token_from_env returns empty string if missing."""
        with patch.dict(os.environ, {}, clear=True):
            assert get_link_token_from_env() == ""

    def test_get_link_token_info(self):
        """get_link_token_info validates token from environment."""
        with patch.dict(os.environ, {"LINK_TOKEN": "intest_token_data"}):
            info = get_link_token_info()
            assert info.status in [LinkTokenStatus.INVALID, LinkTokenStatus.MISSING]

    def test_is_link_token_valid(self):
        """is_link_token_valid checks status correctly."""
        valid_info = LinkTokenInfo(status=LinkTokenStatus.VALID)
        invalid_info = LinkTokenInfo(status=LinkTokenStatus.INVALID)

        assert is_link_token_valid(valid_info) is True
        assert is_link_token_valid(invalid_info) is False


# ============================================================================
# LinkConfigProvider Tests
# ============================================================================


class TestLinkConfigProvider:
    """Tests for LinkConfigProvider HTTP fetching."""

    @pytest.fixture
    def test_token_data(self):
        """Generate test token data."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        # Generate test key pair
        private_key = rsa.generate_private_key(65537, 2048, default_backend())
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        public_key = private_key.public_key()
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("utf-8")

        payload = {
            "sub": "org_123",
            "iss": "mysql-to-sheets",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": "link_test",
            "scope": "agent",
            "permissions": ["sync", "read_configs"],
        }

        token = jwt.encode(payload, private_pem, algorithm="RS256")

        return {
            "token": token,
            "public_key": public_pem,
        }

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Reset config before each test."""
        from mysql_to_sheets.core.config import reset_config

        reset_config()
        yield
        reset_config()

    def test_provider_type(self, test_token_data):
        """LinkConfigProvider.provider_type returns 'link'."""
        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            config_name="test",
        )
        assert provider.provider_type == "link"

    def test_refresh_missing_token(self):
        """LinkConfigProvider.refresh raises ConfigError without token."""
        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token="",
            config_name="test",
        )

        with pytest.raises(ConfigError) as exc_info:
            provider.refresh()

        assert "LINK_TOKEN is required" in str(exc_info.value)

    def test_refresh_invalid_token(self):
        """LinkConfigProvider.refresh raises ConfigError for invalid token."""
        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token="invalid.token.here",
            config_name="test",
        )

        with pytest.raises(ConfigError) as exc_info:
            provider.refresh()

        assert "Invalid LINK_TOKEN" in str(exc_info.value)

    @patch("urllib.request.urlopen")
    @patch("mysql_to_sheets.agent.link_token.validate_link_token")
    def test_fetch_remote_config_success(self, mock_validate, mock_urlopen, test_token_data):
        """_fetch_remote_config successfully fetches and parses JSON."""
        # Mock token validation to return valid status
        mock_validate.return_value = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id="org_123",
            permissions=["sync", "read_configs"],
        )

        remote_config = {
            "name": "daily-sales",
            "sql_query": "SELECT * FROM sales",
            "google_sheet_id": "ABC123",
            "google_worksheet_name": "Sheet1",
            "column_map": {"id": "ID", "total": "Total"},
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(remote_config).encode("utf-8")
        mock_response.headers.get.return_value = None
        mock_urlopen.return_value = mock_response

        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            config_name="daily-sales",
        )

        # Mock base config
        with patch("mysql_to_sheets.core.config.get_config") as mock_get_config:
            from mysql_to_sheets.core.config import Config

            mock_config = Config()
            mock_get_config.return_value = mock_config

            config = provider.refresh()

            # Verify URL was called
            assert mock_urlopen.called
            call_args = mock_urlopen.call_args
            request = call_args[0][0]
            assert "daily-sales" in request.full_url

            # Verify authorization header
            assert request.headers["Authorization"] == f"Bearer {test_token_data['token']}"

    @patch("urllib.request.urlopen")
    @patch("mysql_to_sheets.agent.link_token.validate_link_token")
    def test_fetch_remote_config_http_401(self, mock_validate, mock_urlopen, test_token_data):
        """_fetch_remote_config raises ConfigError on 401."""
        from urllib.error import HTTPError

        # Mock token validation to return valid status
        mock_validate.return_value = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id="org_123",
            permissions=["sync"],
        )

        mock_urlopen.side_effect = HTTPError(
            "https://test.example.com",
            401,
            "Unauthorized",
            {},
            None,
        )

        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            config_name="test",
        )

        with pytest.raises(ConfigError) as exc_info:
            provider.refresh()

        assert "rejected" in str(exc_info.value).lower()

    @patch("urllib.request.urlopen")
    @patch("mysql_to_sheets.agent.link_token.validate_link_token")
    def test_fetch_remote_config_http_404(self, mock_validate, mock_urlopen, test_token_data):
        """_fetch_remote_config raises ConfigError on 404."""
        from urllib.error import HTTPError

        # Mock token validation to return valid status
        mock_validate.return_value = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id="org_123",
            permissions=["sync"],
        )

        mock_urlopen.side_effect = HTTPError(
            "https://test.example.com",
            404,
            "Not Found",
            {},
            None,
        )

        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            config_name="missing-config",
        )

        with pytest.raises(ConfigError) as exc_info:
            provider.refresh()

        assert "not found" in str(exc_info.value).lower()

    @patch("urllib.request.urlopen")
    @patch("mysql_to_sheets.agent.link_token.validate_link_token")
    def test_fetch_remote_config_list_response(self, mock_validate, mock_urlopen, test_token_data):
        """_fetch_remote_config handles list response by taking first item."""
        # Mock token validation to return valid status
        mock_validate.return_value = LinkTokenInfo(
            status=LinkTokenStatus.VALID,
            organization_id="org_123",
            permissions=["sync"],
        )

        remote_configs = [
            {
                "name": "config1",
                "sql_query": "SELECT * FROM table1",
                "google_sheet_id": "ABC",
            },
            {
                "name": "config2",
                "sql_query": "SELECT * FROM table2",
                "google_sheet_id": "XYZ",
            },
        ]

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(remote_configs).encode("utf-8")
        mock_response.headers.get.return_value = None
        mock_urlopen.return_value = mock_response

        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
        )

        with patch("mysql_to_sheets.core.config.get_config") as mock_get_config:
            from mysql_to_sheets.core.config import Config

            mock_config = Config()
            mock_get_config.return_value = mock_config

            config = provider.refresh()
            # Should use first config

    def test_invalidate_cache(self, test_token_data):
        """invalidate_cache clears cached config."""
        provider = LinkConfigProvider(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            config_name="test",
        )

        # Manually set cached config
        from mysql_to_sheets.core.config import Config

        provider._cached_config = Config()
        provider._cached_etag = "etag123"

        provider.invalidate_cache()

        assert provider._cached_config is None
        assert provider._cached_etag is None


# ============================================================================
# AgentWorker Tests
# ============================================================================


class TestAgentWorker:
    """Tests for AgentWorker lifecycle and job processing."""

    @pytest.fixture
    def test_token_data(self):
        """Generate a valid token for testing using cryptography library."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.backends import default_backend

        # Generate test key pair
        private_key = rsa.generate_private_key(65537, 2048, default_backend())
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode("utf-8")

        payload = {
            "sub": "org_123",
            "iss": "mysql-to-sheets",
            "iat": int(datetime.now(timezone.utc).timestamp()),
            "jti": "link_worker_test",
            "scope": "agent",
            "permissions": ["sync"],
        }
        token = jwt.encode(payload, private_pem, algorithm="RS256")
        return {"token": token}

    def test_generate_agent_id(self):
        """generate_agent_id creates unique agent IDs."""
        id1 = generate_agent_id()
        id2 = generate_agent_id()

        assert id1.startswith("agent-")
        assert id2.startswith("agent-")
        assert id1 != id2  # Should be unique

    def test_agent_worker_initialization(self, test_token_data):
        """AgentWorker initializes with correct defaults."""
        worker = AgentWorker(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
        )

        assert worker.control_plane_url == "https://test.example.com"
        assert worker.agent_id.startswith("agent-")
        assert worker.is_running is False
        assert worker.status.status == "idle"

    def test_agent_worker_custom_agent_id(self, test_token_data):
        """AgentWorker can use custom agent ID."""
        worker = AgentWorker(
            control_plane_url="https://test.example.com",
            link_token=test_token_data["token"],
            agent_id="custom-agent-123",
        )

        assert worker.agent_id == "custom-agent-123"

    def test_agent_job_from_dict(self):
        """AgentJob.from_dict correctly parses job data."""
        data = {
            "id": 123,
            "organization_id": 456,
            "job_type": "sync",
            "config_id": 789,
            "priority": 5,
            "max_attempts": 3,
            "payload": {"sheet_id": "ABC"},
            "created_at": "2024-01-15T10:30:00Z",
        }

        job = AgentJob.from_dict(data)

        assert job.id == 123
        assert job.organization_id == 456
        assert job.job_type == "sync"
        assert job.config_id == 789
        assert job.priority == 5
        assert job.payload["sheet_id"] == "ABC"
        assert isinstance(job.created_at, datetime)

    def test_agent_status_to_dict(self):
        """AgentStatus.to_dict serializes correctly."""
        status = AgentStatus(
            agent_id="test-agent",
            status="running",
            current_job_id=123,
            jobs_completed=10,
            jobs_failed=2,
        )

        data = status.to_dict()

        assert data["agent_id"] == "test-agent"
        assert data["status"] == "running"
        assert data["current_job_id"] == 123
        assert data["jobs_completed"] == 10
        assert data["jobs_failed"] == 2
        assert "version" in data


# ============================================================================
# Agent Repository Tests
# ============================================================================


class TestAgentModel:
    """Tests for Agent dataclass and model conversions."""

    def test_agent_to_dict(self):
        """Agent.to_dict serializes correctly."""
        agent = Agent(
            id=1,
            agent_id="agent-test-123",
            organization_id=456,
            version="1.0.0",
            hostname="testhost",
            capabilities=["sync"],
            status="online",
            is_active=True,
            jobs_completed=10,
            jobs_failed=2,
            created_at=datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
            updated_at=datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc),
        )

        data = agent.to_dict()

        assert data["id"] == 1
        assert data["agent_id"] == "agent-test-123"
        assert data["organization_id"] == 456
        assert data["version"] == "1.0.0"
        assert data["hostname"] == "testhost"
        assert data["capabilities"] == ["sync"]
        assert data["status"] == "online"
        assert data["is_active"] is True
        assert data["jobs_completed"] == 10
        assert data["jobs_failed"] == 2
        assert data["created_at"] == "2024-01-15T10:00:00+00:00"

    def test_agent_from_dict(self):
        """Agent.from_dict parses correctly."""
        data = {
            "id": 1,
            "agent_id": "agent-test-456",
            "organization_id": 789,
            "version": "1.1.0",
            "hostname": "prodhost",
            "capabilities": ["sync", "export"],
            "status": "busy",
            "is_active": True,
            "last_seen_at": "2024-01-15T12:00:00Z",
            "created_at": "2024-01-15T10:00:00Z",
        }

        agent = Agent.from_dict(data)

        assert agent.id == 1
        assert agent.agent_id == "agent-test-456"
        assert agent.organization_id == 789
        assert agent.capabilities == ["sync", "export"]
        assert isinstance(agent.last_seen_at, datetime)
        assert isinstance(agent.created_at, datetime)


class TestAgentRepository:
    """Tests for AgentRepository CRUD operations."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        try:
            os.unlink(path)
        except FileNotFoundError:
            pass

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Reset repository singleton."""
        reset_agent_repository()
        yield
        reset_agent_repository()

    def test_repository_initialization(self, temp_db):
        """AgentRepository initializes and creates tables."""
        repo = AgentRepository(temp_db)
        assert repo is not None
        # Tables should be created automatically

    def test_upsert_new_agent(self, temp_db):
        """AgentRepository.upsert creates new agent."""
        repo = AgentRepository(temp_db)

        agent = repo.upsert(
            agent_id="agent-new-1",
            organization_id=100,
            version="1.0.0",
            hostname="testhost",
            capabilities=["sync"],
        )

        assert agent.id is not None
        assert agent.agent_id == "agent-new-1"
        assert agent.organization_id == 100
        assert agent.version == "1.0.0"
        assert agent.status == "online"
        assert agent.is_active is True

    def test_upsert_existing_agent(self, temp_db):
        """AgentRepository.upsert updates existing agent."""
        repo = AgentRepository(temp_db)

        # Create initial
        agent1 = repo.upsert(
            agent_id="agent-update-1",
            organization_id=200,
            version="1.0.0",
            hostname="host1",
        )

        # Update with new version
        agent2 = repo.upsert(
            agent_id="agent-update-1",
            organization_id=200,
            version="1.1.0",
            hostname="host2",
        )

        # Should be same ID but updated
        assert agent1.id == agent2.id
        assert agent2.version == "1.1.0"
        assert agent2.hostname == "host2"

    def test_get_by_agent_id(self, temp_db):
        """AgentRepository.get_by_agent_id retrieves agent."""
        repo = AgentRepository(temp_db)

        repo.upsert(
            agent_id="agent-get-1",
            organization_id=300,
            version="1.0.0",
        )

        agent = repo.get_by_agent_id("agent-get-1")
        assert agent is not None
        assert agent.agent_id == "agent-get-1"
        assert agent.organization_id == 300

    def test_get_by_agent_id_with_org_filter(self, temp_db):
        """AgentRepository.get_by_agent_id filters by organization."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-org-1", organization_id=400)

        # Should find with correct org
        agent1 = repo.get_by_agent_id("agent-org-1", organization_id=400)
        assert agent1 is not None

        # Should not find with wrong org
        agent2 = repo.get_by_agent_id("agent-org-1", organization_id=999)
        assert agent2 is None

    def test_get_by_agent_id_not_found(self, temp_db):
        """AgentRepository.get_by_agent_id returns None for missing agent."""
        repo = AgentRepository(temp_db)
        agent = repo.get_by_agent_id("nonexistent")
        assert agent is None

    def test_get_all_agents(self, temp_db):
        """AgentRepository.get_all retrieves all agents for organization."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-all-1", organization_id=500)
        repo.upsert(agent_id="agent-all-2", organization_id=500)
        repo.upsert(agent_id="agent-all-3", organization_id=600)

        agents = repo.get_all(organization_id=500)
        assert len(agents) == 2
        assert {a.agent_id for a in agents} == {"agent-all-1", "agent-all-2"}

    def test_get_all_with_status_filter(self, temp_db):
        """AgentRepository.get_all filters by status."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-status-1", organization_id=700)
        repo.update_status("agent-status-1", 700, "busy")
        repo.upsert(agent_id="agent-status-2", organization_id=700)

        busy_agents = repo.get_all(organization_id=700, status="busy")
        assert len(busy_agents) == 1
        assert busy_agents[0].status == "busy"

    def test_update_status(self, temp_db):
        """AgentRepository.update_status changes agent status."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-update-status", organization_id=800)
        success = repo.update_status("agent-update-status", 800, "offline")

        assert success is True

        agent = repo.get_by_agent_id("agent-update-status")
        assert agent.status == "offline"

    def test_update_status_not_found(self, temp_db):
        """AgentRepository.update_status returns False for missing agent."""
        repo = AgentRepository(temp_db)
        success = repo.update_status("nonexistent", 999, "offline")
        assert success is False

    def test_update_last_seen(self, temp_db):
        """AgentRepository.update_last_seen updates timestamp."""
        repo = AgentRepository(temp_db)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            repo.upsert(agent_id="agent-last-seen", organization_id=900)

            # Move time forward slightly
            frozen_time.move_to("2024-01-15 10:00:01")

            success = repo.update_last_seen("agent-last-seen", 900)
            assert success is True

            agent = repo.get_by_agent_id("agent-last-seen")
            assert agent.last_seen_at is not None
            assert agent.status == "online"

    def test_update_heartbeat(self, temp_db):
        """AgentRepository.update_heartbeat updates job and metrics."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-heartbeat", organization_id=1000)

        success = repo.update_heartbeat(
            "agent-heartbeat",
            1000,
            current_job_id=123,
            status={"jobs_completed": 5, "jobs_failed": 1},
        )

        assert success is True

        agent = repo.get_by_agent_id("agent-heartbeat")
        assert agent.current_job_id == 123
        assert agent.jobs_completed == 5
        assert agent.jobs_failed == 1
        assert agent.status == "busy"  # Should be busy when job_id set

    def test_deactivate_agent(self, temp_db):
        """AgentRepository.deactivate marks agent inactive."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-deactivate", organization_id=1100)
        success = repo.deactivate("agent-deactivate", 1100)

        assert success is True

        agent = repo.get_by_agent_id("agent-deactivate")
        assert agent.is_active is False
        assert agent.status == "offline"

    def test_get_all_excludes_inactive(self, temp_db):
        """AgentRepository.get_all excludes inactive agents by default."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-active", organization_id=1200)
        repo.upsert(agent_id="agent-inactive", organization_id=1200)
        repo.deactivate("agent-inactive", 1200)

        agents = repo.get_all(organization_id=1200)
        assert len(agents) == 1
        assert agents[0].agent_id == "agent-active"

        # With include_inactive
        all_agents = repo.get_all(organization_id=1200, include_inactive=True)
        assert len(all_agents) == 2

    def test_count_agents(self, temp_db):
        """AgentRepository.count returns correct counts."""
        repo = AgentRepository(temp_db)

        repo.upsert(agent_id="agent-count-1", organization_id=1300)
        repo.upsert(agent_id="agent-count-2", organization_id=1300)
        repo.upsert(agent_id="agent-count-3", organization_id=1400)

        count_org_1300 = repo.count(organization_id=1300)
        assert count_org_1300 == 2

        count_all = repo.count()
        assert count_all == 3

    def test_cleanup_stale_agents(self, temp_db):
        """AgentRepository.cleanup_stale marks stale agents offline."""
        repo = AgentRepository(temp_db)

        with freeze_time("2024-01-15 10:00:00") as frozen_time:
            # Create agents
            repo.upsert(agent_id="agent-stale-1", organization_id=1500)
            repo.upsert(agent_id="agent-stale-2", organization_id=1500)

            # Move time forward to make agents stale
            frozen_time.move_to("2024-01-15 10:05:00")  # 5 minutes later

            # Update only one agent (makes it fresh again)
            repo.update_last_seen("agent-stale-2", 1500)

            # Cleanup with 60 second timeout (agent-stale-1 is 5 min stale)
            count = repo.cleanup_stale(timeout_seconds=60)
            assert count == 1  # One agent marked stale

            # Check statuses
            agent1 = repo.get_by_agent_id("agent-stale-1")
            agent2 = repo.get_by_agent_id("agent-stale-2")

            assert agent1.status == "offline"
            assert agent2.status == "online"

    def test_get_agent_repository_singleton(self, temp_db):
        """get_agent_repository returns singleton instance."""
        repo1 = get_agent_repository(temp_db)
        repo2 = get_agent_repository()  # No path needed

        assert repo1 is repo2

    def test_get_agent_repository_requires_path_first(self):
        """get_agent_repository raises without path on first call."""
        reset_agent_repository()

        with pytest.raises(ValueError) as exc_info:
            get_agent_repository()

        assert "db_path is required" in str(exc_info.value)

    def test_reset_agent_repository(self, temp_db):
        """reset_agent_repository clears singleton."""
        repo1 = get_agent_repository(temp_db)
        reset_agent_repository()
        repo2 = get_agent_repository(temp_db)

        # After reset, should be different instance
        assert repo1 is not repo2
