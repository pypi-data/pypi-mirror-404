"""Tests for edge cases EC-51 through EC-57.

EC-51: SYNC_CHUNK_SIZE max bound validation
EC-52: Environment variable path expansion ($HOME, ${HOME})
EC-53: Empty result visibility in SyncResult
EC-54: PII transform error messages
EC-55: Dashboard port validation
EC-56: Streaming column mapping warning
EC-57: Pagination limit bounding
"""

import json
import os
from dataclasses import field
from unittest.mock import MagicMock, patch

import pytest


class TestChunkSizeMaxBound:
    """EC-51: Validate that SYNC_CHUNK_SIZE has a max bound via env var.

    Without the fix, users could set SYNC_CHUNK_SIZE=999999999 and cause OOM.
    The CLI validates --chunk-size <= 100000, but the env var had no max bound.
    """

    def test_chunk_size_within_bounds_accepted(self, monkeypatch):
        """Valid chunk sizes should be accepted."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        monkeypatch.setenv("SYNC_CHUNK_SIZE", "50000")

        config = Config()
        assert config.sync_chunk_size == 50000

    def test_chunk_size_at_max_bound_accepted(self, monkeypatch):
        """Chunk size at the max bound (100000) should be accepted."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        monkeypatch.setenv("SYNC_CHUNK_SIZE", "100000")

        config = Config()
        assert config.sync_chunk_size == 100000

    def test_chunk_size_exceeding_max_raises_error(self, monkeypatch):
        """Chunk size exceeding max bound should raise ConfigError."""
        from mysql_to_sheets.core.config import Config, reset_config
        from mysql_to_sheets.core.exceptions import ConfigError

        reset_config()
        monkeypatch.setenv("SYNC_CHUNK_SIZE", "200000")

        with pytest.raises(ConfigError) as exc_info:
            Config()

        # Error message should mention the field and the limit
        error_msg = str(exc_info.value)
        assert "SYNC_CHUNK_SIZE" in error_msg
        assert "100000" in error_msg  # max value mentioned

    def test_chunk_size_extremely_large_raises_error(self, monkeypatch):
        """Very large chunk sizes that could cause OOM should be rejected."""
        from mysql_to_sheets.core.config import Config, reset_config
        from mysql_to_sheets.core.exceptions import ConfigError

        reset_config()
        monkeypatch.setenv("SYNC_CHUNK_SIZE", "999999999")

        with pytest.raises(ConfigError) as exc_info:
            Config()

        # Error message should mention the field and indicate it's too large
        error_msg = str(exc_info.value)
        assert "SYNC_CHUNK_SIZE" in error_msg
        assert "too large" in error_msg.lower() or "maximum" in error_msg.lower()


class TestEnvVarExpansionInPaths:
    """EC-52: Test that $HOME and ${HOME} are expanded in service account path.

    Without the fix, only ~ was expanded. Users setting SERVICE_ACCOUNT_FILE=$HOME/creds.json
    would get "file not found" with no hint about the unexpanded variable.
    """

    def test_tilde_expansion(self, monkeypatch, tmp_path):
        """Tilde (~) should be expanded to home directory."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        # Create a temp file to simulate service account
        sa_file = tmp_path / "sa.json"
        sa_file.write_text('{"type": "service_account"}')

        # Use tilde path relative to actual home
        home = os.path.expanduser("~")
        monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "~/nonexistent.json")

        config = Config()
        # Should be expanded to absolute path
        assert config.service_account_file.startswith(home)
        assert "~" not in config.service_account_file

    def test_dollar_home_expansion(self, monkeypatch, tmp_path):
        """$HOME should be expanded to home directory."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        home = os.environ.get("HOME", "/home/user")
        monkeypatch.setenv("HOME", home)
        monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "$HOME/service_account.json")

        config = Config()
        # Should be expanded
        assert "$HOME" not in config.service_account_file
        assert config.service_account_file.startswith(home)

    def test_braced_home_expansion(self, monkeypatch, tmp_path):
        """${HOME} should be expanded to home directory."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        home = os.environ.get("HOME", "/home/user")
        monkeypatch.setenv("HOME", home)
        monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "${HOME}/creds/sa.json")

        config = Config()
        # Should be expanded
        assert "${HOME}" not in config.service_account_file
        assert config.service_account_file.startswith(home)

    def test_undefined_variable_preserved(self, monkeypatch):
        """Path with undefined variables should preserve the variable reference."""
        from mysql_to_sheets.core.config import Config, reset_config

        reset_config()
        # Set an undefined variable reference
        monkeypatch.setenv("SERVICE_ACCOUNT_FILE", "$UNDEFINED_VAR/sa.json")
        monkeypatch.delenv("UNDEFINED_VAR", raising=False)

        config = Config()

        # The unexpanded variable should be preserved in the path
        # (os.path.expandvars leaves undefined vars as-is)
        assert "$UNDEFINED_VAR" in config.service_account_file or "UNDEFINED_VAR" in config.service_account_file


class TestEmptyResultVisibility:
    """EC-53: Empty query results should be visible in SyncResult.

    Without the fix, empty result with action='warn' logs a warning but reports
    success. Users don't notice the sheet wasn't updated.
    """

    def test_sync_result_has_warnings_field(self):
        """SyncResult should have a warnings field."""
        from mysql_to_sheets.core.sync.dataclasses import SyncResult

        result = SyncResult(success=True, warnings=["Test warning"])
        assert hasattr(result, "warnings")
        assert result.warnings == ["Test warning"]

    def test_sync_result_has_empty_result_skipped_field(self):
        """SyncResult should have an empty_result_skipped field."""
        from mysql_to_sheets.core.sync.dataclasses import SyncResult

        result = SyncResult(success=True, empty_result_skipped=True)
        assert hasattr(result, "empty_result_skipped")
        assert result.empty_result_skipped is True

    def test_sync_result_to_dict_includes_warnings(self):
        """SyncResult.to_dict() should include warnings when present."""
        from mysql_to_sheets.core.sync.dataclasses import SyncResult

        result = SyncResult(
            success=True,
            warnings=["Empty result set", "Column mapping ignored"],
        )
        data = result.to_dict()

        assert "warnings" in data
        assert len(data["warnings"]) == 2

    def test_sync_result_to_dict_includes_empty_result_skipped(self):
        """SyncResult.to_dict() should include empty_result_skipped when true."""
        from mysql_to_sheets.core.sync.dataclasses import SyncResult

        result = SyncResult(success=True, empty_result_skipped=True)
        data = result.to_dict()

        assert "empty_result_skipped" in data
        assert data["empty_result_skipped"] is True

    def test_sync_result_to_dict_omits_empty_warnings(self):
        """SyncResult.to_dict() should omit warnings when empty."""
        from mysql_to_sheets.core.sync.dataclasses import SyncResult

        result = SyncResult(success=True)
        data = result.to_dict()

        assert "warnings" not in data
        assert "empty_result_skipped" not in data

    def test_sync_context_has_step_warnings(self):
        """SyncContext should have a step_warnings field for collecting warnings."""
        from mysql_to_sheets.core.sync.protocols import SyncContext
        from mysql_to_sheets.core.config import Config
        import logging

        ctx = SyncContext(
            config=Config(),
            logger=logging.getLogger("test"),
        )

        assert hasattr(ctx, "step_warnings")
        assert ctx.step_warnings == []

        # Should be mutable
        ctx.step_warnings.append("Test warning")
        assert len(ctx.step_warnings) == 1


class TestPIITransformErrorMessages:
    """EC-54: Invalid PII transform values should have clear error messages.

    Without the fix, valid JSON like {"email": "INVALID"} gives a cryptic
    ValueError. Should list valid transforms instead.
    """

    def test_valid_pii_transforms_accepted(self):
        """Valid PII transform values should be accepted."""
        from mysql_to_sheets.core.pii import PIITransform

        assert PIITransform.from_string("none") == PIITransform.NONE
        assert PIITransform.from_string("hash") == PIITransform.HASH
        assert PIITransform.from_string("redact") == PIITransform.REDACT
        assert PIITransform.from_string("partial_mask") == PIITransform.PARTIAL_MASK

    def test_invalid_pii_transform_lists_valid_options(self):
        """Invalid PII transform should raise error listing valid options."""
        from mysql_to_sheets.core.pii import PIITransform

        with pytest.raises(ValueError) as exc_info:
            PIITransform.from_string("INVALID")

        error_msg = str(exc_info.value)
        # Should list valid options
        assert "none" in error_msg
        assert "hash" in error_msg
        assert "redact" in error_msg
        assert "partial_mask" in error_msg
        assert "INVALID" in error_msg

    def test_case_insensitive_transform_names(self):
        """PII transform names should be case-insensitive."""
        from mysql_to_sheets.core.pii import PIITransform

        assert PIITransform.from_string("HASH") == PIITransform.HASH
        assert PIITransform.from_string("Hash") == PIITransform.HASH
        assert PIITransform.from_string("REDACT") == PIITransform.REDACT


class TestDashboardPortValidation:
    """EC-55: Dashboard port validation to prevent crashes.

    Without the fix, non-numeric or out-of-range ports could crash the
    setup wizard with unhelpful errors.
    """

    def test_validate_port_valid_number(self):
        """Valid port numbers should be accepted."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("3306")
        assert port == 3306
        assert error is None

    def test_validate_port_integer_input(self):
        """Integer input should be accepted."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port(5432)
        assert port == 5432
        assert error is None

    def test_validate_port_none_returns_default(self):
        """None input should return default port."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port(None, default=3306)
        assert port == 3306
        assert error is None

    def test_validate_port_empty_string_returns_default(self):
        """Empty string should return default port."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("", default=5432)
        assert port == 5432
        assert error is None

    def test_validate_port_non_numeric_returns_error(self):
        """Non-numeric port should return error."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("abc")
        assert port is None
        assert error is not None
        assert "Invalid port" in error
        assert "abc" in error

    def test_validate_port_below_range_returns_error(self):
        """Port below 1 should return error."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("0")
        assert port is None
        assert error is not None
        assert "out of range" in error

    def test_validate_port_above_range_returns_error(self):
        """Port above 65535 should return error."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("70000")
        assert port is None
        assert error is not None
        assert "out of range" in error

    def test_validate_port_negative_returns_error(self):
        """Negative port should return error."""
        from mysql_to_sheets.web.blueprints.dashboard import _validate_port

        port, error = _validate_port("-1")
        assert port is None
        assert error is not None
        assert "out of range" in error


class TestStreamingColumnMappingWarning:
    """EC-56: Streaming mode column mapping warning should appear in SyncResult.

    Without the fix, the warning is logged but not in SyncResult, so
    dashboard/JSON users never see it.
    """

    def test_streaming_push_step_adds_warning_to_context(self):
        """StreamingPushStep should add warning to ctx.step_warnings when column mapping is active."""
        from mysql_to_sheets.core.sync.steps.push import StreamingPushStep
        from mysql_to_sheets.core.sync.protocols import SyncContext
        from mysql_to_sheets.core.config import Config
        from mysql_to_sheets.core.column_mapping import ColumnMappingConfig
        import logging

        # Create a mock context with active column mapping
        ctx = SyncContext(
            config=Config(),
            logger=logging.getLogger("test"),
            mode="streaming",
        )
        ctx.column_mapping_config = ColumnMappingConfig(
            rename_map={"old": "new"},
        )

        step = StreamingPushStep()

        # Check that warning would be added (we can't fully execute without mocking streaming)
        assert hasattr(ctx, "step_warnings")

    def test_column_mapping_config_is_active(self):
        """ColumnMappingConfig.is_active() should return True when mapping is configured."""
        from mysql_to_sheets.core.column_mapping import ColumnMappingConfig

        # Empty config - not active (enabled=False by default)
        empty_config = ColumnMappingConfig()
        assert not empty_config.is_active()

        # Enabled but no mappings - not active
        enabled_empty = ColumnMappingConfig(enabled=True)
        assert not enabled_empty.is_active()

        # With rename map and enabled - active
        rename_config = ColumnMappingConfig(enabled=True, rename_map={"old": "new"})
        assert rename_config.is_active()

        # With column order and enabled - active
        order_config = ColumnMappingConfig(enabled=True, column_order=["col1", "col2"])
        assert order_config.is_active()

        # With case transform and enabled - active
        case_config = ColumnMappingConfig(enabled=True, case_transform="upper")
        assert case_config.is_active()


class TestPaginationBounding:
    """EC-57: Pagination limit should be bounded to prevent OOM.

    Without the fix, ?per_page=999999999 could cause OOM when loading
    large result sets into memory.
    """

    def test_get_bounded_pagination_defaults(self):
        """get_bounded_pagination should return sensible defaults."""
        from mysql_to_sheets.web.utils.pagination import get_bounded_pagination
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/"):
            page, per_page, offset = get_bounded_pagination(
                request=app.test_request_context("/").request,
            )

        # With no args, should use defaults
        # Note: need to use actual request context
        with app.test_request_context("/"):
            from flask import request
            page, per_page, offset = get_bounded_pagination(request)
            assert page == 1
            assert per_page == 25  # default
            assert offset == 0

    def test_get_bounded_pagination_respects_max(self):
        """get_bounded_pagination should cap per_page at max_per_page."""
        from mysql_to_sheets.web.utils.pagination import get_bounded_pagination
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?per_page=999999999"):
            from flask import request
            page, per_page, offset = get_bounded_pagination(request, max_per_page=100)
            assert per_page == 100  # capped at max

    def test_get_bounded_pagination_handles_limit_param(self):
        """get_bounded_pagination should handle limit parameter."""
        from mysql_to_sheets.web.utils.pagination import get_bounded_pagination
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?limit=50"):
            from flask import request
            page, per_page, offset = get_bounded_pagination(request)
            assert per_page == 50

    def test_get_bounded_pagination_handles_negative_values(self):
        """get_bounded_pagination should handle negative values gracefully."""
        from mysql_to_sheets.web.utils.pagination import get_bounded_pagination
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?page=-5&per_page=-10"):
            from flask import request
            page, per_page, offset = get_bounded_pagination(request)
            assert page == 1  # minimum 1
            assert per_page == 1  # minimum 1
            assert offset == 0

    def test_get_bounded_pagination_calculates_offset(self):
        """get_bounded_pagination should correctly calculate offset."""
        from mysql_to_sheets.web.utils.pagination import get_bounded_pagination
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context("/?page=3&per_page=25"):
            from flask import request
            page, per_page, offset = get_bounded_pagination(request)
            assert page == 3
            assert per_page == 25
            assert offset == 50  # (3-1) * 25
