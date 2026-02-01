"""
Custom exception classes for nitro-validator.
"""


class NitroValidatorException(Exception):
    """Base exception for all validator errors."""

    pass


class NitroValidationError(NitroValidatorException):
    """
    Raised when validation fails.

    Attributes:
        errors: Dictionary of field names to error messages
    """

    def __init__(self, errors):
        self.errors = errors
        super().__init__(f"Validation failed: {errors}")


class NitroRuleNotFoundError(NitroValidatorException):
    """Raised when a validation rule is not found."""

    pass


class NitroInvalidRuleError(NitroValidatorException):
    """Raised when a rule is invalid or improperly defined."""

    pass
