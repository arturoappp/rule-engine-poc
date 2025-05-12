from app.api.models.rules import RuleListResponse, RuleStats, RuleViewModel, StoredRule


def format_list_rules_response(stored_rules: list[StoredRule]) -> RuleListResponse:
    # Create a sorted list of entity_types by name

    sorted_stored_rules = sorted(stored_rules, key=lambda rule: rule.rule_name)
    entity_types_to_display = sorted({rule.entity_type for rule in sorted_stored_rules})
    categories_to_display = create_categories_to_display(sorted_stored_rules, entity_types_to_display)
    rule_view_models = create_rule_view_models(sorted_stored_rules)

    # categories = {}
    stats = create_stats_per_entity_type_and_category(sorted_stored_rules, categories_to_display)

    response_model = RuleListResponse(
        rules=rule_view_models,
        stats=stats
    )
    return response_model


def create_rule_view_models(sorted_stored_rules: list[StoredRule]) -> list[RuleViewModel]:
    rule_view_models = []
    for stored_rule in sorted_stored_rules:
        rule_view_model = RuleViewModel(
            rule_name=stored_rule.rule.name,
            entity_type=stored_rule.rule.entity_type,
            description=stored_rule.rule.description,
            conditions=stored_rule.rule.conditions,
            categories_associated_with=sorted(stored_rule.categories),
        )
        rule_view_models.append(rule_view_model)
    return rule_view_models


def create_stats_per_entity_type_and_category(sorted_stored_rules: list[StoredRule], categories_to_display):
    stats = {}
    return stats


def create_categories_to_display(sorted_stored_rules, entity_types_to_display):
    categories_to_display = {}
    for entity_type in entity_types_to_display:
        stored_rules_for_entity_type = [stored_rule for stored_rule in sorted_stored_rules if stored_rule.rule.entity_type == entity_type]

        unique_categories = set()
        for stored_rule in stored_rules_for_entity_type:
            unique_categories.update(stored_rule.categories)
        categories_to_display[entity_type] = sorted(unique_categories)
    return categories_to_display
