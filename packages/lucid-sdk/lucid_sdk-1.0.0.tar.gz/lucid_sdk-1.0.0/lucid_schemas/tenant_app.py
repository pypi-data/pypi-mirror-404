"""Tenant app deployment schemas for isolated AI Apps in TEEs.

These schemas define the API contracts for deploying private AI apps
that run in Trusted Execution Environments (TEEs). Each tenant's app
is cryptographically isolated - Lucid cannot access app data.

PRIVACY GUARANTEES:
- App runs inside a hardware TEE (SGX/SEV-SNP/TDX)
- Memory is encrypted by CPU, inaccessible to hypervisor/K8s
- Storage is encrypted with key sealed to TEE attestation
- Network is isolated from other tenants and control plane
- App manages its own users/database internally
"""
from __future__ import annotations

import logging
from enum import Enum
from typing import Annotated, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .app_deployment import TeeType
from .app_registry import CatalogApp, ResourceRequirements, TeeSupport
from .constants import SCHEMA_VERSION_DEFAULT

logger = logging.getLogger(__name__)


class TenantAppStatus(str, Enum):
    """Tenant app deployment status."""
    PENDING = "pending"
    DEPLOYING = "deploying"
    READY = "ready"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"
    DELETING = "deleting"


class CreateTenantAppRequest(BaseModel):
    """Request to deploy a private app for the tenant.

    The app will run in a TEE with:
    - Encrypted memory (hardware-enforced)
    - Encrypted storage (key sealed to TEE)
    - Network isolation from Lucid and other tenants
    - Its own internal user management

    Lucid stores only metadata (app exists, URL, status).
    Lucid CANNOT access app data, users, or conversations.
    """
    app_id: Annotated[str, Field(alias="appId", description="App ID from catalog (e.g., 'openhands')")]
    tee_type: Annotated[TeeType, Field(alias="teeType", description="TEE type: sgx, sev-snp, tdx")] = TeeType.SEV_SNP
    storage_size: Annotated[str, Field(alias="storageSize", description="Encrypted storage size")] = "10Gi"

    # Resource configuration
    cpu_request: Annotated[str, Field(alias="cpuRequest")] = "500m"
    cpu_limit: Annotated[str, Field(alias="cpuLimit")] = "2"
    memory_request: Annotated[str, Field(alias="memoryRequest")] = "1Gi"
    memory_limit: Annotated[str, Field(alias="memoryLimit")] = "4Gi"

    # App-specific config (passed to the app container, not stored by Lucid)
    app_env_vars: Annotated[Optional[Dict[str, str]], Field(
        alias="appEnvVars",
        description="Environment variables passed to the app container"
    )] = None

    # Optional custom image tag
    image_tag: Annotated[Optional[str], Field(alias="imageTag", description="Override default image tag")] = None

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('storage_size')
    @classmethod
    def validate_storage_size(cls, v: str) -> str:
        """Validate storage size format (e.g., '10Gi', '100Mi')."""
        import re
        if not re.match(r'^\d+[KMGT]i$', v):
            raise ValueError(f"Invalid storage size format: {v}. Expected format: <number><Ki|Mi|Gi|Ti>")
        return v

    @field_validator('cpu_request', 'cpu_limit')
    @classmethod
    def validate_cpu(cls, v: str) -> str:
        """Validate CPU format (e.g., '500m', '2')."""
        import re
        if not re.match(r'^(\d+m?|\d+\.\d+)$', v):
            raise ValueError(f"Invalid CPU format: {v}. Expected format: <number> or <number>m")
        return v

    @field_validator('memory_request', 'memory_limit')
    @classmethod
    def validate_memory(cls, v: str) -> str:
        """Validate memory format (e.g., '1Gi', '512Mi')."""
        import re
        if not re.match(r'^\d+[KMGT]i$', v):
            raise ValueError(f"Invalid memory format: {v}. Expected format: <number><Ki|Mi|Gi|Ti>")
        return v


class TenantAppResponse(BaseModel):
    """Response with tenant app deployment info.

    Contains only metadata that Lucid is allowed to know.
    App data, users, and conversations are NOT included.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_DEFAULT

    schema_version: Annotated[str, Field(
        alias="schemaVersion",
        description="Schema version for backwards compatibility.",
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

    # Deployment identity
    deployment_id: Annotated[str, Field(alias="deploymentId")]
    app_id: Annotated[str, Field(alias="appId")]
    app_name: Annotated[str, Field(alias="appName")]

    # Status
    status: TenantAppStatus
    status_message: Annotated[Optional[str], Field(alias="statusMessage")] = None

    # TEE configuration
    tee_type: Annotated[TeeType, Field(alias="teeType")]

    # Access
    public_url: Annotated[Optional[str], Field(alias="publicUrl")] = None
    subdomain: Optional[str] = None

    # Attestation (proof app runs in TEE)
    attestation_report_hash: Annotated[Optional[str], Field(alias="attestationReportHash")] = None
    last_attestation_at: Annotated[Optional[str], Field(alias="lastAttestationAt")] = None

    # Resources
    cpu_request: Annotated[str, Field(alias="cpuRequest")]
    memory_request: Annotated[str, Field(alias="memoryRequest")]
    storage_size: Annotated[str, Field(alias="storageSize")]

    # Timestamps
    created_at: Annotated[str, Field(alias="createdAt")]
    ready_at: Annotated[Optional[str], Field(alias="readyAt")] = None

    # Privacy note (for transparency)
    privacy_note: Annotated[str, Field(alias="privacyNote")] = "App data, users, and conversations are encrypted inside the TEE. Lucid cannot access them."

    model_config = ConfigDict(populate_by_name=True)


class TenantAppListResponse(BaseModel):
    """List of tenant app deployments."""
    apps: List[TenantAppResponse]
    total: int


class DeleteTenantAppResponse(BaseModel):
    """Response after deleting a tenant app."""
    deployment_id: Annotated[str, Field(alias="deploymentId")]
    status: str = "deleted"
    message: str = Field(
        default="App and all encrypted data have been permanently deleted.",
        description="Confirmation message"
    )

    model_config = ConfigDict(populate_by_name=True)
