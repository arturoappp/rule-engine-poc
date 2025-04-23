"""
Endpoints for rule management.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.models.rules import (
    Rule,
    RuleListRequest,
    RuleValidationResponse,
    RuleStoreRequest,
    RuleStoreResponse,
    RuleListResponse
)
from app.services.rule_service import RuleService
from app.utilities.response_formatter import format_list_rules_response

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
        default_category=request.default_category
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
async def list_rules(rule_list_request: Annotated[RuleListRequest, Query()], service: RuleService = Depends(get_rule_service)):
    """List all rules in the engine."""
    entity_type = rule_list_request.entity_type
    category = rule_list_request.category
    rules_by_entity = service.get_rules(entity_type, category)
    responseModel = format_list_rules_response(rules_by_entity)

    return responseModel
