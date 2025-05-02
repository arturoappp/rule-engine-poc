from app.api.models.rules import RuleCondition, SpikeRule, SpikeStoredRule
from app.utilities.rule_service_util import spike_create_rules_dict


# def test_spike_create_rules_dict():
#     # Sample data
#     condition1 = RuleCondition()
#     condition2 = RuleCondition()
#     rule1 = SpikeRule(name="rule1", entity_type="entity1", description="description1", conditions=condition1)
#     rule2 = SpikeRule(name="rule2", entity_type="entity2", description="description2", conditions=condition2)

#     stored_rules = [
#         SpikeStoredRule(
#             rule_name=rule1.name,
#             entity_type=rule1.entity_type,
#             description=rule1.description,
#             rule=rule1,
#             categories=["category1", "category2"],
#         ),
#         SpikeStoredRule(
#             rule_name=rule2.name,
#             entity_type=rule2.entity_type,
#             description=rule2.description,
#             categories=["category1"],
#             rule=rule2,
#         )
#     ]
#     categories = {"category1", "category2"}
#     entity_types = {"entity1", "entity2"}

#     # Call the function
#     result = spike_create_rules_dict(stored_rules, categories, entity_types)

#     # Expected result
#     expected_result = {
#         "entity2": {
#             "category1": [
#                 rule2
#             ]
#         },
#         "entity1": {
#             "category1": [
#                 rule1
#             ],
#             "category2": [
#                 rule2
#             ]
#         },
#     }

#     # Assert the result
#     assert result == expected_result