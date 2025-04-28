"""
Tests for the role_device operator in the rule engine using pytest.
"""

import pytest
from rule_engine.core.engine import RuleEngine


@pytest.fixture
def rule_engine():
    """Create a RuleEngine instance with rules for testing the role_device operator."""
    engine = RuleEngine()

    # Load rules for testing the role_device operator
    role_device_rule = """
    [
        {
            "name": "Standalone Device Rule",
            "description": "Checks if the device is a standalone device",
            "conditions": {
                "all": [
                    {
                        "path": "$.devices[*].hostname",
                        "operator": "role_device",
                        "value": "standalone"
                    }
                ]
            }
        },
        {
            "name": "Primary Device Rule",
            "description": "Checks if the device is a primary device",
            "conditions": {
                "all": [
                    {
                        "path": "$.devices[*].hostname",
                        "operator": "role_device",
                        "value": "primary"
                    }
                ]
            }
        },
        {
            "name": "Secondary Device Rule",
            "description": "Checks if the device is a secondary device",
            "conditions": {
                "all": [
                    {
                        "path": "$.devices[*].hostname",
                        "operator": "role_device",
                        "value": "secondary"
                    }
                ]
            }
        }
    ]
    """
    engine.load_rules_from_json(role_device_rule, entity_type="device", category="role")

    return engine


def test_standalone_device(rule_engine):
    """Test the 'role_device' operator with standalone devices."""
    # Test passing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-001", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Test failing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_primary_device(rule_engine):
    """Test the 'role_device' operator with primary devices."""
    # Test passing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Test failing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-201", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_secondary_device(rule_engine):
    """Test the 'role_device' operator with secondary devices."""
    # Test passing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-201", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Test failing case
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    rule_result = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_invalid_hostname_format(rule_engine):
    """Test the 'role_device' operator with invalid hostname format."""
    data = {
        "devices": [
            {"id": "device-1", "hostname": "INVALID", "status": "active"}
        ]
    }

    # The operator should handle invalid formats gracefully
    # We expect all rules to fail in this case
    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])

    for rule_result in results:
        assert not rule_result.success


def test_multiple_devices(rule_engine):
    """Test the 'role_device' operator with multiple devices of different roles."""
    data = {
        "devices": [
            {"id": "device-1", "hostname": "HUJ-AA-001", "status": "active"},  # standalone
            {"id": "device-2", "hostname": "HUJ-AA-101", "status": "active"},  # primary
            {"id": "device-3", "hostname": "HUJ-AA-201", "status": "active"}  # secondary
        ]
    }

    # Test standalone rule
    results = rule_engine.evaluate_data(data, entity_type="device", categories=["role"])
    standalone_rule = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

    assert standalone_rule is not None
    assert not standalone_rule.success  # Should fail because not all devices are standalone
    assert len(standalone_rule.failing_elements) == 2

    # Check the failing elements
    failing_ids = [element["id"] for element in standalone_rule.failing_elements]
    assert "device-2" in failing_ids
    assert "device-3" in failing_ids

    # Test primary rule
    primary_rule = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

    assert primary_rule is not None
    assert not primary_rule.success  # Should fail because not all devices are primary
    assert len(primary_rule.failing_elements) == 2

    # Check the failing elements
    failing_ids = [element["id"] for element in primary_rule.failing_elements]
    assert "device-1" in failing_ids
    assert "device-3" in failing_ids

    # Test secondary rule
    secondary_rule = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

    assert secondary_rule is not None
    assert not secondary_rule.success  # Should fail because not all devices are secondary
    assert len(secondary_rule.failing_elements) == 2

    # Check the failing elements
    failing_ids = [element["id"] for element in secondary_rule.failing_elements]
    assert "device-1" in failing_ids
    assert "device-2" in failing_ids