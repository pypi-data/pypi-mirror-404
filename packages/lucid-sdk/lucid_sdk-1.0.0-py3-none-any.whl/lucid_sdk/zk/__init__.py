"""Zero-Knowledge Proof module for the Lucid SDK.

This module provides functionality for generating and verifying zero-knowledge
proofs in auditors, enabling verifiable computation without revealing sensitive data.

Installation:
    pip install lucid-sdk[zk]

Usage:
    ```python
    from lucid_sdk.zk import ZKCircuit, ZKProof, ZKEvidence
    from lucid_schemas import MeasurementType

    # Load a circuit
    circuit = ZKCircuit.from_files(
        circuit_id="pii-detector-v1",
        proving_key_path="./circuits/pii_detector.zkey",
        verification_key_path="./circuits/pii_detector_vkey.json",
        wasm_path="./circuits/pii_detector.wasm",
    )

    # Generate a proof
    proof = circuit.prove(
        private_inputs={"input_hash": 12345},
        public_inputs={"threshold": 50},
    )

    # Verify the proof
    is_valid = circuit.verify(proof)

    # Or use ZKEvidence for integrated workflow
    zk_evidence = ZKEvidence(
        name="pii_score",
        measurement_type=MeasurementType.quantity,
        circuit=circuit,
        auditor_id="pii-auditor",
    )
    evidence = zk_evidence.create_evidence(
        value={"detected": False},
        private_inputs={"input_hash": 12345},
    )
    ```

Exceptions:
    ZKError: Base exception for all ZK errors.
    ZKNotAvailableError: ZK dependencies not installed.
    ZKCircuitError: Error loading or using circuit.
    ZKProvingError: Error generating proof.
    ZKVerificationError: Error verifying proof.
    ZKInputError: Invalid input to circuit.
"""
from .exceptions import (
    ZKError,
    ZKNotAvailableError,
    ZKCircuitError,
    ZKProvingError,
    ZKVerificationError,
    ZKInputError,
)
from .circuit import ZKCircuit
from .proof import ZKProof
from .evidence import ZKEvidence


def is_snarkjs_available() -> bool:
    """Check if snarkjs is available for ZK functionality.

    Returns:
        True if snarkjs is installed and importable, False otherwise.
    """
    try:
        import snarkjs  # noqa: F401
        return True
    except ImportError:
        return False


__all__ = [
    # Classes
    "ZKCircuit",
    "ZKProof",
    "ZKEvidence",
    # Exceptions
    "ZKError",
    "ZKNotAvailableError",
    "ZKCircuitError",
    "ZKProvingError",
    "ZKVerificationError",
    "ZKInputError",
    # Utilities
    "is_snarkjs_available",
]
