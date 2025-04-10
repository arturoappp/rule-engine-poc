"""
Composite conditions for building complex logical expressions.
"""

from typing import Dict, List, Any, Tuple, Optional

from rule_engine.conditions.base import Condition
from rule_engine.core.failure_info import FailureInfo


class All(Condition):
    """
    A composite condition that is met if all its sub-conditions are met (logical AND).
    """

    def __init__(self, conditions: List[Condition]):
        """
        Initialize an All condition.

        Args:
            conditions: List of sub-conditions
        """
        self.conditions = conditions

    def evaluate_with_details(self, entity: Dict) -> Tuple[bool, Optional[List[FailureInfo]]]:
        """
        Evaluate the condition against an entity and provide details about failures.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            Tuple of (success, failure_info):
            - success: True if all sub-conditions are met, False otherwise
            - failure_info: List of FailureInfo objects describing the failures, or None if successful
        """
        all_failures = []

        for condition in self.conditions:
            success, failures = condition.evaluate_with_details(entity)
            if not success and failures:
                all_failures.extend(failures)

        if all_failures:
            return False, all_failures

        return True, None

    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        return {
            "all": [condition.to_dict() for condition in self.conditions]
        }

    @classmethod
    def from_dict(cls, data: Dict, condition_factory: 'ConditionFactory') -> 'All':
        """
        Create an All condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition
            condition_factory: Factory for creating sub-conditions

        Returns:
            All condition instance
        """
        conditions = [condition_factory.create_condition(cond) for cond in data.get("all", [])]
        return cls(conditions)


class Any(Condition):
    """
    A composite condition that is met if any of its sub-conditions are met (logical OR).
    """

    def __init__(self, conditions: List[Condition]):
        """
        Initialize an Any condition.

        Args:
            conditions: List of sub-conditions
        """
        self.conditions = conditions

    def evaluate_with_details(self, entity: Dict) -> Tuple[bool, Optional[List[FailureInfo]]]:
        """
        Evaluate the condition against an entity and provide details about failures.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            Tuple of (success, failure_info):
            - success: True if any sub-condition is met, False otherwise
            - failure_info: List of FailureInfo objects describing the failures, or None if successful
        """
        all_failures = []

        for condition in self.conditions:
            success, failures = condition.evaluate_with_details(entity)
            if success:
                return True, None
            if failures:
                all_failures.extend(failures)

        return False, all_failures

    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        return {
            "any": [condition.to_dict() for condition in self.conditions]
        }

    @classmethod
    def from_dict(cls, data: Dict, condition_factory: 'ConditionFactory') -> 'Any':
        """
        Create an Any condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition
            condition_factory: Factory for creating sub-conditions

        Returns:
            Any condition instance
        """
        conditions = [condition_factory.create_condition(cond) for cond in data.get("any", [])]
        return cls(conditions)


class None_(Condition):
    """
    A composite condition that is met if none of its sub-conditions are met (logical NOR).
    """

    def __init__(self, conditions: List[Condition]):
        """
        Initialize a None condition.

        Args:
            conditions: List of sub-conditions
        """
        self.conditions = conditions

    def evaluate_with_details(self, entity: Dict) -> Tuple[bool, Optional[List[FailureInfo]]]:
        """
        Evaluate the condition against an entity and provide details about failures.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            Tuple of (success, failure_info):
            - success: True if none of the sub-conditions are met, False otherwise
            - failure_info: List of FailureInfo objects describing the failures, or None if successful
        """
        for condition in self.conditions:
            success, _ = condition.evaluate_with_details(entity)
            if success:
                # If any condition is met, this None_ condition fails
                return False, [FailureInfo(operator="none", path="composite")]

        return True, None

    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        return {
            "none": [condition.to_dict() for condition in self.conditions]
        }

    @classmethod
    def from_dict(cls, data: Dict, condition_factory: 'ConditionFactory') -> 'None_':
        """
        Create a None condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition
            condition_factory: Factory for creating sub-conditions

        Returns:
            None condition instance
        """
        conditions = [condition_factory.create_condition(cond) for cond in data.get("none", [])]
        return cls(conditions)


class Not(Condition):
    """
    A composite condition that is met if its sub-condition is not met (logical NOT).
    """

    def __init__(self, condition: Condition):
        """
        Initialize a Not condition.

        Args:
            condition: Sub-condition to negate
        """
        self.condition = condition

    def evaluate_with_details(self, entity: Dict) -> Tuple[bool, Optional[List[FailureInfo]]]:
        """
        Evaluate the condition against an entity and provide details about failures.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            Tuple of (success, failure_info):
            - success: True if the sub-condition is not met, False otherwise
            - failure_info: List of FailureInfo objects describing the failures, or None if successful
        """
        success, _ = self.condition.evaluate_with_details(entity)

        if not success:
            return True, None

        return False, [FailureInfo(operator="not", path="composite")]

    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        return {
            "not": self.condition.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict, condition_factory: 'ConditionFactory') -> 'Not':
        """
        Create a Not condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition
            condition_factory: Factory for creating sub-conditions

        Returns:
            Not condition instance
        """
        condition = condition_factory.create_condition(data.get("not", {}))
        return cls(condition)