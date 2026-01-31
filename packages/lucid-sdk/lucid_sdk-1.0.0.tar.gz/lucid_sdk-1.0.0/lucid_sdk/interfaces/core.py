"""Core interface definitions for TEE attestation, security, and image policies.

These interfaces define contracts for interacting with Trusted Execution
Environment (TEE) components and deployment policies.
"""

from abc import ABC, abstractmethod


class AttestationAgent(ABC):
    """Interface for TEE Attestation Agent operations."""

    @abstractmethod
    def get_evidence(self, data: bytes) -> str:
        """Get cryptographic evidence/quote for the given data."""
        pass

    @abstractmethod
    def get_secret(self, resource_path: str) -> str:
        """Retrieve a secret from the Confidential Data Hub."""
        pass

    @property
    @abstractmethod
    def attestation_enabled(self) -> bool:
        """Return True if attestation is active."""
        pass


class SecurityPolicy(ABC):
    """Interface for application security policies."""

    @property
    @abstractmethod
    def api_key_required(self) -> bool:
        """Return True if API key verification is mandatory."""
        pass

    @property
    @abstractmethod
    def tls_required(self) -> bool:
        """Return True if TLS is mandatory for the service."""
        pass

    @abstractmethod
    def get_jwt_secret(self) -> str:
        """Retrieve the JWT signing secret."""
        pass

    @abstractmethod
    def get_reset_secret(self) -> str:
        """Retrieve the secret for reset password tokens."""
        pass

    @abstractmethod
    def get_verify_secret(self) -> str:
        """Retrieve the secret for verification tokens."""
        pass


class ImagePolicy(ABC):
    """Interface for container image deployment policies."""

    @property
    @abstractmethod
    def pull_policy(self) -> str:
        """Return K8s imagePullPolicy (e.g., 'Always', 'IfNotPresent')."""
        pass

    @property
    @abstractmethod
    def inject_mock_sidecars(self) -> bool:
        """Return True if mock attestation sidecars should be injected."""
        pass

    @property
    @abstractmethod
    def strict_notarization(self) -> bool:
        """Return True if images must have digests for notarization."""
        pass
