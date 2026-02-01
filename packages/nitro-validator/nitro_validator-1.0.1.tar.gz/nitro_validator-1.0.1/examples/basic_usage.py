"""
Basic usage examples for nitro-validator.
"""

from nitro_validator import Validator, ValidationError


def example_basic_validation():
    """Basic validation example."""
    print("=== Basic Validation ===\n")

    validator = Validator()

    data = {"username": "john_doe", "email": "john@example.com", "age": 25}

    rules = {
        "username": "required|alphanumeric",
        "email": "required|email",
        "age": "required|numeric|min:18",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Validation passed!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


def example_validation_failure():
    """Example of failed validation."""
    print("=== Validation Failure ===\n")

    validator = Validator()

    data = {"email": "not-an-email", "age": 15}

    rules = {"email": "required|email", "age": "required|numeric|min:18"}

    try:
        validator.validate(data, rules)
    except ValidationError as e:
        print("✗ Validation failed as expected!")
        print(f"Errors: {e.errors}")
        print(f"\nFlat error list: {validator.get_errors_flat()}\n")


def example_custom_messages():
    """Example with custom error messages."""
    print("=== Custom Error Messages ===\n")

    validator = Validator()

    data = {"password": "123"}

    rules = {"password": "required|min:8"}

    messages = {
        "password": {
            "required": "Please enter a password",
            "min": "Your password must be at least 8 characters long",
        }
    }

    try:
        validator.validate(data, rules, messages)
    except ValidationError as e:
        print("✗ Validation failed with custom messages:")
        for field, errors in e.errors.items():
            for error in errors:
                print(f"  - {error}")
        print()


def example_is_valid():
    """Example using is_valid() method."""
    print("=== Using is_valid() ===\n")

    validator = Validator()

    data = {"email": "test@example.com"}
    rules = {"email": "required|email"}

    if validator.is_valid(data, rules):
        print("✓ Data is valid!")
    else:
        print("✗ Data is invalid!")
        print(f"Errors: {validator.get_errors()}")
    print()


def example_cross_field_validation():
    """Example of cross-field validation."""
    print("=== Cross-field Validation ===\n")

    validator = Validator()

    data = {"password": "mySecretPass123", "password_confirmation": "mySecretPass123"}

    rules = {"password": "required|min:8", "password_confirmation": "required|same:password"}

    try:
        validated = validator.validate(data, rules)
        print("✓ Passwords match!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


if __name__ == "__main__":
    example_basic_validation()
    example_validation_failure()
    example_custom_messages()
    example_is_valid()
    example_cross_field_validation()
