"""
Composite conditions for building complex logical expressions.
"""

from typing import Dict, List, Any, Union, Type

from conditions.base import Condition


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

    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if all sub-conditions are met, False otherwise
        """
        return all(condition.evaluate(entity) for condition in self.conditions)

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

    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if any sub-condition is met, False otherwise
        """
        return any(condition.evaluate(entity) for condition in self.conditions)

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

    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if none of the sub-conditions are met, False otherwise
        """
        return not any(condition.evaluate(entity) for condition in self.conditions)

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

    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if the sub-condition is not met, False otherwise
        """
        return not self.condition.evaluate(entity)

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