"""
Tests for built-in validation rules.
"""

import pytest
from nitro_validator.utils import (
    RequiredRule,
    OptionalRule,
    AlphaRule,
    AlphanumericRule,
    EmailRule,
    UrlRule,
    RegexRule,
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    BooleanRule,
    DateRule,
    LengthRule,
)


class TestBasicRules:
    """Test basic validation rules."""

    def test_required_rule_passes(self):
        """Test RequiredRule with valid data."""
        rule = RequiredRule()
        assert rule.validate("field", "value", {}) is True
        assert rule.validate("field", 123, {}) is True
        assert rule.validate("field", ["a"], {}) is True

    def test_required_rule_fails(self):
        """Test RequiredRule with invalid data."""
        rule = RequiredRule()
        assert rule.validate("field", None, {}) is False
        assert rule.validate("field", "", {}) is False
        assert rule.validate("field", "   ", {}) is False
        assert rule.validate("field", [], {}) is False
        assert rule.validate("field", {}, {}) is False

    def test_optional_rule(self):
        """Test OptionalRule always passes."""
        rule = OptionalRule()
        assert rule.validate("field", None, {}) is True
        assert rule.validate("field", "", {}) is True
        assert rule.validate("field", "value", {}) is True


class TestStringRules:
    """Test string validation rules."""

    def test_alpha_rule_passes(self):
        """Test AlphaRule with valid data."""
        rule = AlphaRule()
        assert rule.validate("field", "abc", {}) is True
        assert rule.validate("field", "ABC", {}) is True
        assert rule.validate("field", "", {}) is True
        assert rule.validate("field", None, {}) is True

    def test_alpha_rule_fails(self):
        """Test AlphaRule with invalid data."""
        rule = AlphaRule()
        assert rule.validate("field", "abc123", {}) is False
        assert rule.validate("field", "abc def", {}) is False
        assert rule.validate("field", "abc-def", {}) is False

    def test_alphanumeric_rule_passes(self):
        """Test AlphanumericRule with valid data."""
        rule = AlphanumericRule()
        assert rule.validate("field", "abc123", {}) is True
        assert rule.validate("field", "ABC123", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_alphanumeric_rule_fails(self):
        """Test AlphanumericRule with invalid data."""
        rule = AlphanumericRule()
        assert rule.validate("field", "abc 123", {}) is False
        assert rule.validate("field", "abc-123", {}) is False

    def test_email_rule_passes(self):
        """Test EmailRule with valid emails."""
        rule = EmailRule()
        assert rule.validate("field", "test@example.com", {}) is True
        assert rule.validate("field", "user.name@example.co.uk", {}) is True
        assert rule.validate("field", "user+tag@example.com", {}) is True
        assert rule.validate("field", "", {}) is True
        assert rule.validate("field", None, {}) is True

    def test_email_rule_fails(self):
        """Test EmailRule with invalid emails."""
        rule = EmailRule()
        assert rule.validate("field", "invalid", {}) is False
        assert rule.validate("field", "invalid@", {}) is False
        assert rule.validate("field", "@example.com", {}) is False
        assert rule.validate("field", "user@", {}) is False

    def test_url_rule_passes(self):
        """Test UrlRule with valid URLs."""
        rule = UrlRule()
        assert rule.validate("field", "http://example.com", {}) is True
        assert rule.validate("field", "https://example.com", {}) is True
        assert rule.validate("field", "http://example.com/path", {}) is True
        assert rule.validate("field", "http://localhost:8000", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_url_rule_fails(self):
        """Test UrlRule with invalid URLs."""
        rule = UrlRule()
        assert rule.validate("field", "example.com", {}) is False
        assert rule.validate("field", "ftp://example.com", {}) is False
        assert rule.validate("field", "not a url", {}) is False

    def test_regex_rule_passes(self):
        """Test RegexRule with valid patterns."""
        rule = RegexRule(r"^[A-Z]{3}$")
        assert rule.validate("field", "ABC", {}) is True
        assert rule.validate("field", "XYZ", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_regex_rule_fails(self):
        """Test RegexRule with invalid patterns."""
        rule = RegexRule(r"^[A-Z]{3}$")
        assert rule.validate("field", "abc", {}) is False
        assert rule.validate("field", "ABCD", {}) is False
        assert rule.validate("field", "AB", {}) is False


class TestNumericRules:
    """Test numeric validation rules."""

    def test_numeric_rule_passes(self):
        """Test NumericRule with valid numbers."""
        rule = NumericRule()
        assert rule.validate("field", 123, {}) is True
        assert rule.validate("field", 123.45, {}) is True
        assert rule.validate("field", "123", {}) is True
        assert rule.validate("field", "123.45", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_numeric_rule_fails(self):
        """Test NumericRule with invalid data."""
        rule = NumericRule()
        assert rule.validate("field", "abc", {}) is False
        assert rule.validate("field", "12abc", {}) is False

    def test_integer_rule_passes(self):
        """Test IntegerRule with valid integers."""
        rule = IntegerRule()
        assert rule.validate("field", 123, {}) is True
        assert rule.validate("field", "123", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_integer_rule_fails(self):
        """Test IntegerRule with invalid data."""
        rule = IntegerRule()
        assert rule.validate("field", 123.45, {}) is False
        assert rule.validate("field", "123.45", {}) is False
        assert rule.validate("field", "abc", {}) is False
        assert rule.validate("field", True, {}) is False

    def test_min_rule_with_numbers(self):
        """Test MinRule with numeric values."""
        rule = MinRule(18)
        assert rule.validate("field", 18, {}) is True
        assert rule.validate("field", 25, {}) is True
        assert rule.validate("field", 17, {}) is False

    def test_min_rule_with_strings(self):
        """Test MinRule with string length."""
        rule = MinRule(5)
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hello world", {}) is True
        assert rule.validate("field", "hi", {}) is False

    def test_min_rule_with_string_arg(self):
        """Test MinRule with string argument."""
        rule = MinRule("18")
        assert rule.validate("field", 20, {}) is True
        assert rule.validate("field", 15, {}) is False

    def test_max_rule_with_numbers(self):
        """Test MaxRule with numeric values."""
        rule = MaxRule(100)
        assert rule.validate("field", 50, {}) is True
        assert rule.validate("field", 100, {}) is True
        assert rule.validate("field", 101, {}) is False

    def test_max_rule_with_strings(self):
        """Test MaxRule with string length."""
        rule = MaxRule(10)
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hello world!", {}) is False

    def test_between_rule_with_numbers(self):
        """Test BetweenRule with numeric values."""
        rule = BetweenRule(18, 65)
        assert rule.validate("field", 18, {}) is True
        assert rule.validate("field", 30, {}) is True
        assert rule.validate("field", 65, {}) is True
        assert rule.validate("field", 17, {}) is False
        assert rule.validate("field", 66, {}) is False

    def test_between_rule_with_strings(self):
        """Test BetweenRule with string length."""
        rule = BetweenRule(5, 10)
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hello world", {}) is False
        assert rule.validate("field", "hi", {}) is False


class TestComparisonRules:
    """Test comparison validation rules."""

    def test_same_rule_passes(self):
        """Test SameRule with matching fields."""
        rule = SameRule("password")
        data = {"password": "secret123", "password_confirm": "secret123"}
        assert rule.validate("password_confirm", "secret123", data) is True

    def test_same_rule_fails(self):
        """Test SameRule with non-matching fields."""
        rule = SameRule("password")
        data = {"password": "secret123", "password_confirm": "different"}
        assert rule.validate("password_confirm", "different", data) is False

    def test_different_rule_passes(self):
        """Test DifferentRule with different values."""
        rule = DifferentRule("old_email")
        data = {"old_email": "old@example.com", "new_email": "new@example.com"}
        assert rule.validate("new_email", "new@example.com", data) is True

    def test_different_rule_fails(self):
        """Test DifferentRule with same values."""
        rule = DifferentRule("old_email")
        data = {"old_email": "same@example.com", "new_email": "same@example.com"}
        assert rule.validate("new_email", "same@example.com", data) is False

    def test_in_rule_passes(self):
        """Test InRule with valid values."""
        rule = InRule("admin", "user", "guest")
        assert rule.validate("role", "admin", {}) is True
        assert rule.validate("role", "user", {}) is True
        assert rule.validate("role", "guest", {}) is True

    def test_in_rule_fails(self):
        """Test InRule with invalid values."""
        rule = InRule("admin", "user", "guest")
        assert rule.validate("role", "superadmin", {}) is False

    def test_not_in_rule_passes(self):
        """Test NotInRule with valid values."""
        rule = NotInRule("banned", "deleted")
        assert rule.validate("status", "active", {}) is True
        assert rule.validate("status", "pending", {}) is True

    def test_not_in_rule_fails(self):
        """Test NotInRule with invalid values."""
        rule = NotInRule("banned", "deleted")
        assert rule.validate("status", "banned", {}) is False
        assert rule.validate("status", "deleted", {}) is False


class TestBooleanRules:
    """Test boolean validation rules."""

    def test_boolean_rule_passes(self):
        """Test BooleanRule with valid boolean values."""
        rule = BooleanRule()
        assert rule.validate("field", True, {}) is True
        assert rule.validate("field", False, {}) is True
        assert rule.validate("field", "true", {}) is True
        assert rule.validate("field", "false", {}) is True
        assert rule.validate("field", 1, {}) is True
        assert rule.validate("field", 0, {}) is True
        assert rule.validate("field", "yes", {}) is True
        assert rule.validate("field", "no", {}) is True

    def test_boolean_rule_fails(self):
        """Test BooleanRule with invalid values."""
        rule = BooleanRule()
        assert rule.validate("field", "invalid", {}) is False
        assert rule.validate("field", 2, {}) is False


class TestDateRules:
    """Test date validation rules."""

    def test_date_rule_passes(self):
        """Test DateRule with valid dates (ISO 8601 formats only)."""
        rule = DateRule()
        assert rule.validate("field", "2024-01-15", {}) is True
        assert rule.validate("field", "2024/01/15", {}) is True
        assert rule.validate("field", "2024-01-15T10:30:00", {}) is True
        assert rule.validate("field", "", {}) is True

        from datetime import datetime

        assert rule.validate("field", datetime.now(), {}) is True

    def test_date_rule_fails(self):
        """Test DateRule with invalid dates."""
        rule = DateRule()
        assert rule.validate("field", "not-a-date", {}) is False
        assert rule.validate("field", "2024-13-45", {}) is False


class TestLengthRules:
    """Test length validation rules."""

    def test_length_rule_with_string(self):
        """Test LengthRule with strings."""
        rule = LengthRule(5)
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hi", {}) is False
        assert rule.validate("field", "hello world", {}) is False

    def test_length_rule_with_list(self):
        """Test LengthRule with lists."""
        rule = LengthRule(3)
        assert rule.validate("field", [1, 2, 3], {}) is True
        assert rule.validate("field", [1, 2], {}) is False


class TestRuleMessages:
    """Test rule error messages."""

    def test_default_message(self):
        """Test that rules have default messages."""
        rule = RequiredRule()
        message = rule.get_message("username")
        assert "username" in message

    def test_custom_message(self):
        """Test custom error messages."""
        rule = RequiredRule(message="Custom error for {field}")
        message = rule.get_message("email")
        assert message == "Custom error for email"

    def test_message_with_args(self):
        """Test messages with arguments."""
        rule = MinRule(18)
        message = rule.get_message("age")
        assert "18" in message
