# tests/test_rule_service.py
from unittest.mock import Mock, MagicMock
import pytest

from pytest_mock import MockerFixture
from app.services.rule_service import RuleService
from app.api.models.rules import RuleCondition, APIRule, Rule


@pytest.fixture
def rule_service():
    """Fixture to provide a rule service with mocked engine"""
    service = RuleService()
    # Create a mock rule engine with proper return values
    service.engine = Mock()

    # Set up basic mock behaviors
    service.engine.get_categories.return_value = ["Can Run", "Should Run", "Cannot Run"]

    return service


def test_validate_rule_valid(rule_service):
    """Test validation of a valid rule"""
    # Create a test rule
    rule = Rule(
        name="Test Rule",
        entity_type="Commission Request",
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
        entity_type="Commission Request",
        description="Test Description",
        conditions=RuleCondition(),  # Empty conditions (invalid)
        add_to_categories=["test"]  # Changed field name
    )

    # Validate the rule
    valid, errors = rule_service.validate_rule(rule)

    # Check result
    assert valid is False
    assert len(errors) > 0
    assert any("Condition must be either" in error for error in errors)


def test_store_rules_new(rule_service):
    """Test storing new rules"""

    # Create test rules
    rules = [
        APIRule(
            name="Test Rule 1",
            description="Test Description 1",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Cisco Systems"
            ),
            add_to_categories=["Can Run", "Should Run"]
        ),
        APIRule(
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
    rule_service.engine.get_rules_by_category.return_value = []

    # Store the rules
    success, message, count = rule_service.store_rules("Commission Request", rules)

    # Check result
    assert success is True
    assert count == 2
    assert "new" in message


def test_store_rules_update(rule_service):  # Renamed function
    """Test updating existing rules"""  # Updated description
    # Create test rule
    rule = APIRule(
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
    success, message, count = rule_service.store_rules("Commission Request", [rule])

    # Check result
    assert success is True
    assert count == 1
    assert "updated" in message  # Changed expectation


def test_store_rules_multi_category(rule_service):
    """Test storing rules in multiple categories"""

    # Create test rule with multiple categories
    rule = APIRule(
        name="Multi Category Rule",
        entity_type="Commission Request",
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

    # Store the rule
    success, message, count = rule_service.store_rules("Commission Request", [rule])

    # Check result
    assert success is True
    assert count == 1


@pytest.mark.parametrize("entity_type, provided_categories, expected_entity_types", [
    ('commission', ['should'], {'commission'}),
    (None, None, {'commission', 'decommission'})
])
def test_get_rules_calls_create_rules_dict_with_correct_parameters(mocker: MockerFixture, entity_type, provided_categories, expected_entity_types):
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
    mock_create_rules_dict = mocker.patch('app.services.rule_service.create_rules_dict')
    mock_create_rules_dict.return_value = expected_result
    mock_engine = MagicMock()
    mock_engine.get_stored_rules.return_value = stored_rules

    rule_service = RuleService()
    rule_service.engine = mock_engine

    result = rule_service.get_rules(entity_type, provided_categories)

    mock_create_rules_dict.assert_called_with(stored_rules, expected_provided_categories_set, expected_entity_types)
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
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Cannot Run", "Should Not Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Can Run", "Should Run", "Cannot Run", "Should Not Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_no_existing_categories(rule_service):
    """Test adding categories to a rule with no existing categories"""
    mock_rule = MagicMock()
    mock_rule.categories = []
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Can Run", "Should Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Can Run", "Should Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_duplicate_categories(rule_service):
    """Test adding categories that already exist in the rule"""
    mock_rule = MagicMock()
    mock_rule.categories = ["Can Run", "Should Run"]
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Should Run", "Cannot Run"]
    rule_service._add_categories(entity_type, rule_name, categories_to_add)

    # Assert the categories were updated correctly
    expected_categories = {"Can Run", "Should Run", "Cannot Run"}
    assert mock_rule.categories == expected_categories, f"Expected {expected_categories}, but got {mock_rule.categories}"
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_add_categories_exception_handling(rule_service):
    """Test exception handling when adding categories"""
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(side_effect=Exception("Test exception"))

    # Call the method and assert it raises an exception
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_add = ["Can Run", "Should Run"]

    with pytest.raises(Exception, match="Test exception"):
        rule_service._add_categories(entity_type, rule_name, categories_to_add)

    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_success(rule_service):
    """Test successfully removing categories from a rule"""
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run", "Cannot Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Can Run", "Cannot Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories were updated correctly
    assert mock_rule.categories == {"Should Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_no_matching_categories(rule_service):
    """Test removing categories when none match"""
    mock_rule = MagicMock()
    mock_rule.categories = {"Can Run", "Should Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Cannot Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories remain unchanged
    assert mock_rule.categories == {"Can Run", "Should Run"}
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)


def test_remove_categories_empty_categories(rule_service):
    """Test removing categories when the rule has no categories"""
    mock_rule = MagicMock()
    mock_rule.categories = set()
    rule_service.engine.get_stored_rule_by_name_and_entity_type = MagicMock(return_value=mock_rule)

    # Call the method
    rule_name = "Test Rule"
    entity_type = "Commission Request"
    categories_to_remove = ["Can Run"]
    rule_service._remove_categories(rule_name, entity_type, categories_to_remove)

    # Assert the categories remain empty
    assert mock_rule.categories == set()
    rule_service.engine.get_stored_rule_by_name_and_entity_type.assert_called_once_with(rule_name, entity_type)
