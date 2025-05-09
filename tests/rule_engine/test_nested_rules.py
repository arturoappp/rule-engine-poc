"""
Tests for deeply nested rule evaluations using pytest.
"""

import pytest
from rule_engine.core.rule_engine import RuleEngine
from app.api.models.rules import Rule


@pytest.fixture
def rule_engine():
    """Create a RuleEngine instance with a deeply nested rule."""
    engine = RuleEngine.get_instance()

    # Deep nested rules as Rule objects
    nested_rules = [
        Rule(
            name="Deep Nested Rule",
            entity_type="Decommission Request",
            description="A complex rule with several levels of nesting",
            conditions={
                "all": [
                    {
                        "any": [
                            {
                                "path": "$.Decommission Requests[*].type",
                                "operator": "equal",
                                "value": "firewall"
                            },
                            {
                                "all": [
                                    {
                                        "path": "$.Decommission Requests[*].type",
                                        "operator": "equal",
                                        "value": "router"
                                    },
                                    {
                                        "path": "$.Decommission Requests[*].security_level",
                                        "operator": "greater_than_equal",
                                        "value": 3
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "none": [
                            {
                                "path": "$.Decommission Requests[*].status",
                                "operator": "equal",
                                "value": "deprecated"
                            },
                            {
                                "not": {
                                    "path": "$.Decommission Requests[*].compliance_checked",
                                    "operator": "equal",
                                    "value": True
                                }
                            }
                        ]
                    }
                ]
            }
        )
    ]

    engine.add_rules(nested_rules)
    return engine


def test_nested_rule_firewall_pass(rule_engine):
    """Test case where firewall Decommission Requests pass the nested rule."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "firewall",
                "status": "active",
                "compliance_checked": True
            }
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert rule_result.success
    assert len(rule_result.failing_elements) == 0


def test_nested_rule_router_high_security_pass(rule_engine):
    """Test case where router Decommission Requests with high security pass the nested rule."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "router",
                "security_level": 4,
                "status": "active",
                "compliance_checked": True
            }
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert rule_result.success
    assert len(rule_result.failing_elements) == 0


def test_nested_rule_router_low_security_fail(rule_engine):
    """Test case where router Decommission Requests with low security fail the nested rule."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "router",
                "security_level": 2,  # This fails the security level check
                "status": "active",
                "compliance_checked": True
            }
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 1


def test_nested_rule_fail_deprecated(rule_engine):
    """Test case where Decommission Requests fail due to deprecated status."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "firewall",
                "status": "deprecated",  # This fails the status check
                "compliance_checked": True
            }
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 1


def test_nested_rule_fail_compliance(rule_engine):
    """Test case where Decommission Requests fail due to missing compliance check."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "firewall",
                "status": "active",
                "compliance_checked": False  # This fails the compliance check
            }
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 1


def test_nested_rule_mixed_entities(rule_engine):
    """Test case with mixed passing and failing Decommission Requests."""
    data = {
        "Decommission Requests": [
            {
                "id": "cfg-1",
                "type": "firewall",
                "status": "active",
                "compliance_checked": True
            },  # Should pass
            {
                "id": "cfg-2",
                "type": "router",
                "security_level": 2,
                "status": "active",
                "compliance_checked": True
            },  # Should fail - low security
            {
                "id": "cfg-3",
                "type": "firewall",
                "status": "deprecated",
                "compliance_checked": True
            },  # Should fail - deprecated
            {
                "id": "cfg-4",
                "type": "router",
                "security_level": 4,
                "status": "active",
                "compliance_checked": True
            }  # Should pass
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Decommission Request")
    rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

    assert rule_result is not None
    assert not rule_result.success

    # Check that exactly 2 Decommission Requests failed
    assert len(rule_result.failing_elements) == 2

    # Check failing Decommission Request IDs
    failing_ids = [element["id"] for element in rule_result.failing_elements]
    assert "cfg-2" in failing_ids
    assert "cfg-3" in failing_ids
