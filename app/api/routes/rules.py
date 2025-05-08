"""
Endpoints for rule management.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.models.rules import (
    RuleValidationResponse,
    RuleStoreRequest,
    RuleStoreResponse,
    RuleListRequest,
    RuleListResponse,
    RuleStoreRequest,
    Rule
)
from app.services.rule_service import RuleService
from app.helpers.response_formatter import format_list_rules_response
from app.utilities.logging import logger

router = APIRouter()


def get_rule_service() -> RuleService:
    """Dependency for the rule service."""
    return RuleService()


@router.post("/rules/validate", response_model=RuleValidationResponse)
async def validate_rule(rule: Rule, service: RuleService = Depends(get_rule_service)):
    """Validate a rule."""
    logger.params.set(rule_name=rule.name)
    logger.info(f"Validating rule '{rule.name}'")

    valid, errors = service.validate_rule(rule)

    if valid:
        logger.info(f"Rule '{rule.name}' is valid")
    else:
        logger.warning(f"Rule '{rule.name}' validation failed with errors: {errors}")

    return {
        "valid": valid,
        "errors": errors
    }


@router.post("/rules", response_model=RuleStoreResponse)
async def store_rules(request: RuleStoreRequest, service: RuleService = Depends(get_rule_service)):
    """Store rules in the engine."""
    logger.params.set(entity_type=request.entity_type)
    logger.info(f"Processing request to store {len(request.rules)} rules for entity type '{request.entity_type}'")

    success, message, stored_count = service.store_rules(
        entity_type=request.entity_type,
        rules=request.rules,
    )

    if not success:
        logger.error(f"Failed to store spike rules: {message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    logger.info(f"Successfully stored {stored_count} rules for entity type '{request.entity_type}'")
    return {
        "success": success,
        "message": message,
        "stored_rules": stored_count
    }


@router.get("/rules", response_model=RuleListResponse, response_model_exclude_none=True)
async def list_rules(rule_list_request: Annotated[RuleListRequest, Query()],
                     service: RuleService = Depends(get_rule_service)):
    """List all rules in the engine."""
    entity_type = rule_list_request.entity_type
    categories = rule_list_request.categories

    logger.params.set(
        entity_type=entity_type,
        category=','.join(categories) if categories else None
    )

    filter_desc = []
    if entity_type:
        filter_desc.append(f"entity_type='{entity_type}'")
    if categories:
        filter_desc.append(f"categories={categories}")

    filter_str = " and ".join(filter_desc) if filter_desc else "no filters"
    logger.info(f"Listing rules with {filter_str}")

    rules_by_entity = service.get_rules(entity_type, categories)
    response_model = format_list_rules_response(rules_by_entity)

    entity_count = len(response_model.entity_types)
    rule_count = sum(stat.total_rules for stat in response_model.stats.values())
    logger.info(f"Returning {rule_count} rules across {entity_count} entity types")

    return response_model
