"""Base classes for versioned schemas.

This module provides base classes and utilities for schema versioning.
All top-level schemas should inherit from VersionedSchema to ensure
consistent version tracking and validation.
"""
from __future__ import annotations

import logging
from typing import ClassVar

from pydantic import BaseModel, Field, field_validator

from .constants import SCHEMA_VERSION_DEFAULT

logger = logging.getLogger(__name__)


class VersionedSchema(BaseModel):
    """Base class for versioned schemas.

    All top-level schemas should inherit from this class to ensure
    consistent version tracking and backward compatibility.

    The schema_version field follows Semantic Versioning (SemVer):
    - MAJOR: Breaking changes (incompatible API changes)
    - MINOR: Backwards-compatible new features
    - PATCH: Backwards-compatible bug fixes

    Subclasses should set _expected_version as a ClassVar to specify
    the current expected version for validation warnings.

    Example:
        class MySchema(VersionedSchema):
            _expected_version: ClassVar[str] = "2.0.0"
            # ... other fields
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_DEFAULT

    schema_version: str = Field(
        default=SCHEMA_VERSION_DEFAULT,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0", "1.0.0-beta"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )

    @field_validator('schema_version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate schema version and log warnings for mismatches.

        This validator checks if the provided schema version matches
        the expected version for the class. Mismatches are logged as
        warnings to help identify potential compatibility issues.

        Args:
            v: The schema version string to validate.

        Returns:
            The validated schema version string.
        """
        expected = getattr(cls, '_expected_version', SCHEMA_VERSION_DEFAULT)
        if v != expected:
            logger.warning(
                "Schema version mismatch for %s: got '%s', expected '%s'. "
                "This may indicate a compatibility issue.",
                cls.__name__,
                v,
                expected
            )
        return v

    class Config:
        # Include version in serialization
        json_schema_extra = {"required": ["schema_version"]}


def validate_schema_version(
    version: str,
    expected: str,
    schema_name: str = "Unknown"
) -> bool:
    """Utility function to validate schema versions.

    This can be used for validating versions in contexts where
    the VersionedSchema base class is not used.

    Args:
        version: The actual schema version.
        expected: The expected schema version.
        schema_name: Name of the schema for logging purposes.

    Returns:
        True if versions match, False otherwise.
    """
    if version != expected:
        logger.warning(
            "Schema version mismatch for %s: got '%s', expected '%s'",
            schema_name,
            version,
            expected
        )
        return False
    return True
