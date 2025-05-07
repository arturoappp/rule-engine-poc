"""
Tests for all operator implementations in the rule engine using pytest.
"""

import pytest
from app.services.spike_rule_engine import SpikeRuleEngine
from app.services.spike_rule_engine import SpikeRule


@pytest.fixture
def rule_engine():
    """Create a RuleEngine instance with rules for testing various operators."""
    engine = SpikeRuleEngine()

    # Load a rule for each operator type
    operator_rules = [
        SpikeRule(
            name="Equal Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "equal",
                        "value": 100
                    }
                ]
            }
        ),
        SpikeRule(
            name="Not Equal Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "not_equal",
                        "value": 50
                    }
                ]
            }
        ),
        SpikeRule(
            name="Greater Than Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "greater_than",
                        "value": 75
                    }
                ]
            }
        ),
        SpikeRule(
            name="Less Than Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "less_than",
                        "value": 200
                    }
                ]
            }
        ),
        SpikeRule(
            name="Greater Than Equal Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "greater_than_equal",
                        "value": 100
                    }
                ]
            }
        ),
        SpikeRule(
            name="Less Than Equal Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].price",
                        "operator": "less_than_equal",
                        "value": 100
                    }
                ]
            }
        ),
        SpikeRule(
            name="Exists Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].discount",
                        "operator": "exists",
                        "value": True
                    }
                ]
            }
        ),
        SpikeRule(
            name="Not Empty Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].tags",
                        "operator": "not_empty",
                        "value": True
                    }
                ]
            }
        ),
        SpikeRule(
            name="Match Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].sku",
                        "operator": "match",
                        "value": "^PRD-[0-9]{4}$"
                    }
                ]
            }
        ),
        SpikeRule(
            name="Contains Operator Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.Commission Request[*].description",
                        "operator": "contains",
                        "value": "premium"
                    }
                ]
            }
        )
    ]
    # add all of the objects in the list to the engine
    engine.add_rules(operator_rules)
    return engine


def test_equal_operator(rule_engine):
    """Test the 'equal' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Equal Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 101, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Equal Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_not_equal_operator(rule_engine):
    """Test the 'not_equal' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Not Equal Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 50, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Not Equal Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_greater_than_operator(rule_engine):
    """Test the 'greater_than' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Greater Than Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 75, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Greater Than Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_less_than_operator(rule_engine):
    """Test the 'less_than' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Less Than Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 200, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Less Than Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_greater_than_equal_operator(rule_engine):
    """Test the 'greater_than_equal' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Greater Than Equal Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 99, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Greater Than Equal Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_less_than_equal_operator(rule_engine):
    """Test the 'less_than_equal' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Less Than Equal Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 101, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Less Than Equal Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_exists_operator(rule_engine):
    """Test the 'exists' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Exists Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "tags": ["electronics"], "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Exists Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_not_empty_operator(rule_engine):
    """Test the 'not_empty' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Not Empty Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": [], "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Not Empty Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_match_operator(rule_engine):
    """Test the 'match' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Match Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRODUCT-001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Match Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_contains_operator(rule_engine):
    """Test the 'contains' operator."""
    # Passing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A premium product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Contains Operator Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Failing case
    data = {
        "Commission Request": [
            {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
             "description": "A standard product"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Contains Operator Rule"), None)

    assert rule_result is not None
    assert not rule_result.success


def test_value_in_list(rule_engine):
    """Test checking if a value exists in a list."""
    # Add a rule that checks if a value is in a list
    list_rule = [
        SpikeRule(
            name="Protocol Check Rule",
            entity_type="Commission Request",
            conditions={
                "all": [
                    {
                        "path": "$.connections[*].protocol",
                        "operator": "in_list",
                        "value": ["HTTP", "HTTPS", "FTP", "SFTP"]
                    }
                ]
            }
        )
    ]
    rule_engine.add_rules(list_rule)

    # Test success case
    data = {
        "Commission Requests": [
            {"id": "conn-1", "protocol": "HTTPS", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Protocol Check Rule"), None)

    assert rule_result is not None
    assert rule_result.success

    # Test failure case
    data = {
        "Commission Requests": [
            {"id": "conn-1", "protocol": "TELNET", "status": "active"}
        ]
    }

    results = rule_engine.evaluate_data(data, entity_type="Commission Request")
    rule_result = next((r for r in results if r.rule_name == "Protocol Check Rule"), None)

    assert rule_result is not None
    assert not rule_result.success
