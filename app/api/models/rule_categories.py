from pydantic import BaseModel, field_validator


class RuleCategoriesRequest(BaseModel):
    """Request model for rule categories endpoint."""
    rule_name: str
    entity_type: str
    categories: list[str]
    category_action: str  # 'add' or 'remove'

    @field_validator("category_action", mode="before")
    @classmethod
    def validate_category_action(cls, value):
        if value.lower() not in {"add", "remove"}:
            raise ValueError("category_action must be 'add' or 'remove' (case-insensitive).")
        return value.lower()


class RuleCategoriesResponse(BaseModel):
    """Response model for rule categories endpoint."""
    id: int
    name: str
    description: str