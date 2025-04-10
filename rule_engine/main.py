"""
Example usage of the refactored rule engine.
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

    # Load rules for devices
    DEVICE_RULES_JSON = """
    [
        {
            "name": "Cisco Version Rule",
            "description": "Ensures Cisco devices are running the required OS version",
            "conditions": {
                "any": [
                    {
                        "path": "$.devices[*].vendor",
                        "operator": "not_equal",
                        "value": "Cisco Systems"
                    },
                    {
                        "all": [
                            {
                                "path": "$.devices[*].vendor",
                                "operator": "equal",
                                "value": "Cisco Systems"
                            },
                            {
                                "path": "$.devices[*].osVersion",
                                "operator": "equal",
                                "value": "17.3.6"
                            },
                            {
                                "path": "$.devices[*].hostname",
                                "operator": "role_device",
                                "value": "primary"
                            }
                        ]
                    }
                ]
            }
        }
    ]
    """

    engine.load_rules_from_json(DEVICE_RULES_JSON, entity_type="device", category="version")

    # Load rules for tasks
    TASK_RULES_JSON = """
    [
        {
            "name": "Task must have priority",
            "description": "Ensures all tasks have a priority assigned",
            "conditions": {
                "all": [
                    {
                        "path": "$.tasks[*].priority",
                        "operator": "exists",
                        "value": true
                    }
                ]
            }
        }
    ]
    """

    engine.load_rules_from_json(TASK_RULES_JSON, entity_type="task", category="validation")

    # Example data for devices
    device_data = {
        "devices": [
            {
                "vendor": "Cisco Systems",
                "osVersion": "17.3.6",
                "mgmtIP": "192.168.1.1",
                "hostname": "HUJ-AA-101",
            },
            {
                "vendor": "Microsoft",
                "osVersion": "10.0.19045",
                "mgmtIP": "10.0.0.1",
                "hostname": "HUJ-AA-201",
            },
            {
                "vendor": "Cisco Systems",
                "osVersion": "17.3.63",  # This device should fail
                "mgmtIP": "192.168.1.3",
                "hostname": "HUJ-AA-101",
            }
        ]
    }

    # Example data for tasks
    task_data = {
        "tasks": [
            {
                "id": "TASK-001",
                "name": "Update firmware",
                "priority": "high",
                "assignee": "John Smith"
            },
            {
                "id": "TASK-002",
                "name": "Review logs",
                "priority": "low",
                "assignee": "Jane Doe"
                # No priority - should fail
            }
        ]
    }

    # Evaluate device data
    print("\nEvaluating device data...")
    device_results = engine.evaluate_data(device_data, entity_type="device")
    print("Device Evaluation Results:")
    for result in device_results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print(f"    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")

    # Evaluate task data
    print("\nEvaluating task data...")
    task_results = engine.evaluate_data(task_data, entity_type="task")
    print("Task Evaluation Results:")
    for result in task_results:
        print(f"  - {result}")
        if not result.success and result.failing_elements:
            print(f"    Elements that failed:")
            for i, element in enumerate(result.failing_elements):
                print(f"      {i + 1}. {json.dumps(element)}")