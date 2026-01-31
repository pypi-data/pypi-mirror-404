"""LucidEnvironment CRD schema for declarative platform deployment.

This module defines the LucidEnvironment Custom Resource Definition (CRD)
that serves as the single declarative output of the deployment wizard,
capturing infrastructure, agents, apps, and services configuration.

Example usage:
    ```yaml
    apiVersion: lucid.io/v1alpha1
    kind: LucidEnvironment
    metadata:
      name: my-platform
    spec:
      infrastructure:
        provider: gcp
        region: us-central1
        ...
    ```
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SCHEMA_VERSION_DEFAULT
from .agent import ConfiguredAuditor, FrontendApp, GPUConfig, ModelConfig
from .app_deployment import AppConfig
from .app_registry import TeeMode
from .enums import TeeType
from .passport_display import PassportDisplayConfig
from .policy import AuditorPolicy

logger = logging.getLogger(__name__)

# Schema version for LucidEnvironment
SCHEMA_VERSION_ENVIRONMENT = "1.0.0-alpha"


# =============================================================================
# Enums
# =============================================================================


class CloudProvider(str, Enum):
    """Supported cloud providers."""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    LOCAL = "local"


class EnvironmentPhase(str, Enum):
    """Phase of the environment lifecycle."""
    PENDING = "Pending"
    PROVISIONING = "Provisioning"
    READY = "Ready"
    UPDATING = "Updating"
    DEGRADED = "Degraded"
    FAILED = "Failed"
    DELETING = "Deleting"


class GatewayType(str, Enum):
    """Gateway/service mesh type."""
    ISTIO = "istio"
    ENVOY = "envoy"
    NGINX = "nginx"
    TRAEFIK = "traefik"


class VectorDBType(str, Enum):
    """Vector database types."""
    MILVUS = "milvus"
    QDRANT = "qdrant"
    PINECONE = "pinecone"
    WEAVIATE = "weaviate"
    PGVECTOR = "pgvector"


# =============================================================================
# Infrastructure Spec
# =============================================================================


class ConfidentialComputingConfig(BaseModel):
    """Confidential computing configuration."""
    enabled: bool = Field(default=True, description="Enable confidential computing")
    tee_type: TeeType = Field(default=TeeType.SEV_SNP, alias="teeType", description="TEE technology to use")
    attestation_enabled: bool = Field(default=True, alias="attestationEnabled", description="Enable hardware attestation")

    model_config = ConfigDict(populate_by_name=True)


class NodePoolConfig(BaseModel):
    """Kubernetes node pool configuration."""
    name: str = Field(..., description="Node pool name")
    machine_type: str = Field(..., alias="machineType", description="Instance type (e.g., a3-highgpu-8g)")
    min_nodes: int = Field(default=1, alias="minNodes", ge=0)
    max_nodes: int = Field(default=3, alias="maxNodes", ge=1)
    gpu_type: Optional[str] = Field(default=None, alias="gpuType", description="GPU type (e.g., nvidia-h100-80gb)")
    gpu_count: int = Field(default=0, alias="gpuCount", ge=0)
    confidential_nodes: bool = Field(default=True, alias="confidentialNodes", description="Enable CC for this pool")
    spot: bool = Field(default=False, description="Use spot/preemptible instances")
    labels: Dict[str, str] = Field(default_factory=dict, description="Node labels")
    taints: List[str] = Field(default_factory=list, description="Node taints (e.g., 'gpu=true:NoSchedule')")

    model_config = ConfigDict(populate_by_name=True)


class NetworkingConfig(BaseModel):
    """Cluster networking configuration."""
    private_cluster: bool = Field(default=True, alias="privateCluster", description="Private GKE/EKS/AKS cluster")
    vpc_name: Optional[str] = Field(default=None, alias="vpcName", description="Existing VPC name")
    subnet_cidr: str = Field(default="10.0.0.0/16", alias="subnetCidr", description="Subnet CIDR range")
    pod_cidr: str = Field(default="10.1.0.0/16", alias="podCidr", description="Pod CIDR range")
    service_cidr: str = Field(default="10.2.0.0/16", alias="serviceCidr", description="Service CIDR range")
    enable_network_policy: bool = Field(default=True, alias="enableNetworkPolicy")

    model_config = ConfigDict(populate_by_name=True)


class SecurityConfig(BaseModel):
    """Cluster security configuration."""
    workload_identity: bool = Field(default=True, alias="workloadIdentity", description="Enable workload identity")
    binary_authorization: bool = Field(default=True, alias="binaryAuthorization", description="Enable binary authorization")
    shielded_nodes: bool = Field(default=True, alias="shieldedNodes", description="Enable shielded GKE nodes")
    secrets_encryption: bool = Field(default=True, alias="secretsEncryption", description="Enable secrets encryption at rest")
    kms_key_name: Optional[str] = Field(default=None, alias="kmsKeyName", description="KMS key for envelope encryption")

    model_config = ConfigDict(populate_by_name=True)


class ClusterConfig(BaseModel):
    """Kubernetes cluster configuration."""
    name: str = Field(..., description="Cluster name")
    kubernetes_version: Annotated[str, Field(alias="kubernetesVersion")] = "1.29"
    node_pools: Annotated[List[NodePoolConfig], Field(alias="nodePools", default_factory=list)]
    networking: NetworkingConfig = Field(default_factory=NetworkingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)

    model_config = ConfigDict(populate_by_name=True)


class InfrastructureSpec(BaseModel):
    """Infrastructure specification for the environment."""
    provider: CloudProvider = Field(..., description="Cloud provider")
    region: str = Field(..., description="Deployment region (e.g., us-central1)")
    project_id: Annotated[Optional[str], Field(alias="projectId", description="Cloud project ID (GCP) or account ID")] = None
    subscription_id: Annotated[Optional[str], Field(alias="subscriptionId", description="Azure subscription ID")] = None
    resource_group: Annotated[Optional[str], Field(alias="resourceGroup", description="Azure resource group")] = None
    confidential_computing: Annotated[ConfidentialComputingConfig, Field(
        alias="confidentialComputing",
        default_factory=ConfidentialComputingConfig
    )]
    cluster: ClusterConfig = Field(..., description="Kubernetes cluster configuration")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator('region')
    @classmethod
    def validate_region(cls, v: str) -> str:
        """Validate region format."""
        if not v or len(v) < 2:
            raise ValueError("Region must be specified")
        return v


# =============================================================================
# Agent Spec
# =============================================================================


class AgentAuditChainSpec(BaseModel):
    """Audit chain specification for an agent."""
    pre_request: Annotated[List[ConfiguredAuditor], Field(alias="preRequest", default_factory=list)]
    request: List[ConfiguredAuditor] = Field(default_factory=list)
    response: List[ConfiguredAuditor] = Field(default_factory=list)
    post_response: Annotated[List[ConfiguredAuditor], Field(alias="postResponse", default_factory=list)]

    model_config = ConfigDict(populate_by_name=True)

    def to_dict(self) -> Dict[str, List[ConfiguredAuditor]]:
        """Convert to dict format used by CreateAgentRequest."""
        return {
            "pre_request": self.pre_request,
            "request": self.request,
            "response": self.response,
            "post_response": self.post_response,
        }


class AgentGPUSpec(BaseModel):
    """GPU specification for an agent."""
    type: str = Field(..., description="GPU type (e.g., H100, A100)")
    memory: str = Field(default="80GB", description="GPU memory")
    count: int = Field(default=1, ge=1, description="Number of GPUs")

    model_config = ConfigDict(populate_by_name=True)


class AgentModelSpec(BaseModel):
    """Model specification for an agent."""
    id: str = Field(..., description="Model identifier (e.g., meta-llama/Llama-3.3-70B)")
    name: Optional[str] = Field(default=None, description="Display name")
    quantization: Optional[str] = Field(default=None, description="Quantization format (e.g., awq, gptq)")

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


class AgentSpec(BaseModel):
    """Agent specification for the environment.

    This is a higher-level specification that maps to CreateAgentRequest
    when deploying.
    """
    name: str = Field(..., description="Agent name")
    model: AgentModelSpec = Field(..., description="Model configuration")
    gpu: AgentGPUSpec = Field(..., description="GPU requirements")
    audit_chain: Annotated[Optional[AgentAuditChainSpec], Field(alias="auditChain")] = None
    frontend_app: Annotated[Optional[FrontendApp], Field(alias="frontendApp")] = None
    passport_display: Annotated[Optional[PassportDisplayConfig], Field(alias="passportDisplay")] = None
    replicas: int = Field(default=1, ge=1, description="Number of replicas")
    enabled: bool = Field(default=True, description="Whether agent is enabled")

    model_config = ConfigDict(populate_by_name=True, protected_namespaces=())


# =============================================================================
# App Spec
# =============================================================================


class EnvironmentAppSpec(BaseModel):
    """App specification for the environment.

    Extends AppConfig with environment-level settings.
    """
    app_id: Annotated[str, Field(alias="appId", description="Reference to CatalogApp.id")]
    tee_mode: Annotated[TeeMode, Field(alias="teeMode")] = TeeMode.ADJACENT
    replicas: int = Field(default=1, ge=1)
    enabled: bool = Field(default=True)
    env_vars: Annotated[Dict[str, str], Field(alias="envVars", default_factory=dict)]
    secrets: Dict[str, str] = Field(default_factory=dict)
    resources: Optional[Dict[str, str]] = None
    expose_port: Annotated[Optional[int], Field(alias="exposePort", description="Port to expose externally")] = None

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Services Spec
# =============================================================================


class ObservabilityConfig(BaseModel):
    """Observability services configuration."""
    enabled: bool = Field(default=True)
    metrics_enabled: bool = Field(default=True, alias="metricsEnabled")
    tracing_enabled: bool = Field(default=True, alias="tracingEnabled")
    logging_enabled: bool = Field(default=True, alias="loggingEnabled")
    prometheus_retention: str = Field(default="15d", alias="prometheusRetention")

    model_config = ConfigDict(populate_by_name=True)


class VectorDBConfig(BaseModel):
    """Vector database configuration."""
    enabled: bool = Field(default=False)
    type: VectorDBType = Field(default=VectorDBType.MILVUS)
    storage_size: str = Field(default="100Gi", alias="storageSize")
    replicas: int = Field(default=1, ge=1)

    model_config = ConfigDict(populate_by_name=True)


class GatewayConfig(BaseModel):
    """API gateway/service mesh configuration."""
    enabled: bool = Field(default=True)
    type: GatewayType = Field(default=GatewayType.ISTIO)
    mtls_enabled: bool = Field(default=True, alias="mtlsEnabled")
    rate_limiting_enabled: bool = Field(default=True, alias="rateLimitingEnabled")

    model_config = ConfigDict(populate_by_name=True)


class ServicesSpec(BaseModel):
    """Platform services specification."""
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig, alias="vectorDb")
    gateway: GatewayConfig = Field(default_factory=GatewayConfig)

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Environment Status
# =============================================================================


class ConditionStatus(str, Enum):
    """Condition status values."""
    TRUE = "True"
    FALSE = "False"
    UNKNOWN = "Unknown"


class EnvironmentCondition(BaseModel):
    """Condition representing the state of an environment aspect."""
    type: str = Field(..., description="Condition type (e.g., InfrastructureReady)")
    status: ConditionStatus = Field(default=ConditionStatus.UNKNOWN)
    reason: Optional[str] = None
    message: Optional[str] = None
    last_transition_time: Optional[str] = Field(default=None, alias="lastTransitionTime")

    model_config = ConfigDict(populate_by_name=True)


class EndpointsStatus(BaseModel):
    """Endpoints for accessing the environment."""
    observer: Optional[str] = None
    verifier: Optional[str] = None
    gateway: Optional[str] = None
    grafana: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class LucidEnvironmentStatus(BaseModel):
    """Status of a LucidEnvironment."""
    phase: EnvironmentPhase = Field(default=EnvironmentPhase.PENDING)
    conditions: List[EnvironmentCondition] = Field(default_factory=list)
    agent_count: int = Field(default=0, alias="agentCount")
    ready_agents: int = Field(default=0, alias="readyAgents")
    app_count: int = Field(default=0, alias="appCount")
    ready_apps: int = Field(default=0, alias="readyApps")
    endpoints: Optional[EndpointsStatus] = None
    last_reconcile_time: Optional[str] = Field(default=None, alias="lastReconcileTime")
    observed_generation: int = Field(default=0, alias="observedGeneration")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# K8s Metadata
# =============================================================================


class ObjectMeta(BaseModel):
    """Kubernetes-style object metadata."""
    name: str = Field(..., description="Resource name")
    namespace: str = Field(default="default")
    labels: Dict[str, str] = Field(default_factory=dict)
    annotations: Dict[str, str] = Field(default_factory=dict)
    uid: Optional[str] = None
    resource_version: Optional[str] = Field(default=None, alias="resourceVersion")
    generation: int = Field(default=1)
    creation_timestamp: Optional[str] = Field(default=None, alias="creationTimestamp")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# LucidEnvironment Spec
# =============================================================================


class LucidEnvironmentSpec(BaseModel):
    """Specification for a complete Lucid environment."""
    infrastructure: InfrastructureSpec
    agents: List[AgentSpec] = Field(default_factory=list)
    apps: List[EnvironmentAppSpec] = Field(default_factory=list)
    services: ServicesSpec = Field(default_factory=ServicesSpec)
    policies: List[AuditorPolicy] = Field(
        default_factory=list,
        description="Policy definitions for auditors. Auditor instances reference these via policyId."
    )

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# LucidEnvironment CRD
# =============================================================================


class LucidEnvironment(BaseModel):
    """LucidEnvironment Custom Resource Definition.

    This is the top-level declarative configuration for a complete Lucid
    platform deployment, including infrastructure, agents, apps, and services.

    Example:
        ```yaml
        apiVersion: lucid.io/v1alpha1
        kind: LucidEnvironment
        metadata:
          name: my-platform
        spec:
          infrastructure:
            provider: gcp
            region: us-central1
            projectId: my-project
            cluster:
              name: lucid-prod
          agents:
            - name: llama-assistant
              model:
                id: meta-llama/Llama-3.3-70B
              gpu:
                type: H100
                memory: 80GB
          apps:
            - appId: openhands
              teeMode: adjacent
          services:
            observability:
              enabled: true
        ```
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_ENVIRONMENT

    api_version: str = Field(
        default="lucid.io/v1alpha1",
        alias="apiVersion",
        description="API version for the CRD"
    )
    kind: str = Field(
        default="LucidEnvironment",
        description="Resource kind"
    )
    metadata: ObjectMeta
    spec: LucidEnvironmentSpec
    status: Optional[LucidEnvironmentStatus] = Field(default=None)

    # Schema version for backwards compatibility
    schema_version: str = Field(
        default=SCHEMA_VERSION_ENVIRONMENT,
        alias="schemaVersion",
        description="Schema version for backwards compatibility"
    )

    model_config = ConfigDict(populate_by_name=True)

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

    @field_validator('kind')
    @classmethod
    def validate_kind(cls, v: str) -> str:
        """Ensure kind is LucidEnvironment."""
        if v != "LucidEnvironment":
            raise ValueError(f"Invalid kind: {v}, expected LucidEnvironment")
        return v

    def get_agent_count(self) -> int:
        """Get the number of enabled agents."""
        return len([a for a in self.spec.agents if a.enabled])

    def get_app_count(self) -> int:
        """Get the number of enabled apps."""
        return len([a for a in self.spec.apps if a.enabled])
