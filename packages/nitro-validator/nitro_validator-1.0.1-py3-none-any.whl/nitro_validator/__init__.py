"""
Nitro Validator - A powerful, standalone, dependency-free data validation library.

Example:
    from nitro_validator import NitroValidator

    data = {'email': 'user@example.com', 'age': 25}
    rules = {'email': 'required|email', 'age': 'required|numeric|min:18'}

    validator = NitroValidator()
    validated = validator.validate(data, rules)
"""

__version__ = "1.0.0"

from .core import (
    NitroValidator,
    NitroValidationRule,
    NitroRuleRegistry,
    NitroValidationError,
    NitroValidatorException,
    NitroRuleNotFoundError,
    NitroInvalidRuleError,
)

from .utils import (
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
    AsciiRule,
    Base64Rule,
    HexColorRule,
    CreditCardRule,
    MacAddressRule,
    TimezoneRule,
    LocaleRule,
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
    ArrayRule,
    SizeRule,
    DistinctRule,
    register_builtin_rules,
)

# Auto-register built-in rules with default registry
_default_registry = NitroRuleRegistry()
register_builtin_rules(_default_registry)

# Override NitroValidator to use the default registry with built-in rules
_OriginalNitroValidator = NitroValidator


class NitroValidator(_OriginalNitroValidator):
    """
    NitroValidator with built-in rules pre-registered.
    """

    def __init__(self, registry=None):
        super().__init__(registry or _default_registry)


# Provide convenient aliases without "Nitro" prefix
Validator = NitroValidator
Rule = NitroValidationRule
RuleRegistry = NitroRuleRegistry
ValidationError = NitroValidationError
ValidatorException = NitroValidatorException
RuleNotFoundError = NitroRuleNotFoundError
InvalidRuleError = NitroInvalidRuleError


__all__ = [
    "__version__",
    # Nitro-prefixed classes (primary)
    "NitroValidator",
    "NitroValidationRule",
    "NitroRuleRegistry",
    "NitroValidationError",
    "NitroValidatorException",
    "NitroRuleNotFoundError",
    "NitroInvalidRuleError",
    # Convenient aliases (backward compatibility)
    "Validator",
    "Rule",
    "RuleRegistry",
    "ValidationError",
    "ValidatorException",
    "RuleNotFoundError",
    "InvalidRuleError",
    # Built-in rules
    "RequiredRule",
    "OptionalRule",
    "AlphaRule",
    "AlphanumericRule",
    "EmailRule",
    "UrlRule",
    "RegexRule",
    "LowercaseRule",
    "UppercaseRule",
    "AlphaDashRule",
    "StartsWithRule",
    "EndsWithRule",
    "ContainsRule",
    "UuidRule",
    "IpRule",
    "Ipv4Rule",
    "Ipv6Rule",
    "JsonRule",
    "SlugRule",
    "AsciiRule",
    "Base64Rule",
    "HexColorRule",
    "CreditCardRule",
    "MacAddressRule",
    "TimezoneRule",
    "LocaleRule",
    "NumericRule",
    "IntegerRule",
    "MinRule",
    "MaxRule",
    "BetweenRule",
    "PositiveRule",
    "NegativeRule",
    "DivisibleByRule",
    "SameRule",
    "DifferentRule",
    "InRule",
    "NotInRule",
    "BooleanRule",
    "DateRule",
    "BeforeRule",
    "AfterRule",
    "DateEqualsRule",
    "DateFormatRule",
    "ConfirmedRule",
    "AcceptedRule",
    "DeclinedRule",
    "LengthRule",
    "ArrayRule",
    "SizeRule",
    "DistinctRule",
    "register_builtin_rules",
]
