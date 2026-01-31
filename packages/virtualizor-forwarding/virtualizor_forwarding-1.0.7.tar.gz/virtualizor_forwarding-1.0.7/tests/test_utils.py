"""
Unit tests for utility functions.
"""

import pytest
from virtualizor_forwarding.utils import (
    auto_select_single,
    parse_comma_ids,
    validate_port,
    format_bytes,
    truncate_string,
)


class TestAutoSelectSingle:
    """Tests for auto_select_single function."""

    def test_single_item(self):
        """Test with single item list."""
        result = auto_select_single([1])
        assert result == 1

    def test_empty_list(self):
        """Test with empty list."""
        result = auto_select_single([])
        assert result is None

    def test_multiple_items(self):
        """Test with multiple items."""
        result = auto_select_single([1, 2, 3])
        assert result is None

    def test_single_string(self):
        """Test with single string item."""
        result = auto_select_single(["hello"])
        assert result == "hello"

    def test_single_dict(self):
        """Test with single dict item."""
        item = {"key": "value"}
        result = auto_select_single([item])
        assert result == item


class TestParseCommaIds:
    """Tests for parse_comma_ids function."""

    def test_simple_ids(self):
        """Test parsing simple comma-separated IDs."""
        result = parse_comma_ids("1,2,3")
        assert result == ["1", "2", "3"]

    def test_ids_with_spaces(self):
        """Test parsing IDs with spaces."""
        result = parse_comma_ids("1, 2, 3")
        assert result == ["1", "2", "3"]

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_comma_ids("")
        assert result == []

    def test_single_id(self):
        """Test parsing single ID."""
        result = parse_comma_ids("123")
        assert result == ["123"]

    def test_ids_with_extra_spaces(self):
        """Test parsing IDs with extra spaces."""
        result = parse_comma_ids("  1  ,  2  ,  3  ")
        assert result == ["1", "2", "3"]

    def test_ids_with_empty_parts(self):
        """Test parsing IDs with empty parts."""
        result = parse_comma_ids("1,,2,,,3")
        assert result == ["1", "2", "3"]


class TestValidatePort:
    """Tests for validate_port function."""

    def test_valid_port_min(self):
        """Test minimum valid port."""
        assert validate_port(1) is True

    def test_valid_port_max(self):
        """Test maximum valid port."""
        assert validate_port(65535) is True

    def test_valid_port_common(self):
        """Test common valid ports."""
        assert validate_port(80) is True
        assert validate_port(443) is True
        assert validate_port(8080) is True

    def test_invalid_port_zero(self):
        """Test port 0 is invalid."""
        assert validate_port(0) is False

    def test_invalid_port_negative(self):
        """Test negative port is invalid."""
        assert validate_port(-1) is False

    def test_invalid_port_too_high(self):
        """Test port above 65535 is invalid."""
        assert validate_port(65536) is False

    def test_invalid_port_string(self):
        """Test string port is invalid."""
        assert validate_port("80") is False

    def test_invalid_port_float(self):
        """Test float port is invalid."""
        assert validate_port(80.5) is False


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes(self):
        """Test formatting bytes."""
        assert format_bytes(500) == "500.0 B"

    def test_kilobytes(self):
        """Test formatting kilobytes."""
        result = format_bytes(1024)
        assert "KB" in result

    def test_megabytes(self):
        """Test formatting megabytes."""
        result = format_bytes(1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        """Test formatting gigabytes."""
        result = format_bytes(1024 * 1024 * 1024)
        assert "GB" in result

    def test_terabytes(self):
        """Test formatting terabytes."""
        result = format_bytes(1024 * 1024 * 1024 * 1024)
        assert "TB" in result

    def test_zero(self):
        """Test formatting zero bytes."""
        assert format_bytes(0) == "0.0 B"


class TestTruncateString:
    """Tests for truncate_string function."""

    def test_short_string(self):
        """Test string shorter than max length."""
        result = truncate_string("hello", max_length=10)
        assert result == "hello"

    def test_exact_length(self):
        """Test string exactly at max length."""
        result = truncate_string("hello", max_length=5)
        assert result == "hello"

    def test_long_string(self):
        """Test string longer than max length."""
        result = truncate_string("hello world", max_length=8)
        assert result == "hello..."
        assert len(result) == 8

    def test_custom_suffix(self):
        """Test with custom suffix."""
        result = truncate_string("hello world", max_length=10, suffix="…")
        assert result.endswith("…")

    def test_empty_string(self):
        """Test empty string."""
        result = truncate_string("", max_length=10)
        assert result == ""

    def test_very_short_max_length(self):
        """Test with very short max length."""
        result = truncate_string("hello", max_length=3)
        assert result == "..."
