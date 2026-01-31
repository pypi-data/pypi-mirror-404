"""Interaction receipt schemas for user verification.

Signed receipts provide users with verifiable proof of their evidence submissions.
Users can independently verify receipts via the public verification endpoint.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, Optional
from pydantic import BaseModel, Field, field_validator

from .constants import SCHEMA_VERSION_RECEIPT

logger = logging.getLogger(__name__)


class InteractionReceipt(BaseModel):
    """Signed receipt for user verification.

    This receipt is returned as part of the AI Passport response when users
    submit evidence. It contains cryptographic proof that the evidence was
    processed by the verifier.
    """
    model_config = {"protected_namespaces": ()}

    _expected_version: ClassVar[str] = SCHEMA_VERSION_RECEIPT

    schema_version: str = Field(
        default=SCHEMA_VERSION_RECEIPT,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    receipt_id: str = Field(..., description="Unique identifier for this receipt")

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
    passport_id: str = Field(..., description="ID of the associated AI Passport")
    request_hash: str = Field(..., description="SHA-256 hash of the original request")
    response_hash: str = Field(..., description="SHA-256 hash of the passport response")
    issued_at: datetime = Field(..., description="Timestamp when the receipt was issued")
    model_id: str = Field(..., description="ID of the model that processed the evidence")
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    measurement_count: int = Field(0, description="Number of measurements in the evidence")
    verifier_id: str = Field("lucid-verifier", description="ID of the verifier that issued the receipt")
    signature: str = Field(..., description="Cryptographic signature of the receipt data")
    is_mock: bool = Field(False, description="True if this receipt was generated in development mode")


class ReceiptVerifyResponse(BaseModel):
    """Response from receipt verification endpoint.

    This is returned by the public GET /v1/receipts/{receipt_id} endpoint
    when users verify their receipts.
    """
    receipt_id: str = Field(..., description="The receipt ID that was verified")
    valid: bool = Field(..., description="True if the receipt signature is valid")
    verified_at: datetime = Field(..., description="Timestamp when verification was performed")
    passport_id: Optional[str] = Field(None, description="Associated passport ID (if valid)")
    issued_at: Optional[datetime] = Field(None, description="Original issue timestamp (if valid)")
    error: Optional[str] = Field(None, description="Error message if verification failed")
