"""
Advanced validation examples.
"""

from nitro_validator import Validator, ValidationError, RequiredRule, EmailRule, MinRule, MaxRule


def example_rule_objects():
    """Example using Rule objects instead of strings."""
    print("=== Using Rule Objects ===\n")

    validator = Validator()

    data = {"email": "user@example.com", "age": 25, "bio": "Software developer"}

    # Define rules using objects instead of strings
    rules = {
        "email": [RequiredRule(), EmailRule()],
        "age": [RequiredRule(), MinRule(18), MaxRule(120)],
        "bio": [MaxRule(500)],
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ Validation passed!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


def example_complex_form():
    """Example of validating a complex form."""
    print("=== Complex Form Validation ===\n")

    validator = Validator()

    # User registration form data
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "age": 28,
        "country": "USA",
        "username": "johndoe123",
        "password": "SecureP@ss123",
        "password_confirm": "SecureP@ss123",
        "terms_accepted": True,
    }

    rules = {
        "first_name": "required|alpha|min:2|max:50",
        "last_name": "required|alpha|min:2|max:50",
        "email": "required|email",
        "age": "required|integer|min:18|max:120",
        "country": "required|in:USA,Canada,UK,Australia",
        "username": "required|alphanumeric|min:3|max:20",
        "password": "required|min:8|max:100",
        "password_confirm": "required|same:password",
        "terms_accepted": "required|boolean",
    }

    messages = {
        "first_name": {
            "required": "First name is required",
            "alpha": "First name must contain only letters",
            "min": "First name must be at least 2 characters",
        },
        "email": {
            "required": "Email address is required",
            "email": "Please enter a valid email address",
        },
        "password_confirm": {"same": "Passwords do not match"},
        "terms_accepted": "You must accept the terms and conditions",
    }

    try:
        validated = validator.validate(data, rules, messages)
        print("✓ Registration form validated successfully!")
        print(f"\nUser details:")
        for key, value in validated.items():
            if key != "password" and key != "password_confirm":
                print(f"  {key}: {value}")
        print()
    except ValidationError as e:
        print("✗ Form validation failed!")
        print("\nErrors:")
        for field, errors in e.errors.items():
            for error in errors:
                print(f"  - {field}: {error}")
        print()


def example_optional_fields():
    """Example with optional fields."""
    print("=== Optional Fields ===\n")

    validator = Validator()

    data = {
        "name": "John Doe",
        # middle_name is not provided (optional)
        # phone is not provided (optional)
    }

    rules = {"name": "required|alpha", "middle_name": "optional|alpha", "phone": "optional|numeric"}

    try:
        validated = validator.validate(data, rules)
        print("✓ Validation passed with optional fields!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


def example_list_validation():
    """Example validating list values."""
    print("=== List Validation ===\n")

    validator = Validator()

    data = {"tags": ["python", "validation", "library"], "scores": [85, 92, 78]}

    rules = {
        "tags": "required|min:1|max:10",  # Min/max checks list length
        "scores": "required|min:1",
    }

    try:
        validated = validator.validate(data, rules)
        print("✓ List validation passed!")
        print(f"Validated data: {validated}\n")
    except ValidationError as e:
        print("✗ Validation failed!")
        print(f"Errors: {e.errors}\n")


def example_conditional_validation():
    """Example of conditional validation logic."""
    print("=== Conditional Validation ===\n")

    validator = Validator()

    # Scenario 1: Corporate account (requires company info)
    print("Scenario 1: Corporate account")
    data1 = {"account_type": "corporate", "company_name": "Acme Inc", "tax_id": "12-3456789"}

    if data1.get("account_type") == "corporate":
        rules1 = {"company_name": "required|min:2", "tax_id": "required"}
    else:
        rules1 = {}

    try:
        validator.validate(data1, rules1)
        print("✓ Corporate account validated!\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")

    # Scenario 2: Personal account (company info not needed)
    print("Scenario 2: Personal account")
    data2 = {"account_type": "personal", "first_name": "John", "last_name": "Doe"}

    if data2.get("account_type") == "corporate":
        rules2 = {"company_name": "required|min:2", "tax_id": "required"}
    else:
        rules2 = {"first_name": "required", "last_name": "required"}

    try:
        validator.validate(data2, rules2)
        print("✓ Personal account validated!\n")
    except ValidationError as e:
        print(f"✗ Validation failed: {e.errors}\n")


if __name__ == "__main__":
    example_rule_objects()
    example_complex_form()
    example_optional_fields()
    example_list_validation()
    example_conditional_validation()
