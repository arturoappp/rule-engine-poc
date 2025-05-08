# tests/test_rule_service.py
from unittest.mock import Mock, patch, MagicMock
import json
import pytest

from pytest_mock import MockerFixture
from app.services.rule_service import RuleService
from app.api.models.rules import Rule, RuleCondition, SpikeAPIRule


@pytest.fixture
def rule_service():
    """Fixture to provide a rule service with mocked engine"""
    service = RuleService()
    # Create a mock rule engine with proper return values
    service.engine = Mock()

    # Set up basic mock behaviors
    service.engine.get_categories.return_value = ["Can Run", "Should Run", "Cannot Run"]
    service.engine.load_rules_from_json.return_value = None  # No return value needed

    return service


@pytest.fixture
def json_dumps_patch(monkeypatch):
    """Patch json.dumps to avoid serialization issues in tests"""
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
            add_to_categories=["Can Run", "Should Run"]  # Changed field name
        ),
        Rule(
            name="Test Rule 2",
            description="Test Description 2",
            conditions=RuleCondition(
                path="$.devices[*].osVersion",
                operator="equal",
                value="17.3.6"
            ),
            add_to_categories=["Should Run", "Cannot Run"]  # Changed field name
        )
    ]

    # Configure additional mock behaviors
    rule_service.engine.get_rules_by_category.return_value = []

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rules
    success, message, count = rule_service.store_rules("Commission Request", rules)

    # Check result
    assert success is True
    assert count == 2
    assert "new" in message

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called


def test_spike_store_rules_new(rule_service):
    """Test storing new rules"""

    # Create test rules
    rules = [
        SpikeAPIRule(
            name="Test Rule 1",
            description="Test Description 1",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Cisco Systems"
            ),
            add_to_categories=["Can Run", "Should Run"]
        ),
        SpikeAPIRule(
            name="Test Rule 2",
            description="Test Description 2",
            conditions=RuleCondition(
                path="$.devices[*].osVersion",
                operator="equal",
                value="17.3.6"
            ),
            add_to_categories=["Should Run", "Cannot Run"]
        )
    ]

    # Configure additional mock behaviors
    rule_service.engine.spike_get_rules_by_category.return_value = []

    # Store the rules
    success, message, count = rule_service.spike_store_rules("Commission Request", rules)

    # Check result
    assert success is True
    assert count == 2
    assert "new" in message


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
        add_to_categories=["Can Run", "Should Run"]  # Changed field name
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
            "add_to_categories": ["Can Run"]  # Changed field name
        }
    ]

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rule
    success, message, count = rule_service.store_rules("Commission Request", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "updated" in message  # Changed expectation

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called


def test_spike_store_rules_update(rule_service):  # Renamed function
    """Test updating existing rules"""  # Updated description
    # Create test rule
    rule = SpikeAPIRule(
        name="Existing Rule",
        description="Updated Description",
        conditions=RuleCondition(
            path="$.devices[*].vendor",
            operator="equal",
            value="Updated Value"
        ),
        add_to_categories=["Can Run", "Should Run"]  # Changed field name
    )

    # Store the rule
    success, message, count = rule_service.spike_store_rules("Commission Request", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "updated" in message  # Changed expectation


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
        add_to_categories=["Should Run", "Can Run", "category3"]  # Changed field name
    )

    # Configure additional mock behaviors
    rule_service.engine.get_rules_by_category.return_value = []

    # Fix for load_rules_from_json - shouldn't raise exceptions
    rule_service.engine.load_rules_from_json = MagicMock()

    # Store the rule
    success, message, count = rule_service.store_rules("Commission Request", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "categories" in message

    # Verify engine method calls
    assert rule_service.engine.load_rules_from_json.called


@pytest.mark.parametrize("entity_type, provided_categories, expected_entity_types", [
    ('commission', ['should'], {'commission'}),
    (None, None, {'commission', 'decommission'})
])
def test_get_rules_calls_spike_create_rules_dict_with_correct_parameters(mocker: MockerFixture, entity_type, provided_categories, expected_entity_types):
    if entity_type is None:
        entity_type1 = 'commission'
        entity_type2 = 'decommission'
    else:
        entity_type1 = entity_type
        entity_type2 = entity_type
    expected_result = {}
    mock_stored_rule1 = MagicMock()
    mock_stored_rule1.entity_type = entity_type1
    mock_stored_rule1.categories = provided_categories
    mock_stored_rule2 = MagicMock()
    mock_stored_rule2.entity_type = entity_type2
    mock_stored_rule2.categories = provided_categories
    stored_rules = [mock_stored_rule1, mock_stored_rule2]
    expected_provided_categories_set = set(provided_categories) if provided_categories else set()
    mock_spike_create_rules_dict = mocker.patch('app.services.rule_service.create_rules_dict')
    mock_spike_create_rules_dict.return_value = expected_result
    mock_engine = MagicMock()
    mock_engine.get_spike_stored_rules.return_value = stored_rules

    rule_service = RuleService()
    rule_service.spike_engine = mock_engine

    result = rule_service.get_rules(entity_type, provided_categories)

    mock_spike_create_rules_dict.assert_called_with(stored_rules, expected_provided_categories_set, expected_entity_types)
    assert result == expected_result


def test_update_rule_categories_add_success(rule_service):
    """Test successfully adding categories to a rule"""
    rule_service._add_categories = MagicMock()
    rule_service._remove_categories = MagicMock()

    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories = ["Should Run", "Can Run"]

    success, message = rule_service.update_rule_categories(rule_name, entity_type, categories, "add")

    assert success is True
    assert "Successfully updated categories" in message
    rule_service._add_categories.assert_called_once_with(entity_type, rule_name, categories)
    rule_service._remove_categories.assert_not_called()


def test_update_rule_categories_remove_success(rule_service):
    """Test successfully removing categories from a rule"""
    rule_service._add_categories = MagicMock()
    rule_service._remove_categories = MagicMock()

    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories = ["Should Run", "Can Run"]

    success, message = rule_service.update_rule_categories(rule_name, entity_type, categories, "remove")

    assert success is True
    assert "Successfully updated categories" in message
    rule_service._remove_categories.assert_called_once_with(rule_name, entity_type, categories)
    rule_service._add_categories.assert_not_called()


def test_update_rule_categories_invalid_action(rule_service):
    """Test updating categories with an invalid action"""
    rule_service._add_categories = MagicMock()
    rule_service._remove_categories = MagicMock()

    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories = ["Should Run", "Can Run"]

    success, message = rule_service.update_rule_categories(rule_name, entity_type, categories, "invalid_action")

    assert success is False
    assert "Invalid category action" in message
    rule_service._add_categories.assert_not_called()
    rule_service._remove_categories.assert_not_called()


def test_update_rule_categories_exception_handling(rule_service):
    """Test exception handling during category update"""
    rule_service._add_categories = MagicMock(side_effect=Exception("Test exception"))
    rule_service._remove_categories = MagicMock()

    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories = ["Should Run", "Can Run"]

    success, message = rule_service.update_rule_categories(rule_name, entity_type, categories, "add")

    assert success is False
    assert "Error updating rule categories" in message
    rule_service._add_categories.assert_called_once_with(entity_type, rule_name, categories)
    rule_service._remove_categories.assert_not_called()


def test_add_categories_success(rule_service):
    """Test successfully adding categories to a rule"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Cannot Run", "Should Not Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Can Run", "Should Run", "Cannot Run", "Should Not Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_no_existing_categories(rule_service):
    """Test adding categories to a rule with no existing categories"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = []
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Can Run", "Should Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Can Run", "Should Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_duplicate_categories(rule_service):
    """Test adding categories that already exist in the rule"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = ["Can Run", "Should Run"]
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Should Run", "Cannot Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    expected_categories = {"Can Run", "Should Run", "Cannot Run"}
    assert mock_rule.categories == expected_categories, f"Expected {expected_categories}, but got {mock_rule.categories}"
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_exception_handling(rule_service):
    """Test exception handling when adding categories"""
    # Mock the spike engine to raise an exception
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(side_effect=Exception("Test exception"))

    # Call the method and assert it raises an exception
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Can Run", "Should Run"]

    with pytest.raises(Exception, match="Test exception"):
        rule_service._add_categories(entity_type, rule_name, categories_to_add)

    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_success(rule_service):
    """Test successfully removing categories from a rule"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run", "Cannot Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Can Run", "Cannot Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Should Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_no_matching_categories(rule_service):
    """Test removing categories when none match"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Cannot Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories remain unchanged
    assert mock_rule.categories == {"Can Run", "Should Run"}
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_empty_categories(rule_service):
    """Test removing categories when the rule has no categories"""
    # Mock the rule returned by the spike engine
    mock_rule = MagicMock()
    mock_rule.categories = set()
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Can Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories remain empty
    assert mock_rule.categories == set()
    rule_service.spike_engine.get_spike_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)
