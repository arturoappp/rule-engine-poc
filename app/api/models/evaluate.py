"""
API models for data evaluation.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Dict, List, Any, Optional

from app.api.models.rules import Rule


class EvaluationRequest(BaseModel):
    """Request model for evaluating data against rules."""
    data: Dict[str, Any]
    entity_type: str
    categories: Optional[List[str]] = None
    rule_names: Optional[List[str]] = None

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

    @model_validator(mode='after')
    def validate_filtering_criteria(self):
        """Ensure at least one filtering criteria is provided."""
        if self.categories is None and self.rule_names is None:
            raise ValueError("At least one of 'categories' or 'rule_names' must be provided")
        return self


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
    rule_names: Optional[List[str]] = None
    total_rules: int
    passed_rules: int
    failed_rules: int
    results: List[RuleEvaluationResult]

class RuleFailureDetails(BaseModel):
    rule_name: str
    failure_details: List[FailureDetail]


class DataEvaluationSummary(BaseModel):
    rules_passed: int
    rules_failed: int


class DataEvaluationItem(BaseModel):
    data: Dict[str, Any]
    evaluation_summary: DataEvaluationSummary
    rules_passed: List[str]
    rules_failed: List[RuleFailureDetails]


class DataEvaluationResponse(BaseModel):
    entity_type: str
    categories: Optional[List[str]] = None
    rule_names: Optional[List[str]] = None
    total_rules: int
    total_data_objects: int
    results: List[DataEvaluationItem]

class EvaluationWithRulesResponse(BaseModel):
    entity_type: str
    total_rules: int
    total_data_objects: int
    results: List[DataEvaluationItem]
