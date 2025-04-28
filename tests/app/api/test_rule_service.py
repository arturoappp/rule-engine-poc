# tests/test_rule_service.py
import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from pytest_mock import MockerFixture
from app.services.rule_service import RuleService
from app.api.models.rules import Rule, RuleCondition


@pytest.fixture
def rule_service():
    """Fixture to provide a rule service with mocked engine"""
    service = RuleService()
    # Create a mock rule engine with proper return values
    service.engine = Mock()

    # Set up basic mock behaviors
    service.engine.get_categories.return_value = ["test1", "test2", "test3"]
    service.engine.load_rules_from_json.return_value = None  # No return value needed

    return service


@pytest.fixture
def json_dumps_patch(monkeypatch):
    """Patch json.dumps to avoid serialization issues in tests"""
    original_dumps = json.dumps
    monkeypatch.setattr(json, 'dumps', lambda x, **kwargs: str(x))
    yield


def test_validate_rule_valid(rule_service):
    """Test validation of a valid rule"""
    # Create a test rule
    rule = Rule(
        name="Test Rule",
        description="Test Description",
        conditions=RuleCondition(
            path="$.devices[*].vendor",
            operator="equal",
            value="Cisco Systems"
        ),
        add_to_categories=["test"]  # Changed field name
    )

    # Validate the rule
    valid, errors = rule_service.validate_rule(rule)

    # Check result
    assert valid is True
    assert errors is None


def test_validate_rule_invalid(rule_service):
    """Test validation of an invalid rule"""
    # Create an invalid test rule (missing required fields)
    rule = Rule(
        name="test name",
        description="Test Description",
        conditions=RuleCondition(),  # Empty conditions (invalid)
        add_to_categories=["test"]  # Changed field name
    )

    # Validate the rule
    valid, errors = rule_service.validate_rule(rule)

    # Check result
    assert valid is False
    assert len(errors) > 0
    assert any("conditions" in error.lower() for error in errors)


@patch('app.services.rule_service.json.dumps')
def test_store_rules_new(mock_dumps, rule_service):
    """Test storing new rules"""
    # Configure mock to return a valid JSON string
    mock_dumps.return_value = "[]"

    # Create test rules
    rules = [
        Rule(
            name="Test Rule 1",
            description="Test Description 1",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Cisco Systems"
            ),
            add_to_categories=["test1", "test2"]  # Changed field name
        ),
        Rule(
            name="Test Rule 2",
            description="Test Description 2",
            conditions=RuleCondition(
                path="$.devices[*].osVersion",
                operator="equal",
                value="17.3.6"
            ),
            add_to_categories=["test2", "test3"]  # Changed field name
        )
    ]

    # Configure additional mock behaviors
    rule_service.engine.get_rules_by_category.return_value = []

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rules
    success, message, count = rule_service.store_rules("device", rules)

    # Check result
    assert success is True
    assert count == 2
    assert "new" in message

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called


@patch('app.services.rule_service.json.dumps')
def test_store_rules_update(mock_dumps, rule_service):  # Renamed function
    """Test updating existing rules"""  # Updated description
    # Configure mock to return a valid JSON string
    mock_dumps.return_value = "[]"

    # Create test rule
    rule = Rule(
        name="Existing Rule",
        description="Updated Description",
        conditions=RuleCondition(
            path="$.devices[*].vendor",
            operator="equal",
            value="Updated Value"
        ),
        add_to_categories=["test1", "test2"]  # Changed field name
    )

    # Configure additional mock behaviors
    rule_service.engine.get_rules_by_category.return_value = [
        {
            "name": "Existing Rule",
            "description": "Old Description",
            "conditions": {
                "path": "$.devices[*].vendor",
                "operator": "equal",
                "value": "Old Value"
            },
            "add_to_categories": ["test1"]  # Changed field name
        }
    ]

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rule
    success, message, count = rule_service.store_rules("device", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "updated" in message  # Changed expectation

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called


@patch('app.services.rule_service.json.dumps')
def test_store_rules_multi_category(mock_dumps, rule_service):
    """Test storing rules in multiple categories"""
    # Configure mock to return a valid JSON string
    mock_dumps.return_value = "[]"

    # Create test rule with multiple categories
    rule = Rule(
        name="Multi Category Rule",
        description="Test Description",
        conditions=RuleCondition(
            path="$.devices[*].vendor",
            operator="equal",
            value="Cisco Systems"
        ),
        add_to_categories=["category1", "category2", "category3"]  # Changed field name
    )

    # Configure additional mock behaviors
    rule_service.engine.get_rules_by_category.return_value = []

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rule
    success, message, count = rule_service.store_rules("device", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "categories" in message

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called

@pytest.mark.parametrize("entity_type, provided_category, expected_entity_types", [
     ('commission', 'should', ['commission']),
     (None, None, ['commission', 'decommission'])
])
def test_get_rules_calls_create_rules_dict_with_correct_parameters(mocker: MockerFixture, entity_type, provided_category, expected_entity_types):
    expected_result = {}
    mock_create_rules_dict = mocker.patch('app.services.rule_service.create_rules_dict')
    mock_create_rules_dict.return_value = expected_result
    mock_engine = MagicMock()
    mock_engine.get_entity_types.return_value = ['commission', 'decommission']
 
    rule_service = RuleService()
    rule_service.engine = mock_engine

    result = rule_service.get_rules(entity_type, provided_category)

    mock_create_rules_dict.assert_called_with(mock_engine, provided_category, expected_entity_types)
    assert result == expected_result