"""Agent management schemas shared between verifier and observer."""
from __future__ import annotations

import logging
import re
from typing import Annotated, ClassVar, Dict, List, Optional, TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

from .constants import SCHEMA_VERSION_AGENT

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .app_deployment import AppConfig
    from .passport_display import PassportDisplayConfig


class ConfiguredAuditor(BaseModel):
    """Configured auditor within a phase."""
    instance_id: str = Field(..., alias="instanceId")
    auditor_id: str = Field(..., alias="auditorId")
    name: str
    policy_id: Optional[str] = Field(
        default=None,
        alias="policyId",
        description="Reference to a policy from the environment's policies section"
    )
    env: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ModelConfig(BaseModel):
    """Model configuration."""
    id: str
    name: str

    model_config = ConfigDict(protected_namespaces=())


class GPUConfig(BaseModel):
    """GPU configuration."""
    type: str
    region: str
    cc_mode: bool = Field(default=False, alias="ccMode")
    provider: Optional[str] = None  # 'aws' | 'azure' | 'gcp'

    model_config = ConfigDict(populate_by_name=True)


class FrontendApp(BaseModel):
    """Frontend application for agent pairing."""
    id: str
    name: str
    type: str  # 'chatbot' | 'api-only' | 'custom' | 'container'
    url: Optional[str] = None
    container_image: Optional[str] = Field(default=None, alias="containerImage")

    model_config = ConfigDict(populate_by_name=True)


VALID_AUDIT_CHAIN_PHASES = {'pre_request', 'request', 'response', 'post_response'}


class CreateAgentRequest(BaseModel):
    """Request model for creating an agent."""
    name: str
    model: ModelConfig
    gpu: GPUConfig
    audit_chain: Annotated[Dict[str, List[ConfiguredAuditor]], Field(alias="auditChain", default_factory=dict)]
    frontend_app: Annotated[Optional[FrontendApp], Field(alias="frontendApp")] = None

    # App deployment configuration (optional)
    apps: Optional[List["AppConfig"]] = Field(default=None, description="Apps to deploy alongside LLM")
    passport_display: Annotated[Optional["PassportDisplayConfig"], Field(alias="passportDisplay", description="Passport display configuration")] = None

    # Management type: lucid_managed (GUI) or self_hosted (CLI)
    management_type: Annotated[str, Field(
        alias="managementType",
        description="Who manages this agent: lucid_managed (GUI wizard) or self_hosted (CLI deployed)"
    )] = "lucid_managed"

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    @field_validator('audit_chain')
    @classmethod
    def validate_audit_chain(cls, v: Dict[str, List[ConfiguredAuditor]]) -> Dict[str, List[ConfiguredAuditor]]:
        """Validate audit_chain structure and phase names."""
        if not v:
            return v
        invalid_phases = set(v.keys()) - VALID_AUDIT_CHAIN_PHASES
        if invalid_phases:
            raise ValueError(
                f'Invalid audit_chain phases: {invalid_phases}. '
                f'Valid phases are: {VALID_AUDIT_CHAIN_PHASES}'
            )
        return v


class UpdateAgentRequest(BaseModel):
    """Request model for updating an agent."""
    model: Optional[ModelConfig] = None
    gpu: Optional[GPUConfig] = None
    audit_chain: Optional[Dict[str, List[ConfiguredAuditor]]] = Field(default=None, alias="auditChain")
    frontend_app: Optional[FrontendApp] = Field(default=None, alias="frontendApp")
    apps: Optional[List["AppConfig"]] = Field(default=None, description="Apps to deploy alongside LLM")
    passport_display: Optional["PassportDisplayConfig"] = Field(default=None, alias="passportDisplay", description="Passport display configuration")

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

    @field_validator('audit_chain')
    @classmethod
    def validate_audit_chain(cls, v: Dict[str, List[ConfiguredAuditor]]) -> Dict[str, List[ConfiguredAuditor]]:
        """Validate audit_chain structure and phase names."""
        if not v:
            return v
        invalid_phases = set(v.keys()) - VALID_AUDIT_CHAIN_PHASES
        if invalid_phases:
            raise ValueError(
                f'Invalid audit_chain phases: {invalid_phases}. '
                f'Valid phases are: {VALID_AUDIT_CHAIN_PHASES}'
            )
        return v


class AgentEndpoints(BaseModel):
    """Agent deployment endpoints."""
    model: str
    verifier: str
    observer: str
    passport: str

    model_config = ConfigDict(protected_namespaces=())

    @field_validator('model', 'verifier', 'observer', 'passport')
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """Validate that endpoint URLs have valid format."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError(f'Invalid URL format: {v}')
        return v


class AgentResponse(BaseModel):
    """Agent response model."""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_AGENT

    schema_version: Annotated[str, Field(
        alias="schemaVersion",
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )] = SCHEMA_VERSION_AGENT
    id: str

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
    name: str
    model: ModelConfig
    gpu: GPUConfig
    audit_chain: Annotated[Dict[str, List[ConfiguredAuditor]], Field(alias="auditChain")]
    status: str
    created_at: Annotated[str, Field(alias="createdAt")]
    updated_at: Annotated[Optional[str], Field(alias="updatedAt")] = None
    endpoints: Optional[AgentEndpoints] = None
    error: Optional[str] = None
    frontend_app: Annotated[Optional[FrontendApp], Field(alias="frontendApp")] = None

    # App deployment configuration (optional)
    apps: Optional[List[AppConfig]] = Field(default=None, description="Deployed apps configuration")
    passport_display: Annotated[Optional[PassportDisplayConfig], Field(alias="passportDisplay", description="Passport display configuration")] = None
    app_endpoints: Annotated[Optional[Dict[str, str]], Field(alias="appEndpoints", description="Gateway URLs for deployed apps")] = None

    # Management type: who manages this agent's lifecycle
    management_type: Annotated[str, Field(
        alias="managementType",
        description="Who manages this agent: lucid_managed (SaaS wizard, full control) or self_hosted (CLI deployed, view-only)"
    )] = "lucid_managed"

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class AgentLogEntryResponse(BaseModel):
    """Log entry response model."""
    timestamp: str
    level: str
    message: str


# Import for runtime type resolution (after all class definitions)
from .app_deployment import AppConfig
from .passport_display import PassportDisplayConfig

# Update forward references for classes that use AppConfig and PassportDisplayConfig
CreateAgentRequest.model_rebuild()
AgentResponse.model_rebuild()
