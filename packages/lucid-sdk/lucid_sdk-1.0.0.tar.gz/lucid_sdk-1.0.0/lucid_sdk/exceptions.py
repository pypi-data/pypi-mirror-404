"""
Lucid SDK Exception Hierarchy

Provides a standardized set of exceptions for consistent error handling across
all Lucid services (auditors, verifier, operator, etc.).

Exception Hierarchy:
    LucidError (base)
    ├── AuditorError - Errors in auditor processing
    │   ├── ValidationError - Input validation failures
    │   └── ChainError - Auditor chain execution errors
    ├── ConfigurationError - Configuration and environment errors
    ├── AttestationError - TEE attestation failures
    ├── HTTPError - HTTP communication errors
    │   └── RetryableError - Transient errors that can be retried

Usage:
    from lucid_sdk.exceptions import AuditorError, ValidationError

    try:
        result = auditor.process(request)
    except ValidationError as e:
        logger.warning("validation_failed", error=str(e), field=e.field)
        return Deny(reason=str(e))
    except AuditorError as e:
        logger.error("auditor_error", error=str(e))
        raise
"""

from typing import Any, Dict, Optional


class LucidError(Exception):
    """Base exception for all Lucid SDK errors.

    All Lucid exceptions inherit from this class, making it easy to catch
    all Lucid-related errors with a single except clause.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code for categorization.
        details: Additional context about the error.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "LUCID_ERROR"
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details
        }

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class AuditorError(LucidError):
    """Exception raised during auditor processing.

    Use this for errors that occur during the audit evaluation process,
    such as model inference failures or policy evaluation errors.

    Attributes:
        auditor_id: ID of the auditor that raised the error.
        phase: Audit phase where error occurred (request, response, etc.).
    """

    def __init__(
        self,
        message: str,
        auditor_id: Optional[str] = None,
        phase: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code or "AUDITOR_ERROR", details)
        self.auditor_id = auditor_id
        self.phase = phase

    def to_dict(self) -> Dict[str, Any]:
        result = super().to_dict()
        if self.auditor_id:
            result["auditor_id"] = self.auditor_id
        if self.phase:
            result["phase"] = self.phase
        return result


class ValidationError(AuditorError):
    """Exception raised when input validation fails.

    Use this for schema validation errors, missing required fields,
    or invalid input formats.

    Attributes:
        field: Name of the field that failed validation.
        expected: Expected value or format.
        actual: Actual value received.
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        expected: Optional[Any] = None,
        actual: Optional[Any] = None,
        auditor_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if field:
            details["field"] = field
        if expected is not None:
            details["expected"] = str(expected)
        if actual is not None:
            details["actual"] = str(actual)

        super().__init__(
            message,
            auditor_id=auditor_id,
            error_code="VALIDATION_ERROR",
            details=details
        )
        self.field = field
        self.expected = expected
        self.actual = actual


class ChainError(AuditorError):
    """Exception raised during auditor chain execution.

    Use this for errors in the auditor chain coordination, such as
    chain forwarding failures or inter-auditor communication issues.

    Attributes:
        chain_position: Position in the chain where error occurred.
        failed_auditor: ID of the auditor that failed.
    """

    def __init__(
        self,
        message: str,
        chain_position: Optional[int] = None,
        failed_auditor: Optional[str] = None,
        auditor_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if chain_position is not None:
            details["chain_position"] = chain_position
        if failed_auditor:
            details["failed_auditor"] = failed_auditor

        super().__init__(
            message,
            auditor_id=auditor_id,
            error_code="CHAIN_ERROR",
            details=details
        )
        self.chain_position = chain_position
        self.failed_auditor = failed_auditor


class ConfigurationError(LucidError):
    """Exception raised for configuration errors.

    Use this for missing environment variables, invalid configuration
    values, or incompatible settings.

    Attributes:
        config_key: The configuration key that caused the error.
        config_source: Source of the configuration (env, file, etc.).
    """

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if config_key:
            details["config_key"] = config_key
        if config_source:
            details["config_source"] = config_source

        super().__init__(message, "CONFIGURATION_ERROR", details)
        self.config_key = config_key
        self.config_source = config_source


class AttestationError(LucidError):
    """Exception raised for TEE attestation failures.

    Use this for attestation validation failures, quote generation
    errors, or TEE communication issues.

    Attributes:
        tee_provider: TEE provider (e.g., "COCO", "SGX", "SEV").
        attestation_type: Type of attestation that failed.
    """

    def __init__(
        self,
        message: str,
        tee_provider: Optional[str] = None,
        attestation_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if tee_provider:
            details["tee_provider"] = tee_provider
        if attestation_type:
            details["attestation_type"] = attestation_type

        super().__init__(message, "ATTESTATION_ERROR", details)
        self.tee_provider = tee_provider
        self.attestation_type = attestation_type


class HTTPError(LucidError):
    """Exception raised for HTTP communication errors.

    Use this for network failures, timeout errors, or unexpected
    HTTP response codes.

    Attributes:
        status_code: HTTP status code (if available).
        url: URL that was being accessed.
        method: HTTP method used.
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if status_code is not None:
            details["status_code"] = status_code
        if url:
            details["url"] = url
        if method:
            details["method"] = method

        super().__init__(message, "HTTP_ERROR", details)
        self.status_code = status_code
        self.url = url
        self.method = method


class RetryableError(HTTPError):
    """Exception for transient errors that can be retried.

    Use this for temporary failures like network timeouts, rate limiting,
    or service unavailability that may succeed on retry.

    Attributes:
        retry_after: Suggested wait time before retry (seconds).
        attempts: Number of attempts made so far.
        max_attempts: Maximum retry attempts allowed.
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[float] = None,
        attempts: int = 0,
        max_attempts: Optional[int] = None,
        status_code: Optional[int] = None,
        url: Optional[str] = None,
        method: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if retry_after is not None:
            details["retry_after"] = retry_after
        details["attempts"] = attempts
        if max_attempts is not None:
            details["max_attempts"] = max_attempts

        super().__init__(
            message,
            status_code=status_code,
            url=url,
            method=method,
            details=details
        )
        self.error_code = "RETRYABLE_ERROR"
        self.retry_after = retry_after
        self.attempts = attempts
        self.max_attempts = max_attempts

    @property
    def should_retry(self) -> bool:
        """Check if another retry attempt should be made."""
        if self.max_attempts is None:
            return True
        return self.attempts < self.max_attempts
