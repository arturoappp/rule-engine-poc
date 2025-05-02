from app.api.models.rules import RuleCondition, SpikeRule, SpikeStoredRule
from app.utilities.rule_service_util import spike_create_rules_dict


def test_spike_create_rules_dict_empty_stored_rules():
    """Test with no stored rules."""
    stored_rules = []
    categories = {"category1", "category2"}
    entity_types = {"entity1", "entity2"}

    result = spike_create_rules_dict(stored_rules, categories, entity_types)

    assert result == {"entity1": {}, "entity2": {}}


def test_spike_create_rules_dict_no_matching_categories():
    """Test when no categories match."""
    condition = RuleCondition()
    rule = SpikeRule(name="rule1", entity_type="entity1", description="description1", conditions=condition)
    stored_rules = [
        SpikeStoredRule(
            rule_name=rule.name,
            entity_type=rule.entity_type,
            description=rule.description,
            rule=rule,
            categories=["non_matching_category"],
        )
    ]
    categories = {"category1", "category2"}
    entity_types = {"entity1"}

    result = spike_create_rules_dict(stored_rules, categories, entity_types)

    assert result == {"entity1": {}}


def test_spike_create_rules_dict_no_matching_entity_types():
    """Test when no entity types match."""
    condition = RuleCondition()
    rule = SpikeRule(name="rule1", entity_type="non_matching_entity", description="description1", conditions=condition)
    stored_rules = [
        SpikeStoredRule(
            rule_name=rule.name,
            entity_type=rule.entity_type,
            description=rule.description,
            rule=rule,
            categories=["category1"],
        )
    ]
    categories = {"category1"}
    entity_types = {"entity1"}

    result = spike_create_rules_dict(stored_rules, categories, entity_types)

    assert result == {"entity1": {}}


def test_spike_create_rules_dict_multiple_rules_same_category():
    """Test multiple rules in the same category."""
    condition1 = RuleCondition()
    condition2 = RuleCondition()
    rule1 = SpikeRule(name="rule1", entity_type="entity1", description="description1", conditions=condition1)
    rule2 = SpikeRule(name="rule2", entity_type="entity1", description="description2", conditions=condition2)
    stored_rules = [
        SpikeStoredRule(
            rule_name=rule1.name,
            entity_type=rule1.entity_type,
            description=rule1.description,
            rule=rule1,
            categories=["category1"],
        ),
        SpikeStoredRule(
            rule_name=rule2.name,
            entity_type=rule2.entity_type,
            description=rule2.description,
            rule=rule2,
            categories=["category1"],
        )
    ]
    categories = {"category1"}
    entity_types = {"entity1"}

    result = spike_create_rules_dict(stored_rules, categories, entity_types)

    assert result == {
        "entity1": {
            "category1": [rule1, rule2]
        }
    }

def test_spike_create_rules_dict_multiple_rules_different_entity_types_and_categories():
    # Sample data
    condition1 = RuleCondition()
    condition2 = RuleCondition()
    commission_entity  = "commission request"
    decommision_entity = "decommission request"
    should_run_category = "should run"
    could_run_category = "could run"
    rule1 = SpikeRule(name="rule1", entity_type=commission_entity, description="description1", conditions=condition1)
    rule2 = SpikeRule(name="rule2", entity_type=decommision_entity, description="description2", conditions=condition2)

    stored_rules = [
        SpikeStoredRule(
            rule_name=rule1.name,
            entity_type=rule1.entity_type,
            description=rule1.description,
            rule=rule1,
            categories=[should_run_category, could_run_category],
        ),
        SpikeStoredRule(
            rule_name=rule2.name,
            entity_type=rule2.entity_type,
            description=rule2.description,
            categories=[should_run_category],
            rule=rule2,
        )
    ]
    categories = {should_run_category, could_run_category}
    entity_types = {commission_entity, decommision_entity}

    # Call the function
    result = spike_create_rules_dict(stored_rules, categories, entity_types)

    # Expected result
    expected_result = {
        decommision_entity: {
            should_run_category: [
                rule2
            ]
        },
        commission_entity: {
            should_run_category: [
                rule1
            ],
            could_run_category: [
                rule1
            ]
        },
    }

    # Assert the result
    assert result == expected_result