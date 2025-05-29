from app.helpers.helper import (
    _get_entity_key,
    extract_entities,
    organize_results_by_entity,
    _entity_failed_rule,
    _entities_match,
    _get_entity_specific_failures
)
from rule_engine.core.failure_info import FailureInfo
from rule_engine.core.rule_result import RuleResult


# Tests for _get_entity_key
def test_get_entity_key_adds_s_to_singular_entity_type():
    """Test that 's' is added to entity types that don't end with 's'."""
    assert _get_entity_key("device") == "devices"
    assert _get_entity_key("Commission Request") == "Commission Requests"
    assert _get_entity_key("rule") == "rules"


def test_get_entity_key_preserves_plural_entity_type():
    """Test that entity types already ending with 's' are preserved."""
    assert _get_entity_key("devices") == "devices"
    assert _get_entity_key("Commission Requests") == "Commission Requests"
    assert _get_entity_key("rules") == "rules"


def test_get_entity_key_handles_edge_cases():
    """Test edge cases for entity key generation."""
    assert _get_entity_key("") == "s"  # Empty string gets 's' added
    assert _get_entity_key("s") == "s"  # Single 's' stays as is
    assert _get_entity_key("status") == "status"  # Words ending in 's'


# Tests for extract_entities
def test_extract_entities_with_plural_key_returns_entities():
    """Test extracting entities when data has the plural form of entity type."""
    data = {
        "devices": [
            {"id": "1", "name": "Device1"},
            {"id": "2", "name": "Device2"}
        ]
    }

    entities = extract_entities(data, "device")
    assert len(entities) == 2
    assert entities[0]["id"] == "1"
    assert entities[1]["name"] == "Device2"


def test_extract_entities_with_singular_key_returns_entities():
    """Test extracting entities when data uses singular form."""
    data = {
        "device": [
            {"id": "1", "name": "Device1"},
            {"id": "2", "name": "Device2"}
        ]
    }

    entities = extract_entities(data, "device")
    assert len(entities) == 2
    assert entities[0]["id"] == "1"


def test_extract_entities_with_no_matching_key_returns_empty_list():
    """Test that empty list is returned when no matching key exists."""
    data = {
        "something_else": [{"id": "1"}]
    }

    entities = extract_entities(data, "device")
    assert entities == []


def test_extract_entities_with_non_list_value_returns_empty_list():
    """Test that empty list is returned when value is not a list."""
    data = {
        "devices": "not a list",
        "device": {"id": "1"}  # Also not a list
    }

    entities = extract_entities(data, "device")
    assert entities == []


def test_extract_entities_with_complex_entity_type():
    """Test extraction with multi-word entity types."""
    data = {
        "Commission Requests": [
            {"id": "1", "type": "commission"},
            {"id": "2", "type": "commission"}
        ]
    }

    entities = extract_entities(data, "Commission Request")
    assert len(entities) == 2
    assert entities[0]["type"] == "commission"


# Tests for _entities_match
def test_entities_match_with_identical_entities_returns_true():
    """Test that identical entities match."""
    entity1 = {"id": "1", "name": "Test", "value": 100}
    entity2 = {"id": "1", "name": "Test", "value": 100}

    assert _entities_match(entity1, entity2) is True


def test_entities_match_with_different_values_returns_false():
    """Test that entities with different values don't match."""
    entity1 = {"id": "1", "name": "Test"}
    entity2 = {"id": "1", "name": "Different"}

    assert _entities_match(entity1, entity2) is False


def test_entities_match_with_different_keys_returns_false():
    """Test that entities with different keys don't match."""
    entity1 = {"id": "1", "name": "Test"}
    entity2 = {"id": "1", "name": "Test", "extra": "field"}

    assert _entities_match(entity1, entity2) is False


def test_entities_match_with_empty_entities():
    """Test matching with empty entities."""
    assert _entities_match({}, {}) is True
    assert _entities_match({"id": "1"}, {}) is False
    assert _entities_match({}, {"id": "1"}) is False


# Tests for _entity_failed_rule
def test_entity_failed_rule_with_successful_rule_returns_false():
    """Test that successful rules return False."""
    entity = {"id": "1", "name": "Test"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=True,
        message="All entities pass",
        failing_elements=[]
    )

    assert _entity_failed_rule(entity, rule_result, 0) is False


def test_entity_failed_rule_with_matching_failing_element_returns_true():
    """Test that entity matching a failing element returns True."""
    entity = {"id": "1", "name": "Test"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Some entities fail",
        failing_elements=[
            {"id": "1", "name": "Test"},  # Matches our entity
            {"id": "2", "name": "Other"}
        ]
    )

    assert _entity_failed_rule(entity, rule_result, 0) is True


def test_entity_failed_rule_with_no_matching_failing_element_returns_false():
    """Test that entity not in failing elements returns False."""
    entity = {"id": "3", "name": "Different"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Some entities fail",
        failing_elements=[
            {"id": "1", "name": "Test"},
            {"id": "2", "name": "Other"}
        ]
    )

    assert _entity_failed_rule(entity, rule_result, 0) is False


# Tests for _get_entity_specific_failures
def test_get_entity_specific_failures_with_matching_field():
    """Test getting failures for entity with matching field values."""
    entity = {"vendor": "Microsoft", "version": "10.0"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Failed",
        failure_details=[
            FailureInfo(
                operator="equal",
                path="$.devices[*].vendor",
                expected_value="Cisco",
                actual_value="Microsoft"
            )
        ]
    )

    failures = _get_entity_specific_failures(entity, rule_result, 0)
    assert len(failures) == 1
    assert failures[0].operator == "equal"
    assert failures[0].expected_value == "Cisco"
    assert failures[0].actual_value == "Microsoft"


def test_get_entity_specific_failures_with_exists_operator():
    """Test failures for exists operator when field is missing."""
    entity = {"vendor": "Cisco"}  # Missing 'version' field
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Failed",
        failure_details=[
            FailureInfo(
                operator="exists",
                path="$.devices[*].version",
                expected_value=True,
                actual_value=None
            )
        ]
    )

    failures = _get_entity_specific_failures(entity, rule_result, 0)
    assert len(failures) == 1
    assert failures[0].operator == "exists"
    assert failures[0].actual_value is None


def test_get_entity_specific_failures_with_no_specific_failures():
    """Test that generic failure is added when no specific failures found."""
    entity = {"id": "1"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Failed",
        failure_details=[]  # No specific failure details
    )

    failures = _get_entity_specific_failures(entity, rule_result, 0)
    assert len(failures) == 1
    assert failures[0].operator == "unknown"
    assert failures[0].path == "$"


def test_get_entity_specific_failures_with_complex_path():
    """Test failures with nested paths."""
    entity = {"config": {"version": "1.0"}, "version": "2.0"}
    rule_result = RuleResult(
        rule_name="Test Rule",
        success=False,
        message="Failed",
        failure_details=[
            FailureInfo(
                operator="equal",
                path="$.devices[*].config.version",
                expected_value="2.0",
                actual_value="1.0"
            ),
            FailureInfo(
                operator="equal",
                path="$.devices[*].version",
                expected_value="1.0",
                actual_value="2.0"
            )
        ]
    )

    failures = _get_entity_specific_failures(entity, rule_result, 0)
    # Should only match the second failure (direct version field)
    assert len(failures) == 1
    assert failures[0].path == "$.devices[*].version"
    assert failures[0].actual_value == "2.0"


# Tests for organize_results_by_entity
def test_organize_results_by_entity_with_mixed_results():
    """Test organizing results with some entities passing and some failing."""
    entities = [
        {"id": "1", "vendor": "Cisco"},
        {"id": "2", "vendor": "Microsoft"},
        {"id": "3", "vendor": "Cisco"}
    ]

    rule_results = [
        RuleResult(
            rule_name="Vendor Must Be Cisco",
            success=False,
            message="Some entities fail",
            failing_elements=[{"id": "2", "vendor": "Microsoft"}],
            failure_details=[
                FailureInfo(
                    operator="equal",
                    path="$.devices[*].vendor",
                    expected_value="Cisco",
                    actual_value="Microsoft"
                )
            ]
        ),
        RuleResult(
            rule_name="Has ID",
            success=True,
            message="All entities pass",
            failing_elements=[]
        )
    ]

    results = organize_results_by_entity(entities, rule_results)

    assert len(results) == 3

    # First entity (Cisco) should pass both rules
    assert results[0].evaluation_summary.rules_passed == 2
    assert results[0].evaluation_summary.rules_failed == 0
    assert len(results[0].rules_passed) == 2
    assert "Vendor Must Be Cisco" in results[0].rules_passed
    assert "Has ID" in results[0].rules_passed

    # Second entity (Microsoft) should fail vendor rule, pass ID rule
    assert results[1].evaluation_summary.rules_passed == 1
    assert results[1].evaluation_summary.rules_failed == 1
    assert "Has ID" in results[1].rules_passed
    assert len(results[1].rules_failed) == 1
    assert results[1].rules_failed[0].rule_name == "Vendor Must Be Cisco"

    # Third entity (Cisco) should pass both rules
    assert results[2].evaluation_summary.rules_passed == 2
    assert results[2].evaluation_summary.rules_failed == 0


def test_organize_results_by_entity_with_all_passing():
    """Test organizing results when all entities pass all rules."""
    entities = [
        {"id": "1", "status": "active"},
        {"id": "2", "status": "active"}
    ]

    rule_results = [
        RuleResult(
            rule_name="Status Check",
            success=True,
            message="All pass",
            failing_elements=[]
        )
    ]

    results = organize_results_by_entity(entities, rule_results)

    assert len(results) == 2
    for result in results:
        assert result.evaluation_summary.rules_passed == 1
        assert result.evaluation_summary.rules_failed == 0
        assert "Status Check" in result.rules_passed
        assert len(result.rules_failed) == 0


def test_organize_results_by_entity_with_empty_inputs():
    """Test organizing with empty entities or rules."""
    # Empty entities
    results = organize_results_by_entity([], [])
    assert len(results) == 0

    # Entities but no rules
    entities = [{"id": "1"}]
    results = organize_results_by_entity(entities, [])
    assert len(results) == 1
    assert results[0].evaluation_summary.rules_passed == 0
    assert results[0].evaluation_summary.rules_failed == 0


def test_organize_results_by_entity_preserves_entity_data():
    """Test that original entity data is preserved in results."""
    entities = [
        {"id": "1", "name": "Test", "metadata": {"key": "value"}}
    ]

    rule_results = [
        RuleResult(
            rule_name="Test Rule",
            success=True,
            message="Pass",
            failing_elements=[]
        )
    ]

    results = organize_results_by_entity(entities, rule_results)

    assert results[0].data == entities[0]
    assert results[0].data["metadata"]["key"] == "value"
