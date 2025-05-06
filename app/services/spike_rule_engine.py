from typing import Any, Optional
from app.api.models.rules import SpikeRule, SpikeStoredRule
from rule_engine.core.evaluator import RuleEvaluator
from rule_engine.core.rule_result import RuleResult
import logging

# Logging configuration
logger = logging.getLogger(__name__)


class SpikeRuleEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.spike_rule_repository: dict[str, SpikeStoredRule] = {}

    def add_rules(self, rules: list[SpikeRule]) -> None:
        for rule in rules:
            self.add_rule(rule)

    # update add_rule to allow adding optional list of categories

    # list all rules
    @property
    def all_rules(self):
        return self.spike_rule_repository.values()

    def add_rule(self, rule: SpikeRule, categories: Optional[set[str]] = None) -> None:
        if categories is None:
            categories = set()
        print(rule)
        stored_rule_key = f"{rule.entity_type}|{rule.name}"

        new_spike_stored_rule = SpikeStoredRule(
            rule_name=rule.name,
            entity_type=rule.entity_type,
            description=rule.description,
            categories=list(categories),
            rule=rule
        )
        # TODO: Should we require the user to pass an "overwrite" parameter to allow overwriting existing rules?
        # Would prevent accidental overwrites
        self.spike_rule_repository[stored_rule_key] = new_spike_stored_rule

    def get_spike_stored_rule_by_name_and_entity_type(self, rule_name: str, entity_type: str) -> SpikeStoredRule:
        stored_rule_key = f"{entity_type}|{rule_name}"
        if stored_rule_key in self.spike_rule_repository:
            return self.spike_rule_repository[stored_rule_key]
        else:
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")

    # check if rule exists
    def rule_exists(self, rule_name: str, entity_type: str) -> bool:
        stored_rule_key = f"{entity_type}|{rule_name}"
        return stored_rule_key in self.spike_rule_repository

    # get all rules, but if entity type is not none, get only rules for entity_type, and if category is not none, get only rules for entity_type and category
    def get_spike_stored_rules(self, entity_type: Optional[str] = None, categories: Optional[list[str]] = None) -> list[SpikeStoredRule]:
        stored_rules = []
        if entity_type is None and categories is None:
            stored_rules = [stored_rule for stored_rule in self.spike_rule_repository.values()]
        elif entity_type is not None and categories is None:
            stored_rules = [stored_rule for _, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type]
        elif entity_type is None and categories is not None:
            stored_rules = [stored_rule for _, stored_rule in self.spike_rule_repository.items() if any(category in stored_rule.categories for category in categories)]
        elif entity_type is not None and categories is not None:
            stored_rules = [stored_rule for key, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type and any(category in stored_rule.categories for category in categories)]
        if stored_rules is None:
            return []
        return stored_rules

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

        if not self.rule_exists(entity_type):
            logger.warning(f"No rules for entity type: {entity_type}")
            return []

        # Rules to evaluate
        rules_to_evaluate = {}

        # If we have rule names, search for them in the specified entity type
        if rule_names:
            for rule_name in rule_names:
                try:
                    rule = self.get_spike_stored_rule_by_name_and_entity_type(rule_name, entity_type)
                    rules_to_evaluate.update(rule)
                except ValueError as e:
                    logger.warning(f"Rule not found: {e}")

        # If categories is not None, get all rules for the entity type and filter by categories
        if categories is not None:
            for category in categories:
                category_rules = self.get_spike_stored_rules(entity_type, [category])
                for rule in category_rules:
                    if rule.rule_name in rule_names:
                        rules_to_evaluate.update(rule)

        # If we have rule names, search for them in all categories

        # if rule_names:
        #     all_categories = self.get_categories(entity_type)
        #     for category in all_categories:
        #         category_rules = self.get_rules_by_category(entity_type, category)
        #         for rule in category_rules:
        #             if rule.get("name") in rule_names and rule not in rules_to_evaluate:
        #                 rules_to_evaluate.append(rule)

        # If we have categories, add all rules from those categories
        # if categories:
        #     for category in categories:
        #         category_rules = self.get_rules_by_category(entity_type, category)
        #         for rule in category_rules:
        #             if rule not in rules_to_evaluate:
        #                 rules_to_evaluate.append(rule)

        # If no rules to evaluate, return empty list
        if not rules_to_evaluate:
            logger.warning(f"No rules found for the specified criteria")
            return []

        # Evaluate with the filtered rules
        return RuleEvaluator.evaluate_data(data_dict, rules_to_evaluate, entity_type)
