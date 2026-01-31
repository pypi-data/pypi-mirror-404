"""Dashboard management schemas shared between verifier and observer."""
from __future__ import annotations

import logging
from typing import ClassVar, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import SCHEMA_VERSION_DASHBOARD

logger = logging.getLogger(__name__)


class WidgetPosition(BaseModel):
    """Widget position configuration."""
    x: int
    y: int
    w: int
    h: int


class WidgetConfig(BaseModel):
    """Widget configuration."""
    id: str
    type: str
    title: str
    position: WidgetPosition
    data_source: Optional[str] = Field(default=None, alias="dataSource")
    chart_config: Optional[Dict] = Field(default=None, alias="chartConfig")

    model_config = ConfigDict(populate_by_name=True)


class DashboardResponse(BaseModel):
    """Dashboard response model."""
    _expected_version: ClassVar[str] = SCHEMA_VERSION_DASHBOARD

    schema_version: str = Field(
        default=SCHEMA_VERSION_DASHBOARD,
        description="Schema version for backwards compatibility. Follows SemVer.",
        examples=["1.0.0"],
        pattern=r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
    )
    dashboard_id: str

    @field_validator('schema_version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate schema version and log warnings for mismatches."""
        expected = cls._expected_version
        if v != expected:
            logger.warning(
                "Schema version mismatch for %s: got '%s', expected '%s'",
                cls.__name__, v, expected
            )
        return v
    name: str
    description: Optional[str] = None
    auditor_id: Optional[str] = None
    widgets: List[WidgetConfig]
    is_auto_generated: bool
    is_system: bool
    created_at: str
    updated_at: str


class CreateDashboardRequest(BaseModel):
    """Request model for creating a dashboard."""
    name: str
    description: Optional[str] = None
    auditor_id: Optional[str] = None
    widgets: List[WidgetConfig] = Field(default_factory=list)


class UpdateDashboardRequest(BaseModel):
    """Request model for updating a dashboard."""
    name: Optional[str] = None
    description: Optional[str] = None
    widgets: Optional[List[WidgetConfig]] = None
