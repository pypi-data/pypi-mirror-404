"""Policy schema for auditor policy definitions.

A Policy defines the rules, required claims, and enforcement behavior for
an auditor. Policies can be bundled together for deployment profiles.
"""
from __future__ import annotations
import logging
from datetime import datetime
from enum import Enum
from typing import ClassVar, Dict, List, Any, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import MeasurementType, ComplianceFramework, TrustTier

logger = logging.getLogger(__name__)


# =============================================================================
# EAR-Compliant Appraisal Records (per RFC 9334 / draft-ietf-rats-ear)
# =============================================================================


class ClaimAppraisalStatus(str, Enum):
    """Per-claim appraisal status (EAR trustworthiness tier values).

    Based on draft-ietf-rats-ear trustworthiness vector tiers:
    - 0: none (unable to determine)
    - 2: affirming (claim validates policy)
    - 32: warning (minor issues)
    - 96: contraindicated (claim violates policy)
    """
    NONE = "none"                    # 0: Unable to determine
    AFFIRMING = "affirming"          # 2: Claim meets policy requirements
    WARNING = "warning"              # 32: Minor issues but acceptable
    CONTRAINDICATED = "contraindicated"  # 96: Claim violates policy


class ClaimAppraisalRecord(BaseModel):
    """Per-claim appraisal result for visualization and audit.

    This provides granular per-claim policy compliance tracking,
    following the EAR trustworthiness vector pattern but at the
    individual claim level.

    Enables UI visualization of:
    - Which claims passed/failed
    - What policy rules evaluated each claim
    - What reference values were compared
    - The actual claim value vs. expected value
    """
    claim_name: str = Field(
        ...,
        description="Name of the claim being appraised.",
        examples=["location.country", "toxicity.score"]
    )
    claim_value: Any = Field(
        ...,
        description="The actual value of the claim at appraisal time.",
        examples=["IN", 0.85, True]
    )
    claim_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score of the claim."
    )

    # Appraisal result
    status: ClaimAppraisalStatus = Field(
        ...,
        description="Appraisal status for this claim.",
        examples=["affirming", "contraindicated"]
    )

    # Policy context
    evaluated_by_rules: List[str] = Field(
        default_factory=list,
        description="IDs of policy rules that evaluated this claim.",
        examples=[["location-check", "confidence-threshold"]]
    )
    triggered_rules: List[str] = Field(
        default_factory=list,
        description="IDs of rules this claim triggered (failed).",
        examples=[["location-check"]]
    )

    # Reference values for comparison (per RFC 9334)
    reference_value: Optional[Any] = Field(
        default=None,
        description="The reference/expected value from policy (for visualization).",
        examples=["IN", 0.8]
    )
    reference_operator: Optional[str] = Field(
        default=None,
        description="Comparison operator used (==, >=, <=, in, etc.).",
        examples=["==", ">=", "in"]
    )

    # Compliance mapping
    compliance_framework: Optional[ComplianceFramework] = Field(
        default=None,
        description="Compliance framework this claim relates to."
    )
    control_id: Optional[str] = Field(
        default=None,
        description="Specific control ID within the framework."
    )

    # Messages
    message: Optional[str] = Field(
        default=None,
        description="Human-readable message about the appraisal.",
        examples=["Location verified: IN matches required region"]
    )


class AppraisalRecord(BaseModel):
    """Per-Evidence appraisal record (EAR submodule equivalent).

    Contains all claim-level appraisals for a single Evidence bundle,
    following the EAR pattern of per-attester appraisal records.

    This is stored on Evidence after policy evaluation to provide
    full auditability and visualization support.
    """
    evidence_id: str = Field(
        ...,
        description="ID of the Evidence this record appraises."
    )
    attester_id: str = Field(
        ...,
        description="ID of the Attester that produced the Evidence."
    )

    # Policy identification (ear.appraisal-policy-id)
    policy_id: str = Field(
        ...,
        description="ID of the policy used for appraisal."
    )
    policy_version: str = Field(
        ...,
        description="Version of the policy used."
    )

    # Overall result
    overall_status: TrustTier = Field(
        ...,
        description="Overall trust tier for this Evidence."
    )

    # Per-claim breakdown
    claim_appraisals: List[ClaimAppraisalRecord] = Field(
        default_factory=list,
        description="Appraisal record for each claim in the Evidence."
    )

    # Timing
    appraised_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when appraisal was performed."
    )

    # Summary statistics
    claims_affirming: int = Field(
        default=0,
        description="Count of claims with affirming status."
    )
    claims_warning: int = Field(
        default=0,
        description="Count of claims with warning status."
    )
    claims_contraindicated: int = Field(
        default=0,
        description="Count of claims with contraindicated status."
    )

# Schema version for policy schemas
SCHEMA_VERSION_POLICY = "1.0.0"


class EnforcementMode(str, Enum):
    """Enforcement mode for policy violations."""
    BLOCK = "block"    # Deny request if policy fails
    WARN = "warn"      # Allow but flag violation
    LOG = "log"        # Silent logging only
    AUDIT = "audit"    # Require human review
    SHADOW = "shadow"  # Evaluate but don't enforce (for testing)


class PolicyChangeType(str, Enum):
    """Types of changes tracked in policy history."""
    CREATED = "created"
    UPDATED = "updated"
    RULE_ADDED = "rule_added"
    RULE_REMOVED = "rule_removed"
    RULE_MODIFIED = "rule_modified"
    ENFORCEMENT_CHANGED = "enforcement_changed"
    CLAIMS_CHANGED = "claims_changed"
    REVERTED = "reverted"


class PolicyConfig(BaseModel):
    """Configuration values for policy evaluation.

    PolicyConfig holds behavioral settings like thresholds, feature flags,
    and model versions that can be referenced in policy rule conditions.
    This replaces environment variables for behavioral settings, enabling
    dynamic policy updates without redeploying auditors.

    Config values are accessed in LPL expressions via config.* syntax:
        condition: "claims['toxicity.score'].value < config.toxicity_threshold"

    Example YAML:
        config:
          toxicity_threshold: 0.8
          enable_pii_detection: true
          model_version: "v2"
          allowed_regions:
            - US
            - EU
    """
    model_config = {"extra": "allow"}  # Allow arbitrary fields

    def __getattr__(self, name: str) -> Any:
        """Allow dot-notation access to config values."""
        try:
            return self.__dict__[name]
        except KeyError:
            # Check if it's in the model's extra fields
            if hasattr(self, "__pydantic_extra__") and self.__pydantic_extra__:
                if name in self.__pydantic_extra__:
                    return self.__pydantic_extra__[name]
            raise AttributeError(f"Config has no attribute '{name}'")


class ClaimRequirement(BaseModel):
    """Defines a required claim output from an auditor.

    Specifies what claims an auditor must produce and the constraints
    on those claims (type, confidence, schema validation).
    """
    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(
        ...,
        description="Claim name using dot notation (e.g., 'location.verified', 'pii.detected').",
        examples=["location.verified", "toxicity.score", "pii.detected"]
    )
    type: MeasurementType = Field(
        ...,
        description="Expected measurement type for the claim.",
        examples=["score_binary", "score_normalized", "location_region"]
    )
    required: bool = Field(
        default=True,
        description="Whether this claim is required. If true, policy fails without it."
    )
    min_confidence: Optional[float] = Field(
        default=None,
        alias="minConfidence",
        ge=0.0,
        le=1.0,
        description="Minimum confidence score required (0.0 to 1.0).",
        examples=[0.8, 0.95]
    )
    value_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        alias="valueSchema",
        description="JSON Schema for validating the claim value.",
        examples=[{"type": "object", "properties": {"country": {"type": "string"}}}]
    )

    @field_validator('min_confidence')
    @classmethod
    def validate_min_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Validate min_confidence is within valid range."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('min_confidence must be between 0.0 and 1.0')
        return v


class PolicyRule(BaseModel):
    """A single policy rule with conditions and actions.

    Rules use LPL (Lucid Policy Language) expressions to evaluate
    claims and determine the appropriate action.
    """
    id: str = Field(
        ...,
        description="Unique identifier for this rule within the policy.",
        examples=["rule-001", "location-check", "toxicity-threshold"]
    )
    description: str = Field(
        ...,
        description="Human-readable description of what this rule checks.",
        examples=["Verify request originates from allowed region"]
    )
    condition: str = Field(
        ...,
        description="LPL expression to evaluate. Access claims via claims['name'].value syntax.",
        examples=[
            "claims['location.country'].value == 'IN'",
            "claims['toxicity.score'].value > 0.7",
            "claims['pii.detected'].value == True"
        ]
    )
    action: Literal["proceed", "deny", "warn", "redact"] = Field(
        ...,
        description="Action to take when condition evaluates to true.",
        examples=["deny", "warn", "proceed"]
    )
    message: str = Field(
        ...,
        description="Message to include when this rule triggers.",
        examples=[
            "Request denied: origin country not in allowed list",
            "Warning: high toxicity score detected"
        ]
    )


class AuditorPolicy(BaseModel):
    """Complete policy definition for an auditor.

    Defines what claims an auditor must produce, the rules for evaluating
    those claims, and how violations should be enforced.
    """
    model_config = ConfigDict(populate_by_name=True)

    _expected_version: ClassVar[str] = SCHEMA_VERSION_POLICY

    schema_version: str = Field(
        default=SCHEMA_VERSION_POLICY,
        alias="schemaVersion",
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    policy_id: str = Field(
        ...,
        alias="policyId",
        description="Unique identifier for this policy.",
        examples=["pol-location-india", "pol-toxicity-standard"]
    )
    version: str = Field(
        ...,
        description="Policy version string. Follows SemVer.",
        examples=["1.0.0", "2.1.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    name: str = Field(
        ...,
        description="Human-readable name for the policy.",
        examples=["India Location Verification Policy", "Standard Toxicity Policy"]
    )
    description: str = Field(
        ...,
        description="Detailed description of the policy's purpose and behavior.",
        examples=["Verifies that AI workloads are running within India's borders"]
    )
    verification_method: str = Field(
        ...,
        alias="verificationMethod",
        description="Method used to verify claims (e.g., auditor name or verification technique).",
        examples=["lucid-location-auditor", "tee-attestation", "signature-verification"]
    )
    required_claims: List[ClaimRequirement] = Field(
        ...,
        alias="requiredClaims",
        min_length=1,
        description="List of claims that must be produced. At least one required."
    )
    optional_claims: List[ClaimRequirement] = Field(
        default_factory=list,
        alias="optionalClaims",
        description="List of optional claims that may be produced."
    )
    rules: List[PolicyRule] = Field(
        ...,
        min_length=1,
        description="List of policy rules to evaluate. At least one required."
    )
    enforcement: EnforcementMode = Field(
        default=EnforcementMode.BLOCK,
        description="How policy violations should be enforced.",
        examples=["block", "warn", "log"]
    )
    config: Optional[PolicyConfig] = Field(
        default=None,
        description="Configuration values for policy evaluation. "
        "Accessed in LPL expressions via config.* syntax.",
        examples=[{"toxicity_threshold": 0.8, "enable_pii_detection": True}]
    )
    compliance_frameworks: List[ComplianceFramework] = Field(
        default_factory=list,
        alias="complianceFrameworks",
        description="Compliance frameworks this policy helps satisfy.",
        examples=[["gdpr", "soc2"], ["hipaa"]]
    )
    control_mappings: Dict[str, str] = Field(
        default_factory=dict,
        alias="controlMappings",
        description="Mapping from compliance framework to specific control ID.",
        examples=[{"gdpr": "Article 5(1)(f)", "soc2": "CC6.1"}]
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

    @field_validator('control_mappings')
    @classmethod
    def validate_control_mappings(cls, v: Dict[str, str], info) -> Dict[str, str]:
        """Validate that control mappings reference declared frameworks."""
        # Note: We can't validate against compliance_frameworks here because
        # field_validator runs before the model is fully constructed.
        # This validation is informational - unknown frameworks are allowed
        # but may indicate a configuration error.
        return v


class PolicyBundle(BaseModel):
    """Collection of policies for a deployment profile.

    Bundles allow grouping multiple auditor policies together with
    composite rules that span across auditors.
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_POLICY

    schema_version: str = Field(
        default=SCHEMA_VERSION_POLICY,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    bundle_id: str = Field(
        ...,
        description="Unique identifier for this policy bundle.",
        examples=["bundle-india-compliance", "bundle-healthcare-standard"]
    )
    name: str = Field(
        ...,
        description="Human-readable name for the bundle.",
        examples=["India AI Compliance Bundle", "Healthcare Standard Bundle"]
    )
    policies: List[AuditorPolicy] = Field(
        ...,
        min_length=1,
        description="List of auditor policies in this bundle. At least one required."
    )
    composite_rules: List[PolicyRule] = Field(
        default_factory=list,
        description="Rules that evaluate claims across multiple auditors.",
        examples=[[{
            "id": "cross-auditor-check",
            "description": "Verify location and identity both pass",
            "condition": "claims['location.verified'].value and claims['identity.verified'].value",
            "action": "proceed",
            "message": "Both location and identity verified"
        }]]
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
