"""
Endpoints for data evaluation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, Dict, Any

from app.api.models.evaluate import (
    EvaluationRequest,
    EvaluationWithRulesRequest,
    EvaluationResponse,
    RuleEvaluationResult,
    FailureDetail
)
from app.services.rule_service import RuleService
from app.utilities.logging import logger

router = APIRouter()


def get_rule_service() -> RuleService:
    """Dependency for the rule service."""
    return RuleService()


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
