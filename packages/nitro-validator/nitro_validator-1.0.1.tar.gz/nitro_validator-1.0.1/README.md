# Nitro Validate

A powerful, standalone, dependency-free data validation library for Python with extensible rules and a clean, intuitive API.

## Requirements

Python `3.7` or higher is required.

## Installation

```bash
pip install nitro-validator
```

## AI Assistant Integration

Add Nitro CLI knowledge to your AI coding assistant:

```bash
npx skills add nitrosh/nitro-validate
```

## Features

- **Simple API** - Easy to learn with minimal boilerplate
- **Zero Dependencies** - No external dependencies required
- **Extensible** - Create custom validation rules with ease
- **Clean Syntax** - Pipe-delimited rule strings or rule objects
- **Custom Messages** - Override default error messages per field or rule
- **Cross-field Validation** - Validate fields against other fields
- **Type Safe** - Validates strings, numbers, booleans, dates, and more
- **Comprehensive Rules** - 51+ built-in validation rules

## Quick Start

```python
from nitro_validator import NitroValidator

# Create a validator instance
validator = NitroValidator()

# Define your data and rules
data = {
    'email': 'user@example.com',
    'age': 25,
    'password': 'secret123',
    'confirm_password': 'secret123'
}

rules = {
    'email': 'required|email',
    'age': 'required|numeric|min:18',
    'password': 'required|min:8',
    'confirm_password': 'required|same:password'
}

# Validate
try:
    validated_data = validator.validate(data, rules)
    print("Validation passed!", validated_data)
except NitroValidationError as e:
    print("Validation failed:", e.errors)
```

**Note:** For convenience, you can also use `Validator` as an alias for `NitroValidator`, and `ValidationError` for `NitroValidationError`.

## Available Rules

### Basic Rules

| Rule       | Description                         | Example                     |
|------------|-------------------------------------|-----------------------------|
| `required` | Field must be present and not empty | `'email': 'required'`       |
| `optional` | Field is optional (always passes)   | `'middle_name': 'optional'` |

### String Rules

| Rule              | Description                           | Example                      |
|-------------------|---------------------------------------|------------------------------|
| `alpha`           | Only alphabetic characters            | `'name': 'alpha'`            |
| `alphanumeric`    | Only alphanumeric characters          | `'username': 'alphanumeric'` |
| `alpha_dash`      | Letters, numbers, dashes, underscores | `'slug': 'alpha_dash'`       |
| `lowercase`       | Only lowercase characters             | `'code': 'lowercase'`        |
| `uppercase`       | Only uppercase characters             | `'code': 'uppercase'`        |
| `email`           | Valid email address                   | `'email': 'email'`           |
| `url`             | Valid URL                             | `'website': 'url'`           |
| `uuid`            | Valid UUID                            | `'id': 'uuid'`               |
| `ip`              | Valid IP address (v4 or v6)           | `'address': 'ip'`            |
| `ipv4`            | Valid IPv4 address                    | `'address': 'ipv4'`          |
| `ipv6`            | Valid IPv6 address                    | `'address': 'ipv6'`          |
| `json`            | Valid JSON string                     | `'data': 'json'`             |
| `slug`            | Valid URL slug                        | `'slug': 'slug'`             |
| `ascii`           | Only ASCII characters                 | `'text': 'ascii'`            |
| `base64`          | Valid base64 encoding                 | `'encoded': 'base64'`        |
| `hex_color`       | Valid hex color code                  | `'color': 'hex_color'`       |
| `credit_card`     | Valid credit card number              | `'card': 'credit_card'`      |
| `mac_address`     | Valid MAC address                     | `'mac': 'mac_address'`       |
| `timezone`        | Valid timezone identifier             | `'tz': 'timezone'`           |
| `locale`          | Valid locale code                     | `'locale': 'locale'`         |
| `regex:pattern`   | Matches regex pattern                 | `'code': 'regex:^[A-Z]{3}$'` |
| `starts_with:str` | Starts with substring                 | `'name': 'starts_with:Mr'`   |
| `ends_with:str`   | Ends with substring                   | `'file': 'ends_with:.pdf'`   |
| `contains:str`    | Contains substring                    | `'text': 'contains:hello'`   |

### Numeric Rules

| Rule              | Description             | Example                    |
|-------------------|-------------------------|----------------------------|
| `numeric`         | Must be numeric         | `'price': 'numeric'`       |
| `integer`         | Must be an integer      | `'quantity': 'integer'`    |
| `positive`        | Must be positive number | `'amount': 'positive'`     |
| `negative`        | Must be negative number | `'deficit': 'negative'`    |
| `min:value`       | Minimum value or length | `'age': 'min:18'`          |
| `max:value`       | Maximum value or length | `'rating': 'max:5'`        |
| `between:min,max` | Between two values      | `'score': 'between:0,100'` |
| `divisible_by:n`  | Divisible by number     | `'even': 'divisible_by:2'` |

### Comparison Rules

| Rule               | Description                    | Example                               |
|--------------------|--------------------------------|---------------------------------------|
| `same:field`       | Must match another field       | `'password_confirm': 'same:password'` |
| `different:field`  | Must differ from another field | `'new_email': 'different:old_email'`  |
| `in:val1,val2`     | Must be in list of values      | `'role': 'in:admin,user,guest'`       |
| `not_in:val1,val2` | Must not be in list            | `'status': 'not_in:banned,deleted'`   |

### Boolean Rules

| Rule       | Description              | Example                  |
|------------|--------------------------|--------------------------|
| `boolean`  | Must be a boolean value  | `'active': 'boolean'`    |

### Date Rules

| Rule               | Description            | Example                             |
|--------------------|------------------------|-------------------------------------|
| `date`             | Must be a valid date   | `'birthdate': 'date'`               |
| `before:date`      | Date must be before    | `'start': 'before:2025-12-31'`      |
| `after:date`       | Date must be after     | `'end': 'after:2024-01-01'`         |
| `date_equals:date` | Date must equal        | `'today': 'date_equals:2024-11-23'` |
| `date_format:fmt`  | Date must match format | `'date': 'date_format:%Y-%m-%d'`    |

**Note:** The `date`, `before`, `after`, and `date_equals` rules accept unambiguous ISO 8601 formats only (`YYYY-MM-DD`, `YYYY/MM/DD`, and datetime variants like `YYYY-MM-DDTHH:MM:SS`). For specific regional formats like `DD-MM-YYYY` or `MM-DD-YYYY`, use the `date_format` rule with an explicit format string.

### Convenience Rules

| Rule        | Description                       | Example                   |
|-------------|-----------------------------------|---------------------------|
| `confirmed` | Matches {field}_confirmation      | `'password': 'confirmed'` |
| `accepted`  | Must be accepted (yes/true/1/on)  | `'terms': 'accepted'`     |
| `declined`  | Must be declined (no/false/0/off) | `'marketing': 'declined'` |

### Length Rules

| Rule           | Description         | Example                     |
|----------------|---------------------|-----------------------------|
| `length:value` | Exact length        | `'zip_code': 'length:5'`    |

### Collection Rules

| Rule       | Description                        | Example                     |
|------------|------------------------------------|-----------------------------|
| `array`    | Must be a list or tuple            | `'items': 'array'`          |
| `size:n`   | Exact size (length)                | `'tags': 'size:3'`          |
| `distinct` | Array must have unique values      | `'ids': 'distinct'`         |

## Usage Examples

### Basic Validation

```python
from nitro_validator import NitroValidator, NitroValidationError

validator = NitroValidator()

data = {'username': 'johndoe', 'age': '25'}
rules = {'username': 'required|alphanumeric', 'age': 'required|integer|min:18'}

try:
    validated = validator.validate(data, rules)
    print(validated)  # {'username': 'johndoe', 'age': '25'}
except NitroValidationError as e:
    print(e.errors)
```

### Custom Error Messages

```python
# Single message for all rules on a field
messages = {
    'email': 'Please provide a valid email address'
}

# Or specific messages per rule
messages = {
    'password': {
        'required': 'Password is required',
        'min': 'Password must be at least 8 characters'
    }
}

validator.validate(data, rules, messages)
```

### Using Rule Objects

```python
from nitro_validator import Validator, RequiredRule, EmailRule, MinRule

validator = Validator()

data = {'email': 'test@example.com', 'age': 25}
rules = {
    'email': [RequiredRule(), EmailRule()],
    'age': [RequiredRule(), MinRule(18)]
}

validated = validator.validate(data, rules)
```

### Check Validation Without Exception

```python
validator = Validator()

if validator.is_valid(data, rules):
    print("Data is valid!")
else:
    print("Errors:", validator.get_errors())
```

### Factory Method

```python
from nitro_validator import Validator

# Create and validate in one call
try:
    validator = Validator.make(data, rules)
    print("Valid:", validator.validated_data)
except ValidationError as e:
    print("Errors:", e.errors)
```

## Creating Custom Rules

Extend the `NitroValidationRule` class to create custom validation rules:

```python
from nitro_validator import NitroValidationRule, NitroValidator

class StrongPasswordRule(NitroValidationRule):
    """Validate that a password is strong."""

    name = "strong_password"
    message = "The {field} must contain uppercase, lowercase, numbers, and symbols."

    def validate(self, field: str, value: Any, data: dict) -> bool:
        if not value:
            return True

        has_upper = any(c.isupper() for c in value)
        has_lower = any(c.islower() for c in value)
        has_digit = any(c.isdigit() for c in value)
        has_symbol = any(c in '!@#$%^&*()_+-=' for c in value)

        return has_upper and has_lower and has_digit and has_symbol


# Register and use the custom rule
validator = NitroValidator()
validator.register_rule(StrongPasswordRule)

data = {'password': 'MyP@ssw0rd!'}
rules = {'password': 'required|strong_password'}

validated = validator.validate(data, rules)
```

**Backward Compatibility:** You can also use `Rule` as an alias for `NitroValidationRule` for convenience.

## Advanced Usage

### Cross-field Validation

```python
# Validate that one field matches another
data = {
    'password': 'secret123',
    'password_confirmation': 'secret123'
}

rules = {
    'password': 'required|min:8',
    'password_confirmation': 'required|same:password'
}

validator.validate(data, rules)
```

### Conditional Validation

```python
# Validate email only if user type is 'customer'
data = {'user_type': 'customer', 'email': 'user@example.com'}

if data.get('user_type') == 'customer':
    rules = {'email': 'required|email'}
else:
    rules = {'email': 'optional'}

validator.validate(data, rules)
```

### Handling Validation Errors

```python
from nitro_validator import ValidationError

try:
    validator.validate(data, rules)
except ValidationError as e:
    # Get all errors as a dictionary
    print(e.errors)  # {'email': ['Email is required'], 'age': ['Age must be at least 18']}

    # Or get flattened list of all error messages
    flat_errors = validator.get_errors_flat()
    print(flat_errors)  # ['Email is required', 'Age must be at least 18']
```

### Custom Rule Registry

```python
from nitro_validator import Validator, RuleRegistry

# Create a custom registry
registry = RuleRegistry()
registry.register(MyCustomRule)

# Use it with a validator
validator = Validator(registry=registry)
```

## Examples

The `examples/` directory contains working examples:

```bash
python examples/basic_usage.py
python examples/custom_rules.py
python examples/advanced_validation.py
```

## Development

### Setup

```bash
git clone https://github.com/nitro/nitro-validator.git
cd nitro-validator
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
pytest --cov=nitro_validator
```

### Format Code

```bash
black nitro_validator tests examples
```

## Why Nitro Validator?

- **No Dependencies**: Unlike other validation libraries, Nitro Validator has zero external dependencies
- **Extensible**: Easy to create and register custom validation rules
- **Clean API**: Simple, intuitive syntax that's easy to learn and use
- **Pythonic**: Follows Python best practices and idioms
- **Well-tested**: Comprehensive test suite with high code coverage
- **Type-safe**: Works with strings, numbers, booleans, dates, and custom types

## Comparison with GUMP

Nitro Validator is inspired by [GUMP](https://github.com/Wixel/GUMP) (a PHP validation library by the same author) but redesigned for Python with:

- More Pythonic API and conventions
- Better extensibility with the Rule class system
- Cleaner error handling with custom exceptions
- Type hints and modern Python features
- No external dependencies (GUMP requires PHP extensions)

## Ecosystem

- **[nitro-ui](https://github.com/nitrosh/nitro-ui)** - Programmatic HTML generation
- **[nitro-datastore](https://github.com/nitrosh/nitro-datastore)** - Data loading with dot notation access
- **[nitro-dispatch](https://github.com/nitrosh/nitro-dispatch)** - Plugin system
- **[nitro-validate](https://github.com/nitrosh/nitro-validate)** - Data validation

## License

This project is licensed under the BSD 3-Clause License. See the [LICENSE](LICENSE) file for details.