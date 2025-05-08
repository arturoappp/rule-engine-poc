from fastapi.testclient import TestClient
import pytest
from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse, RuleListResponse
from app.api.routes.rules import get_rule_service
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_validate_rule_endpoint(client):
    """Test the rule validation endpoint"""
    # Create a valid rule
    rule = {
        "name": "Test Rule",
        "description": "Test Description",
        "conditions": {
            "path": "$.devices[*].vendor",
            "operator": "equal",
            "value": "Cisco Systems"
        },
        "categories": ["test"]
    }

    # Call the endpoint
    response = client.post("/api/v1/rules/validate", json=rule)

    # Check result
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["errors"] is None


def test_store_rules_endpoint(client):
    """Test the store rules endpoint"""
    # Create request data
    request_data = {
        "entity_type": "device",
        "rules": [
            {
                "name": "API Test Rule",
                "description": "Test Description",
                "conditions": {
                    "path": "$.devices[*].vendor",
                    "operator": "equal",
                    "value": "Cisco Systems"
                },
                "categories": ["test_category"]
            }
        ]
    }

    # Call the endpoint
    response = client.post("/api/v1/rules", json=request_data)

    # Check result
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["stored_rules"] == 1

# TODO: Update since


def test_list_rules_endpoint(client):
    """Test the list rules endpoint"""
    # Save a rule
    store_data = {
        "entity_type": "device",
        "rules": [
            {
                "name": "List Test Rule",
                "description": "Test Description",
                "conditions": {
                    "path": "$.devices[*].vendor",
                    "operator": "equal",
                    "value": "Cisco Systems"
                },
                "add_to_categories": ["default"]
            }
        ]
    }
    client.post("/api/v1/rules", json=store_data)

    # Now get the list of rules
    response = client.get("/api/v1/rules")

    # Verify result
    assert response.status_code == 200
    data = response.json()
    assert "entity_types" in data
    assert "rules" in data

    # Verify if our rule is in the response
    found = False
    for entity_type, categories in data["rules"].items():
        if entity_type == "device":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "List Test Rule":
                        found = True

    assert found, "Added rule not found in list response"


def test_rule_overwrite_functionality(client, mocker: MockerFixture):
    """Test the rule overwriting functionality"""
    # Prepare initial data
    initial_data = {
        "entity_type": "NDC_Request",
        "rules": [
            {
                "name": "OVERWRITE TEST RULE",
                "entity_type": "NDC_Request",
                "description": "Initial version",
                "conditions": {
                    "path": "$.requests[*].managementIP",
                    "operator": "exists",
                    "value": True
                },
                "add_to_categories": ["default"]
            }
        ]
    }
    client.post("/api/v1/rules", json=initial_data)

    # Now save an updated version with the same name
    updated_data = {
        "entity_type": "NDC_Request",
        "rules": [
            {
                "name": "OVERWRITE TEST RULE",
                "entity_type": "NDC_Request",
                "description": "Updated version",
                "conditions": {
                    "path": "$.requests[*].managementIP",
                    "operator": "match",
                    "value": "^192\\.168\\..*$"
                },
                "add_to_categories": ["default"]  # Use the same category to verify overwriting
            }
        ]
    }
    response = client.post("/api/v1/rules", json=updated_data)
    assert response.status_code == 200

    # Get the list of rules and verify if the rule was correctly overwritten
    list_response = client.get("/api/v1/rules")
    data = list_response.json()

    # Look for the rule in categories
    rule_found = None

    # Search in all entities and categories
    for entity_type, categories in data["rules"].items():
        if entity_type == "NDC_Request":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "OVERWRITE TEST RULE":
                        if rule["description"] == "Updated version":
                            rule_found = rule

    # Verify the rule exists and has been updated
    assert rule_found is not None, "Rule not found in default category"
    assert rule_found["description"] == "Updated version"
    assert rule_found["conditions"]["operator"] == "match"
    assert rule_found["conditions"]["value"] == "^192\\.168\\..*$"

    test_rule = [
        {
            "name": "Equal Rule",
            "entity_type": "commission_request",
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
    rule_list_response = RuleListResponse(entity_types=["commission_request"],
                                          categories={"commission_request": ["should_run"]},
                                          rules={"commission_request": {
                                              "should_run": test_rule
                                          }},
                                          stats={}
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


def test_get_rules_excludes_fields_with_none_value(client, mocker: MockerFixture):
    test_rule = [
        {
            "name": "Equal Rule",
            "entity_type": "commission_request",
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

    mock_spike_format_list_rules_response = mocker.patch('app.api.routes.rules.format_list_rules_response')
    rule_list_response = RuleListResponse(entity_types=["commission_request"],
                                          categories={"commission_request": ["should_run"]},
                                          rules={"commission_request": {
                                              "should_run": test_rule
                                          }},
                                          stats={}
                                          )
    mock_spike_format_list_rules_response.return_value = rule_list_response

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


test_cases = [
    {"entity_type": "commission", "categories": ["should_run"]},
    {"entity_type": "decommission"},
    {"category": "could_run"},
    {},
]


@pytest.mark.parametrize("case", test_cases)
def test_list_rules(mocker: MockerFixture, case, client):
    entity_type = case.get("entity_type", None)
    categories = case.get("categories", None)
    request_params = {}
    if entity_type is not None:
        request_params["entity_type"] = entity_type
    if categories is not None:
        request_params["categories"] = categories
    rules_by_entity = {}

    mock_service = mocker.MagicMock()
    mock_service.get_rules.return_value = rules_by_entity
    mock_spike_format_list_rules_response = mocker.patch('app.api.routes.rules.format_list_rules_response')
    rule_list_response = RuleListResponse(entity_types=[], categories={}, rules={}, stats={})
    mock_spike_format_list_rules_response.return_value = rule_list_response
    app.dependency_overrides[get_rule_service] = lambda: mock_service

    response = client.get("/api/v1/rules", params=request_params)
    assert response.status_code == 200

    # Verify service.get_rules is called with the correct values
    mock_service.get_rules.assert_called_with(entity_type, categories)
    mock_spike_format_list_rules_response.assert_called_with(rules_by_entity)
    # Verify the response model
    response_data = response.json()
    assert "entity_types" in response_data
    assert "categories" in response_data
    assert "rules" in response_data

    # Reset the dependency override
    app.dependency_overrides = {}
