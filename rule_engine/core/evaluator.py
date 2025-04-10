"""
Module containing the rule evaluation logic.
"""

import logging
from typing import Dict, List, Tuple, Optional

from rule_engine.conditions.conditions_factory import ConditionFactory
from rule_engine.core.rule_result import RuleResult, FailureInfo
from rule_engine.utils.path_utils import PathUtils

# Logging configuration
logger = logging.getLogger(__name__)


class RuleEvaluator:
    """Class responsible for evaluating rules against data."""

    @staticmethod
    def evaluate_rule_for_entities(entities: List[Dict], rule: Dict) -> Tuple[bool, List[Dict], List[FailureInfo]]:
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
        if 'conditions' not in rule:
            logger.warning(f"Rule '{rule.get('name', 'Unnamed')}' has no conditions")
            return False, entities, [FailureInfo(operator="missing", path="conditions")]

        conditions_data = rule['conditions']
        failing_entities = []
        all_failures = []

        # Create the root condition
        root_condition = ConditionFactory.create_condition(conditions_data)
        if root_condition is None:
            logger.warning(f"Invalid conditions in rule '{rule.get('name', 'Unnamed')}'")
            return False, entities, [FailureInfo(operator="invalid", path="conditions")]

        for entity in entities:
            # Evaluate the conditions for this entity with details
            entity_passes, failures = root_condition.evaluate_with_details(entity)

            # If the entity doesn't pass, add it to the list of failures
            if not entity_passes and failures:
                failing_entities.append(entity)
                all_failures.extend(failures)

        # The rule passes if all entities pass (none fail)
        success = len(failing_entities) == 0
        return success, failing_entities, all_failures

    @staticmethod
    def evaluate_data(data: Dict, rules: List[Dict], entity_type: str) -> List[RuleResult]:
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

        # Extract the entity list
        entities = PathUtils.extract_entity_list(data, entity_type)

        if not entities:
            logger.warning(f"No entities of type '{entity_type}' found in the data")
            return results

        # Evaluate each rule against all entities
        for rule in rules:
            rule_name = rule.get("name", "Unnamed Rule")

            try:
                # Evaluate the rule for all entities
                success, failing_entities, failure_details = RuleEvaluator.evaluate_rule_for_entities(entities, rule)

                # Create result message
                if success:
                    message = "All entities fulfill the rule"
                else:
                    message = f"{len(failing_entities)} of {len(entities)} entities do not fulfill the rule"

                # Create RuleResult object
                result = RuleResult(
                    rule_name=rule_name,
                    success=success,
                    message=message,
                    input_data=rule,
                    failing_elements=failing_entities,
                    failure_details=failure_details
                )

                results.append(result)

            except Exception as e:
                # If there's an error evaluating, log it and create an error result
                logger.error(f"Error evaluating rule '{rule_name}': {e}")
                result = RuleResult(
                    rule_name=rule_name,
                    success=False,
                    message=f"Error evaluating rule: {str(e)}",
                    input_data=rule,
                    failure_details=[FailureInfo(operator="error", path=str(e))]
                )
                results.append(result)

        return results