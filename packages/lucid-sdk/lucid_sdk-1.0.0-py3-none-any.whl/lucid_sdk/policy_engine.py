"""
Policy Engine for Lucid Auditor Policy Evaluation

This module provides a comprehensive policy engine for evaluating claims against
auditor policies defined in YAML format. It integrates with the LPL (Lucid Policy
Language) expression parser for condition evaluation.

The policy engine:
    - Validates claims against required/optional claim specifications
    - Evaluates policy rules using LPL expressions
    - Enforces policy decisions based on rule outcomes and enforcement mode
    - Produces detailed evaluation results for audit trails

Key Classes:
    - PolicyResult: Result of claim validation against requirements
    - RuleResult: Result of evaluating a single policy rule
    - PolicyEvaluationResult: Complete evaluation including decision and details
    - PolicyEngine: Main engine class for policy evaluation

Helper Functions:
    - load_policy: Load an AuditorPolicy from a YAML file
    - load_policy_bundle: Load a PolicyBundle from a YAML file

Example Usage:
    >>> from lucid_sdk.policy_engine import PolicyEngine, load_policy
    >>> from lucid_schemas import Claim, MeasurementType
    >>> from datetime import datetime, timezone
    >>>
    >>> # Load a policy from YAML
    >>> policy = load_policy("/path/to/policy.yaml")
    >>>
    >>> # Create engine and evaluate claims
    >>> engine = PolicyEngine(policy)
    >>> claims = [
    ...     Claim(
    ...         name="location.country",
    ...         type=MeasurementType.conformity,
    ...         value="IN",
    ...         timestamp=datetime.now(timezone.utc),
    ...         confidence=0.95
    ...     )
    ... ]
    >>> result = engine.evaluate(claims)
    >>> print(result.decision)  # AuditDecision.PROCEED or DENY

Author: Lucid Team
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from lucid_schemas import Claim, AuditDecision, Evidence
from lucid_schemas.attestation import AttestationResult
from lucid_schemas.enums import TrustTier
from lucid_schemas.policy import (
    AuditorPolicy,
    PolicyBundle,
    PolicyRule,
    ClaimRequirement,
    EnforcementMode,
    ClaimAppraisalStatus,
    ClaimAppraisalRecord,
    AppraisalRecord,
)

from .lpl_parser import LPLExpressionParser, LPLParseError, LPLEvaluationError
from .exceptions import LucidError, ConfigurationError

logger = logging.getLogger(__name__)


# =============================================================================
# Optional jsonschema import
# =============================================================================

try:
    import jsonschema
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    jsonschema = None  # type: ignore
    JSONSCHEMA_AVAILABLE = False


# =============================================================================
# Exception Classes
# =============================================================================


class PolicyError(LucidError):
    """Exception raised for policy-related errors.

    This error indicates issues with policy loading, validation, or evaluation.

    Attributes:
        policy_id: ID of the policy that caused the error (if available).
    """

    def __init__(
        self,
        message: str,
        policy_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if policy_id:
            details["policy_id"] = policy_id

        super().__init__(message, "POLICY_ERROR", details)
        self.policy_id = policy_id


class PolicyLoadError(PolicyError):
    """Exception raised when a policy file cannot be loaded.

    Attributes:
        file_path: Path to the file that could not be loaded.
    """

    def __init__(
        self,
        message: str,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if file_path:
            details["file_path"] = file_path

        super().__init__(message, details=details)
        self.error_code = "POLICY_LOAD_ERROR"
        self.file_path = file_path


class PolicyValidationError(PolicyError):
    """Exception raised when policy validation fails.

    Attributes:
        claim_name: Name of the claim that failed validation (if applicable).
    """

    def __init__(
        self,
        message: str,
        policy_id: Optional[str] = None,
        claim_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if claim_name:
            details["claim_name"] = claim_name

        super().__init__(message, policy_id=policy_id, details=details)
        self.error_code = "POLICY_VALIDATION_ERROR"
        self.claim_name = claim_name


# =============================================================================
# Result Models
# =============================================================================


class PolicyResult(BaseModel):
    """Result of claim validation against policy requirements.

    This model captures whether the provided claims satisfy the policy's
    required and optional claim specifications.

    Attributes:
        valid: Whether all required claims are present and valid.
        errors: List of validation error messages.

    Example:
        >>> result = PolicyResult(valid=False, errors=["Missing required claim: location.country"])
        >>> if not result.valid:
        ...     for error in result.errors:
        ...         print(f"Validation error: {error}")
    """

    valid: bool = Field(
        ...,
        description="Whether all required claims are present and valid."
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation error messages."
    )


class RuleResult(BaseModel):
    """Result of evaluating a single policy rule.

    Captures the outcome of evaluating one rule's LPL condition against
    the provided claims.

    Attributes:
        rule_id: Unique identifier of the evaluated rule.
        triggered: Whether the rule was triggered (condition NOT met).
        action: The action specified by the rule (if triggered).
        message: The rule's message (if triggered).
        error: Error message if evaluation failed.

    Note:
        A rule is "triggered" when its condition evaluates to False.
        This follows the convention that conditions define what must be
        true for the rule to NOT trigger (i.e., pass).

    Example:
        >>> result = RuleResult(
        ...     rule_id="location-check",
        ...     triggered=True,
        ...     action="deny",
        ...     message="Request denied: location outside allowed region"
        ... )
    """

    rule_id: str = Field(
        ...,
        description="Unique identifier of the evaluated rule."
    )
    triggered: bool = Field(
        default=False,
        description="Whether the rule was triggered (condition NOT met)."
    )
    action: Optional[str] = Field(
        default=None,
        description="The action specified by the rule (if triggered)."
    )
    message: Optional[str] = Field(
        default=None,
        description="The rule's message (if triggered)."
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if evaluation failed."
    )


class PolicyEvaluationResult(BaseModel):
    """Complete result of policy evaluation.

    This model provides a comprehensive view of the policy evaluation,
    including the final decision, validation results, and individual
    rule evaluation results.

    Attributes:
        decision: The final audit decision (PROCEED, DENY, REDACT, WARN).
        validation: Result of claim validation against requirements.
        rule_results: List of individual rule evaluation results.
        policy_id: ID of the policy that was evaluated.
        policy_version: Version of the policy that was evaluated.

    Example:
        >>> result = engine.evaluate(claims)
        >>> if result.decision == AuditDecision.DENY:
        ...     triggered = [r for r in result.rule_results if r.triggered]
        ...     for rule in triggered:
        ...         print(f"Rule {rule.rule_id}: {rule.message}")
    """

    decision: AuditDecision = Field(
        ...,
        description="The final audit decision."
    )
    validation: PolicyResult = Field(
        ...,
        description="Result of claim validation against requirements."
    )
    rule_results: List[RuleResult] = Field(
        default_factory=list,
        description="List of individual rule evaluation results."
    )
    policy_id: str = Field(
        ...,
        description="ID of the policy that was evaluated."
    )
    policy_version: str = Field(
        ...,
        description="Version of the policy that was evaluated."
    )


# =============================================================================
# Policy Engine
# =============================================================================


class PolicyEngine:
    """Engine for evaluating claims against auditor policies.

    The PolicyEngine is the main class for policy evaluation. It takes an
    AuditorPolicy and provides methods to validate claims, evaluate rules,
    and determine the final audit decision.

    The evaluation process:
        1. Validate claims against required/optional claim specifications
        2. Evaluate each policy rule's LPL condition
        3. Determine final decision based on rule outcomes and enforcement mode

    Attributes:
        policy: The AuditorPolicy being enforced.
        parser: The LPL expression parser for condition evaluation.
        last_results: Results from the most recent rule evaluation.

    Example:
        >>> policy = load_policy("my_policy.yaml")
        >>> engine = PolicyEngine(policy)
        >>>
        >>> # Full evaluation
        >>> result = engine.evaluate(claims)
        >>> print(f"Decision: {result.decision}")
        >>>
        >>> # Or step-by-step
        >>> validation = engine.validate_claims(claims)
        >>> if validation.valid:
        ...     decision = engine.enforce(claims)
        ...     reason = engine.get_reason()
    """

    def __init__(self, policy: AuditorPolicy) -> None:
        """Initialize the PolicyEngine with an AuditorPolicy.

        Args:
            policy: The AuditorPolicy to enforce.

        Raises:
            ValueError: If policy is None.
        """
        if policy is None:
            raise ValueError("Policy cannot be None")

        self.policy = policy
        self.parser = LPLExpressionParser()
        self.last_results: List[RuleResult] = []

    def find_claim(self, claims: List[Claim], name: str) -> Optional[Claim]:
        """Find a claim by name in the claims list.

        Searches through the provided claims for one matching the given name.

        Args:
            claims: List of claims to search.
            name: The claim name to find.

        Returns:
            The matching Claim if found, None otherwise.

        Example:
            >>> claim = engine.find_claim(claims, "location.country")
            >>> if claim:
            ...     print(f"Found claim with value: {claim.value}")
        """
        for claim in claims:
            if claim.name == name:
                return claim
        return None

    def validate_claims(self, claims: List[Claim]) -> PolicyResult:
        """Validate claims against the policy's claim requirements.

        Checks that:
            - All required claims are present
            - Claims meet minimum confidence thresholds
            - Claim values match their value_schema (if specified)

        Args:
            claims: List of claims to validate.

        Returns:
            PolicyResult indicating whether validation passed and any errors.

        Example:
            >>> result = engine.validate_claims(claims)
            >>> if not result.valid:
            ...     print(f"Validation failed: {result.errors}")
        """
        errors: List[str] = []

        # Validate required claims
        for requirement in self.policy.required_claims:
            claim = self.find_claim(claims, requirement.name)

            if claim is None:
                if requirement.required:
                    errors.append(f"Missing required claim: {requirement.name}")
                continue

            # Check confidence threshold
            if requirement.min_confidence is not None:
                if claim.confidence < requirement.min_confidence:
                    errors.append(
                        f"Claim '{requirement.name}' confidence {claim.confidence:.2f} "
                        f"below minimum {requirement.min_confidence:.2f}"
                    )

            # Check value schema
            if requirement.value_schema is not None:
                if not self.validate_schema(claim.value, requirement.value_schema):
                    errors.append(
                        f"Claim '{requirement.name}' value does not match schema"
                    )

        # Validate optional claims (only if present)
        for requirement in self.policy.optional_claims:
            claim = self.find_claim(claims, requirement.name)

            if claim is None:
                # Optional claims don't generate errors when missing
                continue

            # Check confidence threshold
            if requirement.min_confidence is not None:
                if claim.confidence < requirement.min_confidence:
                    errors.append(
                        f"Claim '{requirement.name}' confidence {claim.confidence:.2f} "
                        f"below minimum {requirement.min_confidence:.2f}"
                    )

            # Check value schema
            if requirement.value_schema is not None:
                if not self.validate_schema(claim.value, requirement.value_schema):
                    errors.append(
                        f"Claim '{requirement.name}' value does not match schema"
                    )

        return PolicyResult(
            valid=len(errors) == 0,
            errors=errors
        )

    def validate_schema(self, value: Any, schema: Dict[str, Any]) -> bool:
        """Validate a value against a JSON Schema.

        Uses the jsonschema library if available. If jsonschema is not
        installed, this method returns True (validation skipped).

        Args:
            value: The value to validate.
            schema: The JSON Schema to validate against.

        Returns:
            True if the value matches the schema (or jsonschema unavailable),
            False if validation fails.

        Note:
            The jsonschema library is an optional dependency. If not installed,
            schema validation is skipped with a warning logged.

        Example:
            >>> schema = {"type": "object", "properties": {"country": {"type": "string"}}}
            >>> engine.validate_schema({"country": "IN"}, schema)
            True
        """
        if not JSONSCHEMA_AVAILABLE:
            logger.warning(
                "jsonschema not installed, skipping schema validation. "
                "Install with: pip install jsonschema"
            )
            return True

        try:
            jsonschema.validate(instance=value, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.debug(f"Schema validation failed: {e.message}")
            return False
        except jsonschema.SchemaError as e:
            logger.warning(f"Invalid JSON Schema: {e.message}")
            return True  # Don't fail on invalid schema, just skip validation

    def evaluate_rules(self, claims: List[Claim]) -> List[RuleResult]:
        """Evaluate all policy rules against the provided claims.

        Each rule's LPL condition is evaluated. A rule is "triggered" when
        its condition evaluates to False (meaning the condition for proceeding
        is NOT met).

        Args:
            claims: List of claims to evaluate rules against.

        Returns:
            List of RuleResult objects, one for each rule.

        Note:
            The results are also stored in self.last_results for later
            retrieval via get_reason().

        Example:
            >>> results = engine.evaluate_rules(claims)
            >>> for result in results:
            ...     if result.triggered:
            ...         print(f"Rule {result.rule_id} triggered: {result.message}")
        """
        results: List[RuleResult] = []

        # Build claims dictionary for LPL evaluation
        claims_dict = {claim.name: claim for claim in claims}

        for rule in self.policy.rules:
            result = self._evaluate_single_rule(rule, claims_dict)
            results.append(result)

        # Store for later retrieval
        self.last_results = results
        return results

    def _evaluate_single_rule(
        self,
        rule: PolicyRule,
        claims_dict: Dict[str, Claim]
    ) -> RuleResult:
        """Evaluate a single policy rule.

        Args:
            rule: The PolicyRule to evaluate.
            claims_dict: Dictionary mapping claim names to Claim objects.

        Returns:
            RuleResult for this rule's evaluation.
        """
        try:
            # Evaluate the condition
            condition_met = self.parser.evaluate(rule.condition, claims_dict)

            # Rule triggers when condition is NOT met
            triggered = not condition_met

            if triggered:
                return RuleResult(
                    rule_id=rule.id,
                    triggered=True,
                    action=rule.action,
                    message=rule.message
                )
            else:
                return RuleResult(
                    rule_id=rule.id,
                    triggered=False
                )

        except (LPLParseError, LPLEvaluationError) as e:
            logger.warning(
                f"Rule '{rule.id}' evaluation failed: {e.message}",
                extra={"rule_id": rule.id, "error": str(e)}
            )
            return RuleResult(
                rule_id=rule.id,
                triggered=False,
                error=str(e)
            )
        except Exception as e:
            logger.error(
                f"Unexpected error evaluating rule '{rule.id}': {e}",
                extra={"rule_id": rule.id, "error": str(e)}
            )
            return RuleResult(
                rule_id=rule.id,
                triggered=False,
                error=f"Unexpected error: {str(e)}"
            )

    def enforce(self, claims: List[Claim]) -> AuditDecision:
        """Enforce the policy and return the audit decision.

        Evaluates all rules and determines the final decision based on:
            1. Which rules triggered (condition NOT met)
            2. The actions specified by triggered rules
            3. The policy's enforcement mode

        Decision logic:
            - If any rule with action="deny" triggers:
                - EnforcementMode.BLOCK -> DENY
                - EnforcementMode.WARN -> WARN
                - EnforcementMode.LOG -> PROCEED (silent logging)
                - EnforcementMode.AUDIT -> WARN (requires review)
            - If any rule with action="warn" triggers -> WARN
            - If any rule with action="redact" triggers -> REDACT
            - Otherwise -> PROCEED

        Args:
            claims: List of claims to evaluate.

        Returns:
            The AuditDecision for this request.

        Example:
            >>> decision = engine.enforce(claims)
            >>> if decision == AuditDecision.DENY:
            ...     return {"error": engine.get_reason()}
        """
        # Evaluate all rules
        rule_results = self.evaluate_rules(claims)

        # Collect triggered rules by action
        deny_rules = [r for r in rule_results if r.triggered and r.action == "deny"]
        warn_rules = [r for r in rule_results if r.triggered and r.action == "warn"]
        redact_rules = [r for r in rule_results if r.triggered and r.action == "redact"]

        # Check deny rules first (highest priority)
        if deny_rules:
            # Apply enforcement mode
            if self.policy.enforcement == EnforcementMode.BLOCK:
                return AuditDecision.DENY
            elif self.policy.enforcement == EnforcementMode.WARN:
                return AuditDecision.WARN
            elif self.policy.enforcement == EnforcementMode.LOG:
                # Silent logging - proceed but log the violation
                logger.info(
                    f"Policy violation logged (enforcement=log): "
                    f"{[r.message for r in deny_rules]}"
                )
                return AuditDecision.PROCEED
            elif self.policy.enforcement == EnforcementMode.AUDIT:
                # Requires human review
                return AuditDecision.WARN

        # Check warn rules
        if warn_rules:
            return AuditDecision.WARN

        # Check redact rules
        if redact_rules:
            return AuditDecision.REDACT

        # No rules triggered - proceed
        return AuditDecision.PROCEED

    def evaluate(self, claims: List[Claim]) -> PolicyEvaluationResult:
        """Perform complete policy evaluation.

        This is the main entry point for policy evaluation. It:
            1. Validates claims against requirements
            2. Evaluates all policy rules
            3. Determines the final decision
            4. Returns a comprehensive result

        Args:
            claims: List of claims to evaluate.

        Returns:
            PolicyEvaluationResult with decision, validation, and rule results.

        Example:
            >>> result = engine.evaluate(claims)
            >>> print(f"Decision: {result.decision}")
            >>> print(f"Validation: {'PASS' if result.validation.valid else 'FAIL'}")
            >>> for rule in result.rule_results:
            ...     if rule.triggered:
            ...         print(f"  - {rule.rule_id}: {rule.message}")
        """
        # Validate claims first
        validation = self.validate_claims(claims)

        # If validation fails, deny immediately (for BLOCK mode)
        if not validation.valid:
            if self.policy.enforcement == EnforcementMode.BLOCK:
                return PolicyEvaluationResult(
                    decision=AuditDecision.DENY,
                    validation=validation,
                    rule_results=[],
                    policy_id=self.policy.policy_id,
                    policy_version=self.policy.version
                )
            elif self.policy.enforcement in (EnforcementMode.WARN, EnforcementMode.AUDIT):
                # Continue with rule evaluation but note the validation failure
                pass
            else:
                # LOG mode - continue anyway
                pass

        # Evaluate rules and enforce
        decision = self.enforce(claims)

        # Override decision if validation failed and we're in a strict mode
        if not validation.valid and self.policy.enforcement == EnforcementMode.BLOCK:
            decision = AuditDecision.DENY

        return PolicyEvaluationResult(
            decision=decision,
            validation=validation,
            rule_results=self.last_results,
            policy_id=self.policy.policy_id,
            policy_version=self.policy.version
        )

    def get_reason(self) -> str:
        """Get a human-readable reason for the last evaluation result.

        Builds a summary of triggered rules and their messages from the
        most recent call to evaluate_rules() or enforce().

        Returns:
            A string describing the triggered rules, or "No rules triggered"
            if the evaluation passed.

        Example:
            >>> decision = engine.enforce(claims)
            >>> if decision == AuditDecision.DENY:
            ...     print(f"Denied: {engine.get_reason()}")
        """
        if not self.last_results:
            return "No rules evaluated"

        triggered = [r for r in self.last_results if r.triggered]

        if not triggered:
            return "No rules triggered"

        reasons = []
        for result in triggered:
            if result.message:
                reasons.append(f"[{result.rule_id}] {result.message}")
            else:
                reasons.append(f"[{result.rule_id}] Rule triggered (action: {result.action})")

        return "; ".join(reasons)

    # =========================================================================
    # RFC 9334 RATS-Compliant Appraisal Methods
    # =========================================================================

    def appraise_evidence(self, evidence: Evidence) -> Evidence:
        """Appraise Evidence and set its trust_tier (RFC 9334 compliant).

        This is the RATS-compliant way to evaluate Evidence. The Verifier
        applies the Appraisal Policy for Evidence to assess trustworthiness
        and sets the trust_tier field on the Evidence.

        Per RFC 9334:
            - "affirming": Claims meet all policy requirements
            - "warning": Claims have minor issues but are acceptable
            - "contraindicated": Claims violate critical policy rules
            - "none": Unable to determine trustworthiness

        Also populates the EAR-compliant appraisal_record with per-claim
        appraisal details for visualization and audit.

        Args:
            evidence: The Evidence object to appraise.

        Returns:
            The same Evidence object with trust_tier and appraisal_record set.

        Example:
            >>> appraised = engine.appraise_evidence(evidence)
            >>> print(f"Trust tier: {appraised.trust_tier}")
            >>> for claim_result in appraised.appraisal_record['claim_appraisals']:
            ...     print(f"  {claim_result['claim_name']}: {claim_result['status']}")
        """
        from datetime import datetime, timezone

        # Extract claims from this evidence
        claims = evidence.claims

        # Run full evaluation
        result = self.evaluate(claims)

        # Map decision to RATS trust_tier
        trust_tier = self._decision_to_trust_tier(result.decision)

        # Update evidence with trust tier (RATS Verifier output)
        evidence.trust_tier = trust_tier

        # Generate per-claim appraisal records (EAR-compliant)
        claim_appraisals = self._generate_claim_appraisals(claims, result.rule_results)

        # Create the AppraisalRecord
        appraisal_record = AppraisalRecord(
            evidence_id=evidence.evidence_id,
            attester_id=evidence.attester_id,
            policy_id=self.policy.policy_id,
            policy_version=self.policy.version,
            overall_status=trust_tier,
            claim_appraisals=claim_appraisals,
            appraised_at=datetime.now(timezone.utc),
            claims_affirming=sum(1 for c in claim_appraisals if c.status == ClaimAppraisalStatus.AFFIRMING),
            claims_warning=sum(1 for c in claim_appraisals if c.status == ClaimAppraisalStatus.WARNING),
            claims_contraindicated=sum(1 for c in claim_appraisals if c.status == ClaimAppraisalStatus.CONTRAINDICATED),
        )

        # Store as dict on Evidence (to avoid circular import issues)
        evidence.appraisal_record = appraisal_record.model_dump()

        logger.info(
            f"Appraised evidence '{evidence.evidence_id}': trust_tier={trust_tier.value}",
            extra={
                "evidence_id": evidence.evidence_id,
                "attester_id": evidence.attester_id,
                "trust_tier": trust_tier.value,
                "decision": result.decision.value,
                "claims_affirming": appraisal_record.claims_affirming,
                "claims_contraindicated": appraisal_record.claims_contraindicated,
            }
        )

        return evidence

    def _generate_claim_appraisals(
        self,
        claims: List[Claim],
        rule_results: List[RuleResult]
    ) -> List[ClaimAppraisalRecord]:
        """Generate per-claim appraisal records for EAR compliance.

        Maps each claim to its appraisal status based on:
        1. Which rules evaluated the claim
        2. Which rules the claim triggered (failed)
        3. The reference values from policy requirements

        Args:
            claims: List of claims to generate appraisals for.
            rule_results: Results from rule evaluation.

        Returns:
            List of ClaimAppraisalRecord for each claim.
        """
        claim_appraisals: List[ClaimAppraisalRecord] = []

        # Build a map of claim names to the rules that reference them
        claim_to_rules: Dict[str, List[str]] = {}
        claim_to_triggered: Dict[str, List[str]] = {}

        for rule_result in rule_results:
            # Extract claim names from the rule condition
            rule = self._find_rule_by_id(rule_result.rule_id)
            if rule:
                referenced_claims = self._extract_claims_from_condition(rule.condition)
                for claim_name in referenced_claims:
                    if claim_name not in claim_to_rules:
                        claim_to_rules[claim_name] = []
                    claim_to_rules[claim_name].append(rule_result.rule_id)

                    if rule_result.triggered:
                        if claim_name not in claim_to_triggered:
                            claim_to_triggered[claim_name] = []
                        claim_to_triggered[claim_name].append(rule_result.rule_id)

        # Generate appraisal for each claim
        for claim in claims:
            # Determine status based on triggered rules
            triggered_rules = claim_to_triggered.get(claim.name, [])
            evaluated_by = claim_to_rules.get(claim.name, [])

            if triggered_rules:
                # Check the action of triggered rules
                has_deny = any(
                    self._get_rule_action(r) == "deny"
                    for r in triggered_rules
                )
                if has_deny:
                    status = ClaimAppraisalStatus.CONTRAINDICATED
                else:
                    status = ClaimAppraisalStatus.WARNING
            else:
                status = ClaimAppraisalStatus.AFFIRMING

            # Get reference value from policy requirements
            reference_value, reference_operator = self._get_reference_for_claim(claim.name)

            # Build the message
            if status == ClaimAppraisalStatus.AFFIRMING:
                message = f"Claim '{claim.name}' meets policy requirements"
            elif status == ClaimAppraisalStatus.WARNING:
                message = f"Claim '{claim.name}' has warnings: {triggered_rules}"
            else:
                message = f"Claim '{claim.name}' violates policy: {triggered_rules}"

            appraisal = ClaimAppraisalRecord(
                claim_name=claim.name,
                claim_value=claim.value,
                claim_confidence=claim.confidence,
                status=status,
                evaluated_by_rules=evaluated_by,
                triggered_rules=triggered_rules,
                reference_value=reference_value,
                reference_operator=reference_operator,
                compliance_framework=claim.compliance_framework,
                control_id=claim.control_id,
                message=message,
            )
            claim_appraisals.append(appraisal)

        return claim_appraisals

    def _find_rule_by_id(self, rule_id: str) -> Optional[PolicyRule]:
        """Find a policy rule by its ID."""
        for rule in self.policy.rules:
            if rule.id == rule_id:
                return rule
        return None

    def _get_rule_action(self, rule_id: str) -> Optional[str]:
        """Get the action for a rule by ID."""
        rule = self._find_rule_by_id(rule_id)
        return rule.action if rule else None

    def _extract_claims_from_condition(self, condition: str) -> List[str]:
        """Extract claim names referenced in a condition expression.

        Parses expressions like "claims['location.country'].value == 'IN'"
        to extract "location.country".
        """
        try:
            return list(self.parser.get_referenced_claims(condition))
        except Exception:
            # If parsing fails, return empty list
            return []

    def _get_reference_for_claim(self, claim_name: str) -> tuple:
        """Get reference value and operator for a claim from policy.

        Attempts to extract the expected value from policy rules
        for visualization purposes.

        Returns:
            Tuple of (reference_value, reference_operator) or (None, None)
        """
        # Look through rules for conditions involving this claim
        for rule in self.policy.rules:
            if f"claims['{claim_name}']" in rule.condition:
                # Try to extract the comparison
                # This is a simplified extraction - could be enhanced
                condition = rule.condition

                # Look for common patterns
                for op in ["==", "!=", ">=", "<=", ">", "<"]:
                    if op in condition:
                        # Try to extract the value after the operator
                        parts = condition.split(op)
                        if len(parts) == 2:
                            value_part = parts[1].strip()
                            # Remove quotes for string literals
                            if value_part.startswith("'") and value_part.endswith("'"):
                                return (value_part[1:-1], op)
                            elif value_part.startswith('"') and value_part.endswith('"'):
                                return (value_part[1:-1], op)
                            # Try to parse as number
                            try:
                                return (float(value_part), op)
                            except ValueError:
                                pass
                            # Boolean
                            if value_part in ("True", "true"):
                                return (True, op)
                            if value_part in ("False", "false"):
                                return (False, op)

        return (None, None)

    def appraise_attestation_result(
        self,
        attestation_result: AttestationResult
    ) -> AttestationResult:
        """Appraise all Evidence in an AttestationResult (RFC 9334 compliant).

        This is the primary RATS-compliant method for checking if Claims in
        AttestationResults are aligned with a policy. It:

        1. Iterates through all Evidence bundles in the AttestationResult
        2. Applies the Appraisal Policy to each Evidence's Claims
        3. Sets the trust_tier on each Evidence
        4. Updates the overall deployment_authorized status

        Per RFC 9334, the Verifier processes Evidence and produces Attestation
        Results that Relying Parties can use for authorization decisions.

        Args:
            attestation_result: The AttestationResult to appraise.

        Returns:
            The updated AttestationResult with:
                - Each Evidence's trust_tier set
                - deployment_authorized updated based on appraisal
                - authorization_reason explaining the decision

        Example:
            >>> result = engine.appraise_attestation_result(attestation_result)
            >>> if result.deployment_authorized:
            ...     print("All evidence appraised successfully")
            >>> else:
            ...     print(f"Appraisal failed: {result.authorization_reason}")
        """
        if not attestation_result.evidence:
            logger.warning("AttestationResult has no evidence to appraise")
            attestation_result.authorization_reason = "No evidence provided for appraisal"
            return attestation_result

        # Appraise each evidence bundle
        all_affirmed = True
        has_contraindicated = False
        reasons: List[str] = []

        for evidence in attestation_result.evidence:
            self.appraise_evidence(evidence)

            if evidence.trust_tier == TrustTier.CONTRAINDICATED:
                has_contraindicated = True
                all_affirmed = False
                reasons.append(
                    f"Evidence '{evidence.evidence_id}' from '{evidence.attester_id}' "
                    f"is contraindicated"
                )
            elif evidence.trust_tier == TrustTier.WARNING:
                all_affirmed = False
                reasons.append(
                    f"Evidence '{evidence.evidence_id}' from '{evidence.attester_id}' "
                    f"has warnings"
                )
            elif evidence.trust_tier == TrustTier.NONE:
                all_affirmed = False
                reasons.append(
                    f"Evidence '{evidence.evidence_id}' from '{evidence.attester_id}' "
                    f"could not be appraised"
                )

        # Update overall authorization based on enforcement mode
        if self.policy.enforcement == EnforcementMode.BLOCK:
            # Strict mode: deny if any evidence is contraindicated
            attestation_result.deployment_authorized = not has_contraindicated
        elif self.policy.enforcement == EnforcementMode.WARN:
            # Warn mode: authorize but note issues
            attestation_result.deployment_authorized = True
        elif self.policy.enforcement == EnforcementMode.LOG:
            # Log mode: always authorize (silent logging)
            attestation_result.deployment_authorized = True
        else:
            # Audit mode: require human review
            attestation_result.deployment_authorized = all_affirmed

        # Set authorization reason
        if attestation_result.deployment_authorized:
            if all_affirmed:
                attestation_result.authorization_reason = (
                    f"All {len(attestation_result.evidence)} evidence bundles affirmed "
                    f"by policy '{self.policy.policy_id}'"
                )
            else:
                attestation_result.authorization_reason = (
                    f"Authorized with warnings: {'; '.join(reasons)}"
                )
        else:
            attestation_result.authorization_reason = (
                f"Policy violation: {'; '.join(reasons)}"
            )

        logger.info(
            f"Appraised AttestationResult '{attestation_result.passport_id}': "
            f"authorized={attestation_result.deployment_authorized}",
            extra={
                "passport_id": attestation_result.passport_id,
                "authorized": attestation_result.deployment_authorized,
                "policy_id": self.policy.policy_id,
                "evidence_count": len(attestation_result.evidence),
            }
        )

        return attestation_result

    def extract_all_claims(
        self,
        attestation_result: AttestationResult
    ) -> List[Claim]:
        """Extract all Claims from all Evidence in an AttestationResult.

        Flattens the nested structure to get a single list of all Claims
        for policy evaluation.

        Args:
            attestation_result: The AttestationResult to extract claims from.

        Returns:
            List of all Claims from all Evidence bundles.

        Example:
            >>> claims = engine.extract_all_claims(attestation_result)
            >>> print(f"Found {len(claims)} total claims")
        """
        all_claims: List[Claim] = []
        for evidence in attestation_result.evidence:
            all_claims.extend(evidence.claims)
        return all_claims

    def _decision_to_trust_tier(self, decision: AuditDecision) -> TrustTier:
        """Map AuditDecision to RFC 9334 TrustTier.

        Per RFC 9334 EAR (Entity Attestation Results) format:
            - affirming: Positive appraisal, claims are trustworthy
            - warning: Minor issues, but acceptable
            - contraindicated: Claims violate policy, not trustworthy
            - none: Unable to determine

        Args:
            decision: The AuditDecision from policy evaluation.

        Returns:
            Corresponding TrustTier value.
        """
        mapping = {
            AuditDecision.PROCEED: TrustTier.AFFIRMING,
            AuditDecision.WARN: TrustTier.WARNING,
            AuditDecision.REDACT: TrustTier.WARNING,
            AuditDecision.DENY: TrustTier.CONTRAINDICATED,
        }
        return mapping.get(decision, TrustTier.NONE)


# =============================================================================
# Policy Loading Functions
# =============================================================================


def load_policy(path: str) -> AuditorPolicy:
    """Load an AuditorPolicy from a YAML file.

    Parses the YAML file and validates it against the AuditorPolicy schema.

    Args:
        path: Path to the YAML policy file.

    Returns:
        The loaded AuditorPolicy.

    Raises:
        PolicyLoadError: If the file cannot be read or parsed.
        PolicyValidationError: If the YAML doesn't match the policy schema.

    Example:
        >>> policy = load_policy("/path/to/my-policy.yaml")
        >>> print(f"Loaded policy: {policy.name} v{policy.version}")

    YAML Format:
        ```yaml
        schema_version: "1.0.0"
        policy_id: "pol-example"
        version: "1.0.0"
        name: "Example Policy"
        description: "An example policy"
        verification_method: "example-auditor"
        required_claims:
          - name: "example.claim"
            type: "score_binary"
            required: true
        rules:
          - id: "rule-001"
            description: "Check example claim"
            condition: "claims['example.claim'].value == True"
            action: "proceed"
            message: "Example claim verified"
        enforcement: "block"
        ```
    """
    try:
        import yaml
    except ImportError:
        raise PolicyLoadError(
            "PyYAML is required for loading policy files. "
            "Install with: pip install pyyaml",
            file_path=path
        )

    file_path = Path(path)

    if not file_path.exists():
        raise PolicyLoadError(
            f"Policy file not found: {path}",
            file_path=path
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PolicyLoadError(
            f"Invalid YAML in policy file: {e}",
            file_path=path
        )
    except IOError as e:
        raise PolicyLoadError(
            f"Cannot read policy file: {e}",
            file_path=path
        )

    if data is None:
        raise PolicyLoadError(
            "Policy file is empty",
            file_path=path
        )

    try:
        policy = AuditorPolicy(**data)
        return policy
    except Exception as e:
        raise PolicyValidationError(
            f"Invalid policy structure: {e}",
            details={"file_path": path, "parse_error": str(e)}
        )


def load_policy_bundle(path: str) -> PolicyBundle:
    """Load a PolicyBundle from a YAML file.

    Parses the YAML file and validates it against the PolicyBundle schema.

    Args:
        path: Path to the YAML policy bundle file.

    Returns:
        The loaded PolicyBundle.

    Raises:
        PolicyLoadError: If the file cannot be read or parsed.
        PolicyValidationError: If the YAML doesn't match the bundle schema.

    Example:
        >>> bundle = load_policy_bundle("/path/to/bundle.yaml")
        >>> print(f"Loaded bundle: {bundle.name}")
        >>> for policy in bundle.policies:
        ...     print(f"  - {policy.name}")

    YAML Format:
        ```yaml
        schema_version: "1.0.0"
        bundle_id: "bundle-example"
        name: "Example Bundle"
        policies:
          - policy_id: "pol-1"
            version: "1.0.0"
            name: "Policy 1"
            # ... full policy definition
          - policy_id: "pol-2"
            version: "1.0.0"
            name: "Policy 2"
            # ... full policy definition
        composite_rules:
          - id: "cross-check"
            description: "Cross-policy verification"
            condition: "claims['pol1.result'].value and claims['pol2.result'].value"
            action: "proceed"
            message: "All policies passed"
        ```
    """
    try:
        import yaml
    except ImportError:
        raise PolicyLoadError(
            "PyYAML is required for loading policy files. "
            "Install with: pip install pyyaml",
            file_path=path
        )

    file_path = Path(path)

    if not file_path.exists():
        raise PolicyLoadError(
            f"Policy bundle file not found: {path}",
            file_path=path
        )

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PolicyLoadError(
            f"Invalid YAML in policy bundle file: {e}",
            file_path=path
        )
    except IOError as e:
        raise PolicyLoadError(
            f"Cannot read policy bundle file: {e}",
            file_path=path
        )

    if data is None:
        raise PolicyLoadError(
            "Policy bundle file is empty",
            file_path=path
        )

    try:
        bundle = PolicyBundle(**data)
        return bundle
    except Exception as e:
        raise PolicyValidationError(
            f"Invalid policy bundle structure: {e}",
            details={"file_path": path, "parse_error": str(e)}
        )
