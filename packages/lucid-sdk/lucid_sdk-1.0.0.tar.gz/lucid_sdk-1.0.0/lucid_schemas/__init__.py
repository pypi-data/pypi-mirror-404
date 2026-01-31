from __future__ import annotations
import warnings

# Enums
from .enums import (
    EvidenceSource,
    TrustTier,
    WorkloadClassification,
    HardwareProvider,
    AuditorRole,
    AuditorMechanism,
    MeasurementType,
    ComplianceFramework,
    AuditDecision,
    EvidenceType,
    AuditorPhase,
    UserRole,
    TeeType,
)

# Note: TeeTypeServerless backwards compatibility alias is provided via __getattr__
# at the end of this file

# Constants
from .constants import (
    LUCID_LABEL_PREFIX,
    LUCID_LABEL_AUDITOR,
    LUCID_LABEL_SCHEMA_VERSION,
    LUCID_LABEL_PHASE,
    LUCID_LABEL_INTERFACES,
    LUCID_LABEL_SIGNATURE,
    # Schema version constants
    SCHEMA_VERSION_ATTESTATION,
    SCHEMA_VERSION_AGENT,
    SCHEMA_VERSION_DASHBOARD,
    SCHEMA_VERSION_VJM,
    SCHEMA_VERSION_REFERENCE_VALUES,
    SCHEMA_VERSION_EVALUATION,
    SCHEMA_VERSION_RECEIPT,
    SCHEMA_VERSION_SECURITY,
    SCHEMA_VERSION_DEFAULT,
    # RATS-compliant schema versions (RFC 9334)
    SCHEMA_VERSION_CLAIM,
    SCHEMA_VERSION_EVIDENCE,
    # Policy schema versions
    SCHEMA_VERSION_POLICY,
    # Serverless schema versions
    SCHEMA_VERSION_SERVERLESS,
)

# Versioned schema base class
from .versioned import VersionedSchema, validate_schema_version

# Models
from .session import Session
from .auditor import Auditor
from .evaluation import EvaluationResult

# ZK Proof schemas (imported before Evidence to avoid forward references)
from .zk import (
    ZKProofSystem,
    ZKProofSchema,
    ZKCircuitMetadata,
)

# RATS-compliant schemas (RFC 9334)
from .claim import Claim
from .evidence import Evidence

# Attestation schemas (depends on Evidence)
from .attestation import (
    HardwareAttestation,
    RuntimeStatus,
    RoutingProof,
    AttestationResult,
    AIPassport,
)

from .audit_chain import (
    AuditChainItem,
    AuditChainSpec,
    VerifiableJobManifest,
)
from .location import (
    AnchorReceipt,
    LocationMeasurement,
)

# Agent schemas
from .agent import (
    ConfiguredAuditor,
    ModelConfig,
    GPUConfig,
    CreateAgentRequest,
    UpdateAgentRequest,
    AgentEndpoints,
    AgentResponse,
    AgentLogEntryResponse,
    FrontendApp,
)

# Interaction receipt schemas
from .interaction_receipt import (
    InteractionReceipt,
    ReceiptVerifyResponse,
)

# Dashboard schemas
from .dashboard import (
    WidgetPosition,
    WidgetConfig,
    DashboardResponse,
    CreateDashboardRequest,
    UpdateDashboardRequest,
)

# User schemas
from .user import (
    OrganizationMember,
    InviteUserRequest,
    InvitationResponse,
    UpdateMemberRoleRequest,
)

# Reference Values (CoRIM for manufacturer-provided golden measurements)
from .reference_values import (
    CoRIMEnvironment,
    CoRIMMeasurement,
    CoRIM,
)

# OpenTelemetry format conversion
from .otel import (
    OTelSpan,
    OTelResource,
    OTelExportData,
    attestation_result_to_otel,
    attestation_result_to_otel_attributes,
    OTEL_ATTESTATION_PREFIX,
    OTEL_EVIDENCE_PREFIX,
    OTEL_CLAIM_PREFIX,
)

# App registry schemas
from .app_registry import (
    AppCategory,
    TeeMode,
    AppLicense,
    ResourceRequirements,
    HealthCheck,
    AppEnvVar,
    NotarizationInfo,
    ChartReference,
    TeeSupport,
    CatalogApp,
    PassportTemplate,
)

# Passport display schemas
from .passport_display import (
    PassportDisplayMode,
    BannerPosition,
    BannerTheme,
    PassportDisplayConfig,
)

# App deployment schemas (includes passport models)
from .app_deployment import (
    AppConfig,
    CreateAppDeploymentRequest,
    AttestationLevel,
    AppPassportStatus,
    ContainerInfo,
    TeeAttestation,
    SecurityAttestation,
    RuntimeMetrics,
    LinkedPassports,
    VulnerabilitySummary,
    AppPassport,
    AppDeployment,
    PassportValidity,
    PassportSignatureVerification,
)

# Security schemas (image verification, SBOM, vulnerabilities)
from .security import (
    # Enums
    VulnerabilitySeverity,
    SBOMFormat,
    ScannerType,
    # Image manifest
    LayerInfo,
    ImageManifest,
    # Signature verification
    SignatureVerification,
    # Vulnerability scanning
    VulnerabilityReference,
    Vulnerability,
    VulnerabilityScan,
    # SBOM
    SBOMLicense,
    SBOMComponent,
    SBOMDependency,
    SBOMSummary,
    SBOM,
    # SLSA provenance
    SLSABuilder,
    SLSAMaterial,
    SLSAProvenance,
    # Verification result
    ImageVerificationResult,
)

# Tenant app schemas (isolated apps in TEEs)
from .tenant_app import (
    TenantAppStatus,
    CreateTenantAppRequest,
    TenantAppResponse,
    TenantAppListResponse,
    DeleteTenantAppResponse,
)

# Evidence API schemas (request/response models for evidence endpoints)
from .api_evidence import (
    EvidenceRequest,
    EvidenceVerificationRequest,
    EvidenceVerificationResponse,
    AuditLogEntry,
    AuditLogExportResponse,
)

# Policy schemas
from .policy import (
    EnforcementMode,
    PolicyChangeType,
    ClaimRequirement,
    PolicyRule,
    AuditorPolicy,
    PolicyBundle,
    # EAR-compliant appraisal records
    ClaimAppraisalStatus,
    ClaimAppraisalRecord,
    AppraisalRecord,
)

# Dashboard appraisal schemas
from .dashboard_appraisal import (
    DashboardAppraisalRow,
)

# Environment schemas (LucidEnvironment CRD)
from .environment import (
    SCHEMA_VERSION_ENVIRONMENT,
    CloudProvider,
    EnvironmentPhase,
    GatewayType,
    VectorDBType,
    ConfidentialComputingConfig,
    NodePoolConfig,
    NetworkingConfig,
    SecurityConfig,
    ClusterConfig,
    InfrastructureSpec,
    AgentAuditChainSpec,
    AgentGPUSpec,
    AgentModelSpec,
    AgentSpec,
    EnvironmentAppSpec,
    ObservabilityConfig,
    VectorDBConfig,
    GatewayConfig,
    ServicesSpec,
    ConditionStatus,
    EnvironmentCondition,
    EndpointsStatus,
    LucidEnvironmentStatus,
    ObjectMeta,
    LucidEnvironmentSpec,
    LucidEnvironment,
)

# Note: EnvironmentTeeType backwards compatibility alias is provided via __getattr__
# at the end of this file

# Pagination schemas
from .pagination import (
    DEFAULT_LIMIT as PAGINATION_DEFAULT_LIMIT,
    MAX_LIMIT as PAGINATION_MAX_LIMIT,
    PaginationParams,
    PaginatedResponse,
    CursorData,
    CursorPaginationParams,
    CursorPaginatedResponse,
    HybridPaginationParams,
    HybridPaginatedResponse,
)

# Serverless schemas
from .serverless import (
    DataResidency,
    AuditorProfile,
    EnvironmentStatus,
    ResourceType,
    ResourceStatus,
    AuditorConfig,
    EnvironmentConfig,
    CreateEnvironmentRequest,
    UpdateEnvironmentRequest,
    EnvironmentResponse,
    TEEEndpoint,
    ServerlessRouteRequest,
    ServerlessRouteResponse,
    CatalogModelItem,
    AuditorProfileItem,
    CatalogAppItem,
)

__all__ = [
    # Enums
    "EvidenceSource",
    "TrustTier",
    "WorkloadClassification",
    "HardwareProvider",
    "AuditorRole",
    "AuditorMechanism",
    "MeasurementType",
    "ComplianceFramework",
    "AuditDecision",
    "EvidenceType",
    "AuditorPhase",
    "UserRole",
    "TeeType",
    "TeeTypeServerless",
    # Constants
    "LUCID_LABEL_PREFIX",
    "LUCID_LABEL_AUDITOR",
    "LUCID_LABEL_SCHEMA_VERSION",
    "LUCID_LABEL_PHASE",
    "LUCID_LABEL_INTERFACES",
    "LUCID_LABEL_SIGNATURE",
    # Schema version constants
    "SCHEMA_VERSION_ATTESTATION",
    "SCHEMA_VERSION_AGENT",
    "SCHEMA_VERSION_DASHBOARD",
    "SCHEMA_VERSION_VJM",
    "SCHEMA_VERSION_REFERENCE_VALUES",
    "SCHEMA_VERSION_EVALUATION",
    "SCHEMA_VERSION_RECEIPT",
    "SCHEMA_VERSION_SECURITY",
    "SCHEMA_VERSION_DEFAULT",
    # RATS-compliant schema versions (RFC 9334)
    "SCHEMA_VERSION_CLAIM",
    "SCHEMA_VERSION_EVIDENCE",
    # Policy schema versions
    "SCHEMA_VERSION_POLICY",
    # Versioned schema base class
    "VersionedSchema",
    "validate_schema_version",
    # Models
    "Session",
    "Auditor",
    "EvaluationResult",
    "HardwareAttestation",
    "RuntimeStatus",
    "RoutingProof",
    "AttestationResult",
    "AIPassport",
    "AuditChainItem",
    "AuditChainSpec",
    "VerifiableJobManifest",
    "AnchorReceipt",
    "LocationMeasurement",
    # RATS-compliant schemas (RFC 9334)
    "Claim",
    "Evidence",
    # Agent schemas
    "ConfiguredAuditor",
    "ModelConfig",
    "GPUConfig",
    "CreateAgentRequest",
    "UpdateAgentRequest",
    "AgentEndpoints",
    "AgentResponse",
    "AgentLogEntryResponse",
    "FrontendApp",
    # Interaction receipt schemas
    "InteractionReceipt",
    "ReceiptVerifyResponse",
    # Dashboard schemas
    "WidgetPosition",
    "WidgetConfig",
    "DashboardResponse",
    "CreateDashboardRequest",
    "UpdateDashboardRequest",
    # User schemas
    "OrganizationMember",
    "InviteUserRequest",
    "InvitationResponse",
    "UpdateMemberRoleRequest",
    # Reference values
    "CoRIMEnvironment",
    "CoRIMMeasurement",
    "CoRIM",
    # ZK Proof schemas
    "ZKProofSystem",
    "ZKProofSchema",
    "ZKCircuitMetadata",
    # OpenTelemetry format conversion
    "OTelSpan",
    "OTelResource",
    "OTelExportData",
    "attestation_result_to_otel",
    "attestation_result_to_otel_attributes",
    "OTEL_ATTESTATION_PREFIX",
    "OTEL_EVIDENCE_PREFIX",
    "OTEL_CLAIM_PREFIX",
    # App registry schemas
    "AppCategory",
    "TeeMode",
    "AppLicense",
    "ResourceRequirements",
    "HealthCheck",
    "AppEnvVar",
    "NotarizationInfo",
    "ChartReference",
    "TeeSupport",
    "CatalogApp",
    "PassportTemplate",
    # Passport display schemas
    "PassportDisplayMode",
    "BannerPosition",
    "BannerTheme",
    "PassportDisplayConfig",
    # App deployment schemas
    "AppConfig",
    "CreateAppDeploymentRequest",
    # App passport schemas
    "AttestationLevel",
    "AppPassportStatus",
    "TeeType",
    "ContainerInfo",
    "TeeAttestation",
    "SecurityAttestation",
    "RuntimeMetrics",
    "LinkedPassports",
    "VulnerabilitySummary",
    "AppPassport",
    "AppDeployment",
    "PassportValidity",
    "PassportSignatureVerification",
    # Security schemas
    "VulnerabilitySeverity",
    "SBOMFormat",
    "ScannerType",
    "LayerInfo",
    "ImageManifest",
    "SignatureVerification",
    "VulnerabilityReference",
    "Vulnerability",
    "VulnerabilityScan",
    "SBOMLicense",
    "SBOMComponent",
    "SBOMDependency",
    "SBOMSummary",
    "SBOM",
    "SLSABuilder",
    "SLSAMaterial",
    "SLSAProvenance",
    "ImageVerificationResult",
    # Tenant app schemas
    "TenantAppStatus",
    "CreateTenantAppRequest",
    "TenantAppResponse",
    "TenantAppListResponse",
    "DeleteTenantAppResponse",
    # Evidence API schemas
    "EvidenceRequest",
    "EvidenceVerificationRequest",
    "EvidenceVerificationResponse",
    "AuditLogEntry",
    "AuditLogExportResponse",
    # Policy schemas
    "EnforcementMode",
    "PolicyChangeType",
    "ClaimRequirement",
    "PolicyRule",
    "AuditorPolicy",
    "PolicyBundle",
    # EAR-compliant appraisal records
    "ClaimAppraisalStatus",
    "ClaimAppraisalRecord",
    "AppraisalRecord",
    # Dashboard appraisal schemas
    "DashboardAppraisalRow",
    # Pagination schemas
    "PAGINATION_DEFAULT_LIMIT",
    "PAGINATION_MAX_LIMIT",
    "PaginationParams",
    "PaginatedResponse",
    "CursorData",
    "CursorPaginationParams",
    "CursorPaginatedResponse",
    "HybridPaginationParams",
    "HybridPaginatedResponse",
    # Environment schemas (LucidEnvironment CRD)
    "SCHEMA_VERSION_ENVIRONMENT",
    "CloudProvider",
    "EnvironmentTeeType",
    "EnvironmentPhase",
    "GatewayType",
    "VectorDBType",
    "ConfidentialComputingConfig",
    "NodePoolConfig",
    "NetworkingConfig",
    "SecurityConfig",
    "ClusterConfig",
    "InfrastructureSpec",
    "AgentAuditChainSpec",
    "AgentGPUSpec",
    "AgentModelSpec",
    "AgentSpec",
    "EnvironmentAppSpec",
    "ObservabilityConfig",
    "VectorDBConfig",
    "GatewayConfig",
    "ServicesSpec",
    "ConditionStatus",
    "EnvironmentCondition",
    "EndpointsStatus",
    "LucidEnvironmentStatus",
    "ObjectMeta",
    "LucidEnvironmentSpec",
    "LucidEnvironment",
    # Serverless schemas
    "SCHEMA_VERSION_SERVERLESS",
    "DataResidency",
    "AuditorProfile",
    "EnvironmentStatus",
    "ResourceType",
    "ResourceStatus",
    "TeeTypeServerless",
    "AuditorConfig",
    "EnvironmentConfig",
    "CreateEnvironmentRequest",
    "UpdateEnvironmentRequest",
    "EnvironmentResponse",
    "TEEEndpoint",
    "ServerlessRouteRequest",
    "ServerlessRouteResponse",
    "CatalogModelItem",
    "AuditorProfileItem",
    "CatalogAppItem",
]


def __getattr__(name: str):
    """Module-level __getattr__ for deprecation warnings on backwards compatibility aliases.

    DEPRECATED aliases that will be removed in v2.0:
    - EnvironmentTeeType: Use TeeType instead
    - TeeTypeServerless: Use TeeType instead
    """
    if name == "EnvironmentTeeType":
        warnings.warn(
            "EnvironmentTeeType is deprecated and will be removed in v2.0. "
            "Use TeeType instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return TeeType
    if name == "TeeTypeServerless":
        warnings.warn(
            "TeeTypeServerless is deprecated and will be removed in v2.0. "
            "Use TeeType instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return TeeType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
