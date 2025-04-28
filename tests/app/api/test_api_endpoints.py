from fastapi.testclient import TestClient
import pytest
from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse
from app.api.routes.rules import get_rule_service
from main import app

client = TestClient(app)


class TestRuleEndpoints:
    """Integration tests for rule API endpoints"""

    def test_validate_rule_endpoint(self):
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

    def test_store_rules_endpoint(self):
        """Test the store rules endpoint"""
        # Create request data
        request_data = {
            "entity_type": "device",
            "default_category": "default",
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

    def test_list_rules_endpoint(self):
        """Test the list rules endpoint"""
        # First, store a rule
        store_data = {
            "entity_type": "device",
            "default_category": "default",
            "rules": [
                {
                    "name": "List Test Rule",
                    "description": "Test Description",
                    "conditions": {
                        "path": "$.devices[*].vendor",
                        "operator": "equal",
                        "value": "Cisco Systems"
                    },
                    "categories": ["list_test"]
                }
            ]
        }
        client.post("/api/v1/rules", json=store_data)

        # Now get the list of rules
        response = client.get("/api/v1/rules")

        # Check result
        assert response.status_code == 200
        data = response.json()
        assert "entity_types" in data
        assert "rules" in data

        # Check if our test rule is in the response
        found = False
        for entity_type, categories in data["rules"].items():
            if entity_type == "device":
                for category, rules in categories.items():
                    if category == "list_test":
                        for rule in rules:
                            if rule["name"] == "List Test Rule":
                                found = True
                                # Check that categories are correct
                                assert "categories" in rule
                                assert "list_test" in rule["categories"]

        assert found, "Added rule not found in list response"

    def test_rule_overwrite_functionality(self):
        """Test the rule overwriting functionality"""
        # First, store an initial version of a rule
        initial_data = {
            "entity_type": "NDC_Request",
            "default_category": "default",
            "rules": [
                {
                    "name": "OVERWRITE TEST RULE",
                    "description": "Initial version",
                    "conditions": {
                        "path": "$.requests[*].managementIP",
                        "operator": "exists",
                        "value": True
                    },
                    "categories": ["testCategory1", "testCategory2"]
                }
            ]
        }
        client.post("/api/v1/rules", json=initial_data)

        # Now store an updated version with the same name but in different categories
        updated_data = {
            "entity_type": "NDC_Request",
            "default_category": "default",
            "rules": [
                {
                    "name": "OVERWRITE TEST RULE",
                    "description": "Updated version",
                    "conditions": {
                        "path": "$.requests[*].managementIP",
                        "operator": "match",
                        "value": "^192\\.168\\..*$"
                    },
                    "categories": ["testCategory1", "testCategory3"]
                }
            ]
        }
        response = client.post("/api/v1/rules", json=updated_data)
        assert response.status_code == 200

        # Now get the list of rules and check if the rule was properly overwritten
        list_response = client.get("/api/v1/rules")
        data = list_response.json()

        # Check that our rule exists in all three expected categories
        categories_with_rule = set()
        rule_in_category1 = None
        rule_in_category2 = None
        rule_in_category3 = None

        for entity_type, categories in data["rules"].items():
            if entity_type == "NDC_Request":
                for category, rules in categories.items():
                    for rule in rules:
                        if rule["name"] == "OVERWRITE TEST RULE":
                            categories_with_rule.add(category)

                            if category == "testCategory1":
                                rule_in_category1 = rule
                            elif category == "testCategory2":
                                rule_in_category2 = rule
                            elif category == "testCategory3":
                                rule_in_category3 = rule

        # Verify the rule appears in all expected categories
        assert "testCategory1" in categories_with_rule, "Rule should be in testCategory1"
        assert "testCategory2" in categories_with_rule, "Rule should still be in testCategory2"
        assert "testCategory3" in categories_with_rule, "Rule should be added to testCategory3"

        # Verify the rule in testCategory1 and testCategory3 has been updated
        assert rule_in_category1 is not None
        assert rule_in_category1["description"] == "Updated version"
        assert rule_in_category1["conditions"]["operator"] == "match"
        assert rule_in_category1["conditions"]["value"] == "^192\\.168\\..*$"

        # Verify the rule in testCategory3 is the updated version
        assert rule_in_category3 is not None
        assert rule_in_category3["description"] == "Updated version"
        assert rule_in_category3["conditions"]["operator"] == "match"
        assert rule_in_category3["conditions"]["value"] == "^192\\.168\\..*$"

        # Verify the rule in testCategory2 is still the original version
        assert rule_in_category2 is not None
        assert rule_in_category2["description"] == "Initial version"
        assert rule_in_category2["conditions"]["operator"] == "exists"
        assert rule_in_category2["conditions"]["value"] is True


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