"""Evidence API request/response schemas shared between verifier and other services.

These models define the API contract for evidence submission, verification,
and audit log export endpoints.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .evidence import Evidence
from .evaluation import EvaluationResult


class EvidenceRequest(BaseModel):
    """Request model for evidence submission.

    Evidence bundles contain Claims from Attesters (auditors), each with
    a single cryptographic signature covering all claims in the bundle.
    """

    session_id: Annotated[Optional[str], Field(alias="sessionId")] = None
    user_id: Annotated[Optional[str], Field(alias="userId")] = None
    model_id: Annotated[str, Field(alias="modelId")]
    evidence: List[Evidence] = Field(default_factory=list)
    evaluations: List[EvaluationResult] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class EvidenceVerificationRequest(BaseModel):
    """Request model for the transactional evidence verification endpoint.

    This model is used by the POST /v1/evidence/verify endpoint which
    provides stronger consistency guarantees through:
    - Explicit transaction boundaries
    - Row-level locking
    - Optimistic locking with version checks
    - Idempotency support
    """

    model_id: Annotated[str, Field(alias="modelId")]
    evidence: List[Evidence]
    session_id: Annotated[Optional[str], Field(alias="sessionId")] = None
    user_id: Annotated[Optional[str], Field(alias="userId")] = None
    evaluations: List[EvaluationResult] = Field(default_factory=list)
    org_id: Annotated[Optional[str], Field(alias="orgId")] = None

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class EvidenceVerificationResponse(BaseModel):
    """Response model for evidence verification.

    Attributes:
        passport_id: ID of the created/updated passport.
        receipt_id: ID of the interaction receipt.
        is_new_passport: True if a new passport was created.
        evidence_count: Number of evidence items verified.
        cached: True if this is a cached response from idempotency.
    """

    passport_id: Annotated[str, Field(alias="passportId")]
    receipt_id: Annotated[str, Field(alias="receiptId")]
    is_new_passport: Annotated[bool, Field(alias="isNewPassport")]
    evidence_count: Annotated[int, Field(alias="evidenceCount")]
    cached: bool = Field(default=False)

    model_config = ConfigDict(populate_by_name=True)


class AuditLogEntry(BaseModel):
    """Audit log entry for export."""

    id: str
    timestamp: datetime
    action: str
    user_id: Annotated[Optional[str], Field(alias="userId")] = None
    organization_id: Annotated[Optional[str], Field(alias="organizationId")] = None
    resource_type: Annotated[Optional[str], Field(alias="resourceType")] = None
    resource_id: Annotated[Optional[str], Field(alias="resourceId")] = None
    ip_address: Annotated[Optional[str], Field(alias="ipAddress")] = None
    user_agent: Annotated[Optional[str], Field(alias="userAgent")] = None
    request_id: Annotated[Optional[str], Field(alias="requestId")] = None
    details: Optional[dict] = None
    success: bool
    error_message: Annotated[Optional[str], Field(alias="errorMessage")] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class AuditLogExportResponse(BaseModel):
    """Response for audit log export."""

    logs: List[AuditLogEntry]
    total: int
    has_more: Annotated[bool, Field(alias="hasMore")]
    next_cursor: Annotated[Optional[str], Field(alias="nextCursor")] = None

    model_config = ConfigDict(populate_by_name=True)
