"""Tests for structured logging configuration."""

import json
import logging
import os
import tempfile

from mysql_to_sheets.core.logging_config import (
    JSONFormatter,
    LogContext,
    PIIMaskingFilter,
    TextFormatter,
    clear_correlation_context,
    clear_request_id,
    get_config_id,
    get_organization_id,
    get_request_id,
    log_with_context,
    set_config_id,
    set_organization_id,
    set_request_id,
    setup_logging,
)


class TestRequestIdFunctions:
    """Tests for request ID context functions."""

    def setup_method(self) -> None:
        """Clear request ID before each test."""
        clear_request_id()

    def teardown_method(self) -> None:
        """Clear request ID after each test."""
        clear_request_id()

    def test_get_request_id_returns_none_by_default(self) -> None:
        """Test get_request_id returns None when not set."""
        assert get_request_id() is None

    def test_set_request_id_with_value(self) -> None:
        """Test set_request_id with explicit value."""
        result = set_request_id("test-request-123")
        assert result == "test-request-123"
        assert get_request_id() == "test-request-123"

    def test_set_request_id_generates_uuid(self) -> None:
        """Test set_request_id generates UUID when no value provided."""
        result = set_request_id()
        assert result is not None
        assert len(result) == 36  # UUID format: 8-4-4-4-12

    def test_clear_request_id(self) -> None:
        """Test clear_request_id removes the value."""
        set_request_id("test-123")
        clear_request_id()
        assert get_request_id() is None

    def test_request_id_overwrites_previous(self) -> None:
        """Test setting new request ID overwrites previous."""
        set_request_id("first")
        set_request_id("second")
        assert get_request_id() == "second"


class TestJSONFormatter:
    """Tests for JSONFormatter class."""

    def setup_method(self) -> None:
        """Clear request ID before each test."""
        clear_request_id()

    def teardown_method(self) -> None:
        """Clear request ID after each test."""
        clear_request_id()

    def create_log_record(
        self,
        msg: str = "Test message",
        level: int = logging.INFO,
        **kwargs,
    ) -> logging.LogRecord:
        """Create a log record for testing."""
        record = logging.LogRecord(
            name="test_logger",
            level=level,
            pathname="/path/to/file.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=None,
        )
        for key, value in kwargs.items():
            setattr(record, key, value)
        return record

    def test_json_formatter_basic_output(self) -> None:
        """Test JSON formatter produces valid JSON."""
        formatter = JSONFormatter()
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["message"] == "Test message"
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test_logger"

    def test_json_formatter_includes_timestamp(self) -> None:
        """Test JSON formatter includes timestamp."""
        formatter = JSONFormatter()
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert parsed["timestamp"].endswith("Z")

    def test_json_formatter_includes_location(self) -> None:
        """Test JSON formatter includes location info."""
        formatter = JSONFormatter()
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "location" in parsed
        assert parsed["location"]["file"] == "/path/to/file.py"
        assert parsed["location"]["line"] == 42

    def test_json_formatter_includes_request_id(self) -> None:
        """Test JSON formatter includes request ID when set."""
        set_request_id("req-123")
        formatter = JSONFormatter(include_request_id=True)
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "req-123"

    def test_json_formatter_excludes_request_id_when_disabled(self) -> None:
        """Test JSON formatter excludes request ID when disabled."""
        set_request_id("req-123")
        formatter = JSONFormatter(include_request_id=False)
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "request_id" not in parsed

    def test_json_formatter_no_request_id_when_not_set(self) -> None:
        """Test JSON formatter omits request ID when not set."""
        formatter = JSONFormatter(include_request_id=True)
        record = self.create_log_record()

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "request_id" not in parsed

    def test_json_formatter_includes_extras(self) -> None:
        """Test JSON formatter includes extra fields."""
        formatter = JSONFormatter(include_extras=True)
        record = self.create_log_record(custom_field="custom_value")

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["custom_field"] == "custom_value"

    def test_json_formatter_excludes_extras_when_disabled(self) -> None:
        """Test JSON formatter excludes extras when disabled."""
        formatter = JSONFormatter(include_extras=False)
        record = self.create_log_record(custom_field="custom_value")

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "custom_field" not in parsed

    def test_json_formatter_handles_exception_info(self) -> None:
        """Test JSON formatter handles exception info."""
        formatter = JSONFormatter()
        try:
            raise ValueError("Test error")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="test_logger",
                level=logging.ERROR,
                pathname="/path/to/file.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=sys.exc_info(),
            )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_json_formatter_handles_non_serializable_extras(self) -> None:
        """Test JSON formatter handles non-serializable extras."""
        formatter = JSONFormatter(include_extras=True)

        # Create object that's not JSON serializable
        class NonSerializable:
            def __str__(self):
                return "non-serializable-object"

        record = self.create_log_record(custom_obj=NonSerializable())

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["custom_obj"] == "non-serializable-object"


class TestTextFormatter:
    """Tests for TextFormatter class."""

    def setup_method(self) -> None:
        """Clear request ID before each test."""
        clear_request_id()

    def teardown_method(self) -> None:
        """Clear request ID after each test."""
        clear_request_id()

    def create_log_record(
        self,
        msg: str = "Test message",
        level: int = logging.INFO,
    ) -> logging.LogRecord:
        """Create a log record for testing."""
        return logging.LogRecord(
            name="test_logger",
            level=level,
            pathname="/path/to/file.py",
            lineno=42,
            msg=msg,
            args=(),
            exc_info=None,
        )

    def test_text_formatter_default_format(self) -> None:
        """Test text formatter with default format."""
        formatter = TextFormatter()
        record = self.create_log_record()

        output = formatter.format(record)

        assert "Test message" in output
        assert "INFO" in output

    def test_text_formatter_custom_format(self) -> None:
        """Test text formatter with custom format."""
        formatter = TextFormatter(fmt="%(levelname)s: %(message)s")
        record = self.create_log_record()

        output = formatter.format(record)

        assert output == "INFO: Test message"

    def test_text_formatter_includes_request_id(self) -> None:
        """Test text formatter includes request ID prefix."""
        set_request_id("abcdef12-3456-7890-abcd-ef1234567890")
        formatter = TextFormatter(
            fmt="%(message)s",
            include_request_id=True,
        )
        record = self.create_log_record()

        output = formatter.format(record)

        # Request ID prefix (first 8 chars)
        assert "[abcdef12]" in output
        assert "Test message" in output

    def test_text_formatter_excludes_request_id_when_disabled(self) -> None:
        """Test text formatter excludes request ID when disabled."""
        set_request_id("abcdef12-3456-7890-abcd-ef1234567890")
        formatter = TextFormatter(
            fmt="%(message)s",
            include_request_id=False,
        )
        record = self.create_log_record()

        output = formatter.format(record)

        assert "[abcdef12]" not in output
        assert output == "Test message"

    def test_text_formatter_no_request_id_when_not_set(self) -> None:
        """Test text formatter doesn't modify message when no request ID."""
        formatter = TextFormatter(
            fmt="%(message)s",
            include_request_id=True,
        )
        record = self.create_log_record()

        output = formatter.format(record)

        assert output == "Test message"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_returns_logger(self) -> None:
        """Test setup_logging returns a logger instance."""
        logger = setup_logging(logger_name="test_setup")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_setup"

    def test_setup_logging_sets_level(self) -> None:
        """Test setup_logging sets correct log level."""
        logger = setup_logging(log_level="DEBUG", logger_name="test_level")
        assert logger.level == logging.DEBUG

    def test_setup_logging_handles_invalid_level(self) -> None:
        """Test setup_logging defaults to INFO for invalid level."""
        logger = setup_logging(log_level="INVALID", logger_name="test_invalid")
        assert logger.level == logging.INFO

    def test_setup_logging_adds_console_handler(self) -> None:
        """Test setup_logging adds console handler."""
        logger = setup_logging(logger_name="test_console")
        stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_setup_logging_with_file_creates_file_handler(self) -> None:
        """Test setup_logging creates file handler."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test.log")
            logger = setup_logging(
                log_file=log_file,
                logger_name="test_file",
            )

            file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
            assert len(file_handlers) == 1

    def test_setup_logging_creates_log_directory(self) -> None:
        """Test setup_logging creates log directory if missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "subdir", "test.log")
            setup_logging(log_file=log_file, logger_name="test_dir")

            assert os.path.exists(os.path.dirname(log_file))

    def test_setup_logging_json_format(self) -> None:
        """Test setup_logging with JSON format."""
        logger = setup_logging(
            log_format="json",
            logger_name="test_json",
        )

        # Check that handlers use JSONFormatter
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert isinstance(handler.formatter, JSONFormatter)

    def test_setup_logging_text_format(self) -> None:
        """Test setup_logging with text format."""
        logger = setup_logging(
            log_format="text",
            logger_name="test_text",
        )

        # Check that handlers use TextFormatter
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                assert isinstance(handler.formatter, TextFormatter)

    def test_setup_logging_clears_existing_handlers(self) -> None:
        """Test setup_logging clears existing handlers."""
        logger_name = "test_clear_handlers"
        logger = setup_logging(logger_name=logger_name)
        initial_count = len(logger.handlers)

        # Call again - should not accumulate handlers
        logger = setup_logging(logger_name=logger_name)
        assert len(logger.handlers) == initial_count


class TestLogContext:
    """Tests for LogContext context manager."""

    def teardown_method(self) -> None:
        """Restore default log record factory."""
        logging.setLogRecordFactory(logging.LogRecord)

    def test_log_context_adds_extras(self) -> None:
        """Test LogContext adds extras to log records."""
        extras_received = {}

        # Create a custom formatter to capture extras
        class CapturingFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, "user_id"):
                    extras_received["user_id"] = record.user_id
                return super().format(record)

        logger = logging.getLogger("test_context")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(CapturingFormatter())
        logger.handlers = [handler]

        with LogContext(user_id="123"):
            logger.info("Test message")

        assert extras_received.get("user_id") == "123"

    def test_log_context_restores_factory(self) -> None:
        """Test LogContext restores original factory on exit."""
        original_factory = logging.getLogRecordFactory()

        with LogContext(test="value"):
            # Factory should be modified
            assert logging.getLogRecordFactory() != original_factory

        # Factory should be restored
        assert logging.getLogRecordFactory() == original_factory

    def test_log_context_restores_factory_on_exception(self) -> None:
        """Test LogContext restores factory even on exception."""
        original_factory = logging.getLogRecordFactory()

        try:
            with LogContext(test="value"):
                raise ValueError("Test error")
        except ValueError:
            pass

        assert logging.getLogRecordFactory() == original_factory

    def test_log_context_multiple_extras(self) -> None:
        """Test LogContext with multiple extras."""
        extras_received = {}

        class CapturingFormatter(logging.Formatter):
            def format(self, record):
                for key in ["user_id", "operation", "trace_id"]:
                    if hasattr(record, key):
                        extras_received[key] = getattr(record, key)
                return super().format(record)

        logger = logging.getLogger("test_multi_context")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(CapturingFormatter())
        logger.handlers = [handler]

        with LogContext(user_id="123", operation="sync", trace_id="abc"):
            logger.info("Test message")

        assert extras_received == {
            "user_id": "123",
            "operation": "sync",
            "trace_id": "abc",
        }

    def test_log_context_returns_self(self) -> None:
        """Test LogContext __enter__ returns self."""
        ctx = LogContext(test="value")
        with ctx as returned:
            assert returned is ctx


class TestLogWithContext:
    """Tests for log_with_context function."""

    def test_log_with_context_logs_message(self) -> None:
        """Test log_with_context logs the message."""
        logger = logging.getLogger("test_log_with_context")
        logger.setLevel(logging.INFO)

        messages = []
        handler = logging.Handler()
        handler.emit = lambda r: messages.append(r)
        logger.handlers = [handler]

        log_with_context(logger, logging.INFO, "Test message")

        assert len(messages) == 1
        assert messages[0].getMessage() == "Test message"

    def test_log_with_context_includes_extras(self) -> None:
        """Test log_with_context includes extra fields."""
        logger = logging.getLogger("test_log_extras")
        logger.setLevel(logging.INFO)

        records = []
        handler = logging.Handler()
        handler.emit = lambda r: records.append(r)
        logger.handlers = [handler]

        log_with_context(
            logger,
            logging.INFO,
            "Test message",
            user_id="123",
            operation="sync",
        )

        assert len(records) == 1
        assert records[0].user_id == "123"
        assert records[0].operation == "sync"


class TestCorrelationContext:
    """Tests for organization and config ID context variables."""

    def setup_method(self) -> None:
        """Clear correlation context before each test."""
        clear_correlation_context()

    def teardown_method(self) -> None:
        """Clear correlation context after each test."""
        clear_correlation_context()

    def test_organization_id_default_none(self) -> None:
        """Test organization ID defaults to None."""
        assert get_organization_id() is None

    def test_set_organization_id(self) -> None:
        """Test setting organization ID."""
        set_organization_id(42)
        assert get_organization_id() == 42

    def test_clear_organization_id(self) -> None:
        """Test clearing organization ID."""
        set_organization_id(42)
        set_organization_id(None)
        assert get_organization_id() is None

    def test_config_id_default_none(self) -> None:
        """Test config ID defaults to None."""
        assert get_config_id() is None

    def test_set_config_id(self) -> None:
        """Test setting config ID."""
        set_config_id(123)
        assert get_config_id() == 123

    def test_clear_config_id(self) -> None:
        """Test clearing config ID."""
        set_config_id(123)
        set_config_id(None)
        assert get_config_id() is None

    def test_clear_correlation_context(self) -> None:
        """Test clearing all correlation context at once."""
        set_request_id("req-123")
        set_organization_id(42)
        set_config_id(123)

        clear_correlation_context()

        assert get_request_id() is None
        assert get_organization_id() is None
        assert get_config_id() is None

    def test_json_formatter_includes_organization_id(self) -> None:
        """Test JSON formatter includes organization ID when set."""
        set_organization_id(42)
        formatter = JSONFormatter(include_request_id=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["organization_id"] == 42

    def test_json_formatter_includes_config_id(self) -> None:
        """Test JSON formatter includes config ID when set."""
        set_config_id(123)
        formatter = JSONFormatter(include_request_id=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["config_id"] == 123

    def test_json_formatter_all_correlation_ids(self) -> None:
        """Test JSON formatter includes all correlation IDs."""
        set_request_id("req-abc")
        set_organization_id(42)
        set_config_id(123)
        formatter = JSONFormatter(include_request_id=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["request_id"] == "req-abc"
        assert parsed["organization_id"] == 42
        assert parsed["config_id"] == 123

    def test_json_formatter_omits_unset_correlation_ids(self) -> None:
        """Test JSON formatter omits unset correlation IDs."""
        # Only set organization ID
        set_organization_id(42)
        formatter = JSONFormatter(include_request_id=True)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        output = formatter.format(record)
        parsed = json.loads(output)

        assert parsed["organization_id"] == 42
        assert "request_id" not in parsed
        assert "config_id" not in parsed


class TestPIIMaskingFilter:
    """Tests for PIIMaskingFilter class."""

    def test_mask_email_addresses(self) -> None:
        """Test PIIMaskingFilter masks email addresses."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="User email: test@example.com logged in",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "[EMAIL]" in record.msg
        assert "test@example.com" not in record.msg

    def test_mask_ip_addresses(self) -> None:
        """Test PIIMaskingFilter masks IP addresses."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Connection from 192.168.1.100 established",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "[IP]" in record.msg
        assert "192.168.1.100" not in record.msg

    def test_mask_password_values(self) -> None:
        """Test PIIMaskingFilter masks password values."""
        filter_instance = PIIMaskingFilter()
        test_cases = [
            "password=secret123",
            "password='secret123'",
            'password="secret123"',
            "password: secret123",
            "PASSWORD=MySecurePass!",
        ]

        for msg in test_cases:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="/path/to/file.py",
                lineno=42,
                msg=msg,
                args=(),
                exc_info=None,
            )

            filter_instance.filter(record)

            assert "[REDACTED]" in record.msg, f"Failed for: {msg}"
            assert "secret123" not in record.msg
            assert "MySecurePass" not in record.msg

    def test_mask_api_keys(self) -> None:
        """Test PIIMaskingFilter masks API keys and tokens."""
        filter_instance = PIIMaskingFilter()
        test_cases = [
            "api_key=sk_live_abc123xyz",
            "api-key: abcdef123456",
            'token="eyJhbGciOiJI..."',
            "secret=mysupersecret",
        ]

        for msg in test_cases:
            record = logging.LogRecord(
                name="test_logger",
                level=logging.INFO,
                pathname="/path/to/file.py",
                lineno=42,
                msg=msg,
                args=(),
                exc_info=None,
            )

            filter_instance.filter(record)

            assert "[REDACTED]" in record.msg, f"Failed for: {msg}"

    def test_mask_multiple_pii_in_message(self) -> None:
        """Test PIIMaskingFilter masks multiple PII patterns."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="User admin@company.com from 10.0.0.1 set password=abc123",
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert "[EMAIL]" in record.msg
        assert "[IP]" in record.msg
        assert "[REDACTED]" in record.msg
        assert "admin@company.com" not in record.msg
        assert "10.0.0.1" not in record.msg
        assert "abc123" not in record.msg

    def test_filter_always_returns_true(self) -> None:
        """Test PIIMaskingFilter always returns True (allows record)."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result is True

    def test_mask_pii_in_args_dict(self) -> None:
        """Test PIIMaskingFilter masks PII in dict args."""
        filter_instance = PIIMaskingFilter()
        # Create record first, then set args (LogRecord constructor handles dicts specially)
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="User: %(email)s",
            args=(),
            exc_info=None,
        )
        # Set args directly to avoid LogRecord's special dict handling
        record.args = {"email": "test@example.com"}

        filter_instance.filter(record)

        assert record.args["email"] == "[EMAIL]"

    def test_mask_pii_in_args_tuple(self) -> None:
        """Test PIIMaskingFilter masks PII in tuple args."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="User: %s from %s",
            args=("user@test.com", "192.168.0.1"),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.args[0] == "[EMAIL]"
        assert record.args[1] == "[IP]"

    def test_non_string_args_unchanged(self) -> None:
        """Test PIIMaskingFilter leaves non-string args unchanged."""
        filter_instance = PIIMaskingFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg="Count: %d, Ratio: %f",
            args=(42, 3.14),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.args == (42, 3.14)

    def test_no_pii_message_unchanged(self) -> None:
        """Test messages without PII are not modified."""
        filter_instance = PIIMaskingFilter()
        original_msg = "This is a regular log message with no PII"
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=42,
            msg=original_msg,
            args=(),
            exc_info=None,
        )

        filter_instance.filter(record)

        assert record.msg == original_msg


class TestSetupLoggingWithPIIMasking:
    """Tests for setup_logging with PII masking enabled."""

    def test_setup_logging_with_pii_masking(self) -> None:
        """Test setup_logging adds PII masking filter when enabled."""
        logger = setup_logging(
            logger_name="test_pii_logger",
            pii_masking=True,
        )

        pii_filters = [f for f in logger.filters if isinstance(f, PIIMaskingFilter)]
        assert len(pii_filters) == 1

    def test_setup_logging_without_pii_masking(self) -> None:
        """Test setup_logging omits PII masking filter when disabled."""
        logger = setup_logging(
            logger_name="test_no_pii_logger",
            pii_masking=False,
        )

        pii_filters = [f for f in logger.filters if isinstance(f, PIIMaskingFilter)]
        assert len(pii_filters) == 0

    def test_setup_logging_pii_masking_default_disabled(self) -> None:
        """Test PII masking is disabled by default."""
        logger = setup_logging(logger_name="test_default_pii")

        pii_filters = [f for f in logger.filters if isinstance(f, PIIMaskingFilter)]
        assert len(pii_filters) == 0
