"""
Unit tests for the /evaluate and /evaluate/with-rules endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def case_mock_rules():
    """case_mock rules for testing."""
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
                            "operator": "exact_length",
                            "value": 8
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
def case_mock_evaluation_data():
    """case_mock evaluation request data."""
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
def case_mock_evaluation_data_with_rule_names():
    """case_mock evaluation request data with rule names."""
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
                    "vendor": "Cisco Systems4",
                    "osVersion": "16.9.5",
                    "mgmtIP": "10.0.0.11"
                }
            ]
        }
    }


class TestEvaluateDataByItem:
    """Tests for the /evaluate endpoint."""

    def test_evaluate_data_by_item_success(self, client, case_mock_rules, case_mock_evaluation_data):
        """Test successful evaluation by data item."""
        # First, store the rules
        response = client.post("/api/v1/rules", json=case_mock_rules)
        assert response.status_code == 200

        # Then evaluate the data
        response = client.post("/api/v1/evaluate", json=case_mock_evaluation_data)
        assert response.status_code == 200

        data = response.json()
        assert data["entity_type"] == "Commission Request"
        assert data["categories"] == ["Could Run"]
        assert data["total_data_objects"] == 3
        assert len(data["results"]) == 3

    def test_evaluate_data_by_rule_names(self, client, case_mock_rules, case_mock_evaluation_data_with_rule_names):
        """Test evaluation filtering by rule names."""
        # Store rules
        response = client.post("/api/v1/rules", json=case_mock_rules)
        assert response.status_code == 200

        # Evaluate data with rule names filter
        response = client.post("/api/v1/evaluate", json=case_mock_evaluation_data_with_rule_names)
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

        # Third item should fail (vendor and length issues)
        assert results[2]["evaluation_summary"]["rules_passed"] == 0
        assert results[2]["evaluation_summary"]["rules_failed"] == 1

    def test_evaluate_missing_filtering_criteria(self, client):
        """Test evaluation without categories or rule names."""
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

    def test_evaluate_no_entities_found(self, client, case_mock_rules):
        """Test evaluation when no entities are found in data."""
        # Store rules
        response = client.post("/api/v1/rules", json=case_mock_rules)
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

    def test_evaluate_no_matching_rules(self, client):
        """Test evaluation when no rules match the criteria."""
        request_data = {
            "entity_type": "NonExistentType",
            "categories": ["NonExistentCategory"],
            "data": {

            }
        }

        response = client.post("/api/v1/evaluate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["total_rules"] == 0
        assert data["total_data_objects"] == 0
        assert len(data["results"]) == 0

    def test_evaluate_with_both_categories_and_rule_names(self, client, case_mock_rules):
        """Test that providing both categories and rule names causes an error."""
        # Store rules
        response = client.post("/api/v1/rules", json=case_mock_rules)
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


class TestEvaluateWithRulesByData:
    """Tests for the /evaluate/with-rules endpoint."""

    def test_evaluate_with_rules_success(self, client):
        """Test successful evaluation with provided rules."""
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

    def test_evaluate_with_rules_no_entities(self, client):
        """Test evaluation with rules when no entities found."""
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

    def test_evaluate_with_rules_complex_conditions(self, client):
        """Test evaluation with complex rule conditions."""
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

    def test_evaluate_with_invalid_rule_format(self, client):
        """Test evaluation with invalid rule format."""
        request_data = {
            "entity_type": "device",
            "rules": [
                {
                    "name": "Invalid Rule",
                    "entity_type": "device",
                    "conditions": {}  # Empty conditions
                }
            ],
            "data": {
                "devices": [{"id": "device-1"}]
            }
        }

        response = client.post("/api/v1/evaluate/with-rules", json=request_data)
        assert response.status_code == 200

        # The evaluation should handle the invalid rule gracefully
        data = response.json()
        assert data["total_rules"] == 1
        assert data["total_data_objects"] == 1


def test_integration_evaluate_endpoints(client, case_mock_rules):
    """Integration test for both evaluate endpoints."""
    # Store rules
    response = client.post("/api/v1/rules", json=case_mock_rules)
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

    # Test /evaluate/with-rules endpoint with the same rules
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
        "data": eval_request["data"]
    }

    response = client.post("/api/v1/evaluate/with-rules", json=with_rules_request)
    assert response.status_code == 200
    data = response.json()
    assert data["total_rules"] == 1
    assert data["results"][0]["evaluation_summary"]["rules_passed"] == 1  # Cisco Systems passes
    assert data["results"][1]["evaluation_summary"]["rules_failed"] == 1  # Microsoft fails