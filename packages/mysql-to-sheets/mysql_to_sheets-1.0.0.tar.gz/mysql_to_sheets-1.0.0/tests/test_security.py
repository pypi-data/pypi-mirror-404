"""Tests for security module.

Uses freezegun for time-sensitive tests where possible.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from freezegun import freeze_time
import pytest

from mysql_to_sheets.core.security import (
    RateLimiter,
    SQLValidationResult,
    TokenBucket,
    generate_api_key,
    generate_api_key_salt,
    hash_api_key,
    hash_api_key_legacy,
    validate_sql_query,
    verify_api_key,
)
from mysql_to_sheets.models.api_keys import APIKeyRepository
from mysql_to_sheets.models.token_blacklist import (
    TokenBlacklistRepository,
)


class TestAPIKeyGeneration:
    """Tests for API key generation."""

    def test_generate_api_key_format(self):
        """Test generated key has correct format."""
        key = generate_api_key()

        assert key.startswith("mts_")
        assert len(key) == 4 + 32  # prefix + 32 hex chars

    def test_generate_api_key_custom_prefix(self):
        """Test custom prefix."""
        key = generate_api_key(prefix="test")

        assert key.startswith("test_")

    def test_generate_api_key_unique(self):
        """Test generated keys are unique."""
        keys = [generate_api_key() for _ in range(100)]

        assert len(set(keys)) == 100


class TestAPIKeyHashing:
    """Tests for API key hashing."""

    def test_hash_api_key(self):
        """Test hashing produces consistent result with same salt."""
        key = "mts_abc123"
        salt = generate_api_key_salt()

        hash1 = hash_api_key(key, salt)
        hash2 = hash_api_key(key, salt)

        assert hash1 == hash2
        # PBKDF2 hash format: "pbkdf2$<64-char hex>" = 71 chars
        assert hash1.startswith("pbkdf2$")
        assert len(hash1) == 71  # 7 (prefix) + 64 (SHA-256 hex)

    def test_hash_api_key_legacy(self):
        """Test legacy hashing produces consistent result."""
        key = "mts_abc123"

        hash1 = hash_api_key_legacy(key)
        hash2 = hash_api_key_legacy(key)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex

    def test_hash_api_key_different_keys(self):
        """Test different keys produce different hashes."""
        salt = generate_api_key_salt()
        hash1 = hash_api_key("mts_key1", salt)
        hash2 = hash_api_key("mts_key2", salt)

        assert hash1 != hash2

    def test_hash_api_key_with_salt(self):
        """Test different salts produce different hashes for same key."""
        key = "mts_test"

        hash1 = hash_api_key(key, salt="salt1")
        hash2 = hash_api_key(key, salt="salt2")

        assert hash1 != hash2

    def test_generate_api_key_salt(self):
        """Test salt generation produces unique salts."""
        salts = [generate_api_key_salt() for _ in range(100)]

        assert len(set(salts)) == 100
        assert all(len(s) == 32 for s in salts)  # 16 bytes = 32 hex chars

    def test_verify_api_key_valid_with_salt(self):
        """Test verifying valid key with per-key salt."""
        key = "mts_test123"
        salt = generate_api_key_salt()
        stored_hash = hash_api_key(key, salt)

        assert verify_api_key(key, stored_hash, salt) is True

    def test_verify_api_key_valid_legacy(self):
        """Test verifying valid key with legacy static salt."""
        key = "mts_test123"
        stored_hash = hash_api_key_legacy(key)

        # verify_api_key with no salt uses legacy salt
        assert verify_api_key(key, stored_hash) is True

    def test_verify_api_key_invalid(self):
        """Test verifying invalid key."""
        key = "mts_test123"
        salt = generate_api_key_salt()
        stored_hash = hash_api_key(key, salt)

        assert verify_api_key("mts_wrong", stored_hash, salt) is False


class TestSQLValidation:
    """Tests for SQL query validation."""

    def test_valid_select_query(self):
        """Test valid SELECT query passes validation."""
        result = validate_sql_query("SELECT * FROM users")

        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_query(self):
        """Test empty query fails validation."""
        result = validate_sql_query("")

        assert result.valid is False
        assert "empty" in result.errors[0].lower()

    def test_reject_drop_statement(self):
        """Test DROP statement is rejected."""
        result = validate_sql_query("DROP TABLE users")

        assert result.valid is False
        assert any("DROP" in e for e in result.errors)

    def test_reject_delete_statement(self):
        """Test DELETE statement is rejected."""
        result = validate_sql_query("DELETE FROM users WHERE id = 1")

        assert result.valid is False
        assert any("DELETE" in e for e in result.errors)

    def test_reject_update_statement(self):
        """Test UPDATE statement is rejected."""
        result = validate_sql_query("UPDATE users SET name = 'test'")

        assert result.valid is False
        assert any("UPDATE" in e for e in result.errors)

    def test_reject_insert_statement(self):
        """Test INSERT statement is rejected."""
        result = validate_sql_query("INSERT INTO users VALUES (1, 'test')")

        assert result.valid is False
        assert any("INSERT" in e for e in result.errors)

    def test_reject_truncate_statement(self):
        """Test TRUNCATE statement is rejected."""
        result = validate_sql_query("TRUNCATE TABLE users")

        assert result.valid is False
        assert any("TRUNCATE" in e for e in result.errors)

    def test_reject_multiple_statements(self):
        """Test multiple statements are rejected."""
        result = validate_sql_query("SELECT * FROM users; DELETE FROM users")

        assert result.valid is False
        assert any("Multiple" in e for e in result.errors)

    def test_single_statement_with_trailing_semicolon(self):
        """Test single statement with trailing semicolon is allowed."""
        result = validate_sql_query("SELECT * FROM users;")

        assert result.valid is True

    def test_warn_on_union(self):
        """Test UNION triggers warning."""
        result = validate_sql_query("SELECT * FROM users UNION SELECT * FROM admins")

        assert result.valid is True
        assert any("UNION" in w for w in result.warnings)

    def test_case_insensitive(self):
        """Test validation is case insensitive."""
        result = validate_sql_query("drop table users")

        assert result.valid is False

    def test_complex_query(self):
        """Test complex but valid query passes."""
        query = """
        SELECT u.id, u.name, COUNT(o.id) as order_count
        FROM users u
        LEFT JOIN orders o ON u.id = o.user_id
        WHERE u.active = 1
        GROUP BY u.id, u.name
        ORDER BY order_count DESC
        LIMIT 100
        """
        result = validate_sql_query(query)

        assert result.valid is True

    def test_reject_create_table(self):
        """Test CREATE TABLE is rejected."""
        result = validate_sql_query("CREATE TABLE test (id INT)")

        assert result.valid is False
        assert any("CREATE" in e for e in result.errors)

    def test_reject_alter_table(self):
        """Test ALTER TABLE is rejected."""
        result = validate_sql_query("ALTER TABLE users ADD COLUMN email VARCHAR(100)")

        assert result.valid is False
        assert any("ALTER" in e for e in result.errors)

    def test_reject_grant_permissions(self):
        """Test GRANT is rejected."""
        result = validate_sql_query("GRANT SELECT ON users TO user1")

        assert result.valid is False
        assert any("GRANT" in e for e in result.errors)

    def test_reject_load_data(self):
        """Test LOAD DATA is rejected."""
        result = validate_sql_query("LOAD DATA INFILE '/tmp/data.csv' INTO TABLE users")

        assert result.valid is False
        assert any("LOAD" in e for e in result.errors)

    def test_reject_into_outfile(self):
        """Test INTO OUTFILE is rejected."""
        result = validate_sql_query("SELECT * FROM users INTO OUTFILE '/tmp/data.csv'")

        assert result.valid is False
        assert any("INTO" in e for e in result.errors)

    def test_reject_sleep_function(self):
        """Test SLEEP function is rejected."""
        result = validate_sql_query("SELECT SLEEP(10) FROM users")

        assert result.valid is False
        assert any("SLEEP" in e for e in result.errors)

    def test_reject_benchmark_function(self):
        """Test BENCHMARK function is rejected."""
        result = validate_sql_query("SELECT BENCHMARK(1000000, SHA1('test'))")

        assert result.valid is False
        assert any("BENCHMARK" in e for e in result.errors)

    def test_query_max_length(self):
        """Test query exceeding max length is rejected."""
        long_query = "SELECT " + "x" * 11000
        result = validate_sql_query(long_query)

        assert result.valid is False
        assert any("length" in e.lower() for e in result.errors)

    def test_with_cte_query(self):
        """Test CTE (WITH) queries are allowed."""
        query = """
        WITH active_users AS (
            SELECT id, name FROM users WHERE active = 1
        )
        SELECT * FROM active_users
        """
        result = validate_sql_query(query)

        assert result.valid is True

    def test_warn_on_like_wildcards(self):
        """Test LIKE with wildcards triggers warning."""
        result = validate_sql_query("SELECT * FROM users WHERE name LIKE '%admin%'")

        assert result.valid is True
        assert any("LIKE" in w or "Wildcard" in w for w in result.warnings)

    def test_reject_system_variables(self):
        """Test system variable access is rejected."""
        result = validate_sql_query("SELECT @@version")

        assert result.valid is False
        assert any("@@" in e for e in result.errors)

    def test_strict_mode_rejects_non_select(self):
        """Test strict mode rejects non-SELECT/WITH queries."""
        result = validate_sql_query("SHOW TABLES", strict_mode=True)

        assert result.valid is False
        assert any("SELECT or WITH" in e for e in result.errors)

    def test_non_strict_mode_allows_show(self):
        """Test non-strict mode allows SHOW commands."""
        result = validate_sql_query("SHOW TABLES", strict_mode=False)

        # SHOW is not in dangerous patterns, so it should pass
        assert result.valid is True

    def test_sql_validation_result_to_dict(self):
        """Test SQLValidationResult.to_dict()."""
        result = SQLValidationResult(
            valid=False,
            errors=["Error 1"],
            warnings=["Warning 1"],
        )

        d = result.to_dict()

        assert d["valid"] is False
        assert d["errors"] == ["Error 1"]
        assert d["warnings"] == ["Warning 1"]


class TestTokenBucket:
    """Tests for TokenBucket rate limiter."""

    def test_initial_capacity(self):
        """Test bucket starts at full capacity."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        assert bucket.consume(5) is True
        assert bucket.consume(5) is True

    def test_consume_over_capacity(self):
        """Test consuming more than capacity fails."""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)

        assert bucket.consume(15) is False

    def test_refill_over_time(self):
        """Test tokens refill over time.

        Uses fast refill rate to minimize actual wait time.
        """
        import time

        bucket = TokenBucket(capacity=10, refill_rate=100.0)  # Fast: 100 tokens/sec
        bucket.consume(10)  # Empty bucket

        time.sleep(0.05)  # 50ms = ~5 tokens at 100/sec
        bucket._refill()

        assert bucket.tokens > 0

    def test_get_wait_time(self):
        """Test calculating wait time."""
        bucket = TokenBucket(capacity=10, refill_rate=10.0)  # 10 per second
        bucket.consume(10)  # Empty bucket

        wait_time = bucket.get_wait_time(5)

        assert wait_time > 0
        assert wait_time <= 0.6  # ~0.5 seconds for 5 tokens at 10/sec


class TestRateLimiter:
    """Tests for RateLimiter."""

    def test_is_allowed_initial(self):
        """Test initial requests are allowed."""
        limiter = RateLimiter(requests_per_minute=60)

        assert limiter.is_allowed("key1") is True

    def test_rate_limit_enforced(self):
        """Test rate limit is enforced after exhaustion."""
        limiter = RateLimiter(requests_per_minute=5, burst_size=5)

        for _ in range(5):
            assert limiter.is_allowed("key1") is True

        # Next request should be limited
        assert limiter.is_allowed("key1") is False

    def test_separate_keys(self):
        """Test different keys have separate limits."""
        limiter = RateLimiter(requests_per_minute=2, burst_size=2)

        limiter.is_allowed("key1")
        limiter.is_allowed("key1")
        assert limiter.is_allowed("key1") is False

        # Different key should still have capacity
        assert limiter.is_allowed("key2") is True

    def test_get_remaining(self):
        """Test getting remaining requests."""
        limiter = RateLimiter(requests_per_minute=10, burst_size=10)

        limiter.is_allowed("key1")
        limiter.is_allowed("key1")
        limiter.is_allowed("key1")

        remaining = limiter.get_remaining("key1")
        assert remaining == 7

    def test_reset(self):
        """Test resetting rate limits."""
        limiter = RateLimiter(requests_per_minute=2, burst_size=2)

        limiter.is_allowed("key1")
        limiter.is_allowed("key1")
        assert limiter.is_allowed("key1") is False

        limiter.reset("key1")
        assert limiter.is_allowed("key1") is True


class TestAPIKeyRepository:
    """Tests for APIKeyRepository."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_api_keys.db"

    def test_create_key(self, temp_db):
        """Test creating an API key."""
        repo = APIKeyRepository(str(temp_db))

        key = repo.create(
            name="Test Key",
            key_hash="hash123",
            key_prefix="mts_abc...",
            description="Test description",
        )

        assert key.id is not None
        assert key.name == "Test Key"

    def test_get_by_id(self, temp_db):
        """Test getting key by ID."""
        repo = APIKeyRepository(str(temp_db))
        key = repo.create(name="Test", key_hash="hash123")

        result = repo.get_by_id(key.id)

        assert result is not None
        assert result.name == "Test"

    def test_get_by_hash(self, temp_db):
        """Test getting key by hash."""
        repo = APIKeyRepository(str(temp_db))
        repo.create(name="Test", key_hash="unique_hash")

        result = repo.get_by_hash("unique_hash")

        assert result is not None
        assert result.name == "Test"

    def test_get_by_hash_revoked(self, temp_db):
        """Test revoked key not returned by hash lookup."""
        repo = APIKeyRepository(str(temp_db))
        key = repo.create(name="Test", key_hash="hash123")
        repo.revoke(key.id)

        result = repo.get_by_hash("hash123")

        assert result is None

    def test_list_keys(self, temp_db):
        """Test listing all keys."""
        repo = APIKeyRepository(str(temp_db))
        repo.create(name="Key 1", key_hash="hash1")
        repo.create(name="Key 2", key_hash="hash2")

        keys = repo.get_all()

        assert len(keys) == 2

    def test_list_keys_exclude_revoked(self, temp_db):
        """Test listing excludes revoked by default."""
        repo = APIKeyRepository(str(temp_db))
        key1 = repo.create(name="Key 1", key_hash="hash1")
        repo.create(name="Key 2", key_hash="hash2")
        repo.revoke(key1.id)

        keys = repo.get_all(include_revoked=False)

        assert len(keys) == 1

    def test_list_keys_include_revoked(self, temp_db):
        """Test listing can include revoked keys."""
        repo = APIKeyRepository(str(temp_db))
        key1 = repo.create(name="Key 1", key_hash="hash1")
        repo.create(name="Key 2", key_hash="hash2")
        repo.revoke(key1.id)

        keys = repo.get_all(include_revoked=True)

        assert len(keys) == 2

    def test_revoke_key(self, temp_db):
        """Test revoking a key."""
        repo = APIKeyRepository(str(temp_db))
        key = repo.create(name="Test", key_hash="hash123")

        result = repo.revoke(key.id)

        assert result is True
        updated = repo.get_by_id(key.id)
        assert updated.revoked is True
        assert updated.revoked_at is not None

    def test_revoke_nonexistent(self, temp_db):
        """Test revoking non-existent key."""
        repo = APIKeyRepository(str(temp_db))

        result = repo.revoke(999)

        assert result is False

    def test_delete_key(self, temp_db):
        """Test permanently deleting a key."""
        repo = APIKeyRepository(str(temp_db))
        key = repo.create(name="Test", key_hash="hash123")

        result = repo.delete(key.id)

        assert result is True
        assert repo.get_by_id(key.id) is None

    def test_count(self, temp_db):
        """Test counting keys."""
        repo = APIKeyRepository(str(temp_db))
        repo.create(name="Key 1", key_hash="hash1")
        repo.create(name="Key 2", key_hash="hash2")

        assert repo.count() == 2

    def test_update_last_used(self, temp_db):
        """Test updating last used timestamp."""
        repo = APIKeyRepository(str(temp_db))
        key = repo.create(name="Test", key_hash="hash123")

        assert repo.get_by_id(key.id).last_used_at is None

        repo.update_last_used("hash123")

        assert repo.get_by_id(key.id).last_used_at is not None


class TestTokenBlacklistRepository:
    """Tests for TokenBlacklistRepository."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "test_blacklist.db"

    def test_add_token(self, temp_db):
        """Test adding a token to the blacklist."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        entry = repo.add("jti123", expires_at, reason="logout")

        assert entry.id is not None
        assert entry.jti == "jti123"
        assert entry.reason == "logout"

    def test_add_token_idempotent(self, temp_db):
        """Test adding same token twice is idempotent."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        entry1 = repo.add("jti123", expires_at)
        entry2 = repo.add("jti123", expires_at)

        assert entry1.id == entry2.id
        assert repo.count() == 1

    def test_is_blacklisted(self, temp_db):
        """Test checking if a token is blacklisted."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        repo.add("jti123", expires_at)

        assert repo.is_blacklisted("jti123") is True
        assert repo.is_blacklisted("unknown") is False

    def test_cleanup_expired(self, temp_db):
        """Test cleaning up expired entries."""
        repo = TokenBlacklistRepository(str(temp_db))

        # Add an expired entry
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        repo.add("expired_jti", expired)

        # Add a valid entry
        valid = datetime.now(timezone.utc) + timedelta(hours=1)
        repo.add("valid_jti", valid)

        assert repo.count() == 2

        # Cleanup
        removed = repo.cleanup_expired()

        assert removed == 1
        assert repo.count() == 1
        assert repo.is_blacklisted("expired_jti") is False
        assert repo.is_blacklisted("valid_jti") is True

    def test_count(self, temp_db):
        """Test counting blacklisted tokens."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        repo.add("jti1", expires_at)
        repo.add("jti2", expires_at)

        assert repo.count() == 2

    def test_clear(self, temp_db):
        """Test clearing all entries."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        repo.add("jti1", expires_at)
        repo.add("jti2", expires_at)

        removed = repo.clear()

        assert removed == 2
        assert repo.count() == 0

    def test_model_to_dict(self, temp_db):
        """Test TokenBlacklistModel.to_dict()."""
        repo = TokenBlacklistRepository(str(temp_db))
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        entry = repo.add("jti123", expires_at, reason="logout")

        d = entry.to_dict()

        assert d["jti"] == "jti123"
        assert d["reason"] == "logout"
        assert d["expires_at"] is not None
        assert d["blacklisted_at"] is not None

    def test_model_is_expired(self, temp_db):
        """Test TokenBlacklistModel.is_expired()."""
        repo = TokenBlacklistRepository(str(temp_db))

        # Create entry with past expiration
        expired = datetime.now(timezone.utc) - timedelta(hours=1)
        entry = repo.add("expired_jti", expired)

        assert entry.is_expired() is True

        # Create entry with future expiration
        valid = datetime.now(timezone.utc) + timedelta(hours=1)
        entry2 = repo.add("valid_jti", valid)

        assert entry2.is_expired() is False
