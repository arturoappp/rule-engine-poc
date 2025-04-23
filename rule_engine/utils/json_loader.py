"""
Utilities for loading rules from JSON sources.
"""

import json
import os
import logging
from typing import Dict, List, Union, Any, Optional

# Logging configuration
logger = logging.getLogger(__name__)


class JsonLoader:
    """Utility class for loading rules from JSON sources."""

    @staticmethod
    def load_from_file(file_path: str) -> Any:
        """
        Load JSON data from a file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Loaded JSON data

        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file contains invalid JSON
        """
        if not os.path.exists(file_path):
            logger.error(f"Rule file not found: {file_path}")
            raise FileNotFoundError(f"Rule file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {file_path}: {e}")
                raise

    @staticmethod
    def load_from_string(json_str: str) -> Any:
        """
        Load JSON data from a string.

        Args:
            json_str: JSON string

        Returns:
            Loaded JSON data

        Raises:
            json.JSONDecodeError: If the string contains invalid JSON
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON string: {e}")
            raise

    @staticmethod
    def get_file_category(file_path: str) -> str:
        """
        Get a category name from a file path.

        Args:
            file_path: Path to the file

        Returns:
            Category name (basename without extension)
        """
        return os.path.splitext(os.path.basename(file_path))[0]

    @staticmethod
    def normalize_rules_data(rules_data: Union[Dict, List], category: str = "default") -> List[Dict]:
        """
        Normalize rules data into a list of rule dictionaries with categories.

        Args:
            rules_data: Rules data loaded from a JSON source
            category: Base category to assign to the rules

        Returns:
            List of rule dictionaries with categories

        Raises:
            ValueError: If the rules data is invalid
        """
        result = []

        if isinstance(rules_data, list):
            # It's a list of rules
            for rule in rules_data:
                if not isinstance(rule, dict):
                    continue

                # Add category to the rule if it doesn't have one
                rule_copy = rule.copy()
                if "category" not in rule_copy:
                    rule_copy["category"] = category

                result.append(rule_copy)

        elif isinstance(rules_data, dict):
            # Check if it's a single rule
            if "name" in rules_data and "conditions" in rules_data:
                rule_copy = rules_data.copy()
                if "category" not in rule_copy:
                    rule_copy["category"] = category

                result.append(rule_copy)

            # It's a dictionary of categories with rules
            else:
                for cat, rules in rules_data.items():
                    cat_name = f"{category}.{cat}" if category != "default" else cat

                    if isinstance(rules, list):
                        for rule in rules:
                            if not isinstance(rule, dict):
                                continue

                            rule_copy = rule.copy()
                            if "category" not in rule_copy:
                                rule_copy["category"] = cat_name

                            result.append(rule_copy)

                    elif isinstance(rules, dict) and "name" in rules and "conditions" in rules:
                        rule_copy = rules.copy()
                        if "category" not in rule_copy:
                            rule_copy["category"] = cat_name

                        result.append(rule_copy)

        else:
            raise ValueError("Rules must be an object or a list of objects")

        return result
