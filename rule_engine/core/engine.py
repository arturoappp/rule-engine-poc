"""
Module containing the main RuleEngine class.
"""

import json
import logging
from typing import Dict, List, Union

from rule_engine.core.evaluator import RuleEvaluator
from rule_engine.core.rule_result import RuleResult
from rule_engine.utils.json_loader import JsonLoader

# Logging configuration
logger = logging.getLogger(__name__)

OVERWRITE_DUPLICATE_RULES: bool = True


class RuleEngine:
    """
    Main rule engine class that manages rules and performs evaluations.
    """

    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        """Initialize an empty rule engine."""
        self.rules_by_entity = {}  # Dictionary of rules by entity type

    def load_rules_from_file(self, file_path: str, entity_type: str, category: str = None) -> None:
        """
        Load rules from a JSON file for a specific entity type.

        Args:
            file_path: Path to the JSON file containing the rules
            entity_type: Type of entity (device, task, etc.)
            category: Optional category to assign to the loaded rules
        """
        try:
            # Load the rules data from file
            rules_data = JsonLoader.load_from_file(file_path)

            # If no category is specified, use the filename as category
            if category is None:
                category = JsonLoader.get_file_category(file_path)

            # Initialize the structure for the entity type if it doesn't exist
            self._ensure_entity_structure(entity_type)

            # Process and add the rules
            self._add_rules(rules_data, entity_type, category)

            logger.info(f"Rules successfully loaded from {file_path} for entity '{entity_type}', category '{category}'")

        except Exception as e:
            logger.error(f"Error loading rules from {file_path}: {e}")
            raise

    def load_rules_from_json(self, json_str: str, entity_type: str, category: str = "default") -> None:
        """
        Load rules from a JSON string for a specific entity type.

        Args:
            json_str: JSON string containing the rules
            entity_type: Type of entity (device, task, etc.)
            category: Optional category to assign to the loaded rules
        """
        try:
            # Load the rules data from string
            rules_data = JsonLoader.load_from_string(json_str)

            # Initialize the structure for the entity type if it doesn't exist
            self._ensure_entity_structure(entity_type)

            # Process and add the rules
            normalized_rules = JsonLoader.normalize_rules_data(rules_data, category)

            for rule in normalized_rules:
                self._add_rule(rule, entity_type, category)

            logger.info(f"Rules successfully loaded from JSON string for entity '{entity_type}', category '{category}'")

        except Exception as e:
            logger.error(f"Error loading rules from JSON string: {e}")
            raise

    def _ensure_entity_structure(self, entity_type: str) -> None:
        """
        Ensure that the structure for an entity type exists.

        Args:
            entity_type: Entity type
        """
        if entity_type not in self.rules_by_entity:
            self.rules_by_entity[entity_type] = {"rules": [], "categories": {}}

    def _add_rules(self, rules_data: Union[Dict, List], entity_type: str, category: str) -> None:
        """
        Process and add rules to the engine.

        Args:
            rules_data: Rules data loaded from a JSON source
            entity_type: Entity type for which the rules are loaded
            category: Category to assign to the loaded rules
        """
        # Normalize the rules data into a list of rules with categories
        normalized_rules = JsonLoader.normalize_rules_data(rules_data, category)

        # Add each rule to the engine
        for rule in normalized_rules:
            self._add_rule(rule, entity_type, rule.get("category", category))

    def _add_rule(self, rule: Dict, entity_type: str, category: str = "default") -> None:
        """
        Add a rule to the engine.

        Args:
            rule: Rule dictionary
            entity_type: Entity type for which the rule is added
            category: Category to organize the rule
        """
        entity_rules = self.rules_by_entity[entity_type]
        rule_name = rule.get("name", "")

        # Check if overwrite is enabled in config
        if OVERWRITE_DUPLICATE_RULES:
            # Remove any existing rule with the same name from the general list
            entity_rules["rules"] = [r for r in entity_rules["rules"] if r.get("name", "") != rule_name]

            # Remove any existing rule with the same name from the category
            if category in entity_rules["categories"]:
                entity_rules["categories"][category] = [r for r in entity_rules["categories"][category] if r.get("name", "") != rule_name]

        # Make a copy of the rule to avoid modifying the original
        rule_copy = rule.copy()

        # Add the rule to the general list
        entity_rules["rules"].append(rule_copy)

        # Add the rule to the category
        if category not in entity_rules["categories"]:
            entity_rules["categories"][category] = []
        entity_rules["categories"][category].append(rule_copy)

    def get_rules_by_category(self, entity_type: str, category: str = None) -> List[Dict]:
        """
        Get rules by category.

        Args:
            entity_type: Entity type to filter rules
            category: Category to filter rules. If None, returns all rules.

        Returns:
            List of rules in the specified category
        """

        if entity_type not in self.rules_by_entity:
            return []

        entity_rules = self.rules_by_entity[entity_type]

        if category is None:
            return entity_rules["rules"]
        return entity_rules["categories"].get(category, [])

    def get_entity_types(self) -> List[str]:
        """
        Get the list of entity types for which rules are loaded.

        Returns:
            List of entity types
        """
        return list(self.rules_by_entity.keys())

    def get_categories(self, entity_type: str) -> List[str]:
        """
        Get the list of categories for an entity type.

        Args:
            entity_type: Entity type

        Returns:
            List of categories
        """
        if entity_type not in self.rules_by_entity:
            return []

        return list(self.rules_by_entity[entity_type]["categories"].keys())

    def evaluate_data(self, data: Union[str, Dict], entity_type: str, categories: List[str] = None) -> List[RuleResult]:
        """
        Evaluate rules against the provided data.

        Args:
            data: JSON string or dictionary with data to evaluate
            entity_type: Entity type to filter rules
            categories: Optional list of categories to evaluate. If None, evaluates all rules.

        Returns:
            List of RuleResult objects
        """
        try:
            # Convert the data to a dictionary if it's a string
            data_dict = json.loads(data) if isinstance(data, str) else data
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON data: {e}")
            raise

        # If there are no rules for this entity type, return an empty list
        if entity_type not in self.rules_by_entity:
            logger.warning(f"No rules for entity type: {entity_type}")
            return []

        # Filter rules by category if specified
        rules_to_evaluate = []
        if categories:
            for category in categories:
                rules_to_evaluate.extend(self.get_rules_by_category(entity_type, category))
        else:
            rules_to_evaluate = self.rules_by_entity[entity_type]["rules"]

        if not rules_to_evaluate:
            logger.warning(f"No rules to evaluate for entity type: {entity_type}")
            return []

        # Evaluate the rules
        return RuleEvaluator.evaluate_data(data_dict, rules_to_evaluate, entity_type)
