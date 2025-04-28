

from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse, RuleStats
from app.helpers.response_formatter import format_list_rules_response


def test_format_list_rules_response_inits_response_model_with_correct_params(mocker: MockerFixture):
    mock_rule_list_response = mocker.patch('app.utilities.response_formatter.RuleListResponse', autospec=True)
    entity_types = ["entity0", "entity1"]
    categories_list = ["category0", "category1"]
    categories_dict = {
        entity_types[0] : [categories_list[0], categories_list[1]],
        entity_types[1] : [categories_list[1]],
    }
    rules = [ 
        { 
        "name": "rule0",
        "description" : "description0",
        "conditions": {}
        }, 
        { 
        "name": "rule1",
        "description" : "description1",
        "conditions": {}
        }, 
    ]
    rules_by_entity = { 
        entity_types[0] : {
            categories_list[0] : [ rules[0] ],
            categories_list[1] : [ rules[1] ],
        },
        entity_types[1]: {
            categories_list[1] : [ rules[1] ]
        }
    }
    entity0_rules_by_category = {
        categories_list[0]: 1,
        categories_list[1]: 1,
    }
    entity1_rules_by_category = {
        categories_list[1]: 1,
    }
  
    entity0_rule_stats = RuleStats(total_rules=2, rules_by_category=entity0_rules_by_category)
    entity1_rule_stats = RuleStats(total_rules=1, rules_by_category=entity1_rules_by_category)
    stats = {
        entity_types[0] : entity0_rule_stats,
        entity_types[1] : entity1_rule_stats,
    }
    result = format_list_rules_response(rules_by_entity)
    
    assert isinstance(result, RuleListResponse)
    assert mock_rule_list_response.call_args.kwargs == {'entity_types': entity_types, 'categories': categories_dict, 'rules': rules_by_entity, 'stats': stats}
