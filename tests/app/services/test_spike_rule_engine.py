import pytest
from rule_engine.core.rule_engine import RuleEngine
from app.api.models.rules import Rule, StoredRule


@pytest.fixture
def rule_engine():
    return RuleEngine()


@pytest.fixture
def sample_rules():
    return [
        Rule(name="Rule1", entity_type="Commission Request", description="Description1", conditions={"condition": {}}),
        Rule(name="Rule2", entity_type="Decommission Request", description="Description2", conditions={"condition": {}}),
        Rule(name="Rule3", entity_type="Commission Request", description="Description3", conditions={"condition": {}}),
    ]


@pytest.fixture
def sample_stored_rules(rule_engine, sample_rules):
    stored_rules = [
        StoredRule(
            rule_name=sample_rules[0].name,
            entity_type=sample_rules[0].entity_type,
            description=sample_rules[0].description,
            categories=["Should Run", "Can Run"],
            rule=sample_rules[0],
        ),
        StoredRule(
            rule_name=sample_rules[1].name,
            entity_type=sample_rules[1].entity_type,
            description=sample_rules[1].description,
            categories=["Should Run"],
            rule=sample_rules[1],
        ),
        StoredRule(
            rule_name=sample_rules[2].name,
            entity_type=sample_rules[2].entity_type,
            description=sample_rules[2].description,
            categories=["Should Run"],
            rule=sample_rules[2],
        ),
    ]

    for stored_rule in stored_rules:
        rule_engine.rule_repository[f"{stored_rule.entity_type}|{stored_rule.rule_name}"] = stored_rule

    return stored_rules


def test_get_stored_rules_no_filters(rule_engine, sample_stored_rules):

    result = rule_engine.get_stored_rules()

    assert len(result) == len(sample_stored_rules)
    assert all(rule in result for rule in sample_stored_rules)


def test_get_stored_rules_by_entity_type(rule_engine, sample_stored_rules):

    result = rule_engine.get_stored_rules(entity_type="Commission Request")

    assert len(result) == 2
    assert all(rule.entity_type == "Commission Request" for rule in result)


def test_get_stored_rules_by_categories(rule_engine, sample_stored_rules):

    result = rule_engine.get_stored_rules(categories=["Should Run"])

    assert len(result) == 3
    assert all("Should Run" in rule.categories for rule in result)


def test_get_stored_rules_by_entity_type_and_categories(rule_engine, sample_stored_rules):
    """Test filtering by both entity type and categories."""
    result = rule_engine.get_stored_rules(entity_type="Commission Request", categories=["Should Run"])
    
    assert len(result) == 2, f"Expected 2 rules, but got {len(result)}"
    assert all(rule.entity_type == "Commission Request" for rule in result), "All rules should have entity_type 'Commission Request'"
    assert all("Should Run" in rule.categories for rule in result), "All rules should include 'Should Run' in categories"


def test_get_stored_rules_no_match(rule_engine):

    result = rule_engine.get_stored_rules(entity_type="NonexistentType")

    assert len(result) == 0
