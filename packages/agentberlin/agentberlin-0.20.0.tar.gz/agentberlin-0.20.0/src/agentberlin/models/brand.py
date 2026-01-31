"""Pydantic models for brand profile API responses."""

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class BrandProfileResponse(BaseModel):
    """Brand profile configuration for a project."""

    domain: str
    name: str
    context: str
    search_analysis_context: Optional[str] = None
    domain_authority: int
    competitors: List[str] = Field(default_factory=list)
    industries: List[str] = Field(default_factory=list)
    business_models: List[str] = Field(default_factory=list)
    company_size: str
    target_customer_segments: List[str] = Field(default_factory=list)
    geographies: List[str] = Field(default_factory=list)
    personas: List[str] = Field(default_factory=list)
    sitemaps: List[str] = Field(default_factory=list)
    profile_urls: List[str] = Field(default_factory=list)


class BrandProfileUpdateField(BaseModel):
    """Updated field information."""

    field: str
    value: Any


class BrandProfileUpdateResponse(BaseModel):
    """Response for brand profile update."""

    success: bool
    domain: str
    mode: str
    updated: BrandProfileUpdateField
