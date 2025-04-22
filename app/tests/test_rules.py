from fastapi.testclient import TestClient
from pytest_mock import MockerFixture
from app.api.routes.rules import get_rule_service
from app.main import app

client = TestClient(app)


def test_get_rules_exclude_none(self):
    response = client.get("/rules")
    assert response.status_code == 200
    data = response.json()
    # Check that the response structure is correct
    assert "entity_types" in data
    assert "categories" in data
    assert "rules" in data

    # Check that the 'conditions' field does not contain None values
    rules = data["rules"]["device"]["complex"]
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


def test_list_rules(mocker: MockerFixture):
    # Mock the RuleService
    mock_service = mocker.MagicMock()
    app.dependency_overrides[get_rule_service] = lambda: mock_service

    # Define test cases
    test_cases = [
        {"entity_type": "type1", "category": "cat1"},
        {"entity_type": "type2", "category": "cat2"},
        {"entity_type": None, "category": "cat3"},
        {"entity_type": "type3", "category": None},
        {"entity_type": None, "category": None},
    ]

    for case in test_cases:
        response = client.get("/rules", params=case)
        assert response.status_code == 200

        # Verify service.get_rules is called with the correct values
        mock_service.get_rules.assert_called_with(case["entity_type"], case["category"])

        # Verify the response model
        response_data = response.json()
        assert "entity_types" in response_data
        assert "categories" in response_data
        assert "rules" in response_data

    # Reset the dependency override
    app.dependency_overrides = {}

if __name__ == "__main__":
    import pytest
    pytest.main()