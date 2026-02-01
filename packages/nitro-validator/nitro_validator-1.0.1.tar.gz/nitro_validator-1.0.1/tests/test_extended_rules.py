"""
Tests for extended validation rules (high and medium priority validators).
"""

import pytest
from datetime import datetime, timedelta
from nitro_validator.utils import (
    # High priority string rules
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
    # High priority numeric rules
    PositiveRule,
    NegativeRule,
    DivisibleByRule,
    # High priority date rules
    BeforeRule,
    AfterRule,
    DateEqualsRule,
    DateFormatRule,
    # High priority convenience rules
    ConfirmedRule,
    AcceptedRule,
    DeclinedRule,
    # Medium priority string rules
    AsciiRule,
    Base64Rule,
    HexColorRule,
    CreditCardRule,
    MacAddressRule,
    TimezoneRule,
    LocaleRule,
    # Medium priority collection rules
    ArrayRule,
    SizeRule,
    DistinctRule,
)


class TestExtendedStringRules:
    """Test extended string validation rules."""

    def test_lowercase_rule_passes(self):
        """Test LowercaseRule with valid data."""
        rule = LowercaseRule()
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "world123", {}) is True
        assert rule.validate("field", "", {}) is True
        assert rule.validate("field", None, {}) is True

    def test_lowercase_rule_fails(self):
        """Test LowercaseRule with invalid data."""
        rule = LowercaseRule()
        assert rule.validate("field", "Hello", {}) is False
        assert rule.validate("field", "WORLD", {}) is False

    def test_uppercase_rule_passes(self):
        """Test UppercaseRule with valid data."""
        rule = UppercaseRule()
        assert rule.validate("field", "HELLO", {}) is True
        assert rule.validate("field", "WORLD123", {}) is True
        assert rule.validate("field", "", {}) is True
        assert rule.validate("field", None, {}) is True

    def test_uppercase_rule_fails(self):
        """Test UppercaseRule with invalid data."""
        rule = UppercaseRule()
        assert rule.validate("field", "Hello", {}) is False
        assert rule.validate("field", "world", {}) is False

    def test_alpha_dash_rule_passes(self):
        """Test AlphaDashRule with valid data."""
        rule = AlphaDashRule()
        assert rule.validate("field", "hello-world", {}) is True
        assert rule.validate("field", "hello_world", {}) is True
        assert rule.validate("field", "hello123", {}) is True
        assert rule.validate("field", "hello-world_123", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_alpha_dash_rule_fails(self):
        """Test AlphaDashRule with invalid data."""
        rule = AlphaDashRule()
        assert rule.validate("field", "hello world", {}) is False
        assert rule.validate("field", "hello@world", {}) is False
        assert rule.validate("field", "hello.world", {}) is False

    def test_starts_with_rule_passes(self):
        """Test StartsWithRule with valid data."""
        rule = StartsWithRule("Mr")
        assert rule.validate("field", "Mr Smith", {}) is True
        assert rule.validate("field", "Mr", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_starts_with_rule_fails(self):
        """Test StartsWithRule with invalid data."""
        rule = StartsWithRule("Mr")
        assert rule.validate("field", "Dr Smith", {}) is False
        assert rule.validate("field", "Smith", {}) is False

    def test_ends_with_rule_passes(self):
        """Test EndsWithRule with valid data."""
        rule = EndsWithRule(".pdf")
        assert rule.validate("field", "document.pdf", {}) is True
        assert rule.validate("field", ".pdf", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_ends_with_rule_fails(self):
        """Test EndsWithRule with invalid data."""
        rule = EndsWithRule(".pdf")
        assert rule.validate("field", "document.txt", {}) is False
        assert rule.validate("field", "document", {}) is False

    def test_contains_rule_passes(self):
        """Test ContainsRule with valid data."""
        rule = ContainsRule("hello")
        assert rule.validate("field", "say hello world", {}) is True
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_contains_rule_fails(self):
        """Test ContainsRule with invalid data."""
        rule = ContainsRule("hello")
        assert rule.validate("field", "goodbye world", {}) is False
        assert rule.validate("field", "helo", {}) is False

    def test_uuid_rule_passes(self):
        """Test UuidRule with valid UUIDs."""
        rule = UuidRule()
        assert rule.validate("field", "550e8400-e29b-41d4-a716-446655440000", {}) is True
        assert rule.validate("field", "6ba7b810-9dad-11d1-80b4-00c04fd430c8", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_uuid_rule_fails(self):
        """Test UuidRule with invalid UUIDs."""
        rule = UuidRule()
        assert rule.validate("field", "not-a-uuid", {}) is False
        assert rule.validate("field", "550e8400-e29b-41d4-a716", {}) is False

    def test_ip_rule_passes(self):
        """Test IpRule with valid IP addresses."""
        rule = IpRule()
        assert rule.validate("field", "192.168.1.1", {}) is True
        assert rule.validate("field", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_ip_rule_fails(self):
        """Test IpRule with invalid IP addresses."""
        rule = IpRule()
        assert rule.validate("field", "999.999.999.999", {}) is False
        assert rule.validate("field", "not-an-ip", {}) is False

    def test_ipv4_rule_passes(self):
        """Test Ipv4Rule with valid IPv4 addresses."""
        rule = Ipv4Rule()
        assert rule.validate("field", "192.168.1.1", {}) is True
        assert rule.validate("field", "10.0.0.1", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_ipv4_rule_fails(self):
        """Test Ipv4Rule with invalid IPv4 addresses."""
        rule = Ipv4Rule()
        assert rule.validate("field", "999.999.999.999", {}) is False
        assert rule.validate("field", "2001:0db8:85a3::8a2e:0370:7334", {}) is False

    def test_ipv6_rule_passes(self):
        """Test Ipv6Rule with valid IPv6 addresses."""
        rule = Ipv6Rule()
        assert rule.validate("field", "2001:0db8:85a3:0000:0000:8a2e:0370:7334", {}) is True
        assert rule.validate("field", "2001:db8:85a3::8a2e:370:7334", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_ipv6_rule_fails(self):
        """Test Ipv6Rule with invalid IPv6 addresses."""
        rule = Ipv6Rule()
        assert rule.validate("field", "192.168.1.1", {}) is False
        assert rule.validate("field", "not-an-ipv6", {}) is False

    def test_json_rule_passes(self):
        """Test JsonRule with valid JSON strings."""
        rule = JsonRule()
        assert rule.validate("field", '{"key": "value"}', {}) is True
        assert rule.validate("field", "[1, 2, 3]", {}) is True
        assert rule.validate("field", '"string"', {}) is True
        assert rule.validate("field", "123", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_json_rule_fails(self):
        """Test JsonRule with invalid JSON strings."""
        rule = JsonRule()
        assert rule.validate("field", "{key: value}", {}) is False
        assert rule.validate("field", "{'key': 'value'}", {}) is False
        assert rule.validate("field", "not json", {}) is False

    def test_slug_rule_passes(self):
        """Test SlugRule with valid slugs."""
        rule = SlugRule()
        assert rule.validate("field", "hello-world", {}) is True
        assert rule.validate("field", "hello-world-123", {}) is True
        assert rule.validate("field", "123-abc", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_slug_rule_fails(self):
        """Test SlugRule with invalid slugs."""
        rule = SlugRule()
        assert rule.validate("field", "hello_world", {}) is False
        assert rule.validate("field", "Hello-World", {}) is False
        assert rule.validate("field", "hello world", {}) is False
        assert rule.validate("field", "hello--world", {}) is False


class TestExtendedNumericRules:
    """Test extended numeric validation rules."""

    def test_positive_rule_passes(self):
        """Test PositiveRule with valid data."""
        rule = PositiveRule()
        assert rule.validate("field", 1, {}) is True
        assert rule.validate("field", 100, {}) is True
        assert rule.validate("field", 0.1, {}) is True
        assert rule.validate("field", "10", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_positive_rule_fails(self):
        """Test PositiveRule with invalid data."""
        rule = PositiveRule()
        assert rule.validate("field", -1, {}) is False
        assert rule.validate("field", -0.1, {}) is False
        assert rule.validate("field", 0, {}) is False

    def test_negative_rule_passes(self):
        """Test NegativeRule with valid data."""
        rule = NegativeRule()
        assert rule.validate("field", -1, {}) is True
        assert rule.validate("field", -100, {}) is True
        assert rule.validate("field", -0.1, {}) is True
        assert rule.validate("field", "-10", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_negative_rule_fails(self):
        """Test NegativeRule with invalid data."""
        rule = NegativeRule()
        assert rule.validate("field", 1, {}) is False
        assert rule.validate("field", 0.1, {}) is False
        assert rule.validate("field", 0, {}) is False

    def test_divisible_by_rule_passes(self):
        """Test DivisibleByRule with valid data."""
        rule = DivisibleByRule(2)
        assert rule.validate("field", 2, {}) is True
        assert rule.validate("field", 4, {}) is True
        assert rule.validate("field", 100, {}) is True
        assert rule.validate("field", "", {}) is True

    def test_divisible_by_rule_fails(self):
        """Test DivisibleByRule with invalid data."""
        rule = DivisibleByRule(2)
        assert rule.validate("field", 1, {}) is False
        assert rule.validate("field", 3, {}) is False
        assert rule.validate("field", 5, {}) is False

    def test_divisible_by_rule_with_string_arg(self):
        """Test DivisibleByRule with string argument."""
        rule = DivisibleByRule("3")
        assert rule.validate("field", 6, {}) is True
        assert rule.validate("field", 9, {}) is True
        assert rule.validate("field", 7, {}) is False


class TestExtendedDateRules:
    """Test extended date validation rules."""

    def test_before_rule_passes(self):
        """Test BeforeRule with valid dates."""
        rule = BeforeRule("2025-12-31")
        assert rule.validate("field", "2024-01-01", {}) is True
        assert rule.validate("field", "2025-06-15", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_before_rule_fails(self):
        """Test BeforeRule with invalid dates."""
        rule = BeforeRule("2024-01-01")
        assert rule.validate("field", "2024-12-31", {}) is False
        assert rule.validate("field", "2025-01-01", {}) is False

    def test_after_rule_passes(self):
        """Test AfterRule with valid dates."""
        rule = AfterRule("2024-01-01")
        assert rule.validate("field", "2024-12-31", {}) is True
        assert rule.validate("field", "2025-01-01", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_after_rule_fails(self):
        """Test AfterRule with invalid dates."""
        rule = AfterRule("2025-12-31")
        assert rule.validate("field", "2024-01-01", {}) is False
        assert rule.validate("field", "2025-06-15", {}) is False

    def test_date_equals_rule_passes(self):
        """Test DateEqualsRule with valid dates."""
        rule = DateEqualsRule("2024-11-23")
        assert rule.validate("field", "2024-11-23", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_date_equals_rule_fails(self):
        """Test DateEqualsRule with invalid dates."""
        rule = DateEqualsRule("2024-11-23")
        assert rule.validate("field", "2024-11-24", {}) is False
        assert rule.validate("field", "2024-11-22", {}) is False

    def test_date_format_rule_passes(self):
        """Test DateFormatRule with valid formats."""
        rule = DateFormatRule("%Y-%m-%d")
        assert rule.validate("field", "2024-11-23", {}) is True
        assert rule.validate("field", "2024-01-01", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_date_format_rule_fails(self):
        """Test DateFormatRule with invalid formats."""
        rule = DateFormatRule("%Y-%m-%d")
        assert rule.validate("field", "11/23/2024", {}) is False
        assert rule.validate("field", "23-11-2024", {}) is False
        assert rule.validate("field", "not-a-date", {}) is False


class TestConvenienceRules:
    """Test convenience validation rules."""

    def test_confirmed_rule_passes(self):
        """Test ConfirmedRule with valid data."""
        rule = ConfirmedRule()
        data = {"password": "secret123", "password_confirmation": "secret123"}
        assert rule.validate("password", "secret123", data) is True

    def test_confirmed_rule_fails(self):
        """Test ConfirmedRule with invalid data."""
        rule = ConfirmedRule()
        data = {"password": "secret123", "password_confirmation": "different"}
        assert rule.validate("password", "secret123", data) is False

    def test_confirmed_rule_missing_confirmation(self):
        """Test ConfirmedRule with missing confirmation field."""
        rule = ConfirmedRule()
        data = {"password": "secret123"}
        assert rule.validate("password", "secret123", data) is False

    def test_accepted_rule_passes(self):
        """Test AcceptedRule with valid data."""
        rule = AcceptedRule()
        assert rule.validate("field", "yes", {}) is True
        assert rule.validate("field", "on", {}) is True
        assert rule.validate("field", "1", {}) is True
        assert rule.validate("field", 1, {}) is True
        assert rule.validate("field", True, {}) is True
        assert rule.validate("field", "true", {}) is True

    def test_accepted_rule_fails(self):
        """Test AcceptedRule with invalid data."""
        rule = AcceptedRule()
        assert rule.validate("field", "no", {}) is False
        assert rule.validate("field", "off", {}) is False
        assert rule.validate("field", "0", {}) is False
        assert rule.validate("field", 0, {}) is False
        assert rule.validate("field", False, {}) is False

    def test_declined_rule_passes(self):
        """Test DeclinedRule with valid data."""
        rule = DeclinedRule()
        assert rule.validate("field", "no", {}) is True
        assert rule.validate("field", "off", {}) is True
        assert rule.validate("field", "0", {}) is True
        assert rule.validate("field", 0, {}) is True
        assert rule.validate("field", False, {}) is True
        assert rule.validate("field", "false", {}) is True

    def test_declined_rule_fails(self):
        """Test DeclinedRule with invalid data."""
        rule = DeclinedRule()
        assert rule.validate("field", "yes", {}) is False
        assert rule.validate("field", "on", {}) is False
        assert rule.validate("field", "1", {}) is False
        assert rule.validate("field", 1, {}) is False
        assert rule.validate("field", True, {}) is False


class TestMediumPriorityStringRules:
    """Test medium priority string validation rules."""

    def test_ascii_rule_passes(self):
        """Test AsciiRule with valid data."""
        rule = AsciiRule()
        assert rule.validate("field", "hello world", {}) is True
        assert rule.validate("field", "ABC123!@#", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_ascii_rule_fails(self):
        """Test AsciiRule with invalid data."""
        rule = AsciiRule()
        assert rule.validate("field", "hello 世界", {}) is False
        assert rule.validate("field", "café", {}) is False

    def test_base64_rule_passes(self):
        """Test Base64Rule with valid data."""
        rule = Base64Rule()
        assert rule.validate("field", "SGVsbG8gV29ybGQ=", {}) is True
        assert rule.validate("field", "YWJjMTIz", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_base64_rule_fails(self):
        """Test Base64Rule with invalid data."""
        rule = Base64Rule()
        assert rule.validate("field", "not-valid-base64!@#", {}) is False
        assert rule.validate("field", "hello world", {}) is False

    def test_hex_color_rule_passes(self):
        """Test HexColorRule with valid data."""
        rule = HexColorRule()
        assert rule.validate("field", "#ffffff", {}) is True
        assert rule.validate("field", "#fff", {}) is True
        assert rule.validate("field", "#000000", {}) is True
        assert rule.validate("field", "#abc", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_hex_color_rule_fails(self):
        """Test HexColorRule with invalid data."""
        rule = HexColorRule()
        assert rule.validate("field", "#gggggg", {}) is False
        assert rule.validate("field", "ffffff", {}) is False
        assert rule.validate("field", "#ff", {}) is False
        assert rule.validate("field", "#fffffff", {}) is False

    def test_credit_card_rule_passes(self):
        """Test CreditCardRule with valid data."""
        rule = CreditCardRule()
        # Test Visa card
        assert rule.validate("field", "4532015112830366", {}) is True
        # Test MasterCard
        assert rule.validate("field", "5425233430109903", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_credit_card_rule_fails(self):
        """Test CreditCardRule with invalid data."""
        rule = CreditCardRule()
        assert rule.validate("field", "1234567890123456", {}) is False
        assert rule.validate("field", "1111111111111111", {}) is False
        assert rule.validate("field", "not-a-card", {}) is False

    def test_mac_address_rule_passes(self):
        """Test MacAddressRule with valid data."""
        rule = MacAddressRule()
        assert rule.validate("field", "00:1B:44:11:3A:B7", {}) is True
        assert rule.validate("field", "00-1B-44-11-3A-B7", {}) is True
        assert rule.validate("field", "001B44113AB7", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_mac_address_rule_fails(self):
        """Test MacAddressRule with invalid data."""
        rule = MacAddressRule()
        assert rule.validate("field", "00:1B:44:11:3A", {}) is False
        assert rule.validate("field", "invalid-mac", {}) is False
        assert rule.validate("field", "00:GG:44:11:3A:B7", {}) is False

    def test_timezone_rule_passes(self):
        """Test TimezoneRule with valid data."""
        rule = TimezoneRule()
        assert rule.validate("field", "America/New_York", {}) is True
        assert rule.validate("field", "Europe/London", {}) is True
        assert rule.validate("field", "Asia/Tokyo", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_timezone_rule_fails(self):
        """Test TimezoneRule with invalid data."""
        rule = TimezoneRule()
        assert rule.validate("field", "invalid-timezone", {}) is False
        assert rule.validate("field", "123-456", {}) is False

    def test_locale_rule_passes(self):
        """Test LocaleRule with valid data."""
        rule = LocaleRule()
        assert rule.validate("field", "en_US", {}) is True
        assert rule.validate("field", "pt_BR", {}) is True
        assert rule.validate("field", "fr_FR", {}) is True
        assert rule.validate("field", "", {}) is True

    def test_locale_rule_fails(self):
        """Test LocaleRule with invalid data."""
        rule = LocaleRule()
        assert rule.validate("field", "invalid", {}) is False
        assert rule.validate("field", "en_us", {}) is False
        assert rule.validate("field", "123", {}) is False


class TestCollectionRules:
    """Test collection validation rules."""

    def test_array_rule_passes(self):
        """Test ArrayRule with valid data."""
        rule = ArrayRule()
        assert rule.validate("field", [1, 2, 3], {}) is True
        assert rule.validate("field", (1, 2, 3), {}) is True
        assert rule.validate("field", [], {}) is True
        assert rule.validate("field", None, {}) is True

    def test_array_rule_fails(self):
        """Test ArrayRule with invalid data."""
        rule = ArrayRule()
        assert rule.validate("field", "not an array", {}) is False
        assert rule.validate("field", 123, {}) is False
        assert rule.validate("field", {"key": "value"}, {}) is False

    def test_size_rule_with_array(self):
        """Test SizeRule with arrays."""
        rule = SizeRule(3)
        assert rule.validate("field", [1, 2, 3], {}) is True
        assert rule.validate("field", (1, 2, 3), {}) is True
        assert rule.validate("field", [1, 2], {}) is False
        assert rule.validate("field", [1, 2, 3, 4], {}) is False

    def test_size_rule_with_string(self):
        """Test SizeRule with strings."""
        rule = SizeRule(5)
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hi", {}) is False
        assert rule.validate("field", "hello world", {}) is False

    def test_size_rule_with_number(self):
        """Test SizeRule with numbers."""
        rule = SizeRule(10)
        assert rule.validate("field", 10, {}) is True
        assert rule.validate("field", 5, {}) is False
        assert rule.validate("field", 15, {}) is False

    def test_size_rule_with_string_arg(self):
        """Test SizeRule with string argument."""
        rule = SizeRule("5")
        assert rule.validate("field", "hello", {}) is True
        assert rule.validate("field", "hi", {}) is False

    def test_distinct_rule_passes(self):
        """Test DistinctRule with valid data."""
        rule = DistinctRule()
        assert rule.validate("field", [1, 2, 3, 4], {}) is True
        assert rule.validate("field", ["a", "b", "c"], {}) is True
        assert rule.validate("field", [], {}) is True
        assert rule.validate("field", None, {}) is True

    def test_distinct_rule_fails(self):
        """Test DistinctRule with invalid data."""
        rule = DistinctRule()
        assert rule.validate("field", [1, 2, 2, 3], {}) is False
        assert rule.validate("field", ["a", "b", "a"], {}) is False
        assert rule.validate("field", [1, 1, 1], {}) is False

    def test_distinct_rule_with_non_array(self):
        """Test DistinctRule with non-array data."""
        rule = DistinctRule()
        # Should return False for non-array values (requires array)
        assert rule.validate("field", "not an array", {}) is False
        assert rule.validate("field", 123, {}) is False
