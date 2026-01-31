"""ZK Proof class for managing generated proofs.

This module provides the ZKProof class for representing and serializing
zero-knowledge proofs.
"""
from __future__ import annotations
import base64
import uuid
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from lucid_schemas import ZKProofSchema, ZKProofSystem

if TYPE_CHECKING:
    from .circuit import ZKCircuit


class ZKProof:
    """A generated zero-knowledge proof with serialization methods.

    This class wraps the raw proof data from a proving system and provides
    methods for serialization to/from the ZKProofSchema format.

    Attributes:
        proof_id: Unique identifier for this proof.
        circuit_id: ID of the circuit this proof is for.
        circuit_version: Version of the circuit.
        proof_system: The proof system used (groth16, plonk, etc.).
        curve: Elliptic curve used.
        proof_data: Raw proof bytes.
        public_inputs: List of public inputs as field elements.
        generated_at: Timestamp when proof was generated.
        prover_id: Optional ID of the prover (auditor).
        setup_hash: Optional hash of trusted setup.
    """

    def __init__(
        self,
        proof_id: str,
        circuit_id: str,
        circuit_version: str,
        proof_system: ZKProofSystem,
        curve: str,
        proof_data: bytes,
        public_inputs: List[str],
        generated_at: Optional[datetime] = None,
        prover_id: Optional[str] = None,
        setup_hash: Optional[str] = None,
    ):
        self.proof_id = proof_id
        self.circuit_id = circuit_id
        self.circuit_version = circuit_version
        self.proof_system = proof_system
        self.curve = curve
        self.proof_data = proof_data
        self.public_inputs = public_inputs
        self.generated_at = generated_at or datetime.now(timezone.utc)
        self.prover_id = prover_id
        self.setup_hash = setup_hash

    @classmethod
    def create(
        cls,
        circuit: "ZKCircuit",
        proof_data: bytes,
        public_inputs: List[str],
        prover_id: Optional[str] = None,
    ) -> "ZKProof":
        """Create a new ZKProof from circuit and proof data.

        Args:
            circuit: The ZKCircuit used to generate the proof.
            proof_data: Raw proof bytes from the prover.
            public_inputs: Public inputs used in the proof.
            prover_id: Optional identifier of the prover.

        Returns:
            A new ZKProof instance.
        """
        return cls(
            proof_id=f"zk-proof-{uuid.uuid4().hex[:12]}",
            circuit_id=circuit.circuit_id,
            circuit_version=circuit.version,
            proof_system=circuit.proof_system,
            curve=circuit.curve,
            proof_data=proof_data,
            public_inputs=public_inputs,
            prover_id=prover_id,
            setup_hash=circuit.setup_hash,
        )

    def to_schema(self) -> ZKProofSchema:
        """Convert to ZKProofSchema for serialization.

        Returns:
            ZKProofSchema instance ready for JSON serialization.
        """
        return ZKProofSchema(
            proof_id=self.proof_id,
            circuit_id=self.circuit_id,
            circuit_version=self.circuit_version,
            proof_system=self.proof_system,
            curve=self.curve,
            proof_data=base64.b64encode(self.proof_data).decode("utf-8"),
            public_inputs=self.public_inputs,
            generated_at=self.generated_at,
            prover_id=self.prover_id,
            setup_hash=self.setup_hash,
        )

    @classmethod
    def from_schema(cls, schema: ZKProofSchema) -> "ZKProof":
        """Create a ZKProof from a ZKProofSchema.

        Args:
            schema: The ZKProofSchema to convert.

        Returns:
            A new ZKProof instance.
        """
        return cls(
            proof_id=schema.proof_id,
            circuit_id=schema.circuit_id,
            circuit_version=schema.circuit_version,
            proof_system=schema.proof_system,
            curve=schema.curve,
            proof_data=base64.b64decode(schema.proof_data),
            public_inputs=schema.public_inputs,
            generated_at=schema.generated_at,
            prover_id=schema.prover_id,
            setup_hash=schema.setup_hash,
        )

    def get_proof_data_base64(self) -> str:
        """Get the proof data as a base64-encoded string.

        Returns:
            Base64-encoded proof data.
        """
        return base64.b64encode(self.proof_data).decode("utf-8")

    def __repr__(self) -> str:
        return (
            f"ZKProof(proof_id={self.proof_id!r}, "
            f"circuit_id={self.circuit_id!r}, "
            f"proof_system={self.proof_system.value!r})"
        )
