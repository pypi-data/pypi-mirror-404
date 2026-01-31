from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .constants import SCHEMA_VERSION_EVALUATION

logger = logging.getLogger(__name__)


class EvaluationResult(BaseModel):
    """Result from a pre-deployment evaluation (e.g., Petri)"""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_EVALUATION

    schema_version: str = Field(
        default=SCHEMA_VERSION_EVALUATION,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    evaluation_id: str = Field(..., description="Unique ID for this evaluation.")
    evaluator: str = Field(..., description="Name of the evaluation tool (e.g., 'petri').")
    evaluator_version: str = Field(..., description="Version of the evaluator.")
    timestamp: datetime = Field(..., description="Time of evaluation.")

    @field_validator('schema_version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate schema version and log warnings for mismatches."""
        expected = cls._expected_version
        if v != expected:
            logger.warning(
                "Schema version mismatch for %s: got '%s', expected '%s'",
                cls.__name__, v, expected
            )
        return v

    model_id: str = Field(..., description="Identifier of the model being evaluated.")
    model_hash: str = Field(..., description="Cryptographic hash of the model weights.")

    passed: bool = Field(..., description="Whether the evaluation passed its safety thresholds.")
    scores: Dict[str, float] = Field(default_factory=dict, description="Detailed safety scores.")
    findings: List[Dict[str, Any]] = Field(default_factory=list, description="Specific safety violations found.")
    tee_quote: Optional[str] = Field(None, description="Hardware-signed proof of the evaluation run.")

    model_config = ConfigDict(protected_namespaces=())
