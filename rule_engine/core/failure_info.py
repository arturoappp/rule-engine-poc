"""
Module containing the FailureInfo class for tracking condition failures.
"""

from typing import Dict, Optional, Any


class FailureInfo:
    """Class to store information about a failed condition evaluation."""

    def __init__(self, operator: Optional[str] = None, path: Optional[str] = None,
                 expected_value: Any = None, actual_value: Any = None):
        """
        Initialize failure information.

        Args:
            operator: Name of the operator that failed
            path: Path in the data where the failure occurred
            expected_value: The value that was expected by the rule
            actual_value: The actual value found in the data
        """
        self.operator = operator
        self.path = path
        self.expected_value = expected_value
        self.actual_value = actual_value

    def __str__(self) -> str:
        """String representation of failure information."""
        result = ""
        if self.operator and self.path:
            result = f"Failed at: '{self.path}' with operator '{self.operator}'"

            # Add value information if available
            if self.expected_value is not None or self.actual_value is not None:
                result += " ("
                if self.expected_value is not None:
                    result += f"expected: {self.expected_value}"
                if self.expected_value is not None and self.actual_value is not None:
                    result += ", "
                if self.actual_value is not None:
                    result += f"actual: {self.actual_value}"
                result += ")"

            return result
        return "Unknown failure"

    def to_dict(self) -> Dict:
        """Convert the failure info to a dictionary."""
        return {
            "operator": self.operator,
            "path": self.path,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value
        }