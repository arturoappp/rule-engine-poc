"""
Tests for deeply nested rule evaluations.
"""

import unittest
import json

from core.engine import RuleEngine


class NestedRulesTest(unittest.TestCase):
    """Test case for deeply nested rule evaluations."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()

        # Deep nested rule with multiple levels
        nested_rule = """
        [
            {
                "name": "Deep Nested Rule",
                "description": "A complex rule with several levels of nesting",
                "conditions": {
                    "all": [
                        {
                            "any": [
                                {
                                    "path": "$.configs[*].type",
                                    "operator": "equal",
                                    "value": "firewall"
                                },
                                {
                                    "all": [
                                        {
                                            "path": "$.configs[*].type",
                                            "operator": "equal",
                                            "value": "router"
                                        },
                                        {
                                            "path": "$.configs[*].security_level",
                                            "operator": "greater_than_equal",
                                            "value": 3
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "none": [
                                {
                                    "path": "$.configs[*].status",
                                    "operator": "equal",
                                    "value": "deprecated"
                                },
                                {
                                    "not": {
                                        "path": "$.configs[*].compliance_checked",
                                        "operator": "equal",
                                        "value": true
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(nested_rule, entity_type="config", category="nested")

    def test_nested_rule_firewall_pass(self):
        """Test case where firewall configs pass the nested rule."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "firewall",
                    "status": "active",
                    "compliance_checked": True
                }
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 0)

    def test_nested_rule_router_high_security_pass(self):
        """Test case where router configs with high security pass the nested rule."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "router",
                    "security_level": 4,
                    "status": "active",
                    "compliance_checked": True
                }
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 0)

    def test_nested_rule_router_low_security_fail(self):
        """Test case where router configs with low security fail the nested rule."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "router",
                    "security_level": 2,  # This fails the security level check
                    "status": "active",
                    "compliance_checked": True
                }
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 1)

    def test_nested_rule_fail_deprecated(self):
        """Test case where configs fail due to deprecated status."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "firewall",
                    "status": "deprecated",  # This fails the status check
                    "compliance_checked": True
                }
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 1)

    def test_nested_rule_fail_compliance(self):
        """Test case where configs fail due to missing compliance check."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "firewall",
                    "status": "active",
                    "compliance_checked": False  # This fails the compliance check
                }
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)
        self.assertEqual(len(rule_result.failing_elements), 1)

    def test_nested_rule_mixed_entities(self):
        """Test case with mixed passing and failing configs."""
        data = {
            "configs": [
                {
                    "id": "cfg-1",
                    "type": "firewall",
                    "status": "active",
                    "compliance_checked": True
                },  # Should pass
                {
                    "id": "cfg-2",
                    "type": "router",
                    "security_level": 2,
                    "status": "active",
                    "compliance_checked": True
                },  # Should fail - low security
                {
                    "id": "cfg-3",
                    "type": "firewall",
                    "status": "deprecated",
                    "compliance_checked": True
                },  # Should fail - deprecated
                {
                    "id": "cfg-4",
                    "type": "router",
                    "security_level": 4,
                    "status": "active",
                    "compliance_checked": True
                }  # Should pass
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="config", categories=["nested"])
        rule_result = next((r for r in results if r.rule_name == "Deep Nested Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

        # Check that exactly 2 configs failed
        self.assertEqual(len(rule_result.failing_elements), 2)

        # Check failing config IDs
        failing_ids = [element["id"] for element in rule_result.failing_elements]
        self.assertIn("cfg-2", failing_ids)
        self.assertIn("cfg-3", failing_ids)


if __name__ == '__main__':
    unittest.main()