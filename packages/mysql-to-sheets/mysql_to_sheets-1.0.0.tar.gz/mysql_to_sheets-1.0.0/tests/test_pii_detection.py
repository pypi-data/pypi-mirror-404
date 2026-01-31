"""Tests for PII detection module.

Tests cover:
- Pattern-based column name detection
- Content-based regex detection
- Combined detection with confidence thresholds
- Category-specific detection (email, phone, SSN, etc.)
"""

import pytest

from mysql_to_sheets.core.pii import PIICategory, PIITransform
from mysql_to_sheets.core.pii_detection import (
    detect_pii_by_column_name,
    detect_pii_by_content,
    detect_pii_in_columns,
    validate_luhn,
)


class TestColumnNameDetection:
    """Tests for pattern-based column name detection."""

    def test_detects_email_column(self):
        """Should detect columns with 'email' in name."""
        result = detect_pii_by_column_name("user_email")
        assert result is not None
        assert result.category == PIICategory.EMAIL
        assert result.confidence >= 0.7

    def test_detects_phone_column(self):
        """Should detect columns with 'phone' in name."""
        result = detect_pii_by_column_name("phone_number")
        assert result is not None
        assert result.category == PIICategory.PHONE
        assert result.confidence >= 0.7

    def test_detects_ssn_column(self):
        """Should detect columns with 'ssn' in name."""
        result = detect_pii_by_column_name("customer_ssn")
        assert result is not None
        assert result.category == PIICategory.SSN
        assert result.confidence >= 0.7

    def test_detects_credit_card_column(self):
        """Should detect columns with 'credit_card' in name."""
        result = detect_pii_by_column_name("credit_card_number")
        assert result is not None
        assert result.category == PIICategory.CREDIT_CARD
        assert result.confidence >= 0.7

    def test_detects_name_column(self):
        """Should detect columns with 'name' patterns."""
        result = detect_pii_by_column_name("first_name")
        assert result is not None
        assert result.category == PIICategory.NAME
        assert result.confidence >= 0.7

    def test_detects_address_column(self):
        """Should detect columns with 'address' in name."""
        result = detect_pii_by_column_name("street_address")
        assert result is not None
        assert result.category == PIICategory.ADDRESS
        assert result.confidence >= 0.7

    def test_detects_ip_column(self):
        """Should detect columns with 'ip' patterns."""
        result = detect_pii_by_column_name("client_ip_address")
        assert result is not None
        assert result.category == PIICategory.IP_ADDRESS
        assert result.confidence >= 0.7

    def test_detects_dob_column(self):
        """Should detect columns with date of birth patterns."""
        result = detect_pii_by_column_name("date_of_birth")
        assert result is not None
        assert result.category == PIICategory.DATE_OF_BIRTH
        assert result.confidence >= 0.7

    def test_ignores_non_pii_column(self):
        """Should not detect PII in non-PII column names."""
        result = detect_pii_by_column_name("product_id")
        assert result is None

    def test_case_insensitive_detection(self):
        """Should detect PII regardless of case."""
        result = detect_pii_by_column_name("USER_EMAIL")
        assert result is not None
        assert result.category == PIICategory.EMAIL


class TestContentDetection:
    """Tests for content-based regex detection."""

    def test_detects_email_content(self):
        """Should detect email addresses in content."""
        # Pass flat list of values, not list of rows
        # Use 3 out of 4 to get 75% confidence (above 0.7 threshold)
        values = ["user@example.com", "test@domain.org", "another@test.com", "hello"]
        result = detect_pii_by_content("data", values)
        assert result is not None
        assert result.category == PIICategory.EMAIL
        # 3/4 = 75% confidence
        assert result.confidence >= 0.7

    def test_detects_phone_content(self):
        """Should detect phone numbers in content."""
        # Use 3 out of 4 to get 75% confidence
        values = ["555-123-4567", "(555) 987-6543", "555-999-8888", "not a phone"]
        result = detect_pii_by_content("data", values)
        assert result is not None
        assert result.category == PIICategory.PHONE

    def test_detects_ssn_content(self):
        """Should detect SSN patterns in content."""
        # Use 3 out of 4 to get 75% confidence
        values = ["123-45-6789", "987-65-4321", "555-55-5555", "regular text"]
        result = detect_pii_by_content("data", values)
        assert result is not None
        assert result.category == PIICategory.SSN

    def test_detects_ip_content(self):
        """Should detect IP addresses in content."""
        # Use 3 out of 4 to get 75% confidence
        values = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "not an ip"]
        result = detect_pii_by_content("data", values)
        assert result is not None
        assert result.category == PIICategory.IP_ADDRESS

    def test_ignores_non_pii_content(self):
        """Should not detect PII in regular text."""
        values = ["hello world", "product 123", "order status"]
        result = detect_pii_by_content("data", values)
        assert result is None

    def test_confidence_based_on_matches(self):
        """Confidence should be based on percentage of matching rows."""
        # All rows contain email
        values = ["a@b.com", "c@d.com", "e@f.com"]
        result = detect_pii_by_content("data", values)
        assert result is not None
        assert result.confidence >= 0.9

        # Only 1 of 3 rows contains email - below default threshold
        values = ["a@b.com", "not email", "also not"]
        result = detect_pii_by_content("data", values, confidence_threshold=0.2)
        # Should detect with lower confidence since threshold lowered
        assert result is not None
        assert result.confidence < 0.5


class TestCombinedDetection:
    """Tests for combined pattern + content detection."""

    def test_combined_detection(self):
        """Should combine column name and content detection."""
        headers = ["user_email", "product_id", "phone_number"]
        rows = [
            ["user@example.com", "123", "555-123-4567"],
            ["test@domain.org", "456", "(555) 987-6543"],
        ]

        result = detect_pii_in_columns(headers, rows)

        assert result.has_pii is True
        assert len(result.columns) >= 2  # email and phone at minimum

        # Check email detected
        email_col = next((c for c in result.columns if c.column_name == "user_email"), None)
        assert email_col is not None
        assert email_col.category == PIICategory.EMAIL

        # Check phone detected
        phone_col = next((c for c in result.columns if c.column_name == "phone_number"), None)
        assert phone_col is not None
        assert phone_col.category == PIICategory.PHONE

    def test_confidence_threshold_filtering(self):
        """Should filter results by confidence threshold."""
        # Use column names that don't match any PII patterns
        headers = ["value1", "value2"]
        rows = [
            ["not really email", "text"],
            ["still not", "more text"],
        ]

        # With high threshold via config, should not detect
        # (no pattern match, no content match at this threshold)
        from mysql_to_sheets.core.pii import PIITransformConfig
        config = PIITransformConfig(enabled=True, auto_detect=True, confidence_threshold=0.9)
        result = detect_pii_in_columns(headers, rows, config=config)
        assert result.has_pii is False

    def test_suggested_transforms(self):
        """Should suggest appropriate transforms for each category."""
        headers = ["email", "ssn"]
        rows = [
            ["user@example.com", "123-45-6789"],
            ["test@domain.org", "987-65-4321"],
        ]

        result = detect_pii_in_columns(headers, rows)

        email_col = next((c for c in result.columns if c.category == PIICategory.EMAIL), None)
        assert email_col is not None
        assert email_col.suggested_transform in [PIITransform.HASH, PIITransform.REDACT]

        ssn_col = next((c for c in result.columns if c.category == PIICategory.SSN), None)
        assert ssn_col is not None
        # SSN is high-risk PII - REDACT is the suggested transform
        assert ssn_col.suggested_transform == PIITransform.REDACT

    def test_requires_acknowledgment(self):
        """Should require acknowledgment when PII is detected."""
        headers = ["email"]
        rows = [["user@example.com"]]

        result = detect_pii_in_columns(headers, rows)

        assert result.has_pii is True
        assert result.requires_acknowledgment is True

    def test_no_acknowledgment_needed_without_pii(self):
        """Should not require acknowledgment when no PII detected."""
        headers = ["product_id", "quantity"]
        rows = [["ABC123", "10"]]

        result = detect_pii_in_columns(headers, rows)

        assert result.has_pii is False
        assert result.requires_acknowledgment is False


class TestLuhnValidation:
    """Tests for Luhn algorithm validation (credit cards)."""

    def test_valid_credit_card(self):
        """Should validate correct credit card numbers."""
        # Test card number (Visa test card)
        assert validate_luhn("4111111111111111") is True

    def test_invalid_credit_card(self):
        """Should reject invalid credit card numbers."""
        assert validate_luhn("4111111111111112") is False

    def test_handles_spaces(self):
        """Should handle credit cards with spaces."""
        assert validate_luhn("4111 1111 1111 1111") is True

    def test_handles_dashes(self):
        """Should handle credit cards with dashes."""
        assert validate_luhn("4111-1111-1111-1111") is True

    def test_non_numeric_returns_false(self):
        """Should return False for non-numeric input."""
        assert validate_luhn("not a number") is False
        assert validate_luhn("") is False


class TestEmptyInputs:
    """Tests for handling empty inputs."""

    def test_empty_headers(self):
        """Should handle empty headers list."""
        result = detect_pii_in_columns([], [])
        assert result.has_pii is False
        assert len(result.columns) == 0

    def test_empty_rows(self):
        """Should handle empty rows."""
        result = detect_pii_in_columns(["email"], [])
        # Column name detection should still work
        assert result.has_pii is True

    def test_none_values_in_rows(self):
        """Should handle None values in row data."""
        headers = ["email"]
        rows = [[None], ["user@example.com"], [None]]

        result = detect_pii_in_columns(headers, rows)
        assert result.has_pii is True
