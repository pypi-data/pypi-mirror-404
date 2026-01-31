"""Pydantic models for analytics API responses."""

from typing import List

from pydantic import BaseModel, Field


class VisibilityPoint(BaseModel):
    """Single point in visibility history."""

    date: str
    percentage: float


class VisibilityData(BaseModel):
    """Visibility metrics for a domain."""

    current_percentage: float
    ranking_stability: float
    share_of_voice: float
    history: List[VisibilityPoint] = Field(default_factory=list)


class ChannelBreakdown(BaseModel):
    """Traffic breakdown by channel."""

    direct: int = 0
    organic_search: int = 0
    referral: int = 0
    organic_social: int = 0
    llm: int = 0
    other: int = 0


class DailyTraffic(BaseModel):
    """Daily traffic data point."""

    date: str
    sessions: int
    llm_sessions: int


class TrafficData(BaseModel):
    """Traffic metrics for a domain."""

    total_sessions: int
    llm_sessions: int
    channel_breakdown: ChannelBreakdown
    daily_trend: List[DailyTraffic] = Field(default_factory=list)


class TopicSummary(BaseModel):
    """Summary of a topic's performance."""

    name: str
    appearances: int
    avg_position: float
    topical_authority: float
    trend: str  # "up", "down", "stable"


class CompetitorSummary(BaseModel):
    """Summary of competitor visibility."""

    name: str
    visibility: float
    share_of_voice: float


class DataRange(BaseModel):
    """Date range for the analytics data."""

    start: str
    end: str


class AnalyticsResponse(BaseModel):
    """Complete analytics response for a domain."""

    domain: str
    domain_authority: int
    visibility: VisibilityData
    traffic: TrafficData
    topics: List[TopicSummary] = Field(default_factory=list)
    competitors: List[CompetitorSummary] = Field(default_factory=list)
    data_range: DataRange
    last_updated: str
