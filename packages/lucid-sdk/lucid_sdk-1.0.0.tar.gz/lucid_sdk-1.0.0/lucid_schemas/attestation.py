from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, List, Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .enums import HardwareProvider
from .evaluation import EvaluationResult
from .constants import SCHEMA_VERSION_ATTESTATION
from .evidence import Evidence

logger = logging.getLogger(__name__)


class HardwareAttestation(BaseModel):
    """Hardware integrity and platform attestation."""
    attestation_id: str = Field(..., description="Unique ID for this attestation report.")
    timestamp: datetime = Field(..., description="Time report was generated.")

    provider: HardwareProvider = Field(..., description="TEE hardware vendor.")
    tee_type: str = Field(..., description="Specific TEE technology (e.g., 'SEV-SNP', 'TDX').")
    gpu_tee_type: Optional[str] = Field(None, description="Optional GPU TEE info.")

    quote: str = Field(..., description="The raw hardware quote/evidence.")
    verified: bool = Field(False, description="Whether the quote has been verified by the Appraiser.")


class RuntimeStatus(BaseModel):
    """Live status of the auditor chain."""
    active_auditors: List[str] = Field(..., description="List of IDs for currently running auditors.")
    requests_processed: int = Field(0, description="Total AI requests intercepted.")
    requests_blocked: int = Field(0, description="Total requests denied by auditors.")
    requests_redacted: int = Field(0, description="Total requests modified by auditors.")
    signature_digest: Optional[str] = Field(None, description="SHA-256 hash of the signed passport data for verification.")


class RoutingProof(BaseModel):
    """Proof that a request was routed through a specific TEE instance.

    This enables zero-trust verification - customers can independently verify
    that their request was processed by a genuine TEE without trusting Lucid's
    infrastructure. The enclave_signature is created inside the TEE using
    attestation-bound keys.
    """
    tee_instance_id: str = Field(..., description="Unique identifier of the TEE instance that processed the request.")
    environment_id: Optional[str] = Field(None, description="Serverless environment ID (if applicable).")
    timestamp: datetime = Field(..., description="When the request was processed.")
    request_hash: str = Field(..., description="SHA-256 hash of the request that was processed.")
    enclave_signature: str = Field(..., description="Signature created inside the TEE using attestation-bound key.")
    tee_type: str = Field(..., description="Type of TEE (intel_sgx, intel_tdx, amd_sev_snp, aws_nitro).")
    attestation_quote: Optional[str] = Field(None, description="Hardware attestation quote for verification against root of trust.")
    model_endpoint: Optional[str] = Field(None, description="The model endpoint URL that was used.")
    auditor_endpoints: List[str] = Field(default_factory=list, description="Auditor endpoints that processed the request.")

    model_config = ConfigDict(populate_by_name=True)


class AttestationResult(BaseModel):
    """The final AI Passport issued by the Verifier (EAT-inspired)."""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_ATTESTATION

    schema_version: str = Field(
        default=SCHEMA_VERSION_ATTESTATION,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    iss: str = Field(..., description="Issuer ID (e.g. 'lucid-verifier').")

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
    iat: datetime = Field(..., description="Issued-at timestamp.")
    exp: Optional[datetime] = Field(None, description="Expiration timestamp.")
    passport_id: str = Field(..., description="Unique ID for this passport.")

    # Model identity
    model_id: str = Field(..., description="Target model identifier.")
    model_hash: str = Field(..., description="Reference hash of the model.")

    # Evidence layers (RATS RFC 9334 compliant)
    hardware_attestation: Optional[HardwareAttestation] = Field(None)
    evaluations: List[EvaluationResult] = Field(default_factory=list, description="Pre-deployment safety evaluation results.")
    evidence: List[Evidence] = Field(default_factory=list, description="Collection of signed Evidence bundles from Attesters (RFC 9334 compliant).")
    runtime_status: Optional[RuntimeStatus] = Field(None)
    routing_proof: Optional[RoutingProof] = Field(None, description="Zero-trust routing proof for serverless environments.")

    # Cumulative decision
    deployment_authorized: bool = Field(False, description="Overall safety authorization status.")
    authorization_reason: Optional[str] = Field(None, description="Detailed reason for final status.")
    risk_score: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description="Overall risk score across the chain (0.0=safe, 1.0=danger)."
    )

    verifier_signature: Optional[str] = Field(None, description="Verifier's signature over the entitre passport.")

    # Attestation environment metadata
    is_mock: bool = Field(
        False,
        description="True if attestation came from mock/dev environment (no real TEE hardware)."
    )

    # Session and user tracking
    session_id: Optional[str] = Field(None, description="Optional session identifier for grouping traces.")
    user_id: Optional[str] = Field(None, description="Optional user identifier associated with the request.")

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class AIPassport(AttestationResult):
    """Alias for AttestationResult for external API compatibility."""
    pass
