import pytest
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from app.services.rule_service import RuleService


@pytest.mark.parametrize(
    "entity_type, provided_category, expected_entity_types",
    [
        ("commission", "should", ["commission"]),
        (None, None, ["commission", "decommission"]),
    ],
)
def test_get_rules_calls_create_rules_dict_with_correct_parameters(mocker: MockerFixture, entity_type, provided_category, expected_entity_types):
    expected_result = {}
    mock_create_rules_dict = mocker.patch("app.services.rule_service.create_rules_dict")
    mock_create_rules_dict.return_value = expected_result
    mock_engine = MagicMock()
    mock_engine.get_entity_types.return_value = ["commission", "decommission"]

    rule_service = RuleService()
    rule_service.engine = mock_engine

    result = rule_service.get_rules(entity_type, provided_category)

    mock_create_rules_dict.assert_called_with(mock_engine, provided_category, expected_entity_types)
    assert result == expected_result


if __name__ == "__main__":
    pytest.main()
