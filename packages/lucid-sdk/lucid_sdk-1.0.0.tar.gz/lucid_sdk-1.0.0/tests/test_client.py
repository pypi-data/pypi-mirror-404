
import pytest
import base64
from unittest.mock import patch, MagicMock
from lucid_sdk.client import LucidClient, VerificationClient

# --- LucidClient Tests ---

def test_lucidclient_init_default():
    """Test default initialization uses MOCK provider."""
    # Simulate environment where TEE_PROVIDER is missing
    def getenv_side_effect(key, default=None):
        return default

    with patch("os.getenv", side_effect=getenv_side_effect):
        client = LucidClient()
        # provider defaults to MOCK if not set
        assert client.provider == "MOCK"
        # agent_url defaults to hardcoded fallback if env vars missing
        assert client.agent_url == "http://127.0.0.1:8006"
        assert client.attestation_enabled is True
        assert client.is_local_dev is True

def test_lucidclient_init_coco_provider():
    """Test initialization with TEE_PROVIDER=COCO."""
    with patch("os.getenv") as mock_env:
        def getenv_side_effect(key, default=None):
            if key == "TEE_PROVIDER": return "COCO"
            if key == "COCO_AA_URL": return "http://coco-agent:8080"
            return default
        mock_env.side_effect = getenv_side_effect
        
        client = LucidClient()
        assert client.provider == "COCO"
        assert client.agent_url == "http://coco-agent:8080"
        assert client.attestation_enabled is True
        assert client.is_local_dev is False

def test_lucidclient_init_none_provider():
    """Test initialization with TEE_PROVIDER=NONE."""
    with patch("os.getenv") as mock_env:
        def getenv_side_effect(key, default=None):
            if key == "TEE_PROVIDER": return "NONE"
            return default
        mock_env.side_effect = getenv_side_effect
        
        client = LucidClient()
        assert client.provider == "NONE"
        assert client.attestation_enabled is False

@patch("lucid_sdk.providers.attestation.requests.post")
def test_get_quote_success(mock_post):
    """Test successful get_quote call in MOCK/COCO mode."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{"quote": "signed-data"}'
    mock_post.return_value = mock_response
    
    client = LucidClient(agent_url="http://agent")
    data = b"test-data"
    result = client.get_quote(data)
    
    assert result == '{"quote": "signed-data"}'
    
    # Verify requests.post called correctly
    expected_runtime_data = base64.b64encode(data).decode('utf-8')
    mock_post.assert_called_once_with(
        "http://agent/aa/evidence",
        json={"runtime_data": expected_runtime_data},
        timeout=10
    )

def test_get_quote_none_provider():
    """Test get_quote returns placeholder when provider is NONE."""
    with patch("os.getenv", return_value="NONE"):
        client = LucidClient()
        result = client.get_quote(b"data")
        assert result == "none:signature-disabled"

@patch("lucid_sdk.providers.attestation.requests.post")
def test_get_quote_failure(mock_post):
    """Test get_quote handling of network errors."""
    client = LucidClient()
    
    # Simulate HTTP error
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = Exception("Server Error")
    mock_post.return_value = mock_response
    
    with pytest.raises(Exception) as exc:
        client.get_quote(b"data")
    assert "Server Error" in str(exc.value)

@patch("lucid_sdk.providers.attestation.requests.get")
def test_get_secret_success(mock_get):
    """Test successful get_secret call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "super-secret-value"
    mock_get.return_value = mock_response
    
    client = LucidClient(agent_url="http://agent")
    secret = client.get_secret("db_password")
    
    assert secret == "super-secret-value"
    mock_get.assert_called_once_with(
        "http://agent/cdh/resource/db_password",
        timeout=10
    )

def test_get_secret_none_provider():
    """Test get_secret returns placeholder when attestation disabled."""
    with patch("os.getenv", return_value="NONE"):
        client = LucidClient()
        secret = client.get_secret("my_key")
        assert secret == "dev_secret_for_my_key"

# --- VerificationClient.verify_evidence Tests ---

@patch("lucid_sdk.client.requests.post")
def test_verify_evidence_success(mock_post):
    """Test successful evidence verification via VerificationClient."""
    from lucid_sdk.client import Evidence
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    evidence = Evidence(data={"some": "evidence"})
    result = VerificationClient().verify_evidence(evidence)

    assert result.verified is True
    mock_post.assert_called_once()
    assert mock_post.call_args[0][0].endswith("/verify")

@patch("lucid_sdk.client.requests.post")
def test_verify_evidence_failure(mock_post):
    """Test failed evidence verification (AS returns non-200)."""
    from lucid_sdk.client import Evidence
    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.text = "Verification failed"
    mock_post.return_value = mock_response

    evidence = Evidence(data={"some": "evidence"})
    result = VerificationClient().verify_evidence(evidence)

    assert result.verified is False


# =============================================================================
# SDK Error Path Coverage Tests
# =============================================================================

class TestSubmitEvidenceFailureScenarios:
    """Tests for submit_evidence / emit_evidence failure scenarios."""

    @patch("lucid_sdk.auditor.LucidClient")
    @patch("httpx.Client")
    def test_emit_evidence_network_timeout(self, mock_httpx_client, mock_lucid_client):
        """Test emit_evidence handles network timeout gracefully."""
        import httpx
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        # Clear registry for clean test
        _registry.clear()

        # Setup mocks
        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # Simulate timeout on HTTP client
        mock_context = MagicMock()
        mock_context.post.side_effect = httpx.TimeoutException("Connection timed out")
        mock_httpx_client.return_value.__enter__.return_value = mock_context

        builder = create_auditor(
            auditor_id="timeout-test",
            verifier_url="http://mock-verifier"
        )

        @builder.on_request
        def handler(data):
            return Proceed("success")

        auditor = builder.build()

        # Should not raise - emit_evidence logs errors but doesn't propagate
        result = auditor.check_request({"prompt": "test", "nonce": "n1"})
        assert result.decision.value == "proceed"

    @patch("lucid_sdk.auditor.LucidClient")
    @patch("httpx.Client")
    def test_emit_evidence_connection_refused(self, mock_httpx_client, mock_lucid_client):
        """Test emit_evidence handles connection refused error."""
        import httpx
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # Simulate connection refused
        mock_context = MagicMock()
        mock_context.post.side_effect = httpx.ConnectError("Connection refused")
        mock_httpx_client.return_value.__enter__.return_value = mock_context

        builder = create_auditor(
            auditor_id="connection-refused-test",
            verifier_url="http://unreachable-verifier"
        )

        @builder.on_request
        def handler(data):
            return Proceed("success")

        auditor = builder.build()

        # Should complete without raising
        result = auditor.check_request({"prompt": "test", "nonce": "n2"})
        assert result.decision.value == "proceed"

    @patch("lucid_sdk.auditor.LucidClient")
    @patch("httpx.Client")
    def test_emit_evidence_http_500_error(self, mock_httpx_client, mock_lucid_client):
        """Test emit_evidence handles HTTP 500 server error."""
        import httpx
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # Simulate HTTP 500 error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Internal Server Error",
            request=MagicMock(),
            response=mock_response
        )

        mock_context = MagicMock()
        mock_context.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_context

        builder = create_auditor(
            auditor_id="http-500-test",
            verifier_url="http://error-verifier"
        )

        @builder.on_request
        def handler(data):
            return Proceed("success")

        auditor = builder.build()

        # Should complete without raising
        result = auditor.check_request({"prompt": "test", "nonce": "n3"})
        assert result.decision.value == "proceed"

    @patch("lucid_sdk.auditor.LucidClient")
    @patch("httpx.Client")
    def test_emit_evidence_http_401_unauthorized(self, mock_httpx_client, mock_lucid_client):
        """Test emit_evidence handles HTTP 401 unauthorized error."""
        import httpx
        from lucid_sdk.auditor import create_auditor, Deny, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # Simulate HTTP 401 error
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        mock_context = MagicMock()
        mock_context.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_context

        builder = create_auditor(
            auditor_id="http-401-test",
            verifier_url="http://auth-verifier"
        )

        @builder.on_request
        def handler(data):
            return Deny("blocked")

        auditor = builder.build()

        # Should complete without raising
        result = auditor.check_request({"prompt": "test", "nonce": "n4"})
        assert result.decision.value == "deny"

    @patch("lucid_sdk.auditor.LucidClient")
    def test_emit_evidence_no_verifier_url(self, mock_lucid_client):
        """Test emit_evidence when no verifier_url is configured."""
        from lucid_sdk.auditor import create_auditor, Proceed, _registry
        import os

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # Ensure LUCID_VERIFIER_URL is not set
        with patch.dict(os.environ, {}, clear=True):
            with patch("os.getenv", return_value=None):
                builder = create_auditor(auditor_id="no-verifier-test")

                @builder.on_request
                def handler(data):
                    return Proceed("success")

                auditor = builder.build()
                auditor.verifier_url = None  # Explicitly ensure no verifier

                # Should complete without errors (emit_evidence skips when no URL)
                result = auditor.check_request({"prompt": "test"})
                assert result.decision.value == "proceed"


class TestMalformedLucidContext:
    """Tests for malformed lucid_context handling."""

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_none(self, mock_lucid_client):
        """Test handler with lucid_context=None."""
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        builder = create_auditor(auditor_id="context-none-test")

        @builder.on_request
        def handler(data, lucid_context):
            # Should receive None and handle gracefully
            if lucid_context is None:
                return Proceed(reason="context-was-none")
            return Proceed()

        auditor = builder.build()
        result = auditor.check_request({"prompt": "test"}, lucid_context=None)
        assert result.reason == "context-was-none"

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_empty_dict(self, mock_lucid_client):
        """Test handler with empty lucid_context dict."""
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        builder = create_auditor(auditor_id="context-empty-test")

        @builder.on_request
        def handler(data, lucid_context):
            if not lucid_context:
                return Proceed(reason="context-was-empty")
            return Proceed()

        auditor = builder.build()
        result = auditor.check_request({"prompt": "test"}, lucid_context={})
        assert result.reason == "context-was-empty"

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_missing_expected_key(self, mock_lucid_client):
        """Test handler accessing missing key in lucid_context."""
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        builder = create_auditor(auditor_id="context-missing-key-test")

        @builder.on_request
        def handler(data, lucid_context):
            # Safely access potentially missing key
            upstream_data = lucid_context.get("upstream-auditor") if lucid_context else None
            if upstream_data is None:
                return Proceed(reason="upstream-not-found")
            return Proceed(reason="found-upstream")

        auditor = builder.build()
        result = auditor.check_request(
            {"prompt": "test"},
            lucid_context={"other-auditor": {"score": 0.5}}
        )
        assert result.reason == "upstream-not-found"

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_with_nested_data(self, mock_lucid_client):
        """Test handler with deeply nested lucid_context data."""
        from lucid_sdk.auditor import create_auditor, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        builder = create_auditor(auditor_id="context-nested-test")

        @builder.on_request
        def handler(data, lucid_context):
            # Access nested data safely
            nested_score = (
                lucid_context
                .get("pii-auditor", {})
                .get("analysis", {})
                .get("score", 0.0)
            )
            return Proceed(reason=f"score:{nested_score}")

        auditor = builder.build()
        result = auditor.check_request(
            {"prompt": "test"},
            lucid_context={
                "pii-auditor": {
                    "analysis": {
                        "score": 0.95,
                        "entities": ["email", "phone"]
                    }
                }
            }
        )
        assert "0.95" in result.reason

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_with_invalid_types(self, mock_lucid_client):
        """Test handler with invalid types in lucid_context."""
        from lucid_sdk.auditor import create_auditor, Proceed, Deny, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        builder = create_auditor(auditor_id="context-invalid-types-test")

        @builder.on_request
        def handler(data, lucid_context):
            # Handle case where auditor data is not a dict
            upstream = lucid_context.get("upstream") if lucid_context else None
            if upstream is not None and not isinstance(upstream, dict):
                return Deny("invalid-upstream-type")
            return Proceed()

        auditor = builder.build()

        # Pass a string instead of dict for an auditor entry
        result = auditor.check_request(
            {"prompt": "test"},
            lucid_context={"upstream": "not-a-dict"}
        )
        assert result.decision.value == "deny"

    @patch("lucid_sdk.auditor.LucidClient")
    def test_lucid_context_chain_dataflow(self, mock_lucid_client):
        """Test proper dataflow through auditor chain with lucid_context."""
        from lucid_sdk.auditor import create_auditor, create_chain, Proceed, _registry

        _registry.clear()

        mock_lucid_instance = mock_lucid_client.return_value
        mock_lucid_instance.get_quote.return_value = "mock-signature"

        # First auditor produces data
        builder1 = create_auditor(auditor_id="producer-auditor")

        @builder1.on_request
        def produce_handler(data):
            return Proceed(data={"produced_value": 42, "status": "ok"})

        builder1.build()

        # Second auditor consumes data
        builder2 = create_auditor(auditor_id="consumer-auditor")

        @builder2.on_request
        def consume_handler(data, lucid_context):
            producer_data = lucid_context.get("producer-auditor", {})
            if producer_data.get("produced_value") == 42:
                return Proceed(reason="consumed-42")
            return Proceed(reason="value-not-found")

        builder2.build()

        chain = create_chain("dataflow-chain", ["producer-auditor", "consumer-auditor"])
        result = chain.check_request({"prompt": "test"})

        assert result.reason == "consumed-42"


class TestGetQuoteErrorPaths:
    """Additional tests for get_quote error scenarios."""

    @patch("lucid_sdk.providers.attestation.requests.post")
    def test_get_quote_invalid_json_response(self, mock_post):
        """Test get_quote with invalid JSON response from attestation agent."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "not-valid-json{{"
        mock_post.return_value = mock_response

        client = LucidClient(agent_url="http://agent")
        # The client returns the raw text, doesn't parse JSON
        result = client.get_quote(b"test-data")
        assert result == "not-valid-json{{"

    @patch("lucid_sdk.providers.attestation.requests.post")
    def test_get_quote_empty_response(self, mock_post):
        """Test get_quote with empty response from attestation agent."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_post.return_value = mock_response

        client = LucidClient(agent_url="http://agent")
        result = client.get_quote(b"test-data")
        assert result == ""

    @patch("lucid_sdk.providers.attestation.requests.post")
    def test_get_quote_large_payload(self, mock_post):
        """Test get_quote with large payload data."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"quote": "large-quote-data"}'
        mock_post.return_value = mock_response

        client = LucidClient(agent_url="http://agent")
        # Test with 1MB of data
        large_data = b"x" * (1024 * 1024)
        result = client.get_quote(large_data)

        assert result == '{"quote": "large-quote-data"}'
        # Verify the large data was base64 encoded
        call_args = mock_post.call_args
        assert "runtime_data" in call_args[1]["json"]


class TestGetSecretErrorPaths:
    """Additional tests for get_secret error scenarios."""

    @patch("lucid_sdk.providers.attestation.requests.get")
    def test_get_secret_http_404(self, mock_get):
        """Test get_secret with HTTP 404 not found."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value = mock_response

        client = LucidClient(agent_url="http://agent")

        with pytest.raises(Exception) as exc:
            client.get_secret("nonexistent_key")
        assert "Not Found" in str(exc.value)

    @patch("lucid_sdk.providers.attestation.requests.get")
    def test_get_secret_http_403_forbidden(self, mock_get):
        """Test get_secret with HTTP 403 forbidden."""
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.raise_for_status.side_effect = Exception("Forbidden")
        mock_get.return_value = mock_response

        client = LucidClient(agent_url="http://agent")

        with pytest.raises(Exception) as exc:
            client.get_secret("restricted_key")
        assert "Forbidden" in str(exc.value)

    @patch("lucid_sdk.providers.attestation.requests.get")
    def test_get_secret_network_error(self, mock_get):
        """Test get_secret with network connectivity error."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        client = LucidClient(agent_url="http://unreachable-agent")

        with pytest.raises(requests.exceptions.ConnectionError):
            client.get_secret("some_key")

    @patch("lucid_sdk.providers.attestation.requests.get")
    def test_get_secret_timeout(self, mock_get):
        """Test get_secret with request timeout."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        client = LucidClient(agent_url="http://slow-agent")

        with pytest.raises(requests.exceptions.Timeout):
            client.get_secret("some_key")

    @patch("lucid_sdk.providers.attestation.requests.get")
    def test_get_secret_special_chars_in_key(self, mock_get):
        """Test get_secret with special characters in key name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "secret-value"
        mock_get.return_value = mock_response

        client = LucidClient(agent_url="http://agent")
        secret = client.get_secret("my/special-key_123")

        assert secret == "secret-value"
        # Verify URL construction
        mock_get.assert_called_once_with(
            "http://agent/cdh/resource/my/special-key_123",
            timeout=10
        )


class TestVerifyEvidenceErrorPaths:
    """Additional tests for VerificationClient.verify_evidence error scenarios."""

    @patch("lucid_sdk.client.requests.post")
    def test_verify_evidence_network_error(self, mock_post):
        """Test verify_evidence with network error."""
        import requests
        from lucid_sdk.client import Evidence

        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")

        evidence = Evidence(data={"quote": "test"})
        with pytest.raises(requests.exceptions.ConnectionError):
            VerificationClient().verify_evidence(evidence)

    @patch("lucid_sdk.client.requests.post")
    def test_verify_evidence_timeout(self, mock_post):
        """Test verify_evidence with timeout."""
        import requests
        from lucid_sdk.client import Evidence

        mock_post.side_effect = requests.exceptions.Timeout("Verification timed out")

        evidence = Evidence(data={"quote": "test"})
        with pytest.raises(requests.exceptions.Timeout):
            VerificationClient().verify_evidence(evidence)

    def test_verify_evidence_with_empty_data(self):
        """Test verify_evidence with empty evidence data returns False."""
        from lucid_sdk.client import Evidence

        evidence = Evidence(data={})
        result = VerificationClient().verify_evidence(evidence)

        # Empty evidence data is rejected by the client
        assert result.verified is False
        assert result.message == "Missing evidence"

    @patch("lucid_sdk.client.requests.post")
    def test_verify_evidence_server_error_500(self, mock_post):
        """Test verify_evidence with HTTP 500 error."""
        from lucid_sdk.client import Evidence
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        evidence = Evidence(data={"quote": "test"})
        result = VerificationClient().verify_evidence(evidence)

        assert result.verified is False
