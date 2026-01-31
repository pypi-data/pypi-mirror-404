"""Tests for the lucid_sdk.zk module."""
import pytest
import base64
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from lucid_schemas import ZKProofSystem, ZKProofSchema, MeasurementType, Evidence


class TestZKExceptions:
    """Tests for ZK exception classes."""

    def test_zk_error_base(self):
        from lucid_sdk.zk import ZKError

        error = ZKError("Test error", error_code="TEST_CODE", details={"key": "value"})
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"
        assert error.details == {"key": "value"}
        assert "Test error" in str(error)

    def test_zk_not_available_error(self):
        from lucid_sdk.zk import ZKNotAvailableError

        error = ZKNotAvailableError()
        assert "pip install lucid-sdk[zk]" in error.message
        assert error.error_code == "ZK_NOT_AVAILABLE"

    def test_zk_circuit_error(self):
        from lucid_sdk.zk import ZKCircuitError

        error = ZKCircuitError(
            "Circuit file not found",
            circuit_id="test-circuit",
            file_path="/path/to/circuit.zkey",
        )
        assert error.circuit_id == "test-circuit"
        assert error.file_path == "/path/to/circuit.zkey"
        assert error.details["circuit_id"] == "test-circuit"

    def test_zk_proving_error(self):
        from lucid_sdk.zk import ZKProvingError

        error = ZKProvingError(
            "Proof generation failed",
            circuit_id="test-circuit",
            input_name="private_input",
        )
        assert error.circuit_id == "test-circuit"
        assert error.input_name == "private_input"

    def test_zk_verification_error(self):
        from lucid_sdk.zk import ZKVerificationError

        error = ZKVerificationError(
            "Invalid proof",
            proof_id="proof-123",
            circuit_id="circuit-456",
            reason="public_inputs_mismatch",
        )
        assert error.proof_id == "proof-123"
        assert error.circuit_id == "circuit-456"
        assert error.reason == "public_inputs_mismatch"

    def test_zk_input_error(self):
        from lucid_sdk.zk import ZKInputError

        error = ZKInputError(
            "Invalid input type",
            input_name="threshold",
            expected_type="int",
            actual_value="not_a_number",
        )
        assert error.input_name == "threshold"
        assert error.expected_type == "int"
        assert error.actual_value == "not_a_number"

    def test_error_to_dict(self):
        from lucid_sdk.zk import ZKCircuitError

        error = ZKCircuitError("Test", circuit_id="c1", file_path="/path")
        d = error.to_dict()
        assert d["error"] == "ZK_CIRCUIT_ERROR"
        assert d["message"] == "Test"
        assert "circuit_id" in d["details"]


class TestZKProof:
    """Tests for ZKProof class."""

    def test_proof_creation(self):
        from lucid_sdk.zk import ZKProof

        proof = ZKProof(
            proof_id="test-proof-123",
            circuit_id="test-circuit",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.GROTH16,
            curve="bn254",
            proof_data=b'{"proof": "data"}',
            public_inputs=["0x1", "0x2"],
        )

        assert proof.proof_id == "test-proof-123"
        assert proof.circuit_id == "test-circuit"
        assert proof.proof_system == ZKProofSystem.GROTH16
        assert len(proof.public_inputs) == 2

    def test_proof_to_schema(self):
        from lucid_sdk.zk import ZKProof

        proof = ZKProof(
            proof_id="schema-test",
            circuit_id="circuit-1",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.PLONK,
            curve="bn254",
            proof_data=b'{"test": "data"}',
            public_inputs=["0xabc"],
            prover_id="test-prover",
        )

        schema = proof.to_schema()
        assert isinstance(schema, ZKProofSchema)
        assert schema.proof_id == "schema-test"
        assert schema.proof_system == ZKProofSystem.PLONK
        # Verify proof_data is base64 encoded
        decoded = base64.b64decode(schema.proof_data)
        assert decoded == b'{"test": "data"}'

    def test_proof_from_schema(self):
        from lucid_sdk.zk import ZKProof

        schema = ZKProofSchema(
            proof_id="from-schema-test",
            circuit_id="circuit-2",
            circuit_version="2.0.0",
            proof_system=ZKProofSystem.FFLONK,
            curve="bls12_381",
            proof_data=base64.b64encode(b'{"from": "schema"}').decode(),
            public_inputs=["0x1", "0x2", "0x3"],
            generated_at=datetime.now(timezone.utc),
            setup_hash="sha256:abc",
        )

        proof = ZKProof.from_schema(schema)
        assert proof.proof_id == "from-schema-test"
        assert proof.circuit_id == "circuit-2"
        assert proof.proof_system == ZKProofSystem.FFLONK
        assert proof.proof_data == b'{"from": "schema"}'
        assert proof.setup_hash == "sha256:abc"

    def test_proof_roundtrip(self):
        from lucid_sdk.zk import ZKProof

        original = ZKProof(
            proof_id="roundtrip-test",
            circuit_id="circuit",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.GROTH16,
            curve="bn254",
            proof_data=b'complex proof data here',
            public_inputs=["0xdeadbeef"],
            prover_id="prover-1",
            setup_hash="hash123",
        )

        schema = original.to_schema()
        restored = ZKProof.from_schema(schema)

        assert restored.proof_id == original.proof_id
        assert restored.proof_data == original.proof_data
        assert restored.public_inputs == original.public_inputs

    def test_get_proof_data_base64(self):
        from lucid_sdk.zk import ZKProof

        proof = ZKProof(
            proof_id="base64-test",
            circuit_id="circuit",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.GROTH16,
            curve="bn254",
            proof_data=b"test data",
            public_inputs=[],
        )

        b64 = proof.get_proof_data_base64()
        assert base64.b64decode(b64) == b"test data"

    def test_proof_repr(self):
        from lucid_sdk.zk import ZKProof

        proof = ZKProof(
            proof_id="repr-test",
            circuit_id="my-circuit",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.PLONK,
            curve="bn254",
            proof_data=b"data",
            public_inputs=[],
        )

        repr_str = repr(proof)
        assert "repr-test" in repr_str
        assert "my-circuit" in repr_str
        assert "plonk" in repr_str


class TestZKCircuit:
    """Tests for ZKCircuit class."""

    @pytest.fixture
    def temp_circuit_files(self):
        """Create temporary circuit files for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create mock proving key
            pk_path = tmppath / "circuit.zkey"
            pk_path.write_bytes(b"mock proving key data")

            # Create mock verification key
            vk_data = {
                "protocol": "groth16",
                "curve": "bn128",
                "nPublic": 2,
                "IC": [["1", "2"], ["3", "4"], ["5", "6"]],
            }
            vk_path = tmppath / "circuit_vkey.json"
            vk_path.write_text(json.dumps(vk_data))

            # Create mock WASM
            wasm_path = tmppath / "circuit.wasm"
            wasm_path.write_bytes(b"mock wasm data")

            yield {
                "dir": tmppath,
                "pk": pk_path,
                "vk": vk_path,
                "wasm": wasm_path,
                "vk_data": vk_data,
            }

    def test_circuit_from_files(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit

        circuit = ZKCircuit.from_files(
            circuit_id="test-circuit",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
            wasm_path=str(temp_circuit_files["wasm"]),
            version="1.0.0",
        )

        assert circuit.circuit_id == "test-circuit"
        assert circuit.version == "1.0.0"
        assert circuit.proof_system == ZKProofSystem.GROTH16
        assert circuit.setup_hash is not None
        assert circuit.setup_hash.startswith("sha256:")

    def test_circuit_from_files_without_wasm(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit

        circuit = ZKCircuit.from_files(
            circuit_id="verify-only",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
        )

        assert circuit.circuit_id == "verify-only"
        assert circuit.wasm_path is None

    def test_circuit_from_files_missing_pk(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit, ZKCircuitError

        with pytest.raises(ZKCircuitError) as exc_info:
            ZKCircuit.from_files(
                circuit_id="missing-pk",
                proving_key_path="/nonexistent/path.zkey",
                verification_key_path=str(temp_circuit_files["vk"]),
            )

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.circuit_id == "missing-pk"

    def test_circuit_from_files_missing_vk(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit, ZKCircuitError

        with pytest.raises(ZKCircuitError) as exc_info:
            ZKCircuit.from_files(
                circuit_id="missing-vk",
                proving_key_path=str(temp_circuit_files["pk"]),
                verification_key_path="/nonexistent/vkey.json",
            )

        assert "not found" in str(exc_info.value).lower()

    def test_get_verification_key_bytes(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit

        circuit = ZKCircuit.from_files(
            circuit_id="vk-bytes-test",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
        )

        vk_bytes = circuit.get_verification_key_bytes()
        assert isinstance(vk_bytes, bytes)

        # Should be valid JSON
        vk_json = json.loads(vk_bytes.decode("utf-8"))
        assert "nPublic" in vk_json

    def test_get_num_public_inputs(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit

        circuit = ZKCircuit.from_files(
            circuit_id="num-inputs-test",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
        )

        num_inputs = circuit.get_num_public_inputs()
        assert num_inputs == 2  # From nPublic in mock vk_data

    def test_to_metadata(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit
        from lucid_schemas import ZKCircuitMetadata

        circuit = ZKCircuit.from_files(
            circuit_id="metadata-test",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
            version="2.0.0",
        )

        metadata = circuit.to_metadata()
        assert isinstance(metadata, ZKCircuitMetadata)
        assert metadata.circuit_id == "metadata-test"
        assert metadata.version == "2.0.0"
        assert metadata.proof_system == ZKProofSystem.GROTH16
        assert metadata.num_public_inputs == 2

    def test_circuit_repr(self, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit

        circuit = ZKCircuit.from_files(
            circuit_id="repr-circuit",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
            version="1.2.3",
        )

        repr_str = repr(circuit)
        assert "repr-circuit" in repr_str
        assert "1.2.3" in repr_str

    @patch("lucid_sdk.zk.circuit._check_snarkjs_available")
    def test_prove_without_wasm_raises_error(self, mock_check, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit, ZKCircuitError

        # Mock snarkjs check to pass so we can test the wasm check
        mock_check.return_value = None

        circuit = ZKCircuit.from_files(
            circuit_id="no-wasm",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
            # No wasm_path
        )

        with pytest.raises(ZKCircuitError) as exc_info:
            circuit.prove(private_inputs={"x": 1})

        assert "wasm" in str(exc_info.value).lower()

    @patch("lucid_sdk.zk.circuit._check_snarkjs_available")
    def test_prove_without_snarkjs(self, mock_check, temp_circuit_files):
        from lucid_sdk.zk import ZKCircuit, ZKNotAvailableError

        mock_check.side_effect = ZKNotAvailableError()

        circuit = ZKCircuit.from_files(
            circuit_id="no-snarkjs",
            proving_key_path=str(temp_circuit_files["pk"]),
            verification_key_path=str(temp_circuit_files["vk"]),
            wasm_path=str(temp_circuit_files["wasm"]),
        )

        with pytest.raises(ZKNotAvailableError):
            circuit.prove(private_inputs={"x": 1})


class TestZKEvidence:
    """Tests for ZKEvidence helper class."""

    @pytest.fixture
    def mock_circuit(self):
        """Create a mock ZKCircuit for testing."""
        from lucid_sdk.zk import ZKCircuit, ZKProof

        circuit = Mock(spec=ZKCircuit)
        circuit.circuit_id = "mock-circuit"
        circuit.version = "1.0.0"
        circuit.proof_system = ZKProofSystem.GROTH16
        circuit.curve = "bn254"
        circuit.setup_hash = "sha256:mock"

        # Mock prove method to return a ZKProof
        def mock_prove(private_inputs, public_inputs=None, prover_id=None):
            return ZKProof.create(
                circuit=circuit,
                proof_data=b'{"mock": "proof"}',
                public_inputs=["0x1"],
                prover_id=prover_id,
            )

        circuit.prove = Mock(side_effect=mock_prove)
        return circuit

    def test_zk_evidence_creation(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence

        zk_ev = ZKEvidence(
            name="test_evidence",
            measurement_type=MeasurementType.quantity,
            circuit=mock_circuit,
            auditor_id="test-auditor",
        )

        assert zk_ev.name == "test_evidence"
        assert zk_ev.measurement_type == MeasurementType.quantity
        assert zk_ev.auditor_id == "test-auditor"

    def test_create_evidence(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence

        zk_ev = ZKEvidence(
            name="pii_score",
            measurement_type=MeasurementType.quantity,
            circuit=mock_circuit,
            auditor_id="pii-auditor",
        )

        evidence = zk_ev.create_evidence(
            value={"detected": False, "score": 0.1},
            private_inputs={"text_hash": 12345},
            public_inputs={"threshold": 50},
            phase="request",
            confidence=0.95,
        )

        assert isinstance(evidence, Evidence)
        assert evidence.claims[0].name == "pii_score"
        assert evidence.claims[0].type == MeasurementType.quantity
        assert evidence.claims[0].value == {"detected": False, "score": 0.1}
        assert evidence.claims[0].phase == "request"
        assert evidence.claims[0].confidence == 0.95
        assert evidence.zk_proof is not None
        assert evidence.signature == "zk-verified"

        # Verify circuit.prove was called
        mock_circuit.prove.assert_called_once()

    def test_create_evidence_with_nonce(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence

        zk_ev = ZKEvidence(
            name="test",
            measurement_type=MeasurementType.other,
            circuit=mock_circuit,
            auditor_id="test-auditor",
        )

        evidence = zk_ev.create_evidence(
            value="test_value",
            private_inputs={"x": 1},
            nonce="unique-nonce-123",
        )

        assert evidence.nonce == "unique-nonce-123"

    def test_create_evidence_with_compliance(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence

        zk_ev = ZKEvidence(
            name="gdpr_check",
            measurement_type=MeasurementType.policy_violation,
            circuit=mock_circuit,
            auditor_id="gdpr-auditor",
        )

        evidence = zk_ev.create_evidence(
            value=False,
            private_inputs={"data": "test"},
            compliance_framework="gdpr",
            control_id="Article 5(1)(f)",
        )

        assert evidence.claims[0].compliance_framework == "gdpr"
        assert evidence.claims[0].control_id == "Article 5(1)(f)"

    def test_create_evidence_with_proof(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence, ZKProof

        # Pre-generate a proof
        proof = ZKProof(
            proof_id="pre-generated",
            circuit_id="mock-circuit",
            circuit_version="1.0.0",
            proof_system=ZKProofSystem.GROTH16,
            curve="bn254",
            proof_data=b'{"pre": "generated"}',
            public_inputs=["0xabc"],
        )

        zk_ev = ZKEvidence(
            name="with_proof",
            measurement_type=MeasurementType.quantity,
            circuit=mock_circuit,
            auditor_id="proof-auditor",
        )

        evidence = zk_ev.create_evidence_with_proof(
            value=42,
            proof=proof,
            phase="response",
        )

        assert isinstance(evidence, Evidence)
        assert evidence.zk_proof.proof_id == "pre-generated"
        # prove should NOT have been called since we provided a proof
        mock_circuit.prove.assert_not_called()

    def test_zk_evidence_repr(self, mock_circuit):
        from lucid_sdk.zk import ZKEvidence

        zk_ev = ZKEvidence(
            name="repr_test",
            measurement_type=MeasurementType.quantity,
            circuit=mock_circuit,
            auditor_id="repr-auditor",
        )

        repr_str = repr(zk_ev)
        assert "repr_test" in repr_str
        assert "quantity" in repr_str
        assert "mock-circuit" in repr_str


class TestZKModuleImports:
    """Test that ZK module exports are correct."""

    def test_import_from_zk_module(self):
        from lucid_sdk.zk import (
            ZKCircuit,
            ZKProof,
            ZKEvidence,
            ZKError,
            ZKNotAvailableError,
            ZKCircuitError,
            ZKProvingError,
            ZKVerificationError,
            ZKInputError,
        )

        # Just verify imports work
        assert ZKCircuit is not None
        assert ZKProof is not None
        assert ZKEvidence is not None
        assert ZKError is not None
        assert ZKNotAvailableError is not None
        assert ZKCircuitError is not None
        assert ZKProvingError is not None
        assert ZKVerificationError is not None
        assert ZKInputError is not None

    def test_zk_module_all_exports(self):
        from lucid_sdk import zk

        expected = [
            "ZKCircuit",
            "ZKProof",
            "ZKEvidence",
            "ZKError",
            "ZKNotAvailableError",
            "ZKCircuitError",
            "ZKProvingError",
            "ZKVerificationError",
            "ZKInputError",
        ]

        for name in expected:
            assert name in zk.__all__
