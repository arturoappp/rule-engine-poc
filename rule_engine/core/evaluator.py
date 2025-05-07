"""
Module containing the rule evaluation logic.
"""

import logging

from app.api.models.rules import SpikeStoredRule
from rule_engine.conditions.conditions_factory import ConditionFactory
from rule_engine.core.rule_result import RuleResult, FailureInfo
from rule_engine.utils.path_utils import PathUtils

logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Class responsible for evaluating rules against data."""

    @staticmethod
    def evaluate_rule_for_entities(entities: list[dict], stored_rule: SpikeStoredRule) -> tuple[bool, list[dict], list[FailureInfo]]:
        """
        Evaluate a rule for a list of entities.

        Args:
            entities: List of entities (devices, tasks, etc.)
            rule: Rule dictionary

        Returns:
            Tuple (success, failing_entities, failure_details):
            - success: True if the rule is fulfilled, False otherwise
            - failing_entities: List of entities that failed the rule
            - failure_details: List of FailureInfo objects describing the failures
        """
        rule = stored_rule.rule
        rule_dict = rule.model_dump(by_alias=True, exclude_none=True)
        conditions_data = rule_dict['conditions']
        failing_entities = []
        all_failures = []

        root_condition = ConditionFactory.create_condition(conditions_data)
        if root_condition is None:
            logger.warning(f"Invalid conditions in rule '{rule.name}'")
            return False, entities, [FailureInfo(operator="invalid", path="conditions")]

        for entity in entities:
            entity_passes, failures = root_condition.evaluate_with_details(entity)

            if not entity_passes and failures:
                failing_entities.append(entity)
                all_failures.extend(failures)

        success = len(failing_entities) == 0
        return success, failing_entities, all_failures

    @staticmethod
    def evaluate_data(data: dict, stored_rules: list[SpikeStoredRule], entity_type: str) -> list[RuleResult]:
        """
        Evaluate rules against the provided data.

        Args:
            data: Data dictionary to evaluate
            rules: List of rules to evaluate
            entity_type: Entity type to extract from the data

        Returns:
            List of RuleResult objects
        """
        results = []

        entities = PathUtils.extract_entity_list(data, entity_type)

        if not entities:
            logger.warning(f"No entities of type '{entity_type}' found in the data")
            return results

        for stored_rule in stored_rules:
            try:
                success, failing_entities, failure_details = RuleEvaluator.evaluate_rule_for_entities(entities, stored_rule)

                if success:
                    message = "All entities fulfill the rule"
                else:
                    message = f"{len(failing_entities)} of {len(entities)} entities do not fulfill the rule"

                rule_name = stored_rule.rule_name
                result = RuleResult(
                    rule_name=rule_name,
                    success=success,
                    message=message,
                    input_data=stored_rule,
                    failing_elements=failing_entities,
                    failure_details=failure_details
                )

                results.append(result)

            except Exception as e:
                logger.error(f"Error evaluating rule '{rule_name}': {e}")
                result = RuleResult(
                    rule_name=rule_name,
                    success=False,
                    message=f"Error evaluating rule: {str(e)}",
                    input_data=stored_rule,
                    failure_details=[FailureInfo(operator="error", path=str(e))]
                )
                results.append(result)

        return results
