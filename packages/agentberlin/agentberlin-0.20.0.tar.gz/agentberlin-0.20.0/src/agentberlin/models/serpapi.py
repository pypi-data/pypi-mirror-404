"""Pydantic models for SerpApi responses."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SerpApiResult(BaseModel):
    """Single search result from SerpApi."""

    title: str
    url: str
    snippet: str
    displayed_link: Optional[str] = None
    date: Optional[str] = None
    thumbnail: Optional[str] = None


class SerpApiMetadata(BaseModel):
    """Metadata about the SerpApi search."""

    id: Optional[str] = None
    status: Optional[str] = None
    total_time_taken: Optional[float] = None


class SerpApiResponse(BaseModel):
    """Response for SerpApi search."""

    query: str
    engine: str
    search_type: str
    results: List[SerpApiResult] = Field(default_factory=list)
    total: int
    search_metadata: Optional[SerpApiMetadata] = None
