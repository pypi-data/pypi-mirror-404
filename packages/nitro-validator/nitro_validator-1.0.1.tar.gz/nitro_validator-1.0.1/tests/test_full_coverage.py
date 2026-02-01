"""
Tests to achieve 100% code coverage.
These tests cover edge cases and rarely-used code paths.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from nitro_validator import (
    Validator,
    NitroValidator,
    NitroValidationRule,
    NitroRuleRegistry,
    ValidationError,
)
from nitro_validator.utils import (
    RequiredRule,
    OptionalRule,
    AlphaRule,
    AlphanumericRule,
    EmailRule,
    UrlRule,
    RegexRule,
    LowercaseRule,
    UppercaseRule,
    AlphaDashRule,
    StartsWithRule,
    EndsWithRule,
    ContainsRule,
    UuidRule,
    IpRule,
    Ipv4Rule,
    Ipv6Rule,
    JsonRule,
    SlugRule,
    NumericRule,
    IntegerRule,
    MinRule,
    MaxRule,
    BetweenRule,
    PositiveRule,
    NegativeRule,
    DivisibleByRule,
    SameRule,
    DifferentRule,
    InRule,
    NotInRule,
    BooleanRule,
    DateRule,
    BeforeRule,
    AfterRule,
    DateEqualsRule,
    DateFormatRule,
    ConfirmedRule,
    AcceptedRule,
    DeclinedRule,
    LengthRule,
    AsciiRule,
    Base64Rule,
    HexColorRule,
    CreditCardRule,
    MacAddressRule,
    TimezoneRule,
    LocaleRule,
    ArrayRule,
    SizeRule,
    DistinctRule,
)


class TestBaseRuleCoverage:
    """Tests for base NitroValidationRule class."""

    def test_base_rule_not_implemented(self):
        """Test that base rule validate() raises NotImplementedError."""
        rule = NitroValidationRule()
        with pytest.raises(NotImplementedError):
            rule.validate("field", "value", {})

    def test_rule_repr_with_args(self):
        """Test __repr__ method with arguments."""
        rule = MinRule(5)
        assert repr(rule) == "MinRule(5)"

    def test_rule_repr_without_args(self):
        """Test __repr__ method without arguments."""
        rule = RequiredRule()
        assert repr(rule) == "RequiredRule()"

    def test_rule_repr_with_multiple_args(self):
        """Test __repr__ method with multiple arguments."""
        rule = BetweenRule(1, 10)
        assert repr(rule) == "BetweenRule(1, 10)"


class TestValidatorCoverage:
    """Tests for NitroValidator class edge cases."""

    def test_register_rule_returns_self(self):
        """Test that register_rule returns self for chaining."""
        validator = Validator()
        result = validator.register_rule(RequiredRule)
        assert result is validator

    def test_register_rule_chaining(self):
        """Test method chaining with register_rule."""

        class CustomRule(NitroValidationRule):
            name = "custom"

            def validate(self, field, value, data):
                return True

        validator = Validator().register_rule(CustomRule)
        assert validator.registry.has("custom")

    def test_invalid_rule_type_in_list_is_skipped(self):
        """Test that invalid rule types in rules list are skipped."""
        validator = Validator()
        data = {"field": "test@example.com"}
        # Include an integer (invalid rule type) in the rules list
        rules = {"field": [RequiredRule(), 123, None, "email"]}
        # Should not raise, just skip the invalid rules (123 and None)
        result = validator.validate(data, rules)
        assert result == {"field": "test@example.com"}


class TestStringRulesNonStringInput:
    """Test string rules with non-string input values."""

    def test_email_with_integer(self):
        """Test EmailRule with integer input."""
        rule = EmailRule()
        assert rule.validate("email", 123, {}) is False

    def test_email_with_list(self):
        """Test EmailRule with list input."""
        rule = EmailRule()
        assert rule.validate("email", ["test@example.com"], {}) is False

    def test_url_with_integer(self):
        """Test UrlRule with integer input."""
        rule = UrlRule()
        assert rule.validate("url", 123, {}) is False

    def test_regex_with_integer(self):
        """Test RegexRule with integer input."""
        rule = RegexRule(r"^\d+$")
        assert rule.validate("field", 123, {}) is False

    def test_regex_without_pattern(self):
        """Test RegexRule without pattern argument."""
        rule = RegexRule()
        assert rule.validate("field", "test", {}) is False

    def test_lowercase_with_integer(self):
        """Test LowercaseRule with integer input."""
        rule = LowercaseRule()
        assert rule.validate("field", 123, {}) is False

    def test_uppercase_with_integer(self):
        """Test UppercaseRule with integer input."""
        rule = UppercaseRule()
        assert rule.validate("field", 123, {}) is False

    def test_alpha_dash_with_integer(self):
        """Test AlphaDashRule with integer input."""
        rule = AlphaDashRule()
        assert rule.validate("field", 123, {}) is False

    def test_starts_with_non_string(self):
        """Test StartsWithRule with non-string input."""
        rule = StartsWithRule("Mr")
        assert rule.validate("field", 123, {}) is False

    def test_starts_with_no_args(self):
        """Test StartsWithRule without arguments."""
        rule = StartsWithRule()
        assert rule.validate("field", "Mr. Test", {}) is False

    def test_ends_with_non_string(self):
        """Test EndsWithRule with non-string input."""
        rule = EndsWithRule(".pdf")
        assert rule.validate("field", 123, {}) is False

    def test_ends_with_no_args(self):
        """Test EndsWithRule without arguments."""
        rule = EndsWithRule()
        assert rule.validate("field", "file.pdf", {}) is False

    def test_contains_non_string(self):
        """Test ContainsRule with non-string input."""
        rule = ContainsRule("hello")
        assert rule.validate("field", 123, {}) is False

    def test_contains_no_args(self):
        """Test ContainsRule without arguments."""
        rule = ContainsRule()
        assert rule.validate("field", "hello world", {}) is False

    def test_uuid_non_string(self):
        """Test UuidRule with non-string input."""
        rule = UuidRule()
        assert rule.validate("field", 123, {}) is False

    def test_ip_non_string(self):
        """Test IpRule with non-string input."""
        rule = IpRule()
        assert rule.validate("field", 123, {}) is False

    def test_ipv4_non_string(self):
        """Test Ipv4Rule with non-string input."""
        rule = Ipv4Rule()
        assert rule.validate("field", 123, {}) is False

    def test_ipv6_non_string(self):
        """Test Ipv6Rule with non-string input."""
        rule = Ipv6Rule()
        assert rule.validate("field", 123, {}) is False

    def test_json_non_string(self):
        """Test JsonRule with non-string input."""
        rule = JsonRule()
        assert rule.validate("field", 123, {}) is False

    def test_slug_non_string(self):
        """Test SlugRule with non-string input."""
        rule = SlugRule()
        assert rule.validate("field", 123, {}) is False


class TestNumericRulesEdgeCases:
    """Test numeric rules edge cases."""

    def test_numeric_with_non_numeric_type(self):
        """Test NumericRule with non-numeric type (list)."""
        rule = NumericRule()
        assert rule.validate("field", [1, 2, 3], {}) is False

    def test_min_with_float_string_arg(self):
        """Test MinRule with float string argument."""
        rule = MinRule("5.5")
        assert rule.validate("field", 6.0, {}) is True
        assert rule.validate("field", 5.0, {}) is False

    def test_min_with_collection(self):
        """Test MinRule with collection (list/dict/tuple)."""
        rule = MinRule(2)
        assert rule.validate("field", [1, 2, 3], {}) is True
        assert rule.validate("field", [1], {}) is False
        assert rule.validate("field", {"a": 1, "b": 2}, {}) is True
        assert rule.validate("field", (1, 2), {}) is True

    def test_min_with_invalid_type(self):
        """Test MinRule with invalid type."""
        rule = MinRule(5)
        assert rule.validate("field", object(), {}) is False

    def test_max_with_float_string_arg(self):
        """Test MaxRule with float string argument."""
        rule = MaxRule("5.5")
        assert rule.validate("field", 5.0, {}) is True
        assert rule.validate("field", 6.0, {}) is False

    def test_max_with_collection(self):
        """Test MaxRule with collection."""
        rule = MaxRule(2)
        assert rule.validate("field", [1, 2], {}) is True
        assert rule.validate("field", [1, 2, 3], {}) is False
        assert rule.validate("field", {"a": 1}, {}) is True
        assert rule.validate("field", (1,), {}) is True

    def test_max_with_invalid_type(self):
        """Test MaxRule with invalid type."""
        rule = MaxRule(5)
        assert rule.validate("field", object(), {}) is False

    def test_between_with_float_string_args(self):
        """Test BetweenRule with float string arguments."""
        rule = BetweenRule("1.5", "5.5")
        assert rule.validate("field", 3.0, {}) is True
        assert rule.validate("field", 1.0, {}) is False

    def test_between_missing_args(self):
        """Test BetweenRule with missing arguments."""
        rule = BetweenRule(1)  # Only one arg
        assert rule.validate("field", 5, {}) is False

    def test_between_with_collection(self):
        """Test BetweenRule with collection."""
        rule = BetweenRule(2, 5)
        assert rule.validate("field", [1, 2, 3], {}) is True
        assert rule.validate("field", [1], {}) is False
        assert rule.validate("field", {"a": 1, "b": 2, "c": 3}, {}) is True
        assert rule.validate("field", (1, 2, 3, 4), {}) is True

    def test_between_with_invalid_type(self):
        """Test BetweenRule with invalid type."""
        rule = BetweenRule(1, 10)
        assert rule.validate("field", object(), {}) is False

    def test_positive_with_invalid_string(self):
        """Test PositiveRule with non-numeric string."""
        rule = PositiveRule()
        assert rule.validate("field", "abc", {}) is False

    def test_positive_with_non_numeric_type(self):
        """Test PositiveRule with non-numeric type."""
        rule = PositiveRule()
        assert rule.validate("field", [1, 2], {}) is False

    def test_negative_with_invalid_string(self):
        """Test NegativeRule with non-numeric string."""
        rule = NegativeRule()
        assert rule.validate("field", "abc", {}) is False

    def test_negative_with_non_numeric_type(self):
        """Test NegativeRule with non-numeric type."""
        rule = NegativeRule()
        assert rule.validate("field", [1, 2], {}) is False

    def test_divisible_by_no_args(self):
        """Test DivisibleByRule without arguments."""
        rule = DivisibleByRule()
        assert rule.validate("field", 10, {}) is False

    def test_divisible_by_division_by_zero(self):
        """Test DivisibleByRule with zero divisor."""
        rule = DivisibleByRule(0)
        assert rule.validate("field", 10, {}) is False

    def test_divisible_by_invalid_value(self):
        """Test DivisibleByRule with invalid value."""
        rule = DivisibleByRule(2)
        assert rule.validate("field", "abc", {}) is False

    def test_divisible_by_non_numeric_type(self):
        """Test DivisibleByRule with non-numeric type."""
        rule = DivisibleByRule(2)
        assert rule.validate("field", [10], {}) is False


class TestComparisonRulesEdgeCases:
    """Test comparison rules edge cases."""

    def test_same_no_args(self):
        """Test SameRule without arguments."""
        rule = SameRule()
        assert rule.validate("field", "value", {}) is False

    def test_different_no_args(self):
        """Test DifferentRule without arguments."""
        rule = DifferentRule()
        assert rule.validate("field", "value", {}) is False

    def test_in_with_none(self):
        """Test InRule with None value."""
        rule = InRule("a", "b", "c")
        assert rule.validate("field", None, {}) is True

    def test_not_in_with_none(self):
        """Test NotInRule with None value."""
        rule = NotInRule("a", "b", "c")
        assert rule.validate("field", None, {}) is True


class TestDateRulesEdgeCases:
    """Test date rules edge cases."""

    def test_date_with_datetime_object(self):
        """Test DateRule with datetime object."""
        rule = DateRule()
        assert rule.validate("field", datetime.now(), {}) is True

    def test_date_with_non_string(self):
        """Test DateRule with non-string, non-datetime input."""
        rule = DateRule()
        assert rule.validate("field", 123, {}) is False

    def test_before_no_args(self):
        """Test BeforeRule without arguments."""
        rule = BeforeRule()
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_before_invalid_value_date(self):
        """Test BeforeRule with invalid value date."""
        rule = BeforeRule("2025-12-31")
        assert rule.validate("field", "not-a-date", {}) is False

    def test_before_invalid_compare_date(self):
        """Test BeforeRule with invalid comparison date."""
        rule = BeforeRule("not-a-date")
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_before_with_datetime_value(self):
        """Test BeforeRule _parse_date with datetime object."""
        rule = BeforeRule("2025-12-31")
        assert rule.validate("field", datetime(2024, 1, 1), {}) is True

    def test_before_with_non_string_value(self):
        """Test BeforeRule _parse_date with non-string."""
        rule = BeforeRule("2025-12-31")
        assert rule.validate("field", 123, {}) is False

    def test_after_no_args(self):
        """Test AfterRule without arguments."""
        rule = AfterRule()
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_after_invalid_value_date(self):
        """Test AfterRule with invalid value date."""
        rule = AfterRule("2020-01-01")
        assert rule.validate("field", "not-a-date", {}) is False

    def test_after_invalid_compare_date(self):
        """Test AfterRule with invalid comparison date."""
        rule = AfterRule("not-a-date")
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_after_with_datetime_value(self):
        """Test AfterRule _parse_date with datetime object."""
        rule = AfterRule("2020-01-01")
        assert rule.validate("field", datetime(2024, 1, 1), {}) is True

    def test_after_with_non_string_value(self):
        """Test AfterRule _parse_date with non-string."""
        rule = AfterRule("2020-01-01")
        assert rule.validate("field", 123, {}) is False

    def test_date_equals_no_args(self):
        """Test DateEqualsRule without arguments."""
        rule = DateEqualsRule()
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_date_equals_invalid_value_date(self):
        """Test DateEqualsRule with invalid value date."""
        rule = DateEqualsRule("2024-01-01")
        assert rule.validate("field", "not-a-date", {}) is False

    def test_date_equals_invalid_compare_date(self):
        """Test DateEqualsRule with invalid comparison date."""
        rule = DateEqualsRule("not-a-date")
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_date_equals_with_datetime_value(self):
        """Test DateEqualsRule _parse_date with datetime object."""
        rule = DateEqualsRule("2024-01-01")
        assert rule.validate("field", datetime(2024, 1, 1), {}) is True

    def test_date_equals_with_non_string_value(self):
        """Test DateEqualsRule _parse_date with non-string."""
        rule = DateEqualsRule("2024-01-01")
        assert rule.validate("field", 123, {}) is False

    def test_date_format_no_args(self):
        """Test DateFormatRule without arguments."""
        rule = DateFormatRule()
        assert rule.validate("field", "2024-01-01", {}) is False

    def test_date_format_non_string(self):
        """Test DateFormatRule with non-string input."""
        rule = DateFormatRule("%Y-%m-%d")
        assert rule.validate("field", 123, {}) is False


class TestLengthRulesEdgeCases:
    """Test length rules edge cases."""

    def test_length_no_args(self):
        """Test LengthRule without arguments."""
        rule = LengthRule()
        assert rule.validate("field", "test", {}) is False

    def test_length_with_invalid_type(self):
        """Test LengthRule with invalid type (number)."""
        rule = LengthRule(5)
        assert rule.validate("field", 12345, {}) is False


class TestContentRulesEdgeCases:
    """Test content rules edge cases."""

    def test_ascii_non_string(self):
        """Test AsciiRule with non-string input."""
        rule = AsciiRule()
        assert rule.validate("field", 123, {}) is False

    def test_base64_non_string(self):
        """Test Base64Rule with non-string input."""
        rule = Base64Rule()
        assert rule.validate("field", 123, {}) is False

    def test_hex_color_non_string(self):
        """Test HexColorRule with non-string input."""
        rule = HexColorRule()
        assert rule.validate("field", 123, {}) is False

    def test_credit_card_non_string(self):
        """Test CreditCardRule with non-string input."""
        rule = CreditCardRule()
        assert rule.validate("field", 123, {}) is False

    def test_credit_card_too_short(self):
        """Test CreditCardRule with too short number."""
        rule = CreditCardRule()
        assert rule.validate("field", "123456", {}) is False

    def test_mac_address_non_string(self):
        """Test MacAddressRule with non-string input."""
        rule = MacAddressRule()
        assert rule.validate("field", 123, {}) is False

    def test_timezone_non_string(self):
        """Test TimezoneRule with non-string input."""
        rule = TimezoneRule()
        assert rule.validate("field", 123, {}) is False

    def test_locale_non_string(self):
        """Test LocaleRule with non-string input."""
        rule = LocaleRule()
        assert rule.validate("field", 123, {}) is False

    def test_locale_exception_path(self):
        """Test LocaleRule valid locale path."""
        rule = LocaleRule()
        # A valid locale should pass
        assert rule.validate("field", "en_US", {}) is True
        assert rule.validate("field", "pt_BR", {}) is True


class TestCollectionRulesEdgeCases:
    """Test collection rules edge cases."""

    def test_size_no_args(self):
        """Test SizeRule without arguments."""
        rule = SizeRule()
        assert rule.validate("field", [1, 2, 3], {}) is False

    def test_size_with_float_string_arg(self):
        """Test SizeRule with float string argument."""
        rule = SizeRule("3.0")
        assert rule.validate("field", 3.0, {}) is True

    def test_size_with_invalid_type(self):
        """Test SizeRule with invalid type."""
        rule = SizeRule(5)
        assert rule.validate("field", object(), {}) is False

    def test_distinct_with_unhashable_items(self):
        """Test DistinctRule with unhashable items (dicts)."""
        rule = DistinctRule()
        # List of dicts (unhashable) - all unique
        assert rule.validate("field", [{"a": 1}, {"b": 2}], {}) is True
        # List of dicts with duplicates
        assert rule.validate("field", [{"a": 1}, {"a": 1}], {}) is False

    def test_distinct_with_unhashable_unique_items(self):
        """Test DistinctRule with unhashable unique items."""
        rule = DistinctRule()
        assert rule.validate("field", [{"a": 1}, {"a": 2}, {"b": 1}], {}) is True


class TestEmptyStringValues:
    """Test rules with empty string values to cover early return paths."""

    def test_max_with_empty_string(self):
        """Test MaxRule with empty string value."""
        rule = MaxRule(10)
        assert rule.validate("field", "", {}) is True

    def test_max_with_integer_string_arg(self):
        """Test MaxRule with integer string argument."""
        rule = MaxRule("10")
        assert rule.validate("field", 5, {}) is True

    def test_between_with_empty_string(self):
        """Test BetweenRule with empty string value."""
        rule = BetweenRule(1, 10)
        assert rule.validate("field", "", {}) is True

    def test_between_with_integer_string_args(self):
        """Test BetweenRule with integer string arguments."""
        rule = BetweenRule("1", "10")
        assert rule.validate("field", 5, {}) is True

    def test_boolean_with_empty_string(self):
        """Test BooleanRule with empty string value."""
        rule = BooleanRule()
        assert rule.validate("field", "", {}) is True

    def test_length_with_empty_string(self):
        """Test LengthRule with empty string value."""
        rule = LengthRule(5)
        assert rule.validate("field", "", {}) is True

    def test_size_with_empty_string(self):
        """Test SizeRule with empty string value."""
        rule = SizeRule(5)
        assert rule.validate("field", "", {}) is True


class TestLocaleExceptionPath:
    """Test LocaleRule exception path."""

    def test_locale_with_invalid_pattern_but_valid_format(self):
        """Test LocaleRule catches exceptions in locale validation."""
        rule = LocaleRule()
        # These should still work - valid pattern
        assert rule.validate("field", "en", {}) is True
        assert rule.validate("field", "en_US", {}) is True
        # Invalid pattern should fail
        assert rule.validate("field", "invalid_locale_code_xyz", {}) is False