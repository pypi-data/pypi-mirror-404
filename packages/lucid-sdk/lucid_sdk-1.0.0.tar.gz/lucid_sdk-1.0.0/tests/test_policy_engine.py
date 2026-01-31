"""Tests for the Policy Engine.

Tests cover:
- PolicyEngine initialization
- validate_claims() with valid/invalid claims
- evaluate_rules() with triggering/non-triggering rules
- enforce() with different enforcement modes
- evaluate() for complete evaluation
- get_reason() for generating human-readable reasons
- load_policy() with valid YAML
- load_policy() error cases (missing file, invalid YAML)
"""

import pytest
import tempfile
import os
from datetime import datetime, timezone
from pathlib import Path

from lucid_schemas import Claim, MeasurementType, AuditDecision
from lucid_schemas.policy import (
    AuditorPolicy,
    PolicyBundle,
    PolicyRule,
    ClaimRequirement,
    EnforcementMode,
)

from lucid_sdk.policy_engine import (
    PolicyEngine,
    PolicyResult,
    RuleResult,
    PolicyEvaluationResult,
    PolicyError,
    PolicyLoadError,
    PolicyValidationError,
    load_policy,
    load_policy_bundle,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_claim_requirement():
    """Create a sample ClaimRequirement."""
    return ClaimRequirement(
        name="location.country",
        type=MeasurementType.location_region,
        required=True,
        min_confidence=0.8
    )


@pytest.fixture
def sample_policy_rule():
    """Create a sample PolicyRule."""
    return PolicyRule(
        id="location-check",
        description="Verify location is in India",
        condition="claims['location.country'].value == 'IN'",
        action="proceed",
        message="Location verified in India"
    )


@pytest.fixture
def deny_rule():
    """Create a PolicyRule with deny action."""
    return PolicyRule(
        id="block-outside-india",
        description="Block requests from outside India",
        condition="claims['location.country'].value == 'IN'",
        action="deny",
        message="Request denied: location outside India"
    )


@pytest.fixture
def warn_rule():
    """Create a PolicyRule with warn action."""
    return PolicyRule(
        id="low-confidence-warning",
        description="Warn on low confidence",
        condition="claims['location.country'].confidence >= 0.9",
        action="warn",
        message="Warning: Low confidence in location verification"
    )


@pytest.fixture
def sample_policy(sample_claim_requirement, sample_policy_rule):
    """Create a sample AuditorPolicy."""
    return AuditorPolicy(
        policy_id="pol-india-location",
        version="1.0.0",
        name="India Location Policy",
        description="Verifies AI workloads run in India",
        verification_method="lucid-location-auditor",
        required_claims=[sample_claim_requirement],
        rules=[sample_policy_rule],
        enforcement=EnforcementMode.BLOCK
    )


@pytest.fixture
def multi_rule_policy(sample_claim_requirement, sample_policy_rule, deny_rule, warn_rule):
    """Create a policy with multiple rules."""
    return AuditorPolicy(
        policy_id="pol-multi-rule",
        version="1.0.0",
        name="Multi-Rule Policy",
        description="Policy with multiple rules",
        verification_method="test-auditor",
        required_claims=[sample_claim_requirement],
        rules=[sample_policy_rule, deny_rule, warn_rule],
        enforcement=EnforcementMode.BLOCK
    )


@pytest.fixture
def india_claim():
    """Create a claim for India location."""
    return Claim(
        name="location.country",
        type=MeasurementType.location_region,
        value="IN",
        timestamp=datetime.now(timezone.utc),
        confidence=0.95
    )


@pytest.fixture
def us_claim():
    """Create a claim for US location."""
    return Claim(
        name="location.country",
        type=MeasurementType.location_region,
        value="US",
        timestamp=datetime.now(timezone.utc),
        confidence=0.95
    )


@pytest.fixture
def low_confidence_claim():
    """Create a claim with low confidence."""
    return Claim(
        name="location.country",
        type=MeasurementType.location_region,
        value="IN",
        timestamp=datetime.now(timezone.utc),
        confidence=0.5
    )


# =============================================================================
# PolicyEngine Initialization Tests
# =============================================================================


class TestPolicyEngineInit:
    """Tests for PolicyEngine initialization."""

    def test_init_with_valid_policy(self, sample_policy):
        """Test initializing PolicyEngine with valid policy."""
        engine = PolicyEngine(sample_policy)
        assert engine.policy == sample_policy
        assert engine.parser is not None
        assert engine.last_results == []

    def test_init_with_none_policy(self):
        """Test that None policy raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            PolicyEngine(None)
        assert "policy cannot be none" in str(exc_info.value).lower()

    def test_engine_has_parser(self, sample_policy):
        """Test that engine has LPL parser."""
        engine = PolicyEngine(sample_policy)
        assert engine.parser is not None


# =============================================================================
# validate_claims() Tests
# =============================================================================


class TestValidateClaims:
    """Tests for validate_claims() method."""

    def test_validate_valid_claims(self, sample_policy, india_claim):
        """Test validation with valid claims."""
        engine = PolicyEngine(sample_policy)
        result = engine.validate_claims([india_claim])
        assert result.valid is True
        assert result.errors == []

    def test_validate_missing_required_claim(self, sample_policy):
        """Test validation with missing required claim."""
        engine = PolicyEngine(sample_policy)
        result = engine.validate_claims([])  # No claims
        assert result.valid is False
        assert len(result.errors) > 0
        assert "missing" in result.errors[0].lower()

    def test_validate_low_confidence(self, sample_policy, low_confidence_claim):
        """Test validation with claim below confidence threshold."""
        engine = PolicyEngine(sample_policy)
        result = engine.validate_claims([low_confidence_claim])
        assert result.valid is False
        assert len(result.errors) > 0
        assert "confidence" in result.errors[0].lower()

    def test_validate_exactly_at_confidence_threshold(self, sample_policy):
        """Test validation with claim exactly at confidence threshold."""
        claim = Claim(
            name="location.country",
            type=MeasurementType.location_region,
            value="IN",
            timestamp=datetime.now(timezone.utc),
            confidence=0.8  # Exactly at threshold
        )
        engine = PolicyEngine(sample_policy)
        result = engine.validate_claims([claim])
        assert result.valid is True

    def test_validate_optional_claim_missing(self):
        """Test that missing optional claims don't cause validation failure."""
        policy = AuditorPolicy(
            policy_id="pol-optional",
            version="1.0.0",
            name="Optional Claim Policy",
            description="Has optional claims",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="required.claim",
                    type=MeasurementType.score_binary
                )
            ],
            optional_claims=[
                ClaimRequirement(
                    name="optional.claim",
                    type=MeasurementType.score_normalized,
                    required=False
                )
            ],
            rules=[
                PolicyRule(
                    id="rule-001",
                    description="Test",
                    condition="True",
                    action="proceed",
                    message="Test"
                )
            ]
        )
        engine = PolicyEngine(policy)
        required_claim = Claim(
            name="required.claim",
            type=MeasurementType.score_binary,
            value=True,
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        result = engine.validate_claims([required_claim])
        assert result.valid is True

    def test_validate_optional_claim_present_but_low_confidence(self):
        """Test that present optional claim with low confidence fails."""
        policy = AuditorPolicy(
            policy_id="pol-optional-conf",
            version="1.0.0",
            name="Optional Confidence Policy",
            description="Optional claim with confidence requirement",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="required.claim",
                    type=MeasurementType.score_binary
                )
            ],
            optional_claims=[
                ClaimRequirement(
                    name="optional.claim",
                    type=MeasurementType.score_normalized,
                    required=False,
                    min_confidence=0.9
                )
            ],
            rules=[
                PolicyRule(
                    id="rule-001",
                    description="Test",
                    condition="True",
                    action="proceed",
                    message="Test"
                )
            ]
        )
        engine = PolicyEngine(policy)
        required_claim = Claim(
            name="required.claim",
            type=MeasurementType.score_binary,
            value=True,
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        optional_claim = Claim(
            name="optional.claim",
            type=MeasurementType.score_normalized,
            value=0.5,
            timestamp=datetime.now(timezone.utc),
            confidence=0.5  # Below threshold
        )
        result = engine.validate_claims([required_claim, optional_claim])
        assert result.valid is False
        assert "confidence" in result.errors[0].lower()


# =============================================================================
# evaluate_rules() Tests
# =============================================================================


class TestEvaluateRules:
    """Tests for evaluate_rules() method."""

    def test_evaluate_rules_all_pass(self, sample_policy, india_claim):
        """Test rule evaluation when all rules pass."""
        engine = PolicyEngine(sample_policy)
        results = engine.evaluate_rules([india_claim])
        assert len(results) == 1
        assert results[0].triggered is False

    def test_evaluate_rules_rule_triggered(self, sample_policy, us_claim):
        """Test rule evaluation when rule is triggered (condition NOT met)."""
        engine = PolicyEngine(sample_policy)
        results = engine.evaluate_rules([us_claim])
        assert len(results) == 1
        assert results[0].triggered is True
        assert results[0].action == "proceed"

    def test_evaluate_rules_stores_last_results(self, sample_policy, india_claim):
        """Test that evaluate_rules stores results in last_results."""
        engine = PolicyEngine(sample_policy)
        results = engine.evaluate_rules([india_claim])
        assert engine.last_results == results

    def test_evaluate_multiple_rules(self, multi_rule_policy, india_claim):
        """Test evaluation of multiple rules."""
        engine = PolicyEngine(multi_rule_policy)
        results = engine.evaluate_rules([india_claim])
        assert len(results) == 3

    def test_evaluate_rules_with_error(self):
        """Test rule evaluation when condition causes error."""
        policy = AuditorPolicy(
            policy_id="pol-error-rule",
            version="1.0.0",
            name="Error Rule Policy",
            description="Has rule that causes error",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="test.claim",
                    type=MeasurementType.score_binary
                )
            ],
            rules=[
                PolicyRule(
                    id="error-rule",
                    description="Rule that accesses missing claim",
                    condition="claims['nonexistent.claim'].value == True",
                    action="deny",
                    message="Should error"
                )
            ]
        )
        engine = PolicyEngine(policy)
        claim = Claim(
            name="test.claim",
            type=MeasurementType.score_binary,
            value=True,
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        results = engine.evaluate_rules([claim])
        assert len(results) == 1
        assert results[0].error is not None


# =============================================================================
# enforce() Tests
# =============================================================================


class TestEnforce:
    """Tests for enforce() method with different enforcement modes."""

    def test_enforce_proceed_when_rules_pass(self, sample_policy, india_claim):
        """Test that enforce returns PROCEED when all rules pass."""
        engine = PolicyEngine(sample_policy)
        decision = engine.enforce([india_claim])
        assert decision == AuditDecision.PROCEED

    def test_enforce_block_mode_deny(self):
        """Test BLOCK mode returns DENY when deny rule triggers."""
        policy = AuditorPolicy(
            policy_id="pol-block-deny",
            version="1.0.0",
            name="Block Deny Policy",
            description="Denies when location is not IN",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="location.country",
                    type=MeasurementType.location_region
                )
            ],
            rules=[
                PolicyRule(
                    id="deny-non-india",
                    description="Deny non-India",
                    condition="claims['location.country'].value == 'IN'",
                    action="deny",
                    message="Denied: Not in India"
                )
            ],
            enforcement=EnforcementMode.BLOCK
        )
        engine = PolicyEngine(policy)
        us_claim = Claim(
            name="location.country",
            type=MeasurementType.location_region,
            value="US",
            timestamp=datetime.now(timezone.utc),
            confidence=0.95
        )
        decision = engine.enforce([us_claim])
        assert decision == AuditDecision.DENY

    def test_enforce_warn_mode_returns_warn(self):
        """Test WARN mode returns WARN when deny rule triggers."""
        policy = AuditorPolicy(
            policy_id="pol-warn-mode",
            version="1.0.0",
            name="Warn Mode Policy",
            description="Warns instead of denying",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="location.country",
                    type=MeasurementType.location_region
                )
            ],
            rules=[
                PolicyRule(
                    id="deny-non-india",
                    description="Deny non-India",
                    condition="claims['location.country'].value == 'IN'",
                    action="deny",
                    message="Denied: Not in India"
                )
            ],
            enforcement=EnforcementMode.WARN
        )
        engine = PolicyEngine(policy)
        us_claim = Claim(
            name="location.country",
            type=MeasurementType.location_region,
            value="US",
            timestamp=datetime.now(timezone.utc),
            confidence=0.95
        )
        decision = engine.enforce([us_claim])
        assert decision == AuditDecision.WARN

    def test_enforce_log_mode_returns_proceed(self):
        """Test LOG mode returns PROCEED even when deny rule triggers."""
        policy = AuditorPolicy(
            policy_id="pol-log-mode",
            version="1.0.0",
            name="Log Mode Policy",
            description="Logs instead of denying",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="location.country",
                    type=MeasurementType.location_region
                )
            ],
            rules=[
                PolicyRule(
                    id="deny-non-india",
                    description="Deny non-India",
                    condition="claims['location.country'].value == 'IN'",
                    action="deny",
                    message="Denied: Not in India"
                )
            ],
            enforcement=EnforcementMode.LOG
        )
        engine = PolicyEngine(policy)
        us_claim = Claim(
            name="location.country",
            type=MeasurementType.location_region,
            value="US",
            timestamp=datetime.now(timezone.utc),
            confidence=0.95
        )
        decision = engine.enforce([us_claim])
        assert decision == AuditDecision.PROCEED

    def test_enforce_audit_mode_returns_warn(self):
        """Test AUDIT mode returns WARN when deny rule triggers."""
        policy = AuditorPolicy(
            policy_id="pol-audit-mode",
            version="1.0.0",
            name="Audit Mode Policy",
            description="Requires human review",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="location.country",
                    type=MeasurementType.location_region
                )
            ],
            rules=[
                PolicyRule(
                    id="deny-non-india",
                    description="Deny non-India",
                    condition="claims['location.country'].value == 'IN'",
                    action="deny",
                    message="Denied: Not in India"
                )
            ],
            enforcement=EnforcementMode.AUDIT
        )
        engine = PolicyEngine(policy)
        us_claim = Claim(
            name="location.country",
            type=MeasurementType.location_region,
            value="US",
            timestamp=datetime.now(timezone.utc),
            confidence=0.95
        )
        decision = engine.enforce([us_claim])
        assert decision == AuditDecision.WARN

    def test_enforce_warn_action_returns_warn(self, sample_policy):
        """Test that warn action returns WARN decision."""
        policy = AuditorPolicy(
            policy_id="pol-warn-action",
            version="1.0.0",
            name="Warn Action Policy",
            description="Has warn action rule",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="test.claim",
                    type=MeasurementType.score_binary
                )
            ],
            rules=[
                PolicyRule(
                    id="warn-rule",
                    description="Warn when condition not met",
                    condition="claims['test.claim'].value == True",
                    action="warn",
                    message="Warning issued"
                )
            ],
            enforcement=EnforcementMode.BLOCK
        )
        engine = PolicyEngine(policy)
        claim = Claim(
            name="test.claim",
            type=MeasurementType.score_binary,
            value=False,  # Condition not met
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        decision = engine.enforce([claim])
        assert decision == AuditDecision.WARN

    def test_enforce_redact_action_returns_redact(self):
        """Test that redact action returns REDACT decision."""
        policy = AuditorPolicy(
            policy_id="pol-redact-action",
            version="1.0.0",
            name="Redact Action Policy",
            description="Has redact action rule",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="pii.detected",
                    type=MeasurementType.score_binary
                )
            ],
            rules=[
                PolicyRule(
                    id="redact-rule",
                    description="Redact when PII detected",
                    condition="claims['pii.detected'].value == False",
                    action="redact",
                    message="PII redacted"
                )
            ],
            enforcement=EnforcementMode.BLOCK
        )
        engine = PolicyEngine(policy)
        claim = Claim(
            name="pii.detected",
            type=MeasurementType.score_binary,
            value=True,  # PII detected, condition not met
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        decision = engine.enforce([claim])
        assert decision == AuditDecision.REDACT


# =============================================================================
# evaluate() Tests
# =============================================================================


class TestEvaluate:
    """Tests for evaluate() method (complete evaluation)."""

    def test_evaluate_success(self, sample_policy, india_claim):
        """Test complete evaluation with success."""
        engine = PolicyEngine(sample_policy)
        result = engine.evaluate([india_claim])
        assert isinstance(result, PolicyEvaluationResult)
        assert result.decision == AuditDecision.PROCEED
        assert result.validation.valid is True
        assert result.policy_id == sample_policy.policy_id
        assert result.policy_version == sample_policy.version

    def test_evaluate_validation_failure_block_mode(self, sample_policy):
        """Test evaluation with validation failure in BLOCK mode."""
        engine = PolicyEngine(sample_policy)
        result = engine.evaluate([])  # No claims
        assert result.decision == AuditDecision.DENY
        assert result.validation.valid is False

    def test_evaluate_rule_triggered(self, sample_policy, us_claim):
        """Test evaluation when rule is triggered."""
        engine = PolicyEngine(sample_policy)
        result = engine.evaluate([us_claim])
        # Rule action is "proceed" so even when triggered, it proceeds
        assert len(result.rule_results) > 0

    def test_evaluate_includes_rule_results(self, sample_policy, india_claim):
        """Test that evaluate includes all rule results."""
        engine = PolicyEngine(sample_policy)
        result = engine.evaluate([india_claim])
        assert len(result.rule_results) == len(sample_policy.rules)


# =============================================================================
# get_reason() Tests
# =============================================================================


class TestGetReason:
    """Tests for get_reason() method."""

    def test_get_reason_no_evaluation(self, sample_policy):
        """Test get_reason when no evaluation has been done."""
        engine = PolicyEngine(sample_policy)
        reason = engine.get_reason()
        assert "no rules evaluated" in reason.lower()

    def test_get_reason_no_triggered_rules(self, sample_policy, india_claim):
        """Test get_reason when no rules triggered."""
        engine = PolicyEngine(sample_policy)
        engine.enforce([india_claim])
        reason = engine.get_reason()
        assert "no rules triggered" in reason.lower()

    def test_get_reason_with_triggered_rules(self, sample_policy, us_claim):
        """Test get_reason when rules are triggered."""
        engine = PolicyEngine(sample_policy)
        engine.enforce([us_claim])
        reason = engine.get_reason()
        assert "location-check" in reason.lower() or "location" in reason.lower()

    def test_get_reason_multiple_triggered_rules(self):
        """Test get_reason with multiple triggered rules."""
        policy = AuditorPolicy(
            policy_id="pol-multi-trigger",
            version="1.0.0",
            name="Multi Trigger Policy",
            description="Multiple rules that trigger",
            verification_method="test",
            required_claims=[
                ClaimRequirement(
                    name="test.claim",
                    type=MeasurementType.score_binary
                )
            ],
            rules=[
                PolicyRule(
                    id="rule-1",
                    description="First rule",
                    condition="claims['test.claim'].value == True",
                    action="warn",
                    message="First rule triggered"
                ),
                PolicyRule(
                    id="rule-2",
                    description="Second rule",
                    condition="claims['test.claim'].value == True",
                    action="warn",
                    message="Second rule triggered"
                )
            ],
            enforcement=EnforcementMode.BLOCK
        )
        engine = PolicyEngine(policy)
        claim = Claim(
            name="test.claim",
            type=MeasurementType.score_binary,
            value=False,  # Both conditions not met
            timestamp=datetime.now(timezone.utc),
            confidence=1.0
        )
        engine.enforce([claim])
        reason = engine.get_reason()
        assert "rule-1" in reason
        assert "rule-2" in reason


# =============================================================================
# load_policy() Tests
# =============================================================================


class TestLoadPolicy:
    """Tests for load_policy() function."""

    def test_load_policy_valid_yaml(self):
        """Test loading valid policy from YAML file."""
        yaml_content = """
schema_version: "1.0.0"
policy_id: "pol-test"
version: "1.0.0"
name: "Test Policy"
description: "A test policy for unit tests"
verification_method: "test-auditor"
required_claims:
  - name: "test.claim"
    type: "score_binary"
    required: true
rules:
  - id: "rule-001"
    description: "Test rule"
    condition: "claims['test.claim'].value == True"
    action: "proceed"
    message: "Test passed"
enforcement: "block"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                policy = load_policy(f.name)
                assert policy.policy_id == "pol-test"
                assert policy.version == "1.0.0"
                assert len(policy.required_claims) == 1
                assert len(policy.rules) == 1
                assert policy.enforcement == EnforcementMode.BLOCK
            finally:
                os.unlink(f.name)

    def test_load_policy_file_not_found(self):
        """Test that missing file raises PolicyLoadError."""
        with pytest.raises(PolicyLoadError) as exc_info:
            load_policy("/nonexistent/path/to/policy.yaml")
        assert "not found" in str(exc_info.value).lower()

    def test_load_policy_invalid_yaml(self):
        """Test that invalid YAML raises PolicyLoadError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            try:
                with pytest.raises(PolicyLoadError) as exc_info:
                    load_policy(f.name)
                assert "yaml" in str(exc_info.value).lower()
            finally:
                os.unlink(f.name)

    def test_load_policy_empty_file(self):
        """Test that empty file raises PolicyLoadError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("")
            f.flush()
            try:
                with pytest.raises(PolicyLoadError) as exc_info:
                    load_policy(f.name)
                assert "empty" in str(exc_info.value).lower()
            finally:
                os.unlink(f.name)

    def test_load_policy_invalid_schema(self):
        """Test that invalid policy schema raises PolicyValidationError."""
        yaml_content = """
policy_id: "pol-invalid"
# Missing required fields: version, name, description, verification_method, required_claims, rules
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                with pytest.raises(PolicyValidationError):
                    load_policy(f.name)
            finally:
                os.unlink(f.name)


# =============================================================================
# load_policy_bundle() Tests
# =============================================================================


class TestLoadPolicyBundle:
    """Tests for load_policy_bundle() function."""

    def test_load_policy_bundle_valid_yaml(self):
        """Test loading valid policy bundle from YAML file."""
        yaml_content = """
schema_version: "1.0.0"
bundle_id: "bundle-test"
name: "Test Bundle"
policies:
  - policy_id: "pol-1"
    version: "1.0.0"
    name: "Policy 1"
    description: "First policy"
    verification_method: "test-auditor"
    required_claims:
      - name: "claim1"
        type: "score_binary"
    rules:
      - id: "rule-1"
        description: "Rule 1"
        condition: "True"
        action: "proceed"
        message: "Pass"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                bundle = load_policy_bundle(f.name)
                assert bundle.bundle_id == "bundle-test"
                assert len(bundle.policies) == 1
                assert bundle.policies[0].policy_id == "pol-1"
            finally:
                os.unlink(f.name)

    def test_load_policy_bundle_file_not_found(self):
        """Test that missing file raises PolicyLoadError."""
        with pytest.raises(PolicyLoadError) as exc_info:
            load_policy_bundle("/nonexistent/path/to/bundle.yaml")
        assert "not found" in str(exc_info.value).lower()

    def test_load_policy_bundle_invalid_yaml(self):
        """Test that invalid YAML raises PolicyLoadError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: [")
            f.flush()
            try:
                with pytest.raises(PolicyLoadError):
                    load_policy_bundle(f.name)
            finally:
                os.unlink(f.name)


# =============================================================================
# PolicyResult Model Tests
# =============================================================================


class TestPolicyResultModel:
    """Tests for PolicyResult model."""

    def test_policy_result_valid(self):
        """Test creating valid PolicyResult."""
        result = PolicyResult(valid=True, errors=[])
        assert result.valid is True
        assert result.errors == []

    def test_policy_result_invalid(self):
        """Test creating invalid PolicyResult with errors."""
        result = PolicyResult(
            valid=False,
            errors=["Missing claim", "Low confidence"]
        )
        assert result.valid is False
        assert len(result.errors) == 2


# =============================================================================
# RuleResult Model Tests
# =============================================================================


class TestRuleResultModel:
    """Tests for RuleResult model."""

    def test_rule_result_not_triggered(self):
        """Test RuleResult when rule not triggered."""
        result = RuleResult(rule_id="rule-001", triggered=False)
        assert result.rule_id == "rule-001"
        assert result.triggered is False
        assert result.action is None
        assert result.message is None

    def test_rule_result_triggered(self):
        """Test RuleResult when rule triggered."""
        result = RuleResult(
            rule_id="rule-002",
            triggered=True,
            action="deny",
            message="Access denied"
        )
        assert result.triggered is True
        assert result.action == "deny"
        assert result.message == "Access denied"

    def test_rule_result_with_error(self):
        """Test RuleResult with evaluation error."""
        result = RuleResult(
            rule_id="rule-003",
            triggered=False,
            error="Claim not found: missing.claim"
        )
        assert result.error is not None


# =============================================================================
# PolicyEvaluationResult Model Tests
# =============================================================================


class TestPolicyEvaluationResultModel:
    """Tests for PolicyEvaluationResult model."""

    def test_policy_evaluation_result_success(self):
        """Test creating successful PolicyEvaluationResult."""
        result = PolicyEvaluationResult(
            decision=AuditDecision.PROCEED,
            validation=PolicyResult(valid=True, errors=[]),
            rule_results=[RuleResult(rule_id="rule-001", triggered=False)],
            policy_id="pol-001",
            policy_version="1.0.0"
        )
        assert result.decision == AuditDecision.PROCEED
        assert result.validation.valid is True
        assert len(result.rule_results) == 1

    def test_policy_evaluation_result_deny(self):
        """Test creating PolicyEvaluationResult with DENY decision."""
        result = PolicyEvaluationResult(
            decision=AuditDecision.DENY,
            validation=PolicyResult(valid=False, errors=["Missing claim"]),
            rule_results=[],
            policy_id="pol-002",
            policy_version="1.0.0"
        )
        assert result.decision == AuditDecision.DENY
        assert result.validation.valid is False


# =============================================================================
# find_claim() Tests
# =============================================================================


class TestFindClaim:
    """Tests for find_claim() helper method."""

    def test_find_claim_exists(self, sample_policy, india_claim):
        """Test finding an existing claim."""
        engine = PolicyEngine(sample_policy)
        found = engine.find_claim([india_claim], "location.country")
        assert found is not None
        assert found.name == "location.country"

    def test_find_claim_not_exists(self, sample_policy, india_claim):
        """Test finding a non-existent claim."""
        engine = PolicyEngine(sample_policy)
        found = engine.find_claim([india_claim], "nonexistent.claim")
        assert found is None

    def test_find_claim_empty_list(self, sample_policy):
        """Test finding claim in empty list."""
        engine = PolicyEngine(sample_policy)
        found = engine.find_claim([], "any.claim")
        assert found is None


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for complete policy evaluation workflows."""

    def test_full_workflow_success(self):
        """Test complete workflow from YAML to evaluation."""
        yaml_content = """
schema_version: "1.0.0"
policy_id: "pol-integration"
version: "1.0.0"
name: "Integration Test Policy"
description: "Tests full workflow"
verification_method: "test-auditor"
required_claims:
  - name: "location.verified"
    type: "score_binary"
    required: true
    min_confidence: 0.8
rules:
  - id: "verify-location"
    description: "Verify location claim is true"
    condition: "claims['location.verified'].value == True"
    action: "proceed"
    message: "Location verified"
enforcement: "block"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                # Load policy
                policy = load_policy(f.name)

                # Create engine
                engine = PolicyEngine(policy)

                # Create claim
                claim = Claim(
                    name="location.verified",
                    type=MeasurementType.score_binary,
                    value=True,
                    timestamp=datetime.now(timezone.utc),
                    confidence=0.95
                )

                # Evaluate
                result = engine.evaluate([claim])

                # Assert success
                assert result.decision == AuditDecision.PROCEED
                assert result.validation.valid is True
                assert len(result.rule_results) == 1
                assert result.rule_results[0].triggered is False

            finally:
                os.unlink(f.name)

    def test_full_workflow_denial(self):
        """Test complete workflow resulting in denial."""
        yaml_content = """
schema_version: "1.0.0"
policy_id: "pol-denial"
version: "1.0.0"
name: "Denial Test Policy"
description: "Tests denial workflow"
verification_method: "test-auditor"
required_claims:
  - name: "location.country"
    type: "location_region"
    required: true
rules:
  - id: "require-india"
    description: "Require India location"
    condition: "claims['location.country'].value == 'IN'"
    action: "deny"
    message: "Access denied: Not in India"
enforcement: "block"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            try:
                policy = load_policy(f.name)
                engine = PolicyEngine(policy)

                claim = Claim(
                    name="location.country",
                    type=MeasurementType.location_region,
                    value="US",  # Not India
                    timestamp=datetime.now(timezone.utc),
                    confidence=0.95
                )

                result = engine.evaluate([claim])

                assert result.decision == AuditDecision.DENY
                assert result.rule_results[0].triggered is True
                assert "denied" in engine.get_reason().lower()

            finally:
                os.unlink(f.name)
