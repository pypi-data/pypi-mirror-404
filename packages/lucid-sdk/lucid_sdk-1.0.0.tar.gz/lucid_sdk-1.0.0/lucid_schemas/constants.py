from __future__ import annotations

# --- OCI LABEL CONSTANTS ---
LUCID_LABEL_PREFIX = "sh.lucid"
LUCID_LABEL_AUDITOR = f"{LUCID_LABEL_PREFIX}.auditor"
LUCID_LABEL_SCHEMA_VERSION = f"{LUCID_LABEL_PREFIX}.schema_version"
LUCID_LABEL_PHASE = f"{LUCID_LABEL_PREFIX}.phase"
LUCID_LABEL_INTERFACES = f"{LUCID_LABEL_PREFIX}.interfaces"
LUCID_LABEL_SIGNATURE = f"{LUCID_LABEL_PREFIX}.signature"


# =============================================================================
# Schema Version Constants
# =============================================================================
# These version strings follow Semantic Versioning (SemVer).
# MAJOR: Breaking changes (incompatible API changes)
# MINOR: Backwards-compatible new features
# PATCH: Backwards-compatible bug fixes
#
# IMPORTANT: Package version vs Schema version
# - Package version (pyproject.toml): Controls pip/poetry dependency resolution
# - Schema versions (below): Embedded in serialized data for compatibility
#
# When updating a schema version:
# 1. Bump MINOR for new optional fields
# 2. Bump MAJOR for required field changes, field removals, or type changes
# 3. Update the corresponding schema's schema_version default value
# 4. Document the change in CHANGELOG.md with migration guide
# 5. Update the compatibility matrix in CHANGELOG.md
#
# Consumers should:
# - Check schema_version before processing
# - Handle missing fields gracefully (may be from older versions)
# - Log warnings for unknown schema versions
# - See CHANGELOG.md for version history and migration guides
# =============================================================================

# Core schema versions
SCHEMA_VERSION_ATTESTATION = "1.0.0-beta"      # AttestationResult/AIPassport schema version
SCHEMA_VERSION_AGENT = "1.0.0-beta"            # Agent-related schemas version
SCHEMA_VERSION_DASHBOARD = "1.0.0-beta"        # Dashboard schemas version
SCHEMA_VERSION_VJM = "1.0.0-beta"              # VerifiableJobManifest schema version
SCHEMA_VERSION_REFERENCE_VALUES = "1.0.0-beta"  # Reference values (CoRIM) schema version
SCHEMA_VERSION_EVALUATION = "1.0.0-beta"        # EvaluationResult schema version
SCHEMA_VERSION_RECEIPT = "1.0.0-beta"           # InteractionReceipt schema version
SCHEMA_VERSION_SECURITY = "1.0.0-beta"          # Security/ImageVerificationResult schema version

# RATS-compliant schema versions (RFC 9334)
SCHEMA_VERSION_CLAIM = "2.0.0"                 # Claim schema version (unsigned assertion)
SCHEMA_VERSION_EVIDENCE = "2.0.0"              # Evidence schema version (signed container of Claims)

# Policy schema versions
SCHEMA_VERSION_POLICY = "1.0.0"                # Policy/PolicyBundle schema version

# Serverless schema versions
SCHEMA_VERSION_SERVERLESS = "1.0.0-beta"       # Serverless environment schema version

# Current default version for new schemas
SCHEMA_VERSION_DEFAULT = "1.0.0-beta"
