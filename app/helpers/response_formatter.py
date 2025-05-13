from app.api.models.rules import RuleListResponse, RuleViewModel, StoredRule


def format_list_rules_response(stored_rules: list[StoredRule]) -> RuleListResponse:
    sorted_stored_rules = sorted(stored_rules, key=lambda stored_rule: stored_rule.rule.name)
    rule_view_models = create_rule_view_models(sorted_stored_rules)

    response_model = RuleListResponse(
        rules=rule_view_models,
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
