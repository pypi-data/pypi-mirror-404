"""Pydantic models for Google Search Console API responses."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchAnalyticsRow(BaseModel):
    """A single row of search analytics data."""

    keys: List[str] = Field(default_factory=list)
    clicks: float
    impressions: float
    ctr: float
    position: float


class SearchAnalyticsResponse(BaseModel):
    """Response from search analytics query."""

    rows: List[SearchAnalyticsRow] = Field(default_factory=list)
    response_aggregation_type: Optional[str] = None


class SiteInfo(BaseModel):
    """Information about a site in Search Console."""

    site_url: str
    permission_level: str


class SitemapContent(BaseModel):
    """Content information for a sitemap."""

    type: str
    submitted: Optional[int] = None
    indexed: Optional[int] = None


class Sitemap(BaseModel):
    """Information about a sitemap."""

    path: str
    last_submitted: Optional[str] = None
    is_pending: Optional[bool] = None
    is_sitemaps_index: Optional[bool] = None
    last_downloaded: Optional[str] = None
    warnings: Optional[int] = None
    errors: Optional[int] = None
    contents: List[SitemapContent] = Field(default_factory=list)


class SitemapListResponse(BaseModel):
    """Response from listing sitemaps."""

    sitemap: List[Sitemap] = Field(default_factory=list)


class UrlInspectionResult(BaseModel):
    """Result of URL inspection."""

    inspection_result_link: Optional[str] = None
    index_status_result: Optional[Dict[str, Any]] = None
    mobile_usability_result: Optional[Dict[str, Any]] = None
    rich_results_result: Optional[Dict[str, Any]] = None


class UrlInspectionResponse(BaseModel):
    """Response from URL inspection."""

    inspection_result: UrlInspectionResult
