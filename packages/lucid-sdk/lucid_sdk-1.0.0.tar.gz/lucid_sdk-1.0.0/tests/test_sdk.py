from unittest.mock import patch
from lucid_sdk import create_auditor, Proceed, Deny, Redact
from lucid_schemas import AuditDecision

@patch("lucid_sdk.auditor.LucidClient")
@patch("httpx.Client")
def test_on_request_decorator(mock_httpx, mock_coco):
    # Mock TEE signing
    mock_coco_instance = mock_coco.return_value
    mock_coco_instance.get_quote.return_value = "mock-signature"
    
    # Create auditor with a verifier_url so it tries to send evidence
    builder = create_auditor(auditor_id="test-auditor", verifier_url="http://mock-verifier")
    
    @builder.on_request
    def filter_secret(data):
        if "secret" in data.get("prompt", ""):
            return Deny("Secret found")
        return Proceed("Clean")
    
    auditor = builder.build()
    
    # 1. Success Case
    result = auditor.check_request({"prompt": "hello", "nonce": "nonce-1"})
    assert result.decision == AuditDecision.PROCEED
    
    # Verify evidence emission
    assert mock_httpx.return_value.__enter__.return_value.post.called
    
    # 2. Deny Case
    result_deny = auditor.check_request({"prompt": "my secret", "nonce": "nonce-2"})
    assert result_deny.decision == AuditDecision.DENY
    assert result_deny.reason == "Secret found"

@patch("lucid_sdk.auditor.LucidClient")
@patch("httpx.Client")
def test_on_response_redact(mock_httpx, mock_coco):
    mock_coco_instance = mock_coco.return_value
    mock_coco_instance.get_quote.return_value = "mock-signature"

    builder = create_auditor(auditor_id="redactor")
    
    @builder.on_response
    def redact_pii(response):
        content = response.get("content", "")
        if "sensitive" in content:
            return Redact(modifications={"content": "[REDACTED]"}, reason="PII found")
        return Proceed()
    
    auditor = builder.build()
    
    result = auditor.check_response({"content": "sensitive info"})
    assert result.decision == AuditDecision.REDACT
    assert result.modifications == {"content": "[REDACTED]"}

@patch("lucid_sdk.auditor.LucidClient")
@patch("httpx.Client")
def test_auditor_chain(mock_httpx, mock_coco):
    mock_coco_instance = mock_coco.return_value
    mock_coco_instance.get_quote.return_value = "mock-signature"

    from lucid_sdk import create_chain

    # Register two auditors
    b1 = create_auditor("a1")
    @b1.on_request
    def check1(d): return Proceed()
    b1.build()
    
    b2 = create_auditor("a2")
    @b2.on_request
    def check2(d): return Deny("Blocked by a2")
    b2.build()
    
    chain = create_chain("test-chain", ["a1", "a2"])
    
    result = chain.check_request({"prompt": "test"})
    assert result.decision == AuditDecision.DENY
    assert result.reason == "Blocked by a2"
    assert len(chain.get_evidence()) == 2
