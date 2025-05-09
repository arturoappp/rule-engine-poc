from app.api.models.rules import RuleListResponse, RuleStats, StoredRule


def format_list_rules_response(stored_rules: list[StoredRule]) -> RuleListResponse:
    # Create a sorted list of entity_types by name

    sorted_stored_rules = sorted(stored_rules, key=lambda rule: rule.rule_name)
    entity_types_to_display = sorted({rule.entity_type for rule in sorted_stored_rules})
    categories_to_display = create_categories_to_display(sorted_stored_rules, entity_types_to_display)
    rules_to_display = [sorted_stored_rule.rule for sorted_stored_rule in sorted_stored_rules]

    # categories = {}
    stats = create_stats_per_entity_type_and_category(stored_rules, categories_to_display)

    response_model = RuleListResponse(
        entity_types=entity_types_to_display,
        categories=categories_to_display,
        rules=rules_to_display,
        stats=stats
    )
    return response_model


def create_stats_per_entity_type_and_category(stored_rules, categories_to_display):
    stats = {}
    for entity_type, categories in categories_to_display.items():
        number_of_rules_for_entity = len([rule for rule in stored_rules if rule.entity_type == entity_type])

        entity_stats = {
            "total_rules": number_of_rules_for_entity,
            "rules_by_category": {}
        }

        # Count the number of rules in each category for the current entity_type
        for category in categories:
            category_rule_count = len([
                rule for rule in stored_rules
                if rule.entity_type == entity_type and category in rule.categories
            ])
            entity_stats["rules_by_category"][category] = category_rule_count

        stats[entity_type] = RuleStats(
            total_rules=entity_stats["total_rules"],
            rules_by_category=entity_stats["rules_by_category"]
        )
    return stats


def create_categories_to_display(sorted_stored_rules, entity_types_to_display):
    categories_to_display = {}
    for entity_type in entity_types_to_display:
        stored_rules_for_entity_type = [rule for rule in sorted_stored_rules if rule.entity_type == entity_type]

        unique_categories = set()
        for rule in stored_rules_for_entity_type:
            unique_categories.update(rule.categories)
        categories_to_display[entity_type] = sorted(unique_categories)
    return categories_to_display
