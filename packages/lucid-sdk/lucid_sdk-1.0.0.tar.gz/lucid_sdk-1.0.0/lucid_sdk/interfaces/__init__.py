"""Interface definitions for the Lucid SDK.

This module contains abstract base classes (interfaces) that define contracts
for various services, enabling dependency injection and testability.
"""

from .services import (
    IEvidenceService,
    INotarizationService,
    IPassportStore,
)
from .core import (
    AttestationAgent,
    SecurityPolicy,
    ImagePolicy,
)

__all__ = [
    # Service interfaces
    "IEvidenceService",
    "INotarizationService",
    "IPassportStore",
    # Core interfaces (originally from interfaces.py)
    "AttestationAgent",
    "SecurityPolicy",
    "ImagePolicy",
]
