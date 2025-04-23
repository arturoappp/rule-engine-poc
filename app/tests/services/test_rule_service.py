import pytest
from unittest.mock import MagicMock

from app.services.rule_service import RuleService

def test_get_rules(mocker):
    # Mock the create_rules_dict function
    mock_create_rules_dict = mocker.patch('app.services.rule_service.create_rules_dict')

    # Create a mock engine
    mock_engine = MagicMock()
    mock_engine.get_entity_types.return_value = ['commission', 'decommission']

    # Create an instance of the class containing get_rules
    rule_service = RuleService()
    rule_service.engine = mock_engine

    # Call get_rules with specific parameters
    entity_type = 'commission'
    provided_category = 'should'

    rule_service.get_rules(entity_type, provided_category)

    # Assert create_rules_dict was called with the correct parameters
    mock_create_rules_dict.assert_called_with(mock_engine, provided_category, [entity_type])

    # Call get_rules without parameters
    rule_service.get_rules()

    # Assert create_rules_dict was called with the correct parameters
    mock_create_rules_dict.assert_called_with(mock_engine, None, ['commission', 'decommission'])

if __name__ == '__main__':
    pytest.main()
