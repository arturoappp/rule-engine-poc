from typing import Dict, List
from app.api.models.rules import Rule, StoredRule


def create_rules_dict(stored_rules: list[StoredRule], categories_to_display: set[str], entity_types_to_display: set[str]) -> Dict[str, Dict[str, List[Dict]]]:
    result = {}
    for entity_type in entity_types_to_display:
        result[entity_type] = {}

        for category in categories_to_display:
            filtered_stored_rules = [stored_rule for stored_rule in stored_rules if category in stored_rule.categories and stored_rule.entity_type == entity_type]
            rules = [Rule(name=rule.rule_name, entity_type=rule.entity_type, description=rule.description, conditions=rule.rule.conditions) for rule in filtered_stored_rules]
            if len(rules) > 0:
                result[entity_type][category] = rules
    return result
