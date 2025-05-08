"""
Tests for complex rule evaluations with nested logical operators using pytest.
"""

import pytest
from app.services.rule_engine import RuleEngine
from app.api.models.rules import Rule


@pytest.fixture
def rule_engine():
    """Create a SpikeRuleEngine instance with a complex rule."""
    engine = RuleEngine.get_instance()

    # Complex rules as SpikeRule objects
    complex_rules = [
        Rule(
            name="Complex Device Rule",
            entity_type="device",
            description="Vendor must be Cisco with version 17.x, or non-Cisco with any version above 10.0",
            conditions={
                "any": [
                    {
                        "all": [
                            {
                                "path": "$.devices[*].vendor",
                                "operator": "equal",
                                "value": "Cisco Systems"
                            },
                            {
                                "path": "$.devices[*].osVersion",
                                "operator": "match",
                                "value": "^17\\."
                            }
                        ]
                    },
                    {
                        "all": [
                            {
                                "path": "$.devices[*].vendor",
                                "operator": "not_equal",
                                "value": "Cisco Systems"
                            },
                            {
                                "path": "$.devices[*].osVersion",
                                "operator": "match",
                                "value": "^[1-9][0-9]\\."
                            }
                        ]
                    }
                ]
            }
        )
    ]

    engine.add_rules(complex_rules)
    return engine


def test_complex_rule_cisco_pass(rule_engine):
    """Test case where Cisco devices with correct version pass."""
    data = {
        "devices": [
            {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "17.3.6"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device")
    rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

    assert rule_result is not None
    assert rule_result.success
    assert len(rule_result.failing_elements) == 0


def test_complex_rule_non_cisco_pass(rule_engine):
    """Test case where non-Cisco devices with correct version pass."""
    data = {
        "devices": [
            {"id": "device-1", "vendor": "Juniper", "osVersion": "20.1"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device")
    rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

    assert rule_result is not None
    assert rule_result.success
    assert len(rule_result.failing_elements) == 0


def test_complex_rule_cisco_fail(rule_engine):
    """Test case where Cisco devices with wrong version fail."""
    data = {
        "devices": [
            {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "16.9.5"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device")
    rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 1


def test_complex_rule_non_cisco_fail(rule_engine):
    """Test case where non-Cisco devices with wrong version fail."""
    data = {
        "devices": [
            {"id": "device-1", "vendor": "Juniper", "osVersion": "9.5"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device")
    rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 1


def test_complex_rule_mixed_results(rule_engine):
    """Test case with mixed passing and failing devices."""
    data = {
        "devices": [
            {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "17.3.6"},  # Pass
            {"id": "device-2", "vendor": "Cisco Systems", "osVersion": "16.9.5"},  # Fail
            {"id": "device-3", "vendor": "Juniper", "osVersion": "20.1"},  # Pass
            {"id": "device-4", "vendor": "Juniper", "osVersion": "9.5"}  # Fail
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device")
    rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
    assert len(rule_result.failing_elements) == 2

    # Check failing device IDs
    failing_ids = [element["id"] for element in rule_result.failing_elements]
    assert "device-2" in failing_ids
    assert "device-4" in failing_ids
