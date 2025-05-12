"""
API models for rule management.
"""

from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field, model_validator


class RuleCondition(BaseModel):
    """Model for a rule condition."""
    path: Optional[str] = None
    operator: Optional[str] = None
    value: Optional[Any] = None
    all: Optional[List["RuleCondition"]] = None
    any: Optional[List["RuleCondition"]] = None
    none: Optional[List["RuleCondition"]] = None
    not_: Optional["RuleCondition"] = Field(default=None, alias="not")

    model_config = {
        "populate_by_name": True,  # New syntax for Pydantic v2
        "extra": "ignore",
        "json_schema_extra": {
            "examples": [
                {
                    "path": "$.devices[*].vendor",
                    "operator": "equal",
                    "value": "Cisco Systems"
                }
            ]
        }
    }

    @model_validator(mode='before')
    @classmethod
    def validate_condition_structure(cls, data):
        """Validate the condition structure."""
        if not isinstance(data, dict):
            return data

        # Handle the 'not' alias properly
        if "not" in data and "not_" not in data:
            data["not_"] = data.pop("not")

        # Ensure that at least one condition type is present
        condition_types = ["path", "all", "any", "none", "not_"]
        if not any(k in data for k in condition_types):
            data = {"path": None, "operator": None, "value": None}

        # Validate condition lists
        for key in ["all", "any", "none"]:
            if key in data and data[key] is not None:
                if not isinstance(data[key], list):
                    data[key] = []
                elif len(data[key]) == 0:
                    # Ensure there are no empty lists
                    data.pop(key)

        return data

    def model_dump(self, **kwargs):
        """Customized model_dump to deeply clean null values."""
        # Use the original model_dump
        data = super().model_dump(**kwargs)

        # Recursive function to clean dictionaries
        def clean_dict(d):
            if not isinstance(d, dict):
                return d

            # Clean null values at the current level
            result = {k: v for k, v in d.items() if v is not None}

            # Process nested lists
            for key in ['all', 'any', 'none']:
                if key in result and isinstance(result[key], list):
                    # Clean each list element
                    cleaned_list = []
                    for item in result[key]:
                        if isinstance(item, dict):
                            cleaned_item = clean_dict(item)
                            if cleaned_item and len(cleaned_item) > 0:
                                cleaned_list.append(cleaned_item)

                    # If the list is empty, remove the key
                    if cleaned_list:
                        result[key] = cleaned_list
                    else:
                        result.pop(key, None)

            # Process the "not" condition
            if 'not' in result:
                if isinstance(result['not'], dict):
                    cleaned_not = clean_dict(result['not'])
                    if cleaned_not and len(cleaned_not) > 0:
                        result['not'] = cleaned_not
                    else:
                        result.pop('not', None)

            return result

        # Apply recursive cleaning
        return clean_dict(data)


# Forward reference resolution for recursive model
RuleCondition.model_rebuild()


class APIRule(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    conditions: RuleCondition
    add_to_categories: Optional[List[str]] = []


class Rule(BaseModel):
    name: str
    entity_type: str
    description: Optional[str] = None
    conditions: RuleCondition


class StoredRule(BaseModel):
    rule_name: str
    entity_type: str
    description: Optional[str] = None
    categories: set[str]
    rule: Rule  # The rule itself, can be a complex structure

    def __hash__(self):
        # Use a unique combination of attributes to compute the hash
        return hash((self.rule_name, self.entity_type))

    def __eq__(self, other):
        if not isinstance(other, StoredRule):
            return False
        return self.rule_name == other.rule_name and self.entity_type == other.entity_type


class RuleList(BaseModel):
    """Model for a list of rules."""
    rules: list[Rule]


class RuleListRequest(BaseModel):
    """Request model for a list of rules."""
    entity_type: Optional[str] = None
    categories: Optional[list[str]] = None


class RuleValidationResponse(BaseModel):
    """Response model for rule validation."""
    valid: bool
    errors: Optional[List[str]] = None


class RuleStoreRequest(BaseModel):
    """Request model for storing rules."""
    rules: list[APIRule]


class RuleStoreResponse(BaseModel):
    """Response model for storing rules."""
    success: bool
    message: str
    stored_rules: int


class RuleStats(BaseModel):
    """Model for rule statistics."""
    total_rules: int
    rules_by_category: Dict[str, int]


class RuleListResponse(BaseModel):
    """Response model for listing rules."""
    entity_types: list[str]
    categories: dict[str, list[str]]
    rules: list[Rule]
    stats: dict[str, RuleStats]
