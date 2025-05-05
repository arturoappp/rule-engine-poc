import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import AsyncMock, MagicMock
from app.services.rule_service import RuleService
from app.api.routes.rules import get_rule_service

# Create a TestClient for the FastAPI router


@pytest.fixture
def client():
    return TestClient(app)


def test_update_rule_categories_success(client):
    """Test successful update of rule categories."""
    mock_rule_service = MagicMock()
    mock_rule_service.update_rule_categories.return_value = (
        True,
        "Categories updated successfully",
    )

    app.dependency_overrides[get_rule_service] = lambda: mock_rule_service

    request_payload = {
        "rule_name": "Test Rule",
        "entity_type": "Test Entity",
        "categories": ["Category1", "Category2"],
        "category_action": "add",
    }

    response = client.post("/api/v1/rule-categories", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["message"] == "Categories updated successfully"
    app.dependency_overrides = {}


def test_update_rule_categories_failure(client):
    """Test failure case for updating rule categories."""
    mock_rule_service = MagicMock()
    mock_rule_service.update_rule_categories.return_value = (
        False,
        "Error updating rule categories: Rule with name 'Test Rule' not found for entity type 'Test Entity'",
    )

    app.dependency_overrides[get_rule_service] = lambda: mock_rule_service

    request_payload = {
        "rule_name": "Test Rule",
        "entity_type": "Test Entity",
        "categories": ["Category1", "Category2"],
        "category_action": "add",
    }

    response = client.post("/api/v1/rule-categories", json=request_payload)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is False
    assert response_data["message"] == "Error updating rule categories: Rule with name 'Test Rule' not found for entity type 'Test Entity'"
    app.dependency_overrides = {}
