"""ZK Evidence helper for creating Evidence with ZK proofs.

This module provides the ZKEvidence class for easily creating Evidence
objects that include zero-knowledge proofs of computation.

ZK Integration Requirements
===========================

To use ZK-based evidence, you must have:

1. **Circuit Files**: A compiled ZK circuit (R1CS/WASM for Groth16 or equivalent).
   Circuits define the computation being proven and must be pre-compiled before
   use. See :class:`ZKCircuit` for loading circuits.

2. **Proving Key**: The proving key generated during circuit setup (trusted setup
   for Groth16). This is required for proof generation and should be kept secure.

3. **Verification Key**: The verification key must be registered with the Verifier
   service so it can verify proofs. Register via the Verifier API before submitting
   evidence.

Verification Flow
-----------------

When the Verifier receives Evidence with a `zk_proof` field:

1. It extracts the ``zk_proof`` field containing the serialized proof
2. Looks up the verification key by circuit ID from the proof metadata
3. Verifies the proof against the public inputs
4. If valid, the evidence is accepted; otherwise rejected

Example Setup
-------------

.. code-block:: python

    from lucid_sdk.zk import ZKCircuit, ZKEvidence
    from lucid_schemas import MeasurementType

    # 1. Load your compiled circuit
    circuit = ZKCircuit.from_files(
        circuit_path="./circuits/pii_detector.r1cs",
        proving_key_path="./circuits/pii_detector.pk",
        verification_key_path="./circuits/pii_detector.vk",
    )

    # 2. Register verification key with Verifier (one-time setup)
    # await verifier_client.register_verification_key(
    #     circuit_id=circuit.circuit_id,
    #     verification_key=circuit.verification_key,
    # )

    # 3. Create ZKEvidence helper
    zk_evidence = ZKEvidence(
        name="pii_detection",
        measurement_type=MeasurementType.quantity,
        circuit=circuit,
        auditor_id="pii-auditor@sha256:abc123",
    )

    # 4. Generate evidence with proofs
    evidence = zk_evidence.create_evidence(
        value={"pii_detected": False, "score": 0.0},
        private_inputs={"input_text_hash": hash_value},
        public_inputs={"threshold": 0.5},
    )
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union
import uuid

from lucid_schemas import Claim, Evidence, MeasurementType, EvidenceSource

from .circuit import ZKCircuit
from .proof import ZKProof


class ZKEvidence:
    """Helper for creating Evidence with ZK proofs.

    This class simplifies the process of creating Evidence objects that
    include zero-knowledge proofs attesting to the computation.

    Usage:
        ```python
        circuit = ZKCircuit.from_files(...)
        zk_evidence = ZKEvidence(
            name="pii_detection",
            measurement_type=MeasurementType.quantity,
            circuit=circuit,
            auditor_id="pii-auditor@sha256:abc123",
        )

        evidence = zk_evidence.create_evidence(
            value={"pii_detected": False, "score": 0.0},
            private_inputs={"input_text_hash": hash_value},
            public_inputs={"threshold": 0.5},
        )
        ```

    Attributes:
        name: Name for the claim within the evidence.
        measurement_type: Type of measurement.
        circuit: ZKCircuit to use for proof generation.
        auditor_id: Auditor identifier (attester).
    """

    def __init__(
        self,
        name: str,
        measurement_type: MeasurementType,
        circuit: ZKCircuit,
        auditor_id: str,
    ):
        self.name = name
        self.measurement_type = measurement_type
        self.circuit = circuit
        self.auditor_id = auditor_id

    def create_evidence(
        self,
        value: Union[str, float, bool, Dict[str, Any]],
        private_inputs: Dict[str, Any],
        public_inputs: Optional[Dict[str, Any]] = None,
        phase: str = "request",
        nonce: Optional[str] = None,
        confidence: float = 1.0,
        compliance_framework: Optional[str] = None,
        control_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
    ) -> Evidence:
        """Create an Evidence bundle with an attached ZK proof.

        This method generates a ZK proof using the provided inputs and creates
        an Evidence object that includes both the claim value and the
        cryptographic proof.

        Args:
            value: The claim value.
            private_inputs: Private inputs for proof generation (not revealed).
            public_inputs: Public inputs for proof generation.
            phase: Execution phase (request, response, artifact, execution).
            nonce: Optional freshness nonce.
            confidence: Confidence score (0.0 to 1.0).
            compliance_framework: Optional compliance framework mapping.
            control_id: Optional control ID within framework.
            evidence_id: Optional custom evidence ID.

        Returns:
            An Evidence object with the ZK proof attached.

        Raises:
            ZKProvingError: If proof generation fails.
        """
        # Generate the ZK proof
        proof = self.circuit.prove(
            private_inputs=private_inputs,
            public_inputs=public_inputs,
            prover_id=self.auditor_id,
        )

        now = datetime.now(timezone.utc)

        # Create the claim
        claim = Claim(
            name=self.name,
            type=self.measurement_type,
            value=value,
            timestamp=now,
            confidence=confidence,
            phase=phase,
            nonce=nonce,
            compliance_framework=compliance_framework,
            control_id=control_id,
        )

        # Create the evidence with the proof
        return Evidence(
            evidence_id=evidence_id or f"ev-zk-{uuid.uuid4().hex[:12]}",
            attester_id=self.auditor_id,
            attester_type=EvidenceSource.AUDITOR,
            claims=[claim],
            phase=phase,
            generated_at=now,
            nonce=nonce,
            signature="zk-verified",  # ZK proof provides verification
            zk_proof=proof.to_schema(),
        )

    def create_evidence_with_proof(
        self,
        value: Union[str, float, bool, Dict[str, Any]],
        proof: ZKProof,
        phase: str = "request",
        nonce: Optional[str] = None,
        confidence: float = 1.0,
        compliance_framework: Optional[str] = None,
        control_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
    ) -> Evidence:
        """Create Evidence with a pre-generated ZK proof.

        Use this method when you have already generated the proof separately
        and want to attach it to evidence.

        Args:
            value: The claim value.
            proof: Pre-generated ZKProof object.
            phase: Execution phase (request, response, artifact, execution).
            nonce: Optional freshness nonce.
            confidence: Confidence score (0.0 to 1.0).
            compliance_framework: Optional compliance framework mapping.
            control_id: Optional control ID within framework.
            evidence_id: Optional custom evidence ID.

        Returns:
            An Evidence object with the ZK proof attached.
        """
        now = datetime.now(timezone.utc)

        # Create the claim
        claim = Claim(
            name=self.name,
            type=self.measurement_type,
            value=value,
            timestamp=now,
            confidence=confidence,
            phase=phase,
            nonce=nonce,
            compliance_framework=compliance_framework,
            control_id=control_id,
        )

        return Evidence(
            evidence_id=evidence_id or f"ev-zk-{uuid.uuid4().hex[:12]}",
            attester_id=self.auditor_id,
            attester_type=EvidenceSource.AUDITOR,
            claims=[claim],
            phase=phase,
            generated_at=now,
            nonce=nonce,
            signature="zk-verified",
            zk_proof=proof.to_schema(),
        )

    def __repr__(self) -> str:
        return (
            f"ZKEvidence(name={self.name!r}, "
            f"type={self.measurement_type.value!r}, "
            f"circuit={self.circuit.circuit_id!r})"
        )
