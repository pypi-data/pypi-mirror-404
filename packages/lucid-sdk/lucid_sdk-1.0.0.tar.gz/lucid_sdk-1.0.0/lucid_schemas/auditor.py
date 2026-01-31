from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field

from .enums import AuditorRole, AuditorMechanism


class Auditor(BaseModel):
    """Metadata for a trusted Auditor node."""
    id: str = Field(
        ...,
        description="Unique auditor identifier.",
        examples=["pii-auditor-v1"]
    )
    name: str = Field(..., description="Display name of the auditor.")
    role: AuditorRole = Field(..., description="Assigned role.")
    mechanism: AuditorMechanism = Field(..., description="Technical audit mechanism.")
    image_url: str = Field(..., description="Container image path.")
    public_key: str = Field(..., description="Public key used for verifying this auditor's signatures.")
    supported_measurements: List[Dict[str, Any]] = Field(..., description="List of metrics this auditor can provide.")
