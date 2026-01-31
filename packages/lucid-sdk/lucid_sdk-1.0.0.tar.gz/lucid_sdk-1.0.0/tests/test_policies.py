import pytest
from unittest.mock import patch
from lucid_sdk.policies import (
    get_tee_provider,
    get_security_policy,
    get_image_policy,
    _is_production_environment,
    TEE_PROVIDER,
    DefaultSecurityPolicy,
    ProdImagePolicy,
    DevImagePolicy
)

def test_get_tee_provider_default():
    """Test get_tee_provider default behavior."""
    def getenv_side_effect(key, default=None):
        return default
    with patch("os.getenv", side_effect=getenv_side_effect):
        # Default is COCO
        assert get_tee_provider() == TEE_PROVIDER.COCO
        # Custom default
        assert get_tee_provider(default=TEE_PROVIDER.MOCK) == TEE_PROVIDER.MOCK

def test_get_tee_provider_env():
    """Test get_tee_provider with environment variable."""
    with patch("os.getenv") as mock_env:
        mock_env.return_value = "MOCK"
        assert get_tee_provider() == TEE_PROVIDER.MOCK

        mock_env.return_value = "COCO"
        assert get_tee_provider() == TEE_PROVIDER.COCO

        mock_env.return_value = "none"
        assert get_tee_provider() == TEE_PROVIDER.NONE

def test_get_security_policy_selection():
    """Test that security policy is always production-like (DefaultSecurityPolicy)."""
    # Security policy is now always DefaultSecurityPolicy regardless of TEE_PROVIDER
    # to ensure dev behaves like production
    with patch("os.getenv", return_value="COCO"):
        policy = get_security_policy()
        assert isinstance(policy, DefaultSecurityPolicy)
        assert policy.api_key_required is True

    with patch("os.getenv", return_value="MOCK"):
        policy = get_security_policy()
        assert isinstance(policy, DefaultSecurityPolicy)
        assert policy.api_key_required is True

def test_get_image_policy_selection():
    """Test that the correct ImagePolicy is selected based on TEE_PROVIDER."""
    # Production (COCO) - uses ProdImagePolicy
    env = {"TEE_PROVIDER": "COCO", "LUCID_ENV": "production", "LUCID_STRICT_NOTARIZATION": ""}
    with patch.dict("os.environ", env, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.pull_policy == "Always"
        assert policy.inject_mock_sidecars is False
        assert policy.strict_notarization is True

    # Development (MOCK) - uses DevImagePolicy when LUCID_ENV is explicit
    env = {"TEE_PROVIDER": "MOCK", "LUCID_ENV": "development", "LUCID_STRICT_NOTARIZATION": ""}
    with patch.dict("os.environ", env, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, DevImagePolicy)
        assert policy.pull_policy == "IfNotPresent"
        assert policy.inject_mock_sidecars is True

def test_security_policy_jwt_secret():
    """Test JWT secret retrieval - requires explicit LUCID_JWT_SECRET env var."""
    policy = DefaultSecurityPolicy()

    # When LUCID_JWT_SECRET is set, use it
    with patch.dict("os.environ", {"LUCID_JWT_SECRET": "my-production-secret-key-32chars"}, clear=False):
        assert policy.get_jwt_secret() == "my-production-secret-key-32chars"

    # When LUCID_JWT_SECRET is not set, raise RuntimeError
    # Use patch.dict with clear=False and explicitly remove the key to ensure it's not set
    env_without_secret = {k: v for k, v in __import__("os").environ.items() if k != "LUCID_JWT_SECRET"}
    with patch.dict("os.environ", env_without_secret, clear=True):
        with pytest.raises(RuntimeError, match="LUCID_JWT_SECRET must be set"):
            policy.get_jwt_secret()

def test_security_policy_tls_required():
    """Test TLS requirement can be disabled via environment variable."""
    policy = DefaultSecurityPolicy()

    # Default is TLS required
    with patch("os.getenv", return_value="true"):
        assert policy.tls_required is True

    # Can be disabled for local development
    with patch("os.getenv", return_value="false"):
        assert policy.tls_required is False


# --- M-5: Production environment safeguard tests ---

def test_is_production_environment():
    """Test _is_production_environment detects production LUCID_ENV values."""
    with patch.dict("os.environ", {"LUCID_ENV": "production"}, clear=False):
        assert _is_production_environment() is True

    with patch.dict("os.environ", {"LUCID_ENV": "prod"}, clear=False):
        assert _is_production_environment() is True

    with patch.dict("os.environ", {"LUCID_ENV": "Production"}, clear=False):
        assert _is_production_environment() is True

    with patch.dict("os.environ", {"LUCID_ENV": "PROD"}, clear=False):
        assert _is_production_environment() is True

    with patch.dict("os.environ", {"LUCID_ENV": "  production  "}, clear=False):
        assert _is_production_environment() is True

    with patch.dict("os.environ", {"LUCID_ENV": "development"}, clear=False):
        assert _is_production_environment() is False

    with patch.dict("os.environ", {"LUCID_ENV": "MOCK"}, clear=False):
        assert _is_production_environment() is False

    with patch.dict("os.environ", {"LUCID_ENV": ""}, clear=False):
        assert _is_production_environment() is False

    # When env var is not set at all
    env_without = {k: v for k, v in __import__("os").environ.items() if k != "LUCID_ENV"}
    with patch.dict("os.environ", env_without, clear=True):
        assert _is_production_environment() is False


def test_production_env_forces_strict_mode_even_with_mock_tee():
    """M-5: In production environment, get_image_policy must return ProdImagePolicy
    even when TEE_PROVIDER is MOCK."""
    with patch.dict("os.environ", {"LUCID_ENV": "production", "TEE_PROVIDER": "MOCK"}, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.strict_notarization is True

    with patch.dict("os.environ", {"LUCID_ENV": "prod", "TEE_PROVIDER": "MOCK"}, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.strict_notarization is True


def test_production_env_with_coco_returns_prod_policy():
    """M-5: In production environment with COCO TEE_PROVIDER, ProdImagePolicy is returned."""
    with patch.dict("os.environ", {"LUCID_ENV": "production", "TEE_PROVIDER": "COCO"}, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.strict_notarization is True


def test_non_production_env_with_mock_returns_dev_policy():
    """M-5: In non-production environment with MOCK TEE_PROVIDER, DevImagePolicy is returned."""
    env = {"LUCID_ENV": "development", "TEE_PROVIDER": "MOCK", "LUCID_STRICT_NOTARIZATION": ""}
    with patch.dict("os.environ", env, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, DevImagePolicy)
        assert policy.strict_notarization is False


def test_no_lucid_env_with_mock_defaults_to_strict():
    """M-5: Without LUCID_ENV set, defaults to ProdImagePolicy (fail-closed)."""
    env_copy = {k: v for k, v in __import__("os").environ.items()
                if k not in ("LUCID_ENV", "LUCID_STRICT_NOTARIZATION")}
    env_copy["TEE_PROVIDER"] = "MOCK"
    with patch.dict("os.environ", env_copy, clear=True):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.strict_notarization is True


def test_explicit_dev_environment_with_mock_returns_dev_policy():
    """M-5: Explicit dev environment with MOCK TEE_PROVIDER returns DevImagePolicy."""
    for env_val in ("development", "dev", "local", "test"):
        env = {"LUCID_ENV": env_val, "TEE_PROVIDER": "MOCK", "LUCID_STRICT_NOTARIZATION": ""}
        with patch.dict("os.environ", env, clear=False):
            policy = get_image_policy()
            assert isinstance(policy, DevImagePolicy), f"Expected DevImagePolicy for {env_val}"


def test_strict_notarization_env_override_forces_prod_policy():
    """M-5: LUCID_STRICT_NOTARIZATION=true forces ProdImagePolicy even with MOCK TEE_PROVIDER."""
    env = {"LUCID_ENV": "development", "TEE_PROVIDER": "MOCK", "LUCID_STRICT_NOTARIZATION": "true"}
    with patch.dict("os.environ", env, clear=False):
        policy = get_image_policy()
        assert isinstance(policy, ProdImagePolicy)
        assert policy.strict_notarization is True


def test_strict_notarization_env_override_case_insensitive():
    """M-5: LUCID_STRICT_NOTARIZATION override is case-insensitive and strips whitespace."""
    for value in ("True", "TRUE", " true ", "  True  "):
        env = {"LUCID_ENV": "", "TEE_PROVIDER": "MOCK", "LUCID_STRICT_NOTARIZATION": value}
        with patch.dict("os.environ", env, clear=False):
            policy = get_image_policy()
            assert isinstance(policy, ProdImagePolicy), f"Expected ProdImagePolicy for value={value!r}"


def test_strict_notarization_env_non_true_values_ignored():
    """M-5: LUCID_STRICT_NOTARIZATION with non-'true' values does not force strict mode."""
    for value in ("false", "yes", "1", ""):
        env = {"LUCID_ENV": "development", "TEE_PROVIDER": "MOCK", "LUCID_STRICT_NOTARIZATION": value}
        with patch.dict("os.environ", env, clear=False):
            policy = get_image_policy()
            assert isinstance(policy, DevImagePolicy), f"Expected DevImagePolicy for value={value!r}"

