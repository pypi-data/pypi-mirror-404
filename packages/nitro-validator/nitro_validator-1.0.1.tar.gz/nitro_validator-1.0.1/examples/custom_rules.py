"""
Example of creating and using custom validation rules.
"""

from typing import Any
from nitro_validator import Validator, Rule, ValidationError


class StrongPasswordRule(Rule):
    """
    Validate that a password is strong.

    A strong password must contain:
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """

    name = "strong_password"
    message = "The {field} must contain uppercase, lowercase, numbers, and special characters."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not value:
            return True

        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value)

        return has_upper and has_lower and has_digit and has_symbol


class UsernameRule(Rule):
    """
    Validate that a username is valid.

    A valid username:
    - Must be 3-20 characters
    - Can only contain letters, numbers, underscores, and hyphens
    - Must start with a letter
    """

    name = "username"
    message = "The {field} must be 3-20 characters and start with a letter."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not value:
            return True

        if not isinstance(value, str):
            return False

        if len(value) < 3 or len(value) > 20:
            return False

        if not value[0].isalpha():
            return False

        import re

        return bool(re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*$", value))


class PhoneNumberRule(Rule):
    """Validate that a phone number is in valid format."""

    name = "phone"
    message = "The {field} must be a valid phone number (e.g., +1-555-123-4567)."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not value:
            return True

        import re

        # Simple phone number pattern
        pattern = r"^\+?[1-9]\d{0,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}$"
        return bool(re.match(pattern, value))


def example_custom_rule():
    """Example using custom validation rules."""
    print("=== Custom Rules Example ===\n")

    validator = Validator()

    # Register custom rules
    validator.register_rule(StrongPasswordRule)
    validator.register_rule(UsernameRule)
    validator.register_rule(PhoneNumberRule)

    # Test with valid data
    data = {"username": "john_doe", "password": "MyP@ssw0rd!", "phone": "+1-555-123-4567"}

    rules = {
        "username": "required|username",
        "password": "required|strong_password",
        "phone": "required|phone",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ All validations passed!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


def example_weak_password():
    """Example with weak password."""
    print("=== Weak Password Example ===\n")

    validator = Validator()
    validator.register_rule(StrongPasswordRule)

    data = {"password": "weakpass"}
    rules = {"password": "required|strong_password"}

    try:
        validator.validate(data, rules)
    except ValidationError as e:
        print("✗ Validation failed as expected:")
        for field, errors in e.errors.items():
            for error in errors:
                print(f"  - {error}")
        print()


def example_invalid_username():
    """Example with invalid username."""
    print("=== Invalid Username Example ===\n")

    validator = Validator()
    validator.register_rule(UsernameRule)

    # Test various invalid usernames
    test_cases = [
        ("1invalid", "starts with number"),
        ("ab", "too short"),
        ("this-username-is-way-too-long-to-be-valid", "too long"),
        ("user@name", "contains invalid character"),
    ]

    for username, reason in test_cases:
        data = {"username": username}
        rules = {"username": "username"}

        try:
            validator.validate(data, rules)
            print(f"✓ '{username}' passed (unexpected!)")
        except ValidationError:
            print(f"✗ '{username}' failed ({reason})")

    print()


if __name__ == "__main__":
    example_custom_rule()
    example_weak_password()
    example_invalid_username()
