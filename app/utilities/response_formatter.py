from app.api.models.rules import RuleListResponse, RuleStats


def format_list_rules_response(rules_by_entity: dict) -> RuleListResponse:
    entity_types = list(rules_by_entity.keys())
    categories = {}

    for entity_type, categories_rules in rules_by_entity.items():
        categories[entity_type] = list(categories_rules.keys())
    
       
    responseModel = RuleListResponse(entity_types=entity_types, categories=categories, rules=rules_by_entity)
    return responseModel