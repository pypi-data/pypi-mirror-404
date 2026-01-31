"""Claim schema for RFC 9334 (RATS) compliance.

A Claim represents an individual assertion without a signature. Claims are
bundled into Evidence containers which provide the cryptographic signatures.
This aligns with the RATS architecture where Claims are unsigned assertions
that become Evidence when signed by an Attester.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, field_validator

from .enums import MeasurementType, ComplianceFramework
from .constants import SCHEMA_VERSION_CLAIM

logger = logging.getLogger(__name__)

# Validation limits for the value field (same as Measurement)
MAX_VALUE_SIZE_BYTES = 65536  # 64KB max serialized size
MAX_VALUE_DEPTH = 10  # Maximum nesting depth for dictionaries


class Claim(BaseModel):
    """Individual assertion without signature (RFC 9334 Claim).

    A Claim is the atomic unit of attestation data. It represents a single
    assertion made by an Attester (auditor) about some aspect of the system
    or data being audited.

    Claims do NOT include signatures - they are bundled into Evidence
    containers which provide a single signature covering all claims.
    This is more efficient than signing each claim individually.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_CLAIM

    schema_version: str = Field(
        default=SCHEMA_VERSION_CLAIM,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["2.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    name: str = Field(
        ...,
        description="Claim name using dot notation (e.g. 'toxicity.score', 'pii.detected').",
        examples=["toxicity.score", "pii.detected", "injection.risk_level"]
    )
    type: MeasurementType = Field(
        ...,
        description="The type/category of the claim.",
        examples=["score_normalized", "score_binary"]
    )
    value: Union[str, float, bool, Dict[str, Any]] = Field(
        ...,
        description="The actual claim value/data.",
        examples=[0.85, True, {"category": "toxic", "score": 0.9}]
    )
    timestamp: datetime = Field(
        ...,
        description="Time the claim was generated (UTC).",
        examples=["2025-12-30T20:00:00Z"]
    )
    confidence: float = Field(
        1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 (low) to 1.0 (high).",
        examples=[0.95]
    )
    phase: Optional[str] = Field(
        None,
        description="The execution phase (request, response, artifact, execution, deployment).",
        examples=["request", "response", "deployment"]
    )
    nonce: Optional[str] = Field(
        None,
        description="Optional freshness nonce from the relying party."
    )
    compliance_framework: Optional[ComplianceFramework] = Field(
        None,
        description="Optional mapping to a regulatory framework.",
        examples=["gdpr", "soc2"]
    )
    control_id: Optional[str] = Field(
        None,
        description="Specific section ID in the mapped framework.",
        examples=["Article 5(1)(f)", "CC6.1"]
    )

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

    @field_validator('value')
    @classmethod
    def validate_value_constraints(
        cls, v: Union[str, float, bool, Dict[str, Any]]
    ) -> Union[str, float, bool, Dict[str, Any]]:
        """Validate size and depth constraints for the value field."""
        import json

        def get_depth(obj: Any, current_depth: int = 1) -> int:
            """Calculate the maximum nesting depth of a dictionary."""
            if not isinstance(obj, dict):
                return current_depth
            if not obj:
                return current_depth
            return max(get_depth(val, current_depth + 1) for val in obj.values())

        # Check depth for dict values
        if isinstance(v, dict):
            depth = get_depth(v)
            if depth > MAX_VALUE_DEPTH:
                raise ValueError(
                    f'value exceeds maximum depth of {MAX_VALUE_DEPTH} (found depth: {depth})'
                )

        # Check serialized size
        try:
            serialized = json.dumps(v)
            if len(serialized.encode('utf-8')) > MAX_VALUE_SIZE_BYTES:
                raise ValueError(
                    f'value exceeds maximum size of {MAX_VALUE_SIZE_BYTES} bytes'
                )
        except (TypeError, ValueError) as e:
            if 'exceeds maximum' in str(e):
                raise
            raise ValueError(f'value must be JSON serializable: {e}')

        return v
