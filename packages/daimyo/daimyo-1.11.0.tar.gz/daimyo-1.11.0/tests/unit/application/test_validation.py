"""Tests for input validation and sanitization."""

from __future__ import annotations

import pytest

from daimyo.application.validation import (
    ValidationError,
    sanitize_error_message,
    sanitize_for_logging,
    validate_categories,
    validate_scope_name,
)


class TestSanitizeForLogging:
    """Tests for sanitize_for_logging function."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("simple-value", "simple-value"),
            ("value_with_underscores", "value_with_underscores"),
            ("value-with-dashes", "value-with-dashes"),
            ("value.with.dots", "value.with.dots"),
            ("", ""),
        ],
    )
    def test_valid_simple_values(self, value: str, expected: str) -> None:
        """Valid values should pass through unchanged."""
        assert sanitize_for_logging(value) == expected

    def test_none_value(self) -> None:
        """None should be converted to string 'None'."""
        assert sanitize_for_logging(None) == "None"

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("value\nwith\nnewlines", "valuewithnewlines"),
            ("value\rwith\rcarriage", "valuewithcarriage"),
            ("value\twith\ttabs", "valuewithtabs"),
            ("value\x00with\x01null", "valuewithnull"),
            ("value\x7fwith\x80ansi", "valuewithansi"),
        ],
    )
    def test_removes_control_characters(self, value: str, expected: str) -> None:
        """Control characters should be removed."""
        assert sanitize_for_logging(value) == expected

    def test_truncates_long_values(self) -> None:
        """Long values should be truncated with ellipsis."""
        long_value = "a" * 300
        result = sanitize_for_logging(long_value, max_length=200)
        assert len(result) == 203
        assert result.endswith("...")
        assert result[:200] == "a" * 200

    def test_truncates_comma_list_intelligently(self) -> None:
        """Comma-separated lists should be truncated by removing last items."""
        value = "item1,item2,item3,item4,item5"
        result = sanitize_for_logging(value, max_length=20, is_comma_list=True)
        assert "," in result
        assert not result.endswith(",")
        assert len(result) <= 20

    def test_comma_list_with_control_chars(self) -> None:
        """Comma lists with control chars should be sanitized then truncated."""
        value = "item1\n,item2\t,item3"
        result = sanitize_for_logging(value, max_length=100, is_comma_list=True)
        assert "\n" not in result
        assert "\t" not in result

    def test_custom_max_length(self) -> None:
        """Custom max_length should be respected."""
        value = "a" * 100
        result = sanitize_for_logging(value, max_length=50)
        assert len(result) == 53
        assert result == "a" * 50 + "..."


class TestValidateScopeName:
    """Tests for validate_scope_name function."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "simple",
            "with-dashes",
            "with_underscores",
            "MixedCase123",
            "a",
            "a" * 200,
        ],
    )
    def test_valid_scope_names(self, valid_name: str) -> None:
        """Valid scope names should not raise exceptions."""
        validate_scope_name(valid_name)

    def test_none_scope_name(self) -> None:
        """None scope name should be allowed."""
        validate_scope_name(None)

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "with spaces",
            "with/slashes",
            "with\\backslashes",
            "with.dots",
            "with,commas",
            "with\nnewlines",
            "with\ttabs",
            "with@special",
            "with#chars",
            "with$dollar",
            "",
        ],
    )
    def test_invalid_characters(self, invalid_name: str) -> None:
        """Scope names with invalid characters should raise ValidationError."""
        with pytest.raises(
            ValidationError,
            match="must contain only alphanumeric characters",
        ):
            validate_scope_name(invalid_name)

    def test_too_long_scope_name(self) -> None:
        """Scope names exceeding max length should raise ValidationError."""
        long_name = "a" * 201
        with pytest.raises(ValidationError, match="too long"):
            validate_scope_name(long_name)

    def test_exactly_max_length(self) -> None:
        """Scope name at exactly max length should be valid."""
        max_name = "a" * 200
        validate_scope_name(max_name)


class TestValidateCategories:
    """Tests for validate_categories function."""

    @pytest.mark.parametrize(
        "valid_categories",
        [
            "category",
            "parent.child",
            "parent.child.grandchild",
            "with-dashes",
            "with_underscores",
            "MixedCase123",
            "cat1,cat2,cat3",
            "parent.child1, parent.child2",
            "a.b.c.d.e.f.g",
        ],
    )
    def test_valid_categories(self, valid_categories: str) -> None:
        """Valid category strings should not raise exceptions."""
        validate_categories(valid_categories)

    def test_none_categories(self) -> None:
        """None categories should be allowed."""
        validate_categories(None)

    @pytest.mark.parametrize(
        "invalid_categories",
        [
            "with spaces",
            "with/slashes",
            "with\\backslashes",
            "with,commas,and spaces",
            "with\nnewlines",
            "with@special",
            "parent..child",
            "",
        ],
    )
    def test_invalid_characters(self, invalid_categories: str) -> None:
        """Categories with invalid characters should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid category format"):
            validate_categories(invalid_categories)

    def test_too_long_categories(self) -> None:
        """Category string exceeding max length should raise ValidationError."""
        long_categories = "a" * 10001
        with pytest.raises(ValidationError, match="too long"):
            validate_categories(long_categories)

    def test_exactly_max_length(self) -> None:
        """Category string at exactly max length should be valid."""
        max_categories = "a" * 10000
        validate_categories(max_categories)

    def test_comma_separated_validation(self) -> None:
        """Each category in comma-separated list should be validated."""
        with pytest.raises(ValidationError, match="invalid-category@bad"):
            validate_categories("valid.category,invalid-category@bad,another.valid")


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    def test_none_message(self) -> None:
        """None message should return 'Unknown error'."""
        assert sanitize_error_message(None) == "Unknown error"

    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("Simple error", "Simple error"),
            ("Error with details", "Error with details"),
        ],
    )
    def test_simple_messages(self, message: str, expected: str) -> None:
        """Simple error messages should pass through."""
        assert sanitize_error_message(message) == expected

    @pytest.mark.parametrize(
        ("message", "expected_pattern"),
        [
            ("/home/user/project/file.py", "[file]"),
            ("/var/log/app/error.py", "[file]"),
            ("Error in /opt/app/module.py", "Error in [file]"),
            ("line 42", "line [X]"),
            ("line 123", "line [X]"),
            ('File "/path/to/file.py"', 'File "[...]"'),
        ],
    )
    def test_removes_sensitive_info(self, message: str, expected_pattern: str) -> None:
        """File paths and line numbers should be sanitized."""
        result = sanitize_error_message(message)
        assert expected_pattern in result

    @pytest.mark.parametrize(
        ("message", "expected"),
        [
            ("Error\nwith\nnewlines", "Error with newlines"),
            ("Error\twith\ttabs", "Error with tabs"),
            ("Error\rwith\rcarriage", "Error with carriage"),
        ],
    )
    def test_removes_control_characters(self, message: str, expected: str) -> None:
        """Control characters should be replaced with spaces."""
        assert sanitize_error_message(message) == expected

    def test_truncates_long_messages(self) -> None:
        """Long error messages should be truncated."""
        long_message = "a" * 300
        result = sanitize_error_message(long_message, max_length=200)
        assert len(result) == 203
        assert result.endswith("...")

    def test_custom_max_length(self) -> None:
        """Custom max_length should be respected."""
        message = "a" * 100
        result = sanitize_error_message(message, max_length=50)
        assert len(result) == 53
        assert result == "a" * 50 + "..."

    def test_complex_error_message(self) -> None:
        """Complex error with multiple sensitive elements should be fully sanitized."""
        message = 'File "/home/user/app.py", line 123, in function\nValueError: Invalid input'
        result = sanitize_error_message(message)
        assert "/home/user/app.py" not in result
        assert "[...]" in result
        assert "line 123" not in result
        assert "line [X]" in result
        assert "\n" not in result


class TestIntegrationScenarios:
    """Integration tests for common usage patterns."""

    def test_sanitize_then_validate_scope(self) -> None:
        """Sanitization should be separate from validation."""
        malicious_input = "valid-scope\nmalicious-code"
        sanitized = sanitize_for_logging(malicious_input)
        assert "\n" not in sanitized

        with pytest.raises(ValidationError):
            validate_scope_name(malicious_input)

    def test_log_injection_prevention(self) -> None:
        """Log injection attempts should be neutralized."""
        injection_attempt = "innocent\n[ERROR] Fake error message\nmalicious content"
        sanitized = sanitize_for_logging(injection_attempt)
        assert "\n" not in sanitized
        assert sanitized == "innocent[ERROR] Fake error messagemalicious content"

    def test_path_traversal_in_scope_name(self) -> None:
        """Path traversal attempts should be rejected."""
        with pytest.raises(ValidationError):
            validate_scope_name("../../../etc/passwd")

    def test_sql_injection_in_categories(self) -> None:
        """SQL injection attempts should be rejected."""
        with pytest.raises(ValidationError):
            validate_categories("valid.category'; DROP TABLE users; --")
