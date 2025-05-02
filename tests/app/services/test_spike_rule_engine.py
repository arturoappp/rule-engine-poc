import pytest
from app.services.spike_rule_engine import SpikeRuleEngine
from app.api.models.rules import SpikeRule, SpikeStoredRule

@pytest.fixture
def spike_rule_engine():
    return SpikeRuleEngine()


@pytest.fixture
def sample_rules():
    return [
        SpikeRule(name="Rule1", entity_type="Commission Request", description="Description1", conditions= { "condition": {}}),
        SpikeRule(name="Rule2", entity_type="Decommission Request", description="Description2", conditions= { "condition": {}}),
        SpikeRule(name="Rule3", entity_type="Commission Request", description="Description3", conditions= { "condition": {}}),
    ]


@pytest.fixture
def sample_stored_rules(spike_rule_engine, sample_rules):
    stored_rules = [
        SpikeStoredRule(
            rule_name=sample_rules[0].name,
            entity_type=sample_rules[0].entity_type,
            description=sample_rules[0].description,
            categories=["Should Run", "Can Run"],
            rule=sample_rules[0],
        ),
        SpikeStoredRule(
            rule_name=sample_rules[1].name,
            entity_type=sample_rules[1].entity_type,
            description=sample_rules[1].description,
            categories=["Should Run"],
            rule=sample_rules[1],
        ),
        SpikeStoredRule(
            rule_name=sample_rules[2].name,
            entity_type=sample_rules[2].entity_type,
            description=sample_rules[2].description,
            categories=["Should Run"],
            rule=sample_rules[2],
        ),
    ]

    for stored_rule in stored_rules:
        spike_rule_engine.spike_rule_repository[f"{stored_rule.entity_type}|{stored_rule.rule_name}"] = stored_rule

    return stored_rules


def test_get_spike_stored_rules_no_filters(spike_rule_engine, sample_stored_rules):

    result = spike_rule_engine.get_spike_stored_rules()

    assert len(result) == len(sample_stored_rules)
    assert all(rule in result for rule in sample_stored_rules)


def test_get_spike_stored_rules_by_entity_type(spike_rule_engine):

    result = spike_rule_engine.get_spike_stored_rules(entity_type="Commission Request")

    assert len(result) == 2
    assert all(rule.entity_type == "Commission Request" for rule in result)


def test_get_spike_stored_rules_by_categories(spike_rule_engine):

    result = spike_rule_engine.get_spike_stored_rules(categories=["Should Run"])

    assert len(result) == 3
    assert all("Should Run" in rule.categories for rule in result)


def test_get_spike_stored_rules_by_entity_type_and_categories(spike_rule_engine):

    result = spike_rule_engine.get_spike_stored_rules(entity_type="Commission Request", categories=["Should Run"])
    
    assert len(result) == 2
    assert all(rule.entity_type == "Commission Request" for rule in result)
    assert all("Should Run" in rule.categories for rule in result)


def test_get_spike_stored_rules_no_match(spike_rule_engine):

    result = spike_rule_engine.get_spike_stored_rules(entity_type="NonexistentType")

    assert len(result) == 0