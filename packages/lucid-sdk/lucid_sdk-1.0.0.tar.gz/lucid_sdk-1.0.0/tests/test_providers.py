from unittest.mock import patch, MagicMock
from lucid_sdk.providers.attestation import CoCoAttestationAgent, MockAttestationAgent, NoAttestationAgent

@patch("lucid_sdk.providers.attestation.requests.get")
@patch("lucid_sdk.providers.attestation.requests.post")
def test_coco_attestation_agent(mock_post, mock_get):
    """Test CoCoAttestationAgent communication."""
    agent = CoCoAttestationAgent(agent_url="http://coco-agent")
    
    # Mock evidence
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "evidence-data"
    mock_post.return_value = mock_resp
    
    assert agent.get_evidence(b"runtime-data") == "evidence-data"
    mock_post.assert_called_with(
        "http://coco-agent/aa/evidence",
        json={"runtime_data": "cnVudGltZS1kYXRh"}, # base64 of b"runtime-data"
        timeout=10
    )
    
    # Mock secret
    mock_resp.text = "secret-value"
    mock_get.return_value = mock_resp
    assert agent.get_secret("path/to/secret") == "secret-value"
    mock_get.assert_called_with(
        "http://coco-agent/cdh/resource/path/to/secret",
        timeout=10
    )

@patch("lucid_sdk.providers.attestation.requests.get")
@patch("lucid_sdk.providers.attestation.requests.post")
def test_mock_attestation_agent(mock_post, mock_get):
    """Test MockAttestationAgent communication."""
    agent = MockAttestationAgent(agent_url="http://mock-agent")
    
    # Mock evidence
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "mock-evidence"
    mock_post.return_value = mock_resp
    
    assert agent.get_evidence(b"data") == "mock-evidence"
    
    # Mock secret
    mock_resp.text = "mock-secret"
    mock_get.return_value = mock_resp
    assert agent.get_secret("my-secret") == "mock-secret"

def test_no_attestation_agent():
    """Test NoAttestationAgent provides placeholders."""
    agent = NoAttestationAgent()
    assert agent.get_evidence(b"any") == "none:signature-disabled"
    assert agent.get_secret("any") == "dev_secret_for_any"
    assert agent.attestation_enabled is False
