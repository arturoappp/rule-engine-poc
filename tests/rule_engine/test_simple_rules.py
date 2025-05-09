"""
Tests for simple rule evaluations using pytest.
"""

import pytest
from rule_engine.core.rule_engine import RuleEngine
from app.api.models.rules import Rule


@pytest.fixture
def rule_engine():
    """Create a RuleEngine instance with predefined rules."""
    engine = RuleEngine()

    # Simple "equal" rule
    equal_rule = [
        Rule(
            name="Equal Rule",
            entity_type="item",
            description="Tests the 'equal' operator",
            conditions={
                "all": [
                        {
                            "path": "$.items[*].value",
                            "operator": "equal",
                            "value": 10
                        }
                ]
            }
        )
    ]

    engine.add_rules(equal_rule)

    # Simple "not_equal" rule
    not_equal_rule = [
        Rule(
            name="Not Equal Rule",
            entity_type="item",
            description="Tests the 'not_equal' operator",
            conditions={
                "all": [
                        {
                            "path": "$.items[*].value",
                            "operator": "not_equal",
                            "value": 5
                        }
                ]
            }
        )
    ]

    engine.add_rules(not_equal_rule)

    return engine


def test_equal_rule_pass(rule_engine):
    """Test case where all items pass the 'equal' rule."""
    data = {
        "items": [
            {"id": "item-1", "value": 10},
            {"id": "item-2", "value": 10},
            {"id": "item-3", "value": 10}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="item")
    equal_rule_result = next((r for r in results if r.rule_name == "Equal Rule"), None)

    assert equal_rule_result is not None
    assert equal_rule_result.success
    assert len(equal_rule_result.failing_elements) == 0


def test_equal_rule_fail(rule_engine):
    """Test case where some items fail the 'equal' rule."""
    data = {
        "items": [
            {"id": "item-1", "value": 10},
            {"id": "item-2", "value": 15},  # This should fail
            {"id": "item-3", "value": 10}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="item")
    equal_rule_result = next((r for r in results if r.rule_name == "Equal Rule"), None)

    assert equal_rule_result is not None
    assert not equal_rule_result.success
    assert len(equal_rule_result.failing_elements) == 1
    assert equal_rule_result.failing_elements[0]["id"] == "item-2"


def test_not_equal_rule_pass(rule_engine):
    """Test case where all items pass the 'not_equal' rule."""
    data = {
        "items": [
            {"id": "item-1", "value": 10},
            {"id": "item-2", "value": 15},
            {"id": "item-3", "value": 20}
        ]
    }

    equal_rule = Rule(
        name="Equal Rule",
        entity_type="item",
        description="Tests the 'equal' operator",
        conditions={
                    "all": [
                        {"operator": "equal", "path": "$.items[*].value", "value": 10}
                    ]
        }
    )

    rule_engine.add_rules([equal_rule])

    results = rule_engine.evaluate_data(data, entity_type="item")
    not_equal_rule_result = next((r for r in results if r.rule_name == "Not Equal Rule"), None)

    assert not_equal_rule_result is not None
    assert not_equal_rule_result.success
    assert len(not_equal_rule_result.failing_elements) == 0


def test_not_equal_rule_fail(rule_engine):
    """Test case where some items fail the 'not_equal' rule."""
    data = {
        "items": [
            {"id": "item-1", "value": 10},
            {"id": "item-2", "value": 5},  # This should fail
            {"id": "item-3", "value": 20}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="item")
    not_equal_rule_result = next((r for r in results if r.rule_name == "Not Equal Rule"), None)

    assert not_equal_rule_result is not None
    assert not not_equal_rule_result.success
    assert len(not_equal_rule_result.failing_elements) == 1
    assert not_equal_rule_result.failing_elements[0]["id"] == "item-2"
