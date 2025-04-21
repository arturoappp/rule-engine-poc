from unittest.mock import Mock

from app.api.models.rules import Rule, RuleCondition
from app.services.rule_service import RuleService


class TestRuleService:
    """Unit tests for the RuleService class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.service = RuleService()
        # Create a mock rule engine to avoid hitting the actual engine in unit tests
        self.service.engine = Mock()

    def test_validate_rule_valid(self):
        """Test validation of a valid rule"""
        # Create a test rule
        rule = Rule(
            name="Test Rule",
            description="Test Description",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Cisco Systems"
            ),
            categories=["test"]
        )

        # Validate the rule
        valid, errors = self.service.validate_rule(rule)

        # Check result
        assert valid is True
        assert errors is None

    def test_validate_rule_invalid(self):
        """Test validation of an invalid rule"""
        # Create an invalid test rule (missing required fields)
        rule = Rule(
            name="name rule test",
            description="Test Description",
            conditions=RuleCondition(),  # Empty conditions (invalid)
            categories=["test"]
        )

        # Validate the rule
        valid, errors = self.service.validate_rule(rule)

        # Check result
        assert valid is False
        assert len(errors) > 0
        assert any("conditions" in error.lower() for error in errors)

    def test_store_rules_new(self):
        """Test storing new rules"""
        # Create test rules
        rules = [
            Rule(
                name="Test Rule 1",
                description="Test Description 1",
                conditions=RuleCondition(
                    path="$.devices[*].vendor",
                    operator="equal",
                    value="Cisco Systems"
                ),
                categories=["test1", "test2"]
            ),
            Rule(
                name="Test Rule 2",
                description="Test Description 2",
                conditions=RuleCondition(
                    path="$.devices[*].osVersion",
                    operator="equal",
                    value="17.3.6"
                ),
                categories=["test2", "test3"]
            )
        ]

        # Configure mock to return empty rule lists (no existing rules)
        self.service.engine.get_rules_by_category.return_value = []

        # Store the rules
        success, message, count = self.service.store_rules("device", rules)

        # Check result
        assert success is True
        assert count == 2
        assert "2 new" in message

        # Verify engine method calls
        assert self.service.engine.load_rules_from_json.call_count >= 1

    def test_store_rules_overwrite(self):
        """Test overwriting existing rules"""
        # Create test rule
        rule = Rule(
            name="Existing Rule",
            description="Updated Description",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Updated Value"
            ),
            categories=["test1", "test2"]
        )

        # Configure mock to return existing rules
        self.service.engine.get_rules_by_category.return_value = [
            {
                "name": "Existing Rule",
                "description": "Old Description",
                "conditions": {
                    "path": "$.devices[*].vendor",
                    "operator": "equal",
                    "value": "Old Value"
                },
                "categories": ["test1"]
            }
        ]

        # Store the rule
        success, message, count = self.service.store_rules("device", [rule])

        # Check result
        assert success is True
        assert count == 1
        assert "1 overwritten" in message

        # Verify engine method calls
        assert self.service.engine.load_rules_from_json.call_count >= 1

    def test_store_rules_multi_category(self):
        """Test storing rules in multiple categories"""
        # Create test rule with multiple categories
        rule = Rule(
            name="Multi Category Rule",
            description="Test Description",
            conditions=RuleCondition(
                path="$.devices[*].vendor",
                operator="equal",
                value="Cisco Systems"
            ),
            categories=["category1", "category2", "category3"]
        )

        # Configure mock to return empty rule lists
        self.service.engine.get_rules_by_category.return_value = []

        # Store the rule
        success, message, count = self.service.store_rules("device", [rule])

        # Check result
        assert success is True
        assert count == 1
        assert "3 categories" in message

        # Verify engine method calls - should call load_rules_from_json once for each category
        assert self.service.engine.load_rules_from_json.call_count >= 3