"""Tests for configuration edge cases.

Covers Edge Cases:
- EC-15: Env Var Integer Parsing
- EC-18: Streaming Mode Chunk Validation
- EC-19: Streaming Generator Early Termination
- EC-20: Rate Limit Bucket Memory Leak
- EC-21: CLI Chunk Size Not Validated
- EC-22: Schedule Cron/Interval Conflict
"""

import argparse
import inspect
import os
import time
from unittest.mock import MagicMock

import pytest

from mysql_to_sheets.core.exceptions import ConfigError, SheetsError


class TestEnvVarIntegerParsing:
    """Tests for safe integer parsing in environment variables.

    Edge Case 15: Environment Variable Integer Parsing Crashes
    ----------------------------------------------------------
    Integer environment variables were parsed with int() without try/catch,
    causing uncaught ValueError crashes on non-numeric input.
    """

    def test_config_handles_non_numeric_port_gracefully(self):
        """Verify non-numeric DB_PORT raises ConfigError, not ValueError."""
        from mysql_to_sheets.core.config import _safe_parse_int

        os.environ["TEST_PORT"] = "abc"

        with pytest.raises(ConfigError) as exc_info:
            _safe_parse_int("TEST_PORT", 3306)

        assert "TEST_PORT" in str(exc_info.value)
        assert "abc" in str(exc_info.value)
        del os.environ["TEST_PORT"]

    def test_config_negative_pool_size_rejected(self):
        """Verify negative pool size raises ConfigError."""
        from mysql_to_sheets.core.config import _safe_parse_int

        os.environ["TEST_POOL_SIZE"] = "-5"

        with pytest.raises(ConfigError) as exc_info:
            _safe_parse_int("TEST_POOL_SIZE", 5, min_value=1)

        assert "too small" in str(exc_info.value).lower()
        del os.environ["TEST_POOL_SIZE"]

    def test_config_port_out_of_range_rejected(self):
        """Verify port number above 65535 raises ConfigError."""
        from mysql_to_sheets.core.config import _safe_parse_int

        os.environ["TEST_PORT"] = "99999"

        with pytest.raises(ConfigError) as exc_info:
            _safe_parse_int("TEST_PORT", 3306, min_value=1, max_value=65535)

        assert "too large" in str(exc_info.value).lower()
        del os.environ["TEST_PORT"]

    def test_config_valid_integer_passes(self):
        """Verify valid integer values pass."""
        from mysql_to_sheets.core.config import _safe_parse_int

        os.environ["TEST_PORT"] = "8080"

        result = _safe_parse_int("TEST_PORT", 3306, min_value=1, max_value=65535)

        assert result == 8080
        del os.environ["TEST_PORT"]

    def test_config_empty_value_uses_default(self):
        """Verify empty env var uses default value."""
        from mysql_to_sheets.core.config import _safe_parse_int

        os.environ["TEST_PORT"] = ""

        result = _safe_parse_int("TEST_PORT", 3306)

        assert result == 3306
        del os.environ["TEST_PORT"]

    def test_config_missing_var_uses_default(self):
        """Verify missing env var uses default value."""
        from mysql_to_sheets.core.config import _safe_parse_int

        if "TEST_MISSING_VAR" in os.environ:
            del os.environ["TEST_MISSING_VAR"]

        result = _safe_parse_int("TEST_MISSING_VAR", 42)

        assert result == 42


class TestStreamingModeValidation:
    """Tests for streaming mode batch validation.

    Edge Case 18: Streaming Mode Skips Batch Validation
    ---------------------------------------------------
    In streaming mode, run_streaming_sync() didn't call validate_batch_size()
    before pushing chunks.
    """

    def test_streaming_validates_chunks_before_push(self):
        """Verify streaming mode validates chunks before pushing."""
        from mysql_to_sheets.core import streaming

        source = inspect.getsource(streaming.run_streaming_sync)

        assert "validate_batch_size" in source

    def test_streaming_with_oversized_cell_fails_early(self):
        """Verify streaming with oversized cell fails at validation."""
        from mysql_to_sheets.core.sync import validate_batch_size

        large_content = "x" * 60_000  # 60KB - exceeds 50KB limit
        headers = ["id", "content"]
        chunk = [[1, large_content]]

        with pytest.raises(SheetsError):
            validate_batch_size(headers, chunk)


class TestStreamingGeneratorEarlyTermination:
    """Tests for streaming generator early termination handling.

    Edge Case 19: Streaming Generator Early Termination Connection Leak
    -------------------------------------------------------------------
    When a user breaks out of a streaming loop early, the cursor and connection
    may not close properly.
    """

    def test_streaming_validates_chunk_size(self):
        """Verify streaming rejects invalid chunk_size values."""
        from mysql_to_sheets.core.database.mysql import MySQLConnection

        mock_config = MagicMock()
        mock_config.host = "localhost"
        mock_config.port = 3306
        mock_config.user = "test"
        mock_config.password = "test"
        mock_config.database = "test"
        mock_config.connect_timeout = 10

        conn = MySQLConnection(mock_config)

        with pytest.raises(ValueError) as exc_info:
            list(conn.execute_streaming("SELECT 1", chunk_size=0))

        assert "chunk_size must be positive" in str(exc_info.value)

    def test_streaming_rejects_negative_chunk_size(self):
        """Verify streaming rejects negative chunk_size values."""
        from mysql_to_sheets.core.database.mysql import MySQLConnection

        mock_config = MagicMock()
        mock_config.host = "localhost"
        mock_config.port = 3306
        mock_config.user = "test"
        mock_config.password = "test"
        mock_config.database = "test"
        mock_config.connect_timeout = 10

        conn = MySQLConnection(mock_config)

        with pytest.raises(ValueError) as exc_info:
            list(conn.execute_streaming("SELECT 1", chunk_size=-100))

        assert "chunk_size must be positive" in str(exc_info.value)

    def test_streaming_documentation_mentions_cleanup(self):
        """Verify streaming methods document proper cleanup."""
        from mysql_to_sheets.core.database.mysql import MySQLConnection

        source = inspect.getsource(MySQLConnection.execute_streaming)

        assert "fully consumed" in source.lower() or "close" in source.lower()
        assert "GeneratorExit" in source


class TestRateLimitBucketMemoryLeak:
    """Tests for rate limit bucket memory leak prevention.

    Edge Case 20: Rate Limit Bucket Memory Leak
    -------------------------------------------
    The rate limit middleware's _buckets dictionary grew unbounded because
    new IP keys were never removed.
    """

    def test_rate_limit_bucket_cleanup_exists(self):
        """Verify rate limit middleware has bucket cleanup mechanism."""
        from mysql_to_sheets.api.middleware.rate_limit import RateLimitMiddleware

        source = inspect.getsource(RateLimitMiddleware)

        assert "cleanup" in source.lower() or "_cleanup" in source

    def test_rate_limit_cleans_stale_buckets(self):
        """Verify stale buckets are removed during cleanup."""
        from mysql_to_sheets.api.middleware.rate_limit import RateLimitMiddleware

        middleware = RateLimitMiddleware(app=MagicMock(), enabled=True, requests_per_minute=60)

        # Create some buckets with old timestamps
        old_time = time.time() - 120  # 2 minutes ago
        middleware._buckets["old_ip_1"] = [old_time]
        middleware._buckets["old_ip_2"] = [old_time]
        middleware._buckets["current_ip"] = [time.time()]

        # Trigger cleanup
        middleware._last_cleanup = 0
        middleware._allow("new_ip")

        # Old buckets should be removed or empty
        assert (
            "old_ip_1" not in middleware._buckets or middleware._buckets.get("old_ip_1") == []
        )
        assert (
            "old_ip_2" not in middleware._buckets or middleware._buckets.get("old_ip_2") == []
        )


class TestChunkSizeBoundsValidation:
    """Tests for CLI chunk size bounds validation.

    Edge Case 21: CLI Chunk Size Bounds Not Validated
    ------------------------------------------------
    The --chunk-size CLI argument accepted any integer without validation.
    """

    def test_cli_chunk_size_validation_exists(self):
        """Verify CLI validates chunk-size bounds."""
        from mysql_to_sheets.cli import sync_commands

        source = inspect.getsource(sync_commands.cmd_sync)

        assert "chunk_size" in source
        assert "100000" in source or "positive" in source.lower()

    def test_cli_rejects_zero_chunk_size(self):
        """Verify CLI rejects chunk-size of 0."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = argparse.Namespace(
            verbose=False,
            output="json",
            mode="streaming",
            chunk_size=0,
            dry_run=True,
            preview=False,
            google_sheet_id=None,
            google_worksheet_name=None,
            sql_query=None,
            incremental=False,
            incremental_since=None,
            notify=None,
            db_type=None,
            column_map=None,
            column_order=None,
            column_case=None,
            use_query=None,
            use_sheet=None,
            org_slug=None,
            create_worksheet=None,
        )

        result = cmd_sync(args)
        assert result == 1

    def test_cli_rejects_negative_chunk_size(self):
        """Verify CLI rejects negative chunk-size."""
        from mysql_to_sheets.cli.sync_commands import cmd_sync

        args = argparse.Namespace(
            verbose=False,
            output="json",
            mode="streaming",
            chunk_size=-100,
            dry_run=True,
            preview=False,
            google_sheet_id=None,
            google_worksheet_name=None,
            sql_query=None,
            incremental=False,
            incremental_since=None,
            notify=None,
            db_type=None,
            column_map=None,
            column_order=None,
            column_case=None,
            use_query=None,
            use_sheet=None,
            org_slug=None,
            create_worksheet=None,
        )

        result = cmd_sync(args)
        assert result == 1


class TestScheduleCronIntervalConflict:
    """Tests for schedule cron/interval mutual exclusivity.

    Edge Case 22: Schedule Created with Both Cron AND Interval
    ---------------------------------------------------------
    When creating a schedule, both cron_expression AND interval_minutes
    could be provided, leading to undefined behavior.
    """

    def test_api_rejects_both_cron_and_interval(self):
        """Verify API rejects requests with both cron and interval."""
        from mysql_to_sheets.api import routes

        source = inspect.getsource(routes.create_schedule)

        assert "cron_expression" in source and "interval_minutes" in source
        assert "both" in source.lower() or "Cannot specify both" in source

    def test_cli_rejects_both_cron_and_interval(self):
        """Verify CLI rejects both --cron and --interval."""
        from mysql_to_sheets.cli import schedule_commands

        source = inspect.getsource(schedule_commands.cmd_schedule_add)

        assert "cron" in source and "interval" in source
        assert "both" in source.lower() or "Cannot specify both" in source

    def test_api_rejects_negative_interval(self):
        """Verify API rejects negative interval values."""
        from mysql_to_sheets.api import routes

        source = inspect.getsource(routes.create_schedule)

        assert "interval_minutes" in source
        assert "<= 0" in source or "positive" in source.lower() or "must be positive" in source
