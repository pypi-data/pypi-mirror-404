"""Pydantic models for search API responses (pages, keywords)."""

from typing import List, Optional

from pydantic import BaseModel, Field

# Page search models


class PageResult(BaseModel):
    """Single page in search results."""

    url: str
    title: str


class PageSearchResponse(BaseModel):
    """Response for page search."""

    pages: List[PageResult] = Field(default_factory=list)
    total: int


# Keyword search models


class KeywordResult(BaseModel):
    """Single keyword with metadata."""

    keyword: str
    volume: Optional[int] = None
    difficulty: Optional[int] = None  # 0-100
    cpc: Optional[float] = None
    intent: Optional[str] = None  # informational, commercial, transactional, navigational


class KeywordSearchResponse(BaseModel):
    """Response for keyword search."""

    keywords: List[KeywordResult] = Field(default_factory=list)
    total: int


# Get page models


class PageLink(BaseModel):
    """Link in page details."""

    source_url: str
    target_url: str
    anchor_text: Optional[str] = None
    domain_type: str  # "internal" or "external"
    source_title: Optional[str] = None
    target_title: Optional[str] = None


class PageLinksDetail(BaseModel):
    """Links for a page."""

    inlinks: List[PageLink] = Field(default_factory=list)
    outlinks: List[PageLink] = Field(default_factory=list)


class PageTopicInfo(BaseModel):
    """Topic classification for a page."""

    topics: List[str] = Field(default_factory=list)
    topic_scores: List[float] = Field(default_factory=list)
    page_type: Optional[str] = None  # "pillar" or "landing"
    assigned_topic: Optional[str] = None


class PageDetailResponse(BaseModel):
    """Detailed page information."""

    url: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    domain: Optional[str] = None
    links: Optional[PageLinksDetail] = None
    topic_info: Optional[PageTopicInfo] = None
    content_preview: Optional[str] = None
    content_length: int = 0
