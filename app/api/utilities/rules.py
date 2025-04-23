from rule_engine.core.engine import RuleEngine


def create_rules_dict(engine: RuleEngine, provided_category: str, entity_types: list[str]):
        result = {}
        for entity_type in entity_types:
            result[entity_type] = {}

            if provided_category == None:
                categories = engine.get_categories(entity_type)
            else:
                categories = [provided_category]

            for category in categories:
                # Get rules for this category
                rules = engine.get_rules_by_category(entity_type, category)
                result[entity_type][category] = rules