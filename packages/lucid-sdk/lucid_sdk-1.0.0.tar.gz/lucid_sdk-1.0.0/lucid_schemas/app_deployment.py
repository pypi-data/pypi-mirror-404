"""App deployment and passport schemas for AI Apps."""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, ClassVar, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .app_registry import ResourceRequirements, TeeMode
from .constants import SCHEMA_VERSION_DEFAULT
from .enums import TeeType
from .passport_display import PassportDisplayConfig
from .agent import ConfiguredAuditor, FrontendApp, GPUConfig, ModelConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class AttestationLevel(str, Enum):
    """Attestation level based on TEE deployment mode."""
    FULL = "full"
    PARTIAL = "partial"
    CONTAINER_ONLY = "container_only"


class AppPassportStatus(str, Enum):
    """App passport status values."""
    VALID = "valid"
    EXPIRED = "expired"
    REVOKED = "revoked"


# =============================================================================
# Base Models (no dependencies on other models in this file)
# =============================================================================

class ContainerInfo(BaseModel):
    """Container provenance information."""
    image: str = Field(..., description="Full image reference (e.g., 'ghcr.io/all-hands-ai/openhands:0.21.0')")
    digest: str = Field(..., description="Image digest (e.g., 'sha256:abc123...')")
    registry: str = Field(..., description="Registry hostname (e.g., 'ghcr.io')")
    tag: str = Field(..., description="Image tag (e.g., '0.21.0')")
    build_date: Annotated[Optional[str], Field(alias="buildDate", description="ISO timestamp of image build")] = None
    base_image: Annotated[Optional[str], Field(alias="baseImage", description="Base image (e.g., 'python:3.11-slim')")] = None
    base_image_digest: Annotated[Optional[str], Field(alias="baseImageDigest", description="Base image digest")] = None

    model_config = ConfigDict(populate_by_name=True)


class TeeAttestation(BaseModel):
    """TEE attestation information (in_tee and adjacent modes only)."""
    tee_type: Annotated[TeeType, Field(alias="teeType", description="Hardware TEE type")]
    enclave_id: Annotated[str, Field(alias="enclaveId", description="Enclave measurement")]
    hardware_report: Annotated[str, Field(alias="hardwareReport", description="Raw attestation report (base64)")]
    verified_at: Annotated[str, Field(alias="verifiedAt", description="When TEE was verified (ISO timestamp)")]
    shared_with_llm: Annotated[bool, Field(alias="sharedWithLlm", description="True if same enclave as LLM")]
    platform_cert_chain: Annotated[Optional[str], Field(alias="platformCertChain", description="Hardware cert chain")] = None

    model_config = ConfigDict(populate_by_name=True)


class SecurityAttestation(BaseModel):
    """Security attestation information (all modes)."""
    sbom_url: Annotated[Optional[str], Field(alias="sbomUrl", description="Link to SBOM (CycloneDX/SPDX)")] = None
    vuln_scan_url: Annotated[Optional[str], Field(alias="vulnScanUrl", description="Link to CVE scan results")] = None
    slsa_level: Annotated[int, Field(alias="slsaLevel", ge=0, le=4, description="SLSA supply chain level (0-4)")] = 0
    sigstore_signature: Annotated[Optional[str], Field(alias="sigstoreSignature", description="Sigstore/Cosign signature")] = None
    notarized_at: Annotated[Optional[str], Field(alias="notarizedAt", description="When image was notarized (ISO timestamp)")] = None
    notarized_by: Annotated[Optional[str], Field(alias="notarizedBy", description="Notarization authority")] = None

    model_config = ConfigDict(populate_by_name=True)


class RuntimeMetrics(BaseModel):
    """Runtime metrics for a deployed app."""
    started_at: Annotated[str, Field(alias="startedAt", description="When app started (ISO timestamp)")]
    last_health_check: Annotated[Optional[str], Field(alias="lastHealthCheck", description="Last health check timestamp")] = None
    total_requests: Annotated[int, Field(alias="totalRequests")] = 0
    error_rate: Annotated[float, Field(alias="errorRate", ge=0.0, le=1.0)] = 0.0
    avg_latency_ms: Annotated[float, Field(alias="avgLatencyMs", ge=0.0)] = 0.0

    model_config = ConfigDict(populate_by_name=True)


class LinkedPassports(BaseModel):
    """References to linked passports."""
    llm_passport: Annotated[Optional[str], Field(alias="llmPassport", description="Associated LLM passport ID")] = None
    auditor_passports: Annotated[List[str], Field(alias="auditorPassports", description="Auditor sidecar passport IDs", default_factory=list)]

    model_config = ConfigDict(populate_by_name=True)


class VulnerabilitySummary(BaseModel):
    """Vulnerability scan summary counts."""
    critical: int = Field(default=0, ge=0, description="Number of critical vulnerabilities")
    high: int = Field(default=0, ge=0, description="Number of high vulnerabilities")
    medium: int = Field(default=0, ge=0, description="Number of medium vulnerabilities")
    low: int = Field(default=0, ge=0, description="Number of low vulnerabilities")
    scan_url: Annotated[Optional[str], Field(alias="scanUrl", description="URL to full scan results")] = None
    scanned_at: Annotated[Optional[str], Field(alias="scannedAt", description="When the scan was performed (ISO timestamp)")] = None

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# App Configuration Models
# =============================================================================

class AppConfig(BaseModel):
    """Configuration for a deployed app."""
    app_id: Annotated[str, Field(alias="appId", description="Reference to CatalogApp.id")]
    image_override: Annotated[Optional[str], Field(alias="imageOverride", description="Custom image if not using catalog")] = None
    tag: str = "latest"

    # TEE Configuration (user choice)
    tee_mode: Annotated[TeeMode, Field(alias="teeMode", description="Where to run the app")] = TeeMode.IN_TEE

    # Runtime config
    env_vars: Annotated[Dict[str, str], Field(alias="envVars", description="User-provided env vars", default_factory=dict)]
    secrets: Dict[str, str] = Field(default_factory=dict, description="Encrypted secrets (API keys, etc.)")

    # Resource overrides
    resources: Optional[ResourceRequirements] = None

    # Workspace
    workspace_enabled: Annotated[bool, Field(alias="workspaceEnabled")] = True
    workspace_path: Annotated[str, Field(alias="workspacePath")] = "/workspace"

    # Networking
    expose_port: Annotated[Optional[int], Field(alias="exposePort", description="Port to expose externally")] = None
    internal_only: Annotated[bool, Field(alias="internalOnly", description="If true, only accessible within cluster")] = False

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Complex Models (depend on base models)
# =============================================================================

class AppPassport(BaseModel):
    """AI Passport for a deployed app."""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_DEFAULT

    schema_version: Annotated[str, Field(
        alias="schemaVersion",
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )] = SCHEMA_VERSION_DEFAULT

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

    # Identity
    passport_id: Annotated[str, Field(alias="passportId", description="Unique passport ID (e.g., 'app-passport-{uuid}')")]
    app_id: Annotated[str, Field(alias="appId", description="App instance ID (e.g., 'openhands-{agent_id}')")]
    agent_id: Annotated[str, Field(alias="agentId", description="Parent agent reference")]

    # Deployment Mode
    tee_mode: Annotated[TeeMode, Field(alias="teeMode", description="TEE deployment mode")]
    attestation_level: Annotated[AttestationLevel, Field(alias="attestationLevel", description="Attestation level based on TEE mode")]

    # Container Provenance (all modes)
    container: ContainerInfo

    # TEE Attestation (in_tee and adjacent modes only)
    tee_attestation: Annotated[Optional[TeeAttestation], Field(alias="teeAttestation")] = None

    # Security Attestation (all modes)
    security: SecurityAttestation

    # Runtime Claims (all modes)
    runtime: RuntimeMetrics

    # Linked Resources
    linked_passports: Annotated[LinkedPassports, Field(alias="linkedPassports", default_factory=LinkedPassports)]

    # Cryptographic Proof
    signature: Optional[str] = Field(default=None, description="Ed25519 signature")
    signed_at: Annotated[Optional[str], Field(alias="signedAt", description="When passport was signed (ISO timestamp)")] = None
    signed_by: Annotated[Optional[str], Field(alias="signedBy", description="Verifier public key")] = None

    # Validity
    expires_at: Annotated[Optional[str], Field(alias="expiresAt", description="Passport expiration (ISO timestamp)")] = None
    verified: bool = Field(default=False, description="Whether passport has been verified")

    model_config = ConfigDict(populate_by_name=True)


class AppDeployment(BaseModel):
    """Information about a deployed app."""
    app_id: Annotated[str, Field(alias="appId", description="App identifier")]
    agent_id: Annotated[str, Field(alias="agentId", description="Parent agent identifier")]
    name: str = Field(..., description="Display name of the app")
    status: str = Field(..., description="Current status (e.g., 'running', 'stopped')")
    tee_mode: Annotated[TeeMode, Field(alias="teeMode", description="TEE deployment mode")]
    image: str = Field(..., description="Container image reference")
    tag: str = Field(..., description="Image tag")
    port: int = Field(..., ge=1, le=65535, description="Exposed port number")
    created_at: Annotated[str, Field(alias="createdAt", description="When the app was created (ISO timestamp)")]
    passport_id: Annotated[Optional[str], Field(alias="passportId", description="Associated passport ID if exists")] = None

    model_config = ConfigDict(populate_by_name=True)


class PassportValidity(BaseModel):
    """Result of passport validity check."""
    valid: bool = Field(..., description="Whether the passport is currently valid")
    passport_id: Annotated[str, Field(alias="passportId", description="The passport identifier")]
    status: str = Field(..., description="Status: 'valid', 'expired', 'revoked', or 'security_issue'")
    expires_at: Annotated[Optional[str], Field(alias="expiresAt", description="Passport expiration (ISO timestamp)")] = None
    issues: List[str] = Field(default_factory=list, description="List of validation issues")
    has_new_critical_vulnerabilities: Annotated[bool, Field(
        alias="hasNewCriticalVulnerabilities",
        description="Whether new critical vulnerabilities were found"
    )] = False

    model_config = ConfigDict(populate_by_name=True)


class PassportSignatureVerification(BaseModel):
    """Result of passport signature verification.

    Note: This is distinct from SignatureVerification in security.py which handles
    container image signature verification. This model is for verifying the
    Ed25519 signature on the passport itself.
    """
    valid: bool = Field(..., description="Whether the signature was successfully verified")
    passport_id: Annotated[str, Field(alias="passportId", description="The passport identifier")]
    signed_at: Annotated[str, Field(alias="signedAt", description="When the passport was signed (ISO timestamp)")]
    signed_by: Annotated[str, Field(alias="signedBy", description="Verifier identity that signed the passport")]
    public_key_id: Annotated[str, Field(alias="publicKeyId", description="Public key identifier used for verification")]
    error: Optional[str] = Field(default=None, description="Error message if verification failed")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Request Models
# =============================================================================

class CreateAppDeploymentRequest(BaseModel):
    """Request to deploy an AI App (LLM + apps + auditors)."""
    name: str
    model: ModelConfig
    gpu: GPUConfig
    audit_chain: Annotated[Dict[str, List[ConfiguredAuditor]], Field(alias="auditChain", default_factory=dict)]
    frontend_app: Annotated[Optional[FrontendApp], Field(alias="frontendApp")] = None

    # App configuration
    apps: List[AppConfig] = Field(default_factory=list, description="Apps to deploy alongside LLM")

    # Passport display configuration
    passport_display: Annotated[PassportDisplayConfig, Field(alias="passportDisplay", default_factory=PassportDisplayConfig)]

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())
