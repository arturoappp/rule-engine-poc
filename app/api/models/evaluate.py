"""
API models for data evaluation.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

from app.api.models.rules import Rule


class EvaluationRequest(BaseModel):
    """Request model for evaluating data against rules."""
    data: Dict[str, Any]
    entity_type: str
    categories: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_type": "device",
                    "categories": ["version"],
                    "data": {
                        "devices": [
                            {
                                "vendor": "Cisco Systems",
                                "osVersion": "17.3.6",
                                "mgmtIP": "192.168.1.1"
                            }
                        ]
                    }
                }
            ]
        }
    }


class EvaluationWithRulesRequest(BaseModel):
    """Request model for evaluating data against provided rules."""
    data: Dict[str, Any]
    entity_type: str
    rules: List[Rule]

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "entity_type": "device",
                    "rules": [
                        {
                            "name": "All Devices Must Have Management IP",
                            "conditions": {
                                "all": [
                                    {
                                        "path": "$.devices[*].mgmtIP",
                                        "operator": "exists",
                                        "value": True
                                    }
                                ]
                            }
                        }
                    ],
                    "data": {
                        "devices": [
                            {
                                "vendor": "Cisco Systems",
                                "osVersion": "17.3.6",
                                "mgmtIP": "192.168.1.1"
                            }
                        ]
                    }
                }
            ]
        }
    }


class FailureDetail(BaseModel):
    """Model for detailed failure information."""
    operator: Optional[str] = None
    path: Optional[str] = None
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None


class RuleEvaluationResult(BaseModel):
    """Model for a rule evaluation result."""
    rule_name: str
    success: bool
    message: str
    failing_elements: List[Dict[str, Any]] = Field(default_factory=list)
    failure_details: List[FailureDetail] = Field(default_factory=list)


class EvaluationResponse(BaseModel):
    """Response model for evaluation requests."""
    entity_type: str
    categories: Optional[List[str]] = None
    total_rules: int
    passed_rules: int
    failed_rules: int
    results: List[RuleEvaluationResult]
