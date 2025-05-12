from codecs import ignore_errors

import pytest
from pytest_mock import MockerFixture
from app.api.models.rules import RuleCondition, RuleListResponse, RuleStats, StoredRule
from app.helpers.response_formatter import format_list_rules_response
from app.api.models.rules import Rule
from app.api.models.rules import Rule, RuleListResponse, RuleStats, StoredRule


def test_format_list_rules_response_with_empty_stored_rules():
    stored_rules = []
    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.entity_types == []
    assert result.categories == {}
    assert result.rules == []
    assert result.stats == {}


def test_format_list_rules_response_with_single_stored_rule():
    rule = Rule(
        name="rule1",
        entity_type="Entity1",
        description="Test rule",
        conditions={}
    )
    stored_rule = StoredRule(
        rule_name="rule1",
        entity_type="Entity1",
        description="Test rule",
        categories={"Category1"},
        rule=rule
    )
    stored_rules = [stored_rule]

    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.entity_types == ["Entity1"]
    assert result.categories == {"Entity1": ["Category1"]}
    assert result.rules == [rule]
    assert result.stats == {
        "Entity1": RuleStats(
            total_rules=1,
            rules_by_category={"Category1": 1}
        )
    }


def test_format_list_rules_response_with_multiple_stored_rules():
    rule1 = Rule(
        name="rule1",
        entity_type="Entity1",
        description="Test rule 1",
        conditions={}
    )
    rule2 = Rule(
        name="rule2",
        entity_type="Entity2",
        description="Test rule 2",
        conditions={}
    )
    rule3 = Rule(
        name="rule3",
        entity_type="Entity1",
        description="Test rule 3",
        conditions={}
    )
    stored_rules = [
        StoredRule(
            rule_name="rule1",
            entity_type="Entity1",
            description="Test rule 1",
            categories={"Category1", "Category2"},
            rule=rule1
        ),
        StoredRule(
            rule_name="rule3",
            entity_type="Entity1",
            description="Test rule 3",
            categories={"Category1"},
            rule=rule3
        ),
        StoredRule(
            rule_name="rule2",
            entity_type="Entity2",
            description="Test rule 2",
            categories={"Category2"},
            rule=rule2
        ),
    ]

    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.entity_types == ["Entity1", "Entity2"]
    assert result.categories == {
        "Entity1": ["Category1", "Category2"],
        "Entity2": ["Category2"]
    }
    assert result.rules == [rule1, rule2, rule3]
    assert result.stats == {
        "Entity1": RuleStats(
            total_rules=2,
            rules_by_category={"Category1": 2, "Category2": 1}
        ),
        "Entity2": RuleStats(
            total_rules=1,
            rules_by_category={"Category2": 1}
        )
    }
