"""
Service layer for rule engine operations.
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

from app.api.models.rules import Rule as APIRule
from app.api.models.rules import RuleCondition as APIRuleCondition
from rule_engine.core.engine import RuleEngine
from rule_engine.core.rule_result import RuleResult

# Set up logging
logger = logging.getLogger(__name__)


class RuleService:
    """Service for rule engine operations."""

    def __init__(self):
        """Initialize the rule service."""
        self.engine = RuleEngine()

    def validate_rule(self, rule: APIRule) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a rule.

        Args:
            rule: Rule to validate

        Returns:
            Tuple of (valid, errors)
        """
        errors = []

        # Check if conditions are valid
        try:
            # Convert to dictionary and validate - use model_dump() for Pydantic v2
            rule_dict = rule.model_dump(by_alias=True)

            # Check for required fields
            if "name" not in rule_dict or not rule_dict["name"]:
                errors.append("Rule must have a name")

            if "conditions" not in rule_dict or not rule_dict["conditions"]:
                errors.append("Rule must have conditions")
            else:
                # Validate conditions recursively
                condition_errors = self._validate_condition(rule_dict["conditions"])
                errors.extend(condition_errors)

            return len(errors) == 0, errors if errors else None

        except Exception as e:
            logger.error(f"Error validating rule: {e}")
            errors.append(f"Invalid rule format: {str(e)}")
            return False, errors

    def _validate_condition(self, condition: Dict) -> List[str]:
        """
        Validate a condition recursively.

        Args:
            condition: Condition to validate

        Returns:
            List of validation errors
        """
        errors = []

        # If condition is None or not a dict, it's invalid
        if condition is None or not isinstance(condition, dict):
            errors.append("Condition must be a valid object")
            return errors

        # Identify what type of condition we have
        composite_operators = ["all", "any", "none", "not"]
        simple_condition = "path" in condition and condition["path"] is not None
        composite_condition = any(op in condition and condition[op] is not None for op in composite_operators)

        # If neither simple nor composite, it's invalid
        if not simple_condition and not composite_condition:
            errors.append("Condition must be either a simple condition with 'path' or a composite condition")
            return errors

        # Validate composite condition
        if "all" in condition and condition["all"] is not None:
            if not isinstance(condition["all"], list):
                errors.append("'all' must be a list of conditions")
            elif len(condition["all"]) == 0:
                errors.append("'all' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["all"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "any" in condition and condition["any"] is not None:
            if not isinstance(condition["any"], list):
                errors.append("'any' must be a list of conditions")
            elif len(condition["any"]) == 0:
                errors.append("'any' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["any"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "none" in condition and condition["none"] is not None:
            if not isinstance(condition["none"], list):
                errors.append("'none' must be a list of conditions")
            elif len(condition["none"]) == 0:
                errors.append("'none' must be a non-empty list of conditions")
            else:
                for sub_condition in condition["none"]:
                    errors.extend(self._validate_condition(sub_condition))

        if "not" in condition and condition["not"] is not None:
            if not isinstance(condition["not"], dict):
                errors.append("'not' must contain a valid condition object")
            else:
                errors.extend(self._validate_condition(condition["not"]))

        # Validate simple condition
        if simple_condition:
            if "operator" not in condition or not condition["operator"]:
                errors.append("Simple condition must have an 'operator'")
            elif condition["operator"] != "exists" and "value" not in condition:
                errors.append("Simple condition must have a 'value' unless operator is 'exists'")

        return errors

    def store_rules(self, entity_type: str, rules: List[APIRule], category: str = "default") -> Tuple[bool, str, int]:
        """
        Store rules in the engine.

        Args:
            entity_type: Entity type
            rules: List of rules to store
            category: Optional category

        Returns:
            Tuple of (success, message, stored_rules_count)
        """
        try:
            # Convert rules to JSON - use model_dump() for Pydantic v2
            rules_json = json.dumps([
                rule.model_dump(by_alias=True, exclude_none=True)
                for rule in rules
            ])

            # Debugging output
            logger.debug(f"Converting rules to JSON: {rules_json}")

            # Load rules into engine
            self.engine.load_rules_from_json(rules_json, entity_type=entity_type, category=category)

            return True, f"Successfully stored {len(rules)} rules", len(rules)

        except Exception as e:
            logger.error(f"Error storing rules: {e}")
            return False, f"Error storing rules: {str(e)}", 0

    def get_rules(self, entity_type = None, provided_category = None) -> Dict[str, Dict[str, List[Dict]]]:
        """
        Get all rules from the engine.

        Returns:
            Dictionary of rules by entity type and category
        """
        # TEMP for testing list_rules
          # Complex rule with nested conditions
        
        equal_rule = """
        [
            {
                "name": "Equal Rule",
                "description": "Tests the 'equal' operator",
                "conditions": {
                    "all": [
                        {
                            "path": "$.items[*].value",
                            "operator": "equal",
                            "value": 10
                        }
                    ]
                }
            }
        ]
        """

        complex_rule = """
        [
            {
                "name": "Complex Device Rule",
                "description": "Vendor must be Cisco with version 17.x, or non-Cisco with any version above 10.0",
                "conditions": {
                    "any": [
                        {
                            "all": [
                                {
                                    "path": "$.devices[*].vendor",
                                    "operator": "equal",
                                    "value": "Cisco Systems"
                                },
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^17\\\\."
                                }
                            ]
                        },
                        {
                            "all": [
                                {
                                    "path": "$.devices[*].vendor",
                                    "operator": "not_equal",
                                    "value": "Cisco Systems"
                                },
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^[1-9][0-9]\\\\."
                                }
                            ]
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(complex_rule, entity_type="commission", category="should")
        self.engine.load_rules_from_json(equal_rule, entity_type="decommission", category="could")

        result = {}

        if entity_type == None:
            # Get all entity types
            entity_types = self.engine.get_entity_types()
        else:
            entity_types = [entity_type]

        for entity_type in entity_types:
            result[entity_type] = {}

            if provided_category == None:
                # Get all categories for this entity type
                categories = self.engine.get_categories(entity_type)
            else:
                categories = [provided_category]

            for category in categories:
                # Get rules for this category
                rules = self.engine.get_rules_by_category(entity_type, category)
                result[entity_type][category] = rules

        return result

    def evaluate_data(self, data: Dict[str, Any], entity_type: str, categories: Optional[List[str]] = None) -> List[
        RuleResult]:
        """
        Evaluate data against rules.

        Args:
            data: Data to evaluate
            entity_type: Entity type
            categories: Optional list of categories to filter rules

        Returns:
            List of evaluation results
        """
        try:
            return self.engine.evaluate_data(data, entity_type=entity_type, categories=categories)
        except Exception as e:
            logger.error(f"Error evaluating data: {e}")
            raise

    def evaluate_with_rules(self, data: Dict[str, Any], entity_type: str, rules: List[APIRule]) -> List[RuleResult]:
        """
        Evaluate data against provided rules.

        Args:
            data: Data to evaluate
            entity_type: Entity type
            rules: Rules to evaluate against

        Returns:
            List of evaluation results
        """
        try:
            # Create a temporary rule engine
            temp_engine = RuleEngine()

            # Convert rules to JSON
            rules_json = json.dumps([rule.dict(by_alias=True) for rule in rules])

            # Load rules into engine
            temp_engine.load_rules_from_json(rules_json, entity_type=entity_type)

            # Evaluate data
            return temp_engine.evaluate_data(data, entity_type=entity_type)
        except Exception as e:
            logger.error(f"Error evaluating data with provided rules: {e}")
            raise