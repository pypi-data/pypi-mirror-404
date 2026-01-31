import os
import structlog
from .interfaces import SecurityPolicy, ImagePolicy

logger = structlog.get_logger()

class TEE_PROVIDER:
    COCO = "COCO"
    MOCK = "MOCK"
    NONE = "NONE"

def get_tee_provider(default: str = TEE_PROVIDER.COCO) -> str:
    return os.getenv("TEE_PROVIDER", default).upper()

# --- Security Policies ---
# Security policies are decoupled from TEE_PROVIDER to ensure dev behaves like production.
# Only TEE-related functionality (mocking hardware attestation) should differ based on TEE_PROVIDER.

class DefaultSecurityPolicy(SecurityPolicy):
    """Security policy that behaves like production in all environments.

    Dev environments should use the same security controls as production.
    All secrets must be explicitly set via environment variables - no fallbacks.
    This ensures dev/prod parity and prevents accidental use of weak secrets.
    """

    @property
    def api_key_required(self) -> bool:
        # Always require proper API key validation
        return True

    @property
    def tls_required(self) -> bool:
        # TLS can be disabled for local development via LUCID_TLS_REQUIRED=false
        return os.getenv("LUCID_TLS_REQUIRED", "true").lower() != "false"

    def get_jwt_secret(self) -> str:
        """Get JWT secret - must be explicitly set in all environments."""
        secret = os.getenv("LUCID_JWT_SECRET")
        if not secret:
            raise RuntimeError(
                "LUCID_JWT_SECRET must be set. "
                "For local development, use 'make dev' which sets this automatically, "
                "or set it manually: export LUCID_JWT_SECRET=your-secret-min-32-chars"
            )
        if len(secret) < 32:
            raise RuntimeError("LUCID_JWT_SECRET must be at least 32 characters")
        return secret

    def get_reset_secret(self) -> str:
        """Get password reset token secret - must be explicitly set in all environments."""
        secret = os.getenv("LUCID_RESET_SECRET")
        if not secret:
            raise RuntimeError(
                "LUCID_RESET_SECRET must be set. "
                "For local development, use 'make dev' which sets this automatically, "
                "or set it manually: export LUCID_RESET_SECRET=your-secret-min-32-chars"
            )
        if len(secret) < 32:
            raise RuntimeError("LUCID_RESET_SECRET must be at least 32 characters")
        return secret

    def get_verify_secret(self) -> str:
        """Get email verification token secret - must be explicitly set in all environments."""
        secret = os.getenv("LUCID_VERIFY_SECRET")
        if not secret:
            raise RuntimeError(
                "LUCID_VERIFY_SECRET must be set. "
                "For local development, use 'make dev' which sets this automatically, "
                "or set it manually: export LUCID_VERIFY_SECRET=your-secret-min-32-chars"
            )
        if len(secret) < 32:
            raise RuntimeError("LUCID_VERIFY_SECRET must be at least 32 characters")
        return secret

# --- Image Policies ---

class ProdImagePolicy(ImagePolicy):
    @property
    def pull_policy(self) -> str:
        return "Always"

    @property
    def inject_mock_sidecars(self) -> bool:
        return False

    @property
    def strict_notarization(self) -> bool:
        return True

class DevImagePolicy(ImagePolicy):
    @property
    def pull_policy(self) -> str:
        return "IfNotPresent"

    @property
    def inject_mock_sidecars(self) -> bool:
        return True

    @property
    def strict_notarization(self) -> bool:
        """Allow tag-based image references in dev/mock mode.

        In production (COCO), strict_notarization=True requires digest-based references
        (image@sha256:...) to ensure immutability. Images without digests are rejected.

        In dev/mock mode, we allow tag-based references (image:tag) because:
        1. Local Kind clusters use locally-built images with tags
        2. Resolving digests for local images is complex and adds friction
        3. The notarization check still verifies the image is in the registry

        Note: Even with strict_notarization=False, unnotarized images are still rejected.
        The difference is that tag-based images are checked against the registry rather
        than rejected outright.
        """
        return False

# --- Factory ---

def get_security_policy(default: str = TEE_PROVIDER.COCO) -> SecurityPolicy:
    """Returns security policy - always production-like to ensure dev behaves like production."""
    return DefaultSecurityPolicy()

def _is_production_environment() -> bool:
    """Check if LUCID_ENV indicates a production deployment."""
    return os.getenv("LUCID_ENV", "").strip().lower() in ("production", "prod")


def _is_strict_notarization_override() -> bool:
    """Check if LUCID_STRICT_NOTARIZATION is explicitly set to true."""
    return os.getenv("LUCID_STRICT_NOTARIZATION", "").strip().lower() == "true"


def _is_explicit_dev_environment() -> bool:
    """Check if LUCID_ENV explicitly indicates a development deployment."""
    return os.getenv("LUCID_ENV", "").strip().lower() in (
        "development", "dev", "local", "test"
    )


def get_image_policy(default: str = TEE_PROVIDER.COCO) -> ImagePolicy:
    """Returns image policy based on TEE_PROVIDER and environment.

    Image policy controls TEE-specific behavior (mock sidecars, notarization).
    This is the only policy that varies based on TEE_PROVIDER, which is acceptable
    since TEE mocking is explicitly allowed.

    SECURITY (M-5): Default is ProdImagePolicy (strict / fail-closed).
    DevImagePolicy (fail-open) is only returned when LUCID_ENV is
    explicitly set to a development value ("development", "dev", "local", "test")
    AND neither LUCID_STRICT_NOTARIZATION=true nor TEE_PROVIDER=COCO is set.

    ProdImagePolicy is returned when ANY of the following is true:
      1. LUCID_ENV is "production" or "prod"
      2. TEE_PROVIDER is "COCO"
      3. LUCID_STRICT_NOTARIZATION is "true"
      4. LUCID_ENV is not set or not recognized (fail-closed default)
    """
    # SECURITY: Force strict mode in production environments regardless of TEE_PROVIDER
    if _is_production_environment():
        tee = get_tee_provider(default=default)
        if tee != TEE_PROVIDER.COCO:
            logger.error(
                "production_environment_with_non_coco_tee_provider",
                tee_provider=tee,
                lucid_env=os.getenv("LUCID_ENV", ""),
                message="SECURITY: LUCID_ENV is production but TEE_PROVIDER is not COCO. "
                        "Forcing strict (ProdImagePolicy) to prevent fail-open behavior."
            )
        return ProdImagePolicy()

    # SECURITY (M-5): Explicit env-var override to force strict mode.
    # This allows operators to enable fail-closed behaviour without changing
    # TEE_PROVIDER or LUCID_ENV -- belt-and-suspenders.
    if _is_strict_notarization_override():
        logger.info(
            "strict_notarization_override_enabled",
            tee_provider=get_tee_provider(default=default),
            message="LUCID_STRICT_NOTARIZATION=true is set. "
                    "Forcing ProdImagePolicy (strict / fail-closed) regardless of TEE_PROVIDER."
        )
        return ProdImagePolicy()

    if get_tee_provider(default=default) == TEE_PROVIDER.COCO:
        return ProdImagePolicy()

    # SECURITY (M-5): DevImagePolicy requires explicit opt-in via LUCID_ENV
    if _is_explicit_dev_environment():
        logger.warning(
            "non_strict_image_policy_active",
            tee_provider=get_tee_provider(default=default),
            lucid_env=os.getenv("LUCID_ENV", ""),
            message="SECURITY WARNING: Non-strict image policy (DevImagePolicy) is active. "
                    "Unnotarized images may be allowed if the Verifier is unreachable. "
                    "This mode must NOT be used in production deployments."
        )
        return DevImagePolicy()

    # Default: fail-closed for unknown/unset environments
    logger.warning(
        "unknown_environment_defaulting_to_strict",
        tee_provider=get_tee_provider(default=default),
        lucid_env=os.getenv("LUCID_ENV", ""),
        message="LUCID_ENV is not set or not recognized. "
                "Defaulting to ProdImagePolicy (strict / fail-closed). "
                "Set LUCID_ENV to 'development' to use DevImagePolicy."
    )
    return ProdImagePolicy()
