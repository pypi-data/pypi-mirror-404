import os
import json
import pytest
from unittest.mock import MagicMock, patch

# Mock the LucidClient before imports that use it
with patch("lucid_sdk.auditor.LucidClient") as mock_client:
    from lucid_sdk.auditor import create_auditor, create_chain, Proceed, AuditDecision, _registry
    from lucid_schemas import AuditDecision as SchemaAuditDecision

@pytest.fixture(autouse=True)
def mock_sdk_tee(monkeypatch):
    """Ensure every test has a mocked TEE client."""
    with patch("lucid_sdk.auditor.LucidClient") as mock:
        mock_instance = mock.return_value
        mock_instance.get_quote.return_value = "mock-signature"
        yield mock_instance

def test_auditor_config_loading(monkeypatch):
    """Verify that auditors correctly load unique configuration from the environment."""
    config_data = {"threshold": 0.5, "mode": "strict"}
    monkeypatch.setenv("LUCID_AUDITOR_CONFIG", json.dumps(config_data))
    
    builder = create_auditor(auditor_id="config-test")
    auditor = builder.build()
    
    assert auditor.config == config_data

def test_handler_intelligent_injection():
    """Verify that handlers can optionally request 'config' and 'lucid_context'."""
    builder = create_auditor(auditor_id="injection-test")
    
    # Handler with no extra args
    @builder.on_request
    def simple_handler(data):
        return Proceed(received=True)
    
    # Handler with config
    @builder.on_request
    def config_handler(data, config):
        return Proceed(has_config=True, threshold=config.get("threshold"))

    # Handler with context
    @builder.on_request
    def context_handler(data, lucid_context):
        return Proceed(prev_data=lucid_context.get("prev_node"))

    auditor = builder.build()
    auditor.config = {"threshold": 0.5}
    
    # Task: Check request runs all handlers
    ctx = {"prev_node": "some-data"}
    result = auditor.check_request({"input": "test"}, lucid_context=ctx)
    
    assert result.decision == SchemaAuditDecision.PROCEED
    # Note: In FunctionAuditor, handlers run sequentially, 
    # and the last one to return a non-PROCEED or the last one wins if all are PROCEED.
    # Actually, FunctionAuditor.check_request runs all and returns the last PROCEED 
    # unless one DENYs.

def test_composite_auditor_dataflow():
    """Verify that data is passed from one auditor to the next in a chain."""
    _registry.clear()
    
    # Auditor 1: Produces data
    b1 = create_auditor(auditor_id="node1")
    @b1.on_request
    def handler1(data):
        return Proceed(data={"shared_key": "secret-value"})
    b1.build()
    
    # Auditor 2: Consumes data
    b2 = create_auditor(auditor_id="node2")
    @b2.on_request
    def handler2(data, lucid_context):
        print(f"DEBUG: lucid_context = {lucid_context}")
        prev_val = lucid_context.get("node1", {}).get("shared_key")
        if prev_val == "secret-value":
            return Proceed(reason="verified-dataflow")
        return Proceed(reason="broken-dataflow")
    b2.build()
    
    chain = create_chain("test-chain", ["node1", "node2"])
    result = chain.check_request({"q": "test"})
    
    assert result.decision == SchemaAuditDecision.PROCEED
    assert result.reason == "verified-dataflow"
