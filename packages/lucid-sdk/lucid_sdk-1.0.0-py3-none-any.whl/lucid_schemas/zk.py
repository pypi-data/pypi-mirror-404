"""Zero-Knowledge Proof schemas for verifiable computation attestation.

This module defines the schemas for ZK proof generation and verification,
enabling auditors to generate cryptographic proofs of their computations
that can be verified without revealing the raw data.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class ZKProofSystem(str, Enum):
    """Supported zero-knowledge proof systems."""
    GROTH16 = "groth16"
    PLONK = "plonk"
    FFLONK = "fflonk"
    STARK = "stark"


class ZKProofSchema(BaseModel):
    """A zero-knowledge proof attesting to a computation.

    This schema represents a cryptographic proof that a computation was
    performed correctly, without revealing the private inputs.
    """
    proof_id: str = Field(
        ...,
        description="Unique identifier for this proof.",
        examples=["zk-proof-abc123"]
    )
    circuit_id: str = Field(
        ...,
        description="Links to the registered verification key.",
        examples=["pii-detector-v1"]
    )
    circuit_version: str = Field(
        ...,
        description="Version of the circuit for compatibility checking.",
        examples=["1.0.0"]
    )
    proof_system: ZKProofSystem = Field(
        ...,
        description="The proof system used (groth16, plonk, etc.).",
        examples=["groth16"]
    )
    curve: str = Field(
        "bn254",
        description="Elliptic curve used for the proof.",
        examples=["bn254", "bls12_381"]
    )
    proof_data: str = Field(
        ...,
        description="Base64-encoded proof bytes.",
        examples=["eyJwaV9hIjogWyIxMjM0NSIsICIx..."]
    )
    public_inputs: List[str] = Field(
        ...,
        description="Hex-encoded field elements representing public inputs.",
        examples=[["0x1a2b3c", "0x4d5e6f"]]
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp when the proof was generated (UTC).",
        examples=["2025-12-30T20:00:00Z"]
    )
    prover_id: Optional[str] = Field(
        None,
        description="Identifier of the auditor that generated the proof.",
        examples=["pii-auditor@sha256:abc123"]
    )
    setup_hash: Optional[str] = Field(
        None,
        description="Hash of the trusted setup (for groth16).",
        examples=["sha256:def456..."]
    )


class ZKCircuitMetadata(BaseModel):
    """Metadata for a registered ZK circuit.

    This schema describes a ZK circuit that has been registered with
    the verifier, including its verification key.
    """
    circuit_id: str = Field(
        ...,
        description="Unique identifier for the circuit.",
        examples=["pii-detector-v1"]
    )
    circuit_name: str = Field(
        ...,
        description="Human-readable name for the circuit.",
        examples=["PII Detection Circuit"]
    )
    version: str = Field(
        ...,
        description="Semantic version of the circuit.",
        examples=["1.0.0"]
    )
    proof_system: ZKProofSystem = Field(
        ...,
        description="The proof system this circuit uses.",
        examples=["groth16"]
    )
    curve: str = Field(
        "bn254",
        description="Elliptic curve the circuit is defined over.",
        examples=["bn254"]
    )
    verification_key: str = Field(
        ...,
        description="Base64-encoded verification key.",
        examples=["eyJ2ayI6IHsia..."]
    )
    num_public_inputs: int = Field(
        ...,
        ge=0,
        description="Number of public inputs expected by the circuit.",
        examples=[3]
    )
    registered_at: datetime = Field(
        ...,
        description="Timestamp when the circuit was registered (UTC).",
        examples=["2025-12-30T20:00:00Z"]
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable description of what the circuit verifies.",
        examples=["Verifies that PII detection was performed correctly"]
    )
