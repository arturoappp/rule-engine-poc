"""
Endpoints for rule management.
"""

from typing import List, Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.models.rules import (
    Rule,
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


@router.get("/rules", response_model=RuleListResponse, response_model_exclude_none= True)
async def list_rules(service: RuleService = Depends(get_rule_service)):
    """List all rules in the engine with statistics."""
    rules_by_entity = service.get_rules()

    # Format response
    entity_types = list(rules_by_entity.keys())
    categories = {}
    stats = {}

    # Get categories and statistics for each entity type
    for entity_type, categories_rules in rules_by_entity.items():
        categories[entity_type] = list(categories_rules.keys())

        # Calcular estadísticas
        entity_stats = {
            "total_rules": 0,
            "rules_by_category": {}
        }

        for category, rules_list in categories_rules.items():
            category_rule_count = len(rules_list)
            entity_stats["rules_by_category"][category] = category_rule_count
            entity_stats["total_rules"] += category_rule_count

        stats[entity_type] = entity_stats

    return {
        "entity_types": entity_types,
        "categories": categories,
        "rules": rules_by_entity,
        "stats": stats
    }


@router.get("/rules/export", response_model=Dict)
async def export_rules(
        entity_type: Optional[str] = None,
        category: Optional[str] = None,
        service: RuleService = Depends(get_rule_service)
):
    """Export rules to JSON format."""
    return service.export_rules_to_json(entity_type, category)


@router.get("/rules/history", response_model=List[Dict])
async def get_evaluation_history(
        limit: int = 10,
        service: RuleService = Depends(get_rule_service)
):
    """Get rule evaluation history."""
    return service.get_rule_history(limit)
