from __future__ import annotations
import warnings
from enum import Enum


# =============================================================================
# ATTESTATION & EVIDENCE
# =============================================================================
# Enums related to evidence sources, types, and trust levels in the
# attestation chain. These define what evidence is collected and how
# trustworthy it is considered.
# =============================================================================

class EvidenceSource(str, Enum):
    """Source of evidence/measurements in the attestation chain.

    Identifies which device or component produced a measurement.
    """
    # Hardware attestation sources
    DC_SCM = "dc_scm"                        # OCP DC-SCM with PUF
    FLEXNIC = "flexnic"                      # FlexNIC (shadow mode network monitoring)
    TPM = "tpm"                              # TPM 2.0
    GPU_CC = "gpu_cc"                        # GPU Confidential Computing (NVIDIA/AMD)
    HSM = "hsm"                              # Hardware Security Module

    # SmartNICs/DPUs
    SMARTNIC_NVIDIA = "smartnic_nvidia"      # BlueField DPU
    SMARTNIC_AMD = "smartnic_amd"            # Pensando
    SMARTNIC_INTEL = "smartnic_intel"        # Intel IPU

    # Software/auditor sources
    AUDITOR = "auditor"                      # Software auditor in chain
    TEE = "tee"                              # TEE runtime environment
    VERIFIER = "verifier"                    # Lucid Verifier service
    OPERATOR = "operator"                    # Lucid Operator (sidecar injection)


class EvidenceType(str, Enum):
    """Types of evidence an auditor can produce"""
    MEASUREMENT = "measurement"      # Quantitative metric
    ASSERTION = "assertion"          # Boolean claim
    LOG = "log"                      # Audit trail entry
    ANOMALY = "anomaly"              # Detected deviation


class TrustTier(str, Enum):
    """Trust tier for evidence appraisal (per RFC 9334 EAR format)."""
    AFFIRMING = "affirming"              # Evidence fully validates
    WARNING = "warning"                  # Some issues but usable
    CONTRAINDICATED = "contraindicated"  # Evidence indicates compromise
    NONE = "none"                        # Unable to verify


# =============================================================================
# AUDIT & DECISION
# =============================================================================
# Enums that control how auditors operate, what decisions they can make,
# and at which phase of the pipeline they execute.
# =============================================================================

class AuditDecision(str, Enum):
    """Decision an auditor can make about a request/response"""
    PROCEED = "proceed"      # Allow the request to continue
    DENY = "deny"            # Block the request entirely
    REDACT = "redact"        # Allow but modify content
    WARN = "warn"            # Allow but flag for review


class AuditorPhase(str, Enum):
    """Execution phases for auditors."""
    build = "build"
    input_gate = "input_gate"
    runtime = "runtime"
    output_gate = "output_gate"


class AuditorRole(str, Enum):
    """The persona or goal of the audit node."""
    developer = "developer"
    security = "security"
    compliance = "compliance"


class AuditorMechanism(str, Enum):
    """The technical method used by an auditor to verify state."""
    rule_based_code = "rule_based_code"
    formal_verification = "formal_verification"
    signature_verification = "signature_verification"
    llm_judge = "llm_judge"
    statistical_detector = "statistical_detector"
    benchmark_suite = "benchmark_suite"


# =============================================================================
# MEASUREMENT TYPES
# =============================================================================
# Granular measurement types that enable automatic visualization selection
# for dashboards and reporting. Each type maps to an appropriate chart or
# display component.
# =============================================================================

class MeasurementType(str, Enum):
    """The data type/intent of a measurement.

    Granular types enable automatic visualization selection for dashboards.
    """
    # Location & Geographic
    location_coordinates = "location_coordinates"     # lat/lon -> Map
    location_region = "location_region"               # region codes -> Table
    location_anchors = "location_anchors"             # anchor data -> Tree/Table

    # Time Series
    time_series_metric = "time_series_metric"         # -> Line chart
    time_series_event = "time_series_event"           # -> Timeline

    # Scores
    score_binary = "score_binary"                     # pass/fail -> Badge
    score_percentage = "score_percentage"             # 0-100% -> Gauge
    score_normalized = "score_normalized"             # 0.0-1.0 -> Stat card
    score_multi_dimensional = "score_multi_dimensional"  # -> Radar chart

    # Categorical
    category = "category"                             # -> Badge/Label
    category_list = "category_list"                   # -> Tag list
    categorical_count = "categorical_count"           # -> Bar chart
    categorical_proportion = "categorical_proportion" # -> Pie chart

    # Distribution
    distribution_histogram = "distribution_histogram" # -> Histogram

    # Hierarchical
    hierarchical_tree = "hierarchical_tree"           # -> Tree graph

    # Resource
    resource_tokens = "resource_tokens"               # -> Stat card/Line
    resource_cost = "resource_cost"                   # -> Stat card
    resource_latency = "resource_latency"             # -> Histogram

    # Security/Compliance
    security_finding = "security_finding"             # -> Table
    security_severity = "security_severity"           # -> Pie/Bar
    compliance_status = "compliance_status"           # -> Table

    # General-purpose types
    quantity = "quantity"
    benchmark = "benchmark"
    policy_violation = "policy_violation"
    conformity = "conformity"
    hash = "hash"
    telemetry = "telemetry"
    audit_pass = "audit_pass"
    other = "other"


class WorkloadClassification(str, Enum):
    """Workload classification from multi-signal analysis."""
    TRAINING = "training"
    INFERENCE = "inference"
    UNKNOWN = "unknown"
    INCONSISTENT = "inconsistent"  # Signals disagree


# =============================================================================
# COMPLIANCE FRAMEWORKS
# =============================================================================
# Standardized compliance frameworks for policy mapping, organized by
# geographic region. Used to map auditor findings to regulatory requirements.
# =============================================================================

class ComplianceFramework(str, Enum):
    """Standardized compliance frameworks for policy mapping.

    Organized by region:
    - US: 12 frameworks (SOC2, SOX, HIPAA, etc.)
    - EU: 7 frameworks (GDPR, EU AI Act, DORA, etc.)
    - India: 7 frameworks (DPDP, RBI, SEBI, etc.)
    - APAC/International: 10 frameworks (LGPD, PIPL, CSA STAR, etc.)
    - Legacy: 3 frameworks (kept for backwards compatibility)
    """

    # US Frameworks (12)
    soc2 = "soc2"
    sox = "sox"
    ccpa = "ccpa"
    hipaa = "hipaa"
    pci_dss = "pci_dss"
    glba = "glba"
    ferpa = "ferpa"
    fedramp = "fedramp"
    cmmc = "cmmc"
    colorado_ai = "colorado_ai"
    nist_ai_rmf = "nist_ai_rmf"
    aiuc_1 = "aiuc_1"

    # EU Frameworks (7)
    gdpr = "gdpr"
    eu_ai_act = "eu_ai_act"
    dora = "dora"
    nis2 = "nis2"
    iso_27001 = "iso_27001"
    iso_42001 = "iso_42001"
    c5 = "c5"

    # India Frameworks (7)
    dpdp = "dpdp"
    rbi_free_ai = "rbi_free_ai"
    rbi_it = "rbi_it"
    sebi_cscrf = "sebi_cscrf"
    cert_in = "cert_in"
    irdai = "irdai"
    india_ai = "india_ai"

    # APAC/International Frameworks (10)
    lgpd = "lgpd"
    pipl = "pipl"
    appi = "appi"
    pdpa_sg = "pdpa_sg"
    pdpa_th = "pdpa_th"
    csa_star = "csa_star"
    hitrust = "hitrust"
    cis_controls = "cis_controls"
    cobit = "cobit"
    oecd_ai = "oecd_ai"

    # DEPRECATED: Legacy frameworks - will be removed in v2.0
    # Use specific frameworks like nist_ai_rmf, cmmc, or fedramp instead
    nist_800_53 = "nist_800_53"  # Deprecated: use nist_ai_rmf or specific NIST controls
    itar = "itar"  # Deprecated: use cmmc or fedramp for export control compliance
    export_control = "export_control"  # Deprecated: use cmmc or fedramp


# =============================================================================
# HARDWARE & TEE
# =============================================================================
# Enums related to Trusted Execution Environments (TEE) and hardware
# security providers. These define the supported confidential computing
# platforms and their configurations.
# =============================================================================

class HardwareProvider(str, Enum):
    """Supported Trusted Execution Environment (TEE) hardware providers."""
    aws_nitro = "aws_nitro"
    intel_tdx = "intel_tdx"
    amd_sev = "amd_sev"
    nvidia_h100 = "nvidia_h100"


class TeeType(str, Enum):
    """Unified Trusted Execution Environment types.

    This enum consolidates all TEE hardware types used across the platform,
    including both on-premise hardware and cloud-specific implementations.
    """
    # On-premise / Hardware TEE types
    SGX = "sgx"          # Intel Software Guard Extensions
    SEV_SNP = "sev-snp"  # AMD Secure Encrypted Virtualization - Secure Nested Paging
    TDX = "tdx"          # Intel Trust Domain Extensions

    # Cloud-specific / Serverless TEE types
    AWS_NITRO = "aws_nitro"    # AWS Nitro Enclaves
    INTEL_TDX = "intel_tdx"    # Intel TDX (cloud variant naming)
    AMD_SEV = "amd_sev"        # AMD SEV (cloud variant naming)
    NVIDIA_CC = "nvidia_cc"    # NVIDIA Confidential Computing


def __getattr__(name: str):
    """Module-level __getattr__ for deprecation warnings on backwards compatibility aliases."""
    if name == "TeeTypeServerless":
        warnings.warn(
            "TeeTypeServerless is deprecated and will be removed in v2.0. "
            "Use TeeType instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return TeeType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# =============================================================================
# USER & ACCESS
# =============================================================================
# Enums for user management, roles, and access control within the platform.
# =============================================================================

class UserRole(str, Enum):
    """User roles within an organization."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"
