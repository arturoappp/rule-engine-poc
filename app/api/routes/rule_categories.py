from app.api.models.rule_categories import RuleCategoriesRequest, RuleCategoriesResponse
from fastapi import APIRouter, status

router = APIRouter()

@router.post("/rule-categories", response_model=RuleCategoriesResponse, status_code=status.HTTP_200_OK)
async def update_rule_categories(request: RuleCategoriesRequest):
    """Update rule categories."""


    return {
        "success": "", 
        "message": "",
    }