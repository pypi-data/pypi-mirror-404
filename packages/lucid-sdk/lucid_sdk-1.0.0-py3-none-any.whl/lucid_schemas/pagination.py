"""Pagination models shared across Lucid services.

This module provides standardized pagination models for list endpoints,
supporting both offset-based and cursor-based pagination patterns.

Pagination modes:
- Offset-based: Traditional skip/limit pagination (default)
- Cursor-based: Efficient for large datasets and time-series data
- Hybrid: Supports both modes in a single endpoint
"""
from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

# Default pagination configuration
# These can be overridden by application-specific settings
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class PaginationParams(BaseModel):
    """Query parameters for offset-based pagination."""

    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of items to return (max {MAX_LIMIT})",
    )

    model_config = ConfigDict(populate_by_name=True)


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response format for offset-based pagination.

    Example:
    {
        "items": [...],
        "total": 150,
        "offset": 0,
        "limit": 50,
        "hasMore": true
    }
    """

    items: list[T] = Field(description="List of items for this page")
    total: int = Field(description="Total number of items available")
    offset: int = Field(description="Current offset")
    limit: int = Field(description="Items per page")
    has_more: bool = Field(alias="hasMore", description="Whether more items are available")

    model_config = ConfigDict(populate_by_name=True)


class CursorData(BaseModel):
    """Data encoded in a cursor token.

    Cursors contain the values needed to efficiently resume pagination
    from a specific position without offset scanning.
    """

    # Primary sort field value (usually timestamp)
    timestamp: Optional[str] = None

    # Secondary sort field (usually ID for stable ordering)
    id: Optional[str] = None

    # Direction: "next" or "prev"
    direction: str = "next"

    # Original limit for consistency
    limit: int = DEFAULT_LIMIT

    model_config = ConfigDict(populate_by_name=True)


class CursorPaginationParams(BaseModel):
    """Parameters for cursor-based pagination."""

    cursor: Optional[str] = Field(
        default=None,
        description="Opaque cursor for pagination. Pass the 'nextCursor' or 'prevCursor' from previous response.",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of items to return (max {MAX_LIMIT})",
    )

    model_config = ConfigDict(populate_by_name=True)


class CursorPaginatedResponse(BaseModel, Generic[T]):
    """Response format for cursor-based pagination.

    Example:
    {
        "items": [...],
        "limit": 50,
        "hasMore": true,
        "nextCursor": "eyJ0aW1l...",
        "prevCursor": null
    }
    """

    items: list[T] = Field(description="List of items for this page")
    limit: int = Field(description="Items per page")
    has_more: bool = Field(alias="hasMore", description="Whether more items are available in the next direction")
    next_cursor: Optional[str] = Field(
        default=None,
        alias="nextCursor",
        description="Cursor to fetch the next page (null if no more items)",
    )
    prev_cursor: Optional[str] = Field(
        default=None,
        alias="prevCursor",
        description="Cursor to fetch the previous page (null if at beginning)",
    )

    # Also include total count for convenience
    # This can be expensive for large datasets, so it's optional
    total: Optional[int] = Field(
        default=None,
        description="Total count of items (may be null for performance)",
    )

    model_config = ConfigDict(populate_by_name=True)


class HybridPaginationParams(BaseModel):
    """Parameters supporting both offset and cursor pagination.

    When cursor is provided, it takes precedence over offset.
    This allows clients to choose the pagination mode that best fits their use case.
    """

    # Cursor-based (takes precedence when provided)
    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for efficient pagination (takes precedence over offset)",
    )

    # Offset-based (standard fallback when no cursor is provided)
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of items to skip (ignored when cursor is provided)",
    )

    limit: int = Field(
        default=DEFAULT_LIMIT,
        ge=1,
        le=MAX_LIMIT,
        description=f"Maximum number of items to return (max {MAX_LIMIT})",
    )

    model_config = ConfigDict(populate_by_name=True)

    @property
    def use_cursor(self) -> bool:
        """Check if cursor-based pagination should be used."""
        return self.cursor is not None


class HybridPaginatedResponse(BaseModel, Generic[T]):
    """Response format supporting both pagination modes.

    Always includes offset-based fields as the standard response format,
    and adds cursor fields when cursor pagination is used.
    """

    items: list[T] = Field(description="List of items for this page")
    total: int = Field(description="Total number of items available")
    offset: int = Field(description="Current offset (for offset-based pagination)")
    limit: int = Field(description="Items per page")
    has_more: bool = Field(alias="hasMore", description="Whether more items are available")

    # Cursor fields (present when cursor pagination is used)
    next_cursor: Optional[str] = Field(
        default=None,
        alias="nextCursor",
        description="Cursor for next page (only when using cursor pagination)",
    )
    prev_cursor: Optional[str] = Field(
        default=None,
        alias="prevCursor",
        description="Cursor for previous page (only when using cursor pagination)",
    )

    model_config = ConfigDict(populate_by_name=True)
