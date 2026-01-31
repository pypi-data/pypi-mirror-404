import json
import structlog
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, TypedDict, NotRequired
from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel


# =============================================================================
# TypedDict definitions for structured payloads
# =============================================================================

class MessageDict(TypedDict):
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: NotRequired[str]
    tool_call_id: NotRequired[str]


class ToolCallDict(TypedDict):
    """A tool/function call made by the model."""
    id: NotRequired[str]
    name: str
    arguments: Union[str, Dict[str, object]]
    type: NotRequired[str]


class UsageDict(TypedDict, total=False):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ResourceUsageDict(TypedDict, total=False):
    """Resource consumption metrics during execution."""
    cpu_percent: float
    memory_mb: float
    gpu_memory_mb: float
    tokens_processed: int
    latency_ms: float


class RequestMetadataDict(TypedDict, total=False):
    """Optional metadata attached to requests."""
    user_id: str
    session_id: str
    trace_id: str
    timestamp: str
    source: str
    custom: Dict[str, object]


class RequestDict(TypedDict, total=False):
    """Incoming model request structure.

    This TypedDict represents the standard request format for LLM API calls.
    Compatible with OpenAI, Anthropic, and similar API formats.
    """
    messages: List[MessageDict]
    model: str
    nonce: str
    metadata: RequestMetadataDict
    # Common optional parameters
    temperature: float
    max_tokens: int
    top_p: float
    stream: bool
    tools: List[Dict[str, object]]
    tool_choice: Union[str, Dict[str, object]]


class ResponseDict(TypedDict, total=False):
    """Model response structure.

    Represents the standard response format from LLM API calls.
    """
    content: str
    tool_calls: List[ToolCallDict]
    finish_reason: str  # "stop", "length", "tool_calls", "content_filter"
    usage: UsageDict
    model: str
    id: str
    created: int


class ExecutionContextDict(TypedDict, total=False):
    """Runtime execution telemetry for check_execution.

    Contains telemetry data collected during model execution,
    used for runtime monitoring and anomaly detection.
    """
    tool_calls: List[ToolCallDict]
    intermediate_outputs: List[str]
    resource_usage: ResourceUsageDict
    # Additional telemetry
    step_count: int
    current_phase: str
    elapsed_ms: float


class AuditorDataDict(TypedDict, total=False):
    """Data passed between auditors in the dataflow chain.

    Each auditor can include arbitrary data in their AuditResult.data
    which is then accessible to downstream auditors via lucid_context.
    """
    # Common fields auditors might pass
    score: float
    confidence: float
    detected: bool
    findings: List[Dict[str, object]]
    labels: List[str]
    # Allow extension
    # Note: Additional keys can be added at runtime


# =============================================================================
# RATS-compliant TypedDicts (RFC 9334)
# =============================================================================


class ClaimValueDict(TypedDict, total=False):
    """Value structure for Claim creation.

    The value field in a Claim contains the audit decision
    and associated metadata.
    """
    decision: str  # AuditDecision value
    reason: Optional[str]
    modifications: Optional[Dict[str, object]]
    metadata: Dict[str, object]


class ClaimDict(TypedDict, total=False):
    """Serialized Claim for evidence bundling (RFC 9334).

    Represents a single unsigned assertion. Claims are bundled
    into Evidence containers which provide the cryptographic signature.
    """
    name: str
    type: str
    value: ClaimValueDict
    timestamp: str
    confidence: float
    phase: str
    nonce: str
    compliance_framework: str
    control_id: str


class EvidenceDict(TypedDict, total=False):
    """Serialized Evidence for submission to Verifier (RFC 9334).

    Represents a signed container of Claims from a single Attester.
    This replaces the per-Measurement signature approach.
    """
    schema_version: str
    evidence_id: str
    attester_id: str
    attester_type: str
    claims: List[ClaimDict]
    phase: str
    generated_at: str
    nonce: str
    signature: str
    trust_tier: str


# =============================================================================
# Audit Finding types for structured audit results
# =============================================================================


class AuditFindingSeverity(str, Enum):
    """Severity levels for audit findings.

    Used to classify the importance and urgency of detected issues.
    """
    CRITICAL = "critical"  # Immediate action required, blocks execution
    HIGH = "high"          # Serious issue, should be addressed soon
    MEDIUM = "medium"      # Moderate concern, should be reviewed
    LOW = "low"            # Minor issue, informational
    INFO = "info"          # Informational finding, no action needed


class AuditFindingDict(TypedDict, total=False):
    """TypedDict representation of an audit finding.

    Used for serialization and type hints when working with finding data.
    """
    pattern: str                    # Name/identifier of the pattern that matched
    severity: str                   # AuditFindingSeverity value
    matched: str                    # The actual content that matched
    description: str                # Human-readable description of the finding
    category: str                   # Category of the finding (e.g., injection, pii, toxicity)
    evidence: Dict[str, object]     # Additional evidence/context for the finding
    remediation: str                # Suggested remediation action


class AuditFinding:
    """Represents a single finding from an audit check.

    Encapsulates information about a detected issue, including its severity,
    the content that triggered it, and any remediation suggestions.

    Attributes:
        pattern: Name/identifier of the pattern that matched.
        severity: Severity level of the finding.
        matched: The actual content that triggered the finding.
        description: Human-readable description of the finding.
        category: Category of the finding (e.g., "injection", "pii", "toxicity").
        evidence: Additional context or evidence about the finding.
        remediation: Suggested action to remediate the finding.

    Example:
        finding = AuditFinding(
            pattern="ssn_pattern",
            severity=AuditFindingSeverity.HIGH,
            matched="123-45-6789",
            description="Social Security Number detected",
            category="pii"
        )
    """
    pattern: str
    severity: AuditFindingSeverity
    matched: str
    description: str
    category: str
    evidence: Dict[str, object]
    remediation: Optional[str]

    def __init__(
        self,
        pattern: str,
        severity: Union[AuditFindingSeverity, str],
        matched: str = "",
        description: str = "",
        category: str = "general",
        evidence: Optional[Dict[str, object]] = None,
        remediation: Optional[str] = None
    ) -> None:
        self.pattern = pattern
        self.severity = (
            severity if isinstance(severity, AuditFindingSeverity)
            else AuditFindingSeverity(severity)
        )
        self.matched = matched
        self.description = description
        self.category = category
        self.evidence = evidence or {}
        self.remediation = remediation

    def to_dict(self) -> AuditFindingDict:
        """Convert to dictionary representation."""
        result: AuditFindingDict = {
            "pattern": self.pattern,
            "severity": self.severity.value,
            "matched": self.matched,
            "description": self.description,
            "category": self.category,
        }
        if self.evidence:
            result["evidence"] = self.evidence
        if self.remediation:
            result["remediation"] = self.remediation
        return result

    def __repr__(self) -> str:
        return (
            f"AuditFinding(pattern={self.pattern!r}, severity={self.severity.value!r}, "
            f"category={self.category!r})"
        )


class AuditCounts(TypedDict, total=False):
    """Counts of audit findings and decisions.

    Used to aggregate statistics about audit results.
    """
    total: int              # Total number of findings
    critical: int           # Count of CRITICAL severity findings
    high: int               # Count of HIGH severity findings
    medium: int             # Count of MEDIUM severity findings
    low: int                # Count of LOW severity findings
    info: int               # Count of INFO severity findings
    blocked: int            # Number of requests blocked (DENY decisions)
    warned: int             # Number of requests warned (WARN decisions)
    passed: int             # Number of requests passed (PROCEED decisions)
    redacted: int           # Number of requests redacted (REDACT decisions)


# =============================================================================
# Type aliases using TypedDicts
# =============================================================================

# RequestPayload represents an incoming model request - either a TypedDict or a Pydantic model
RequestPayload = Union[RequestDict, Dict[str, object], 'BaseModel']
# ResponsePayload represents a model response - either a TypedDict or a Pydantic model
ResponsePayload = Union[ResponseDict, Dict[str, object], 'BaseModel']
# ExecutionContext represents runtime telemetry/context data
ExecutionContext = Union[ExecutionContextDict, Dict[str, Union[str, int, float, bool, List[object], Dict[str, object]]]]
# ArtifactPayload represents deployment artifacts for static analysis
ArtifactPayload = Union[Dict[str, object], bytes, str]
# LucidContext is the dataflow context passed between auditors
# Keys are auditor IDs, values are the AuditorDataDict from each auditor
LucidContext = Optional[Dict[str, AuditorDataDict]]
# AuditorConfig represents the unique configuration for an auditor instance
AuditorConfig = Dict[str, Union[str, int, float, bool, List[object], Dict[str, object]]]
# MetadataDict for AuditResult metadata
MetadataDict = Dict[str, Union[str, int, float, bool, List[object], Dict[str, object], None]]
from lucid_schemas import (
    AuditDecision,
    MeasurementType,
    # RATS-compliant schemas (RFC 9334)
    Claim,
    Evidence,
    EvidenceSource,
)
from .client import LucidClient

logger = structlog.get_logger()

# --- Configuration ---
AUDITOR_HTTP_TIMEOUT = float(os.getenv("AUDITOR_HTTP_TIMEOUT", "5.0"))
AUDITOR_MAX_RETRIES = int(os.getenv("AUDITOR_MAX_RETRIES", "3"))
AUDITOR_RETRY_MAX_WAIT = float(os.getenv("AUDITOR_RETRY_MAX_WAIT", "10"))

class AuditResult(BaseModel):
    """The outcome of an auditor's evaluation.

    Encapsulates the decision made by the auditor, along with any relevant
    reasons, modifications to the data, and additional metadata for the
    Verifier or Observer.

    Attributes:
        decision (AuditDecision): The final decision (PROCEED, DENY, REDACT, WARN).
        reason (Optional[str]): Human-readable explanation for the decision.
        modifications (Optional[Dict[str, object]]): If decision is REDACT, contains
            the specific key-value updates to be applied to the request.
        metadata (MetadataDict): Arbitrary key-value pairs providing extra
            context for the audit (e.g., specific rules triggered).
        data (Dict[str, Any]): Results to be passed to the NEXT auditor in the chain (Dataflow).
            Accepts arbitrary key-value pairs for flexible inter-auditor communication.
    """
    decision: AuditDecision
    reason: Optional[str] = None
    modifications: Optional[Dict[str, object]] = None
    metadata: MetadataDict = {}
    data: Dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


# Convenience constructors
# MetadataValue type for **kwargs metadata values
MetadataValue = Union[str, int, float, bool, List[object], Dict[str, object], None]


def Proceed(
    reason: Optional[str] = None,
    data: Optional[AuditorDataDict] = None,
    **metadata: MetadataValue
) -> AuditResult:
    """Helper to create a PROCEED result.

    Args:
        reason: Optional explanation.
        data: Optional results to pass to next auditor (dataflow).
        **metadata: Extra context to include (e.g., safety_score=1.0).

    Returns:
        AuditResult with PROCEED decision.

    Example:
        return Proceed(safety_score=0.95, data={"processed": True})
    """
    return AuditResult(decision=AuditDecision.PROCEED, reason=reason, data=data or {}, metadata=dict(metadata))


def Deny(
    reason: str,
    data: Optional[AuditorDataDict] = None,
    **metadata: MetadataValue
) -> AuditResult:
    """Helper to create a DENY result.

    Args:
        reason: Required explanation for the denial.
        data: Optional results to pass to next auditor (dataflow).
        **metadata: Extra context to include.

    Returns:
        AuditResult with DENY decision.

    Example:
        return Deny("Prompt injection detected", injection_score=0.95)
    """
    return AuditResult(decision=AuditDecision.DENY, reason=reason, data=data or {}, metadata=dict(metadata))


def Redact(
    modifications: Dict[str, object],
    reason: Optional[str] = None,
    data: Optional[AuditorDataDict] = None,
    **metadata: MetadataValue
) -> AuditResult:
    """Helper to create a REDACT result.

    Args:
        modifications: Dictionary of keys and their new, redacted values.
        reason: Optional explanation.
        data: Optional results to pass to next auditor (dataflow).
        **metadata: Extra context to include.

    Returns:
        AuditResult with REDACT decision.

    Example:
        return Redact({"content": "[REDACTED]"}, reason="PII detected")
    """
    return AuditResult(decision=AuditDecision.REDACT, reason=reason, modifications=modifications, data=data or {}, metadata=dict(metadata))


def Warn(
    reason: str,
    data: Optional[AuditorDataDict] = None,
    **metadata: MetadataValue
) -> AuditResult:
    """Helper to create a WARN result.

    Args:
        reason: Required explanation for the warning.
        data: Optional results to pass to next auditor (dataflow).
        **metadata: Extra context to include.

    Returns:
        AuditResult with WARN decision.

    Example:
        return Warn("Elevated toxicity score", toxicity_score=0.6)
    """
    return AuditResult(decision=AuditDecision.WARN, reason=reason, data=data or {}, metadata=dict(metadata))

class Auditor(ABC):
    """Abstract base class for all Lucid Auditors.

    Auditors are the primary units of safety enforcement in the Lucid platform.
    They execute within Trusted Execution Environments (TEEs) and produce
    cryptographically signed evidence of their findings.

    Attributes:
        auditor_id (str): Unique identifier for the auditor.
        version (str): Protocol version string.
        tee (LucidClient): Client for hardware attestation and secret management.
        verifier_url (Optional[str]): Endpoint for the Verifier service to send evidence to.
        config (AuditorConfig): Unique configuration patterns for this auditor.

    API Contract:
        Subclasses must implement:
        - check_request(request, lucid_context) -> AuditResult
        - check_execution(context, lucid_context) -> AuditResult
        - check_response(response, request, lucid_context) -> AuditResult

    Request Parameter (RequestPayload):
        - messages: List[Dict] - Conversation messages with role and content
        - model: str - Model identifier being called
        - nonce: str (optional) - Anti-replay token for session binding
        - metadata: Dict (optional) - Additional request metadata

    Context Parameter (ExecutionContext, for check_execution):
        - tool_calls: List[Dict] - Tool invocations with name and arguments
        - intermediate_outputs: List[str] - Model intermediate reasoning steps
        - resource_usage: Dict - CPU/memory/token consumption metrics

    Response Parameter (ResponsePayload):
        - content: str - Generated text response
        - tool_calls: List[Dict] (optional) - Tool calls in the response
        - finish_reason: str - Why generation stopped (stop, length, tool_calls)
        - usage: Dict - Token usage statistics

    lucid_context Structure (LucidContext):
        Enables dataflow between auditors in a chain. Each auditor AuditResult.data
        is stored under its auditor_id key::

            {
                "pii-auditor": {
                    "contains_pii": False,
                    "confidence": 0.95,
                    "detected_entities": []
                },
                "injection-auditor": {
                    "is_injection": False,
                    "score": 0.1
                }
            }

    Example::

        class MyAuditor(Auditor):
            def check_request(self, request, lucid_context=None):
                # Access upstream auditor results
                if lucid_context and "pii-auditor" in lucid_context:
                    if lucid_context["pii-auditor"].get("contains_pii"):
                        return Deny("PII detected by upstream auditor")

                # Pass data to downstream auditors via AuditResult.data
                return Proceed(data={"processed": True, "score": 0.8})
    """
    auditor_id: str
    version: str
    tee: LucidClient
    verifier_url: Optional[str]
    config: AuditorConfig

    def __init__(self, auditor_id: str, version: str = "1.0.0", verifier_url: Optional[str] = None) -> None:
        self.auditor_id = auditor_id
        self.version = version
        self.tee = LucidClient()
        self.verifier_url = verifier_url or os.getenv("LUCID_VERIFIER_URL")

        # Load unique configuration from environment (injected by Operator)
        config_raw = os.getenv("LUCID_AUDITOR_CONFIG") or "{}"
        try:
            self.config = json.loads(config_raw)
        except (json.JSONDecodeError, TypeError):
            logger.warning("failed_to_parse_auditor_config", auditor_id=auditor_id)
            self.config = {}

    @abstractmethod
    def check_request(self, request: RequestPayload, lucid_context: LucidContext = None) -> AuditResult:
        """Evaluate an incoming model request.

        Args:
            request: The request payload to audit (dict or Pydantic model).
            lucid_context: Optional context from previous auditors (dataflow).

        Returns:
            AuditResult containing the decision.
        """
        pass

    @abstractmethod
    def check_execution(self, context: ExecutionContext, lucid_context: LucidContext = None) -> AuditResult:
        """Monitor the model execution process.

        Args:
            context: Execution context containing telemetry indicators.
            lucid_context: Optional context from previous auditors (dataflow).

        Returns:
            AuditResult containing the decision.
        """
        pass

    @abstractmethod
    def check_response(self, response: ResponsePayload, request: Optional[RequestPayload] = None, lucid_context: LucidContext = None) -> AuditResult:
        """Evaluate a model generated response.

        Args:
            response: The response payload to audit (dict or Pydantic model).
            request: Optional original request for context.
            lucid_context: Optional context from previous auditors (dataflow).

        Returns:
            AuditResult containing the decision.
        """
        pass

    def emit_evidence(self, phase: str, result: AuditResult, request: Optional[RequestPayload] = None) -> None:
        """Standard method to create, sign, and send evidence to the Verifier.

        This method wraps the audit result into an Evidence bundle (RFC 9334),
        calls the hardware Attestation Agent to sign it, and pushes it to the Verifier.

        Args:
            phase: The lifecycle phase (artifact, request, execution, response).
            result: The result of the audit.
            request: Optional request object to extract nonces/metadata.
        """
        import httpx

        # Get session/nonce context for freshness
        nonce: Optional[str] = None
        if isinstance(request, dict):
            nonce = request.get("nonce")
        elif hasattr(request, "nonce"):
            nonce = getattr(request, "nonce")

        # Use RATS-compliant Evidence format
        evidence = self.create_evidence(phase, result, nonce=nonce)

        if self.verifier_url:
            try:
                payload: Dict[str, object] = {
                    "session_id": nonce or "default-session",
                    "model_id": os.getenv("MODEL_ID", "default-model"),
                    "evidence": [evidence]
                }
                # Synchronous send to ensure evidence is committed during the call
                from tenacity import retry, stop_after_attempt, wait_exponential

                @retry(
                    stop=stop_after_attempt(AUDITOR_MAX_RETRIES),
                    wait=wait_exponential(multiplier=1, max=AUDITOR_RETRY_MAX_WAIT),
                    reraise=True
                )
                def _send() -> None:
                    with httpx.Client() as client:
                        resp = client.post(f"{self.verifier_url}/v1/evidence", json=payload, timeout=AUDITOR_HTTP_TIMEOUT)
                        resp.raise_for_status()

                _send()
            except Exception as e:
                logger.error("failed_to_emit_evidence", verifier_url=self.verifier_url, error=str(e))

    def create_claim(self, phase: str, result: AuditResult, nonce: Optional[str] = None) -> ClaimDict:
        """Create an unsigned Claim for the given audit result.

        Claims are unsigned assertions that can be bundled into Evidence.
        Use create_evidence() to bundle Claims and sign them together.

        Args:
            phase: The lifecycle phase to record.
            result: The AuditResult to transform into a Claim.
            nonce: Optional anti-replay nonce.

        Returns:
            Dictionary representation of a Claim (ClaimDict).
        """
        # Build the claim value with proper types
        claim_value: ClaimValueDict = {
            "decision": result.decision.value,
            "reason": result.reason,
            "modifications": result.modifications,
            "metadata": dict(result.metadata) if result.metadata else {}
        }

        # Use the Claim model
        c = Claim(
            name=self.auditor_id,
            type=MeasurementType.policy_violation if result.decision == AuditDecision.DENY else MeasurementType.conformity,
            phase=phase,
            nonce=nonce,
            value=claim_value,
            timestamp=datetime.now(timezone.utc),
        )

        return c.model_dump(mode='json')

    def create_evidence(
        self,
        phase: str,
        results: Union[AuditResult, List[AuditResult]],
        nonce: Optional[str] = None,
        evidence_id: Optional[str] = None
    ) -> EvidenceDict:
        """Create and sign an Evidence bundle for the given audit results.

        Evidence bundles one or more Claims and signs them together.
        This is the RATS-compliant (RFC 9334) approach, replacing
        per-Measurement signatures with per-Evidence signatures.

        Args:
            phase: The lifecycle phase (request, response, artifact, execution).
            results: Single AuditResult or list of AuditResults to bundle.
            nonce: Optional anti-replay nonce.
            evidence_id: Optional custom evidence ID. If not provided, auto-generated.

        Returns:
            Dictionary representation of signed Evidence (EvidenceDict).
        """
        import uuid

        # Normalize to list
        result_list = [results] if isinstance(results, AuditResult) else results

        # Create Claims from results
        claims: List[Claim] = []
        now = datetime.now(timezone.utc)

        for i, result in enumerate(result_list):
            claim_value: ClaimValueDict = {
                "decision": result.decision.value,
                "reason": result.reason,
                "modifications": result.modifications,
                "metadata": dict(result.metadata) if result.metadata else {}
            }

            claim = Claim(
                name=f"{self.auditor_id}.{i}" if len(result_list) > 1 else self.auditor_id,
                type=MeasurementType.policy_violation if result.decision == AuditDecision.DENY else MeasurementType.conformity,
                phase=phase,
                nonce=nonce,
                value=claim_value,
                timestamp=now,
            )
            claims.append(claim)

        # Create Evidence container
        ev = Evidence(
            evidence_id=evidence_id or f"ev-{uuid.uuid4().hex[:12]}",
            attester_id=self.auditor_id,
            attester_type=EvidenceSource.AUDITOR,
            claims=claims,
            phase=phase,
            generated_at=now,
            nonce=nonce,
            signature=""  # Will be replaced
        )

        # Sign the entire Evidence (all claims bundled together)
        ev_dict = ev.model_dump(mode='json', exclude={"signature", "zk_proof", "trust_tier"})
        blob = json.dumps(ev_dict, sort_keys=True, separators=(',', ':')).encode('utf-8')
        ev.signature = self.tee.get_quote(blob)

        return ev.model_dump(mode='json')

# Type alias for handler functions
ArtifactHandler = Callable[[ArtifactPayload], AuditResult]
RequestHandler = Callable[[RequestPayload], AuditResult]
ExecutionHandler = Callable[[ExecutionContext], AuditResult]
ResponseHandler = Callable[[ResponsePayload, Optional[RequestPayload]], AuditResult]


class FunctionAuditor(Auditor):
    """An Auditor implementation that delegates to decorated functions.

    This class enables building auditors by simply wrapping functions with
    lifecycle decorators (e.g., @sdk.on_request).

    Attributes:
        _artifact_handlers: List of handlers for artifact phase.
        _request_handlers: List of handlers for request phase.
        _execution_handlers: List of handlers for execution phase.
        _response_handlers: List of handlers for response phase.
    """
    _artifact_handlers: List[Callable[..., AuditResult]]
    _request_handlers: List[Callable[..., AuditResult]]
    _execution_handlers: List[Callable[..., AuditResult]]
    _response_handlers: List[Callable[..., AuditResult]]

    def __init__(self, auditor_id: str, version: str = "1.0.0", verifier_url: Optional[str] = None) -> None:
        super().__init__(auditor_id, version, verifier_url)
        self._artifact_handlers = []
        self._request_handlers = []
        self._execution_handlers = []
        self._response_handlers = []

    def _invoke_handler(
        self,
        handler: Callable[..., AuditResult],
        *args: object,
        **kwargs: object
    ) -> AuditResult:
        """Intelligently invoke a handler, injecting config or context if requested."""
        import inspect
        sig = inspect.signature(handler)
        params = sig.parameters

        call_kwargs: Dict[str, object] = {}
        # Support injecting 'config' and 'lucid_context' if the handler asks for them
        if "config" in params:
            call_kwargs["config"] = self.config
        if "lucid_context" in params:
            call_kwargs["lucid_context"] = kwargs.get("lucid_context")

        # Extract positional args that the handler expects
        handler_args: List[object] = []
        for i, (name, param) in enumerate(params.items()):
            if i < len(args):
                handler_args.append(args[i])
            elif name in call_kwargs:
                continue  # Already handled via call_kwargs

        return handler(*handler_args, **call_kwargs)

    def check_artifact(self, artifact: ArtifactPayload, lucid_context: LucidContext = None) -> AuditResult:
        """Run artifact security handlers.

        Args:
            artifact: The deployment artifact to audit.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the handler chain.
        """
        final_result = Proceed()
        for handler in self._artifact_handlers:
            result = self._invoke_handler(handler, artifact, lucid_context=lucid_context)
            final_result = result
            if result.decision != AuditDecision.PROCEED:
                break

        self.emit_evidence("artifact", final_result, None)
        return final_result

    def check_request(self, request: RequestPayload, lucid_context: LucidContext = None) -> AuditResult:
        """Run request filtering handlers.

        Args:
            request: The request payload to audit.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the handler chain.
        """
        final_result = Proceed()
        for handler in self._request_handlers:
            result = self._invoke_handler(handler, request, lucid_context=lucid_context)
            final_result = result
            if result.decision != AuditDecision.PROCEED:
                break

        self.emit_evidence("request", final_result, request)
        return final_result

    def check_execution(self, context: ExecutionContext, lucid_context: LucidContext = None) -> AuditResult:
        """Run runtime execution monitoring handlers.

        Args:
            context: The execution context with telemetry data.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the handler chain.
        """
        final_result = Proceed()
        for handler in self._execution_handlers:
            result = self._invoke_handler(handler, context, lucid_context=lucid_context)
            final_result = result
            if result.decision != AuditDecision.PROCEED:
                break

        self.emit_evidence("execution", final_result, None)
        return final_result

    def check_response(
        self,
        response: ResponsePayload,
        request: Optional[RequestPayload] = None,
        lucid_context: LucidContext = None
    ) -> AuditResult:
        """Run output policy validation handlers.

        Args:
            response: The response payload to audit.
            request: Optional original request for context.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the handler chain.
        """
        final_result = Proceed()
        for handler in self._response_handlers:
            result = self._invoke_handler(handler, response, request, lucid_context=lucid_context)
            final_result = result
            if result.decision != AuditDecision.PROCEED:
                break

        self.emit_evidence("response", final_result, request)
        return final_result

# TypeVar for handler decorator return types
HandlerT = TypeVar("HandlerT", bound=Callable[..., AuditResult])


class AuditorBuilder:
    """A builder for composing auditors using decorators.

    This provides a 'fluent' API for creating custom safety nodes.

    Example:
        builder = create_auditor("my-auditor")

        @builder.on_request
        def check_request(data: RequestDict) -> AuditResult:
            if "malicious" in data.get("prompt", ""):
                return Deny("Malicious content detected")
            return Proceed()

        auditor = builder.build()
    """
    _auditor: FunctionAuditor

    def __init__(self, auditor_id: str, version: str = "1.0.0", verifier_url: Optional[str] = None) -> None:
        self._auditor = FunctionAuditor(auditor_id, version, verifier_url)

    def on_artifact(self, func: HandlerT) -> HandlerT:
        """Register a handler for deployment artifacts (Phase 1).

        Args:
            func: Handler function that receives ArtifactPayload.

        Returns:
            The decorated function unchanged.
        """
        self._auditor._artifact_handlers.append(func)
        return func

    def on_request(self, func: HandlerT) -> HandlerT:
        """Register a handler for incoming model requests (Phase 2).

        Args:
            func: Handler function that receives RequestPayload.

        Returns:
            The decorated function unchanged.
        """
        self._auditor._request_handlers.append(func)
        return func

    def on_execution(self, func: HandlerT) -> HandlerT:
        """Register a handler for runtime model execution (Phase 3).

        Args:
            func: Handler function that receives ExecutionContext.

        Returns:
            The decorated function unchanged.
        """
        self._auditor._execution_handlers.append(func)
        return func

    def on_response(self, func: HandlerT) -> HandlerT:
        """Register a handler for model generated responses (Phase 4).

        Args:
            func: Handler function that receives ResponsePayload.

        Returns:
            The decorated function unchanged.
        """
        self._auditor._response_handlers.append(func)
        return func

    def build(self) -> FunctionAuditor:
        """Finish configuration and return the Auditor instance.

        Returns:
            The configured FunctionAuditor ready for use.
        """
        return self._auditor

# Global registry
_registry: Dict[str, Auditor] = {}

def create_auditor(
    auditor_id: Optional[str] = None,
    version: str = "1.0.0",
    verifier_url: Optional[str] = None
) -> AuditorBuilder:
    """Factory function to start building a new Auditor.

    The auditor_id is automatically resolved in the following order:
    1. LUCID_AUDITOR_ID env var (injected by Lucid Operator) - preferred for TEE environments
    2. Explicit auditor_id argument
    3. Static fallback ("unnamed-auditor")

    Args:
        auditor_id: Unique ID for the safety node. If None, uses LUCID_AUDITOR_ID.
        version: Version of the auditor implementation.
        verifier_url: Optional Verifier service endpoint.

    Returns:
        An AuditorBuilder instance.

    Example:
        builder = create_auditor("my-auditor", version="1.0.0")

        @builder.on_request
        def check_request(data: RequestDict) -> AuditResult:
            return Proceed()

        auditor = builder.build()
    """
    # Auto-resolve auditor ID from environment if not explicitly provided
    # Priority: LUCID_AUDITOR_ID > explicit arg > static fallback
    resolved_id = os.getenv("LUCID_AUDITOR_ID") or auditor_id or "unnamed-auditor"

    if os.getenv("LUCID_AUDITOR_ID"):
        logger.info("using_lucid_auditor_id", resolved_id=resolved_id)

    builder = AuditorBuilder(resolved_id, version, verifier_url)
    # Automatically register in the global registry when build() is called
    original_build = builder.build

    def build_and_register() -> FunctionAuditor:
        auditor = original_build()
        _registry[resolved_id] = auditor
        return auditor

    builder.build = build_and_register  # type: ignore[method-assign]
    return builder


class CompositeAuditor(Auditor):
    """A chain of auditors that executes sequentially.

    This implements the 'Auditor Chain' concept where multiple safety nodes
    inspect the same data. Execution stops at the first 'DENY' decision.

    Attributes:
        chain_id (str): Unique identifier for this chain (same as auditor_id).
        auditors (List[Auditor]): Ordered list of safety nodes to run.
        _evidence (List[EvidenceDict]): Evidence collected during last check.
    """
    auditors: List[Auditor]
    _evidence: List[EvidenceDict]

    def __init__(
        self,
        chain_id: str,
        auditors: List[Auditor],
        verifier_url: Optional[str] = None
    ) -> None:
        super().__init__(chain_id, verifier_url=verifier_url)
        self.auditors = auditors
        self._evidence = []

    def check_artifact(self, artifact: ArtifactPayload, lucid_context: LucidContext = None) -> AuditResult:
        """Run all auditors in the chain on the artifact.

        Args:
            artifact: The deployment artifact to audit.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the chain (first DENY or final PROCEED).
        """
        self._evidence.clear()
        context: Dict[str, AuditorDataDict] = dict(lucid_context) if lucid_context else {}
        for auditor in self.auditors:
            result = auditor.check_artifact(artifact, lucid_context=context)
            self._evidence.append(auditor.create_evidence("artifact", result))
            if result.data:
                context[auditor.auditor_id] = result.data
            if result.decision == AuditDecision.DENY:
                return result
        return Proceed()

    def check_request(self, request: RequestPayload, lucid_context: LucidContext = None) -> AuditResult:
        """Run all auditors in the chain on the request.

        Args:
            request: The request payload to audit.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the chain (first DENY or last result).
        """
        self._evidence.clear()
        context: Dict[str, AuditorDataDict] = dict(lucid_context) if lucid_context else {}
        last_result = Proceed()
        for auditor in self.auditors:
            result = auditor.check_request(request, lucid_context=context)
            last_result = result
            self._evidence.append(auditor.create_evidence("request", result))
            if result.data:
                context[auditor.auditor_id] = result.data
            if result.decision == AuditDecision.DENY:
                return result
        return last_result

    def check_execution(self, context: ExecutionContext, lucid_context: LucidContext = None) -> AuditResult:
        """Monitor execution across all auditors in the chain.

        Args:
            context: The execution context with telemetry data.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the chain (first DENY or final PROCEED).
        """
        ctx: Dict[str, AuditorDataDict] = dict(lucid_context) if lucid_context else {}
        for auditor in self.auditors:
            result = auditor.check_execution(context, lucid_context=ctx)
            if result.data:
                ctx[auditor.auditor_id] = result.data
            if result.decision == AuditDecision.DENY:
                return result
        return Proceed()

    def check_response(
        self,
        response: ResponsePayload,
        request: Optional[RequestPayload] = None,
        lucid_context: LucidContext = None
    ) -> AuditResult:
        """Validate response across all auditors in the chain.

        Args:
            response: The response payload to audit.
            request: Optional original request for context.
            lucid_context: Optional context from previous auditors.

        Returns:
            AuditResult from the chain (first DENY or last result).
        """
        ctx: Dict[str, AuditorDataDict] = dict(lucid_context) if lucid_context else {}
        last_result = Proceed()
        for auditor in self.auditors:
            result = auditor.check_response(response, request, lucid_context=ctx)
            last_result = result
            self._evidence.append(auditor.create_evidence("response", result))
            if result.data:
                ctx[auditor.auditor_id] = result.data
            if result.decision == AuditDecision.DENY:
                return result
        return last_result

    def get_evidence(self) -> List[EvidenceDict]:
        """Return the signed evidence collected during the last check.

        Returns:
            List of EvidenceDict from all auditors in the chain.
        """
        return self._evidence


def create_chain(
    chain_id: str,
    auditor_ids: List[str],
    verifier_url: Optional[str] = None
) -> CompositeAuditor:
    """Create a composite auditor chain from registered IDs.

    Args:
        chain_id: Unique ID for the resulting chain.
        auditor_ids: List of IDs of already registered auditors.
        verifier_url: Optional Verifier endpoint.

    Returns:
        A CompositeAuditor instance.

    Raises:
        ValueError: If any auditor_id is not found in the registry.

    Example:
        # Create individual auditors first
        builder1 = create_auditor("pii-auditor")
        builder1.build()

        builder2 = create_auditor("injection-auditor")
        builder2.build()

        # Then create the chain
        chain = create_chain("safety-chain", ["pii-auditor", "injection-auditor"])
    """
    auditors: List[Auditor] = []
    for aid in auditor_ids:
        if aid not in _registry:
            raise ValueError(f"Auditor {aid} not registered.")
        auditors.append(_registry[aid])
    return CompositeAuditor(chain_id, auditors, verifier_url=verifier_url)
