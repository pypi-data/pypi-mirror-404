"""Dashboard appraisal row schema for policy-centric visualization.

This module defines the flattened row format for dashboard visualization
that combines ClaimAppraisalRecord (per-claim policy evaluation) with
deployment context from CreateAppDeploymentRequest or AgentResponse.

The DashboardAppraisalRow provides a policy-centric view showing:
- Per-claim appraisal status (affirming/warning/contraindicated)
- Policy evaluation details (rules, reference values)
- Full deployment context (model, GPU, audit chain)
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .policy import ClaimAppraisalStatus
from .enums import TrustTier


class DashboardAppraisalRow(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    """Flattened row for dashboard visualization combining appraisal + deployment context.

    This schema is designed for efficient REST API delivery and frontend rendering.
    Each row represents a single claim appraisal with its full context.
    """

    # Identifiers
    id: str = Field(
        ...,
        description="Unique row ID (evidence_id + claim_name hash)."
    )
    passport_id: str = Field(
        ...,
        description="ID of the passport containing this evidence."
    )
    evidence_id: str = Field(
        ...,
        description="ID of the evidence bundle containing this claim."
    )
    org_id: Optional[str] = Field(
        default=None,
        description="Organization ID if scoped."
    )

    # ClaimAppraisalRecord fields
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
    status: ClaimAppraisalStatus = Field(
        ...,
        description="Appraisal status: affirming, warning, contraindicated, none.",
        examples=["affirming", "contraindicated"]
    )
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
    compliance_framework: Optional[str] = Field(
        default=None,
        description="Compliance framework this claim relates to.",
        examples=["soc2", "gdpr", "hipaa"]
    )
    control_id: Optional[str] = Field(
        default=None,
        description="Specific control ID within the framework.",
        examples=["CC6.1", "Article 5(1)(f)"]
    )
    appraisal_message: Optional[str] = Field(
        default=None,
        description="Human-readable message about the appraisal.",
        examples=["Location verified: IN matches required region"]
    )

    # Policy context
    policy_id: str = Field(
        ...,
        description="ID of the policy used for appraisal."
    )
    policy_version: str = Field(
        ...,
        description="Version of the policy used."
    )
    overall_trust_tier: TrustTier = Field(
        ...,
        description="Overall trust tier for the evidence bundle."
    )
    appraised_at: datetime = Field(
        ...,
        description="Timestamp when appraisal was performed."
    )

    # Deployment context (from CreateAppDeploymentRequest / AgentResponse)
    deployment_name: str = Field(
        default="",
        description="Agent/deployment name."
    )
    model_id: str = Field(
        default="",
        description="Model identifier."
    )
    model_name: str = Field(
        default="",
        description="Human-readable model name."
    )
    gpu_type: str = Field(
        default="",
        description="GPU type used for inference.",
        examples=["A100", "H100", "L4"]
    )
    gpu_region: str = Field(
        default="",
        description="GPU region.",
        examples=["us-west-2", "eu-central-1"]
    )
    gpu_cc_mode: bool = Field(
        default=False,
        description="Whether Confidential Computing mode is enabled."
    )
    gpu_provider: Optional[str] = Field(
        default=None,
        description="Cloud provider: aws, azure, gcp.",
        examples=["aws", "azure", "gcp"]
    )

    # Auditor context
    auditor_id: str = Field(
        ...,
        description="Attester ID (auditor that produced the evidence)."
    )
    auditor_phase: str = Field(
        default="",
        description="Audit phase: pre_request, request, response, post_response.",
        examples=["request", "response"]
    )

    # Audit chain summary (flattened)
    audit_chain_phases: List[str] = Field(
        default_factory=list,
        description="Phases with auditors configured.",
        examples=[["pre_request", "request", "response"]]
    )
    audit_chain_auditor_count: int = Field(
        default=0,
        description="Total number of auditors in the chain."
    )

    # Frontend app (if configured)
    frontend_app_id: Optional[str] = Field(
        default=None,
        description="Frontend app ID if configured."
    )
    frontend_app_type: Optional[str] = Field(
        default=None,
        description="Frontend app type: chatbot, api-only, custom, container.",
        examples=["chatbot", "api-only", "custom", "container"]
    )

    # Apps (summary)
    apps_count: int = Field(
        default=0,
        description="Number of apps deployed with this agent."
    )
    apps_ids: List[str] = Field(
        default_factory=list,
        description="IDs of apps deployed with this agent."
    )

    # Timestamps
    created_at: datetime = Field(
        ...,
        description="When the evidence was generated."
    )

    # Mock indicator
    is_mock: bool = Field(
        default=False,
        description="Whether this is mock/seeded data."
    )

