from app.api.models.rule_categories import RuleCategoriesRequest, RuleCategoriesResponse
from fastapi import APIRouter, Depends, status

from app.api.routes.rules import get_rule_service
from app.services.rule_service import RuleService

router = APIRouter()


@router.post("/rule-categories", response_model=RuleCategoriesResponse, status_code=status.HTTP_200_OK)
async def update_rule_categories(request: RuleCategoriesRequest, service: RuleService = Depends(get_rule_service)):
    """Update rule categories."""
    success, message = service.update_rule_categories(
        rule_name=request.rule_name,
        entity_type=request.entity_type,
        categories=request.categories,
        category_action=request.category_action,
    )

    return RuleCategoriesResponse(success=success, message=message)
