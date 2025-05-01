from typing import Dict, List
from app.api.models.rules import SpikeStoredRule
from app.services.spike_rule_engine import SpikeRuleEngine
from rule_engine.core.engine import RuleEngine


def create_rules_dict(engine: RuleEngine, provided_category: str, entity_types: list[str]) -> Dict[str, Dict[str, List[Dict]]]:
    result = {}
    for entity_type in entity_types:
        result[entity_type] = {}

        if provided_category is None:
            categories = engine.get_categories(entity_type)
        else:
            categories = [provided_category]

        for category in categories:
            # Get rules for this category
            rules = engine.get_rules_by_category(entity_type, category)
            result[entity_type][category] = rules

    return result


def spike_create_rules_dict(rules: list[SpikeStoredRule], categories: list[str], entity_types: list[str]) -> Dict[str, Dict[str, List[Dict]]]:
    result = {}
    for entity_type in entity_types:
        result[entity_type] = {}

        for category in categories:
            # Get rules for this category
            rules = [rule for rule in rules if category in rule.categories and rule.entity_type == entity_type]
            if not rules:
                rules = [rule for rule in rules if rule.category == category and rule.entity_type is None]
            result[entity_type][category] = rules

    return result
