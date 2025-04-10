"""
Demo for NDC Rules - Testing various scenarios for commission and decommission requests
"""

import json
import logging

from rule_engine.core.engine import RuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Create rule engine
    engine = RuleEngine()

    # Rule #1: SHOULD RUN CMDB TASK (Commission)
    COMMISSION_SHOULD_RUN_RULE = """
    [
        {
            "name": "SHOULD RUN CMDB TASK",
            "description": "Checks if a CMDB task should be run for NDC Commission Request",
            "conditions": {
                "all": [
                    {
                        "path": "$.requests[*].fqdn",
                        "operator": "exists",
                        "value": true
                    }
                ]
            }
        }
    ]
    """
    engine.load_rules_from_json(COMMISSION_SHOULD_RUN_RULE, entity_type="request", category="SHOULD NDC COMMISSION REQUEST")

    # Rule #2: SHOULD RUN CMDB TASK (Decommission)
    DECOMMISSION_SHOULD_RUN_RULE = """
    [
        {
            "name": "SHOULD RUN CMDB TASK",
            "description": "Checks if a CMDB task should be run for NDC Decommission Request",
            "conditions": {
                "all": [
                    {
                        "path": "$.requests[*].fqdn",
                        "operator": "exists",
                        "value": true
                    }
                ]
            }
        }
    ]
    """
    engine.load_rules_from_json(DECOMMISSION_SHOULD_RUN_RULE, entity_type="request", category="SHOULD NDC DECOMMISSION REQUEST")

    # Rule #3: CAN RUN CMDB NDC COMMISSION REQUEST
    COMMISSION_CAN_RUN_RULE = """
    [
        {
            "name": "CAN RUN CMDB NDC COMMISSION REQUEST",
            "description": "Validates if a CMDB NDC commission request meets all required criteria",
            "conditions": {
                "all": [
                    {
                        "path": "$.requests[*].fqdn",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "all": [
                            {
                                "path": "$.requests[*].functionCode",
                                "operator": "exists",
                                "value": true
                            },
                            {
                                "path": "$.requests[*].functionCode",
                                "operator": "exact_length",
                                "value": 3
                            }
                        ]
                    },
                    {
                        "all": [
                            {
                                "path": "$.requests[*].subFunctionCode",
                                "operator": "exists",
                                "value": true
                            },
                            {
                                "path": "$.requests[*].subFunctionCode",
                                "operator": "exact_length",
                                "value": 3
                            }
                        ]
                    },
                    {
                        "all": [
                            {
                                "path": "$.requests[*].sequenceNumber",
                                "operator": "exists",
                                "value": true
                            },
                            {
                                "path": "$.requests[*].sequenceNumber",
                                "operator": "exact_length",
                                "value": 3
                            }
                        ]
                    },
                    {
                        "path": "$.requests[*].managementIP",
                        "operator": "match",
                        "value": "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    },
                    {
                        "path": "$.requests[*].l1Technician",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].l1TechnicianGroup",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].isVirtual",
                        "operator": "equal",
                        "value": false
                    },
                    {
                        "any": [
                            {
                                "path": "$.requests[*].serialNumber",
                                "operator": "exists",
                                "value": false
                            },
                            {
                                "path": "$.requests[*].serialNumber",
                                "operator": "max_length",
                                "value": 20
                            }
                        ]
                    },
                    {
                        "path": "$.requests[*].country",
                        "operator": "exact_length",
                        "value": 2
                    },
                    {
                        "path": "$.requests[*].siteCode",
                        "operator": "exact_length",
                        "value": 3
                    },
                    {
                        "any": [
                            {
                                "path": "$.requests[*].buildingCode",
                                "operator": "exists",
                                "value": false
                            },
                            {
                                "path": "$.requests[*].buildingCode",
                                "operator": "max_length",
                                "value": 5
                            }
                        ]
                    },
                    {
                        "path": "$.requests[*].osVersion",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].hardwareModel",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].capability",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].vendor",
                        "operator": "exists",
                        "value": true
                    }
                ]
            }
        }
    ]
    """
    engine.load_rules_from_json(COMMISSION_CAN_RUN_RULE, entity_type="request", category="CAN NDC COMMISSION REQUEST")

    # Rule #4: CAN RUN CMDB NDC DECOMMISSION REQUEST
    DECOMMISSION_CAN_RUN_RULE = """
    [
        {
            "name": "CAN RUN CMDB NDC DECOMMISSION REQUEST",
            "description": "Validates if a CMDB NDC decommission request meets all required criteria",
            "conditions": {
                "all": [
                    {
                        "path": "$.requests[*].fqdn",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].managementIP",
                        "operator": "match",
                        "value": "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
                    },
                    {
                        "path": "$.requests[*].l1Technician",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "path": "$.requests[*].l1TechnicianGroup",
                        "operator": "exists",
                        "value": true
                    },
                    {
                        "any": [
                            {
                                "path": "$.requests[*].serialNumber",
                                "operator": "exists",
                                "value": false
                            },
                            {
                                "path": "$.requests[*].serialNumber",
                                "operator": "max_length",
                                "value": 20
                            }
                        ]
                    }
                ]
            }
        }
    ]
    """
    engine.load_rules_from_json(DECOMMISSION_CAN_RUN_RULE, entity_type="request", category="CAN NDC DECOMMISSION REQUEST")

    # Test data for Rule #1: SHOULD RUN CMDB TASK (Commission)
    print("\n=== Test Data for SHOULD RUN CMDB TASK (Commission) ===")

    # Scenario 1: FQDN exists - should pass
    commission_should_run_data_1 = {
        "requests": [
            {
                "id": "REQ-001",
                "fqdn": "server01.example.com",
                "type": "commission"
            }
        ]
    }

    print("\nScenario 1: FQDN exists - should pass")
    results = engine.evaluate_data(commission_should_run_data_1, entity_type="request", categories=["SHOULD NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 2: FQDN missing - should fail
    commission_should_run_data_2 = {
        "requests": [
            {
                "id": "REQ-002",
                "type": "commission"
            }
        ]
    }

    print("\nScenario 2: FQDN missing - should fail")
    results = engine.evaluate_data(commission_should_run_data_2, entity_type="request",  categories=["SHOULD NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Test data for Rule #2: SHOULD RUN CMDB TASK (Decommission)
    print("\n=== Test Data for SHOULD RUN CMDB TASK (Decommission) ===")

    # Scenario 1: FQDN exists - should pass
    decommission_should_run_data_1 = {
        "requests": [
            {
                "id": "REQ-003",
                "fqdn": "server02.example.com",
                "type": "decommission"
            }
        ]
    }

    print("\nScenario 1: FQDN exists - should pass")
    results = engine.evaluate_data(decommission_should_run_data_1, entity_type="request", categories=["SHOULD NDC DECOMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 2: FQDN missing - should fail
    decommission_should_run_data_2 = {
        "requests": [
            {
                "id": "REQ-004",
                "type": "decommission"
            }
        ]
    }

    print("\nScenario 2: FQDN missing - should fail")
    results = engine.evaluate_data(decommission_should_run_data_2, entity_type="request", categories= ["SHOULD NDC DECOMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Test data for Rule #3: CAN RUN CMDB NDC COMMISSION REQUEST
    print("\n=== Test Data for CAN RUN CMDB NDC COMMISSION REQUEST ===")

    # Scenario 1: All criteria met - should pass
    commission_can_run_data_1 = {
        "requests": [
            {
                "id": "REQ-005",
                "fqdn": "server03.example.com",
                "functionCode": "SRV",
                "subFunctionCode": "APP",
                "sequenceNumber": "001",
                "managementIP": "192.168.1.1",
                "l1Technician": "John Doe",
                "l1TechnicianGroup": "Network Support",
                "isVirtual": False,
                "serialNumber": "SN12345678",
                "country": "US",
                "siteCode": "NYC",
                "buildingCode": "B001",
                "osVersion": "Windows Server 2019",
                "hardwareModel": "Dell PowerEdge R740",
                "capability": "Application Server",
                "vendor": "Dell"
            }
        ]
    }

    print("\nScenario 1: All criteria met - should pass")
    results = engine.evaluate_data(commission_can_run_data_1, entity_type="request", categories=["CAN NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 2: Missing some required fields - should fail
    commission_can_run_data_2 = {
        "requests": [
            {
                "id": "REQ-006",
                "fqdn": "server04.example.com",
                "functionCode": "SRV",
                "subFunctionCode": "APP",
                "sequenceNumber": "001",
                "managementIP": "192.168.1.2",
                "l1Technician": "Jane Smith",
                # Missing l1TechnicianGroup
                "isVirtual": False,
                "serialNumber": "SN87654321",
                "country": "US",
                "siteCode": "LAX",
                # Missing osVersion
                "hardwareModel": "Dell PowerEdge R740",
                "capability": "Database Server",
                "vendor": "Dell"
            }
        ]
    }

    print("\nScenario 2: Missing some required fields - should fail")
    results = engine.evaluate_data(commission_can_run_data_2, entity_type="request",  categories= ["CAN NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 3: Invalid field formats - should fail
    commission_can_run_data_3 = {
        "requests": [
            {
                "id": "REQ-007",
                "fqdn": "server05.example.com",
                "functionCode": "SERV",  # Too long (4 chars instead of 3)
                "subFunctionCode": "AP",  # Too short (2 chars instead of 3)
                "sequenceNumber": "0001",  # Too long (4 chars instead of 3)
                "managementIP": "192.168.1.256",  # Invalid IP
                "l1Technician": "Mike Johnson",
                "l1TechnicianGroup": "Server Support",
                "isVirtual": True,  # Should be False
                "serialNumber": "SN1234567890123456789012345",  # Too long (>20)
                "country": "USA",  # Too long (3 chars instead of 2)
                "siteCode": "NYCC",  # Too long (4 chars instead of 3)
                "buildingCode": "B00001",  # Too long (6 chars instead of max 5)
                "osVersion": "Windows Server 2019",
                "hardwareModel": "Dell PowerEdge R740",
                "capability": "Application Server",
                "vendor": "Dell"
            }
        ]
    }

    print("\nScenario 3: Invalid field formats - should fail")
    results = engine.evaluate_data(commission_can_run_data_3, entity_type="request", categories= ["CAN NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 4: No serialNumber - should still pass
    commission_can_run_data_4 = {
        "requests": [
            {
                "id": "REQ-008",
                "fqdn": "server06.example.com",
                "functionCode": "SRV",
                "subFunctionCode": "APP",
                "sequenceNumber": "001",
                "managementIP": "192.168.1.3",
                "l1Technician": "Sara Miller",
                "l1TechnicianGroup": "Network Support",
                "isVirtual": False,
                # No serialNumber - should pass due to any condition
                "country": "UK",
                "siteCode": "LON",
                "buildingCode": "B002",
                "osVersion": "Windows Server 2019",
                "hardwareModel": "Dell PowerEdge R740",
                "capability": "Application Server",
                "vendor": "Dell"
            }
        ]
    }

    print("\nScenario 4: No serialNumber - should still pass")
    results = engine.evaluate_data(commission_can_run_data_4, entity_type="request", categories= ["CAN NDC COMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Test data for Rule #4: CAN RUN CMDB NDC DECOMMISSION REQUEST
    print("\n=== Test Data for CAN RUN CMDB NDC DECOMMISSION REQUEST ===")

    # Scenario 1: All criteria met - should pass
    decommission_can_run_data_1 = {
        "requests": [
            {
                "id": "REQ-009",
                "fqdn": "server07.example.com",
                "managementIP": "192.168.1.4",
                "l1Technician": "Robert Brown",
                "l1TechnicianGroup": "Server Support",
                "serialNumber": "SN98765432"
            }
        ]
    }

    print("\nScenario 1: All criteria met - should pass")
    results = engine.evaluate_data(decommission_can_run_data_1, entity_type="request", categories = ["CAN NDC DECOMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 2: Missing required fields - should fail
    decommission_can_run_data_2 = {
        "requests": [
            {
                "id": "REQ-010",
                "fqdn": "server08.example.com",
                "managementIP": "192.168.1.5",
                # Missing l1Technician
                "l1TechnicianGroup": "Server Support",
                "serialNumber": "SN12345678"
            }
        ]
    }

    print("\nScenario 2: Missing required fields - should fail")
    results = engine.evaluate_data(decommission_can_run_data_2, entity_type="request", categories= ["CAN NDC DECOMMISSION REQUEST" ])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 3: Invalid IP and too long serialNumber - should fail
    decommission_can_run_data_3 = {
        "requests": [
            {
                "id": "REQ-011",
                "fqdn": "server09.example.com",
                "managementIP": "300.168.1.5",  # Invalid IP
                "l1Technician": "Alice Wilson",
                "l1TechnicianGroup": "Network Support",
                "serialNumber": "SN123456789012345678901234567890"  # Too long (>20)
            }
        ]
    }

    print("\nScenario 3: Invalid IP and too long serialNumber - should fail")
    results = engine.evaluate_data(decommission_can_run_data_3, entity_type="request", categories= ["CAN NDC DECOMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Scenario 4: No serialNumber - should still pass
    decommission_can_run_data_4 = {
        "requests": [
            {
                "id": "REQ-012",
                "fqdn": "server10.example.com",
                "managementIP": "192.168.1.6",
                "l1Technician": "David Clark",
                "l1TechnicianGroup": "Server Support"
                # No serialNumber - should pass due to any condition
            }
        ]
    }

    print("\nScenario 4: No serialNumber - should still pass")
    results = engine.evaluate_data(decommission_can_run_data_4, entity_type="request", categories = ["CAN NDC DECOMMISSION REQUEST"])
    for result in results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print("    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")