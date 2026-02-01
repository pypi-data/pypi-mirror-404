"""
Main NitroValidator class for validating data.
"""

from typing import Dict, Any, List, Union, Optional
from .rule import NitroValidationRule
from .rule_registry import NitroRuleRegistry
from .exceptions import NitroValidationError


class NitroValidator:
    """
    Main validator class for validating data against rules.

    Example:
        validator = NitroValidator()
        validator.validate(
            {'email': 'user@example.com', 'age': 25},
            {'email': 'required|email', 'age': 'required|numeric|min:18'}
        )
    """

    def __init__(self, registry: Optional[NitroRuleRegistry] = None):
        """
        Initialize the validator.

        Args:
            registry: Optional custom NitroRuleRegistry instance
        """
        self.registry = registry or NitroRuleRegistry()
        self.errors: Dict[str, List[str]] = {}
        self.validated_data: Dict[str, Any] = {}

    def register_rule(self, rule_class: type, name: Optional[str] = None):
        """
        Register a custom validation rule.

        Args:
            rule_class: The Rule class to register
            name: Optional custom name for the rule

        Returns:
            Self for method chaining
        """
        self.registry.register(rule_class, name)
        return self

    def validate(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List[Union[str, NitroValidationRule]]]],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
    ) -> Dict[str, Any]:
        """
        Validate data against rules.

        Args:
            data: The data to validate
            rules: Dictionary of field names to validation rules
            messages: Optional custom error messages

        Returns:
            The validated data

        Raises:
            NitroValidationError: If validation fails

        Example:
            validator.validate(
                {'email': 'test@example.com'},
                {'email': 'required|email'}
            )

            # Or with rule objects
            validator.validate(
                {'age': 25},
                {'age': [RequiredRule(), NumericRule(), MinRule(18)]}
            )

            # Or with custom messages
            validator.validate(
                {'email': ''},
                {'email': 'required|email'},
                {'email': 'Please provide a valid email address'}
            )
        """
        self.errors = {}
        self.validated_data = {}
        messages = messages or {}

        for field, field_rules in rules.items():
            value = data.get(field)

            # Parse rules if they're a string
            if isinstance(field_rules, str):
                parsed_rules = self._parse_rules(field_rules)
            else:
                parsed_rules = field_rules

            # Validate each rule
            for rule in parsed_rules:
                # Create rule instance if it's a string
                if isinstance(rule, str):
                    rule_instance = self._create_rule_from_string(rule)
                elif isinstance(rule, NitroValidationRule):
                    rule_instance = rule
                else:
                    continue

                # Check if field has custom messages
                field_messages = messages.get(field, {})
                if isinstance(field_messages, str):
                    # Single message for all rules
                    rule_instance.custom_message = field_messages
                elif isinstance(field_messages, dict):
                    # Specific message for this rule
                    rule_name = rule_instance.name or rule_instance.__class__.__name__.lower()
                    if rule_name in field_messages:
                        rule_instance.custom_message = field_messages[rule_name]

                # Run validation
                if not rule_instance.validate(field, value, data):
                    if field not in self.errors:
                        self.errors[field] = []
                    self.errors[field].append(rule_instance.get_message(field))

            # Add to validated data if no errors
            if field not in self.errors:
                self.validated_data[field] = value

        # Raise exception if there are errors
        if self.errors:
            raise NitroValidationError(self.errors)

        return self.validated_data

    def is_valid(
        self,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List[Union[str, NitroValidationRule]]]],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
    ) -> bool:
        """
        Check if data is valid without raising an exception.

        Args:
            data: The data to validate
            rules: Dictionary of field names to validation rules
            messages: Optional custom error messages

        Returns:
            True if valid, False otherwise
        """
        try:
            self.validate(data, rules, messages)
            return True
        except NitroValidationError:
            return False

    def get_errors(self) -> Dict[str, List[str]]:
        """
        Get validation errors.

        Returns:
            Dictionary of field names to error messages
        """
        return self.errors

    def get_errors_flat(self) -> List[str]:
        """
        Get all error messages as a flat list.

        Returns:
            List of all error messages
        """
        flat_errors = []
        for field_errors in self.errors.values():
            flat_errors.extend(field_errors)
        return flat_errors

    def _parse_rules(self, rules_string: str) -> List[str]:
        """
        Parse a pipe-delimited rule string.

        Args:
            rules_string: String like "required|email|min:5"

        Returns:
            List of rule strings
        """
        return [rule.strip() for rule in rules_string.split("|") if rule.strip()]

    def _create_rule_from_string(self, rule_string: str) -> NitroValidationRule:
        """
        Create a NitroValidationRule instance from a string.

        Args:
            rule_string: String like "min:5" or "required"

        Returns:
            NitroValidationRule instance

        Raises:
            NitroRuleNotFoundError: If the rule is not found
        """
        # Parse rule name and arguments
        if ":" in rule_string:
            rule_name, args_string = rule_string.split(":", 1)
            args = [arg.strip() for arg in args_string.split(",")]
        else:
            rule_name = rule_string
            args = []

        # Get rule class from registry
        rule_class = self.registry.get(rule_name)

        # Create and return rule instance
        return rule_class(*args)

    @classmethod
    def make(
        cls,
        data: Dict[str, Any],
        rules: Dict[str, Union[str, List[Union[str, NitroValidationRule]]]],
        messages: Optional[Dict[str, Union[str, Dict[str, str]]]] = None,
        registry: Optional[NitroRuleRegistry] = None,
    ) -> "NitroValidator":
        """
        Factory method to create a validator and validate data in one call.

        Args:
            data: The data to validate
            rules: Dictionary of field names to validation rules
            messages: Optional custom error messages
            registry: Optional custom NitroRuleRegistry instance

        Returns:
            NitroValidator instance with validation results

        Raises:
            NitroValidationError: If validation fails
        """
        validator = cls(registry)
        validator.validate(data, rules, messages)
        return validator
