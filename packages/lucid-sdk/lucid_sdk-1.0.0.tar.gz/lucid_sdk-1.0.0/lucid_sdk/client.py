"""
Lucid SDK Client Module

This module provides a refactored client architecture following single-responsibility principles.
The monolithic LucidClient has been decomposed into focused client classes:

- AttestationClient: TEE attestation operations (quotes, secrets)
- VerificationClient: Evidence verification against attestation service
- PolicyClient: Security and image policy retrieval
- NotarizationClient: Image notarization checks

The LucidClient class serves as a facade providing backward-compatible access
to all functionality while delegating to specialized clients.
"""

import os
import structlog
import json
import requests
from typing import Optional, Dict, Any
from dataclasses import dataclass
from .policies import get_tee_provider, get_security_policy, get_image_policy, TEE_PROVIDER
from .providers.attestation import (
    CoCoAttestationAgent,
    MockAttestationAgent,
    NoAttestationAgent
)
from .interfaces import AttestationAgent, SecurityPolicy, ImagePolicy

logger = structlog.get_logger()

# --- Configuration ---
SDK_HTTP_TIMEOUT = float(os.getenv("SDK_HTTP_TIMEOUT", "15"))


# --- Data Classes ---

@dataclass
class Quote:
    """Represents a cryptographic quote/signature from the attestation agent."""
    raw: str
    runtime_data: Optional[bytes] = None

    def __str__(self) -> str:
        return self.raw


@dataclass
class Evidence:
    """Represents attestation evidence for verification."""
    data: Dict[str, Any]

    def to_json(self) -> str:
        return json.dumps(self.data)

    @classmethod
    def from_json(cls, json_str: str) -> "Evidence":
        return cls(data=json.loads(json_str))


@dataclass
class VerificationResult:
    """Result of evidence verification."""
    verified: bool
    status_code: Optional[int] = None
    message: Optional[str] = None


@dataclass
class NotarizationResult:
    """Result of image notarization check."""
    notarized: bool
    digest: str
    message: Optional[str] = None


# --- Specialized Client Classes ---

class AttestationClient:
    """Client for TEE attestation operations.

    Handles all interactions with the Attestation Agent, including:
    - Requesting cryptographic quotes/evidence
    - Retrieving secrets from the Confidential Data Hub (CDH)

    Attributes:
        base_url: URL of the attestation agent service.
        provider: The active TEE provider (COCO, MOCK, or NONE).
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        provider: Optional[str] = None
    ):
        """Initialize the attestation client.

        Args:
            base_url: URL of the attestation agent. If not provided, uses
                     environment variables (AA_URL, MOCK_AA_URL, COCO_AA_URL)
                     or defaults to http://127.0.0.1:8006.
            provider: TEE provider override. If not provided, uses TEE_PROVIDER
                     environment variable or defaults to MOCK.
        """
        self._provider = provider or get_tee_provider(default=TEE_PROVIDER.MOCK)
        self.base_url = base_url or os.getenv("AA_URL") or os.getenv("MOCK_AA_URL") or os.getenv("COCO_AA_URL") or "http://127.0.0.1:8006"

        if self._provider == TEE_PROVIDER.COCO:
            self._agent: AttestationAgent = CoCoAttestationAgent(self.base_url)
        elif self._provider == TEE_PROVIDER.MOCK:
            self._agent = MockAttestationAgent(self.base_url)
        else:
            self._agent = NoAttestationAgent()

    @property
    def provider(self) -> str:
        """Returns the active TEE Provider string (COCO, MOCK, or NONE)."""
        return self._provider

    @property
    def attestation_enabled(self) -> bool:
        """Returns True if attestation is active (COCO or MOCK mode)."""
        return self._agent.attestation_enabled

    @property
    def is_local_dev(self) -> bool:
        """Returns True if running in local development mode (MOCK)."""
        return self._provider == TEE_PROVIDER.MOCK

    def get_quote(self, data: bytes) -> Quote:
        """Request a cryptographic quote/signature from the Attestation Agent.

        Args:
            data: The data to be signed/quoted by the TEE.

        Returns:
            Quote object containing the cryptographic evidence.
        """
        raw = self._agent.get_evidence(data)
        return Quote(raw=raw, runtime_data=data)

    def get_evidence(self, data: bytes) -> str:
        """Request raw evidence string from the Attestation Agent.

        This is the lower-level API that returns the raw string response.
        For structured access, use get_quote() instead.

        Args:
            data: The data to be signed/quoted by the TEE.

        Returns:
            Raw evidence string from the attestation agent.
        """
        return self._agent.get_evidence(data)

    def get_secret(self, resource_path: str) -> str:
        """Request a secret from the Confidential Data Hub (CDH).

        Args:
            resource_path: Path to the secret resource.

        Returns:
            The secret value as a string.
        """
        return self._agent.get_secret(resource_path)


class VerificationClient:
    """Client for evidence verification operations.

    Handles verification of attestation evidence against the
    Attestation Service (AS).

    Attributes:
        verifier_url: URL of the verification/attestation service.
    """

    def __init__(
        self,
        verifier_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """Initialize the verification client.

        Args:
            verifier_url: URL of the attestation service. If not provided,
                         uses environment variables (AS_URL, COCO_AS_URL, MOCK_AS_URL)
                         or defaults to http://127.0.0.1:8007.
            timeout: HTTP request timeout in seconds. Defaults to SDK_HTTP_TIMEOUT.
        """
        self.verifier_url = verifier_url or os.getenv("AS_URL") or os.getenv("COCO_AS_URL") or os.getenv("MOCK_AS_URL") or "http://127.0.0.1:8007"
        self.timeout = timeout or SDK_HTTP_TIMEOUT

    def verify_evidence(self, evidence: Evidence) -> VerificationResult:
        """Verify attestation evidence.

        Args:
            evidence: Evidence object containing the attestation data.

        Returns:
            VerificationResult indicating whether verification succeeded.
        """
        provider = get_tee_provider()

        if provider == TEE_PROVIDER.NONE:
            logger.info("verification_skipped_attestation_disabled")
            return VerificationResult(verified=True, message="Attestation disabled")

        if not evidence or not evidence.data:
            logger.warning("verification_failed_missing_evidence")
            return VerificationResult(verified=False, message="Missing evidence")

        response = requests.post(
            f"{self.verifier_url}/verify",
            json=evidence.data,
            timeout=self.timeout
        )

        if response.status_code == 200:
            return VerificationResult(verified=True, status_code=200)
        else:
            logger.warning(
                "attestation_service_error",
                status=response.status_code,
                text=response.text
            )
            return VerificationResult(
                verified=False,
                status_code=response.status_code,
                message=response.text
            )

class PolicyClient:
    """Client for policy retrieval operations.

    Provides access to security and image deployment policies
    based on the current environment configuration.
    """

    def __init__(self, provider: Optional[str] = None):
        """Initialize the policy client.

        Args:
            provider: TEE provider override. If not provided, uses
                     the TEE_PROVIDER environment variable.
        """
        self._provider = provider

    def get_image_policy(self) -> ImagePolicy:
        """Get the current image deployment policy.

        Returns:
            ImagePolicy based on the current TEE provider setting.
        """
        if self._provider:
            return get_image_policy(default=self._provider)
        return get_image_policy()

    def get_security_policy(self) -> SecurityPolicy:
        """Get the current security policy.

        Returns:
            SecurityPolicy for the current environment.
        """
        if self._provider:
            return get_security_policy(default=self._provider)
        return get_security_policy()

    @property
    def tee_provider(self) -> str:
        """Get the current TEE provider setting."""
        return self._provider or get_tee_provider()


class NotarizationClient:
    """Client for image notarization operations.

    Handles checking whether container images are properly notarized
    and authorized for deployment.

    Attributes:
        verifier_url: URL of the verifier service that handles notarization checks.
    """

    def __init__(
        self,
        verifier_url: Optional[str] = None,
        timeout: Optional[float] = None
    ):
        """Initialize the notarization client.

        Args:
            verifier_url: URL of the verifier service. If not provided,
                         uses LUCID_VERIFIER_URL environment variable
                         or defaults to http://127.0.0.1:8080.
            timeout: HTTP request timeout in seconds. Defaults to SDK_HTTP_TIMEOUT.
        """
        self.verifier_url = verifier_url or os.getenv("LUCID_VERIFIER_URL") or "http://127.0.0.1:8080"
        self.timeout = timeout or SDK_HTTP_TIMEOUT

    def check_notarization(self, digest: str) -> NotarizationResult:
        """Check if an image digest is notarized.

        Args:
            digest: The container image digest to check (e.g., sha256:abc123...).

        Returns:
            NotarizationResult indicating whether the image is notarized.
        """
        try:
            response = requests.get(
                f"{self.verifier_url}/notarization/{digest}",
                timeout=self.timeout
            )

            if response.status_code == 200:
                return NotarizationResult(
                    notarized=True,
                    digest=digest,
                    message="Image is notarized"
                )
            elif response.status_code == 404:
                return NotarizationResult(
                    notarized=False,
                    digest=digest,
                    message="Image not found in notarization registry"
                )
            else:
                logger.warning(
                    "notarization_check_error",
                    status=response.status_code,
                    digest=digest
                )
                return NotarizationResult(
                    notarized=False,
                    digest=digest,
                    message=f"Notarization check failed: {response.status_code}"
                )
        except requests.RequestException as e:
            logger.error("notarization_check_failed", error=str(e), digest=digest)
            return NotarizationResult(
                notarized=False,
                digest=digest,
                message=f"Notarization check error: {str(e)}"
            )

    def is_notarized(self, digest: str) -> bool:
        """Simple check if an image is notarized.

        Args:
            digest: The container image digest to check.

        Returns:
            True if notarized, False otherwise.
        """
        result = self.check_notarization(digest)
        return result.notarized


# --- Facade Class ---

class LucidClient:
    """Unified client for Trusted Execution Environment (TEE) operations.

    This client serves as a facade providing access to all Lucid SDK functionality.
    It composes specialized clients for different responsibilities:

    - attestation: TEE attestation operations (quotes, secrets)
    - verification: Evidence verification
    - policy: Security and image policy retrieval
    - notarization: Image notarization checks

    Supported TEE Providers:
    - **MOCK**: Simulates TEE signing using a sidecar Mock Attestation Agent.
    - **COCO**: Connects to the Confidential Containers Attestation Agent (Prod).
    - **NONE**: Disables all cryptographic operations (Observability-only).
    """

    def __init__(
        self,
        agent_url: Optional[str] = None,
        verifier_url: Optional[str] = None
    ):
        """Initialize the Lucid client.

        Args:
            agent_url: URL of the attestation agent. Passed to AttestationClient.
            verifier_url: URL of the verification service. Passed to VerificationClient
                         and NotarizationClient.
        """
        # Initialize specialized clients
        self.attestation = AttestationClient(base_url=agent_url)
        self.verification = VerificationClient(verifier_url=verifier_url)
        self.policy = PolicyClient()
        self.notarization = NotarizationClient(verifier_url=verifier_url)

        self.agent_url = self.attestation.base_url
        self._agent = self.attestation._agent

    @property
    def provider(self) -> str:
        """Returns the active TEE Provider string (COCO, MOCK, or NONE)."""
        return get_tee_provider(default=TEE_PROVIDER.MOCK)

    @property
    def attestation_enabled(self) -> bool:
        """Returns True if attestation is active (COCO or MOCK mode)."""
        return self.attestation.attestation_enabled

    @property
    def is_local_dev(self) -> bool:
        """Returns True if running in local development mode (MOCK)."""
        return get_tee_provider(default=TEE_PROVIDER.MOCK) == TEE_PROVIDER.MOCK

    def get_quote(self, data: bytes) -> str:
        """Request a cryptographic quote/signature from the Attestation Agent.

        Args:
            data: The data to be signed/quoted by the TEE.

        Returns:
            Raw evidence string from the attestation agent.
        """
        return self.attestation.get_evidence(data)

    def get_secret(self, resource_path: str) -> str:
        """Request a secret from the Confidential Data Hub (CDH).

        Args:
            resource_path: Path to the secret resource.

        Returns:
            The secret value as a string.
        """
        return self.attestation.get_secret(resource_path)
