from typing import Optional
from app.api.models.rules import SpikeRule, SpikeStoredRule
from app.utilities.logging import logger


class SpikeRuleEngine:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            logger.info("Initializing SpikeRuleEngine singleton instance")
        return cls._instance

    def __init__(self):
        self.spike_rule_repository: dict[str, SpikeStoredRule] = {}
        logger.debug("RuleEngine repository initialized")

    def add_rules(self, rules: list[SpikeRule]) -> None:
        logger.info(f"Adding {len(rules)} rules to engine")
        for rule in rules:
            self.add_rule(rule)
        logger.debug("Finished adding multiple rules")

    # list all rules
    @property
    def all_rules(self):
        rule_count = len(self.spike_rule_repository)
        logger.debug(f"Getting all rules ({rule_count} total)")
        return self.spike_rule_repository.values()

    def add_rule(self, rule: SpikeRule, categories: Optional[set[str]] = None) -> None:
        if categories is None:
            categories = set()

        logger.params.set(
            entity_type=rule.entity_type,
            rule_name=rule.name,
            category=','.join(categories) if categories else None
        )

        logger.info(f"Adding rule with {len(categories)} categories")

        stored_rule_key = f"{rule.entity_type}|{rule.name}"

        if stored_rule_key in self.spike_rule_repository:
            existing_rule = self.spike_rule_repository[stored_rule_key]
            existing_categories = existing_rule.categories
            logger.info(f"Overwriting existing rule with previous categories: {existing_categories}")

        new_spike_stored_rule = SpikeStoredRule(
            rule_name=rule.name,
            entity_type=rule.entity_type,
            description=rule.description,
            categories=list(categories),
            rule=rule
        )
        # TODO: Should we require the user to pass an "overwrite" parameter to allow overwriting existing rules?
        # Would prevent accidental overwrites
        self.spike_rule_repository[stored_rule_key] = new_spike_stored_rule
        logger.debug(f"Rule successfully added to repository with key: {stored_rule_key}")

    def get_spike_stored_rule_by_name_and_entity_type(self, rule_name: str, entity_type: str) -> SpikeStoredRule:
        logger.params.set(entity_type=entity_type, rule_name=rule_name)

        stored_rule_key = f"{entity_type}|{rule_name}"
        logger.debug(f"Looking up rule with key: {stored_rule_key}")

        if stored_rule_key in self.spike_rule_repository:
            logger.debug(f"Rule found: {stored_rule_key}")
            return self.spike_rule_repository[stored_rule_key]
        else:
            logger.warning(f"Rule not found: {stored_rule_key}")
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")

    # check if rule exists
    def rule_exists(self, rule_name: str, entity_type: str) -> bool:
        stored_rule_key = f"{entity_type}|{rule_name}"
        exists = stored_rule_key in self.spike_rule_repository

        logger.debug(f"Checking if rule exists: {stored_rule_key}, result: {exists}")

        return exists

    # get all rules, but if entity type is not none, get only rules for entity_type, and if category is not none, get only rules for entity_type and category
    def get_spike_stored_rules(self, entity_type: Optional[str] = None, categories: Optional[list[str]] = None) -> list[
        SpikeStoredRule]:
        # Set context for logging
        logger.params.set(
            entity_type=entity_type,
            category=','.join(categories) if categories else None
        )

        filter_desc = []
        if entity_type:
            filter_desc.append(f"entity_type='{entity_type}'")
        if categories:
            filter_desc.append(f"categories={categories}")

        filter_str = " and ".join(filter_desc) if filter_desc else "no filters"
        logger.info(f"Getting stored rules with {filter_str}")

        stored_rules = []
        if entity_type is None and categories is None:
            stored_rules = [stored_rule for stored_rule in self.spike_rule_repository.values()]
        elif entity_type is not None and categories is None:
            stored_rules = [stored_rule for _, stored_rule in self.spike_rule_repository.items() if
                            stored_rule.entity_type == entity_type]
        elif entity_type is None and categories is not None:
            stored_rules = [stored_rule for _, stored_rule in self.spike_rule_repository.items() if
                            any(category in stored_rule.categories for category in categories)]
        elif entity_type is not None and categories is not None:
            stored_rules = [stored_rule for key, stored_rule in self.spike_rule_repository.items() if
                            stored_rule.entity_type == entity_type and any(
                                category in stored_rule.categories for category in categories)]

        if stored_rules is None:
            logger.debug("No rules found, returning empty list")
            return []

        logger.info(f"Found {len(stored_rules)} rules matching criteria")
        return stored_rules