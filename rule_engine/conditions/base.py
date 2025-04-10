"""
Base classes for conditions in the rule engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Condition(ABC):
    """
    Abstract base class for all conditions.
    """

    @abstractmethod
    def evaluate(self, entity: Dict) -> bool:
        """
        Evaluate the condition against an entity.

        Args:
            entity: Entity dictionary to evaluate against

        Returns:
            True if the condition is met, False otherwise
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict) -> 'Condition':
        """
        Create a condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition

        Returns:
            Condition instance
        """
        pass


class ValueCondition(Condition):
    """
    Base class for conditions that compare a value from an entity against an expected value.
    """

    def __init__(self, path: str, operator: str, expected_value: Any):
        """
        Initialize a value condition.

        Args:
            path: Access path to the value in the entity
            operator: Operator to apply
            expected_value: Expected value to compare against
        """
        self.path = path
        self.operator = operator
        self.expected_value = expected_value

    def to_dict(self) -> Dict:
        """
        Convert the condition to a dictionary representation.

        Returns:
            Dictionary representation of the condition
        """
        return {
            "path": self.path,
            "operator": self.operator,
            "value": self.expected_value
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ValueCondition':
        """
        Create a value condition from a dictionary representation.

        Args:
            data: Dictionary representation of the condition

        Returns:
            ValueCondition instance
        """
        return cls(
            path=data.get("path", ""),
            operator=data.get("operator", ""),
            expected_value=data.get("value")
        )