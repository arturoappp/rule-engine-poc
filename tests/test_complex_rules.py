"""
Tests for complex rule evaluations with nested logical operators.
"""

import unittest

from core.engine import RuleEngine


class ComplexRulesTest(unittest.TestCase):
    """Test case for complex rule evaluations."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()

        # Complex rule with nested conditions
        complex_rule = """
        [
            {
                "name": "Complex Device Rule",
                "description": "Vendor must be Cisco with version 17.x, or non-Cisco with any version above 10.0",
                "conditions": {
                    "any": [
                        {
                            "all": [
                                {
                                    "path": "$.devices[*].vendor",
                                    "operator": "equal",
                                    "value": "Cisco Systems"
                                },
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^17\\\\."
                                }
                            ]
                        },
                        {
                            "all": [
                                {
                                    "path": "$.devices[*].vendor",
                                    "operator": "not_equal",
                                    "value": "Cisco Systems"
                                },
                                {
                                    "path": "$.devices[*].osVersion",
                                    "operator": "match",
                                    "value": "^[1-9][0-9]\\\\."
                                }
                            ]
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(complex_rule, entity_type="device", category="complex")

    def test_complex_rule_cisco_pass(self):
        """Test case where Cisco devices with correct version pass."""
        data = {
            "devices": [
                {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "17.3.6"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["complex"])
        rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 0)

    def test_complex_rule_non_cisco_pass(self):
        """Test case where non-Cisco devices with correct version pass."""
        data = {
            "devices": [
                {"id": "device-1", "vendor": "Juniper", "osVersion": "20.1"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["complex"])
        rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 0)

    def test_complex_rule_cisco_fail(self):
        """Test case where Cisco devices with wrong version fail."""
        data = {
            "devices": [
                {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "16.9.5"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["complex"])
        rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 1)

    def test_complex_rule_non_cisco_fail(self):
        """Test case where non-Cisco devices with wrong version fail."""
        data = {
            "devices": [
                {"id": "device-1", "vendor": "Juniper", "osVersion": "9.5"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["complex"])
        rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 1)

    def test_complex_rule_mixed_results(self):
        """Test case with mixed passing and failing devices."""
        data = {
            "devices": [
                {"id": "device-1", "vendor": "Cisco Systems", "osVersion": "17.3.6"},  # Pass
                {"id": "device-2", "vendor": "Cisco Systems", "osVersion": "16.9.5"},  # Fail
                {"id": "device-3", "vendor": "Juniper", "osVersion": "20.1"},  # Pass
                {"id": "device-4", "vendor": "Juniper", "osVersion": "9.5"}  # Fail
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="device", categories=["complex"])
        rule_result = next((r for r in results if r.rule_name == "Complex Device Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 2)

        # Check failing device IDs
        failing_ids = [element["id"] for element in rule_result.failing_elements]
        self.assertIn("device-2", failing_ids)
        self.assertIn("device-4", failing_ids)


if __name__ == '__main__':
    unittest.main()