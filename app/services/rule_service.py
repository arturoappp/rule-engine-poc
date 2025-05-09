"""
Service layer for rule engine operations.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from app.api.models.rules import APIRule, Rule
from app.services.rule_engine import RuleEngine
from app.utilities.rule_service_util import create_rules_dict
from rule_engine.core.failure_info import FailureInfo
from rule_engine.core.rule_result import RuleResult

# Set up logging
logger = logging.getLogger(__name__)


class RuleService:
    """Service for rule engine operations."""

    def __init__(self):
        """Initialize the rule service."""
        self.engine = RuleEngine.get_instance()

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
            # TODO: Find where this needs added for evaluate data, and if it needs an analagous method created
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

    def get_rule_history(self, limit: int = 10) -> List[Dict]:
        """
        Get information about available rules and their structure.

        # In a real implementation, this method could retrieve an evaluation history from a database.
        # For now, it provides useful information about available rules.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of rule information records
        """
        history = []
        entity_types = self.engine.get_entity_types()

        for entity_type in entity_types:
            categories = self.engine.get_categories(entity_type)

            for category in categories:
                rules = self.engine.get_rules_by_category(entity_type, category)

                for rule in rules:
                    rule_info = {
                        "id": f"{entity_type}-{category}-{rule.get('name', 'unknown')}",
                        "entity_type": entity_type,
                        "category": category,
                        "rule_name": rule.get("name", "Unnamed Rule"),
                        "description": rule.get("description", "No description provided"),
                        "complexity": self._calculate_rule_complexity(rule)
                    }

                    history.append(rule_info)

                    # Limit the number of records returned
                    if len(history) >= limit:
                        return history

        return history

    def _calculate_rule_complexity(self, rule: Dict) -> Dict:
        """
        Calculate the complexity of a rule based on its structure.

        Args:
            rule: Rule dictionary

        Returns:
            Dictionary with complexity metrics
        """
        if "conditions" not in rule:
            return {"level": "unknown", "conditions": 0, "depth": 0}

        # Count conditions and depth
        conditions_count = 0
        max_depth = 0

        def count_conditions(cond, depth=0):
            nonlocal conditions_count, max_depth

            if depth > max_depth:
                max_depth = depth

            # Count simple condition
            if "path" in cond and "operator" in cond:
                conditions_count += 1

            # Count composite conditions
            for op_type in ["all", "any", "none"]:
                if op_type in cond and isinstance(cond[op_type], list):
                    for subcond in cond[op_type]:
                        count_conditions(subcond, depth + 1)

            # Count "not" condition
            if "not" in cond and isinstance(cond["not"], dict):
                count_conditions(cond["not"], depth + 1)

        # Start counting with root conditions
        count_conditions(rule["conditions"])

        # Determine complexity level
        complexity_level = "simple"
        if conditions_count > 5 or max_depth > 2:
            complexity_level = "moderate"
        if conditions_count > 10 or max_depth > 4:
            complexity_level = "complex"

        return {
            "level": complexity_level,
            "conditions": conditions_count,
            "depth": max_depth
        }

    def export_rules_to_json(self, entity_type: str = None, category: str = None) -> Dict:
        """
        Export rules to a structured JSON format with additional metadata.

        Args:
            entity_type: Optional entity type to filter rules
            category: Optional category to filter rules

        Returns:
            Dictionary with exported rules and metadata
        """
        # Create an object to contain rules and metadata
        result = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_rules": 0,
                "entity_types": [],
                "categories": []
            },
            "rules": {}
        }

        # Get entity types to export
        entity_types = [entity_type] if entity_type else self.engine.get_entity_types()
        result["metadata"]["entity_types"] = entity_types

        all_categories = []
        total_rules = 0

        # Collect rules by entity type and category
        for ent_type in entity_types:
            # Get categories for this entity type
            if category:
                categories = [category] if category in self.engine.get_categories(ent_type) else []
            else:
                categories = self.engine.get_categories(ent_type)

            all_categories.extend(categories)

            # Initialize structure for this entity type
            result["rules"][ent_type] = {}

            # Get rules for each category
            for cat in categories:
                rules = self.engine.get_rules_by_category(ent_type, cat)

                if rules:
                    result["rules"][ent_type][cat] = rules
                    total_rules += len(rules)

        # Update metadata
        result["metadata"]["total_rules"] = total_rules
        result["metadata"]["categories"] = list(set(all_categories))

        return result

    def store_rules(self, entity_type: str, rules: List[APIRule]) -> Tuple[
            bool, str, int]:
        """
        Store rules in the engine, overwriting duplicates with same name across all categories.

        Args:
            entity_type: Entity type
            rules: List of rules to store
            default_category: Default category for rules without specified add_to_categories

        Returns:
            Tuple of (success, message, stored_rules_count)
        """
        try:
            new_rules = 0
            updated_rules = 0
            # Process all rules from request
            for rule in rules:
                existing_categories = []
                if self.engine.rule_exists(rule.name, entity_type):
                    existing_stored_rule = self.engine.get_stored_rule_by_name_and_entity_type(rule.name,
                                                                                               entity_type)
                    existing_categories = existing_stored_rule.categories
                    updated_rules += 1
                else:
                    new_rules += 1

                new_rule = Rule(
                    name=rule.name,
                    entity_type=rule.entity_type,
                    description=rule.description,
                    conditions=rule.conditions)

                all_categories_to_include = {}
                # append any existing categories to the rule.categories list
                if existing_categories:
                    all_categories_to_include = existing_categories.union(rule.add_to_categories)
                else:
                    all_categories_to_include = set(rule.add_to_categories)

                self.engine.add_rule(new_rule, all_categories_to_include)

            # Create success message
            message = f"Successfully stored rules: {new_rules} new, {updated_rules} updated"

            # Return the total number of unique rules stored
            return True, message, len(rules)

        except Exception as e:
            logger.error(f"Error storing rules: {e}")
            return False, f"Error storing rules: {str(e)}", 0

    def get_rules(self, entity_type: Optional[str] = None, provided_categories: Optional[list[str]] = None) -> \
            Dict[str, Dict[str, List[Dict]]]:
        """
        Get all rules from the engine.

        Returns:
            Dictionary of rules by entity type and category
        """
        stored_rules = self.engine.get_stored_rules(entity_type, provided_categories)

        if entity_type:
            entity_types_to_display = {entity_type}
        else:
            entity_types_to_display = {rule.entity_type for rule in stored_rules if rule.entity_type}

        categories_to_display = set()
        if provided_categories:
            categories_to_display = set(provided_categories)
        else:
            for rule in stored_rules:
                if rule.categories:
                    categories_to_display.update(rule.categories)

        rules_dict = create_rules_dict(stored_rules, categories_to_display, entity_types_to_display)

        return rules_dict

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

    def evaluate_data_with_criteria(self, data: Dict[str, Any], entity_type: str,
                                    categories: Optional[List[str]] = None,
                                    rule_names: Optional[List[str]] = None) -> List[RuleResult]:
        """
        Evaluate data against rules filtered by categories and/or rule names.

        Args:
            data: Data to evaluate
            entity_type: Entity type
            categories: Optional list of categories to filter rules
            rule_names: Optional list of rule names to filter rules

        Returns:
            List of evaluation results
        """
        try:
            # Convert the data to a dictionary if it's a string
            data_dict = json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON data: {e}")
            # TODO: Should a ValueError and message be included with the raise?
            raise

        if categories and rule_names:
            logger.error("Cannot filter by both categories and rule names at the same time. Please provide only one of them.")
            raise ValueError("Cannot filter by both categories and rule names at the same time. Please provide only one of them.")

        # Call the RuleEngine method that contains the filtering logic
        return self.engine.evaluate_data_with_criteria(
            data_dict=data_dict,
            entity_type=entity_type,
            categories=categories,
            rule_names=rule_names
        )

    def evaluate_with_rules(self, data: dict[str, Any], entity_type: str, api_rules: list[APIRule]) -> list[RuleResult]:
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
            temp_engine = RuleEngine()

            rules = [Rule(
                name=rule.name,
                entity_type=rule.entity_type,
                description=rule.description,
                conditions=rule.conditions
            ) for rule in api_rules]

            for rule in rules:
                temp_engine.add_rule(rule)

            rules_json = json.dumps([
                rule.model_dump(by_alias=True, exclude_none=True)
                for rule in rules
            ])

            # Debugging to see the JSON structure
            logger.debug(f"Rules JSON: {rules_json}")

            return temp_engine.evaluate_data(data, entity_type=entity_type)

        except Exception as e:
            logger.error(f"Error evaluating data with provided rules: {e}")
            error_result = RuleResult(
                rule_name=api_rules[0].name if api_rules else "Unknown Rule",
                success=False,
                message=f"Error evaluating rule: {str(e)}",
                input_data={"error": str(e)},
                failing_elements=[],
                failure_details=[
                    FailureInfo(
                        operator="unknown",
                        path="$.error",
                        expected_value="valid evaluation",
                        actual_value=str(e)
                    )
                ]
            )
            return [error_result]

    def get_evaluation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about rule evaluation capabilities.

        Returns:
            Statistics about current rule engine configuration
        """
        # Get statistics based on currently loaded rules
        entity_types = self.engine.get_entity_types()
        rule_stats = {}
        total_rules = 0

        for entity_type in entity_types:
            categories = self.engine.get_categories(entity_type)
            entity_rule_count = 0
            category_counts = {}

            for category in categories:
                rules = self.engine.get_rules_by_category(entity_type, category)
                category_rule_count = len(rules)
                category_counts[category] = category_rule_count
                entity_rule_count += category_rule_count

            rule_stats[entity_type] = {
                "total_rules": entity_rule_count,
                "categories": category_counts
            }
            total_rules += entity_rule_count

        # Information about supported operators
        supported_operators = [
            "equal", "not_equal", "greater_than", "less_than",
            "greater_than_equal", "less_than_equal", "exists",
            "not_empty", "match", "contains", "role_device"
        ]

        # Statistics about the rule engine
        engine_stats = {
            "total_rules": total_rules,
            "entity_types": len(entity_types),
            "supported_operators": supported_operators,
            "max_rules_per_request": 100,  # Example: configurable
            "rule_stats_by_entity": rule_stats
        }

        return engine_stats

    def get_rule_failure_details(self, rule_name: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get detailed information about a specific rule, including its structure and validation.

        Args:
            rule_name: Name of the rule to analyze
            entity_type: Optional entity type to filter rules

        Returns:
            Detailed information about the rule
        """
        # Find the specified rule in the engine
        rule_info = None
        rule_entity_type = None
        rule_category = None

        # Search all entity types if none is specified
        search_entity_types = [entity_type] if entity_type else self.engine.get_entity_types()

        for et in search_entity_types:
            categories = self.engine.get_categories(et)
            for category in categories:
                rules = self.engine.get_rules_by_category(et, category)
                for rule in rules:
                    if rule.get("name") == rule_name:
                        rule_info = rule
                        rule_entity_type = et
                        rule_category = category
                        break
                if rule_info:
                    break
            if rule_info:
                break

        if not rule_info:
            return {
                "rule_name": rule_name,
                "found": False,
                "message": f"Rule '{rule_name}' not found in the engine"
            }

        # Analyze the rule's condition structure
        def analyze_conditions(conditions, parent_path=""):
            if not conditions:
                return []

            structure = []

            if "path" in conditions and "operator" in conditions:
                # This is a simple condition
                op_info = {
                    "type": "simple",
                    "path": conditions.get("path"),
                    "operator": conditions.get("operator"),
                    "expected_value": conditions.get("value"),
                    "parent_path": parent_path
                }
                structure.append(op_info)

            # Analyze composite conditions
            for op_type in ["all", "any", "none"]:
                if op_type in conditions:
                    for i, subcond in enumerate(conditions[op_type]):
                        new_parent = f"{parent_path}.{op_type}[{i}]" if parent_path else f"{op_type}[{i}]"
                        structure.extend(analyze_conditions(subcond, new_parent))

            if "not" in conditions:
                new_parent = f"{parent_path}.not" if parent_path else "not"
                structure.extend(analyze_conditions(conditions["not"], new_parent))

            return structure

        # Analyze the rule structure
        conditions_structure = analyze_conditions(rule_info.get("conditions", {}))

        # Build the response
        rule_analysis = {
            "rule_name": rule_name,
            "found": True,
            "entity_type": rule_entity_type,
            "category": rule_category,
            "description": rule_info.get("description"),
            "conditions_count": len(conditions_structure),
            "operators_used": list(set(c["operator"] for c in conditions_structure if "operator" in c)),
            "paths_used": list(set(c["path"] for c in conditions_structure if "path" in c)),
            "structure": conditions_structure,
            "rule_definition": rule_info
        }

        return rule_analysis

    def update_rule_categories(self, rule_name: str, entity_type: str, categories: List[str], category_action: str) -> \
            Tuple[bool, str]:
        """This method allows adding or removing categories associated with a rule
        for a given entity type. The action to perform is determined by the
        `category_action` parameter.
        Args:
            rule_name (str): The name of the rule to update.
            entity_type (str): The type of entity associated with the rule.
            categories (List[str]): A list of category names to add or remove.
            category_action (str): The action to perform, either "add" or "remove".
        Returns:
            Tuple[bool, str]: A tuple containing a boolean indicating success or failure,
            and a message providing additional context about the operation.
        Raises:
            Exception: If an unexpected error occurs during the update process.
        Notes:
            - If `category_action` is not "add" or "remove", the method will return
              a failure message without performing any updates.
        """
        try:
            if category_action == "add":
                self._add_categories(entity_type, rule_name, categories)
            elif category_action == "remove":
                self._remove_categories(rule_name, entity_type, categories)
            else:
                return False, f"Invalid category action: {category_action}. Must be either 'add' or 'remove'"

            return True, f"Successfully updated categories {categories}, for {entity_type} rule {rule_name}"
        except Exception as e:
            logger.error("Error updating rule categories: %s", e)
            return False, f"Error updating rule categories: {str(e)}"

    def _add_categories(self, entity_type: str, rule_name: str, categories: list[str]) -> None:
        rule_to_add_categories_to = self.engine.get_stored_rule_by_name_and_entity_type(rule_name,
                                                                                        entity_type)
        categories_set = set(categories)
        rule_to_add_categories_to.categories = set(rule_to_add_categories_to.categories).union(categories_set)

    def _remove_categories(self, rule_name, entity_type, categories: list[str]) -> None:
        rule_to_remove_categories_from = self.engine.get_stored_rule_by_name_and_entity_type(rule_name,
                                                                                             entity_type)
        rule_to_remove_categories_from.categories = {category for category in rule_to_remove_categories_from.categories
                                                     if category not in categories}
