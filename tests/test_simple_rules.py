"""
Tests for simple rule evaluations.
"""

import unittest
import json

from core.engine import RuleEngine


class SimpleRulesTest(unittest.TestCase):
    """Test case for simple rule evaluations."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()

        # Simple "equal" rule
        equal_rule = """
        [
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
        """

        self.engine.load_rules_from_json(equal_rule, entity_type="item", category="test")

        # Simple "not_equal" rule
        not_equal_rule = """
        [
            {
                "name": "Not Equal Rule",
                "description": "Tests the 'not_equal' operator",
                "conditions": {
                    "all": [
                        {
                            "path": "$.items[*].value",
                            "operator": "not_equal",
                            "value": 5
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(not_equal_rule, entity_type="item", category="test")

    def test_equal_rule_pass(self):
        """Test case where all items pass the 'equal' rule."""
        data = {
            "items": [
                {"id": "item-1", "value": 10},
                {"id": "item-2", "value": 10},
                {"id": "item-3", "value": 10}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="item", categories=["test"])
        equal_rule_result = next((r for r in results if r.rule_name == "Equal Rule"), None)

        self.assertIsNotNone(equal_rule_result)
        self.assertTrue(equal_rule_result.success)
        self.assertEqual(len(equal_rule_result.failing_elements), 0)

    def test_equal_rule_fail(self):
        """Test case where some items fail the 'equal' rule."""
        data = {
            "items": [
                {"id": "item-1", "value": 10},
                {"id": "item-2", "value": 15},  # This should fail
                {"id": "item-3", "value": 10}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="item", categories=["test"])
        equal_rule_result = next((r for r in results if r.rule_name == "Equal Rule"), None)

        self.assertIsNotNone(equal_rule_result)
        self.assertFalse(equal_rule_result.success)
        self.assertEqual(len(equal_rule_result.failing_elements), 1)
        self.assertEqual(equal_rule_result.failing_elements[0]["id"], "item-2")

    def test_not_equal_rule_pass(self):
        """Test case where all items pass the 'not_equal' rule."""
        data = {
            "items": [
                {"id": "item-1", "value": 10},
                {"id": "item-2", "value": 15},
                {"id": "item-3", "value": 20}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="item", categories=["test"])
        not_equal_rule_result = next((r for r in results if r.rule_name == "Not Equal Rule"), None)

        self.assertIsNotNone(not_equal_rule_result)
        self.assertTrue(not_equal_rule_result.success)
        self.assertEqual(len(not_equal_rule_result.failing_elements), 0)

    def test_not_equal_rule_fail(self):
        """Test case where some items fail the 'not_equal' rule."""
        data = {
            "items": [
                {"id": "item-1", "value": 10},
                {"id": "item-2", "value": 5},  # This should fail
                {"id": "item-3", "value": 20}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="item", categories=["test"])
        not_equal_rule_result = next((r for r in results if r.rule_name == "Not Equal Rule"), None)

        self.assertIsNotNone(not_equal_rule_result)
        self.assertFalse(not_equal_rule_result.success)
        self.assertEqual(len(not_equal_rule_result.failing_elements), 1)
        self.assertEqual(not_equal_rule_result.failing_elements[0]["id"], "item-2")


if __name__ == '__main__':
    unittest.main()