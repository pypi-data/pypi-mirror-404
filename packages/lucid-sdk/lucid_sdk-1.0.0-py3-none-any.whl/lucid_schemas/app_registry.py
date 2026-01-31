"""App registry schemas for the AI Apps catalog."""
from __future__ import annotations

from enum import Enum
from typing import Annotated, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class AppCategory(str, Enum):
    """Category of app in the catalog."""
    TEST = "test"
    AUTONOMOUS_DEV = "autonomous_dev"
    ORCHESTRATOR = "orchestrator"
    CODING_TOOL = "coding_tool"
    APP_BUILDER = "app_builder"
    AGENT_OPS = "agent_ops"
    PERSONAL_AGENT = "personal_agent"
    PRODUCTIVITY = "productivity"
    CODING = "coding"
    AGENT_BUILDER = "agent_builder"
    AI_CHAT = "ai_chat"
    ENTERPRISE_SEARCH = "enterprise_search"
    CUSTOMER_ENGAGEMENT = "customer_engagement"
    LEGAL = "legal"


class TeeMode(str, Enum):
    """TEE deployment mode for apps."""
    IN_TEE = "in_tee"        # Same pod as LLM, inside TEE
    ADJACENT = "adjacent"    # Separate pod, same CC node
    EXTERNAL = "external"    # Standard compute, outside TEE


class AppLicense(str, Enum):
    """Open source licenses for catalog apps."""
    MIT = "MIT"
    APACHE_2 = "Apache-2.0"
    GPL_3 = "GPL-3.0"
    AGPL_3 = "AGPL-3.0"
    CC_BY_4 = "CC-BY-4.0"
    SUSTAINABLE_USE = "Sustainable-Use"
    CUSTOM = "Custom"


class ResourceRequirements(BaseModel):
    """Kubernetes resource requirements for an app."""
    cpu_request: Annotated[str, Field(alias="cpuRequest")] = "500m"
    cpu_limit: Annotated[str, Field(alias="cpuLimit")] = "2"
    memory_request: Annotated[str, Field(alias="memoryRequest")] = "1Gi"
    memory_limit: Annotated[str, Field(alias="memoryLimit")] = "4Gi"
    gpu_required: Annotated[bool, Field(alias="gpuRequired")] = False

    model_config = ConfigDict(populate_by_name=True)


class HealthCheck(BaseModel):
    """Health check configuration for an app."""
    path: str = "/health"
    port: int
    initial_delay_seconds: Annotated[int, Field(alias="initialDelaySeconds")] = 30
    period_seconds: Annotated[int, Field(alias="periodSeconds")] = 10
    timeout_seconds: Annotated[int, Field(alias="timeoutSeconds")] = 5

    model_config = ConfigDict(populate_by_name=True)


class AppEnvVar(BaseModel):
    """Environment variable definition for an app."""
    name: str
    description: str
    required: bool = False
    default: Optional[str] = None
    secret: bool = False  # If true, stored encrypted

    model_config = ConfigDict(populate_by_name=True)


class NotarizationInfo(BaseModel):
    """Notarization information for a catalog app."""
    is_notarized: Annotated[bool, Field(alias="isNotarized")] = False
    status: Optional[str] = None  # active, revoked, expired
    notarized_at: Annotated[Optional[str], Field(alias="notarizedAt")] = None
    notarized_by: Annotated[Optional[str], Field(alias="notarizedBy")] = None
    expires_at: Annotated[Optional[str], Field(alias="expiresAt")] = None
    certificate_id: Annotated[Optional[str], Field(alias="certificateId")] = None
    digest: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ChartReference(BaseModel):
    """Helm chart reference for Kubernetes deployment."""
    repo: str = ""  # Helm chart repo URL
    name: str = ""  # Chart name
    version: str = ""  # Chart version

    model_config = ConfigDict(populate_by_name=True)


class TeeSupport(BaseModel):
    """TEE support matrix for an app."""
    sgx: bool = Field(default=True, description="Intel SGX enclave support")
    sev_snp: Annotated[bool, Field(alias="sevSnp", description="AMD SEV-SNP support")] = True
    tdx: bool = Field(default=True, description="Intel TDX support")
    notes: Optional[str] = Field(default=None, description="Notes about TEE support limitations")

    model_config = ConfigDict(populate_by_name=True)


class CatalogApp(BaseModel):
    """Registered app in the catalog."""
    # Identity
    id: str = Field(..., description="Unique app identifier (e.g., 'openhands')")
    name: str = Field(..., description="Display name (e.g., 'OpenHands')")
    description: str
    category: AppCategory

    # Container
    image: str = Field(..., description="Container image (e.g., 'ghcr.io/all-hands-ai/openhands')")
    default_tag: Annotated[str, Field(alias="defaultTag")] = "latest"
    supported_tags: Annotated[List[str], Field(alias="supportedTags", default_factory=list)]

    # Helm chart reference
    chart: ChartReference = Field(default_factory=ChartReference, description="Helm chart reference for K8s deployment")

    # Networking
    default_port: Annotated[int, Field(alias="defaultPort")]
    additional_ports: Annotated[List[int], Field(alias="additionalPorts", default_factory=list)]

    # Resources
    resources: ResourceRequirements = Field(default_factory=ResourceRequirements)
    health_check: Annotated[Optional[HealthCheck], Field(alias="healthCheck")] = None

    # Configuration
    env_vars: Annotated[List[AppEnvVar], Field(alias="envVars", default_factory=list)]
    volumes: List[str] = Field(default_factory=list, description="Mount paths")

    # Metadata
    license: AppLicense
    homepage: Optional[HttpUrl] = None
    documentation: Optional[HttpUrl] = None
    repository: Optional[HttpUrl] = None
    stars: int = Field(default=0, description="GitHub stars")

    # LLM Integration
    requires_llm: Annotated[bool, Field(alias="requiresLlm", description="Needs LLM endpoint")] = True
    llm_env_var: Annotated[str, Field(alias="llmEnvVar", description="Env var for LLM endpoint")] = "OPENAI_API_BASE"
    llm_api_key_env_var: Annotated[str, Field(alias="llmApiKeyEnvVar", description="Env var for API key")] = "OPENAI_API_KEY"

    # Workspace Integration
    supports_workspace: Annotated[bool, Field(alias="supportsWorkspace", description="Can mount shared workspace")] = True
    workspace_env_var: Annotated[str, Field(alias="workspaceEnvVar", description="Env var for workspace path")] = "WORKSPACE_DIR"

    # Security
    verified: bool = Field(default=False, description="Lucid-verified image")
    sbom_available: Annotated[bool, Field(alias="sbomAvailable")] = False
    slsa_level: Annotated[int, Field(alias="slsaLevel", ge=0, le=4)] = 0

    # TEE Configuration
    default_tee_mode: Annotated[TeeMode, Field(alias="defaultTeeMode")] = TeeMode.IN_TEE
    tee_compatible: Annotated[bool, Field(alias="teeCompatible", description="Can run inside TEE")] = True
    tee_recommended: Annotated[bool, Field(alias="teeRecommended", description="Should run in TEE for security")] = True
    external_reason: Annotated[Optional[str], Field(alias="externalReason", description="Why app defaults to external")] = None

    # TEE support matrix (hardware-specific compatibility)
    tee_support: Annotated[TeeSupport, Field(alias="teeSupport", description="TEE hardware support matrix", default_factory=TeeSupport)]

    # Auditor profile
    auditor_profile: Annotated[str, Field(alias="auditorProfile", description="Auditor profile for attestation")] = "default"

    # Usability rating
    ease_of_use: Annotated[int, Field(alias="easeOfUse", ge=1, le=5, description="Ease of use rating (1-5)")] = 3

    # Notarization status (populated dynamically from database)
    notarization_status: Annotated[Optional[NotarizationInfo], Field(alias="notarizationStatus")] = None

    model_config = ConfigDict(populate_by_name=True)


class PassportTemplate(BaseModel):
    """Passport template for an app."""
    app_id: Annotated[str, Field(alias="appId")]
    container: dict
    security: dict
    default_tee_mode: Annotated[TeeMode, Field(alias="defaultTeeMode")]

    model_config = ConfigDict(populate_by_name=True)
