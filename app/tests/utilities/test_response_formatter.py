

from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse
from app.utilities.response_formatter import format_list_rules_response


def test_format_list_rules_response_inits_response_model_with_correct_params(mocker: MockerFixture):
    mock_rule_list_response = mocker.patch('app.utilities.response_formatter.RuleListResponse')
    entity_types = ["entity1", "entity1"]
    categories_list = ["category0", "category1"]
    categories_dict = {
        categories_list[0] : 
    }
    rules = [ { "rule0": {}, "rule1": {}}]
    rules_by_entity = { 
        entity_types[0] : {
            categories_list[0] : [ rules[0] ],
            categories_list[1] : [ rules[1] ],
        },
        entity_types[1]: {
            categories_list[1] : [ rules[1] ]
        }
    }
    
    result = format_list_rules_response(rules_by_entity)
    
    assert isinstance(result, RuleListResponse)
    mock_rule_list_response.assert_called_with(entity_types, )
    
