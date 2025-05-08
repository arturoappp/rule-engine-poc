import json
from typing import Any, Optional, Union
from app.api.models.rules import Rule, StoredRule
from rule_engine.core.evaluator import RuleEvaluator
from rule_engine.core.rule_result import RuleResult

from app.utilities.logging import logger


class RuleEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Initializing RuleEngine singleton instance")
        return cls._instance

    def __init__(self):
        self.rule_repository: dict[str, StoredRule] = {}
        logger.debug("RuleEngine repository initialized")

    def add_rules(self, rules: list[Rule]) -> None:
        logger.info(f"Adding {len(rules)} rules to engine")
        for rule in rules:
            self.add_rule(rule)
        logger.debug("Finished adding multiple rules")

    # list all rules
    @property
    def all_rules(self):
        rule_count = len(self.rule_repository)
        logger.debug(f"Getting all rules ({rule_count} total)")
        return self.rule_repository.values()

    def add_rule(self, rule: Rule, categories: Optional[set[str]] = None) -> None:
        if categories is None:
            categories = set()

        logger.params.set(
            entity_type=rule.entity_type,
            rule_name=rule.name,
            category=','.join(categories) if categories else None
        )

        logger.info(f"Adding rule with {len(categories)} categories")

        stored_rule_key = f"{rule.entity_type}|{rule.name}"

        if stored_rule_key in self.rule_repository:
            existing_rule = self.rule_repository[stored_rule_key]
            existing_categories = existing_rule.categories
            logger.info(f"Overwriting existing rule with previous categories: {existing_categories}")

        new_spike_stored_rule = StoredRule(
            rule_name=rule.name,
            entity_type=rule.entity_type,
            description=rule.description,
            categories=list(categories),
            rule=rule
        )
        # TODO: Should we require the user to pass an "overwrite" parameter to allow overwriting existing rules?
        # Would prevent accidental overwrites
        self.rule_repository[stored_rule_key] = new_spike_stored_rule
        logger.debug(f"Rule successfully added to repository with key: {stored_rule_key}")

    def get_stored_rules_by_names_and_entity_type(self, rule_names: list[str], entity_type: str) -> StoredRule:
        stored_rules = [self.get_stored_rule_by_name_and_entity_type(rule_name, entity_type) for rule_name in rule_names]
        return stored_rules

    def get_stored_rule_by_name_and_entity_type(self, rule_name: str, entity_type: str) -> StoredRule:
        logger.params.set(entity_type=entity_type, rule_name=rule_name)

        stored_rule_key = f"{entity_type}|{rule_name}"
        logger.debug(f"Looking up rule with key: {stored_rule_key}")

        if stored_rule_key in self.rule_repository:
            logger.debug(f"Rule found: {stored_rule_key}")
            return self.rule_repository[stored_rule_key]
        else:
            logger.warning(f"Rule not found: {stored_rule_key}")
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")

    # check if rule exists
    def rule_exists(self, rule_name: str, entity_type: str) -> bool:
        stored_rule_key = f"{entity_type}|{rule_name}"
        exists = stored_rule_key in self.rule_repository

        logger.debug(f"Checking if rule exists: {stored_rule_key}, result: {exists}")

        return exists

    # get all rules, but if entity type is not none, get only rules for entity_type, and if category is not none, get only rules for entity_type and category
    def get_stored_rules(self, entity_type: Optional[str] = None, categories: Optional[list[str]] = None) -> list[
            StoredRule]:
        # Set context for logging
        logger.params.set(
            entity_type=entity_type,
            category=','.join(categories) if categories else None
        )

        filter_desc = []
        if entity_type:
            filter_desc.append(f"entity_type='{entity_type}'")
        if categories:
            filter_desc.append(f"categories={categories}")

        filter_str = " and ".join(filter_desc) if filter_desc else "no filters"
        logger.info(f"Getting stored rules with {filter_str}")

        stored_rules = []
        if entity_type is None and categories is None:
            stored_rules = [stored_rule for stored_rule in self.rule_repository.values()]
        elif entity_type is not None and categories is None:
            stored_rules = [stored_rule for _, stored_rule in self.rule_repository.items() if
                            stored_rule.entity_type == entity_type]
        elif entity_type is None and categories is not None:
            stored_rules = [stored_rule for _, stored_rule in self.rule_repository.items() if
                            any(category in stored_rule.categories for category in categories)]
        elif entity_type is not None and categories is not None:
            stored_rules = [stored_rule for key, stored_rule in self.rule_repository.items() if
                            stored_rule.entity_type == entity_type and any(
                                category in stored_rule.categories for category in categories)]

        if stored_rules is None:
            logger.debug("No rules found, returning empty list")
            return []

        logger.info(f"Found {len(stored_rules)} rules matching criteria")
        return stored_rules

    def evaluate_data(self, data: Union[str, dict], entity_type: str,
                      categories: list[str] = None) -> list[RuleResult]:
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

        # # If there are no rules for this entity type, return an empty list
        # if entity_type not in self.rules_by_entity:
        #     logger.warning(f"No rules for entity type: {entity_type}")
        #     return []

        # Filter rules by category if specified
        rules_to_evaluate = []
        if categories:
            for category in categories:
                rules_to_evaluate.extend(self.get_stored_rules_to_evaluate(entity_type, category))
        else:
            rules_to_evaluate = self.get_stored_rules_to_evaluate(entity_type)

        if not rules_to_evaluate:
            logger.warning(f"No rules to evaluate for entity type: {entity_type}")
            return []

        # Evaluate the rules
        return RuleEvaluator.evaluate_data(data_dict, rules_to_evaluate, entity_type)

    def evaluate_data_with_criteria(self, data_dict: dict[str, Any], entity_type: str,
                                    categories: Optional[list[str]] = None,
                                    rule_names: Optional[list[str]] = None) -> list[RuleResult]:
        """
        Evaluate data against rules filtered by categories and/or rule names.

        Args:
            data_dict: Data to evaluate
            entity_type: Entity type
            categories: Optional list of categories to filter rules
            rule_names: Optional list of rule names to filter rules
        """

        stored_rules_to_evaluate = self.get_stored_rules_to_evaluate(entity_type, categories, rule_names)

        # If no rules to evaluate, return empty list
        if not stored_rules_to_evaluate:
            logger.warning("No rules found for the specified criteria")
            return []

        # Evaluate with the filtered rules
        return RuleEvaluator.evaluate_data(data_dict, stored_rules_to_evaluate, entity_type)

    def get_stored_rules_to_evaluate(self, entity_type: str, categories: Optional[list[str]] = None, rule_names: Optional[list[str]] = None) -> list[StoredRule]:
        """
        Retrieve rules to evaluate based on entity type, categories, and/or rule names.

        Args:
            entity_type: The entity type to filter rules.
            categories: Optional list of categories to filter rules.
            rule_names: Optional list of rule names to filter rules.

        Returns:
            A list of SpikeStoredRule objects to evaluate.
        """
        rules_to_evaluate = set()

        if rule_names:
            stored_rules = self.get_stored_rules_by_names_and_entity_type(rule_names, entity_type)
            rules_to_evaluate.update(stored_rules)

        elif categories:
            category_rules = self.get_stored_rules(entity_type, categories)
            rules_to_evaluate.update(category_rules)
        else:
            all_rules = self.get_stored_rules(entity_type)
            rules_to_evaluate.update(all_rules)

        return list(rules_to_evaluate)
