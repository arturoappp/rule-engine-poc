import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock
from app.api.routes.rule_categories import router
from app.services.rule_service import RuleService

# Create a TestClient for the FastAPI router
client = TestClient(router)


@pytest.fixture
def mock_rule_service():
    """Fixture to mock RuleService."""
    service = MagicMock(spec=RuleService)
    service.update_rule_categories = AsyncMock(return_value=(True, "Categories updated successfully"))
    return service


@pytest.fixture
def mock_get_rule_service(mock_rule_service):
    """Fixture to mock the dependency injection of RuleService."""
    return lambda: mock_rule_service


def test_update_rule_categories_success(mock_get_rule_service, monkeypatch):
    """Test successful update of rule categories."""
    # Explicitly configure the mock to simulate success
    mock_rule_service = mock_get_rule_service()
    mock_rule_service.update_rule_categories.return_value = (
        True,
        "Categories updated successfully",
    )
    monkeypatch.setattr("app.api.routes.rule_categories.get_rule_service", lambda: mock_rule_service)

    # Define the request payload
    request_payload = {
        "rule_name": "Test Rule",
        "entity_type": "Test Entity",
        "categories": ["Category1", "Category2"],
        "category_action": "add",
    }

    # Send the POST request
    response = client.post("/rule-categories", json=request_payload)

    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["message"] == "Categories updated successfully"


def test_update_rule_categories_failure(mock_get_rule_service, monkeypatch):
    """Test failure case for updating rule categories."""
    # Mock the dependency to simulate failure
    mock_get_rule_service().update_rule_categories.return_value = (
        False,
        "Error updating rule categories: Rule with name 'Test Rule' not found for entity type 'Test Entity'",
    )
    monkeypatch.setattr("app.api.routes.rule_categories.get_rule_service", mock_get_rule_service)

    # Define the request payload
    request_payload = {
        "rule_name": "Test Rule",
        "entity_type": "Test Entity",
        "categories": ["Category1", "Category2"],
        "category_action": "add",
    }

    # Send the POST request
    response = client.post("/rule-categories", json=request_payload)

    # Assert the response
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["message"] == "Error updating rule categories: Rule with name 'Test Rule' not found for entity type 'Test Entity'"
