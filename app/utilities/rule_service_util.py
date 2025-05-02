from typing import Dict, List
from app.api.models.rules import SpikeRule, SpikeStoredRule
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


def spike_create_rules_dict(stored_rules: list[SpikeStoredRule], categories: set[str], entity_types: set[str]) -> Dict[str, Dict[str, List[Dict]]]:
    result = {}
    for entity_type in entity_types:
        result[entity_type] = {}

        for category in categories:
            filtered_stored_rules = [stored_rule for stored_rule in stored_rules if category in stored_rule.categories and stored_rule.entity_type == entity_type]
            rules = [SpikeRule(name=rule.rule_name, entity_type=rule.entity_type, description=rule.description, conditions=rule.rule.conditions) for rule in filtered_stored_rules]
            # Check if rules is empty
            if len(rules) > 0:
               result[entity_type][category] = rules
    return result
