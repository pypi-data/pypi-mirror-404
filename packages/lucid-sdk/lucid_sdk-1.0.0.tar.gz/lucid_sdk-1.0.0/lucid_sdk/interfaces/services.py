"""Service layer interfaces for the verifier to enable dependency injection and testability."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class IEvidenceService(ABC):
    """Interface for evidence handling."""

    @abstractmethod
    async def submit_evidence(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Submit evidence and create passport.

        Args:
            evidence: Dictionary containing evidence data to submit.

        Returns:
            Dictionary containing the created passport information.
        """
        pass

    @abstractmethod
    async def verify_evidence(self, evidence_id: str) -> bool:
        """Verify evidence integrity.

        Args:
            evidence_id: The unique identifier of the evidence to verify.

        Returns:
            True if the evidence is valid, False otherwise.
        """
        pass

    @abstractmethod
    async def get_evidence(self, evidence_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve evidence by ID.

        Args:
            evidence_id: The unique identifier of the evidence to retrieve.

        Returns:
            Dictionary containing the evidence data, or None if not found.
        """
        pass


class INotarizationService(ABC):
    """Interface for notarization."""

    @abstractmethod
    async def notarize(self, data: Dict[str, Any]) -> str:
        """Create notarization for data.

        Args:
            data: Dictionary containing data to notarize.

        Returns:
            The notarization ID as a string.
        """
        pass

    @abstractmethod
    async def verify_notarization(self, notarization_id: str) -> bool:
        """Verify a notarization.

        Args:
            notarization_id: The unique identifier of the notarization to verify.

        Returns:
            True if the notarization is valid, False otherwise.
        """
        pass


class IPassportStore(ABC):
    """Interface for passport storage."""

    @abstractmethod
    async def store(self, passport_id: str, passport: Dict[str, Any]) -> None:
        """Store passport.

        Args:
            passport_id: The unique identifier for the passport.
            passport: Dictionary containing the passport data to store.
        """
        pass

    @abstractmethod
    async def retrieve(self, passport_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve passport by ID.

        Args:
            passport_id: The unique identifier of the passport to retrieve.

        Returns:
            Dictionary containing the passport data, or None if not found.
        """
        pass

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """List passports with pagination.

        Args:
            skip: Number of records to skip (for pagination). Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            List of dictionaries containing passport data.
        """
        pass
