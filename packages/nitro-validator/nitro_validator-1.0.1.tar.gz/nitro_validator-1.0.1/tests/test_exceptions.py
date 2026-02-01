"""
Tests for custom exceptions.
"""

import pytest
from nitro_validator import ValidatorException, ValidationError, RuleNotFoundError, InvalidRuleError


class TestExceptions:
    """Test custom exception classes."""

    def test_validator_exception(self):
        """Test base ValidatorException."""
        exc = ValidatorException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_validation_error(self):
        """Test ValidationError with errors dict."""
        errors = {"email": ["Email is required"], "age": ["Age must be 18+"]}
        exc = ValidationError(errors)

        assert exc.errors == errors
        assert "email" in str(exc)

    def test_rule_not_found_error(self):
        """Test RuleNotFoundError."""
        exc = RuleNotFoundError("Rule 'custom' not found")
        assert "custom" in str(exc)
        assert isinstance(exc, ValidatorException)

    def test_invalid_rule_error(self):
        """Test InvalidRuleError."""
        exc = InvalidRuleError("Invalid rule definition")
        assert "Invalid" in str(exc)
        assert isinstance(exc, ValidatorException)
