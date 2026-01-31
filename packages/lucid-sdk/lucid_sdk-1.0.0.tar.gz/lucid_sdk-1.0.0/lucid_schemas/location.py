from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field


class AnchorReceipt(BaseModel):
    """Signed receipt from an Anchor Fleet node after RTT probe.

    The Anchor signs this receipt to attest to the exact time it received
    a probe from an Attester. This enables RTT-based distance estimation.
    """
    anchor_id: str = Field(
        ...,
        description="Unique identifier for the anchor node.",
        examples=["anchor-sf"]
    )
    anchor_location: str = Field(
        ...,
        description="Geographic coordinates of the anchor as 'lat,lon'.",
        examples=["37.7749,-122.4194"]
    )
    probe_received_at: datetime = Field(
        ...,
        description="High-precision timestamp when the anchor received the probe.",
        examples=["2025-12-30T20:00:00.123456Z"]
    )
    probe_sent_at: datetime = Field(
        ...,
        description="Timestamp when the attester sent the probe (from attester's clock).",
        examples=["2025-12-30T20:00:00.100000Z"]
    )
    anchor_signature: str = Field(
        ...,
        description="Cryptographic signature of the receipt by the Anchor's TEE.",
        examples=["mock_evidence_signature_abc123"]
    )


class LocationMeasurement(BaseModel):
    """Computed location result from the Verifier's internal location-auditor.

    This is the output of multilateration based on RTT measurements to
    multiple Anchor Fleet nodes. Treated as a measurement in the audit chain.
    """
    latitude: float = Field(
        ...,
        description="Estimated latitude of the Attester.",
        examples=[37.7749]
    )
    longitude: float = Field(
        ...,
        description="Estimated longitude of the Attester.",
        examples=[-122.4194]
    )
    radius_km: float = Field(
        ...,
        description="Uncertainty radius in kilometers.",
        examples=[50.0]
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from 0.0 (low) to 1.0 (high).",
        examples=[0.85]
    )
    method: str = Field(
        "multilateration",
        description="Method used to compute the location.",
        examples=["multilateration"]
    )
    anchor_count: int = Field(
        ...,
        description="Number of anchors used in the computation.",
        examples=[3]
    )
