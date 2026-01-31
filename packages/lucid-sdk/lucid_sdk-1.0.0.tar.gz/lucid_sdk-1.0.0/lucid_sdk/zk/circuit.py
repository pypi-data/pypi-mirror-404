"""ZK Circuit class for loading and using ZK circuits.

This module provides the ZKCircuit class for loading proving/verification keys
and generating/verifying zero-knowledge proofs.
"""
from __future__ import annotations
import base64
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lucid_schemas import ZKProofSystem, ZKCircuitMetadata

from .exceptions import (
    ZKNotAvailableError,
    ZKCircuitError,
    ZKProvingError,
    ZKVerificationError,
    ZKInputError,
)
from .proof import ZKProof


def _check_snarkjs_available() -> None:
    """Check if snarkjs is available."""
    try:
        import snarkjs  # noqa: F401
    except ImportError:
        raise ZKNotAvailableError()


class ZKCircuit:
    """Represents a ZK circuit with proving and verification keys.

    This class manages the circuit artifacts (WASM, proving key, verification key)
    and provides methods for proof generation and verification.

    The circuit supports multiple proof systems (groth16, plonk, fflonk) and
    can be used with circom-compiled circuits.

    Attributes:
        circuit_id: Unique identifier for the circuit.
        version: Semantic version of the circuit.
        proof_system: Proof system to use (groth16, plonk, etc.).
        curve: Elliptic curve the circuit is defined over.
        proving_key_path: Path to the proving key file.
        verification_key_path: Path to the verification key file.
        wasm_path: Path to the WASM witness generator.
        setup_hash: Hash of the trusted setup (for groth16).
    """

    def __init__(
        self,
        circuit_id: str,
        proving_key_path: Path,
        verification_key_path: Path,
        wasm_path: Optional[Path] = None,
        version: str = "1.0.0",
        proof_system: ZKProofSystem = ZKProofSystem.GROTH16,
        curve: str = "bn254",
        setup_hash: Optional[str] = None,
    ):
        self.circuit_id = circuit_id
        self.version = version
        self.proof_system = proof_system
        self.curve = curve
        self.proving_key_path = Path(proving_key_path)
        self.verification_key_path = Path(verification_key_path)
        self.wasm_path = Path(wasm_path) if wasm_path else None
        self.setup_hash = setup_hash

        # Cached verification key
        self._verification_key: Optional[Dict[str, Any]] = None
        self._verification_key_bytes: Optional[bytes] = None

    @classmethod
    def from_files(
        cls,
        circuit_id: str,
        proving_key_path: str,
        verification_key_path: str,
        wasm_path: Optional[str] = None,
        version: str = "1.0.0",
        proof_system: ZKProofSystem = ZKProofSystem.GROTH16,
        curve: str = "bn254",
    ) -> "ZKCircuit":
        """Load a circuit from files.

        Args:
            circuit_id: Unique identifier for the circuit.
            proving_key_path: Path to the proving key (.zkey file).
            verification_key_path: Path to the verification key (.json file).
            wasm_path: Path to the WASM witness generator (.wasm file).
            version: Semantic version of the circuit.
            proof_system: Proof system to use.
            curve: Elliptic curve.

        Returns:
            A new ZKCircuit instance.

        Raises:
            ZKCircuitError: If any of the required files don't exist.
        """
        pk_path = Path(proving_key_path)
        vk_path = Path(verification_key_path)

        if not pk_path.exists():
            raise ZKCircuitError(
                f"Proving key not found: {proving_key_path}",
                circuit_id=circuit_id,
                file_path=proving_key_path,
            )

        if not vk_path.exists():
            raise ZKCircuitError(
                f"Verification key not found: {verification_key_path}",
                circuit_id=circuit_id,
                file_path=verification_key_path,
            )

        wasm = None
        if wasm_path:
            wasm = Path(wasm_path)
            if not wasm.exists():
                raise ZKCircuitError(
                    f"WASM file not found: {wasm_path}",
                    circuit_id=circuit_id,
                    file_path=wasm_path,
                )

        # Compute setup hash for groth16 circuits
        setup_hash = None
        if proof_system == ZKProofSystem.GROTH16:
            with open(pk_path, "rb") as f:
                setup_hash = f"sha256:{hashlib.sha256(f.read()).hexdigest()[:32]}"

        return cls(
            circuit_id=circuit_id,
            proving_key_path=pk_path,
            verification_key_path=vk_path,
            wasm_path=wasm,
            version=version,
            proof_system=proof_system,
            curve=curve,
            setup_hash=setup_hash,
        )

    def _load_verification_key(self) -> Dict[str, Any]:
        """Load and cache the verification key."""
        if self._verification_key is None:
            try:
                with open(self.verification_key_path, "r") as f:
                    self._verification_key = json.load(f)
            except Exception as e:
                raise ZKCircuitError(
                    f"Failed to load verification key: {e}",
                    circuit_id=self.circuit_id,
                    file_path=str(self.verification_key_path),
                )
        return self._verification_key

    def get_verification_key_bytes(self) -> bytes:
        """Get the verification key as bytes.

        Returns:
            The verification key serialized as JSON bytes.
        """
        if self._verification_key_bytes is None:
            vk = self._load_verification_key()
            self._verification_key_bytes = json.dumps(vk, sort_keys=True).encode("utf-8")
        return self._verification_key_bytes

    def get_num_public_inputs(self) -> int:
        """Get the number of public inputs for this circuit.

        Returns:
            Number of public inputs.
        """
        vk = self._load_verification_key()
        # The verification key typically has an nPublic field
        return vk.get("nPublic", len(vk.get("IC", [])) - 1)

    def prove(
        self,
        private_inputs: Dict[str, Any],
        public_inputs: Optional[Dict[str, Any]] = None,
        prover_id: Optional[str] = None,
    ) -> ZKProof:
        """Generate a ZK proof for the given inputs.

        This method computes a witness from the inputs and generates a proof
        using the circuit's proving key.

        Args:
            private_inputs: Private inputs to the circuit (not revealed).
            public_inputs: Public inputs to the circuit (included in proof).
            prover_id: Optional identifier of the prover (auditor).

        Returns:
            A ZKProof object containing the proof.

        Raises:
            ZKNotAvailableError: If snarkjs is not installed.
            ZKProvingError: If proof generation fails.
            ZKInputError: If inputs are invalid.
        """
        _check_snarkjs_available()

        if self.wasm_path is None:
            raise ZKCircuitError(
                "WASM path required for proof generation",
                circuit_id=self.circuit_id,
            )

        # Merge inputs
        all_inputs = {**(public_inputs or {}), **private_inputs}

        try:
            import snarkjs

            # Generate witness and proof based on proof system
            if self.proof_system == ZKProofSystem.GROTH16:
                proof_data, public_signals = snarkjs.groth16.fullProve(
                    all_inputs,
                    str(self.wasm_path),
                    str(self.proving_key_path),
                )
            elif self.proof_system == ZKProofSystem.PLONK:
                proof_data, public_signals = snarkjs.plonk.fullProve(
                    all_inputs,
                    str(self.wasm_path),
                    str(self.proving_key_path),
                )
            elif self.proof_system == ZKProofSystem.FFLONK:
                proof_data, public_signals = snarkjs.fflonk.fullProve(
                    all_inputs,
                    str(self.wasm_path),
                    str(self.proving_key_path),
                )
            else:
                raise ZKProvingError(
                    f"Unsupported proof system for proving: {self.proof_system}",
                    circuit_id=self.circuit_id,
                )

            # Serialize proof
            proof_bytes = json.dumps(proof_data, sort_keys=True).encode("utf-8")

            # Convert public signals to hex format
            public_inputs_hex = [hex(int(s)) for s in public_signals]

            return ZKProof.create(
                circuit=self,
                proof_data=proof_bytes,
                public_inputs=public_inputs_hex,
                prover_id=prover_id,
            )

        except ZKProvingError:
            raise
        except Exception as e:
            raise ZKProvingError(
                f"Proof generation failed: {e}",
                circuit_id=self.circuit_id,
            )

    def verify(self, proof: ZKProof) -> bool:
        """Verify a ZK proof.

        Args:
            proof: The ZKProof to verify.

        Returns:
            True if the proof is valid, False otherwise.

        Raises:
            ZKNotAvailableError: If snarkjs is not installed.
            ZKVerificationError: If verification encounters an error.
        """
        _check_snarkjs_available()

        # Check circuit compatibility
        if proof.circuit_id != self.circuit_id:
            raise ZKVerificationError(
                f"Circuit ID mismatch: expected {self.circuit_id}, got {proof.circuit_id}",
                proof_id=proof.proof_id,
                circuit_id=self.circuit_id,
                reason="circuit_id_mismatch",
            )

        try:
            import snarkjs

            # Parse proof data
            proof_json = json.loads(proof.proof_data.decode("utf-8"))

            # Convert public inputs from hex to decimal strings
            public_signals = [str(int(p, 16)) for p in proof.public_inputs]

            # Load verification key
            vk = self._load_verification_key()

            # Verify based on proof system
            if self.proof_system == ZKProofSystem.GROTH16:
                result = snarkjs.groth16.verify(vk, public_signals, proof_json)
            elif self.proof_system == ZKProofSystem.PLONK:
                result = snarkjs.plonk.verify(vk, public_signals, proof_json)
            elif self.proof_system == ZKProofSystem.FFLONK:
                result = snarkjs.fflonk.verify(vk, public_signals, proof_json)
            else:
                raise ZKVerificationError(
                    f"Unsupported proof system: {self.proof_system}",
                    proof_id=proof.proof_id,
                    circuit_id=self.circuit_id,
                )

            return result

        except ZKVerificationError:
            raise
        except Exception as e:
            raise ZKVerificationError(
                f"Proof verification failed: {e}",
                proof_id=proof.proof_id,
                circuit_id=self.circuit_id,
            )

    def to_metadata(self) -> ZKCircuitMetadata:
        """Convert circuit to ZKCircuitMetadata for registration.

        Returns:
            ZKCircuitMetadata instance for the verifier registry.
        """
        vk_bytes = self.get_verification_key_bytes()
        return ZKCircuitMetadata(
            circuit_id=self.circuit_id,
            circuit_name=self.circuit_id,
            version=self.version,
            proof_system=self.proof_system,
            curve=self.curve,
            verification_key=base64.b64encode(vk_bytes).decode("utf-8"),
            num_public_inputs=self.get_num_public_inputs(),
            registered_at=datetime.now(timezone.utc),
        )

    def __repr__(self) -> str:
        return (
            f"ZKCircuit(circuit_id={self.circuit_id!r}, "
            f"version={self.version!r}, "
            f"proof_system={self.proof_system.value!r})"
        )
