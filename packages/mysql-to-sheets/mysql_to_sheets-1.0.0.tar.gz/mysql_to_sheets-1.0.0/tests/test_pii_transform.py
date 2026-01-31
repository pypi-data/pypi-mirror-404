"""Tests for PII transformation module.

Tests cover:
- Hash transformation (SHA256)
- Redact transformation (category-aware)
- Partial mask transformation
- Transform application to datasets
- Transform preview generation
"""

import pytest

from mysql_to_sheets.core.pii import PIICategory, PIITransform, PIITransformConfig
from mysql_to_sheets.core.pii_transform import (
    apply_pii_transforms,
    get_transform_preview,
    hash_value,
    partial_mask_value,
    redact_value,
)


class TestHashTransform:
    """Tests for SHA256 hash transformation."""

    def test_hash_returns_fixed_length(self):
        """Hash should return 16-character string."""
        result = hash_value("user@example.com")
        assert len(result) == 16

    def test_hash_is_deterministic(self):
        """Same input should always produce same hash."""
        value = "test@example.com"
        hash1 = hash_value(value)
        hash2 = hash_value(value)
        assert hash1 == hash2

    def test_different_inputs_different_hashes(self):
        """Different inputs should produce different hashes."""
        hash1 = hash_value("user1@example.com")
        hash2 = hash_value("user2@example.com")
        assert hash1 != hash2

    def test_hash_handles_none(self):
        """Should handle None values gracefully."""
        result = hash_value(None)
        assert result == ""

    def test_hash_handles_empty_string(self):
        """Should handle empty strings."""
        result = hash_value("")
        assert len(result) == 16  # Still produces a hash


class TestRedactTransform:
    """Tests for category-aware redaction."""

    def test_redact_email(self):
        """Should redact email while preserving structure."""
        result = redact_value("john.doe@example.com", PIICategory.EMAIL)
        # Should preserve first char and domain
        assert result.startswith("j")
        assert "@" in result
        assert result.endswith("@example.com")
        assert "***" in result

    def test_redact_phone(self):
        """Should redact phone showing last 4 digits."""
        result = redact_value("555-123-4567", PIICategory.PHONE)
        assert result.endswith("4567")
        assert "***" in result

    def test_redact_ssn(self):
        """Should redact SSN showing last 4 digits."""
        result = redact_value("123-45-6789", PIICategory.SSN)
        assert result.endswith("6789")
        assert "***" in result

    def test_redact_credit_card(self):
        """Should redact credit card showing last 4 digits."""
        result = redact_value("4111-1111-1111-1111", PIICategory.CREDIT_CARD)
        assert result.endswith("1111")
        assert "***" in result

    def test_redact_ip_address(self):
        """Should redact IP address preserving first octet."""
        result = redact_value("192.168.1.100", PIICategory.IP_ADDRESS)
        assert result.startswith("192.")
        assert "*" in result

    def test_redact_generic(self):
        """Should redact generic text with asterisks."""
        result = redact_value("John Smith", PIICategory.NAME)
        assert "***" in result

    def test_redact_handles_none(self):
        """Should handle None values gracefully."""
        result = redact_value(None, PIICategory.EMAIL)
        assert result == ""


class TestPartialMaskTransform:
    """Tests for partial mask transformation."""

    def test_partial_mask_default(self):
        """Should keep last 4 characters visible by default."""
        result = partial_mask_value("123-45-6789")
        assert result.endswith("6789")
        assert result.startswith("***")

    def test_partial_mask_custom_visible(self):
        """Should respect custom visible character count."""
        result = partial_mask_value("1234567890", visible_chars=6)
        assert result.endswith("567890")
        assert result.startswith("***")

    def test_partial_mask_short_value(self):
        """Should handle values shorter than visible chars."""
        result = partial_mask_value("ab", visible_chars=4)
        assert result == "ab"  # Too short to mask

    def test_partial_mask_handles_none(self):
        """Should handle None values gracefully."""
        result = partial_mask_value(None)
        assert result == ""


class TestApplyTransforms:
    """Tests for applying transforms to datasets."""

    def test_apply_single_transform(self):
        """Should apply transform to single column."""
        headers = ["email", "product_id"]
        rows = [
            ["user@example.com", "ABC123"],
            ["test@domain.org", "XYZ789"],
        ]

        config = PIITransformConfig(
            enabled=True,
            transform_map={"email": PIITransform.HASH},
        )

        new_headers, new_rows = apply_pii_transforms(headers, rows, config)

        # Headers unchanged
        assert new_headers == headers

        # Email column transformed
        assert new_rows[0][0] != "user@example.com"
        assert len(new_rows[0][0]) == 16  # Hash length

        # Product ID unchanged
        assert new_rows[0][1] == "ABC123"

    def test_apply_multiple_transforms(self):
        """Should apply different transforms to multiple columns."""
        headers = ["email", "phone", "ssn"]
        rows = [
            ["user@example.com", "555-123-4567", "123-45-6789"],
        ]

        config = PIITransformConfig(
            enabled=True,
            transform_map={
                "email": PIITransform.HASH,
                "phone": PIITransform.REDACT,
                "ssn": PIITransform.PARTIAL_MASK,
            },
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)

        # Email hashed
        assert len(new_rows[0][0]) == 16

        # Phone redacted - without category info, redact returns placeholder
        assert new_rows[0][1] == "***"

        # SSN partial masked - keeps last 4 chars visible
        assert new_rows[0][2].endswith("6789")
        assert "*" in new_rows[0][2]

    def test_no_transform_when_disabled(self):
        """Should not transform when config disabled."""
        headers = ["email"]
        rows = [["user@example.com"]]

        config = PIITransformConfig(
            enabled=False,
            transform_map={"email": PIITransform.HASH},
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)

        # Original value unchanged
        assert new_rows[0][0] == "user@example.com"

    def test_transform_none_no_change(self):
        """Transform.NONE should not modify values."""
        headers = ["email"]
        rows = [["user@example.com"]]

        config = PIITransformConfig(
            enabled=True,
            transform_map={"email": PIITransform.NONE},
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)

        # Original value unchanged
        assert new_rows[0][0] == "user@example.com"

    def test_handles_missing_columns(self):
        """Should handle transforms for non-existent columns."""
        headers = ["email"]
        rows = [["user@example.com"]]

        config = PIITransformConfig(
            enabled=True,
            transform_map={
                "email": PIITransform.HASH,
                "nonexistent": PIITransform.REDACT,
            },
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)

        # Should still work for existing columns
        assert len(new_rows[0][0]) == 16


class TestTransformPreview:
    """Tests for transform preview generation."""

    def test_preview_shows_original_and_transformed(self):
        """Preview should show columns info with before/after samples."""
        headers = ["email", "name"]
        rows = [
            ["user@example.com", "John Doe"],
            ["test@domain.org", "Jane Smith"],
        ]

        config = PIITransformConfig(
            enabled=True,
            transform_map={"email": PIITransform.HASH},
        )

        preview = get_transform_preview(headers, rows, config)

        # Preview returns dict with columns info
        assert "columns" in preview
        assert "total_rows" in preview
        assert preview["total_rows"] == 2
        assert preview["transforms_applied"] == 1

        # Find the email column info
        email_col = next((c for c in preview["columns"] if c["column"] == "email"), None)
        assert email_col is not None
        assert email_col["transform"] == "hash"
        assert email_col["source"] == "explicit"
        # Sample before/after should be present
        assert "sample_before" in email_col
        assert "sample_after" in email_col
        assert email_col["sample_before"] == "user@example.com"
        assert len(email_col["sample_after"]) == 16

    def test_preview_with_multiple_transforms(self):
        """Preview should work with multiple transform types."""
        headers = ["email", "phone"]
        rows = [["user@example.com", "555-123-4567"]]

        config = PIITransformConfig(
            enabled=True,
            transform_map={
                "email": PIITransform.HASH,
                "phone": PIITransform.REDACT,
            },
        )

        preview = get_transform_preview(headers, rows, config)

        assert preview["transforms_applied"] == 2
        assert len(preview["columns"]) == 2

        # Check email transform
        email_col = next((c for c in preview["columns"] if c["column"] == "email"), None)
        assert email_col is not None
        assert len(email_col["sample_after"]) == 16

        # Check phone transform
        phone_col = next((c for c in preview["columns"] if c["column"] == "phone"), None)
        assert phone_col is not None
        assert phone_col["sample_after"] == "***"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_rows(self):
        """Should handle empty row list."""
        headers = ["email"]
        rows: list[list[str]] = []

        config = PIITransformConfig(
            enabled=True,
            transform_map={"email": PIITransform.HASH},
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)
        assert new_rows == []

    def test_empty_headers(self):
        """Should handle empty header list."""
        headers: list[str] = []
        rows: list[list[str]] = []

        config = PIITransformConfig(
            enabled=True,
            transform_map={"email": PIITransform.HASH},
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)
        assert new_rows == []

    def test_unicode_values(self):
        """Should handle unicode values."""
        headers = ["name"]
        rows = [["Jöhn Döe 日本語"]]

        config = PIITransformConfig(
            enabled=True,
            transform_map={"name": PIITransform.HASH},
        )

        _, new_rows = apply_pii_transforms(headers, rows, config)
        assert len(new_rows[0][0]) == 16

    def test_special_characters_in_email(self):
        """Should handle special characters in email."""
        result = hash_value("user+tag@example.com")
        assert len(result) == 16

    def test_very_long_values(self):
        """Should handle very long input values."""
        long_value = "a" * 10000
        result = hash_value(long_value)
        assert len(result) == 16
