"""Resilience utilities for handling external service failures.

This module provides retry logic with exponential backoff and circuit breaker
patterns for external service calls, ensuring graceful degradation.

Pattern Selection Guide:
    Use retry_with_backoff when:
        - Transient failures are expected (network timeouts, 5xx errors)
        - The operation is idempotent (safe to retry)
        - You need automatic recovery from brief outages
        - Example: Submitting evidence to verifier, fetching model metadata

    Use circuit_breaker when:
        - Calling an external service that may be down for extended periods
        - You want to fail fast after detecting persistent failures
        - Preventing cascade failures is critical
        - Example: Third-party API calls, database connections

    Use resilient (combined) when:
        - You need both retry and circuit breaker protection
        - Calling critical external dependencies
        - Maximum fault tolerance is required
        - Example: Chain calls to next auditor, verifier submissions

    Use with_timeout when:
        - Operations must complete within a deadline
        - Preventing hung requests in the audit pipeline
        - Example: ML model inference calls

Error Recovery Examples:

    Basic retry for verifier calls::

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.5,
            retryable_exceptions=(httpx.TimeoutException, httpx.ConnectError),
        )
        async def submit_evidence(evidence: dict) -> bool:
            response = await client.post("/v1/evidence/verify", json=evidence)
            return response.status_code == 200

    Circuit breaker for external API::

        @circuit_breaker(
            name="openai_api",
            failure_threshold=5,      # Open after 5 failures
            recovery_timeout=60.0,    # Try recovery after 60s
            fallback=lambda *a: {"error": "service_unavailable"},
        )
        async def call_external_classifier(text: str) -> dict:
            return await external_api.classify(text)

    Full resilience for critical paths::

        @resilient(
            circuit_name="verifier",
            max_retries=3,
            timeout=10.0,
            fallback=async_safe_default,
        )
        async def critical_verification(data: dict) -> VerifyResult:
            return await verifier.verify(data)

Metrics and Monitoring:
    Use get_circuit_status() to expose circuit breaker state::

        @app.get("/metrics/circuits")
        async def circuit_metrics():
            return get_circuit_status()
            # Returns: {"verifier": {"state": "closed", "failure_count": 0, ...}}

    Use reset_circuit(name) for manual recovery during incidents.

Usage:
    from lucid_sdk import retry_with_backoff, circuit_breaker, resilient

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def call_external_service():
        ...

    @circuit_breaker("location_service", failure_threshold=5, recovery_timeout=60)
    async def verify_location():
        ...
"""

import asyncio
import functools
import time
from typing import Callable, TypeVar, Any, Optional, Type, Dict
from dataclasses import dataclass
from enum import Enum
import structlog

log = structlog.get_logger()

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"      # Failing, requests are rejected immediately
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerState:
    """State tracking for a circuit breaker."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: float = 0
    failure_threshold: int = 5
    recovery_timeout: float = 60.0  # seconds
    half_open_max_calls: int = 3

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_max_calls:
                self._transition_to_closed()
        else:
            self.failure_count = 0  # Reset failures on success

    def record_failure(self) -> None:
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = time.monotonic()

        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.failure_count >= self.failure_threshold:
            self._transition_to_open()

    def should_allow_request(self) -> bool:
        """Check if a request should be allowed through."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.monotonic() - self.last_failure_time >= self.recovery_timeout:
                self._transition_to_half_open()
                return True
            return False

        # HALF_OPEN - allow limited requests
        return True

    def _transition_to_open(self) -> None:
        """Transition to open state."""
        log.warning(
            "circuit_breaker_opened",
            circuit=self.name,
            failure_count=self.failure_count,
        )
        self.state = CircuitState.OPEN
        self.success_count = 0

    def _transition_to_half_open(self) -> None:
        """Transition to half-open state."""
        log.info(
            "circuit_breaker_half_open",
            circuit=self.name,
            recovery_timeout=self.recovery_timeout,
        )
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.failure_count = 0

    def _transition_to_closed(self) -> None:
        """Transition to closed state."""
        log.info(
            "circuit_breaker_closed",
            circuit=self.name,
            success_count=self.success_count,
        )
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreakerState] = {}


def get_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
) -> CircuitBreakerState:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreakerState(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
    return _circuit_breakers[name]


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""

    def __init__(self, circuit_name: str):
        self.circuit_name = circuit_name
        super().__init__(f"Circuit breaker '{circuit_name}' is open")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retry logic with exponential backoff.

    Use this decorator when:
        - Operations may fail transiently (network timeouts, temporary 5xx errors)
        - The operation is idempotent (safe to retry without side effects)
        - You expect brief outages that resolve quickly
        - External services have rate limits that clear after a delay

    Do NOT use when:
        - The operation has side effects that cannot be safely repeated
        - Failures are deterministic (e.g., validation errors, 4xx responses)
        - You need to fail fast for time-sensitive operations

    Args:
        max_retries: Maximum number of retry attempts. Default 3 gives 4 total
            attempts (1 initial + 3 retries). For critical operations, consider
            5-10 retries with longer delays.
        base_delay: Initial delay between retries in seconds. The delay doubles
            with each attempt (exponential backoff). Default 1.0s is suitable
            for most HTTP calls.
        max_delay: Maximum delay cap in seconds. Prevents extremely long waits
            after many retries. Default 30s is reasonable for background tasks.
        exponential_base: Multiplier for backoff calculation. Default 2.0 means
            delays of 1s, 2s, 4s, 8s, etc. Use 1.5 for gentler backoff.
        jitter: Add randomness to delays (up to 25%) to prevent thundering herd
            when multiple clients retry simultaneously. Recommended True.
        retryable_exceptions: Tuple of exception types that trigger retries.
            Non-matching exceptions propagate immediately. Always be specific
            about which errors warrant retries.

    Returns:
        Decorated async function with retry logic.

    Raises:
        The original exception after all retry attempts are exhausted.

    Example - Verifier submission with specific retryable errors::

        import httpx

        @retry_with_backoff(
            max_retries=5,
            base_delay=0.5,
            max_delay=15.0,
            retryable_exceptions=(
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.HTTPStatusError,  # For 5xx errors, filter in function
            ),
        )
        async def submit_to_verifier(evidence: dict) -> dict:
            response = await client.post("/api/v1/evidence", json=evidence)
            if response.status_code >= 500:
                # Raise to trigger retry for server errors
                response.raise_for_status()
            elif response.status_code >= 400:
                # Don't retry client errors - they're deterministic
                return {"error": response.json()}
            return response.json()

    Example - Retry with custom exception filtering::

        class TransientDatabaseError(Exception):
            pass

        @retry_with_backoff(
            max_retries=3,
            base_delay=0.1,
            retryable_exceptions=(TransientDatabaseError, ConnectionResetError),
        )
        async def fetch_from_database(query: str) -> list:
            try:
                return await db.execute(query)
            except DatabaseError as e:
                if "deadlock" in str(e).lower():
                    raise TransientDatabaseError(str(e)) from e
                raise  # Non-transient errors propagate immediately

    Logging:
        This decorator logs retry attempts and exhaustion via structlog:
        - ``retry_attempt``: Logged at WARNING level for each retry
        - ``retry_exhausted``: Logged at ERROR level when all retries fail
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        log.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e),
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay,
                    )

                    # Add jitter (up to 25% of delay)
                    if jitter:
                        import random
                        delay = delay * (0.75 + random.random() * 0.5)

                    log.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay=delay,
                        error=str(e),
                    )

                    await asyncio.sleep(delay)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry_with_backoff")

        return wrapper  # type: ignore[return-value]

    return decorator


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    fallback: Optional[Callable[..., Any]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for circuit breaker pattern.

    The circuit breaker prevents cascade failures by failing fast when a
    downstream service is unhealthy. It tracks failures and "opens" the circuit
    to reject requests immediately, allowing the failing service time to recover.

    Circuit States:
        - **CLOSED**: Normal operation. Requests pass through. Failures are counted.
        - **OPEN**: Service is failing. Requests are rejected immediately or routed
          to fallback. No load is sent to the failing service.
        - **HALF_OPEN**: Testing recovery. A limited number of requests are allowed
          through. If they succeed, circuit closes. If they fail, circuit reopens.

    Use this decorator when:
        - Calling external services that may have extended outages
        - You want to fail fast rather than wait for timeouts
        - Preventing cascade failures to upstream services is critical
        - You have a meaningful fallback response for degraded operation

    Do NOT use when:
        - Failures should always be retried immediately
        - There's no meaningful fallback behavior
        - The operation is purely internal with predictable behavior

    Args:
        name: Unique identifier for this circuit breaker. Use descriptive names
            like "openai_api", "verifier_submit", or "postgres_read". Circuit
            state is shared across all decorators with the same name.
        failure_threshold: Consecutive failures before opening circuit. Lower
            values (2-3) for critical paths, higher (5-10) for flaky services.
        recovery_timeout: Seconds before attempting recovery (half-open state).
            Match this to your service's typical recovery time. Shorter (30s)
            for fast-recovering services, longer (300s) for slow restarts.
        fallback: Function called when circuit is open. Can be sync or async.
            Should return a safe default or cached value. If None, raises
            CircuitBreakerOpen exception.

    Returns:
        Decorated async function with circuit breaker logic.

    Raises:
        CircuitBreakerOpen: When circuit is open and no fallback is provided.

    Example - External API with fallback::

        async def cached_classification(text: str) -> dict:
            '''Return cached or default classification when API is down.'''
            cached = await cache.get(f"classify:{hash(text)}")
            if cached:
                return cached
            return {"classification": "unknown", "confidence": 0.0, "degraded": True}

        @circuit_breaker(
            name="classifier_api",
            failure_threshold=3,
            recovery_timeout=120.0,
            fallback=cached_classification,
        )
        async def classify_text(text: str) -> dict:
            response = await external_api.post("/classify", json={"text": text})
            result = response.json()
            await cache.set(f"classify:{hash(text)}", result, ttl=3600)
            return result

    Example - Critical path without fallback::

        @circuit_breaker(
            name="payment_processor",
            failure_threshold=2,  # Open quickly for payment failures
            recovery_timeout=300.0,  # Wait 5 min before retry
        )
        async def process_payment(order_id: str, amount: float) -> dict:
            # CircuitBreakerOpen raised if circuit is open
            return await payment_api.charge(order_id, amount)

        # Caller handles the exception
        try:
            result = await process_payment(order_id, 99.99)
        except CircuitBreakerOpen:
            await notify_user("Payment system temporarily unavailable")
            await queue_for_retry(order_id, amount)

    Monitoring:
        Use ``get_circuit_status()`` to expose circuit state to monitoring:

        .. code-block:: python

            @app.get("/health/circuits")
            async def circuit_health():
                status = get_circuit_status()
                # Returns: {"classifier_api": {"state": "closed", ...}}
                unhealthy = [n for n, s in status.items() if s["state"] != "closed"]
                return {"circuits": status, "unhealthy": unhealthy}
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            cb = get_circuit_breaker(name, failure_threshold, recovery_timeout)

            if not cb.should_allow_request():
                log.warning(
                    "circuit_breaker_rejected",
                    circuit=name,
                    state=cb.state.value,
                )
                if fallback:
                    if asyncio.iscoroutinefunction(fallback):
                        return await fallback(*args, **kwargs)
                    return fallback(*args, **kwargs)
                raise CircuitBreakerOpen(name)

            try:
                result = await func(*args, **kwargs)
                cb.record_success()
                return result
            except Exception:
                cb.record_failure()
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


def with_timeout(timeout_seconds: float) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to add timeout to async functions.

    Use this decorator when:
        - Operations must complete within a strict deadline
        - Preventing hung requests that block the audit pipeline
        - Enforcing SLAs for ML model inference or external API calls
        - You need predictable latency bounds

    Args:
        timeout_seconds: Maximum time to wait for function completion.
            Choose based on your operation's expected latency:
            - Fast operations (cache lookups): 0.5-2s
            - HTTP calls: 5-30s
            - ML inference: 30-120s
            - Batch processing: 300-600s

    Returns:
        Decorated async function with timeout.

    Raises:
        asyncio.TimeoutError: If the operation exceeds the timeout.

    Example - ML inference with timeout::

        @with_timeout(60.0)  # 1 minute max for inference
        async def run_model_inference(input_data: dict) -> dict:
            return await model.predict(input_data)

        try:
            result = await run_model_inference(data)
        except asyncio.TimeoutError:
            log.error("Model inference timed out", input_size=len(data))
            result = {"error": "inference_timeout", "fallback": True}

    Example - Combining with retry for robust timeout handling::

        @retry_with_backoff(
            max_retries=2,
            retryable_exceptions=(asyncio.TimeoutError,),
        )
        @with_timeout(10.0)
        async def fetch_with_deadline(url: str) -> dict:
            '''Fetch URL with 10s timeout, retry up to 2 times on timeout.'''
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                return response.json()

    Logging:
        Logs ``operation_timeout`` at ERROR level when timeout occurs.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                log.error(
                    "operation_timeout",
                    function=func.__name__,
                    timeout=timeout_seconds,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


# Combined decorator for common patterns
def resilient(
    circuit_name: Optional[str] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    timeout: Optional[float] = None,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    fallback: Optional[Callable[..., Any]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Combined decorator for resilient external service calls.

    This decorator applies multiple resilience patterns in the optimal order:
    1. Circuit breaker (outermost) - Fails fast if service is known to be down
    2. Retry with backoff - Handles transient failures
    3. Timeout (innermost) - Ensures bounded execution time

    Use this decorator when:
        - Calling critical external dependencies (verifier, next auditor in chain)
        - Maximum fault tolerance is required for the operation
        - You want a single decorator instead of stacking multiple decorators
        - The operation is important enough to warrant full protection

    Execution flow:
        1. Request arrives at circuit breaker
        2. If circuit OPEN: return fallback or raise CircuitBreakerOpen
        3. If circuit CLOSED/HALF_OPEN: proceed to retry logic
        4. Retry logic attempts the operation (with timeout if specified)
        5. On success: circuit records success, returns result
        6. On failure: retry with backoff until exhausted
        7. After all retries fail: circuit records failure, raises exception

    Args:
        circuit_name: Unique name for circuit breaker. Defaults to the decorated
            function's name. Use explicit names when the same logical service
            is called from multiple functions.
        max_retries: Maximum retry attempts for transient failures. Each retry
            uses exponential backoff starting from base_delay.
        base_delay: Initial delay between retries in seconds. Subsequent delays
            double (1s, 2s, 4s, ...) up to 30s max.
        timeout: Optional timeout per attempt in seconds. Applied to each retry
            attempt individually, not the total operation time.
        failure_threshold: Consecutive failures before circuit opens. Lower for
            critical paths (2-3), higher for flaky services (5-10).
        recovery_timeout: Seconds before circuit transitions to half-open and
            allows test requests through.
        fallback: Async or sync function called when circuit is open. Should
            return a safe degraded response. If None, CircuitBreakerOpen is raised.

    Returns:
        Decorated async function with full resilience pattern.

    Raises:
        CircuitBreakerOpen: If circuit is open and no fallback provided.
        asyncio.TimeoutError: If timeout specified and all attempts timeout.
        Exception: The underlying exception after retries are exhausted.

    Example - Verifier submission with full resilience::

        async def fallback_queue_evidence(evidence: dict) -> dict:
            '''Queue evidence for later submission when verifier is down.'''
            await evidence_queue.put(evidence)
            return {"status": "queued", "degraded": True}

        @resilient(
            circuit_name="verifier_submit",
            max_retries=3,
            base_delay=1.0,
            timeout=30.0,
            failure_threshold=5,
            recovery_timeout=120.0,
            fallback=fallback_queue_evidence,
        )
        async def submit_evidence(evidence: dict) -> dict:
            '''Submit evidence to verifier with full resilience.'''
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{VERIFIER_URL}/api/v1/evidence",
                    json=evidence,
                )
                response.raise_for_status()
                return response.json()

    Example - Chain call to next auditor::

        @resilient(
            circuit_name="auditor_chain",
            max_retries=5,
            timeout=60.0,
            fallback=lambda req: AuditResult(status="skipped", reason="next_auditor_unavailable"),
        )
        async def call_next_auditor(request: AuditRequest) -> AuditResult:
            '''Forward request to next auditor in chain.'''
            return await next_auditor_client.audit(request)

    Example - Database operation with short timeout::

        @resilient(
            circuit_name="postgres_write",
            max_retries=2,
            base_delay=0.1,
            timeout=5.0,
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        async def save_audit_result(result: dict) -> None:
            '''Save audit result to database.'''
            await db.execute(
                "INSERT INTO audit_results (data) VALUES ($1)",
                json.dumps(result),
            )

    Metrics Setup:
        Expose circuit breaker metrics for monitoring dashboards:

        .. code-block:: python

            from lucid_sdk import get_circuit_status, reset_circuit

            @app.get("/metrics/resilience")
            async def resilience_metrics():
                '''Expose circuit breaker states for Prometheus/Grafana.'''
                circuits = get_circuit_status()
                return {
                    "circuits": circuits,
                    "open_circuits": [
                        name for name, state in circuits.items()
                        if state["state"] == "open"
                    ],
                    "total_failures": sum(
                        s["failure_count"] for s in circuits.values()
                    ),
                }

            @app.post("/admin/circuits/{name}/reset")
            async def manual_reset(name: str):
                '''Manual circuit reset for incident recovery.'''
                if reset_circuit(name):
                    return {"status": "reset", "circuit": name}
                return {"status": "not_found", "circuit": name}

    Error Recovery Guide:
        When circuits open frequently, investigate:

        1. **Check downstream service health** - Is the service actually down?
        2. **Review timeout settings** - Are timeouts too aggressive?
        3. **Analyze failure patterns** - Are failures transient or persistent?
        4. **Consider fallback quality** - Is the fallback providing value?
        5. **Adjust thresholds** - May need higher threshold for flaky services

        Manual recovery during incidents:

        .. code-block:: python

            # Force circuit closed after confirming service recovery
            reset_circuit("verifier_submit")

            # Or via admin endpoint
            await httpx.post("/admin/circuits/verifier_submit/reset")
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Build decorator stack from inside out
        result = func

        # First: timeout (innermost)
        if timeout:
            result = with_timeout(timeout)(result)

        # Second: retry with backoff
        result = retry_with_backoff(
            max_retries=max_retries,
            base_delay=base_delay,
        )(result)

        # Third: circuit breaker (outermost)
        cb_name = circuit_name or func.__name__
        result = circuit_breaker(
            name=cb_name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            fallback=fallback,
        )(result)

        return result

    return decorator


def get_circuit_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all circuit breakers for monitoring.

    Returns a dictionary of all registered circuit breakers and their current
    state. Use this for health checks, metrics endpoints, and dashboards.

    Returns:
        Dictionary mapping circuit names to their state information:
        - state: Current state ("closed", "open", or "half_open")
        - failure_count: Number of consecutive failures
        - success_count: Successes in half-open state (for recovery tracking)
        - failure_threshold: Configured failure threshold
        - recovery_timeout: Configured recovery timeout in seconds

    Example - Prometheus metrics endpoint::

        from prometheus_client import Gauge

        circuit_state = Gauge(
            'circuit_breaker_state',
            'Circuit breaker state (0=closed, 1=half_open, 2=open)',
            ['circuit_name']
        )
        circuit_failures = Gauge(
            'circuit_breaker_failures',
            'Current failure count',
            ['circuit_name']
        )

        @app.get("/metrics")
        async def metrics():
            for name, status in get_circuit_status().items():
                state_value = {"closed": 0, "half_open": 1, "open": 2}
                circuit_state.labels(circuit_name=name).set(
                    state_value[status["state"]]
                )
                circuit_failures.labels(circuit_name=name).set(
                    status["failure_count"]
                )
            return generate_latest()

    Example - Health check endpoint::

        @app.get("/health")
        async def health_check():
            circuits = get_circuit_status()
            open_circuits = [
                name for name, s in circuits.items()
                if s["state"] == "open"
            ]

            if open_circuits:
                return JSONResponse(
                    status_code=503,
                    content={
                        "status": "degraded",
                        "open_circuits": open_circuits,
                        "message": "Some downstream services are unavailable",
                    }
                )

            return {"status": "healthy", "circuits": len(circuits)}
    """
    return {
        name: {
            "state": cb.state.value,
            "failure_count": cb.failure_count,
            "success_count": cb.success_count,
            "failure_threshold": cb.failure_threshold,
            "recovery_timeout": cb.recovery_timeout,
        }
        for name, cb in _circuit_breakers.items()
    }


def reset_circuit(name: str) -> bool:
    """Manually reset a circuit breaker to closed state.

    Use this for manual recovery during incidents when you have confirmed
    the downstream service has recovered but the circuit hasn't automatically
    transitioned yet.

    Args:
        name: The circuit breaker name to reset.

    Returns:
        True if the circuit was found and reset, False if not found.

    Warning:
        Only use this after confirming the downstream service is healthy.
        Resetting a circuit while the service is still failing will cause
        a burst of failed requests before the circuit reopens.

    Example - Admin endpoint for incident recovery::

        @app.post("/admin/circuits/{circuit_name}/reset")
        async def reset_circuit_endpoint(
            circuit_name: str,
            api_key: str = Header(...),
        ):
            # Verify admin authorization
            if not verify_admin_key(api_key):
                raise HTTPException(status_code=403)

            if reset_circuit(circuit_name):
                log.info(
                    "circuit_manually_reset_by_admin",
                    circuit=circuit_name,
                )
                return {
                    "status": "reset",
                    "circuit": circuit_name,
                    "new_state": "closed",
                }

            return JSONResponse(
                status_code=404,
                content={"error": f"Circuit '{circuit_name}' not found"}
            )

    Example - Automated recovery after health check passes::

        async def check_and_recover_circuits():
            '''Periodically check if services recovered and reset circuits.'''
            for name, status in get_circuit_status().items():
                if status["state"] == "open":
                    # Check if downstream service is healthy
                    if await health_check_for_circuit(name):
                        reset_circuit(name)
                        log.info("circuit_auto_recovered", circuit=name)
    """
    if name in _circuit_breakers:
        cb = _circuit_breakers[name]
        cb.state = CircuitState.CLOSED
        cb.failure_count = 0
        cb.success_count = 0
        log.info("circuit_breaker_manually_reset", circuit=name)
        return True
    return False
