from typing import List, Optional
from app.api.models.rules import SpikeRule, SpikeStoredRule


class SpikeRuleEngine:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def __init__(self):
        self.spike_rule_repository: dict[str, SpikeStoredRule] = {}

    def add_rules(self, rules: list[SpikeRule]) -> None:
        for rule in rules:
            self.add_rule(rule)

    # update add_rule to allow adding optional list of categories 

    # list all rules
    @property
    def all_rules(self):
        return self.spike_rule_repository.values()

    def add_rule(self, rule: SpikeRule, categories: Optional[set[str]] = None) -> None:
        if categories is None:
            categories = set()
        print(rule)
        stored_rule_key = f"{rule.entity_type}|{rule.name}"

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
       


    def add_rule_category(self, rule_name: str, entity_type: str, category: str) -> None:
        stored_rule_key = f"{entity_type}|{rule_name}"
        if stored_rule_key in self.spike_rule_repository:
            # Check if the category already exists
            if category not in self.spike_rule_repository[stored_rule_key].categories:
                self.spike_rule_repository[stored_rule_key].categories.append(category)
        else:
            # raise error rule not found
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")

    
    def remove_rule_category(self, rule_name: str, entity_type: str, category: str) -> None:
        stored_rule_key = f"{entity_type}|{rule_name}"
        if stored_rule_key in self.spike_rule_repository:
            # Check if the category exists
            if category in self.spike_rule_repository[stored_rule_key].categories:
                self.spike_rule_repository[stored_rule_key].categories.remove(category)
        else:
            # raise error rule not found
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")
    
    def spike_get_entity_types(self) -> List[str]:
        """
        Get the list of entity types for which rules are loaded.

        Returns:
            List of entity types
        """
        # Get a set of unique entity types from the values of the spike_rule_repository
        entity_types = {rule.entity_type for rule in self.spike_rule_repository.values()}
        return entity_types.list()
    
    #  get spikestoredrule by name and entity type
    def get_spike_stored_rule_by_name_and_entity_type(self, rule_name: str, entity_type: str) -> SpikeStoredRule:
        stored_rule_key = f"{entity_type}|{rule_name}"
        if stored_rule_key in self.spike_rule_repository:
            return self.spike_rule_repository[stored_rule_key]
        else:
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")
        
    def get_spike_rule_by_name_and_entity_type(self, rule_name: str, entity_type: str) -> SpikeRule:
        stored_rule_key = f"{entity_type}|{rule_name}"
        if stored_rule_key in self.spike_rule_repository:
            return self.spike_rule_repository[stored_rule_key].rule
        else:
            # raise error rule not found
            raise ValueError(f"Rule with name '{rule_name}' not found for entity type '{entity_type}'")
    
    # check if rule exists
    def rule_exists(self, rule_name: str, entity_type: str) -> bool:
        stored_rule_key = f"{entity_type}|{rule_name}"
        return stored_rule_key in self.spike_rule_repository

    # get all rules, but if entity type is not none, get only rules for entity_type, and if category is not none, get only rules for entity_type and category
    def get_spike_stored_rules(self, entity_type: Optional[str] = None, category: Optional[str] = None) -> list[SpikeStoredRule]:
        if entity_type is None and category is None:
            return [stored_rule for stored_rule in self.spike_rule_repository.values()]
        elif entity_type is not None and category is None:
            return [stored_rule for _, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type]
        elif entity_type is not None and category is not None:
            return [stored_rule for key, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type and category in stored_rule.categories]

        
    # get rules by entity type
    def get_spike_rules_by_entity_type(self, entity_type: str) -> list[SpikeRule]:
        return [stored_rule.rule for key, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type]
    
    # get rules by entity type and category
    def get_spike_rules_by_entity_type_and_category(self, entity_type: str, category: str) -> list[SpikeRule]:
        return [stored_rule.rule for key, stored_rule in self.spike_rule_repository.items() if stored_rule.entity_type == entity_type and category in stored_rule.categories]

    