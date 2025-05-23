from typing import Dict, List, Any

from app.api.models.evaluate import DataEvaluationItem, RuleFailureDetails, DataEvaluationSummary, FailureDetail


def _get_entity_key(entity_type: str) -> str:
    return f"{entity_type}s" if not entity_type.endswith('s') else entity_type


def _extract_entities(data: Dict[str, Any], entity_type: str) -> List[Dict[str, Any]]:
    entity_key = _get_entity_key(entity_type)

    if entity_key in data and isinstance(data[entity_key], list):
        return data[entity_key]
    elif entity_type in data and isinstance(data[entity_type], list):
        return data[entity_type]

    return []


def _organize_results_by_entity(
        all_entities: List[Dict[str, Any]],
        all_results: List[Any]
) -> List[DataEvaluationItem]:
    data_evaluation_results = []

    for entity_index, entity in enumerate(all_entities):
        rules_passed = []
        rules_failed = []

        for rule_result in all_results:
            rule_name = rule_result.rule_name

            entity_failed_rule = _entity_failed_rule(entity, rule_result, entity_index)

            if entity_failed_rule:
                entity_failure_details = _get_entity_specific_failures(
                    entity, rule_result, entity_index
                )

                rule_failure = RuleFailureDetails(
                    rule_name=rule_name,
                    failure_details=entity_failure_details
                )
                rules_failed.append(rule_failure)
            else:
                rules_passed.append(rule_name)

        # Create evaluation item for this entity
        evaluation_summary = DataEvaluationSummary(
            rules_passed=len(rules_passed),
            rules_failed=len(rules_failed)
        )

        data_evaluation_item = DataEvaluationItem(
            data=entity,
            evaluation_summary=evaluation_summary,
            rules_passed=rules_passed,
            rules_failed=rules_failed
        )

        data_evaluation_results.append(data_evaluation_item)

    return data_evaluation_results


def _entity_failed_rule(entity: Dict[str, Any], rule_result: Any, entity_index: int) -> bool:
    if rule_result.success:
        return False

    for failing_element in rule_result.failing_elements:
        if _entities_match(entity, failing_element):
            return True

    return False


def _entities_match(entity1: Dict[str, Any], entity2: Dict[str, Any]) -> bool:
    for key, value in entity1.items():
        if key not in entity2 or entity2[key] != value:
            return False

    for key, value in entity2.items():
        if key not in entity1 or entity1[key] != value:
            return False

    return True


def _get_entity_specific_failures(
        entity: Dict[str, Any],
        rule_result: Any,
        entity_index: int
) -> List[FailureDetail]:
    entity_failures = []

    for failure_detail in rule_result.failure_details:
        path = failure_detail.path
        if path and path.startswith('$.'):
            field_parts = path.split('.')
            if len(field_parts) >= 2:
                field_name = field_parts[-1]

                if field_name in entity:
                    entity_value = entity[field_name]
                    if entity_value == failure_detail.actual_value:
                        entity_failures.append(FailureDetail(
                            operator=failure_detail.operator,
                            path=failure_detail.path,
                            expected_value=failure_detail.expected_value,
                            actual_value=failure_detail.actual_value
                        ))
                elif failure_detail.operator == "exists" and failure_detail.expected_value is True:
                    entity_failures.append(FailureDetail(
                        operator=failure_detail.operator,
                        path=failure_detail.path,
                        expected_value=failure_detail.expected_value,
                        actual_value=None
                    ))

    if not entity_failures and not rule_result.success:
        entity_failures.append(FailureDetail(
            operator="unknown",
            path="$",
            expected_value=None,
            actual_value=None
        ))

    return entity_failures
