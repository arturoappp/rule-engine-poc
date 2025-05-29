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
    FailureDetail, DataEvaluationResponse, EvaluationWithRulesResponse
)
from app.helpers.helper import extract_entities, organize_results_by_entity
from app.services.rule_service import RuleService
from app.utilities.logging import logger

router = APIRouter()


def get_rule_service() -> RuleService:
    """Dependency for the rule service."""
    return RuleService()


@router.post("/evaluate", response_model=DataEvaluationResponse)
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

        all_entities = extract_entities(request.data, request.entity_type)

        if not all_entities:
            logger.warning(f"No entities found in data for entity_type={request.entity_type}")
            return DataEvaluationResponse(
                entity_type=request.entity_type,
                categories=request.categories,
                rule_names=request.rule_names,
                total_rules=0,
                total_data_objects=0,
                results=[]
            )

        all_results = service.evaluate_data_with_criteria(
            data=request.data,
            entity_type=request.entity_type,
            categories=request.categories,
            rule_names=request.rule_names
        )

        if not all_results:
            logger.info("No rules evaluated for request")
            return DataEvaluationResponse(
                entity_type=request.entity_type,
                categories=request.categories,
                rule_names=request.rule_names,
                total_rules=0,
                total_data_objects=len(all_entities),
                results=[]
            )

        data_evaluation_results = organize_results_by_entity(
            all_entities=all_entities,
            all_results=all_results
        )

        logger.info(
            f"Data evaluation completed: {len(all_results)} rules processed for {len(data_evaluation_results)} entities")

        return DataEvaluationResponse(
            entity_type=request.entity_type,
            categories=request.categories,
            rule_names=request.rule_names,
            total_rules=len(all_results),
            total_data_objects=len(all_entities),
            results=data_evaluation_results
        )

    except Exception as e:
        logger.error(f"Error evaluating data by item: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error evaluating data: {str(e)}"
        )


@router.post("/evaluate/with-rules", response_model=EvaluationWithRulesResponse)
async def evaluate_with_rules_by_data(request: EvaluationWithRulesRequest,
                                      service: RuleService = Depends(get_rule_service)):
    """Evaluate data against provided rules, organizing results by data item."""
    logger.params.set(entity_type=request.entity_type)
    logger.info(
        f"Evaluating data by item against {len(request.rules)} provided rules for entity_type={request.entity_type}")

    try:
        # Validate all rules before evaluation
        validation_errors = []
        for i, rule in enumerate(request.rules):
            logger.info(f"Validating rule '{rule.name}' before evaluation")
            valid, errors = service.validate_rule(rule)

            if not valid:
                logger.warning(f"Rule '{rule.name}' validation failed with errors: {errors}")
                validation_errors.append({
                    "rule_index": i,
                    "rule_name": rule.name,
                    "errors": errors
                })

        # If any rule failed validation, don't proceed with evaluation
        if validation_errors:
            error_message = f"Validation failed for {len(validation_errors)} rule(s)"
            detailed_errors = []
            for error in validation_errors:
                detailed_errors.append(
                    f"Rule '{error['rule_name']}' (index {error['rule_index']}): {', '.join(error['errors'])}")

            full_error_message = f"{error_message}. Details: {'; '.join(detailed_errors)}"
            logger.error(f"Failed to evaluate data due to rule validation errors: {full_error_message}")

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=full_error_message
            )

        # All rules are valid, proceed with evaluation
        logger.info("All rules passed validation, proceeding with evaluation")

        # Extract entities from data
        all_entities = extract_entities(request.data, request.entity_type)

        if not all_entities:
            logger.warning(f"No entities found in data for entity_type={request.entity_type}")
            return EvaluationWithRulesResponse(
                entity_type=request.entity_type,
                total_rules=len(request.rules),
                total_data_objects=0,
                results=[]
            )

        all_results = service.evaluate_with_rules(
            data=request.data,
            entity_type=request.entity_type,
            api_rules=request.rules
        )

        if not all_results:
            logger.info("No rules evaluated for request")
            return EvaluationWithRulesResponse(
                entity_type=request.entity_type,
                total_rules=len(request.rules),
                total_data_objects=len(all_entities),
                results=[]
            )

        data_evaluation_results = organize_results_by_entity(
            all_entities=all_entities,
            all_results=all_results
        )

        logger.info(
            f"Evaluation with provided rules by data completed: {len(all_results)} rules processed for {len(data_evaluation_results)} entities")

        return EvaluationWithRulesResponse(
            entity_type=request.entity_type,
            total_rules=len(all_results),
            total_data_objects=len(all_entities),
            results=data_evaluation_results
        )

    except Exception as e:
        logger.error(f"Error evaluating data with provided rules by data: {str(e)}", exc_info=True)
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
