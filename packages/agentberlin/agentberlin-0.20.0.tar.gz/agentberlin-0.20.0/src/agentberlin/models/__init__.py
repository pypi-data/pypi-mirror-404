"""Pydantic models for Agent Berlin API responses."""

from .analytics import (
    AnalyticsResponse,
    ChannelBreakdown,
    CompetitorSummary,
    DailyTraffic,
    DataRange,
    TopicSummary,
    TrafficData,
    VisibilityData,
    VisibilityPoint,
)
from .brand import BrandProfileResponse, BrandProfileUpdateResponse
from .files import FileMetadata, FileUploadResponse
from .search import (
    KeywordResult,
    KeywordSearchResponse,
    PageDetailResponse,
    PageLink,
    PageLinksDetail,
    PageResult,
    PageSearchResponse,
    PageTopicInfo,
)
from .gsc import (
    SearchAnalyticsResponse,
    SearchAnalyticsRow,
    SiteInfo,
    Sitemap,
    SitemapContent,
    SitemapListResponse,
    UrlInspectionResponse,
    UrlInspectionResult,
)
from .google_cse import GoogleCSEResponse, GoogleCSEResult
from .serpapi import SerpApiMetadata, SerpApiResponse, SerpApiResult

__all__ = [
    # Analytics
    "AnalyticsResponse",
    "VisibilityData",
    "VisibilityPoint",
    "TrafficData",
    "ChannelBreakdown",
    "DailyTraffic",
    "TopicSummary",
    "CompetitorSummary",
    "DataRange",
    # Search
    "PageSearchResponse",
    "PageResult",
    "KeywordSearchResponse",
    "KeywordResult",
    "PageDetailResponse",
    "PageLinksDetail",
    "PageLink",
    "PageTopicInfo",
    # Brand
    "BrandProfileResponse",
    "BrandProfileUpdateResponse",
    # Files
    "FileMetadata",
    "FileUploadResponse",
    # Google Custom Search
    "GoogleCSEResponse",
    "GoogleCSEResult",
    # SerpApi
    "SerpApiResponse",
    "SerpApiResult",
    "SerpApiMetadata",
    # GSC (Google Search Console)
    "SearchAnalyticsResponse",
    "SearchAnalyticsRow",
    "SiteInfo",
    "Sitemap",
    "SitemapContent",
    "SitemapListResponse",
    "UrlInspectionResponse",
    "UrlInspectionResult",
]
