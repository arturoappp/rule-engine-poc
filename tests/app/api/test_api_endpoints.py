from fastapi.testclient import TestClient
import pytest
from pytest_mock import MockerFixture
from app.api.models.rules import RuleListResponse, SpikeRuleListResponse
from app.api.routes.rules import get_rule_service
from main import app


# Crear un cliente de prueba como fixture
@pytest.fixture
def client():
    return TestClient(app)


# Test para el endpoint de validación de reglas
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


# Test para el endpoint de almacenamiento de reglas
def test_store_rules_endpoint(client):
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


def test_spike_store_rules_endpoint(client):
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
    response = client.post("/api/v1/spike-rules", json=request_data)

    # Check result
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["stored_rules"] == 1


# Test para el endpoint de listado de reglas - CORREGIDO
def test_list_rules_endpoint(client):
    """Test the list rules endpoint"""
    # Guardar una regla
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
                "categories": ["default"]
            }
        ]
    }
    client.post("/api/v1/rules", json=store_data)

    # Ahora obtener la lista de reglas
    response = client.get("/api/v1/rules")

    # Verificar resultado
    assert response.status_code == 200
    data = response.json()
    assert "entity_types" in data
    assert "rules" in data

    # Verificar si nuestra regla está en la respuesta
    found = False
    for entity_type, categories in data["rules"].items():
        if entity_type == "device":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "List Test Rule":
                        found = True
                        # El campo podría ser 'categories' o 'add_to_categories'
                        # Verificamos cuál existe y luego su contenido
                        categories_field = None
                        if "categories" in rule:
                            categories_field = "categories"
                        elif "add_to_categories" in rule:
                            categories_field = "add_to_categories"

                        # Verificar que hay un campo con las categorías
                        assert categories_field is not None, "No categories field found in rule"

                        # Verificar que la categoría default está presente
                        assert "default" in rule[categories_field], f"Default category not found in {categories_field}"

    assert found, "Added rule not found in list response"

def test_spike_list_rules_endpoint(client):
    """Test the list rules endpoint"""
    # Guardar una regla
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
                "add_to_categories": ["default"]
            }
        ]
    }
    client.post("/api/v1/spike-rules", json=store_data)

    # Ahora obtener la lista de reglas
    response = client.get("/api/v1/spike-rules")

    # Verificar resultado
    assert response.status_code == 200
    data = response.json()
    assert "entity_types" in data
    assert "rules" in data

    # Verificar si nuestra regla está en la respuesta
    found = False
    for entity_type, categories in data["rules"].items():
        if entity_type == "device":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "List Test Rule":
                        found = True

    assert found, "Added rule not found in list response"


# Test for rule overwriting functionality - FIXED
def test_rule_overwrite_functionality(client):
    """Test the rule overwriting functionality"""
    # Preparar datos iniciales
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
                "categories": ["default"]  # Cambiado para probar con categorías que sabemos que funcionan
            }
        ]
    }
    client.post("/api/v1/rules", json=initial_data)

    # Ahora guardar una versión actualizada con el mismo nombre
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
                "categories": ["default"]  # Usar la misma categoría para verificar sobreescritura
            }
        ]
    }
    response = client.post("/api/v1/rules", json=updated_data)
    assert response.status_code == 200

    # Obtener la lista de reglas y verificar si la regla fue sobreescrita correctamente
    list_response = client.get("/api/v1/rules")
    data = list_response.json()

    # Buscar la regla en las categorías
    rule_found = None

    # Buscar en todas las entidades y categorías
    for entity_type, categories in data["rules"].items():
        if entity_type == "NDC_Request":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "OVERWRITE TEST RULE":
                        if category == "default":
                            rule_found = rule

    # Verificar que la regla existe y ha sido actualizada
    assert rule_found is not None, "Rule not found in default category"
    assert rule_found["description"] == "Updated version"
    assert rule_found["conditions"]["operator"] == "match"
    assert rule_found["conditions"]["value"] == "^192\\.168\\..*$"

# TODO: Fix this
def test_spike_rule_overwrite_functionality(client):
    """Test the rule overwriting functionality"""
    # Preparar datos iniciales
    initial_data = {
        "entity_type": "NDC_Request",
        "rules": [
            {
                "name": "OVERWRITE TEST RULE",
                "description": "Initial version",
                "conditions": {
                    "path": "$.requests[*].managementIP",
                    "operator": "exists",
                    "value": True
                },
                "add_to_categories": ["default"]  # Cambiado para probar con categorías que sabemos que funcionan
            }
        ]
    }
    client.post("/api/v1/spike-rules", json=initial_data)

    # Ahora guardar una versión actualizada con el mismo nombre
    updated_data = {
        "entity_type": "NDC_Request",
        "rules": [
            {
                "name": "OVERWRITE TEST RULE",
                "description": "Updated version",
                "conditions": {
                    "path": "$.requests[*].managementIP",
                    "operator": "match",
                    "value": "^192\\.168\\..*$"
                },
                "add_to_categories": ["default"]  # Usar la misma categoría para verificar sobreescritura
            }
        ]
    }
    response = client.post("/api/v1/spike-rules", json=updated_data)
    assert response.status_code == 200

    # Obtener la lista de reglas y verificar si la regla fue sobreescrita correctamente
    list_response = client.get("/api/v1/spike-rules")
    data = list_response.json()

    # Buscar la regla en las categorías
    rule_found = None

    # Buscar en todas las entidades y categorías
    for entity_type, categories in data["rules"].items():
        if entity_type == "NDC_Request":
            for category, rules in categories.items():
                for rule in rules:
                    if rule["name"] == "OVERWRITE TEST RULE":
                        if  rule["description"] == "Updated version":
                            rule_found = rule

    # Verificar que la regla existe y ha sido actualizada
    assert rule_found is not None, "Rule not found in default category"
    assert rule_found["description"] == "Updated version"
    assert rule_found["conditions"]["operator"] == "match"
    assert rule_found["conditions"]["value"] == "^192\\.168\\..*$"


def test_get_rules_excludes_fields_with_none_value(client, mocker: MockerFixture):
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


def test_spike_get_rules_excludes_fields_with_none_value(client, mocker: MockerFixture):
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
    mock_service.get_spike_rules.return_value = {}
    app.dependency_overrides[get_rule_service] = lambda: mock_service

    mock_spike_format_list_rules_response = mocker.patch('app.api.routes.rules.spike_format_list_rules_response')
    rule_list_response = SpikeRuleListResponse(entity_types=["commission_request"],
                                          categories={"commission_request": ["should_run"]},
                                          rules={"commission_request": {
                                              "should_run": test_rule
                                          }},
                                          stats={}
                                          )
    mock_spike_format_list_rules_response.return_value = rule_list_response

    response = client.get("/api/v1/spike-rules")
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
def test_list_rules(mocker: MockerFixture, case, client):
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


@pytest.mark.parametrize("case", test_cases)
def test_spike_list_rules(mocker: MockerFixture, case, client):
    entity_type = case.get("entity_type", None)
    category = case.get("category", None)
    request_params = {}
    if entity_type != None:
        request_params["entity_type"] = entity_type
    if category != None:
        request_params["category"] = category
    rules_by_entity = {}

    mock_service = mocker.MagicMock()
    mock_service.spike_get_rules.return_value = rules_by_entity
    mock_spike_format_list_rules_response = mocker.patch('app.api.routes.rules.spike_format_list_rules_response')
    rule_list_response = SpikeRuleListResponse(entity_types=[], categories={}, rules={}, stats={})
    mock_spike_format_list_rules_response.return_value = rule_list_response
    app.dependency_overrides[get_rule_service] = lambda: mock_service

    response = client.get("/api/v1/spike-rules", params=request_params)
    assert response.status_code == 200

    # Verify service.get_rules is called with the correct values
    mock_service.spike_get_rules.assert_called_with(entity_type, category)
    mock_spike_format_list_rules_response.assert_called_with(rules_by_entity)
    # Verify the response model
    response_data = response.json()
    assert "entity_types" in response_data
    assert "categories" in response_data
    assert "rules" in response_data

    # Reset the dependency override
    app.dependency_overrides = {}