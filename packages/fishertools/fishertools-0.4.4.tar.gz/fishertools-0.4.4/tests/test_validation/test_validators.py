"""Tests for validation functions."""

import pytest
from fishertools.validation import (
    validate_email,
    validate_url,
    validate_number,
    validate_string,
    validate_structure,
    ValidationError,
)


class TestValidateEmail:
    """Tests for email validation."""

    def test_valid_email(self):
        """Test valid email addresses."""
        validate_email("user@example.com")
        validate_email("test.user@example.co.uk")
        validate_email("user+tag@example.com")

    def test_invalid_email(self):
        """Test invalid email addresses."""
        with pytest.raises(ValidationError):
            validate_email("invalid-email")

        with pytest.raises(ValidationError):
            validate_email("user@")

        with pytest.raises(ValidationError):
            validate_email("@example.com")


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_url(self):
        """Test valid URLs."""
        validate_url("https://example.com")
        validate_url("http://example.com")
        validate_url("https://sub.example.co.uk")

    def test_invalid_url(self):
        """Test invalid URLs."""
        with pytest.raises(ValidationError):
            validate_url("not-a-url")

        with pytest.raises(ValidationError):
            validate_url("ftp://example.com")

        with pytest.raises(ValidationError):
            validate_url("example.com")


class TestValidateNumber:
    """Tests for number validation."""

    def test_valid_number_in_range(self):
        """Test valid numbers in range."""
        validate_number(50, min_val=0, max_val=100)
        validate_number(0, min_val=0, max_val=100)
        validate_number(100, min_val=0, max_val=100)

    def test_number_below_minimum(self):
        """Test number below minimum."""
        with pytest.raises(ValidationError):
            validate_number(-1, min_val=0, max_val=100)

    def test_number_above_maximum(self):
        """Test number above maximum."""
        with pytest.raises(ValidationError):
            validate_number(101, min_val=0, max_val=100)

    def test_number_without_limits(self):
        """Test number without limits."""
        validate_number(-1000)
        validate_number(1000000)


class TestValidateString:
    """Tests for string validation."""

    def test_valid_string_length(self):
        """Test valid string lengths."""
        validate_string("hello", min_length=3, max_length=10)
        validate_string("hi", min_length=2)
        validate_string("hello", max_length=10)

    def test_string_too_short(self):
        """Test string too short."""
        with pytest.raises(ValidationError):
            validate_string("hi", min_length=3)

    def test_string_too_long(self):
        """Test string too long."""
        with pytest.raises(ValidationError):
            validate_string("hello world", max_length=5)

    def test_string_pattern_match(self):
        """Test string pattern matching."""
        validate_string("123", pattern=r"^\d+$")

    def test_string_pattern_no_match(self):
        """Test string pattern not matching."""
        with pytest.raises(ValidationError):
            validate_string("abc", pattern=r"^\d+$")


class TestValidateStructure:
    """Tests for structure validation."""

    def test_valid_structure(self):
        """Test valid data structure."""
        schema = {"name": str, "age": int}
        data = {"name": "Alice", "age": 25}
        validate_structure(data, schema)

    def test_missing_key(self):
        """Test missing required key."""
        schema = {"name": str, "age": int}
        data = {"name": "Alice"}
        with pytest.raises(ValidationError):
            validate_structure(data, schema)

    def test_wrong_type(self):
        """Test wrong type in structure."""
        schema = {"name": str, "age": int}
        data = {"name": "Alice", "age": "twenty-five"}
        with pytest.raises(ValidationError):
            validate_structure(data, schema)

    def test_complex_structure(self):
        """Test complex structure validation."""
        schema = {"name": str, "age": int, "active": bool}
        data = {"name": "Alice", "age": 25, "active": True}
        validate_structure(data, schema)
