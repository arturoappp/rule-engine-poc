from app.api.models.rules import RuleListResponse, RuleStats


def format_list_rules_response(rules_by_entity: dict) -> RuleListResponse:
     # Format response
    entity_types = list(rules_by_entity.keys())
    categories = {}
    stats = {}

    # Get categories and statistics for each entity type
    for entity_type, categories_rules in rules_by_entity.items():
        categories[entity_type] = list(categories_rules.keys())

        # Calcular estadísticas
        entity_stats = {
            "total_rules": 0,
            "rules_by_category": {}
        }

        for category, rules_list in categories_rules.items():
            category_rule_count = len(rules_list)
            entity_stats["rules_by_category"][category] = category_rule_count
            entity_stats["total_rules"] += category_rule_count

        stats[entity_type] = RuleStats(total_rules=entity_stats["total_rules"], rules_by_category=entity_stats["rules_by_category"])


    responseModel = RuleListResponse(entity_types=entity_types, categories=categories, rules=rules_by_entity, stats=stats)
    return responseModel