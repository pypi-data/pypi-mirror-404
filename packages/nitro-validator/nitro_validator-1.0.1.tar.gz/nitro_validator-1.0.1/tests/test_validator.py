"""
Tests for the Validator class.
"""

import pytest
from nitro_validator import Validator, ValidationError, RuleRegistry
from nitro_validator.utils import RequiredRule, EmailRule, MinRule


class TestValidator:
    """Test the Validator class."""

    def test_validator_initialization(self):
        """Test that validator initializes correctly."""
        validator = Validator()
        assert validator is not None
        assert isinstance(validator.registry, RuleRegistry)

    def test_basic_validation_passes(self):
        """Test basic validation with valid data."""
        validator = Validator()
        data = {"email": "test@example.com"}
        rules = {"email": "required|email"}

        result = validator.validate(data, rules)
        assert result == {"email": "test@example.com"}

    def test_basic_validation_fails(self):
        """Test basic validation with invalid data."""
        validator = Validator()
        data = {"email": "invalid-email"}
        rules = {"email": "required|email"}

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, rules)

        assert "email" in exc_info.value.errors
        assert len(exc_info.value.errors["email"]) > 0

    def test_multiple_rules_on_field(self):
        """Test multiple validation rules on a single field."""
        validator = Validator()
        data = {"password": "abc"}
        rules = {"password": "required|min:8"}

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, rules)

        assert "password" in exc_info.value.errors

    def test_validation_with_rule_objects(self):
        """Test validation using rule objects instead of strings."""
        validator = Validator()
        data = {"email": "test@example.com", "age": 25}
        rules = {"email": [RequiredRule(), EmailRule()], "age": [RequiredRule(), MinRule(18)]}

        result = validator.validate(data, rules)
        assert result == data

    def test_custom_error_messages_single(self):
        """Test custom error message for entire field."""
        validator = Validator()
        data = {"email": ""}
        rules = {"email": "required|email"}
        messages = {"email": "Please enter your email"}

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, rules, messages)

        assert exc_info.value.errors["email"][0] == "Please enter your email"

    def test_custom_error_messages_per_rule(self):
        """Test custom error messages per rule."""
        validator = Validator()
        data = {"password": ""}
        rules = {"password": "required|min:8"}
        messages = {
            "password": {
                "required": "Password is required",
                "min": "Password must be at least 8 characters",
            }
        }

        with pytest.raises(ValidationError) as exc_info:
            validator.validate(data, rules, messages)

        assert "Password is required" in exc_info.value.errors["password"]

    def test_is_valid_returns_true(self):
        """Test is_valid() returns True for valid data."""
        validator = Validator()
        data = {"email": "test@example.com"}
        rules = {"email": "required|email"}

        assert validator.is_valid(data, rules) is True

    def test_is_valid_returns_false(self):
        """Test is_valid() returns False for invalid data."""
        validator = Validator()
        data = {"email": "invalid"}
        rules = {"email": "required|email"}

        assert validator.is_valid(data, rules) is False

    def test_get_errors(self):
        """Test getting validation errors."""
        validator = Validator()
        data = {"email": "invalid"}
        rules = {"email": "email"}

        validator.is_valid(data, rules)
        errors = validator.get_errors()

        assert "email" in errors
        assert len(errors["email"]) > 0

    def test_get_errors_flat(self):
        """Test getting flattened error list."""
        validator = Validator()
        data = {"email": "", "age": "abc"}
        rules = {"email": "required|email", "age": "numeric"}

        validator.is_valid(data, rules)
        errors = validator.get_errors_flat()

        assert len(errors) >= 2
        assert all(isinstance(error, str) for error in errors)

    def test_static_make_method(self):
        """Test the static make() factory method."""
        data = {"email": "test@example.com"}
        rules = {"email": "required|email"}

        validator = Validator.make(data, rules)
        assert validator.validated_data == data

    def test_static_make_method_fails(self):
        """Test the static make() factory method with invalid data."""
        data = {"email": "invalid"}
        rules = {"email": "email"}

        with pytest.raises(ValidationError):
            Validator.make(data, rules)

    def test_empty_data(self):
        """Test validation with empty data."""
        validator = Validator()
        data = {}
        rules = {}

        result = validator.validate(data, rules)
        assert result == {}

    def test_optional_field_missing(self):
        """Test that optional fields don't fail when missing."""
        validator = Validator()
        data = {"name": "John"}
        rules = {"name": "required", "email": "optional|email"}

        result = validator.validate(data, rules)
        assert "name" in result

    def test_multiple_fields_validation(self):
        """Test validation of multiple fields."""
        validator = Validator()
        data = {"username": "johndoe", "email": "john@example.com", "age": 25}
        rules = {
            "username": "required|alphanumeric",
            "email": "required|email",
            "age": "required|numeric|min:18",
        }

        result = validator.validate(data, rules)
        assert result == data
