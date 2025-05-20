"""
Endpoints for data evaluation.
"""

from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.evaluate import (
    EvaluationRequest,
    EvaluationWithRulesRequest,
    EvaluationResponse,
    RuleEvaluationResult,
    FailureDetail, DataEvaluationResponse
)
from app.helpers.helper import entity_matches
from app.services.rule_service import RuleService
from app.utilities.logging import logger

router = APIRouter()


def get_rule_service() -> RuleService:
    """Dependency for the rule service."""
    return RuleService()


@router.post("/evaluate/by-data", response_model=DataEvaluationResponse)
async def evaluate_data_by_item(request: EvaluationRequest, service: RuleService = Depends(get_rule_service)):
    """
    Evaluate data against stored rules, organizing results by data item rather than by rule.

    For each data item, shows which rules passed and which rules failed with their details.
    Rules can be filtered by categories or specific rule names.
    At least one of categories or rule_names must be provided.
    """
    categories_str = ", ".join(request.categories) if request.categories else "None"
    rule_names_str = ", ".join(request.rule_names) if request.rule_names else "None"
    logger.params.set(
        entity_type=request.entity_type,
        category=categories_str
    )

    logger.info(
        f"Evaluating data by item for entity_type={request.entity_type}, categories={categories_str}, rule_names={rule_names_str}")

    try:
        if request.categories is None and request.rule_names is None:
            logger.warning("Request missing both categories and rule_names")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'categories' or 'rule_names' must be provided"
            )

        results = service.evaluate_data_with_criteria(
            data=request.data,
            entity_type=request.entity_type,
            categories=request.categories,
            rule_names=request.rule_names
        )

        if not results:
            logger.info("No rules evaluated for request")
            return {
                "entity_type": request.entity_type,
                "categories": request.categories,
                "rule_names": request.rule_names,
                "total_rules": 0,
                "results": []
            }

        entity_key = f"{request.entity_type}s" if not request.entity_type.endswith('s') else request.entity_type

        all_entities = []
        if entity_key in request.data and isinstance(request.data[entity_key], list):
            all_entities = request.data[entity_key]
        elif request.entity_type in request.data and isinstance(request.data[request.entity_type], list):
            all_entities = request.data[request.entity_type]

        if not all_entities:
            logger.warning(f"No entities found in data for entity_type={request.entity_type}")
            return {
                "entity_type": request.entity_type,
                "categories": request.categories,
                "rule_names": request.rule_names,
                "total_rules": len(results),
                "results": []
            }

        data_evaluation_results = []

        for entity in all_entities:
            rules_passed = []
            rules_failed = []

            for result in results:
                entity_failed = False
                for failing_elem in result.failing_elements:
                    if entity_matches(entity, failing_elem):
                        entity_failed = True
                        break

                if entity_failed:
                    failure_details = [
                        FailureDetail(
                            operator=detail.operator,
                            path=detail.path,
                            expected_value=detail.expected_value,
                            actual_value=detail.actual_value
                        ) for detail in result.failure_details
                    ]

                    rule_failure = {
                        "rule_name": result.rule_name,
                        "failure_details": failure_details
                    }

                    rules_failed.append(rule_failure)
                else:
                    rules_passed.append(result.rule_name)

            evaluation_summary = {
                "rules_passed": len(rules_passed),
                "rules_failed": len(rules_failed)
            }

            data_evaluation_results.append({
                "data": entity,
                "evaluation_summary": evaluation_summary,
                "rules_passed": rules_passed,
                "rules_failed": rules_failed
            })

        logger.info(
            f"Data evaluation completed: {len(results)} rules processed for {len(data_evaluation_results)} entities")

        return {
            "entity_type": request.entity_type,
            "categories": request.categories,
            "rule_names": request.rule_names,
            "total_rules": len(results),
            "results": data_evaluation_results
        }

    except Exception as e:
        logger.error(f"Error evaluating data by item: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_data(request: EvaluationRequest, service: RuleService = Depends(get_rule_service)):
    """
    Evaluate data against stored rules.

    Rules can be filtered by categories or specific rule names.
    At least one of categories or rule_names must be provided.
    """
    categories_str = ", ".join(request.categories) if request.categories else "None"
    rule_names_str = ", ".join(request.rule_names) if request.rule_names else "None"
    logger.params.set(
        entity_type=request.entity_type,
        category=categories_str
    )

    logger.info(
        f"Evaluating data for entity_type={request.entity_type}, categories={categories_str}, rule_names={rule_names_str}")

    try:
        # Validate that at least one filtering criteria is present
        if request.categories is None and request.rule_names is None:
            logger.warning("Request missing both categories and rule_names")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one of 'categories' or 'rule_names' must be provided"
            )

        # Use the new method to evaluate data with criteria
        results = service.evaluate_data_with_criteria(
            data=request.data,
            entity_type=request.entity_type,
            categories=request.categories,
            rule_names=request.rule_names
        )

        if not results:
            logger.info("No rules evaluated for request")
            return {
                "entity_type": request.entity_type,
                "categories": request.categories,
                "rule_names": request.rule_names,
                "total_rules": 0,
                "passed_rules": 0,
                "failed_rules": 0,
                "results": []
            }

        # Convert results to response format
        evaluation_results = []
        passed_count = 0

        for result in results:
            failure_details = [
                FailureDetail(
                    operator=detail.operator,
                    path=detail.path,
                    expected_value=detail.expected_value,
                    actual_value=detail.actual_value
                ) for detail in result.failure_details
            ]

            evaluation_result = RuleEvaluationResult(
                rule_name=result.rule_name,
                success=result.success,
                message=result.message,
                failing_elements=result.failing_elements,
                failure_details=failure_details
            )

            evaluation_results.append(evaluation_result)

            if result.success:
                passed_count += 1

        logger.info(
            f"Evaluation completed: {len(results)} rules processed, {passed_count} passed, {len(results) - passed_count} failed")

        return {
            "entity_type": request.entity_type,
            "categories": request.categories,
            "rule_names": request.rule_names,
            "total_rules": len(results),
            "passed_rules": passed_count,
            "failed_rules": len(results) - passed_count,
            "results": evaluation_results
        }

    except Exception as e:
        logger.error(f"Error evaluating data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.post("/evaluate/with-rules", response_model=EvaluationResponse)
async def evaluate_with_rules(request: EvaluationWithRulesRequest, service: RuleService = Depends(get_rule_service)):
    """Evaluate data against provided rules."""
    # Set context for logging
    logger.params.set(entity_type=request.entity_type)
    logger.info(f"Evaluating data against {len(request.rules)} provided rules for entity_type={request.entity_type}")

    try:
        results = service.evaluate_with_rules(
            data=request.data,
            entity_type=request.entity_type,
            api_rules=request.rules
        )

        # Convert results to response format
        evaluation_results = []
        passed_count = 0

        for result in results:
            failure_details = [
                FailureDetail(
                    operator=detail.operator,
                    path=detail.path,
                    expected_value=detail.expected_value,
                    actual_value=detail.actual_value
                ) for detail in result.failure_details
            ]

            evaluation_result = RuleEvaluationResult(
                rule_name=result.rule_name,
                success=result.success,
                message=result.message,
                failing_elements=result.failing_elements,
                failure_details=failure_details
            )

            evaluation_results.append(evaluation_result)

            if result.success:
                passed_count += 1

        logger.info(
            f"Evaluation with provided rules completed: {len(results)} rules processed, {passed_count} passed, {len(results) - passed_count} failed")

        return {
            "entity_type": request.entity_type,
            "categories": None,
            "total_rules": len(results),
            "passed_rules": passed_count,
            "failed_rules": len(results) - passed_count,
            "results": evaluation_results
        }

    except Exception as e:
        logger.error(f"Error evaluating data with provided rules: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.get("/evaluate/stats", response_model=Dict[str, Any])
async def get_evaluation_stats(service: RuleService = Depends(get_rule_service)):
    """Get statistics about rule evaluations."""
    logger.info("Getting evaluation statistics")
    stats = service.get_evaluation_stats()
    total_rules = stats.get("total_rules", 0)
    entity_types = len(stats.get("entity_types", []))
    logger.info(f"Retrieved statistics: {total_rules} total rules across {entity_types} entity types")
    return stats


@router.get("/evaluate/failure-details/{rule_name}", response_model=Dict[str, Any])
async def get_rule_failure_details(
        rule_name: str,
        entity_type: Optional[str] = None,
        service: RuleService = Depends(get_rule_service)
):
    """Get detailed information about failures for a specific rule."""
    logger.params.set(rule_name=rule_name, entity_type=entity_type)
    logger.info(
        f"Getting failure details for rule '{rule_name}'{f', entity_type={entity_type}' if entity_type else ''}")

    details = service.get_rule_failure_details(rule_name, entity_type)

    if details.get("found", False):
        logger.info(f"Found rule '{rule_name}', returning failure details")
    else:
        logger.warning(f"Rule '{rule_name}' not found")

    return details
