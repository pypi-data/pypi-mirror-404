"""
Tests for the RuleRegistry class.
"""

import pytest
from nitro_validator import RuleRegistry, Rule, RuleNotFoundError, InvalidRuleError


class DummyRule(Rule):
    """Dummy rule for testing."""

    name = "dummy"

    def validate(self, field, value, data):
        return True


class TestRuleRegistry:
    """Test the RuleRegistry class."""

    def test_registry_initialization(self):
        """Test that registry initializes correctly."""
        registry = RuleRegistry()
        assert registry is not None
        assert registry.all() == {}

    def test_register_rule(self):
        """Test registering a rule."""
        registry = RuleRegistry()
        registry.register(DummyRule)

        assert registry.has("dummy")
        assert registry.get("dummy") == DummyRule

    def test_register_rule_with_custom_name(self):
        """Test registering a rule with custom name."""
        registry = RuleRegistry()
        registry.register(DummyRule, "custom_name")

        assert registry.has("custom_name")
        assert registry.get("custom_name") == DummyRule

    def test_register_invalid_rule(self):
        """Test registering an invalid rule raises error."""
        registry = RuleRegistry()

        class NotARule:
            pass

        with pytest.raises(InvalidRuleError):
            registry.register(NotARule)

    def test_register_rule_without_name(self):
        """Test registering a rule without a name raises error."""
        registry = RuleRegistry()

        class NoNameRule(Rule):
            def validate(self, field, value, data):
                return True

        with pytest.raises(InvalidRuleError):
            registry.register(NoNameRule)

    def test_unregister_rule(self):
        """Test unregistering a rule."""
        registry = RuleRegistry()
        registry.register(DummyRule)

        assert registry.has("dummy")
        registry.unregister("dummy")
        assert not registry.has("dummy")

    def test_get_rule(self):
        """Test getting a rule from registry."""
        registry = RuleRegistry()
        registry.register(DummyRule)

        rule_class = registry.get("dummy")
        assert rule_class == DummyRule

    def test_get_nonexistent_rule(self):
        """Test getting a non-existent rule raises error."""
        registry = RuleRegistry()

        with pytest.raises(RuleNotFoundError):
            registry.get("nonexistent")

    def test_has_rule(self):
        """Test checking if rule exists."""
        registry = RuleRegistry()
        assert not registry.has("dummy")

        registry.register(DummyRule)
        assert registry.has("dummy")

    def test_all_rules(self):
        """Test getting all registered rules."""
        registry = RuleRegistry()
        registry.register(DummyRule)

        all_rules = registry.all()
        assert "dummy" in all_rules
        assert all_rules["dummy"] == DummyRule

    def test_clear_registry(self):
        """Test clearing all rules from registry."""
        registry = RuleRegistry()
        registry.register(DummyRule)

        assert len(registry.all()) > 0
        registry.clear()
        assert len(registry.all()) == 0
