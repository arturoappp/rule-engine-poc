from app.api.models.rule_categories import RuleCategoriesRequest, RuleCategoriesResponse
from fastapi import APIRouter, Depends, status, HTTPException
from app.utilities.logging import logger  # Import the logger

from app.api.routes.rules import get_rule_service
from app.services.rule_service import RuleService

router = APIRouter()


@router.post("/rule-categories", response_model=RuleCategoriesResponse, status_code=status.HTTP_200_OK)
async def update_rule_categories(request: RuleCategoriesRequest, service: RuleService = Depends(get_rule_service)):
    """Update rule categories."""
    # Set context for logging
    logger.params.set(
        entity_type=request.entity_type,
        rule_name=request.rule_name,
        category=','.join(request.categories) if request.categories else None
    )

    logger.info(
        f"Request to {request.category_action} categories for rule '{request.rule_name}' (entity_type: '{request.entity_type}')")
    logger.debug(f"Categories to {request.category_action}: {request.categories}")

    success, message = service.update_rule_categories(
        rule_name=request.rule_name,
        entity_type=request.entity_type,
        categories=request.categories,
        category_action=request.category_action,
    )

    if success:
        logger.info(f"Successfully {request.category_action}ed categories for rule '{request.rule_name}'")
    else:
        logger.warning(f"Failed to {request.category_action} categories for rule '{request.rule_name}': {message}")

    return RuleCategoriesResponse(success=success, message=message)
