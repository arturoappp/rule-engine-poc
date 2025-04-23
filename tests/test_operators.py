"""
Tests for all operator implementations in the rule engine.
"""

import unittest

from rule_engine.core.engine import RuleEngine


class OperatorsTest(unittest.TestCase):
    """Test case for all operators in the rule engine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = RuleEngine()

        # Load a rule for each operator type
        operators_rule = """
        [
            {
                "name": "Equal Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "equal",
                            "value": 100
                        }
                    ]
                }
            },
            {
                "name": "Not Equal Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "not_equal",
                            "value": 50
                        }
                    ]
                }
            },
            {
                "name": "Greater Than Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "greater_than",
                            "value": 75
                        }
                    ]
                }
            },
            {
                "name": "Less Than Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "less_than",
                            "value": 200
                        }
                    ]
                }
            },
            {
                "name": "Greater Than Equal Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "greater_than_equal",
                            "value": 100
                        }
                    ]
                }
            },
            {
                "name": "Less Than Equal Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].price",
                            "operator": "less_than_equal",
                            "value": 100
                        }
                    ]
                }
            },
            {
                "name": "Exists Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].discount",
                            "operator": "exists",
                            "value": true
                        }
                    ]
                }
            },
            {
                "name": "Not Empty Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].tags",
                            "operator": "not_empty",
                            "value": true
                        }
                    ]
                }
            },
            {
                "name": "Match Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].sku",
                            "operator": "match",
                            "value": "^PRD-[0-9]{4}$"
                        }
                    ]
                }
            },
            {
                "name": "Contains Operator Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.products[*].description",
                            "operator": "contains",
                            "value": "premium"
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(operators_rule, entity_type="product", category="operators")

    def test_equal_operator(self):
        """Test the 'equal' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 101, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_not_equal_operator(self):
        """Test the 'not_equal' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Not Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 50, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Not Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_greater_than_operator(self):
        """Test the 'greater_than' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Greater Than Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 75, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Greater Than Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_less_than_operator(self):
        """Test the 'less_than' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Less Than Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 200, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Less Than Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_greater_than_equal_operator(self):
        """Test the 'greater_than_equal' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Greater Than Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 99, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Greater Than Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_less_than_equal_operator(self):
        """Test the 'less_than_equal' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Less Than Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 101, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Less Than Equal Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_exists_operator(self):
        """Test the 'exists' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Exists Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "tags": ["electronics"], "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Exists Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_not_empty_operator(self):
        """Test the 'not_empty' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Not Empty Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": [], "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Not Empty Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_match_operator(self):
        """Test the 'match' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Match Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRODUCT-001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Match Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_contains_operator(self):
        """Test the 'contains' operator."""
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A premium product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Contains Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "products": [
                {"sku": "PRD-0001", "price": 100, "discount": 10, "tags": ["electronics"],
                 "description": "A standard product"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="product", categories=["operators"])
        rule_result = next((r for r in results if r.rule_name == "Contains Operator Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)

    def test_value_in_list(self):
        """Test checking if a value exists in a list."""
        # Add a rule that checks if a value is in a list
        list_rule = """
        [
            {
                "name": "Protocol Check Rule",
                "conditions": {
                    "all": [
                        {
                            "path": "$.connections[*].protocol",
                            "operator": "in_list",
                            "value": ["HTTP", "HTTPS", "FTP", "SFTP"]
                        }
                    ]
                }
            }
        ]
        """
        self.engine.load_rules_from_json(list_rule, entity_type="connection", category="list_ops")

        # Test success case
        data = {
            "connections": [
                {"id": "conn-1", "protocol": "HTTPS", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="connection", categories=["list_ops"])
        rule_result = next((r for r in results if r.rule_name == "Protocol Check Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertTrue(rule_result.success)

        # Test failure case
        data = {
            "connections": [
                {"id": "conn-1", "protocol": "TELNET", "status": "active"}
            ]
        }

        results = self.engine.evaluate_data(data, entity_type="connection", categories=["list_ops"])
        rule_result = next((r for r in results if r.rule_name == "Protocol Check Rule"), None)

        self.assertIsNotNone(rule_result)
        self.assertFalse(rule_result.success)


if __name__ == '__main__':
    unittest.main()