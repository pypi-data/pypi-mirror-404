"""
Base NitroValidationRule class for validation rules.
"""

from typing import Any


class NitroValidationRule:
    """
    Base class for all validation rules.

    Custom rules should inherit from NitroValidationRule and implement the validate() method.
    """

    name = None  # Rule name (e.g., 'required', 'email', 'min')
    message = "The {field} field is invalid."  # Default error message

    def __init__(self, *args, **kwargs):
        """
        Initialize the rule with optional parameters.

        Args:
            *args: Positional arguments for the rule (e.g., min value, max value)
            **kwargs: Keyword arguments (e.g., custom error message)
        """
        self.args = args
        self.kwargs = kwargs
        self.custom_message = kwargs.get("message")

    def validate(self, field: str, value: Any, data: dict) -> bool:
        """
        Validate the field value.

        Args:
            field: The field name being validated
            value: The value to validate
            data: The complete data dictionary (for cross-field validation)

        Returns:
            True if validation passes, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")

    def get_message(self, field: str) -> str:
        """
        Get the error message for this rule.

        Args:
            field: The field name being validated

        Returns:
            The formatted error message
        """
        message = self.custom_message or self.message

        # Replace placeholders in message
        replacements = {
            "{field}": field,
            "{args}": ", ".join(str(arg) for arg in self.args) if self.args else "",
        }

        # Add indexed args for specific replacements like {0}, {1}, etc.
        for i, arg in enumerate(self.args):
            replacements[f"{{{i}}}"] = str(arg)

        for placeholder, value in replacements.items():
            message = message.replace(placeholder, value)

        return message

    def __repr__(self):
        args_str = ", ".join(str(arg) for arg in self.args) if self.args else ""
        return f"{self.__class__.__name__}({args_str})"
