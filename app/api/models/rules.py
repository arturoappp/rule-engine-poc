"""
API models for rule management.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Dict, List, Any, Optional, Union, ClassVar


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
        "populate_by_name": True,  # Nueva sintaxis para Pydantic v2
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

        # Asegurar que al menos un tipo de condición esté presente
        condition_types = ["path", "all", "any", "none", "not_"]
        if not any(k in data for k in condition_types):
            data = {"path": None, "operator": None, "value": None}

        # Validar listas de condiciones
        for key in ["all", "any", "none"]:
            if key in data and data[key] is not None:
                if not isinstance(data[key], list):
                    data[key] = []
                elif len(data[key]) == 0:
                    # Asegurar que no haya listas vacías
                    data.pop(key)

        return data

    def model_dump(self, **kwargs):
        """Customize the model dump to handle empty conditions."""
        data = super().model_dump(**kwargs)

        # Eliminar campos nulos o listas vacías
        return {k: v for k, v in data.items() if v is not None and (not isinstance(v, list) or len(v) > 0)}


# Forward reference resolution for recursive model
RuleCondition.model_rebuild()


class Rule(BaseModel):
    """Model for a rule."""
    name: str
    description: Optional[str] = None
    conditions: RuleCondition
    category: Optional[str] = "default"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Cisco Version Rule",
                    "description": "Ensures Cisco devices are running the required OS version",
                    "conditions": {
                        "any": [
                            {
                                "path": "$.devices[*].vendor",
                                "operator": "not_equal",
                                "value": "Cisco Systems"
                            },
                            {
                                "all": [
                                    {
                                        "path": "$.devices[*].vendor",
                                        "operator": "equal",
                                        "value": "Cisco Systems"
                                    },
                                    {
                                        "path": "$.devices[*].osVersion",
                                        "operator": "equal",
                                        "value": "17.3.6"
                                    }
                                ]
                            }
                        ]
                    }
                }
            ]
        }
    }

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v):
        """Validate that name is not empty."""
        if not v.strip():
            raise ValueError("Rule name must not be empty")
        return v

    def model_dump(self, **kwargs):
        """Customize model dump to ensure conditions are properly formatted."""
        data = super().model_dump(**kwargs)

        # Asegurar que las condiciones estén bien formateadas
        if "conditions" in data and data["conditions"] is not None:
            # Convertir condiciones a formato correcto para el motor de reglas
            if isinstance(data["conditions"], dict) and not any(k in data["conditions"] for k in ["all", "any", "none", "not", "path"]):
                # Si no hay ninguna condición definida, crear una estructura por defecto
                data["conditions"] = {"all": []}

        return data


class RuleList(BaseModel):
    """Model for a list of rules."""
    rules: List[Rule]


class RuleValidationResponse(BaseModel):
    """Response model for rule validation."""
    valid: bool
    errors: Optional[List[str]] = None


class RuleStoreRequest(BaseModel):
    """Request model for storing rules."""
    entity_type: str
    category: Optional[str] = "default"
    rules: List[Rule]


class RuleStoreResponse(BaseModel):
    """Response model for storing rules."""
    success: bool
    message: str
    stored_rules: int


class RuleListResponse(BaseModel):
    """Response model for listing rules."""
    entity_types: List[str]
    categories: Dict[str, List[str]]
    rules: Dict[str, Dict[str, List[Rule]]]