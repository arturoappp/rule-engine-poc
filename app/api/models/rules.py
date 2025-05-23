"""
API models for rule management.
"""

from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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
        """Customized model_dump to deeply clean null values."""
        # Usar el model_dump original
        data = super().model_dump(**kwargs)

        # Función recursiva para limpiar diccionarios
        def clean_dict(d):
            if not isinstance(d, dict):
                return d

            # Limpiar valores nulos en el nivel actual
            result = {k: v for k, v in d.items() if v is not None}

            # Procesar listas anidadas
            for key in ['all', 'any', 'none']:
                if key in result and isinstance(result[key], list):
                    # Limpiar cada elemento de la lista
                    cleaned_list = []
                    for item in result[key]:
                        if isinstance(item, dict):
                            cleaned_item = clean_dict(item)
                            if cleaned_item and len(cleaned_item) > 0:
                                cleaned_list.append(cleaned_item)

                    # Si la lista queda vacía, eliminar la clave
                    if cleaned_list:
                        result[key] = cleaned_list
                    else:
                        result.pop(key, None)

            # Procesar la condición "not"
            if 'not' in result:
                if isinstance(result['not'], dict):
                    cleaned_not = clean_dict(result['not'])
                    if cleaned_not and len(cleaned_not) > 0:
                        result['not'] = cleaned_not
                    else:
                        result.pop('not', None)

            return result

        # Aplicar limpieza recursiva
        return clean_dict(data)


# Forward reference resolution for recursive model
RuleCondition.model_rebuild()


class Rule(BaseModel):
    """Model for a rule."""
    name: str
    description: Optional[str] = None
    conditions: RuleCondition
    categories: Optional[List[str]] = Field(default_factory=lambda: ["default"])

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Cisco Version Rule",
                    "description": "Ensures Cisco devices are running the required OS version",
                    "categories": ["version", "compliance"],
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
        """Customize model dump to remove null values."""
        # No añadimos exclude_none aquí, lo pasamos a través de kwargs
        data = super().model_dump(**kwargs)

        # Asegurar que las condiciones no tengan valores nulos
        if 'conditions' in data and isinstance(data['conditions'], dict):
            # Eliminar atributos nulos de las condiciones
            conditions = {
                k: v for k, v in data['conditions'].items()
                if v is not None
            }
            data['conditions'] = conditions

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
    default_category: Optional[str] = "default"  # Used only if a rule doesn't specify categories
    rules: List[Rule]


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
    entity_types: List[str]
    categories: Dict[str, List[str]]
    rules: Dict[str, Dict[str, List[Rule]]]
    stats: Dict[str, RuleStats]
