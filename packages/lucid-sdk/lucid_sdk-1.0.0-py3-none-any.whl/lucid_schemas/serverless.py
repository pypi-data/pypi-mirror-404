"""Serverless architecture schemas for Lucid platform.

This module provides Pydantic models for the serverless deployment mode,
enabling customers to get instant access to pre-deployed shared pools of
models, auditors, and apps without dedicated infrastructure.

TEE (Trusted Execution Environment) properties provide equivalent security
guarantees to self-hosted deployments.
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, ClassVar, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SCHEMA_VERSION_DEFAULT
from .enums import TeeType, TeeTypeServerless

logger = logging.getLogger(__name__)

# Schema version for serverless models
SCHEMA_VERSION_SERVERLESS = "1.0.0-beta"


class DataResidency(str, Enum):
    """Data residency regions for serverless deployments.

    Controls where customer data is processed and stored for compliance
    with regional data protection regulations.
    """
    US = "us"      # United States
    EU = "eu"      # European Union
    APAC = "apac"  # Asia-Pacific
    ANY = "any"    # No specific requirement (lowest latency routing)


class AuditorProfile(str, Enum):
    """Pre-configured auditor profiles for common use cases.

    Each profile includes a curated set of auditors optimized for
    specific workload types. Customers can extend with custom auditors.
    """
    CODING = "coding"        # Optimized for code generation tasks
    WORKFLOW = "workflow"    # Multi-step agent workflows
    CHAT = "chat"            # Conversational AI applications
    CUSTOMER = "customer"    # Customer service / support bots
    DEFAULT = "default"      # Balanced general-purpose profile


class EnvironmentStatus(str, Enum):
    """Status of a serverless environment."""
    PENDING = "pending"      # Environment created, awaiting resource allocation
    ACTIVE = "active"        # Environment ready for traffic
    SUSPENDED = "suspended"  # Temporarily disabled (billing, policy, etc.)
    DELETED = "deleted"      # Soft-deleted, pending cleanup


class ResourceType(str, Enum):
    """Types of shared resources in the serverless pool."""
    MODEL = "model"          # LLM inference endpoints
    AUDITOR = "auditor"      # Auditor service instances
    APP = "app"              # Frontend applications (Open WebUI, etc.)


class ResourceStatus(str, Enum):
    """Status of a shared resource in the pool."""
    AVAILABLE = "available"  # Ready for traffic
    DRAINING = "draining"    # Completing existing requests, no new traffic
    MAINTENANCE = "maintenance"  # Temporarily unavailable
    FAILED = "failed"        # Unhealthy, excluded from routing


class AuditorConfig(BaseModel):
    """Configuration override for an auditor within a profile.

    Allows customers to customize auditor behavior without changing
    the underlying profile definition.
    """
    auditor_id: str = Field(..., alias="auditorId", description="Auditor identifier")
    enabled: bool = Field(default=True, description="Whether this auditor is active")
    config: Dict[str, str] = Field(
        default_factory=dict,
        description="Auditor-specific configuration overrides"
    )

    model_config = ConfigDict(populate_by_name=True)


class EnvironmentConfig(BaseModel):
    """Configuration for a serverless environment.

    An environment represents a customer's logical deployment configuration
    that maps to shared pool resources. Multiple environments can share
    the same underlying model/auditor/app instances while maintaining
    isolation via TEE properties.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_SERVERLESS

    schema_version: Annotated[str, Field(
        alias="schemaVersion",
        description="Schema version for backwards compatibility"
    )] = SCHEMA_VERSION_SERVERLESS
    environment_id: Annotated[UUID, Field(alias="environmentId")]
    customer_id: Annotated[UUID, Field(alias="customerId")]
    org_id: Annotated[Optional[UUID], Field(alias="orgId")] = None
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)

    # Resource selection
    app_id: Annotated[str, Field(alias="appId", description="Catalog app identifier")]
    model_id: Annotated[str, Field(alias="modelId", description="Catalog model identifier")]

    # Auditor configuration
    auditor_profile: Annotated[AuditorProfile, Field(
        alias="auditorProfile",
        description="Pre-configured auditor profile"
    )] = AuditorProfile.DEFAULT
    custom_auditors: Annotated[List[str], Field(
        alias="customAuditors",
        description="Additional custom auditor IDs to include",
        default_factory=list
    )]
    auditor_configs: Annotated[List[AuditorConfig], Field(
        alias="auditorConfigs",
        description="Configuration overrides for auditors",
        default_factory=list
    )]

    # Deployment constraints
    data_residency: Annotated[DataResidency, Field(
        alias="dataResidency",
        description="Data residency requirement for compliance"
    )] = DataResidency.ANY

    # Status tracking
    status: EnvironmentStatus = Field(default=EnvironmentStatus.PENDING)

    # Timestamps
    created_at: Annotated[Optional[datetime], Field(alias="createdAt")] = None
    updated_at: Annotated[Optional[datetime], Field(alias="updatedAt")] = None

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())

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


class CreateEnvironmentRequest(BaseModel):
    """Request model for creating a serverless environment."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)

    # Resource selection
    app_id: Annotated[str, Field(alias="appId", description="Catalog app identifier")]
    model_id: Annotated[str, Field(alias="modelId", description="Catalog model identifier")]

    # Auditor configuration
    auditor_profile: Annotated[AuditorProfile, Field(alias="auditorProfile")] = AuditorProfile.DEFAULT
    custom_auditors: Annotated[List[str], Field(alias="customAuditors", default_factory=list)]
    auditor_configs: Annotated[List[AuditorConfig], Field(alias="auditorConfigs", default_factory=list)]

    # Deployment constraints
    data_residency: Annotated[DataResidency, Field(alias="dataResidency")] = DataResidency.ANY

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class UpdateEnvironmentRequest(BaseModel):
    """Request model for updating a serverless environment."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)

    # Resource selection (can be changed)
    app_id: Annotated[Optional[str], Field(alias="appId")] = None
    model_id: Annotated[Optional[str], Field(alias="modelId")] = None

    # Auditor configuration (can be changed)
    auditor_profile: Annotated[Optional[AuditorProfile], Field(alias="auditorProfile")] = None
    custom_auditors: Annotated[Optional[List[str]], Field(alias="customAuditors")] = None
    auditor_configs: Annotated[Optional[List[AuditorConfig]], Field(alias="auditorConfigs")] = None

    # Deployment constraints (can be changed with potential traffic shift)
    data_residency: Annotated[Optional[DataResidency], Field(alias="dataResidency")] = None

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class EnvironmentResponse(BaseModel):
    """Response model for serverless environment operations."""
    schema_version: Annotated[str, Field(alias="schemaVersion")] = SCHEMA_VERSION_SERVERLESS
    environment_id: Annotated[UUID, Field(alias="environmentId")]
    customer_id: Annotated[UUID, Field(alias="customerId")]
    org_id: Annotated[Optional[UUID], Field(alias="orgId")] = None
    name: str
    description: Optional[str] = None

    # Resource selection
    app_id: Annotated[str, Field(alias="appId")]
    model_id: Annotated[str, Field(alias="modelId")]

    # Auditor configuration
    auditor_profile: Annotated[AuditorProfile, Field(alias="auditorProfile")]
    custom_auditors: Annotated[List[str], Field(alias="customAuditors", default_factory=list)]
    auditor_configs: Annotated[List[AuditorConfig], Field(alias="auditorConfigs", default_factory=list)]

    # Deployment constraints
    data_residency: Annotated[DataResidency, Field(alias="dataResidency")]

    # Status
    status: EnvironmentStatus

    # Connection information (populated when status is ACTIVE)
    connection_url: Annotated[Optional[str], Field(alias="connectionUrl")] = None

    # Timestamps
    created_at: Annotated[datetime, Field(alias="createdAt")]
    updated_at: Annotated[Optional[datetime], Field(alias="updatedAt")] = None

    model_config = ConfigDict(populate_by_name=True, from_attributes=True, protected_namespaces=())


class TEEEndpoint(BaseModel):
    """A TEE endpoint available for routing.

    Represents a specific instance in the shared pool that can serve
    requests for an environment. Includes attestation information for
    client-side verification.
    """
    endpoint_url: str = Field(..., alias="endpointUrl")
    region: str = Field(..., description="Geographic region of the endpoint")
    tee_type: TeeTypeServerless = Field(..., alias="teeType")

    # Attestation data for zero-trust verification
    attestation_report: Optional[str] = Field(
        default=None,
        alias="attestationReport",
        description="Base64-encoded attestation report from TEE"
    )
    attestation_timestamp: Optional[datetime] = Field(
        default=None,
        alias="attestationTimestamp",
        description="When the attestation was generated"
    )

    # Load information for client-side load balancing
    load_percentage: int = Field(
        default=0,
        alias="loadPercentage",
        ge=0,
        le=100,
        description="Current load percentage (0-100)"
    )

    # Health status
    healthy: bool = Field(default=True)

    model_config = ConfigDict(populate_by_name=True)


class ServerlessRouteRequest(BaseModel):
    """Request for routing to serverless TEE endpoints.

    The client provides the environment ID and receives back available
    TEE endpoints with their attestation reports for verification.
    """
    environment_id: Annotated[UUID, Field(alias="environmentId")]

    # Optional preferences for endpoint selection
    preferred_region: Annotated[Optional[str], Field(
        alias="preferredRegion",
        description="Preferred region for latency optimization"
    )] = None
    require_attestation: Annotated[bool, Field(
        alias="requireAttestation",
        description="Only return endpoints with valid attestation"
    )] = True

    model_config = ConfigDict(populate_by_name=True)


class ServerlessRouteResponse(BaseModel):
    """Response containing available TEE endpoints for routing.

    Clients receive multiple endpoints and can choose based on
    latency, load, or attestation verification results.
    """
    environment_id: UUID = Field(..., alias="environmentId")

    # Available endpoints for each resource type
    model_endpoints: List[TEEEndpoint] = Field(
        default_factory=list,
        alias="modelEndpoints"
    )
    auditor_endpoints: List[TEEEndpoint] = Field(
        default_factory=list,
        alias="auditorEndpoints"
    )
    app_endpoints: List[TEEEndpoint] = Field(
        default_factory=list,
        alias="appEndpoints"
    )

    # Routing metadata
    routing_timestamp: datetime = Field(..., alias="routingTimestamp")
    ttl_seconds: int = Field(
        default=60,
        alias="ttlSeconds",
        description="How long this routing info is valid"
    )

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


# Catalog item schemas for listing available resources

class CatalogModelItem(BaseModel):
    """A model available in the serverless catalog."""
    model_id: Annotated[str, Field(alias="modelId")]
    name: str
    description: Optional[str] = None
    provider: str = Field(..., description="Model provider (openai, anthropic, meta, etc.)")
    context_length: Annotated[int, Field(alias="contextLength")]
    supports_cc: Annotated[bool, Field(
        alias="supportsCc",
        description="Whether confidential computing is supported"
    )] = False
    available_regions: Annotated[List[str], Field(alias="availableRegions", default_factory=list)]

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class AuditorProfileItem(BaseModel):
    """An auditor profile available in the serverless catalog."""
    profile_id: Annotated[str, Field(alias="profileId")]
    name: str
    description: Optional[str] = None
    included_auditors: Annotated[List[str], Field(
        alias="includedAuditors",
        description="List of auditor IDs included in this profile",
        default_factory=list
    )]
    recommended_for: Annotated[List[str], Field(
        alias="recommendedFor",
        description="Use cases this profile is recommended for",
        default_factory=list
    )]

    model_config = ConfigDict(populate_by_name=True)


class CatalogAppItem(BaseModel):
    """An app available in the serverless catalog."""
    app_id: Annotated[str, Field(alias="appId")]
    name: str
    description: Optional[str] = None
    category: str = Field(..., description="App category (chat, agent, api, etc.)")
    available_regions: Annotated[List[str], Field(alias="availableRegions", default_factory=list)]

    model_config = ConfigDict(populate_by_name=True)
