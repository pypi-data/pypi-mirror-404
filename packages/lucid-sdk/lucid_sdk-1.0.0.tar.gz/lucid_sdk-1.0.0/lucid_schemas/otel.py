"""OpenTelemetry format conversion for AttestationResult.

This module provides functions to convert AttestationResult (AI Passport) data
into OpenTelemetry-compatible formats following semantic conventions.

The conversion maps attestation data to:
- Resource attributes: Service and environment metadata
- Span attributes: Attestation-specific data
- Events: Evidence and claims as timestamped events

References:
- OpenTelemetry Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry Gen AI Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/gen-ai/
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .attestation import AttestationResult


# OpenTelemetry attribute prefixes following semantic conventions
OTEL_RESOURCE_PREFIX = "service"
OTEL_GENAI_PREFIX = "gen_ai"
OTEL_ATTESTATION_PREFIX = "lucid.attestation"
OTEL_EVIDENCE_PREFIX = "lucid.evidence"
OTEL_CLAIM_PREFIX = "lucid.claim"


class OTelSpan:
    """Represents an OpenTelemetry span in dictionary format."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        attributes: Optional[Dict[str, Any]] = None,
        events: Optional[List[Dict[str, Any]]] = None,
        status: str = "OK",
        kind: str = "INTERNAL",
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.start_time = start_time
        self.end_time = end_time or start_time
        self.attributes = attributes or {}
        self.events = events or []
        self.status = status
        self.kind = kind

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenTelemetry span dictionary format."""
        return {
            "name": self.name,
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "startTimeUnixNano": _datetime_to_unix_nano(self.start_time),
            "endTimeUnixNano": _datetime_to_unix_nano(self.end_time),
            "attributes": _format_attributes(self.attributes),
            "events": self.events,
            "status": {"code": self.status},
            "kind": self.kind,
        }


class OTelResource:
    """Represents OpenTelemetry resource attributes."""

    def __init__(self, attributes: Optional[Dict[str, Any]] = None):
        self.attributes = attributes or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OpenTelemetry resource dictionary format."""
        return {
            "attributes": _format_attributes(self.attributes),
        }


class OTelExportData:
    """Container for OpenTelemetry export data."""

    def __init__(
        self,
        resource: OTelResource,
        spans: List[OTelSpan],
        scope_name: str = "lucid-attestation",
        scope_version: str = "1.0.0",
    ):
        self.resource = resource
        self.spans = spans
        self.scope_name = scope_name
        self.scope_version = scope_version

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OTLP JSON format (OpenTelemetry Protocol).

        Returns a structure compatible with the OTLP/JSON specification.
        """
        return {
            "resourceSpans": [
                {
                    "resource": self.resource.to_dict(),
                    "scopeSpans": [
                        {
                            "scope": {
                                "name": self.scope_name,
                                "version": self.scope_version,
                            },
                            "spans": [span.to_dict() for span in self.spans],
                        }
                    ],
                }
            ]
        }


def _datetime_to_unix_nano(dt: datetime) -> int:
    """Convert datetime to Unix nanoseconds."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _format_attributes(attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Format attributes to OpenTelemetry key-value format."""
    result = []
    for key, value in attrs.items():
        if value is None:
            continue
        attr = {"key": key}
        if isinstance(value, bool):
            attr["value"] = {"boolValue": value}
        elif isinstance(value, int):
            attr["value"] = {"intValue": str(value)}
        elif isinstance(value, float):
            attr["value"] = {"doubleValue": value}
        elif isinstance(value, (list, tuple)):
            # Array values
            attr["value"] = {"arrayValue": {"values": [_format_single_value(v) for v in value]}}
        else:
            attr["value"] = {"stringValue": str(value)}
        result.append(attr)
    return result


def _format_single_value(value: Any) -> Dict[str, Any]:
    """Format a single value for array attributes."""
    if isinstance(value, bool):
        return {"boolValue": value}
    elif isinstance(value, int):
        return {"intValue": str(value)}
    elif isinstance(value, float):
        return {"doubleValue": value}
    else:
        return {"stringValue": str(value)}


def _generate_trace_id(passport_id: str) -> str:
    """Generate a deterministic trace ID from passport ID."""
    import hashlib
    hash_bytes = hashlib.sha256(passport_id.encode()).digest()[:16]
    return hash_bytes.hex()


def _generate_span_id(evidence_id: str) -> str:
    """Generate a deterministic span ID from evidence ID."""
    import hashlib
    hash_bytes = hashlib.sha256(evidence_id.encode()).digest()[:8]
    return hash_bytes.hex()


def attestation_result_to_otel(
    attestation: "AttestationResult",
    service_name: str = "lucid-verifier",
    service_version: str = "1.0.0",
    environment: str = "production",
) -> OTelExportData:
    """Convert an AttestationResult to OpenTelemetry export format.

    This function transforms the attestation data into OTLP-compatible format
    that can be exported to any OpenTelemetry-compatible backend (Jaeger,
    Zipkin, Datadog, etc.).

    Args:
        attestation: The AttestationResult (AI Passport) to convert
        service_name: Service name for resource attributes
        service_version: Service version for resource attributes
        environment: Deployment environment (production, staging, etc.)

    Returns:
        OTelExportData containing resource and spans in OTLP format
    """
    # Generate trace ID from passport ID for correlation
    trace_id = _generate_trace_id(attestation.passport_id)

    # Build resource attributes
    resource = OTelResource({
        f"{OTEL_RESOURCE_PREFIX}.name": service_name,
        f"{OTEL_RESOURCE_PREFIX}.version": service_version,
        "deployment.environment": environment,
        f"{OTEL_ATTESTATION_PREFIX}.passport_id": attestation.passport_id,
        f"{OTEL_ATTESTATION_PREFIX}.model_id": attestation.model_id,
        f"{OTEL_ATTESTATION_PREFIX}.is_mock": attestation.is_mock,
    })

    spans = []

    # Main attestation span
    main_span = _create_attestation_span(attestation, trace_id)
    spans.append(main_span)

    # Evidence spans (child spans of the main attestation)
    for evidence in attestation.evidence:
        evidence_span = _create_evidence_span(evidence, trace_id, main_span.span_id)
        spans.append(evidence_span)

    # Evaluation spans
    for evaluation in attestation.evaluations:
        eval_span = _create_evaluation_span(evaluation, trace_id, main_span.span_id)
        spans.append(eval_span)

    return OTelExportData(resource=resource, spans=spans)


def _create_attestation_span(
    attestation: "AttestationResult",
    trace_id: str,
) -> OTelSpan:
    """Create the main attestation span."""
    from .attestation import AttestationResult

    span_id = _generate_span_id(f"{attestation.passport_id}-main")

    # Build attributes following semantic conventions
    attributes = {
        # Attestation metadata
        f"{OTEL_ATTESTATION_PREFIX}.schema_version": attestation.schema_version,
        f"{OTEL_ATTESTATION_PREFIX}.issuer": attestation.iss,
        f"{OTEL_ATTESTATION_PREFIX}.passport_id": attestation.passport_id,

        # Model information (Gen AI semantic conventions)
        f"{OTEL_GENAI_PREFIX}.system": "lucid",
        f"{OTEL_GENAI_PREFIX}.request.model": attestation.model_id,
        f"{OTEL_ATTESTATION_PREFIX}.model_hash": attestation.model_hash,

        # Authorization status
        f"{OTEL_ATTESTATION_PREFIX}.deployment_authorized": attestation.deployment_authorized,
        f"{OTEL_ATTESTATION_PREFIX}.risk_score": attestation.risk_score,

        # Counts
        f"{OTEL_ATTESTATION_PREFIX}.evidence_count": len(attestation.evidence),
        f"{OTEL_ATTESTATION_PREFIX}.evaluation_count": len(attestation.evaluations),

        # Environment
        f"{OTEL_ATTESTATION_PREFIX}.is_mock": attestation.is_mock,
    }

    # Optional attributes
    if attestation.authorization_reason:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.authorization_reason"] = attestation.authorization_reason
    if attestation.session_id:
        attributes["session.id"] = attestation.session_id
    if attestation.user_id:
        attributes["enduser.id"] = attestation.user_id
    if attestation.exp:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.expiration"] = attestation.exp.isoformat()
    if attestation.verifier_signature:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.signed"] = True

    # Hardware attestation attributes
    if attestation.hardware_attestation:
        hw = attestation.hardware_attestation
        attributes[f"{OTEL_ATTESTATION_PREFIX}.hardware.provider"] = hw.provider.value if hasattr(hw.provider, 'value') else str(hw.provider)
        attributes[f"{OTEL_ATTESTATION_PREFIX}.hardware.tee_type"] = hw.tee_type
        attributes[f"{OTEL_ATTESTATION_PREFIX}.hardware.verified"] = hw.verified
        if hw.gpu_tee_type:
            attributes[f"{OTEL_ATTESTATION_PREFIX}.hardware.gpu_tee_type"] = hw.gpu_tee_type

    # Runtime status attributes
    if attestation.runtime_status:
        rs = attestation.runtime_status
        attributes[f"{OTEL_ATTESTATION_PREFIX}.runtime.active_auditors"] = rs.active_auditors
        attributes[f"{OTEL_ATTESTATION_PREFIX}.runtime.requests_processed"] = rs.requests_processed
        attributes[f"{OTEL_ATTESTATION_PREFIX}.runtime.requests_blocked"] = rs.requests_blocked
        attributes[f"{OTEL_ATTESTATION_PREFIX}.runtime.requests_redacted"] = rs.requests_redacted

    # Determine status based on authorization
    status = "OK" if attestation.deployment_authorized else "ERROR"

    return OTelSpan(
        name="attestation",
        trace_id=trace_id,
        span_id=span_id,
        start_time=attestation.iat,
        end_time=attestation.exp or attestation.iat,
        attributes=attributes,
        status=status,
        kind="SERVER",
    )


def _create_evidence_span(
    evidence: Any,  # Evidence type
    trace_id: str,
    parent_span_id: str,
) -> OTelSpan:
    """Create a span for an evidence bundle."""
    span_id = _generate_span_id(evidence.evidence_id)

    attributes = {
        f"{OTEL_EVIDENCE_PREFIX}.id": evidence.evidence_id,
        f"{OTEL_EVIDENCE_PREFIX}.attester_id": evidence.attester_id,
        f"{OTEL_EVIDENCE_PREFIX}.attester_type": evidence.attester_type.value if hasattr(evidence.attester_type, 'value') else str(evidence.attester_type),
        f"{OTEL_EVIDENCE_PREFIX}.phase": evidence.phase,
        f"{OTEL_EVIDENCE_PREFIX}.claim_count": len(evidence.claims),
    }

    if evidence.nonce:
        attributes[f"{OTEL_EVIDENCE_PREFIX}.nonce"] = evidence.nonce
    if evidence.trust_tier:
        attributes[f"{OTEL_EVIDENCE_PREFIX}.trust_tier"] = evidence.trust_tier.value if hasattr(evidence.trust_tier, 'value') else str(evidence.trust_tier)
    if evidence.zk_proof:
        attributes[f"{OTEL_EVIDENCE_PREFIX}.has_zk_proof"] = True

    # Add claim events
    events = []
    for claim in evidence.claims:
        event = _create_claim_event(claim)
        events.append(event)

    span = OTelSpan(
        name=f"evidence.{evidence.attester_id}",
        trace_id=trace_id,
        span_id=span_id,
        start_time=evidence.generated_at,
        attributes=attributes,
        events=events,
        kind="INTERNAL",
    )
    span.parent_span_id = parent_span_id
    return span


def _create_claim_event(claim: Any) -> Dict[str, Any]:
    """Create an event for a claim within an evidence span."""
    attributes = {
        f"{OTEL_CLAIM_PREFIX}.name": claim.name,
        f"{OTEL_CLAIM_PREFIX}.type": claim.type.value if hasattr(claim.type, 'value') else str(claim.type),
        f"{OTEL_CLAIM_PREFIX}.confidence": claim.confidence,
    }

    # Handle claim value based on type
    if isinstance(claim.value, dict):
        # For dict values, extract key fields as attributes
        for key, val in claim.value.items():
            if isinstance(val, (str, int, float, bool)):
                attributes[f"{OTEL_CLAIM_PREFIX}.value.{key}"] = val
    elif isinstance(claim.value, (str, int, float, bool)):
        attributes[f"{OTEL_CLAIM_PREFIX}.value"] = claim.value

    if claim.phase:
        attributes[f"{OTEL_CLAIM_PREFIX}.phase"] = claim.phase
    if claim.compliance_framework:
        attributes[f"{OTEL_CLAIM_PREFIX}.compliance_framework"] = claim.compliance_framework.value if hasattr(claim.compliance_framework, 'value') else str(claim.compliance_framework)
    if claim.control_id:
        attributes[f"{OTEL_CLAIM_PREFIX}.control_id"] = claim.control_id

    return {
        "name": f"claim.{claim.name}",
        "timeUnixNano": _datetime_to_unix_nano(claim.timestamp),
        "attributes": _format_attributes(attributes),
    }


def _create_evaluation_span(
    evaluation: Any,  # EvaluationResult type
    trace_id: str,
    parent_span_id: str,
) -> OTelSpan:
    """Create a span for a pre-deployment evaluation."""
    span_id = _generate_span_id(evaluation.evaluation_id)

    attributes = {
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.id": evaluation.evaluation_id,
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.evaluator": evaluation.evaluator,
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.evaluator_version": evaluation.evaluator_version,
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.model_id": evaluation.model_id,
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.model_hash": evaluation.model_hash,
        f"{OTEL_ATTESTATION_PREFIX}.evaluation.passed": evaluation.passed,
    }

    # Add scores as individual attributes
    for score_name, score_value in evaluation.scores.items():
        attributes[f"{OTEL_ATTESTATION_PREFIX}.evaluation.score.{score_name}"] = score_value

    if evaluation.tee_quote:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.evaluation.has_tee_quote"] = True

    # Add findings as events
    events = []
    for i, finding in enumerate(evaluation.findings):
        event = {
            "name": f"finding.{i}",
            "timeUnixNano": _datetime_to_unix_nano(evaluation.timestamp),
            "attributes": _format_attributes({
                f"{OTEL_ATTESTATION_PREFIX}.finding": str(finding),
            }),
        }
        events.append(event)

    status = "OK" if evaluation.passed else "ERROR"

    span = OTelSpan(
        name=f"evaluation.{evaluation.evaluator}",
        trace_id=trace_id,
        span_id=span_id,
        start_time=evaluation.timestamp,
        attributes=attributes,
        events=events,
        status=status,
        kind="INTERNAL",
    )
    span.parent_span_id = parent_span_id
    return span


def attestation_result_to_otel_attributes(
    attestation: "AttestationResult",
) -> Dict[str, Any]:
    """Convert AttestationResult to flat OpenTelemetry span attributes.

    This is a simpler conversion that returns just the attributes dictionary,
    useful for adding attestation data to existing spans.

    Args:
        attestation: The AttestationResult to convert

    Returns:
        Dictionary of OpenTelemetry-compatible attributes
    """
    attributes = {
        # Core attestation fields
        f"{OTEL_ATTESTATION_PREFIX}.passport_id": attestation.passport_id,
        f"{OTEL_ATTESTATION_PREFIX}.schema_version": attestation.schema_version,
        f"{OTEL_ATTESTATION_PREFIX}.issuer": attestation.iss,
        f"{OTEL_ATTESTATION_PREFIX}.issued_at": attestation.iat.isoformat(),

        # Model information
        f"{OTEL_GENAI_PREFIX}.request.model": attestation.model_id,
        f"{OTEL_ATTESTATION_PREFIX}.model_hash": attestation.model_hash,

        # Authorization
        f"{OTEL_ATTESTATION_PREFIX}.deployment_authorized": attestation.deployment_authorized,
        f"{OTEL_ATTESTATION_PREFIX}.risk_score": attestation.risk_score,

        # Counts
        f"{OTEL_ATTESTATION_PREFIX}.evidence_count": len(attestation.evidence),
        f"{OTEL_ATTESTATION_PREFIX}.evaluation_count": len(attestation.evaluations),

        # Environment
        f"{OTEL_ATTESTATION_PREFIX}.is_mock": attestation.is_mock,
    }

    # Optional fields
    if attestation.exp:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.expiration"] = attestation.exp.isoformat()
    if attestation.authorization_reason:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.authorization_reason"] = attestation.authorization_reason
    if attestation.session_id:
        attributes["session.id"] = attestation.session_id
    if attestation.user_id:
        attributes["enduser.id"] = attestation.user_id
    if attestation.verifier_signature:
        attributes[f"{OTEL_ATTESTATION_PREFIX}.signed"] = True

    return attributes
