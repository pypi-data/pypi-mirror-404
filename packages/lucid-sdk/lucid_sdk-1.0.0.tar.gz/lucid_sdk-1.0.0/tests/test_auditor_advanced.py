import pytest
from unittest.mock import patch
from lucid_sdk import create_chain, Proceed, Deny
from lucid_schemas import AuditDecision
from lucid_sdk.auditor import CompositeAuditor, Auditor
import httpx

class MockAuditor(Auditor):
    def __init__(self, auditor_id, decision=AuditDecision.PROCEED, reason=None):
        super().__init__(auditor_id, verifier_url="http://mock")
        self.decision = decision
        self.reason = reason

    def check_request(self, request, lucid_context=None):
        if self.decision == AuditDecision.DENY:
            return Deny(self.reason)
        return Proceed()

    def check_response(self, response, request=None, lucid_context=None):
        if self.decision == AuditDecision.DENY:
            return Deny(self.reason)
        return Proceed()
    
    def check_execution(self, context, lucid_context=None):
        if self.decision == AuditDecision.DENY:
            return Deny(self.reason)
        return Proceed()
    
    def check_artifact(self, artifact, lucid_context=None):
        if self.decision == AuditDecision.DENY:
            return Deny(self.reason)
        return Proceed()

@patch("lucid_sdk.auditor.LucidClient")
def test_composite_auditor_short_circuit(mock_coco):
    # Setup
    a1 = MockAuditor("a1", AuditDecision.PROCEED)
    a2 = MockAuditor("a2", AuditDecision.DENY, "Blocked")
    a3 = MockAuditor("a3", AuditDecision.PROCEED) # Should not be reached
    
    mock_coco.return_value.get_quote.return_value = "sig"

    chain = CompositeAuditor("chain", [a1, a2, a3])

    # Check Request
    res = chain.check_request({})
    assert res.decision == AuditDecision.DENY
    assert res.reason == "Blocked"
    assert len(chain.get_evidence()) == 2 # a1 and a2 only

    # Check Execution
    res = chain.check_execution({})
    assert res.decision == AuditDecision.DENY
    
    # Check Artifact
    res = chain.check_artifact({})
    assert res.decision == AuditDecision.DENY

    # Check Response
    res = chain.check_response({})
    assert res.decision == AuditDecision.DENY

@patch("lucid_sdk.auditor.LucidClient")
def test_composite_auditor_all_proceed(mock_coco):
    a1 = MockAuditor("a1", AuditDecision.PROCEED)
    a2 = MockAuditor("a2", AuditDecision.PROCEED)
    
    mock_coco.return_value.get_quote.return_value = "sig"

    chain = CompositeAuditor("chain", [a1, a2])

    res = chain.check_request({})
    assert res.decision == AuditDecision.PROCEED
    assert len(chain.get_evidence()) == 2

    res = chain.check_execution({})
    assert res.decision == AuditDecision.PROCEED

    res = chain.check_artifact({})
    assert res.decision == AuditDecision.PROCEED

    res = chain.check_response({})
    assert res.decision == AuditDecision.PROCEED

@patch("lucid_sdk.auditor.LucidClient")
@patch("httpx.Client")
def test_emit_evidence_failure(mock_httpx, mock_coco):
    mock_coco.return_value.get_quote.return_value = "sig"
    
    auditor = MockAuditor("fail_auditor")
    # Simulate network error
    mock_httpx.return_value.__enter__.return_value.post.side_effect = httpx.HTTPError("Network Down")

    # Should log error but not crash
    auditor.emit_evidence("request", Proceed(), {})

def test_create_chain_invalid_id():
    with pytest.raises(ValueError, match="Auditor missing not registered"):
        create_chain("bad_chain", ["missing"])
