import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_rules():
    return {
        "rules": [
            {
                "name": "All Devices Must Have Management IP",
                "entity_type": "Commission Request",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].mgmtIP",
                            "operator": "exists",
                            "value": True
                        },
                        {
                            "path": "$.devices[*].vendor",
                            "operator": "equal",
                            "value": "Cisco Systems"
                        },
                        {
                            "path": "$.devices[*].mgmtIP",
                            "operator": "max_length",
                            "value": 15
                        }
                    ]
                },
                "add_to_categories": ["Could Run"]
            },
            {
                "name": "All Devices Must vendor Cisco Systems",
                "entity_type": "Commission Request",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].vendor",
                            "operator": "equal",
                            "value": "Cisco Systems"
                        }
                    ]
                },
                "add_to_categories": ["Could Run"]
            },
            {
                "name": "All Devices Must Have OS Version",
                "entity_type": "Decommission Request",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].osVersion",
                            "operator": "exists",
                            "value": True
                        }
                    ]
                },
                "add_to_categories": ["Should Run"]
            }
        ]
    }


@pytest.fixture
def invalid_rules():
    """Invalid rules for testing validation."""
    return [
        {
            "name": "Invalid Rule - Empty Conditions",
            "entity_type": "device",
            "conditions": {}
        },
        {
            "name": "Invalid Rule - Missing Operator",
            "entity_type": "device",
            "conditions": {
                "path": "$.devices[*].test",
                "value": True
            }
        },
        {
            "name": "Invalid Rule - Empty All",
            "entity_type": "device",
            "conditions": {
                "all": []
            }
        }
    ]


@pytest.fixture
def evaluation_data():
    """Evaluation request data."""
    return {
        "entity_type": "Commission Request",
        "categories": ["Could Run"],
        "data": {
            "Commission Requests": [
                {
                    "vendor": "Cisco Systems",
                    "osVersion": "17.3.6",
                    "mgmtIP": "192.168.1.1"
                },
                {
                    "vendor": "Microsoft",
                    "osVersion": "10.0.19045",
                    "mgmtIP": "10.0.0.1"
                },
                {
                    "vendor": "Cisco Systems",
                    "osVersion": "16.9.5"
                }
            ]
        }
    }


@pytest.fixture
def evaluation_data_with_rule_names():
    """Evaluation request data with rule names."""
    return {
        "entity_type": "Commission Request",
        "rule_names": ["All Devices Must Have Management IP"],
        "data": {
            "Commission Requests": [
                {
                    "vendor": "Cisco Systems",
                    "osVersion": "17.3.6",
                    "mgmtIP": "10.0.0.1"
                },
                {
                    "vendor": "Microsoft",
                    "osVersion": "10.0.19045",
                    "mgmtIP": "10.0.0.1"
                },
                {
                    "vendor": "Cisco Systems",
                    "osVersion": "16.9.5",
                    "mgmtIP": "10.0.0.11"
                }
            ]
        }
    }


# Tests for /evaluate endpoint
def test_evaluate_data_by_item_with_valid_rules_returns_success(client, valid_rules, evaluation_data):
    """Test successful evaluation by data item with valid rules."""
    # First, store the rules
    response = client.post("/api/v1/rules", json=valid_rules)
    assert response.status_code == 200

    # Then evaluate the data
    response = client.post("/api/v1/evaluate", json=evaluation_data)
    assert response.status_code == 200

    data = response.json()
    assert data["entity_type"] == "Commission Request"
    assert data["categories"] == ["Could Run"]
    assert data["total_data_objects"] == 3
    assert len(data["results"]) == 3


def test_evaluate_data_filtering_by_rule_names_returns_filtered_results(client, valid_rules,
                                                                        evaluation_data_with_rule_names):
    """Test evaluation filtering by specific rule names."""
    # Store rules
    response = client.post("/api/v1/rules", json=valid_rules)
    assert response.status_code == 200

    # Evaluate data with rule names filter
    response = client.post("/api/v1/evaluate", json=evaluation_data_with_rule_names)
    assert response.status_code == 200

    data = response.json()
    assert data["entity_type"] == "Commission Request"
    assert data["rule_names"] == ["All Devices Must Have Management IP"]
    assert data["total_rules"] == 1
    assert data["total_data_objects"] == 3

    # Check specific results
    results = data["results"]

    # First item should pass
    assert results[0]["evaluation_summary"]["rules_passed"] == 1
    assert results[0]["evaluation_summary"]["rules_failed"] == 0
    assert "All Devices Must Have Management IP" in results[0]["rules_passed"]

    # Second item should fail (vendor is Microsoft)
    assert results[1]["evaluation_summary"]["rules_passed"] == 0
    assert results[1]["evaluation_summary"]["rules_failed"] == 1
    assert len(results[1]["rules_failed"]) == 1
    assert results[1]["rules_failed"][0]["rule_name"] == "All Devices Must Have Management IP"


def test_evaluate_without_categories_or_rule_names_returns_validation_error(client):
    """Test evaluation fails without categories or rule names."""
    request_data = {
        "entity_type": "Commission Request",
        "data": {
            "Commission Requests": [
                {"vendor": "Cisco Systems", "osVersion": "17.3.6"}
            ]
        }
    }

    response = client.post("/api/v1/evaluate", json=request_data)
    assert response.status_code == 422
    assert "At least one of 'categories' or 'rule_names' must be provided" in response.json()["detail"][0]["msg"]


def test_evaluate_with_no_matching_entities_returns_empty_results(client, valid_rules):
    """Test evaluation when no entities are found in data."""
    # Store rules
    response = client.post("/api/v1/rules", json=valid_rules)
    assert response.status_code == 200

    request_data = {
        "entity_type": "Commission Request",
        "categories": ["Could Run"],
        "data": {
            "devices": []  # Wrong key, should be "Commission Requests"
        }
    }

    response = client.post("/api/v1/evaluate", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["total_data_objects"] == 0
    assert len(data["results"]) == 0


def test_evaluate_with_no_matching_rules_returns_zero_rules(client):
    """Test evaluation when no rules match the criteria."""
    request_data = {
        "entity_type": "NonExistentType",
        "categories": ["NonExistentCategory"],
        "data": {}
    }

    response = client.post("/api/v1/evaluate", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["total_rules"] == 0
    assert data["total_data_objects"] == 0
    assert len(data["results"]) == 0


def test_evaluate_with_both_categories_and_rule_names_returns_error(client, valid_rules):
    """Test that providing both categories and rule names causes an error."""
    # Store rules
    response = client.post("/api/v1/rules", json=valid_rules)
    assert response.status_code == 200

    request_data = {
        "entity_type": "Commission Request",
        "categories": ["Could Run"],
        "rule_names": ["All Devices Must Have Management IP"],
        "data": {
            "Commission Requests": [
                {"vendor": "Cisco Systems", "osVersion": "17.3.6"}
            ]
        }
    }

    response = client.post("/api/v1/evaluate", json=request_data)
    assert response.status_code == 400
    assert "Cannot filter by both categories and rule names" in response.json()["detail"]


# Tests for /evaluate/with-rules endpoint
def test_evaluate_with_rules_validates_rules_before_evaluation(client, invalid_rules):
    """Test that invalid rules are rejected before evaluation."""
    request_data = {
        "entity_type": "device",
        "rules": invalid_rules,
        "data": {
            "devices": [{"id": "device-1"}]
        }
    }

    response = client.post("/api/v1/evaluate/with-rules", json=request_data)
    assert response.status_code == 400

    error_detail = response.json()["detail"]
    assert "Validation failed" in error_detail
    assert "Invalid Rule - Empty Conditions" in error_detail
    assert "Invalid Rule - Missing Operator" in error_detail
    assert "Invalid Rule - Empty All" in error_detail


def test_evaluate_with_valid_rules_returns_success(client):
    """Test successful evaluation with valid provided rules."""
    request_data = {
        "entity_type": "device",
        "rules": [
            {
                "name": "All Devices Must Have IP",
                "entity_type": "device",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].ip",
                            "operator": "exists",
                            "value": True
                        }
                    ]
                }
            }
        ],
        "data": {
            "devices": [
                {"id": "device-1", "ip": "192.168.1.1"},
                {"id": "device-2", "ip": "192.168.1.2"},
                {"id": "device-3"}  # No IP
            ]
        }
    }

    response = client.post("/api/v1/evaluate/with-rules", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["entity_type"] == "device"
    assert data["total_rules"] == 1
    assert data["total_data_objects"] == 3
    assert len(data["results"]) == 3

    # Check specific results
    assert data["results"][0]["evaluation_summary"]["rules_passed"] == 1
    assert data["results"][1]["evaluation_summary"]["rules_passed"] == 1
    assert data["results"][2]["evaluation_summary"]["rules_failed"] == 1


def test_evaluate_with_rules_and_no_entities_returns_empty_results(client):
    """Test evaluation with valid rules when no entities found."""
    request_data = {
        "entity_type": "device",
        "rules": [
            {
                "name": "Test Rule",
                "entity_type": "device",
                "conditions": {
                    "path": "$.devices[*].test",
                    "operator": "exists",
                    "value": True
                }
            }
        ],
        "data": {
            "wrong_key": []  # Should be "devices"
        }
    }

    response = client.post("/api/v1/evaluate/with-rules", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["total_data_objects"] == 0
    assert len(data["results"]) == 0


def test_evaluate_with_complex_valid_rules_returns_correct_results(client):
    """Test evaluation with complex valid rule conditions."""
    request_data = {
        "entity_type": "Commission Request",
        "rules": [
            {
                "name": "Complex Rule",
                "entity_type": "Commission Request",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].vendor",
                            "operator": "equal",
                            "value": "Cisco Systems"
                        },
                        {
                            "any": [
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^17\\."
                                },
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^16\\."
                                }
                            ]
                        }
                    ]
                }
            }
        ],
        "data": {
            "Commission Requests": [
                {"vendor": "Cisco Systems", "osVersion": "17.3.6"},  # Pass
                {"vendor": "Cisco Systems", "osVersion": "16.9.5"},  # Pass
                {"vendor": "Cisco Systems", "osVersion": "15.2.1"},  # Fail
                {"vendor": "Juniper", "osVersion": "17.3.6"}  # Fail
            ]
        }
    }

    response = client.post("/api/v1/evaluate/with-rules", json=request_data)
    assert response.status_code == 200

    data = response.json()
    assert data["total_data_objects"] == 4

    # First two should pass
    assert data["results"][0]["evaluation_summary"]["rules_passed"] == 1
    assert data["results"][1]["evaluation_summary"]["rules_passed"] == 1

    # Last two should fail
    assert data["results"][2]["evaluation_summary"]["rules_failed"] == 1
    assert data["results"][3]["evaluation_summary"]["rules_failed"] == 1


def test_evaluate_with_mixed_valid_and_invalid_rules_fails_validation(client):
    """Test that mix of valid and invalid rules fails validation."""
    request_data = {
        "entity_type": "device",
        "rules": [
            {
                "name": "Valid Rule",
                "entity_type": "device",
                "conditions": {
                    "path": "$.devices[*].ip",
                    "operator": "exists",
                    "value": True
                }
            },
            {
                "name": "Invalid Rule",
                "entity_type": "device",
                "conditions": {}  # Invalid - empty conditions
            }
        ],
        "data": {
            "devices": [{"id": "device-1", "ip": "192.168.1.1"}]
        }
    }

    response = client.post("/api/v1/evaluate/with-rules", json=request_data)
    assert response.status_code == 400

    error_detail = response.json()["detail"]
    assert "Validation failed" in error_detail
    assert "Invalid Rule" in error_detail


# Integration tests
def test_integration_stored_rules_and_evaluate_endpoints(client, valid_rules):
    """Integration test for storing rules and then evaluating with both endpoints."""
    # Store rules
    response = client.post("/api/v1/rules", json=valid_rules)
    assert response.status_code == 200

    # Test /evaluate endpoint
    eval_request = {
        "entity_type": "Commission Request",
        "categories": ["Could Run"],
        "data": {
            "Commission Requests": [
                {"vendor": "Cisco Systems", "osVersion": "17.3.6", "mgmtIP": "10.0.0.1"},
                {"vendor": "Microsoft", "osVersion": "10.0", "mgmtIP": "10.0.0.2"}
            ]
        }
    }

    response = client.post("/api/v1/evaluate", json=eval_request)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rules"] == 2  # Two rules in "Could Run" category

    # Test /evaluate/with-rules endpoint with equivalent rules
    # This request contains only ONE rule that checks if vendor equals "Cisco Systems"
    with_rules_request = {
        "entity_type": "Commission Request",
        "rules": [
            {
                "name": "All Devices Must vendor Cisco Systems",
                "entity_type": "Commission Request",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].vendor",
                            "operator": "equal",
                            "value": "Cisco Systems"
                        }
                    ]
                }
            }
        ],
        "data": eval_request["data"]  # Same data as above: 2 items (Cisco Systems and Microsoft)
    }

    response = client.post("/api/v1/evaluate/with-rules", json=with_rules_request)
    assert response.status_code == 200
    data = response.json()

    # We're evaluating with only 1 rule (the vendor check rule)
    assert data["total_rules"] == 1

    # First item in data has vendor="Cisco Systems", so it passes the rule
    # results[0] corresponds to {"vendor": "Cisco Systems", "osVersion": "17.3.6", "mgmtIP": "10.0.0.1"}
    assert data["results"][0]["evaluation_summary"]["rules_passed"] == 1  # Passes because vendor is "Cisco Systems"

    # Second item in data has vendor="Microsoft", so it fails the rule
    # results[1] corresponds to {"vendor": "Microsoft", "osVersion": "10.0", "mgmtIP": "10.0.0.2"}
    assert data["results"][1]["evaluation_summary"][
               "rules_failed"] == 1  # Fails because vendor is "Microsoft", not "Cisco Systems"


def test_evaluate_endpoints_handle_malformed_json_gracefully(client):
    """Test that endpoints handle malformed data gracefully."""
    # Test with invalid JSON structure
    response = client.post(
        "/api/v1/evaluate",
        json={
            "entity_type": "device",
            "categories": ["test"],
            "data": "not_a_dict"  # Should be a dict
        }
    )
    assert response.status_code == 422

    # Test with missing required fields
    response = client.post(
        "/api/v1/evaluate/with-rules",
        json={
            "entity_type": "device"
            # Missing 'rules' and 'data'
        }
    )
    assert response.status_code == 422  # Validation error
