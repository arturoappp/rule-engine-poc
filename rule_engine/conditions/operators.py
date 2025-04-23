"""
Operator implementations for value conditions.
"""

import re
from typing import Any, Dict, Callable, Type


class Operator:
    """Base class for operators."""

    @staticmethod
    def get_operator_function(operator_name: str) -> Callable[[Any, Any], bool]:
        """
        Get the operator function for a given operator name.

        Args:
            operator_name: Name of the operator

        Returns:
            Function that implements the operator

        Raises:
            ValueError: If the operator is not supported
        """
        operators = {
            # Equality operators
            'equal': Operator.equal,
            'eq': Operator.equal,
            '=': Operator.equal,
            'not_equal': Operator.not_equal,
            'neq': Operator.not_equal,

            # Comparison operators
            'greater_than': Operator.greater_than,
            'gt': Operator.greater_than,
            'less_than': Operator.less_than,
            'lt': Operator.less_than,
            'greater_than_equal': Operator.greater_than_equal,
            'gte': Operator.greater_than_equal,
            'less_than_equal': Operator.less_than_equal,
            'lte': Operator.less_than_equal,

            # Existence operators
            'exists': Operator.exists,
            'not_empty': Operator.not_empty,

            # String operators
            'match': Operator.match,
            'matches': Operator.match,
            'contains': Operator.contains,

            # List operators
            'in_list': Operator.in_list,
            'not_in_list': lambda actual, expected: not Operator.in_list(actual, expected),

            # Device Rules
            'role_device': Operator.role_device,

            # Length operators
            'max_length': Operator.max_length,
            'exact_length': Operator.exact_length,
        }

        if operator_name not in operators:
            raise ValueError(f"Unsupported operator: {operator_name}")

        return operators[operator_name]

    @staticmethod
    def equal(actual: Any, expected: Any) -> bool:
        """Equal operator implementation."""
        return actual == expected

    @staticmethod
    def not_equal(actual: Any, expected: Any) -> bool:
        """Not equal operator implementation."""
        return actual != expected

    @staticmethod
    def greater_than(actual: Any, expected: Any) -> bool:
        """Greater than operator implementation."""
        try:
            return float(actual) > float(expected)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def less_than(actual: Any, expected: Any) -> bool:
        """Less than operator implementation."""
        try:
            return float(actual) < float(expected)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def greater_than_equal(actual: Any, expected: Any) -> bool:
        """Greater than or equal operator implementation."""
        try:
            return float(actual) >= float(expected)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def less_than_equal(actual: Any, expected: Any) -> bool:
        """Less than or equal operator implementation."""
        try:
            return float(actual) <= float(expected)
        except (TypeError, ValueError):
            return False

    @staticmethod
    def exists(actual: Any, expected: Any) -> bool:
        """Exists operator implementation."""
        return (actual is not None) == expected

    @staticmethod
    def not_empty(actual: Any, expected: Any) -> bool:
        """Not empty operator implementation."""
        if actual is None:
            return not expected
        if isinstance(actual, (list, dict, str)):
            return bool(actual) == expected
        return bool(expected)

    @staticmethod
    def match(actual: Any, expected: Any) -> bool:
        """Regex match operator implementation."""
        if not isinstance(actual, str) or not isinstance(expected, str):
            return False
        try:
            pattern = re.compile(expected)
            return bool(pattern.match(actual))
        except re.error:
            return False

    @staticmethod
    def contains(actual: Any, expected: Any) -> bool:
        """Contains operator implementation."""
        if actual is None:
            return False
        if isinstance(actual, str):
            return expected in actual
        if isinstance(actual, (list, tuple)):
            return expected in actual
        return False

    @staticmethod
    def in_list(actual: Any, expected: list) -> bool:
        """In list operator implementation."""
        if not isinstance(expected, list):
            return False
        return actual in expected

    @staticmethod
    def role_device(actual: Any, expected: Any) -> bool:
        """check for role device match"""
        role = {
            'standalone': 0,
            'primary': 1,
            'secondary': 2,
        }
        try:
            if not isinstance(actual, str) or expected not in role:
                return False

            return str(role[expected]) == actual[-3][0]
        except (IndexError, TypeError):
            return False

    @staticmethod
    def max_length(actual: Any, expected: int) -> bool:
        """Check if the length of a value is less than or equal to the expected value."""
        if not isinstance(actual, (str, list, dict, tuple)):
            return False
        return len(actual) <= expected

    @staticmethod
    def exact_length(actual: Any, expected: int) -> bool:
        """Check if the length of a value is exactly equal to the expected value."""
        if not isinstance(actual, (str, list, dict, tuple)):
            return False
        return len(actual) == expected
