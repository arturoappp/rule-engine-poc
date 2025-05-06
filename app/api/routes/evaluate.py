"""
Endpoints for data evaluation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any

from app.api.models.evaluate import (
    EvaluationRequest,
    EvaluationWithRulesRequest,
    EvaluationResponse,
    RuleEvaluationResult,
    FailureDetail
)
from app.services.rule_service import RuleService

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
    try:
        # Validate that at least one filtering criteria is present
        if request.categories is None and request.rule_names is None:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.post("/evaluate/with-rules", response_model=EvaluationResponse)
async def evaluate_with_rules(request: EvaluationWithRulesRequest, service: RuleService = Depends(get_rule_service)):
    """Evaluate data against provided rules."""
    try:
        results = service.evaluate_with_rules(
            data=request.data,
            entity_type=request.entity_type,
            rules=request.rules
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

        return {
            "entity_type": request.entity_type,
            "categories": None,
            "total_rules": len(results),
            "passed_rules": passed_count,
            "failed_rules": len(results) - passed_count,
            "results": evaluation_results
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.get("/evaluate/stats", response_model=Dict[str, Any])
async def get_evaluation_stats(service: RuleService = Depends(get_rule_service)):
    """Get statistics about rule evaluations."""
    return service.get_evaluation_stats()


@router.get("/evaluate/failure-details/{rule_name}", response_model=Dict[str, Any])
async def get_rule_failure_details(
    rule_name: str,
    entity_type: Optional[str] = None,
    service: RuleService = Depends(get_rule_service)
):
    """Get detailed information about failures for a specific rule."""
    return service.get_rule_failure_details(rule_name, entity_type)
