"""ZK-specific exceptions for the Lucid SDK.

Provides a standardized set of exceptions for ZK proof generation and verification.
"""
from typing import Any, Dict, Optional
from ..exceptions import LucidError


class ZKError(LucidError):
    """Base exception for all ZK-related errors.

    All ZK exceptions inherit from this class, making it easy to catch
    all ZK-related errors with a single except clause.
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code or "ZK_ERROR", details)


class ZKNotAvailableError(ZKError):
    """Exception raised when ZK dependencies are not installed.

    Install the ZK extras with: pip install lucid-sdk[zk]
    """

    def __init__(
        self,
        message: str = "ZK functionality requires additional dependencies. Install with: pip install lucid-sdk[zk]",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "ZK_NOT_AVAILABLE", details)


class ZKCircuitError(ZKError):
    """Exception raised during circuit operations.

    Use this for errors loading circuits, verification keys, or WASM files.

    Attributes:
        circuit_id: ID of the circuit that caused the error.
        file_path: Path to the file that caused the error.
    """

    def __init__(
        self,
        message: str,
        circuit_id: Optional[str] = None,
        file_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if circuit_id:
            details["circuit_id"] = circuit_id
        if file_path:
            details["file_path"] = file_path

        super().__init__(message, "ZK_CIRCUIT_ERROR", details)
        self.circuit_id = circuit_id
        self.file_path = file_path


class ZKProvingError(ZKError):
    """Exception raised during proof generation.

    Use this for errors that occur during the proving process,
    such as invalid inputs or computation failures.

    Attributes:
        circuit_id: ID of the circuit being proven.
        input_name: Name of the input that caused the error.
    """

    def __init__(
        self,
        message: str,
        circuit_id: Optional[str] = None,
        input_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if circuit_id:
            details["circuit_id"] = circuit_id
        if input_name:
            details["input_name"] = input_name

        super().__init__(message, "ZK_PROVING_ERROR", details)
        self.circuit_id = circuit_id
        self.input_name = input_name


class ZKVerificationError(ZKError):
    """Exception raised during proof verification.

    Use this for errors that occur during verification,
    such as invalid proofs or mismatched public inputs.

    Attributes:
        proof_id: ID of the proof that failed verification.
        circuit_id: ID of the circuit used for verification.
        reason: Specific reason for verification failure.
    """

    def __init__(
        self,
        message: str,
        proof_id: Optional[str] = None,
        circuit_id: Optional[str] = None,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if proof_id:
            details["proof_id"] = proof_id
        if circuit_id:
            details["circuit_id"] = circuit_id
        if reason:
            details["reason"] = reason

        super().__init__(message, "ZK_VERIFICATION_ERROR", details)
        self.proof_id = proof_id
        self.circuit_id = circuit_id
        self.reason = reason


class ZKInputError(ZKError):
    """Exception raised for invalid ZK inputs.

    Use this for input validation errors, missing required inputs,
    or inputs that don't match the circuit's expected format.

    Attributes:
        input_name: Name of the invalid input.
        expected_type: Expected type or format.
        actual_value: The actual value provided.
    """

    def __init__(
        self,
        message: str,
        input_name: Optional[str] = None,
        expected_type: Optional[str] = None,
        actual_value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        if input_name:
            details["input_name"] = input_name
        if expected_type:
            details["expected_type"] = expected_type
        if actual_value is not None:
            details["actual_value"] = str(actual_value)

        super().__init__(message, "ZK_INPUT_ERROR", details)
        self.input_name = input_name
        self.expected_type = expected_type
        self.actual_value = actual_value
