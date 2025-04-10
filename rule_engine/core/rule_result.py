"""
Module containing the RuleResult class for storing rule evaluation results.
"""

from typing import Dict, List, Any, Optional

from rule_engine.core.failure_info import FailureInfo


class RuleResult:
    """Class to store the result of a rule evaluation"""

    def __init__(self, rule_name: str, success: bool, message: str, input_data: Any = None,
                 failing_elements: List[Dict] = None, failure_details: List[FailureInfo] = None):
        """
        Initialize a rule result

        Args:
            rule_name: Name of the rule
            success: Whether the rule passed or failed
            message: Message describing the result
            input_data: Optional data related to the result
            failing_elements: List of elements that failed the rule
            failure_details: List of FailureInfo objects describing the failures
        """
        self.rule_name = rule_name
        self.success = success
        self.message = message
        self.input_data = input_data
        self.failing_elements = failing_elements or []
        self.failure_details = failure_details or []

    def __str__(self) -> str:
        """String representation of the result"""
        status = "PASSED" if self.success else "FAILED"
        base_str = f"Rule '{self.rule_name}': {status} - {self.message}"

        if not self.success:
            if self.failing_elements:
                base_str += f" ({len(self.failing_elements)} elements failed)"

            if self.failure_details:
                base_str += "\nFailure details:"
                for i, detail in enumerate(self.failure_details):
                    base_str += f"\n  {i + 1}. {str(detail)}"

        return base_str

    def to_dict(self) -> Dict:
        """Convert the result to a dictionary for JSON serialization"""
        return {
            "rule_name": self.rule_name,
            "success": self.success,
            "message": self.message,
            "input_data": self.input_data,
            "failing_elements": self.failing_elements,
            "failure_details": [detail.to_dict() for detail in self.failure_details]
        }