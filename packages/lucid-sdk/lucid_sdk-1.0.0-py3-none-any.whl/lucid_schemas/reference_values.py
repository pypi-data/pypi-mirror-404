"""Reference Values for attestation verification.

Reference Values are provided by device manufacturers (Reference Value Providers
in RATS terminology) and contain the "golden measurements" expected from genuine,
unmodified hardware.

This module defines schemas for CoRIM (Concise Reference Integrity Manifest)
per draft-ietf-rats-corim specification.

Standards:
    - IETF draft-ietf-rats-corim (Concise Reference Integrity Manifest)
    - IETF RFC 9334 (RATS Architecture)
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, List, Optional
from pydantic import BaseModel, Field, field_validator

from .enums import EvidenceSource
from .constants import SCHEMA_VERSION_REFERENCE_VALUES

logger = logging.getLogger(__name__)


class CoRIMEnvironment(BaseModel):
    """Target environment for reference values."""
    vendor: str = Field(..., description="Hardware vendor (e.g., 'NVIDIA', 'Intel')")
    model: str = Field(..., description="Hardware model (e.g., 'H100', 'DC-SCM-v2')")
    firmware_version: Optional[str] = Field(None, description="Firmware version string")
    hardware_revision: Optional[str] = Field(None, description="Hardware revision")


class CoRIMMeasurement(BaseModel):
    """Expected measurement value (golden measurement)."""
    index: int = Field(..., ge=0, description="Measurement index")
    digest_algorithm: str = Field(..., description="Hash algorithm: sha256, sha384, sha512")
    expected_value: str = Field(..., description="Base64-encoded expected digest")
    description: Optional[str] = Field(None, description="Human-readable description")


class CoRIM(BaseModel):
    """Concise Reference Integrity Manifest (CoRIM) for verification.

    CoRIMs are provided by device manufacturers (NVIDIA, Intel, AMD) and
    contain the "golden measurements" expected from genuine, unmodified hardware.
    The Verifier compares Evidence against these Reference Values.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_REFERENCE_VALUES

    schema_version: str = Field(
        default=SCHEMA_VERSION_REFERENCE_VALUES,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    corim_id: str = Field(..., description="Unique manifest identifier")

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
    issued_at: datetime = Field(..., description="When the manifest was issued")
    expires_at: Optional[datetime] = Field(None, description="When the manifest expires")

    # Device identification
    device_type: EvidenceSource = Field(..., description="Type of device this CoRIM applies to")
    environment: CoRIMEnvironment = Field(..., description="Target hardware environment")

    # Expected measurements (golden values)
    measurements: List[CoRIMMeasurement] = Field(
        default_factory=list,
        description="List of expected measurement values"
    )

    # Signing (manufacturer signature required)
    issuer: str = Field(..., description="Manufacturer or Reference Value Provider identifier")
    signature: str = Field(..., description="Cryptographic signature over manifest")
