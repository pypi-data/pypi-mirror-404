import base64
import requests
import structlog
from ..interfaces import AttestationAgent

logger = structlog.get_logger()

class CoCoAttestationAgent(AttestationAgent):
    def __init__(self, agent_url: str):
        self.agent_url = agent_url

    def get_evidence(self, data: bytes) -> str:
        runtime_data = base64.b64encode(data).decode('utf-8')
        url = f"{self.agent_url}/aa/evidence"
        
        # Use POST for large payloads to avoid URI length limits & connection resets
        response = requests.post(url, json={"runtime_data": runtime_data}, timeout=10)
        response.raise_for_status()
        return response.text

    def get_secret(self, resource_path: str) -> str:
        url = f"{self.agent_url}/cdh/resource/{resource_path}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    @property
    def attestation_enabled(self) -> bool:
        return True


class MockAttestationAgent(AttestationAgent):
    def __init__(self, agent_url: str):
        self.agent_url = agent_url

    def get_evidence(self, data: bytes) -> str:
        # Mock agent still calls a sidecar, but it's the mock-aa
        runtime_data = base64.b64encode(data).decode('utf-8')
        url = f"{self.agent_url}/aa/evidence"
        
        # Use POST for large payloads to avoid URI length limits & connection resets
        response = requests.post(url, json={"runtime_data": runtime_data}, timeout=10)
        response.raise_for_status()
        return response.text

    def get_secret(self, resource_path: str) -> str:
        # In mock mode, we still call the mock-cdh (running in the same agent)
        url = f"{self.agent_url}/cdh/resource/{resource_path}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    @property
    def attestation_enabled(self) -> bool:
        return True


class NoAttestationAgent(AttestationAgent):
    def get_evidence(self, data: bytes) -> str:
        return "none:signature-disabled"

    def get_secret(self, resource_path: str) -> str:
        return f"dev_secret_for_{resource_path}"

    @property
    def attestation_enabled(self) -> bool:
        return False
