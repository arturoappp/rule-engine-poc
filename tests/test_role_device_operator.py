"""
Tests for the role_device operator in the rule engine.
"""

import unittest
import json

from core.engine import RuleEngine


class RoleDeviceOperatorTest(unittest.TestCase):
    """Test case for the role_device operator."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()

        # Load rules for testing the role_device operator
        role_device_rule = """
        [
            {
                "name": "Standalone Device Rule",
                "description": "Checks if the device is a standalone device",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].hostname",
                            "operator": "role_device",
                            "value": "standalone"
                        }
                    ]
                }
            },
            {
                "name": "Primary Device Rule",
                "description": "Checks if the device is a primary device",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].hostname",
                            "operator": "role_device",
                            "value": "primary"
                        }
                    ]
                }
            },
            {
                "name": "Secondary Device Rule",
                "description": "Checks if the device is a secondary device",
                "conditions": {
                    "all": [
                        {
                            "path": "$.devices[*].hostname",
                            "operator": "role_device",
                            "value": "secondary"
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(role_device_rule, entity_type="device", category="role")

    def test_standalone_device(self):
        """Test the 'role_device' operator with standalone devices."""
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-001", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test with a non-standalone device (should fail)
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_primary_device(self):
        """Test the 'role_device' operator with primary devices."""
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test with a non-primary device (should fail)
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-201", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_secondary_device(self):
        """Test the 'role_device' operator with secondary devices."""
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-201", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test with a non-secondary device (should fail)
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-101", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        rule_result = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_invalid_hostname_format(self):
        """Test the 'role_device' operator with invalid hostname format."""
        data = {
            "devices": [
                {"id": "device-1", "hostname": "INVALID", "status": "active"}
            ]
        }

        # The operator should handle invalid formats gracefully
        # We expect all rules to fail in this case
        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])

        for rule_result in results:
            self.assertFalse(rule_result.success)

    def test_multiple_devices(self):
        """Test the 'role_device' operator with multiple devices of different roles."""
        data = {
            "devices": [
                {"id": "device-1", "hostname": "HUJ-AA-001", "status": "active"},  # standalone
                {"id": "device-2", "hostname": "HUJ-AA-101", "status": "active"},  # primary
                {"id": "device-3", "hostname": "HUJ-AA-201", "status": "active"}  # secondary
            ]
        }

        # Test standalone rule
        results = self.engine.evaluate_data(data, entity_type="device", categories=["role"])
        standalone_rule = next((r for r in results if r.rule_name == "Standalone Device Rule"), None)

        self.assertIsNotNone(standalone_rule)
        self.assertFalse(standalone_rule.success)  # Should fail because not all devices are standalone
        self.assertEqual(len(standalone_rule.failing_elements), 2)

        # Check the failing elements
        failing_ids = [element["id"] for element in standalone_rule.failing_elements]
        self.assertIn("device-2", failing_ids)
        self.assertIn("device-3", failing_ids)

        # Test primary rule
        primary_rule = next((r for r in results if r.rule_name == "Primary Device Rule"), None)

        self.assertIsNotNone(primary_rule)
        self.assertFalse(primary_rule.success)  # Should fail because not all devices are primary
        self.assertEqual(len(primary_rule.failing_elements), 2)

        # Check the failing elements
        failing_ids = [element["id"] for element in primary_rule.failing_elements]
        self.assertIn("device-1", failing_ids)
        self.assertIn("device-3", failing_ids)

        # Test secondary rule
        secondary_rule = next((r for r in results if r.rule_name == "Secondary Device Rule"), None)

        self.assertIsNotNone(secondary_rule)
        self.assertFalse(secondary_rule.success)  # Should fail because not all devices are secondary
        self.assertEqual(len(secondary_rule.failing_elements), 2)

        # Check the failing elements
        failing_ids = [element["id"] for element in secondary_rule.failing_elements]
        self.assertIn("device-1", failing_ids)
        self.assertIn("device-2", failing_ids)


if __name__ == '__main__':
    unittest.main()