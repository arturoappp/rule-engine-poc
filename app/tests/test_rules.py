from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse
from app.api.routes.rules import get_rule_service
from main import app
import pytest

client = TestClient(app)


def test_get_rules_excludes_fields_with_none_value(mocker: MockerFixture):
    test_rule = [
        {
                "name": "Equal Rule",
                "description": "Tests the 'equal' operator",
                "conditions": {
                    "all": [
                        {
                            "path": "$.items[*].value",
                            "operator": "equal",
                            "value": 10
                        }
                    ]
                }
            }
    ]
    
    mock_service = mocker.MagicMock()  
    mock_service.get_rules.return_value = {}
    app.dependency_overrides[get_rule_service] = lambda: mock_service

    mock_format_list_rules_response = mocker.patch('app.api.routes.rules.format_list_rules_response')
    rule_list_response = RuleListResponse(entity_types=["commission_request"], categories={"commission_request": ["should_run"]}, rules={"commission_request" : {
                "should_run": test_rule
            }},
            stats = {}
            )
    mock_format_list_rules_response.return_value = rule_list_response

    response = client.get("/api/v1/rules")
    assert response.status_code == 200
    data = response.json()
    # Check that the response structure is correct
    assert "entity_types" in data
    assert "categories" in data
    assert "rules" in data
    assert "stats" in data

    # Check that the 'conditions' field does not contain None values
    rules = data["rules"]["commission_request"]["should_run"]
    for rule in rules:
        conditions = rule["conditions"]
        assert "path" not in conditions
        assert "operator" not in conditions
        assert "value" not in conditions
        assert "any" not in conditions
        assert "none" not in conditions
        assert "not" not in conditions

        # Check nested 'all' conditions
        for condition in conditions["all"]:
            assert "path" in condition
            assert "operator" in condition
            assert "value" in condition
            assert "all" not in condition
            assert "any" not in condition
            assert "none" not in condition
            assert "not" not in condition


# Define your test cases
test_cases = [
    {"entity_type": "commission", "category": "should_run"},
    {"entity_type": "decommission"},
    {"category": "could_run"},
    {},
]


@pytest.mark.parametrize("case", test_cases)
def test_list_rules(mocker: MockerFixture, case):
    
    entity_type = case.get("entity_type", None)
    category = case.get("category", None)
    request_params = {}
    if entity_type != None:
        request_params["entity_type"] = entity_type
    if category != None:
        request_params["category"] = category
    rules_by_entity = {}
    
    mock_service = mocker.MagicMock()  
    mock_service.get_rules.return_value = rules_by_entity
    mock_format_list_rules_response = mocker.patch('app.api.routes.rules.format_list_rules_response')
    rule_list_response = RuleListResponse(entity_types=[], categories={}, rules={}, stats={})
    mock_format_list_rules_response.return_value = rule_list_response
    app.dependency_overrides[get_rule_service] = lambda: mock_service
    
    response = client.get("/api/v1/rules", params=request_params)
    assert response.status_code == 200

    # Verify service.get_rules is called with the correct values
    mock_service.get_rules.assert_called_with(entity_type, category)
    mock_format_list_rules_response.assert_called_with(rules_by_entity)
    # Verify the response model
    response_data = response.json()
    assert "entity_types" in response_data
    assert "categories" in response_data
    assert "rules" in response_data

    # Reset the dependency override
    app.dependency_overrides = {}

if __name__ == "__main__":
    pytest.main()