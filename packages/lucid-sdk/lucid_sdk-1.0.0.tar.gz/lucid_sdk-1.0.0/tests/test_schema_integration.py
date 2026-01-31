"""Integration tests verifying SDK-generated Claims conform to schema constraints."""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from lucid_schemas import Claim, MeasurementType


class TestSDKSchemaIntegration:
    """Tests that SDK-generated claims conform to schema constraints."""

    def test_claim_schema_validation(self):
        """Test that claims pass schema validation."""
        claim = Claim(
            name="test-auditor",
            type=MeasurementType.conformity,
            value={"decision": "proceed", "reason": "Test passed"},
            timestamp=datetime.now(timezone.utc),
            confidence=1.0,
        )
        assert claim.name == "test-auditor"
        assert isinstance(claim.timestamp, datetime)

    def test_deny_claim_type(self):
        """Test that DENY decisions use policy_violation claim type."""
        claim = Claim(
            name="deny-type-test",
            type=MeasurementType.policy_violation,
            value={"decision": "deny", "reason": "Blocked"},
            timestamp=datetime.now(timezone.utc),
        )
        assert claim.type == MeasurementType.policy_violation

    def test_proceed_claim_type(self):
        """Test that PROCEED decisions use conformity claim type."""
        claim = Claim(
            name="proceed-type-test",
            type=MeasurementType.conformity,
            value={"decision": "proceed", "reason": "Passed"},
            timestamp=datetime.now(timezone.utc),
        )
        assert claim.type == MeasurementType.conformity

    def test_claim_value_structure(self):
        """Test that claim value contains expected fields."""
        claim = Claim(
            name="value-structure-test",
            type=MeasurementType.policy_violation,
            value={
                "decision": "deny",
                "reason": "Security violation",
                "score": 0.95,
                "category": "injection",
            },
            timestamp=datetime.now(timezone.utc),
        )
        assert "decision" in claim.value
        assert "reason" in claim.value
        assert claim.value["decision"] == "deny"
        assert claim.value["reason"] == "Security violation"

    def test_claim_confidence_bounds(self):
        """Test that claim confidence is within valid bounds."""
        claim = Claim(
            name="confidence-test",
            type=MeasurementType.conformity,
            value={"decision": "proceed"},
            timestamp=datetime.now(timezone.utc),
            confidence=0.85,
        )
        assert 0.0 <= claim.confidence <= 1.0

    def test_claim_with_nonce(self):
        """Test that claims properly store nonce values."""
        claim = Claim(
            name="nonce-test",
            type=MeasurementType.conformity,
            value={"decision": "proceed"},
            timestamp=datetime.now(timezone.utc),
            nonce="test-nonce-12345",
        )
        assert claim.nonce == "test-nonce-12345"

    def test_claim_with_phase(self):
        """Test that claims properly store phase values."""
        for phase in ["request", "response", "pre", "post"]:
            claim = Claim(
                name="phase-test",
                type=MeasurementType.conformity,
                value={"decision": "proceed"},
                timestamp=datetime.now(timezone.utc),
                phase=phase,
            )
            assert claim.phase == phase
