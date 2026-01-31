"""Evidence schema for RFC 9334 (RATS) compliance.

Evidence is a signed container of Claims from a single Attester. This aligns
with the RATS architecture where Evidence is produced by an Attester and
contains one or more Claims signed together for efficiency.
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import ClassVar, List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator

from .enums import EvidenceSource, TrustTier
from .claim import Claim
from .constants import SCHEMA_VERSION_EVIDENCE
from .zk import ZKProofSchema

logger = logging.getLogger(__name__)


class Evidence(BaseModel):
    """Container of Claims from a single Attester (RFC 9334 Evidence).

    Evidence bundles one or more Claims and provides a single cryptographic
    signature covering all of them. This is more efficient than signing
    each claim individually (as was done with Measurements).

    The signature flow is:
    1. Attester creates Claims (unsigned assertions)
    2. Attester bundles Claims into Evidence
    3. Attester signs the Evidence once (covering all Claims)
    4. Verifier verifies one signature per Evidence

    This replaces the per-Measurement signature approach.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_EVIDENCE

    schema_version: str = Field(
        default=SCHEMA_VERSION_EVIDENCE,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["2.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    evidence_id: str = Field(
        ...,
        description="Unique identifier for this evidence bundle.",
        examples=["ev-abc123-def456"]
    )

    # Attester identification
    attester_id: str = Field(
        ...,
        description="Identifier of the Attester that produced this evidence.",
        examples=["lucid-toxicity-auditor", "lucid-pii-auditor"]
    )
    attester_type: EvidenceSource = Field(
        ...,
        description="The type of Attester (auditor, tee, verifier, operator, etc.).",
        examples=["auditor", "tee", "operator"]
    )

    # Claims bundle
    claims: List[Claim] = Field(
        ...,
        min_length=1,
        description="List of Claims contained in this evidence. Must have at least one claim."
    )
    phase: str = Field(
        ...,
        description="The execution phase this evidence relates to.",
        examples=["request", "response", "artifact", "execution", "deployment"]
    )

    # Timing
    generated_at: datetime = Field(
        ...,
        description="Time the evidence was generated (UTC).",
        examples=["2025-12-30T20:00:00Z"]
    )
    nonce: Optional[str] = Field(
        None,
        description="Optional freshness nonce for anti-replay protection."
    )

    # Single signature covering ALL claims
    signature: str = Field(
        ...,
        description="Cryptographic signature covering all claims in this evidence.",
        examples=["base64-encoded-signature"]
    )

    # Trust assessment (filled by Verifier during appraisal)
    trust_tier: Optional[TrustTier] = Field(
        None,
        description="Trust tier assigned by the Verifier during appraisal (per RFC 9334 EAR format).",
        examples=["affirming", "warning", "contraindicated"]
    )

    # ZK proof option (moved from Claim level for efficiency)
    zk_proof: Optional[ZKProofSchema] = Field(
        None,
        description="Optional ZK proof attesting to the computation of all claims."
    )

    # EAR-compliant appraisal record (populated by Verifier after policy evaluation)
    # Uses Dict to avoid circular imports - structure follows AppraisalRecord schema
    appraisal_record: Optional[Dict[str, Any]] = Field(
        None,
        description=(
            "Per-claim appraisal results from policy evaluation (EAR-compliant). "
            "Structure follows AppraisalRecord schema from lucid_schemas.policy."
        )
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
