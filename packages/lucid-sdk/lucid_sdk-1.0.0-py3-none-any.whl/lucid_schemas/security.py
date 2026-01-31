"""Security schemas for image verification and supply chain attestation.

This module provides Pydantic models for:
- OCI image manifest information
- Sigstore/Cosign signature verification
- Vulnerability scanning results
- SBOM (Software Bill of Materials) parsing
- Comprehensive image verification results
"""
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SCHEMA_VERSION_SECURITY

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================


class VulnerabilitySeverity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class SBOMFormat(str, Enum):
    """SBOM format types."""
    CYCLONEDX = "cyclonedx"
    SPDX = "spdx"


class ScannerType(str, Enum):
    """Vulnerability scanner types."""
    TRIVY = "trivy"
    GRYPE = "grype"


# =============================================================================
# Image Manifest Models
# =============================================================================


class LayerInfo(BaseModel):
    """Information about a container image layer."""
    digest: str = Field(..., description="Layer digest (e.g., 'sha256:abc123...')")
    media_type: str = Field(..., alias="mediaType", description="Layer media type")
    size: int = Field(..., ge=0, description="Layer size in bytes")

    model_config = ConfigDict(populate_by_name=True)


class ImageManifest(BaseModel):
    """OCI image manifest information."""
    digest: str = Field(..., description="Image digest (e.g., 'sha256:abc123...')")
    media_type: str = Field(..., alias="mediaType", description="Manifest media type")
    size: int = Field(..., ge=0, description="Manifest size in bytes")
    config_digest: str = Field(..., alias="configDigest", description="Config blob digest")
    layers: List[LayerInfo] = Field(default_factory=list, description="Image layers")
    annotations: Optional[Dict[str, str]] = Field(default=None, description="OCI annotations")
    created: Optional[datetime] = Field(default=None, description="Image creation timestamp")
    architecture: Optional[str] = Field(default=None, description="Target architecture (e.g., 'amd64')")
    os: Optional[str] = Field(default=None, description="Target OS (e.g., 'linux')")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Signature Verification Models
# =============================================================================


class SignatureVerification(BaseModel):
    """Result of Sigstore/Cosign signature verification."""
    verified: bool = Field(..., description="Whether the signature was successfully verified")
    signer: Optional[str] = Field(default=None, description="Signer identity (email or OIDC subject)")
    issuer: Optional[str] = Field(default=None, description="OIDC issuer for keyless signing")
    timestamp: Optional[datetime] = Field(default=None, description="Signature timestamp")
    certificate_chain: List[str] = Field(
        default_factory=list,
        alias="certificateChain",
        description="Certificate chain in PEM format"
    )
    transparency_log_entry: Optional[str] = Field(
        default=None,
        alias="transparencyLogEntry",
        description="Rekor transparency log entry ID"
    )
    error: Optional[str] = Field(default=None, description="Error message if verification failed")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Vulnerability Models
# =============================================================================


class VulnerabilityReference(BaseModel):
    """Reference URL for a vulnerability."""
    source: str = Field(..., description="Source name (e.g., 'NVD', 'GHSA')")
    url: str = Field(..., description="Reference URL")


class Vulnerability(BaseModel):
    """A single vulnerability found during scanning."""
    id: str = Field(..., description="Vulnerability ID (e.g., 'CVE-2023-12345')")
    severity: VulnerabilitySeverity = Field(..., description="Vulnerability severity")
    package: str = Field(..., description="Affected package name")
    version: str = Field(..., description="Installed version of the package")
    fixed_version: Optional[str] = Field(
        default=None,
        alias="fixedVersion",
        description="Version that fixes the vulnerability"
    )
    title: Optional[str] = Field(default=None, description="Brief vulnerability title")
    description: Optional[str] = Field(default=None, description="Detailed vulnerability description")
    cvss_score: Optional[float] = Field(
        default=None,
        alias="cvssScore",
        ge=0.0,
        le=10.0,
        description="CVSS score (0.0-10.0)"
    )
    cvss_vector: Optional[str] = Field(
        default=None,
        alias="cvssVector",
        description="CVSS vector string"
    )
    references: List[VulnerabilityReference] = Field(
        default_factory=list,
        description="Reference URLs"
    )
    published_at: Optional[datetime] = Field(
        default=None,
        alias="publishedAt",
        description="When the vulnerability was published"
    )

    model_config = ConfigDict(populate_by_name=True)


class VulnerabilityScan(BaseModel):
    """Result of a vulnerability scan."""
    scanned_at: datetime = Field(..., alias="scannedAt", description="When the scan was performed")
    scanner: ScannerType = Field(..., description="Scanner used (trivy or grype)")
    scanner_version: Optional[str] = Field(
        default=None,
        alias="scannerVersion",
        description="Version of the scanner"
    )
    image: str = Field(..., description="Scanned image reference")
    digest: Optional[str] = Field(default=None, description="Image digest that was scanned")

    # Summary counts by severity
    critical: int = Field(default=0, ge=0, description="Number of critical vulnerabilities")
    high: int = Field(default=0, ge=0, description="Number of high vulnerabilities")
    medium: int = Field(default=0, ge=0, description="Number of medium vulnerabilities")
    low: int = Field(default=0, ge=0, description="Number of low vulnerabilities")
    unknown: int = Field(default=0, ge=0, description="Number of unknown severity vulnerabilities")

    # Detailed vulnerability list
    vulnerabilities: List[Vulnerability] = Field(
        default_factory=list,
        description="List of vulnerabilities found"
    )

    # Scan metadata
    scan_duration_ms: Optional[int] = Field(
        default=None,
        alias="scanDurationMs",
        description="Scan duration in milliseconds"
    )
    error: Optional[str] = Field(default=None, description="Error message if scan failed")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def total_vulnerabilities(self) -> int:
        """Total number of vulnerabilities found."""
        return self.critical + self.high + self.medium + self.low + self.unknown

    @property
    def has_critical(self) -> bool:
        """Whether any critical vulnerabilities were found."""
        return self.critical > 0

    @property
    def has_high_or_critical(self) -> bool:
        """Whether any high or critical vulnerabilities were found."""
        return self.critical > 0 or self.high > 0


# =============================================================================
# SBOM Models
# =============================================================================


class SBOMLicense(BaseModel):
    """License information for an SBOM component."""
    id: Optional[str] = Field(default=None, description="SPDX license ID")
    name: Optional[str] = Field(default=None, description="License name")
    url: Optional[str] = Field(default=None, description="License URL")


class SBOMComponent(BaseModel):
    """A component in an SBOM."""
    name: str = Field(..., description="Component name")
    version: str = Field(..., description="Component version")
    purl: Optional[str] = Field(default=None, description="Package URL (purl)")
    type: Optional[str] = Field(default=None, description="Component type (library, application, etc.)")
    supplier: Optional[str] = Field(default=None, description="Component supplier/publisher")
    licenses: List[SBOMLicense] = Field(default_factory=list, description="Component licenses")
    hashes: Optional[Dict[str, str]] = Field(default=None, description="Component hashes (SHA256, etc.)")
    description: Optional[str] = Field(default=None, description="Component description")
    external_references: List[str] = Field(
        default_factory=list,
        alias="externalReferences",
        description="External reference URLs"
    )

    model_config = ConfigDict(populate_by_name=True)


class SBOMDependency(BaseModel):
    """A dependency relationship in an SBOM."""
    ref: str = Field(..., description="Component reference (usually purl or name)")
    depends_on: List[str] = Field(
        default_factory=list,
        alias="dependsOn",
        description="List of dependencies (purls or names)"
    )

    model_config = ConfigDict(populate_by_name=True)


class SBOMSummary(BaseModel):
    """Summary statistics for an SBOM."""
    total_components: int = Field(default=0, alias="totalComponents")
    total_dependencies: int = Field(default=0, alias="totalDependencies")
    unique_licenses: List[str] = Field(default_factory=list, alias="uniqueLicenses")
    component_types: Dict[str, int] = Field(default_factory=dict, alias="componentTypes")

    model_config = ConfigDict(populate_by_name=True)


class SBOM(BaseModel):
    """Software Bill of Materials."""
    format: SBOMFormat = Field(..., description="SBOM format (cyclonedx or spdx)")
    spec_version: str = Field(..., alias="specVersion", description="SBOM specification version")
    serial_number: Optional[str] = Field(
        default=None,
        alias="serialNumber",
        description="Unique SBOM serial number"
    )
    version: int = Field(default=1, description="SBOM document version")
    created: Optional[datetime] = Field(default=None, description="SBOM creation timestamp")
    tool_name: Optional[str] = Field(default=None, alias="toolName", description="Tool that generated the SBOM")
    tool_version: Optional[str] = Field(
        default=None,
        alias="toolVersion",
        description="Version of the generating tool"
    )

    # Components and dependencies
    components: List[SBOMComponent] = Field(default_factory=list, description="List of components")
    dependencies: List[SBOMDependency] = Field(default_factory=list, description="Dependency relationships")

    # Summary (computed)
    summary: Optional[SBOMSummary] = Field(default=None, description="SBOM summary statistics")

    # Raw data (for debugging/advanced use)
    raw: Optional[Dict[str, Any]] = Field(default=None, description="Raw SBOM document")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# SLSA Provenance Models
# =============================================================================


class SLSABuilder(BaseModel):
    """SLSA builder information."""
    id: str = Field(..., description="Builder ID URI")
    version: Optional[str] = Field(default=None, description="Builder version")


class SLSAMaterial(BaseModel):
    """SLSA build material (source input)."""
    uri: str = Field(..., description="Material URI")
    digest: Dict[str, str] = Field(default_factory=dict, description="Material digests")


class SLSAProvenance(BaseModel):
    """SLSA provenance attestation."""
    builder: SLSABuilder = Field(..., description="Builder information")
    build_type: str = Field(..., alias="buildType", description="Build type URI")
    invocation: Optional[Dict[str, Any]] = Field(default=None, description="Build invocation details")
    materials: List[SLSAMaterial] = Field(default_factory=list, description="Build materials")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

    model_config = ConfigDict(populate_by_name=True)


# =============================================================================
# Image Verification Result
# =============================================================================


class ImageVerificationResult(BaseModel):
    """Comprehensive result of image verification pipeline.

    This model combines all verification data including:
    - Image manifest and digest
    - Sigstore/Cosign signature verification
    - SBOM data
    - Vulnerability scan results
    - SLSA level calculation
    """
    _expected_version: ClassVar[str] = SCHEMA_VERSION_SECURITY

    schema_version: str = Field(
        default=SCHEMA_VERSION_SECURITY,
        alias="schemaVersion",
        description="Schema version for backwards compatibility. Follows SemVer.",
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )

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

    # Image identification
    image: str = Field(..., description="Image reference (e.g., 'ghcr.io/org/repo:tag')")
    tag: str = Field(..., description="Image tag")
    digest: str = Field(..., description="Image digest")

    # Manifest
    manifest: ImageManifest = Field(..., description="OCI image manifest")

    # Signature verification
    signature: Optional[SignatureVerification] = Field(
        default=None,
        description="Sigstore/Cosign signature verification result"
    )

    # SBOM
    sbom: Optional[SBOM] = Field(default=None, description="Software Bill of Materials")

    # Vulnerability scan
    vulnerabilities: VulnerabilityScan = Field(..., description="Vulnerability scan results")

    # SLSA level
    slsa_level: int = Field(
        default=0,
        alias="slsaLevel",
        ge=0,
        le=4,
        description="Calculated SLSA level (0-4)"
    )
    slsa_provenance: Optional[SLSAProvenance] = Field(
        default=None,
        alias="slsaProvenance",
        description="SLSA provenance attestation if available"
    )

    # Verification metadata
    verified_at: datetime = Field(..., alias="verifiedAt", description="When verification was performed")
    verification_duration_ms: Optional[int] = Field(
        default=None,
        alias="verificationDurationMs",
        description="Total verification duration in milliseconds"
    )

    # Overall status
    verified: bool = Field(default=False, description="Whether the image passed all verification checks")
    errors: List[str] = Field(default_factory=list, description="List of verification errors")
    warnings: List[str] = Field(default_factory=list, description="List of verification warnings")

    model_config = ConfigDict(populate_by_name=True)

    @property
    def is_signed(self) -> bool:
        """Whether the image has a valid signature."""
        return self.signature is not None and self.signature.verified

    @property
    def has_sbom(self) -> bool:
        """Whether an SBOM is available."""
        return self.sbom is not None and len(self.sbom.components) > 0

    @property
    def security_score(self) -> int:
        """Calculate a simple security score (0-100).

        Scoring:
        - Base: 50 points
        - Signature verified: +20 points
        - SBOM available: +10 points
        - No critical vulns: +10 points
        - No high vulns: +5 points
        - SLSA level: +5 points per level (max 20)
        - Deductions for vulnerabilities
        """
        score = 50

        # Signature
        if self.is_signed:
            score += 20

        # SBOM
        if self.has_sbom:
            score += 10

        # SLSA
        score += min(self.slsa_level * 5, 20)

        # Vulnerabilities
        if not self.vulnerabilities.has_critical:
            score += 10
        if not self.vulnerabilities.has_high_or_critical:
            score += 5

        # Deductions
        score -= min(self.vulnerabilities.critical * 10, 30)
        score -= min(self.vulnerabilities.high * 3, 15)
        score -= min(self.vulnerabilities.medium * 1, 5)

        return max(0, min(100, score))
