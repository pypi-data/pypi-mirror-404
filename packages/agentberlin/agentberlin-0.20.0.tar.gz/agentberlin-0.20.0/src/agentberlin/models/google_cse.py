"""Pydantic models for Google Custom Search API responses."""

from typing import List

from pydantic import BaseModel, Field


class GoogleCSEResult(BaseModel):
    """Single search result from Google Custom Search."""

    title: str
    url: str
    snippet: str


class GoogleCSEResponse(BaseModel):
    """Response for Google Custom Search."""

    query: str
    results: List[GoogleCSEResult] = Field(default_factory=list)
    total: int
