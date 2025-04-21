from fastapi.testclient import TestClient
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

        # Now store an updated version with the same name
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

        # Look for our rule in each category
        categories_found = []
        description = None

        for entity_type, categories in data["rules"].items():
            if entity_type == "NDC_Request":
                for category, rules in categories.items():
                    for rule in rules:
                        if rule["name"] == "OVERWRITE TEST RULE":
                            categories_found.append(category)
                            description = rule["description"]

                            # Check the rule's own categories list
                            assert "categories" in rule
                            assert set(rule["categories"]) == set(["testCategory1", "testCategory3"])

        # Verify the rule appears in the expected categories
        assert set(categories_found) == set(["testCategory1", "testCategory3"])
        assert "testCategory2" not in categories_found
        assert description == "Updated version"