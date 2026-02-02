"""Pydantic models for DeFiStream API responses."""

from typing import Any, Literal
from pydantic import BaseModel


class ResponseMetadata(BaseModel):
    """Metadata from API response headers."""

    rate_limit: int | None = None
    quota_remaining: int | None = None
    request_cost: int | None = None


class EventsResponse(BaseModel):
    """Standard events API response."""

    status: Literal["success", "error"]
    events: list[dict[str, Any]] = []
    count: int = 0
    error: str | None = None


class DecodersResponse(BaseModel):
    """Response from /decoders endpoint."""

    decoders: list[str] = []
