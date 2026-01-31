"""Tests for new user onboarding edge cases (EC-31 through EC-35).

These tests verify that the sync tool properly handles common mistakes
that new users make during their first setup experience, providing
clear error messages and guidance.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mysql_to_sheets.core.config import (
    Config,
    _check_placeholders,
    _is_placeholder,
    _validate_service_account_json,
    _validate_service_account_structure,
    get_service_account_email,
)
from mysql_to_sheets.core.exceptions import ConfigError, ErrorCode
from mysql_to_sheets.core.sheets_utils import (
    parse_sheet_id,
    validate_google_url,
)


class TestServiceAccountInvalidJSON:
    """EC-31: Service account file with invalid JSON.

    Problem: User downloads corrupted file or copies wrong file.
    File exists but contains invalid JSON.
    """

    def test_truncated_json_gives_clear_error(self):
        """Truncated JSON file should give clear error with line number."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"type": "service_account", "client_email": ')  # Truncated
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert not is_valid
            assert error is not None
            assert "invalid json" in error.lower()
            assert "re-download" in error.lower()
        finally:
            Path(path).unlink()

    def test_empty_file_gives_clear_error(self):
        """Empty file should give clear error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("")
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert not is_valid
            assert error is not None
            assert "invalid json" in error.lower()
        finally:
            Path(path).unlink()

    def test_non_json_content_gives_clear_error(self):
        """Non-JSON content (e.g., XML, HTML) should give clear error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("<?xml version='1.0'?><root>Not JSON</root>")
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert not is_valid
            assert error is not None
            assert "invalid json" in error.lower()
        finally:
            Path(path).unlink()

    def test_binary_file_gives_encoding_error(self):
        """Binary file should give clear encoding error."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
            f.write(b"\x00\x01\x02\x03\xff\xfe\xfd")  # Binary content
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert not is_valid
            assert error is not None
            # May be JSON decode error or encoding error depending on content
            assert "invalid" in error.lower()
        finally:
            Path(path).unlink()

    def test_valid_json_passes(self):
        """Valid JSON file should pass validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"key": "value"}, f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_json(path)
            assert is_valid
            assert error is None
        finally:
            Path(path).unlink()


class TestServiceAccountMissingFields:
    """EC-32: Service account file missing required fields.

    Problem: User uses OAuth2 user credentials or API key file
    instead of service account.
    """

    def test_missing_client_email_gives_clear_error(self):
        """Missing client_email should suggest downloading correct file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "service_account", "private_key": "xxx"}, f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            assert "client_email" in error
            assert "service account" in error.lower()
        finally:
            Path(path).unlink()

    def test_missing_private_key_gives_clear_error(self):
        """Missing private_key should suggest downloading correct file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "service_account", "client_email": "test@example.com"}, f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            assert "private_key" in error
        finally:
            Path(path).unlink()

    def test_missing_type_field_gives_clear_error(self):
        """Missing type field should suggest downloading correct file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"client_email": "test@example.com", "private_key": "xxx"}, f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            assert "type" in error
        finally:
            Path(path).unlink()

    def test_wrong_type_oauth2_gives_specific_guidance(self):
        """OAuth2 credentials (type != service_account) should give specific guidance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # This is what OAuth2 credentials look like
            json.dump(
                {
                    "type": "authorized_user",
                    "client_id": "xxx.apps.googleusercontent.com",
                    "client_secret": "xxx",
                    "refresh_token": "xxx",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            assert "authorized_user" in error
            assert "oauth" in error.lower() or "service account" in error.lower()
        finally:
            Path(path).unlink()

    def test_api_key_file_gives_guidance(self):
        """API key file structure should give service account guidance."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # API keys don't have a type field typically
            json.dump({"api_key": "AIzaSyAbc123"}, f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            # Should mention missing fields
            assert "missing" in error.lower() or "required" in error.lower()
        finally:
            Path(path).unlink()

    def test_valid_service_account_passes(self):
        """Valid service account file should pass validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "type": "service_account",
                    "client_email": "test@project.iam.gserviceaccount.com",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n",
                    "project_id": "my-project",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert is_valid
            assert error is None
        finally:
            Path(path).unlink()

    def test_non_dict_json_gives_clear_error(self):
        """JSON that's not an object should give clear error."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(["this", "is", "an", "array"], f)
            f.flush()
            path = f.name

        try:
            is_valid, error = _validate_service_account_structure(path)
            assert not is_valid
            assert error is not None
            assert "object" in error.lower() or "dict" in error.lower()
        finally:
            Path(path).unlink()


class TestWrongGoogleServiceURL:
    """EC-33: User pastes URL from wrong Google service.

    Problem: User copies URL from Google Docs, Forms, or Slides
    instead of Sheets.
    """

    def test_google_docs_url_rejected_with_hint(self):
        """Google Docs URL should explain to use Sheets."""
        docs_url = "https://docs.google.com/document/d/abc123/edit"

        is_valid, error = validate_google_url(docs_url)
        assert not is_valid
        assert error is not None
        assert "google docs" in error.lower()
        assert "spreadsheet" in error.lower()

        # Also test via parse_sheet_id
        with pytest.raises(ValueError) as exc_info:
            parse_sheet_id(docs_url)
        assert "google docs" in str(exc_info.value).lower()

    def test_google_forms_url_rejected_with_response_hint(self):
        """Google Forms URL should explain how to get responses spreadsheet."""
        forms_url = "https://docs.google.com/forms/d/abc123/edit"

        is_valid, error = validate_google_url(forms_url)
        assert not is_valid
        assert error is not None
        assert "google forms" in error.lower()
        assert "responses" in error.lower()

        with pytest.raises(ValueError) as exc_info:
            parse_sheet_id(forms_url)
        assert "forms" in str(exc_info.value).lower()

    def test_google_slides_url_rejected_with_hint(self):
        """Google Slides URL should explain to use Sheets."""
        slides_url = "https://docs.google.com/presentation/d/abc123/edit"

        is_valid, error = validate_google_url(slides_url)
        assert not is_valid
        assert error is not None
        assert "google slides" in error.lower()

        with pytest.raises(ValueError) as exc_info:
            parse_sheet_id(slides_url)
        assert "slides" in str(exc_info.value).lower()

    def test_google_drive_url_rejected_with_hint(self):
        """Google Drive URL should explain to open spreadsheet directly."""
        drive_url = "https://drive.google.com/file/d/abc123/view"

        is_valid, error = validate_google_url(drive_url)
        assert not is_valid
        assert error is not None
        assert "drive" in error.lower()

        with pytest.raises(ValueError) as exc_info:
            parse_sheet_id(drive_url)
        assert "drive" in str(exc_info.value).lower()

    def test_valid_sheets_url_accepted(self):
        """Valid Google Sheets URL should be accepted."""
        sheets_url = "https://docs.google.com/spreadsheets/d/abc123xyz/edit#gid=0"

        is_valid, error = validate_google_url(sheets_url)
        assert is_valid
        assert error is None

        sheet_id = parse_sheet_id(sheets_url)
        assert sheet_id == "abc123xyz"

    def test_raw_sheet_id_accepted(self):
        """Raw sheet ID (not a URL) should be accepted."""
        sheet_id = "1a2B3c4D5e6F7g8h9i0j1k2l3m4n5o6p"

        is_valid, error = validate_google_url(sheet_id)
        assert is_valid  # Not a URL, so validation passes
        assert error is None

        result = parse_sheet_id(sheet_id)
        assert result == sheet_id

    def test_http_variant_also_detected(self):
        """HTTP (non-HTTPS) variants should also be detected."""
        docs_url = "http://docs.google.com/document/d/abc123/edit"

        is_valid, error = validate_google_url(docs_url)
        assert not is_valid
        assert "google docs" in error.lower()


class TestPlaceholderDetection:
    """EC-34: User leaves placeholder values in .env.

    Problem: User copies .env.example but forgets to replace
    placeholder values.
    """

    def test_your_password_detected(self):
        """'your_password' should be detected as placeholder."""
        assert _is_placeholder("your_password")
        assert _is_placeholder("your-password")
        assert _is_placeholder("your_database")
        assert _is_placeholder("YOUR_USERNAME")

    def test_angle_bracket_placeholder_detected(self):
        """'<your_database>' should be detected as placeholder."""
        assert _is_placeholder("<your_database>")
        assert _is_placeholder("<PASSWORD>")
        assert _is_placeholder("<enter_value_here>")

    def test_square_bracket_placeholder_detected(self):
        """'[your_database]' should be detected as placeholder."""
        assert _is_placeholder("[your_password]")
        assert _is_placeholder("[DATABASE_NAME]")

    def test_changeme_variants_detected(self):
        """'CHANGE_ME' and variants should be detected."""
        assert _is_placeholder("changeme")
        assert _is_placeholder("CHANGEME")
        assert _is_placeholder("change_me")
        assert _is_placeholder("CHANGE_ME")
        assert _is_placeholder("change-me")

    def test_xxx_placeholder_detected(self):
        """'xxx' patterns should be detected."""
        assert _is_placeholder("xxx")
        assert _is_placeholder("xxxx")
        assert _is_placeholder("XXX")

    def test_common_placeholder_words_detected(self):
        """Common placeholder words should be detected."""
        assert _is_placeholder("placeholder")
        assert _is_placeholder("PLACEHOLDER")
        assert _is_placeholder("example")
        assert _is_placeholder("todo")
        assert _is_placeholder("TODO")
        assert _is_placeholder("sample")
        assert _is_placeholder("demo")

    def test_real_values_not_flagged(self):
        """Actual values that happen to contain 'your' should not be flagged."""
        # These are real values that might look like placeholders but aren't
        assert not _is_placeholder("mycompany_db")
        assert not _is_placeholder("production_password_123")
        assert not _is_placeholder("user@example.com")  # Contains 'example' but structured
        assert not _is_placeholder("secret123!")
        assert not _is_placeholder("abc123XYZ")
        assert not _is_placeholder("sales_data_2024")

    def test_check_placeholders_returns_field_names(self):
        """_check_placeholders should return list of problematic field names."""
        placeholders = _check_placeholders(
            db_user="your_user",
            db_password="changeme",
            db_name="production",  # This is real
            google_sheet_id="<your_sheet_id>",
        )

        assert "DB_USER" in placeholders
        assert "DB_PASSWORD" in placeholders
        assert "GOOGLE_SHEET_ID" in placeholders
        assert "DB_NAME" not in placeholders  # Real value

    def test_check_placeholders_empty_for_real_values(self):
        """_check_placeholders should return empty list for real values."""
        placeholders = _check_placeholders(
            db_user="app_readonly",
            db_password="Sup3rS3cr3t!",
            db_name="sales_db",
            google_sheet_id="1a2B3c4D5e6F7g8h9i0j",
        )

        assert placeholders == []


class TestServiceAccountNotShared:
    """EC-35: Service account not shared with sheet.

    Problem: User creates service account and sheet but forgets
    to share the sheet with the service account email.
    """

    def test_get_service_account_email_extracts_email(self):
        """get_service_account_email should extract client_email from valid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "type": "service_account",
                    "client_email": "test@my-project.iam.gserviceaccount.com",
                    "private_key": "xxx",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            email = get_service_account_email(path)
            assert email == "test@my-project.iam.gserviceaccount.com"
        finally:
            Path(path).unlink()

    def test_get_service_account_email_returns_none_for_missing_file(self):
        """get_service_account_email should return None for missing file."""
        email = get_service_account_email("/nonexistent/path.json")
        assert email is None

    def test_get_service_account_email_returns_none_for_invalid_json(self):
        """get_service_account_email should return None for invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json")
            f.flush()
            path = f.name

        try:
            email = get_service_account_email(path)
            assert email is None
        finally:
            Path(path).unlink()

    def test_get_service_account_email_returns_none_for_missing_field(self):
        """get_service_account_email should return None if client_email missing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "service_account"}, f)
            f.flush()
            path = f.name

        try:
            email = get_service_account_email(path)
            assert email is None
        finally:
            Path(path).unlink()


class TestConfigValidateIntegration:
    """Integration tests for Config.validate() with all edge cases."""

    def test_invalid_json_in_service_account_detected(self):
        """Config.validate() should catch invalid JSON in service account file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not valid json {")
            f.flush()
            path = f.name

        try:
            config = Config(
                db_user="user",
                db_password="pass",
                db_name="db",
                google_sheet_id="abc123",
                service_account_file=path,
                sql_query="SELECT 1",
            )
            errors = config.validate()

            # Should have an error about invalid JSON
            assert len(errors) > 0
            json_error = [e for e in errors if "json" in e.lower()]
            assert len(json_error) > 0
        finally:
            Path(path).unlink()

    def test_missing_fields_in_service_account_detected(self):
        """Config.validate() should catch missing fields in service account."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"type": "authorized_user"}, f)  # Wrong type, missing fields
            f.flush()
            path = f.name

        try:
            config = Config(
                db_user="user",
                db_password="pass",
                db_name="db",
                google_sheet_id="abc123",
                service_account_file=path,
                sql_query="SELECT 1",
            )
            errors = config.validate()

            # Should have an error about missing fields or wrong type
            assert len(errors) > 0
            sa_error = [e for e in errors if "service account" in e.lower() or "authorized_user" in e.lower()]
            assert len(sa_error) > 0
        finally:
            Path(path).unlink()

    def test_placeholder_values_detected_in_validate(self):
        """Config.validate() should catch placeholder values."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "type": "service_account",
                    "client_email": "test@example.iam.gserviceaccount.com",
                    "private_key": "xxx",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            config = Config(
                db_user="your_user",
                db_password="changeme",
                db_name="production_db",
                google_sheet_id="abc123",
                service_account_file=path,
                sql_query="SELECT 1",
            )
            errors = config.validate()

            # Should have an error about placeholder values
            assert len(errors) > 0
            placeholder_error = [e for e in errors if "placeholder" in e.lower()]
            assert len(placeholder_error) > 0
            # Should mention the specific fields
            assert "DB_USER" in placeholder_error[0]
            assert "DB_PASSWORD" in placeholder_error[0]
        finally:
            Path(path).unlink()

    def test_wrong_google_url_detected_in_validate(self):
        """Config.validate() should catch wrong Google service URLs."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "type": "service_account",
                    "client_email": "test@example.iam.gserviceaccount.com",
                    "private_key": "xxx",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            config = Config(
                db_user="user",
                db_password="pass",
                db_name="db",
                google_sheet_id="https://docs.google.com/document/d/abc123/edit",
                service_account_file=path,
                sql_query="SELECT 1",
            )
            errors = config.validate()

            # Should have an error about wrong URL
            assert len(errors) > 0
            url_error = [e for e in errors if "google docs" in e.lower() or "not a google sheets" in e.lower()]
            assert len(url_error) > 0
        finally:
            Path(path).unlink()

    def test_valid_config_passes_all_validations(self):
        """A valid config should pass all validations."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "type": "service_account",
                    "client_email": "test@example.iam.gserviceaccount.com",
                    "private_key": "-----BEGIN PRIVATE KEY-----\nxxx\n-----END PRIVATE KEY-----\n",
                },
                f,
            )
            f.flush()
            path = f.name

        try:
            config = Config(
                db_user="app_user",
                db_password="secure_password_123",
                db_name="production_db",
                google_sheet_id="1a2B3c4D5e6F7g8h9i0j",
                service_account_file=path,
                sql_query="SELECT * FROM users",
            )
            errors = config.validate()

            # Should have no errors
            assert errors == [], f"Unexpected errors: {errors}"
        finally:
            Path(path).unlink()
