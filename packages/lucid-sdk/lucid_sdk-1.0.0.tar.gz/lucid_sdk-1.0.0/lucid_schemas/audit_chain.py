from __future__ import annotations
import logging
from typing import ClassVar, List, Dict
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SCHEMA_VERSION_VJM

logger = logging.getLogger(__name__)


class AuditChainItem(BaseModel):
    """A single auditor definition within a chain."""
    name: str = Field(..., description="Name of the auditor in the chain.")
    image: str = Field(..., description="Container image of the auditor.")


class AuditChainSpec(BaseModel):
    """Specification for an Audit Chain."""
    auditors: List[AuditChainItem] = Field(..., description="Ordered list of auditors to execute.")


class VerifiableJobManifest(BaseModel):
    """Manifest defining a verifiable audit job/chain."""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_VJM

    schema_version: str = Field(
        default=SCHEMA_VERSION_VJM,
        alias="schemaVersion",
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    api_version: str = Field("lucid.sh/v1", alias="apiVersion", description="API Version")

    @field_validator('schema_version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate schema version and log warnings for mismatches."""
        expected = cls._expected_version
        if v != expected:
            logger.warning(
                "Schema version mismatch for %s: got '%s', expected '%s'",
                cls.__name__, v, expected
            )
        return v
    kind: str = Field("VerifiableJobManifest", description="Kind of the resource")
    metadata: Dict[str, str] = Field(..., description="Metadata including name.")
    spec: AuditChainSpec = Field(..., description="Specification of the audit chain.")

    model_config = ConfigDict(populate_by_name=True)
