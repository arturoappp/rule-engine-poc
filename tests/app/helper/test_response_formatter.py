from app.helpers.response_formatter import format_list_rules_response
from app.api.models.rules import Rule, RuleListResponse, RuleViewModel, StoredRule


def test_format_list_rules_response_with_empty_stored_rules():
    stored_rules = []
    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.rules == []


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

    expected_rule_view_model = RuleViewModel(
        rule_name="rule1",
        entity_type="Entity1",
        description="Test rule",
        conditions={},
        categories_associated_with={"Category1"}  # Updated to include categories
    )
    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.rules == [expected_rule_view_model]


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
            rule_name=rule1.name,
            entity_type=rule1.entity_type,
            description=rule1.description,
            categories={"Category1", "Category2"},
            rule=rule1
        ),
        StoredRule(
            rule_name=rule3.name,
            entity_type=rule3.entity_type,
            description=rule3.description,
            categories={"Category1"},
            rule=rule3
        ),
        StoredRule(
            rule_name=rule2.name,
            entity_type=rule2.entity_type,
            description=rule2.description,
            categories={"Category2"},
            rule=rule2
        ),
    ]

    ruleViewModel1 = RuleViewModel(
        rule_name="rule1",
        entity_type="Entity1",
        description="Test rule 1",
        conditions={},
        categories_associated_with={"Category1", "Category2"}  # Updated to include categories
    )
    ruleViewModel2 = RuleViewModel(
        rule_name="rule2",
        entity_type="Entity2",
        description="Test rule 2",
        conditions={},
        categories_associated_with={"Category2"}  # Updated to include categories
    )
    ruleViewModel3 = RuleViewModel(
        rule_name="rule3",
        entity_type="Entity1",
        description="Test rule 3",
        conditions={},
        categories_associated_with={"Category1"}  # Updated to include categories
    )

    result = format_list_rules_response(stored_rules)

    assert isinstance(result, RuleListResponse)
    assert result.rules == [ruleViewModel1, ruleViewModel2, ruleViewModel3]
