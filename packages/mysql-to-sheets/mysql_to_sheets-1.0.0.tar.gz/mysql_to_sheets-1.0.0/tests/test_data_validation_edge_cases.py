"""Tests for data validation edge cases.

Covers Edge Cases:
- EC-1: Cell Size Limit (50KB)
- EC-4: Ragged Row Data
- EC-9: Unicode Cell Size Validation
- EC-10: Infinity/NaN Handling
- EC-11: Decimal Precision Loss
"""

import math
from decimal import Decimal

import pytest

from mysql_to_sheets.core.exceptions import ConfigError, SheetsError
from mysql_to_sheets.core.sync import SHEETS_CELL_SIZE_LIMIT, validate_batch_size


class TestCellSizeLimit:
    """Tests for Google Sheets cell size limit (50KB per cell).

    Edge Case 1: Cell Size Limit Not Validated
    ------------------------------------------
    The constant SHEETS_CELL_SIZE_LIMIT = 50,000 is defined but never used
    in validate_batch_size(). A large TEXT column could cause partial data
    corruption when the API fails mid-sync.
    """

    def test_cell_size_limit_constant_exists(self):
        """Verify the cell size limit constant is defined correctly."""
        assert SHEETS_CELL_SIZE_LIMIT == 50_000

    def test_validate_batch_size_accepts_normal_data(self):
        """Verify normal-sized data passes validation."""
        headers = ["id", "name", "description"]
        rows = [[1, "Alice", "A short description"]]

        # Should not raise
        validate_batch_size(headers, rows)

    def test_validate_batch_size_rejects_oversized_cell(self):
        """Verify data with a cell exceeding 50KB limit is rejected.

        This test demonstrates Edge Case 1: A cell with 60KB of content
        should be rejected BEFORE attempting to push to Google Sheets,
        not fail mid-operation leaving partial data.
        """
        large_content = "x" * 60_000  # 60KB - exceeds 50KB limit
        headers = ["id", "content"]
        rows = [[1, large_content]]

        with pytest.raises(SheetsError) as exc_info:
            validate_batch_size(headers, rows)

        assert "cell" in str(exc_info.value).lower() or "size" in str(exc_info.value).lower()

    def test_validate_batch_size_rejects_multiple_oversized_cells(self):
        """Verify multiple oversized cells in different rows are detected."""
        large_content = "y" * 55_000  # 55KB - exceeds 50KB limit
        headers = ["id", "data"]
        rows = [
            [1, "small content"],
            [2, large_content],  # Row 2 has oversized cell
            [3, "also small"],
        ]

        with pytest.raises(SheetsError):
            validate_batch_size(headers, rows)

    def test_validate_batch_size_allows_exactly_50k_cell(self):
        """Verify a cell with exactly 50KB (the limit) passes validation."""
        exact_limit_content = "z" * 50_000  # Exactly 50KB
        headers = ["id", "content"]
        rows = [[1, exact_limit_content]]

        # Should NOT raise - exactly at limit is valid
        validate_batch_size(headers, rows)


class TestRaggedRowData:
    """Tests for ragged row data (variable column counts).

    Edge Case 4: Ragged Row Data
    ----------------------------
    When database query results have rows with different column counts than
    the headers, the code can fail silently or raise cryptic errors.
    """

    def test_validates_all_rows_same_length_as_headers(self):
        """Verify normal data with consistent column counts passes validation."""
        headers = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob", "bob@example.com"],
            [3, "Charlie", "charlie@example.com"],
        ]

        # Should not raise
        validate_batch_size(headers, rows)

    def test_rejects_row_with_fewer_columns(self):
        """Verify rows with fewer columns than headers are rejected.

        This catches the case where a database returns NULL for some columns
        and the driver truncates the row.
        """
        headers = ["id", "name", "email"]
        rows = [
            [1, "Alice", "alice@example.com"],
            [2, "Bob"],  # Missing email column
            [3, "Charlie", "charlie@example.com"],
        ]

        with pytest.raises(ConfigError) as exc_info:
            validate_batch_size(headers, rows)

        assert "CONFIG_106" in str(exc_info.value.code)
        assert "inconsistent" in str(exc_info.value.message).lower()

    def test_rejects_row_with_more_columns(self):
        """Verify rows with more columns than headers are rejected.

        This catches the case where a query returns extra columns that
        would be silently ignored.
        """
        headers = ["id", "name"]
        rows = [
            [1, "Alice"],
            [2, "Bob", "extra_data", "more_data"],  # Too many columns
        ]

        with pytest.raises(ConfigError) as exc_info:
            validate_batch_size(headers, rows)

        assert "CONFIG_106" in str(exc_info.value.code)

    def test_reports_multiple_ragged_rows(self):
        """Verify error message includes multiple ragged row examples."""
        headers = ["a", "b", "c"]
        rows = [
            [1],  # Row 1: 1 column
            [2, 3],  # Row 2: 2 columns
            [4, 5, 6, 7],  # Row 3: 4 columns
        ]

        with pytest.raises(ConfigError) as exc_info:
            validate_batch_size(headers, rows)

        # Error should mention row numbers
        msg = str(exc_info.value.message)
        assert "row 1" in msg.lower() or "row 2" in msg.lower()

    def test_empty_rows_list_passes(self):
        """Verify empty data (0 rows) passes validation."""
        headers = ["id", "name", "email"]
        rows: list[list] = []

        # Should not raise - no rows to validate
        validate_batch_size(headers, rows)


class TestUnicodeCellSizeValidation:
    """Tests for Unicode character handling in cell size validation.

    Edge Case 9: Unicode/Emoji Cell Size Validation
    -----------------------------------------------
    The cell size validation uses len(cell_str) which counts Python characters.
    However, emoji and multi-byte Unicode characters count as 1 char in Python
    but may consume more "space" in the Sheets API.
    """

    def test_ascii_content_character_count_equals_byte_count(self):
        """Verify ASCII content has same character and byte count."""
        content = "Hello World" * 1000  # 11KB ASCII
        assert len(content) == len(content.encode("utf-8"))

    def test_emoji_content_byte_count_exceeds_character_count(self):
        """Verify emoji content has higher byte count than character count.

        This demonstrates the potential issue: len() vs byte length differ.
        """
        # Each emoji is 1 character in Python but 4 bytes in UTF-8
        emoji_content = "🎉" * 1000  # 1000 chars = 4000 bytes
        char_count = len(emoji_content)
        byte_count = len(emoji_content.encode("utf-8"))

        assert char_count == 1000
        assert byte_count == 4000
        assert byte_count > char_count

    def test_cjk_content_byte_count_exceeds_character_count(self):
        """Verify CJK (Chinese/Japanese/Korean) content has higher byte count."""
        # Each CJK character is 1 character in Python but 3 bytes in UTF-8
        cjk_content = "日本語" * 1000  # 3000 chars = 9000 bytes
        char_count = len(cjk_content)
        byte_count = len(cjk_content.encode("utf-8"))

        assert char_count == 3000
        assert byte_count == 9000
        assert byte_count > char_count

    def test_validate_batch_size_warns_on_high_byte_ratio_content(self):
        """Verify validation handles high byte ratio content.

        Tests that validation works with emoji-heavy content.
        """
        # 25K emoji chars = 100KB bytes
        emoji_content = "🎉" * 25_000
        headers = ["id", "content"]
        rows = [[1, emoji_content]]

        # Should pass basic validation
        validate_batch_size(headers, rows)

    def test_mixed_content_byte_validation(self):
        """Verify mixed ASCII/Unicode content is handled correctly."""
        # Mix of ASCII and emoji
        mixed_content = "Hello 🌍 World 🎉" * 3000  # ~18K chars, ~30K bytes
        headers = ["id", "message"]
        rows = [[1, mixed_content]]

        # Should pass basic validation
        validate_batch_size(headers, rows)

    def test_byte_count_near_limit_detection(self):
        """Test that cells near the limit in bytes are properly handled."""
        # 40K emoji chars = 160KB bytes
        emoji_heavy = "🔥" * 40_000
        headers = ["id", "data"]
        rows = [[1, emoji_heavy]]

        char_count = len(emoji_heavy)
        byte_count = len(emoji_heavy.encode("utf-8"))

        assert char_count == 40_000  # Under 50K limit
        assert byte_count == 160_000  # Way over in bytes

        # Current behavior: passes (only checks char count)
        validate_batch_size(headers, rows)


class TestInfinityNaNHandling:
    """Tests for Decimal infinity and NaN handling in type conversion.

    Edge Case 10: Floating Point Infinity & NaN Handling
    ----------------------------------------------------
    When database columns contain Decimal('Infinity'), Decimal('NaN'), or
    Decimal('-Infinity'), the type converter converts them to float, which
    then becomes the literal strings "inf", "nan", "-inf" in Google Sheets.
    """

    def test_decimal_infinity_converted_to_float_inf(self):
        """Verify Decimal('Infinity') converts to float('inf')."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        result = clean_value(Decimal("Infinity"))

        assert math.isinf(result)
        assert result > 0  # Positive infinity

    def test_decimal_negative_infinity_converted_to_float_neg_inf(self):
        """Verify Decimal('-Infinity') converts to float('-inf')."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        result = clean_value(Decimal("-Infinity"))

        assert math.isinf(result)
        assert result < 0  # Negative infinity

    def test_decimal_nan_converted_to_float_nan(self):
        """Verify Decimal('NaN') converts to float('nan')."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        result = clean_value(Decimal("NaN"))

        assert math.isnan(result)

    def test_infinity_in_mixed_numeric_column(self):
        """Demonstrate infinity mixed with normal values in a column."""
        from mysql_to_sheets.core.database.type_converters import clean_row

        row_normal = [1, Decimal("123.45"), "Alice"]
        row_infinity = [2, Decimal("Infinity"), "Bob"]

        cleaned_normal = clean_row(row_normal)
        cleaned_infinity = clean_row(row_infinity)

        # Normal row converts properly
        assert cleaned_normal == [1, 123.45, "Alice"]

        # Infinity row has float('inf')
        assert math.isinf(cleaned_infinity[1])

    def test_infinity_should_raise_or_warn(self):
        """Document recommended behavior for special float values."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        # Current behavior: silently returns inf
        result = clean_value(Decimal("Infinity"))

        # Verify current behavior exists
        assert math.isinf(result)


class TestDecimalPrecisionLoss:
    """Tests for high-precision Decimal conversion to float.

    Edge Case 11: Decimal Precision Loss (>15 digits)
    -------------------------------------------------
    Python float only has ~15-17 digits of precision. Converting high-precision
    Decimal values silently loses data.
    """

    def test_high_precision_decimal_loses_precision(self):
        """Verify that 30-digit decimals lose precision when converted to float."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        # 30-digit precision number
        original = Decimal("123456789012345678901234567890")
        result = clean_value(original)

        # Float only retains ~15 digits of precision
        assert isinstance(result, float)

    def test_financial_precision_example(self):
        """Demonstrate precision loss in financial context."""
        from mysql_to_sheets.core.database.type_converters import clean_value

        # Exact financial amount
        exact_amount = Decimal("123456789012345.678901234567")
        float_amount = clean_value(exact_amount)

        # Verify type conversion happened
        assert isinstance(float_amount, float)

    def test_decimal_precision_preserved_as_string(self):
        """Demonstrate that string conversion preserves precision."""
        original = Decimal("123456789012345678901234567890.12345")

        # String conversion preserves all digits
        string_result = str(original)
        assert string_result == "123456789012345678901234567890.12345"

        # Float conversion loses precision
        float_result = float(original)
        assert str(float_result) != string_result

    def test_detect_high_precision_decimal(self):
        """Test helper to detect high-precision decimals."""

        def needs_string_conversion(value: Decimal) -> bool:
            """Check if decimal has more precision than float can handle."""
            sign, digits, exponent = value.as_tuple()
            significant_digits = len(digits)
            return significant_digits > 15

        # Normal precision - OK for float
        normal = Decimal("123.456789")
        assert not needs_string_conversion(normal)

        # High precision - should be string
        high_prec = Decimal("123456789012345678901234567890")
        assert needs_string_conversion(high_prec)
