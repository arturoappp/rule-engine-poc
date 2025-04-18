"""
Endpoints for rule management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from pydantic import BaseModel

from app.api.models.rules import (
    Rule,
    RuleList,
    RuleValidationResponse,
    RuleStoreRequest,
    RuleStoreResponse,
    RuleListResponse
)
from app.services.rule_service import RuleService

router = APIRouter()


def get_rule_service() -> RuleService:
    """Dependency for the rule service."""
    return RuleService()


@router.post("/rules/validate", response_model=RuleValidationResponse)
async def validate_rule(rule: Rule, service: RuleService = Depends(get_rule_service)):
    """Validate a rule."""
    valid, errors = service.validate_rule(rule)
    return {
        "valid": valid,
        "errors": errors
    }


@router.post("/rules", response_model=RuleStoreResponse)
async def store_rules(request: RuleStoreRequest, service: RuleService = Depends(get_rule_service)):
    """Store rules in the engine."""
    success, message, stored_count = service.store_rules(
        entity_type=request.entity_type,
        rules=request.rules,
        category=request.category
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    return {
        "success": success,
        "message": message,
        "stored_rules": stored_count
    }


@router.get("/rules", response_model=RuleListResponse, response_model_exclude_none=True)
async def list_rules(service: RuleService = Depends(get_rule_service)):
    """List all rules in the engine."""
    rules_by_entity = service.get_rules()

    # Format response
    entity_types = list(rules_by_entity.keys())
    categories = {}

    # Get categories for each entity type
    for entity_type, categories_rules in rules_by_entity.items():
        categories[entity_type] = list(categories_rules.keys())
   
    responseModel = RuleListResponse(entity_types=entity_types, categories=categories, rules=rules_by_entity)

    return responseModel