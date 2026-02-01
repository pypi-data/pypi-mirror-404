"""
Rule registry for managing validation rules.
"""

from typing import Dict, Type, Optional
from .rule import NitroValidationRule
from .exceptions import NitroRuleNotFoundError, NitroInvalidRuleError


class NitroRuleRegistry:
    """
    Registry for storing and retrieving validation rules.

    This allows users to register custom rules and access built-in rules.
    """

    def __init__(self):
        """Initialize the rule registry."""
        self._rules: Dict[str, Type[NitroValidationRule]] = {}

    def register(self, rule_class: Type[NitroValidationRule], name: Optional[str] = None):
        """
        Register a validation rule.

        Args:
            rule_class: The NitroValidationRule class to register
            name: Optional custom name for the rule (defaults to rule_class.name)

        Raises:
            NitroInvalidRuleError: If the rule class is invalid
        """
        if not issubclass(rule_class, NitroValidationRule):
            raise NitroInvalidRuleError(f"{rule_class} must inherit from NitroValidationRule")

        rule_name = name or rule_class.name

        if not rule_name:
            raise NitroInvalidRuleError(
                f"Rule {rule_class} must have a 'name' attribute or provide a name parameter"
            )

        self._rules[rule_name] = rule_class

    def unregister(self, name: str):
        """
        Unregister a validation rule.

        Args:
            name: The name of the rule to unregister
        """
        if name in self._rules:
            del self._rules[name]

    def get(self, name: str) -> Type[NitroValidationRule]:
        """
        Get a rule class by name.

        Args:
            name: The name of the rule

        Returns:
            The NitroValidationRule class

        Raises:
            NitroRuleNotFoundError: If the rule is not found
        """
        if name not in self._rules:
            raise NitroRuleNotFoundError(f"Rule '{name}' not found in registry")

        return self._rules[name]

    def has(self, name: str) -> bool:
        """
        Check if a rule exists in the registry.

        Args:
            name: The name of the rule

        Returns:
            True if the rule exists, False otherwise
        """
        return name in self._rules

    def all(self) -> Dict[str, Type[NitroValidationRule]]:
        """
        Get all registered rules.

        Returns:
            Dictionary of rule names to NitroValidationRule classes
        """
        return self._rules.copy()

    def clear(self):
        """Clear all registered rules."""
        self._rules.clear()
