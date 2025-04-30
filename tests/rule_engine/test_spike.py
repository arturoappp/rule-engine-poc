import json
from app.api.models.rules import SpikeRule
from app.services.spike_rule_engine import SpikeRuleEngine


spike_engine = SpikeRuleEngine().get_instance()

cr_equal_rule = """
        {
            "name": "Equal Rule",
            "entity_type": "Commission Request",
            "description": "Tests the 'equal' operator",
            "conditions": {
                "all": [
                    {
                        "path": "$.items[*].value",
                        "operator": "equal",
                        "value": 10
                    }
                ]
            }
        }
    """

cr_not_equal_rule = """
        {
            "name": "Not Equal Rule",
            "entity_type": "Commission Request",
            "description": "Tests the 'not_equal' operator",
            "conditions": {
                "all": [
                    {
                        "path": "$.items[*].value",
                        "operator": "not_equal",
                        "value": 5
                    }
                ]
            }
        }
    """

dr_equal_rule = """
        {
            "name": "Equal Rule",
            "entity_type": "Decommission Request",
            "description": "Tests the 'equal' operator",
            "conditions": {
                "all": [
                    {
                        "path": "$.items[*].value",
                        "operator": "equal",
                        "value": 10
                    }
                ]
            }
        }
    """

dr_not_equal_rule = """
        {
            "name": "Not Equal Rule",
            "entity_type": "Decommission Request",
            "description": "Tests the 'not_equal' operator",
            "conditions": {
                "all": [
                    {
                        "path": "$.items[*].value",
                        "operator": "not_equal",
                        "value": 5
                    }
                ]
            }
        }
    """

# Load rules into the SpikeRuleManager instance
spike_engine.add_rule(SpikeRule.parse_raw(cr_equal_rule), categories=["Paul", "Micah"])
spike_engine.add_rules([SpikeRule.parse_raw(cr_not_equal_rule)])
spike_engine.add_rules([SpikeRule.parse_raw(dr_equal_rule), SpikeRule.parse_raw(dr_not_equal_rule)])

# Add categories to the rules
spike_engine.add_rule_category("Equal Rule", "Commission Request", "Can Run")
spike_engine.add_rule_category("Not Equal Rule", "Commission Request", "Can Run")
spike_engine.add_rule_category("Equal Rule", "Decommission Request", "Should Run")
spike_engine.add_rule_category("Not Equal Rule", "Decommission Request", "Can Run")
spike_engine.add_rule_category("Not Equal Rule", "Decommission Request", "Should Run")


result = spike_engine.get_spike_rules_by_entity_type_and_category(
    "Decommission Request", "Should Run"
)
result2 = spike_engine.get_spike_rules_by_entity_type_and_category(
    "Commission Request", "Micah"
)
assert len(result2) == 1, "Should only return one rule"
# remove micah category
spike_engine.remove_rule_category("Equal Rule", "Commission Request", "Micah")
result3 = spike_engine.get_spike_rules_by_entity_type_and_category(
    "Commission Request", "Micah"
)
assert len(result3) == 0, "Should not return any rules"
spike_engine.remove_rule_category("Equal Rule", "Commission Request", "Can Run")
spike_engine.remove_rule_category("Equal Rule", "Commission Request", "Paul")
result_rule_still_exists_with_no_category = spike_engine.get_spike_rule_by_name_and_entity_type(
    "Equal Rule", "Commission Request"
)
assert result_rule_still_exists_with_no_category is not None, "Rule should still exist without categories"

print(result)  # Should print the rules that match the criteria
