"""
Package for condition classes in the rule engine.
"""

from typing import Dict, Optional, Tuple, List

from rule_engine.conditions.base import Condition, ValueCondition
from rule_engine.conditions.composite import All, Any, None_, Not
from rule_engine.conditions.operators import Operator
from rule_engine.core.failure_info import FailureInfo
from rule_engine.utils.path_utils import PathUtils


class StandardValueCondition(ValueCondition):
    """
    Standard implementation of ValueCondition that uses the Operator class.
    """

    def evaluate_with_details(self, entity: Dict) -> Tuple[bool, Optional[List[FailureInfo]]]:
        """
        Evaluate the condition against an entity and provide details about failures.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            Tuple of (success, failure_info):
            - success: True if the condition is met, False otherwise
            - failure_info: List of FailureInfo objects describing the failures, or None if successful
        """
        # Simplify the path
        simplified_path = PathUtils.simplify_path(self.path)

        # Get the current value
        actual_value = PathUtils.get_value_from_path(entity, simplified_path)

        # Get the operator function
        operator_func = Operator.get_operator_function(self.operator)

        # Apply the operator
        success = operator_func(actual_value, self.expected_value)

        if success:
            return True, None

        # If failed, return failure details with the actual and expected values
        return False, [FailureInfo(
            operator=self.operator,
            path=self.path,
            expected_value=self.expected_value,
            actual_value=actual_value
        )]


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
