from app.api.models.rules import RuleListResponse


def format_list_rules_response(rules_by_entity: dict) -> RuleListResponse:
    entity_types = list(rules_by_entity.keys())
    categories = {}

    # Get categories for each entity type
    for entity_type, categories_rules in rules_by_entity.items():
        categories[entity_type] = list(categories_rules.keys())
   
    responseModel = RuleListResponse(entity_types=entity_types, categories=categories, rules=rules_by_entity)
    return responseModel