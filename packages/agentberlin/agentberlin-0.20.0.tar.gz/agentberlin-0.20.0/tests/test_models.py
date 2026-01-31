"""Tests for Pydantic models."""

import pytest

from agentberlin.models import (
    AnalyticsResponse,
    BrandProfileResponse,
    ChannelBreakdown,
    DataRange,
    KeywordResult,
    KeywordSearchResponse,
    PageDetailResponse,
    PageResult,
    PageSearchResponse,
    SERPResponse,
    SERPResult,
    TrafficData,
    VisibilityData,
)


class TestAnalyticsModels:
    """Tests for analytics models."""

    def test_analytics_response_minimal(self):
        """Test AnalyticsResponse with minimal data."""
        data = {
            "domain": "example.com",
            "domain_authority": 50,
            "visibility": {
                "current_percentage": 75.5,
                "ranking_stability": 0.85,
                "share_of_voice": 12.3,
                "history": [],
            },
            "traffic": {
                "total_sessions": 10000,
                "llm_sessions": 500,
                "channel_breakdown": {
                    "direct": 2000,
                    "organic_search": 5000,
                    "referral": 1000,
                    "organic_social": 500,
                    "llm": 500,
                    "other": 1000,
                },
                "daily_trend": [],
            },
            "topics": [],
            "competitors": [],
            "data_range": {"start": "2024-01-01", "end": "2024-01-31"},
            "last_updated": "2024-01-31T12:00:00Z",
        }

        response = AnalyticsResponse.model_validate(data)
        assert response.domain == "example.com"
        assert response.domain_authority == 50
        assert response.visibility.current_percentage == 75.5

    def test_channel_breakdown_defaults(self):
        """Test ChannelBreakdown default values."""
        breakdown = ChannelBreakdown()
        assert breakdown.direct == 0
        assert breakdown.organic_search == 0
        assert breakdown.llm == 0


class TestSearchModels:
    """Tests for search models."""

    def test_page_search_response(self):
        """Test PageSearchResponse parsing."""
        data = {
            "pages": [
                {"url": "https://example.com/page1", "title": "Page 1"},
                {"url": "https://example.com/page2", "title": "Page 2"},
            ],
            "total": 2,
        }

        response = PageSearchResponse.model_validate(data)
        assert len(response.pages) == 2
        assert response.pages[0].url == "https://example.com/page1"

    def test_keyword_result_optional_fields(self):
        """Test KeywordResult with optional fields."""
        # With all fields
        full_data = {
            "keyword": "seo tips",
            "volume": 1000,
            "difficulty": 45,
            "cpc": 2.50,
            "intent": "informational",
        }
        result = KeywordResult.model_validate(full_data)
        assert result.keyword == "seo tips"
        assert result.volume == 1000

        # With minimal fields
        minimal_data = {"keyword": "seo tips"}
        result = KeywordResult.model_validate(minimal_data)
        assert result.keyword == "seo tips"
        assert result.volume is None

    def test_page_detail_response(self):
        """Test PageDetailResponse with links."""
        data = {
            "url": "https://example.com/page",
            "title": "Test Page",
            "h1": "Welcome",
            "content_length": 5000,
            "links": {
                "inlinks": [
                    {
                        "source_url": "https://example.com/other",
                        "target_url": "https://example.com/page",
                        "domain_type": "internal",
                    }
                ],
                "outlinks": [],
            },
        }

        response = PageDetailResponse.model_validate(data)
        assert response.url == "https://example.com/page"
        assert len(response.links.inlinks) == 1


class TestBrandModels:
    """Tests for brand profile models."""

    def test_brand_profile_response(self):
        """Test BrandProfileResponse parsing."""
        data = {
            "domain": "example.com",
            "name": "Example Inc",
            "context": "A technology company",
            "domain_authority": 60,
            "competitors": ["competitor1.com", "competitor2.com"],
            "industries": ["technology", "saas"],
            "business_models": ["b2b"],
            "company_size": "startup",
            "target_customer_segments": ["enterprise"],
            "geographies": ["us", "eu"],
            "personas": ["cto", "developer"],
            "sitemaps": [],
            "profile_urls": [],
        }

        response = BrandProfileResponse.model_validate(data)
        assert response.domain == "example.com"
        assert len(response.competitors) == 2


class TestSERPModels:
    """Tests for SERP models."""

    def test_serp_response(self):
        """Test SERPResponse parsing."""
        data = {
            "query": "best seo tools",
            "results": [
                {
                    "title": "Top 10 SEO Tools",
                    "url": "https://example.com/seo-tools",
                    "snippet": "Discover the best SEO tools...",
                }
            ],
            "total": 1,
        }

        response = SERPResponse.model_validate(data)
        assert response.query == "best seo tools"
        assert len(response.results) == 1
        assert response.results[0].title == "Top 10 SEO Tools"
