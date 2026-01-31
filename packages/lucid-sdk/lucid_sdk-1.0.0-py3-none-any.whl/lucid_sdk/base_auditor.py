"""
Base Auditor Framework

Provides common boilerplate for Lucid auditors including:
- Structured JSON logging setup
- Environment variable parsing utilities
- HTTP client factory with timeout configuration
- FastAPI app factory with health endpoints
- Configuration validation utilities

Usage:
    from lucid_sdk.base_auditor import BaseAuditorConfig, create_auditor_app, get_logger

    class MyConfig(BaseAuditorConfig):
        threshold: float = 0.8
        block_on_detection: bool = True

    config = MyConfig.from_env(prefix="MY_AUDITOR")
    app = create_auditor_app("My Auditor", config)
    logger = get_logger()
"""

import os
import json
import hashlib
import structlog
import httpx
from typing import Any, Dict, Optional, TypeVar, Type, Callable
from dataclasses import dataclass, field, fields
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.routing import APIRouter

from .resilience import retry_with_backoff, resilient

# Configure structlog once at import time
_logger_configured = False


def configure_logging() -> None:
    """Configure structlog for JSON output with timestamps."""
    global _logger_configured
    if _logger_configured:
        return

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )
    _logger_configured = True


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured structlog logger.

    Args:
        name: Optional logger name for context.

    Returns:
        A configured structlog logger instance.
    """
    configure_logging()
    logger = structlog.get_logger()
    if name:
        logger = logger.bind(auditor=name)
    return logger


# Type variable for config subclasses
T = TypeVar("T", bound="BaseAuditorConfig")


@dataclass
class BaseAuditorConfig:
    """Base configuration class for auditors.

    Provides common configuration fields and environment variable parsing.
    Subclass this to add auditor-specific configuration.

    Environment Variables (supported by all auditors):
        LUCID_AUDITOR_ID: Unique identifier for this auditor instance.
            Injected by Lucid Operator in TEE environments.
            Default: "unknown-auditor"

        LUCID_SESSION_ID: Current audit session identifier.
            Used for correlating measurements within a request lifecycle.
            Default: "demo-session"

        LUCID_VERIFIER_URL: URL of the Verifier service for submitting evidence.
            Default: "http://verifier-service.lucid-system.svc.cluster.local:8000"

        MODEL_ID: Identifier of the model being audited.
            Default: "default-model"

        HTTP_TIMEOUT: Timeout (seconds) for standard HTTP requests.
            Used for verifier calls and external API requests.
            Default: 5.0

        HTTP_CHAIN_TIMEOUT: Timeout (seconds) for auditor chain forwarding.
            Longer timeout to account for multi-hop latency.
            Default: 10.0

        PORT: Port number for the auditor HTTP server.
            Default: 8090

    Configuration Precedence (highest to lowest):
        1. Prefixed env var (e.g., INJECTION_THRESHOLD)
        2. Unprefixed env var (e.g., THRESHOLD)
        3. Field default value
        4. Dataclass default_factory

    Type Conversion Rules:
        - bool: "true" (case-insensitive) -> True, anything else -> False
        - int: Parsed via int()
        - float: Parsed via float()
        - str: Used as-is

    Validation:
        Call validate() after construction. Override to add custom rules.
        Built-in checks: http_timeout > 0, 1 <= port <= 65535

    Example:
        @dataclass
        class InjectionConfig(BaseAuditorConfig):
            threshold: float = 0.8
            block_on_detection: bool = True
            ban_substrings: str = "ignore previous,disregard"

        config = InjectionConfig.from_env(prefix="INJECTION")
    """
    # Common auditor configuration
    auditor_id: str = field(default_factory=lambda: os.getenv("LUCID_AUDITOR_ID", "unknown-auditor"))
    session_id: str = field(default_factory=lambda: os.getenv("LUCID_SESSION_ID", "demo-session"))
    verifier_url: str = field(
        default_factory=lambda: os.getenv(
            "LUCID_VERIFIER_URL",
            "http://verifier-service.lucid-system.svc.cluster.local:8000"
        )
    )
    model_id: str = field(default_factory=lambda: os.getenv("MODEL_ID", "default-model"))

    # HTTP client configuration
    http_timeout: float = field(default_factory=lambda: float(os.getenv("HTTP_TIMEOUT", "5.0")))
    http_chain_timeout: float = field(default_factory=lambda: float(os.getenv("HTTP_CHAIN_TIMEOUT", "10.0")))

    # Server configuration
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8090")))

    @classmethod
    def from_env(cls: Type[T], prefix: str = "") -> T:
        """Create configuration from environment variables.

        Args:
            prefix: Optional prefix for environment variables (e.g., "INJECTION" -> "INJECTION_THRESHOLD").

        Returns:
            Configuration instance with values from environment.
        """
        kwargs: Dict[str, Any] = {}
        prefix_str = f"{prefix}_" if prefix else ""

        for f in fields(cls):
            env_key = f"{prefix_str}{f.name.upper()}"
            env_value = os.getenv(env_key)

            if env_value is not None:
                # Convert to appropriate type
                if f.type == bool:
                    kwargs[f.name] = env_value.lower() == "true"
                elif f.type == int:
                    kwargs[f.name] = int(env_value)
                elif f.type == float:
                    kwargs[f.name] = float(env_value)
                else:
                    kwargs[f.name] = env_value

        return cls(**kwargs)

    def validate(self) -> None:
        """Validate configuration. Override to add custom validation.

        Raises:
            ValueError: If configuration is invalid.
        """
        if self.http_timeout <= 0:
            raise ValueError(f"http_timeout must be positive, got {self.http_timeout}")
        if self.port <= 0 or self.port > 65535:
            raise ValueError(f"port must be between 1 and 65535, got {self.port}")


class HTTPClientFactory:
    """Factory for creating configured HTTP clients with resilience patterns."""

    def __init__(self, config: BaseAuditorConfig, logger: Optional[structlog.BoundLogger] = None):
        self.config = config
        self.logger = logger or get_logger()
        self._client: Optional[httpx.AsyncClient] = None
        self._chain_client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client.

        Returns:
            Configured httpx.AsyncClient instance.
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.http_timeout),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        return self._client

    async def close(self) -> None:
        """Close all HTTP clients."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        if self._chain_client is not None and not self._chain_client.is_closed:
            await self._chain_client.aclose()
            self._chain_client = None

    async def get_chain_client(self) -> httpx.AsyncClient:
        """Get an HTTP client configured for chain calls (longer timeout).

        Returns:
            Configured httpx.AsyncClient for chain operations.
        """
        if self._chain_client is None or self._chain_client.is_closed:
            self._chain_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.http_chain_timeout),
                limits=httpx.Limits(max_connections=50, max_keepalive_connections=10)
            )
        return self._chain_client

    async def post_with_retry(
        self,
        url: str,
        json_data: Dict[str, Any],
        max_retries: int = 3,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """POST with automatic retry on 5xx/timeout errors.

        Args:
            url: The URL to POST to.
            json_data: JSON payload to send.
            max_retries: Maximum retry attempts.
            timeout: Optional timeout override.

        Returns:
            httpx.Response on success.

        Raises:
            httpx.HTTPError: If all retries fail.
        """
        @retry_with_backoff(
            max_retries=max_retries,
            base_delay=0.5,
            retryable_exceptions=(httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError),
        )
        async def _post() -> httpx.Response:
            client = await self.get_client()
            response = await client.post(
                url,
                json=json_data,
                timeout=timeout or self.config.http_timeout
            )
            # Raise for 5xx errors to trigger retry
            if response.status_code >= 500:
                response.raise_for_status()
            return response

        return await _post()

    async def chain_call(
        self,
        next_auditor_url: str,
        data: Dict[str, Any],
        lucid_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Resilient call to next auditor in chain.

        Args:
            next_auditor_url: URL of the next auditor.
            data: Request data to forward.
            lucid_context: Lucid context to pass through chain.

        Returns:
            Response from next auditor, or None if chain fails.
        """
        try:
            chain_payload = {"data": data, "lucid_context": lucid_context}
            client = await self.get_chain_client()
            response = await client.post(
                next_auditor_url,
                json=chain_payload,
                timeout=self.config.http_chain_timeout
            )
            return response.json()
        except (httpx.HTTPError, ValueError) as e:
            self.logger.error("auditor_chain_broken", error=str(e), next_url=next_auditor_url)
            return None

    async def submit_evidence(
        self,
        auditor_id: str,
        model_id: str,
        session_id: str,
        nonce: Optional[str],
        decision: str,
        metadata: Dict[str, Any],
        phase: str = "request",
    ) -> bool:
        """Submit audit evidence to the verifier for passport creation.

        Args:
            auditor_id: ID of this auditor.
            model_id: Model being audited.
            session_id: Current session ID.
            nonce: Optional nonce for request binding.
            decision: Audit decision (proceed/warn/deny/redact).
            metadata: Additional audit metadata.
            phase: Audit phase (request/response/artifact/execution).

        Returns:
            True if evidence was submitted successfully, False otherwise.
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            measurement = {
                "name": auditor_id,
                "type": "conformity",
                "phase": phase,
                "value": {
                    "decision": decision,
                    **metadata
                },
                "timestamp": timestamp,
                "nonce": nonce,
            }
            # Generate signature for the measurement
            blob = json.dumps(measurement, sort_keys=True, separators=(',', ':')).encode('utf-8')
            measurement["signature"] = hashlib.sha256(blob).hexdigest()

            evidence_payload = {
                "session_id": session_id,
                "model_id": model_id,
                "measurements": [measurement],
                "evaluations": []
            }

            response = await self.post_with_retry(
                f"{self.config.verifier_url}/v1/evidence/verify",
                evidence_payload,
                max_retries=2,
            )

            if response.status_code == 200:
                self.logger.info("evidence_submitted", model_id=model_id, nonce=nonce)
                return True
            else:
                self.logger.warning(
                    "evidence_submission_failed",
                    status=response.status_code,
                    body=response.text[:200]
                )
                return False
        except Exception as e:
            self.logger.error("evidence_submission_error", error=str(e))
            return False


def create_health_router(
    service_name: str,
    readiness_check: Optional[Callable] = None,
) -> APIRouter:
    """Create an APIRouter with standard health-check endpoints.

    Provides the same health endpoint pattern used by auditors (via
    ``create_auditor_app``) so that non-auditor apps can reuse it.

    Endpoints registered:
    - ``GET /`` and ``GET /health`` – liveness check
    - ``GET /health/live`` – Kubernetes liveness probe
    - ``GET /health/ready`` – Kubernetes readiness probe

    Args:
        service_name: Human-readable service name included in responses.
        readiness_check: Optional *async* callable that raises
            ``HTTPException(503, ...)`` when the service is not ready.

    Returns:
        A FastAPI ``APIRouter`` ready to be included in an application.

    Example::

        from lucid_sdk import create_health_router

        router = create_health_router("lucid-verifier")
        app.include_router(router)
    """
    router = APIRouter(tags=["health"])

    @router.get("/health")
    @router.get("/")
    async def liveness_check():
        return {"status": "ok", "service": service_name}

    @router.get("/health/live")
    async def live():
        return {"status": "ok", "service": service_name}

    @router.get("/health/ready")
    async def readiness():
        if readiness_check is not None:
            await readiness_check()
        return {"status": "ready", "service": service_name}

    return router


def create_auditor_app(
    title: str,
    config: BaseAuditorConfig,
    on_startup: Optional[Callable] = None,
    on_shutdown: Optional[Callable] = None,
) -> FastAPI:
    """Create a FastAPI app with standard auditor endpoints.

    Creates a FastAPI application with:
    - /health endpoint for liveness checks
    - /ready endpoint for readiness checks
    - Standard error handling
    - Lifecycle management

    Args:
        title: The auditor's display name.
        config: Auditor configuration instance.
        on_startup: Optional async function to run on startup.
        on_shutdown: Optional async function to run on shutdown.

    Returns:
        Configured FastAPI application.

    Example:
        config = MyConfig.from_env()
        app = create_auditor_app("My Auditor", config)

        @app.post("/audit")
        async def audit(request: Request):
            # Auditor logic here
            pass
    """
    logger = get_logger(config.auditor_id)
    http_factory = HTTPClientFactory(config, logger)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage application lifecycle."""
        logger.info("auditor_starting", auditor_id=config.auditor_id, port=config.port)

        if on_startup:
            await on_startup()

        yield

        logger.info("auditor_shutting_down", auditor_id=config.auditor_id)
        await http_factory.close()

        if on_shutdown:
            await on_shutdown()

    app = FastAPI(title=title, lifespan=lifespan)

    # Store config and factory on app for access in routes
    app.state.config = config
    app.state.http_factory = http_factory
    app.state.logger = logger

    @app.get("/health")
    async def health_check() -> Dict[str, Any]:
        """Liveness check endpoint."""
        return {
            "status": "healthy",
            "auditor_id": config.auditor_id,
            "version": "1.0.0"
        }

    @app.get("/ready")
    async def readiness_check() -> Dict[str, Any]:
        """Readiness check endpoint."""
        return {
            "status": "ready",
            "auditor_id": config.auditor_id
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.error(
            "unhandled_exception",
            auditor_id=config.auditor_id,
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred",
                "auditor_id": config.auditor_id
            }
        )

    return app


def run_auditor(app: FastAPI, config: BaseAuditorConfig) -> None:
    """Run the auditor using uvicorn.

    Args:
        app: The FastAPI application.
        config: Auditor configuration.
    """
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=config.port)  # nosec B104 - Required for container/K8s networking


class BaseAuditorApp:
    """Base class for auditor applications with common /audit endpoint logic.

    This class encapsulates the boilerplate that all 7 auditors share:
    - FastAPI app creation with health/ready endpoints
    - Common /audit endpoint pattern with phase detection
    - Auditor chain forwarding
    - Evidence submission to verifier
    - Redact/deny/warn/proceed handling

    Subclasses should:
    1. Create their config class extending BaseAuditorConfig
    2. Create their auditor using create_auditor()
    3. Override phase_detection() if needed for custom phase logic
    4. Optionally override build_response_metadata() for custom metadata

    Example:
        class MyAuditor(BaseAuditorApp):
            def __init__(self):
                # Create config
                config = MyConfig()
                config.auditor_id = os.getenv("LUCID_AUDITOR_ID", "my-auditor")
                config.port = int(os.getenv("PORT", "8090"))

                # Initialize base
                super().__init__("My Auditor", config)

                # Create auditor handlers
                builder = create_auditor(auditor_id=config.auditor_id)

                @builder.on_request
                def check_request(data, config_param=None, lucid_context=None):
                    # Custom logic
                    return Proceed(data={"checked": True})

                self.auditor = builder.build()

        # Usage
        auditor_app = MyAuditor()
        app = auditor_app.app

        if __name__ == "__main__":
            auditor_app.run()
    """

    def __init__(
        self,
        title: str,
        config: BaseAuditorConfig,
        on_startup: Optional[Callable] = None,
        on_shutdown: Optional[Callable] = None,
    ):
        """Initialize the base auditor application.

        Args:
            title: Display name for the auditor.
            config: Auditor configuration instance.
            on_startup: Optional async callback for startup.
            on_shutdown: Optional async callback for shutdown.
        """
        self.config = config
        self.title = title
        self._on_startup = on_startup
        self._on_shutdown = on_shutdown

        # Create the FastAPI app
        self.app = create_auditor_app(title, config, on_startup, on_shutdown)

        # Get references to shared state
        self.logger = self.app.state.logger
        self.http_factory = self.app.state.http_factory

        # Auditor instance - should be set by subclass
        self.auditor = None

        # Register the /audit endpoint
        self._register_audit_endpoint()

    def _register_audit_endpoint(self) -> None:
        """Register the common /audit endpoint."""

        @self.app.post("/audit")
        async def handle_audit(request: Request) -> Dict[str, Any]:
            """Main audit endpoint with common boilerplate."""
            return await self._handle_audit(request)

    async def _handle_audit(self, request: Request) -> Dict[str, Any]:
        """Internal handler for the /audit endpoint.

        This implements the common pattern shared by all auditors:
        1. Parse request payload
        2. Detect the audit phase (request, response, artifact, execution)
        3. Run the appropriate auditor check
        4. Handle the result (deny, redact, warn, proceed)
        5. Update lucid_context with this auditor's data
        6. Chain to next auditor or submit evidence to verifier

        Subclasses can override detect_phase() for custom phase detection.
        """
        payload = await request.json()
        lucid_context = payload.get("lucid_context", {})
        data = payload.get("data", payload)

        # Detect and run the appropriate phase
        result = self.detect_and_run_phase(data, lucid_context)

        # Handle deny - early return
        if result.decision.value == "deny":
            return {
                "status": "deny",
                "message": result.reason,
                "metadata": result.metadata,
                "session_id": self.config.session_id,
            }

        # Handle redact - apply modifications to data
        if result.decision.value == "redact" and result.modifications:
            data.update(result.modifications)

        # Update context with this auditor's results
        if result.data:
            lucid_context[self.config.auditor_id] = result.data

        # Chain to next auditor if configured
        next_auditor_url = os.getenv("AUDITOR_URL")
        if next_auditor_url:
            chain_result = await self.http_factory.chain_call(
                next_auditor_url, data, lucid_context
            )
            if chain_result:
                return chain_result
            # Chain failure - return appropriate status based on auditor type
            return self.build_chain_failure_response(result)

        # This is the last auditor - submit evidence to verifier
        await self.submit_evidence(data, result, lucid_context)

        # Build final response
        return self.build_response(data, result, lucid_context)

    def detect_and_run_phase(
        self,
        data: Dict[str, Any],
        lucid_context: Dict[str, Any],
    ) -> Any:
        """Detect the audit phase and run the appropriate check.

        Override this method for custom phase detection logic.

        Default detection:
        - "content" in data -> response phase
        - "partial_output" or "execution_step" in data -> execution phase
        - "model_id" with "benchmarks" or "artifact" -> artifact phase
        - Otherwise -> request phase

        Args:
            data: The request data payload.
            lucid_context: The Lucid context from previous auditors.

        Returns:
            AuditResult from the appropriate phase handler.
        """
        if self.auditor is None:
            from .auditor import Proceed
            return Proceed(error="Auditor not initialized")

        phase = self.detect_phase(data)

        if phase == "response":
            return self.auditor.check_response(data, lucid_context=lucid_context)
        elif phase == "execution":
            return self.auditor.check_execution(data, lucid_context=lucid_context)
        elif phase == "artifact":
            return self.auditor.check_artifact(data, lucid_context=lucid_context)
        else:  # request
            return self.auditor.check_request(data, lucid_context=lucid_context)

    def detect_phase(self, data: Dict[str, Any]) -> str:
        """Detect the audit phase from the data payload.

        Override this method for custom phase detection.

        Args:
            data: The request data payload.

        Returns:
            Phase string: "request", "response", "execution", or "artifact"
        """
        if "content" in data:
            return "response"
        elif "partial_output" in data or "execution_step" in data:
            return "execution"
        elif "model_id" in data and ("benchmarks" in data or "artifact" in data):
            return "artifact"
        else:
            return "request"

    def build_chain_failure_response(self, result: Any) -> Dict[str, Any]:
        """Build response when the auditor chain fails.

        Override for custom chain failure handling.

        Args:
            result: The audit result from this auditor.

        Returns:
            Response dict for chain failure.
        """
        # Default to deny on chain failure for security-critical auditors
        # Subclasses can override to use "warn" for non-blocking auditors
        return {"status": "deny", "message": "Chain failure"}

    async def submit_evidence(
        self,
        data: Dict[str, Any],
        result: Any,
        lucid_context: Dict[str, Any],
    ) -> None:
        """Submit evidence to the verifier.

        Override for custom evidence submission logic.

        Args:
            data: The request data payload.
            result: The audit result.
            lucid_context: The Lucid context.
        """
        nonce = data.get("nonce")
        model_id = data.get("model_id", self.config.model_id)

        metadata = self.build_evidence_metadata(result, lucid_context)

        await self.http_factory.submit_evidence(
            auditor_id=self.config.auditor_id,
            model_id=model_id,
            session_id=self.config.session_id,
            nonce=nonce,
            decision=result.decision.value,
            metadata=metadata,
        )

    def build_evidence_metadata(
        self,
        result: Any,
        lucid_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build metadata for evidence submission.

        Override to add custom metadata fields.

        Args:
            result: The audit result.
            lucid_context: The Lucid context.

        Returns:
            Metadata dict for evidence.
        """
        return result.metadata or {}

    def build_response(
        self,
        data: Dict[str, Any],
        result: Any,
        lucid_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build the final audit response.

        Override for custom response formatting.

        Args:
            data: The request data payload.
            result: The audit result.
            lucid_context: The Lucid context.

        Returns:
            Response dict.
        """
        return {
            "status": result.decision.value,
            "message": result.reason or "",
            "modifications": result.modifications,
            "metadata": result.metadata,
            "session_id": self.config.session_id,
            "lucid_context": lucid_context,
        }

    def run(self) -> None:
        """Run the auditor application."""
        run_auditor(self.app, self.config)


# Decorator for creating audit endpoints with common boilerplate
def audit_endpoint(
    auditor_getter: Callable[[], Any],
    config: BaseAuditorConfig,
    http_factory: HTTPClientFactory,
    logger: Any,
    phase_detector: Optional[Callable[[Dict[str, Any]], str]] = None,
    chain_failure_status: str = "deny",
):
    """Decorator factory for creating /audit endpoints with common boilerplate.

    This provides a more flexible alternative to BaseAuditorApp for auditors
    that need more control over their endpoint implementation.

    Args:
        auditor_getter: Function that returns the auditor instance.
        config: Auditor configuration.
        http_factory: HTTP client factory.
        logger: Logger instance.
        phase_detector: Optional custom phase detection function.
        chain_failure_status: Status to return on chain failure ("deny" or "warn").

    Returns:
        Decorator that wraps the endpoint function.

    Example:
        @app.post("/audit")
        @audit_endpoint(
            lambda: auditor,
            config,
            http_factory,
            logger,
            phase_detector=my_phase_detector,
        )
        async def handle_audit(request: Request) -> Dict[str, Any]:
            # Custom pre/post processing can go here
            pass
    """

    def default_phase_detector(data: Dict[str, Any]) -> str:
        if "content" in data:
            return "response"
        elif "partial_output" in data or "execution_step" in data:
            return "execution"
        elif "model_id" in data and ("benchmarks" in data or "artifact" in data):
            return "artifact"
        return "request"

    detector = phase_detector or default_phase_detector

    def decorator(func: Callable):
        async def wrapper(request: Request) -> Dict[str, Any]:
            auditor = auditor_getter()

            payload = await request.json()
            lucid_context = payload.get("lucid_context", {})
            data = payload.get("data", payload)

            # Detect phase and run check
            phase = detector(data)
            if phase == "response":
                result = auditor.check_response(data, lucid_context=lucid_context)
            elif phase == "execution":
                result = auditor.check_execution(data, lucid_context=lucid_context)
            elif phase == "artifact":
                result = auditor.check_artifact(data, lucid_context=lucid_context)
            else:
                result = auditor.check_request(data, lucid_context=lucid_context)

            # Handle deny
            if result.decision.value == "deny":
                return {
                    "status": "deny",
                    "message": result.reason,
                    "metadata": result.metadata,
                    "session_id": config.session_id,
                }

            # Handle redact
            if result.decision.value == "redact" and result.modifications:
                data.update(result.modifications)

            # Update context
            if result.data:
                lucid_context[config.auditor_id] = result.data

            # Chain to next auditor
            next_auditor_url = os.getenv("AUDITOR_URL")
            if next_auditor_url:
                chain_result = await http_factory.chain_call(
                    next_auditor_url, data, lucid_context
                )
                if chain_result:
                    return chain_result
                return {"status": chain_failure_status, "message": "Chain failure"}

            # Submit evidence
            nonce = data.get("nonce")
            model_id = data.get("model_id", config.model_id)
            await http_factory.submit_evidence(
                auditor_id=config.auditor_id,
                model_id=model_id,
                session_id=config.session_id,
                nonce=nonce,
                decision=result.decision.value,
                metadata=result.metadata or {},
            )

            return {
                "status": result.decision.value,
                "message": result.reason or "",
                "modifications": result.modifications,
                "metadata": result.metadata,
                "session_id": config.session_id,
                "lucid_context": lucid_context,
            }

        return wrapper

    return decorator


# Utility functions for common environment variable patterns


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Boolean value.
    """
    value = os.getenv(key, str(default).lower())
    return value.lower() == "true"


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get a float from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Float value.
    """
    return float(os.getenv(key, str(default)))


def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.

    Returns:
        Integer value.
    """
    return int(os.getenv(key, str(default)))


def get_env_list(key: str, default: str = "", separator: str = ",") -> list:
    """Get a list from environment variable.

    Args:
        key: Environment variable name.
        default: Default value if not set.
        separator: List item separator.

    Returns:
        List of strings.
    """
    value = os.getenv(key, default)
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]
