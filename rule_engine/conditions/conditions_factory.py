"""
Package for condition classes in the rule engine.
"""

from typing import Dict, Optional

from rule_engine.conditions.base import Condition, ValueCondition
from rule_engine.conditions.composite import All, Any, None_, Not
from rule_engine.conditions.operators import Operator
from rule_engine.utils.path_utils import PathUtils


class StandardValueCondition(ValueCondition):
    """
    Standard implementation of ValueCondition that uses the Operator class.
    """

    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if the condition is met, False otherwise
        """
        # Simplify the path
        simplified_path = PathUtils.simplify_path(self.path)

        # Get the current value
        actual_value = PathUtils.get_value_from_path(entity, simplified_path)

        # Get the operator function
        operator_func = Operator.get_operator_function(self.operator)

        # Apply the operator
        return operator_func(actual_value, self.expected_value)


class ConditionFactory:
    """
    Factory for creating condition instances from dictionary representations.
    """

    @staticmethod
    def create_condition(data: Dict) -> Optional[Condition]:
        """
        Create a condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition

        Returns:
            Condition instance, or None if the data is invalid
        """
        if not data or not isinstance(data, dict):
            return None

        # Check for composite conditions first
        if "all" in data:
            return All.from_dict(data, ConditionFactory)
        elif "any" in data:
            return Any.from_dict(data, ConditionFactory)
        elif "none" in data:
            return None_.from_dict(data, ConditionFactory)
        elif "not" in data:
            return Not.from_dict(data, ConditionFactory)

        # Then check for value conditions
        if "path" in data and "operator" in data:
            return StandardValueCondition.from_dict(data)

        return None