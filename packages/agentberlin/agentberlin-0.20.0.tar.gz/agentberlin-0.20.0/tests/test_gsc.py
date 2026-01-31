"""Tests for GSC (Google Search Console) resource and models."""

import os
from unittest.mock import MagicMock, patch

import pytest

from agentberlin.models import (
    SearchAnalyticsResponse,
    SearchAnalyticsRow,
    SiteInfo,
    Sitemap,
    SitemapContent,
    SitemapListResponse,
    UrlInspectionResponse,
    UrlInspectionResult,
)
from agentberlin.resources.gsc import GSCResource


class TestGSCModels:
    """Tests for GSC Pydantic models."""

    def test_search_analytics_row(self):
        """Test SearchAnalyticsRow parsing."""
        data = {
            "keys": ["query1", "https://example.com/page1"],
            "clicks": 100.0,
            "impressions": 1000.0,
            "ctr": 0.1,
            "position": 5.5,
        }
        row = SearchAnalyticsRow.model_validate(data)
        assert row.keys == ["query1", "https://example.com/page1"]
        assert row.clicks == 100.0
        assert row.impressions == 1000.0
        assert row.ctr == 0.1
        assert row.position == 5.5

    def test_search_analytics_response(self):
        """Test SearchAnalyticsResponse parsing."""
        data = {
            "rows": [
                {
                    "keys": ["query1"],
                    "clicks": 50.0,
                    "impressions": 500.0,
                    "ctr": 0.1,
                    "position": 3.0,
                },
                {
                    "keys": ["query2"],
                    "clicks": 30.0,
                    "impressions": 300.0,
                    "ctr": 0.1,
                    "position": 7.0,
                },
            ],
            "response_aggregation_type": "auto",
        }
        response = SearchAnalyticsResponse.model_validate(data)
        assert len(response.rows) == 2
        assert response.rows[0].clicks == 50.0
        assert response.response_aggregation_type == "auto"

    def test_search_analytics_response_empty(self):
        """Test SearchAnalyticsResponse with empty rows."""
        data = {"rows": []}
        response = SearchAnalyticsResponse.model_validate(data)
        assert len(response.rows) == 0
        assert response.response_aggregation_type is None

    def test_site_info(self):
        """Test SiteInfo parsing."""
        data = {
            "site_url": "https://example.com/",
            "permission_level": "siteOwner",
        }
        site = SiteInfo.model_validate(data)
        assert site.site_url == "https://example.com/"
        assert site.permission_level == "siteOwner"

    def test_sitemap_content(self):
        """Test SitemapContent parsing."""
        data = {
            "type": "web",
            "submitted": 100,
            "indexed": 95,
        }
        content = SitemapContent.model_validate(data)
        assert content.type == "web"
        assert content.submitted == 100
        assert content.indexed == 95

    def test_sitemap(self):
        """Test Sitemap parsing."""
        data = {
            "path": "https://example.com/sitemap.xml",
            "last_submitted": "2024-01-15T10:00:00Z",
            "is_pending": False,
            "is_sitemaps_index": True,
            "last_downloaded": "2024-01-15T11:00:00Z",
            "warnings": 0,
            "errors": 0,
            "contents": [
                {"type": "web", "submitted": 50, "indexed": 48},
            ],
        }
        sitemap = Sitemap.model_validate(data)
        assert sitemap.path == "https://example.com/sitemap.xml"
        assert sitemap.is_sitemaps_index is True
        assert len(sitemap.contents) == 1
        assert sitemap.contents[0].type == "web"

    def test_sitemap_minimal(self):
        """Test Sitemap with minimal fields."""
        data = {"path": "https://example.com/sitemap.xml"}
        sitemap = Sitemap.model_validate(data)
        assert sitemap.path == "https://example.com/sitemap.xml"
        assert sitemap.last_submitted is None
        assert len(sitemap.contents) == 0

    def test_sitemap_list_response(self):
        """Test SitemapListResponse parsing."""
        data = {
            "sitemap": [
                {"path": "https://example.com/sitemap1.xml"},
                {"path": "https://example.com/sitemap2.xml"},
            ]
        }
        response = SitemapListResponse.model_validate(data)
        assert len(response.sitemap) == 2

    def test_url_inspection_result(self):
        """Test UrlInspectionResult parsing."""
        data = {
            "inspection_result_link": "https://search.google.com/search-console/inspect?...",
            "index_status_result": {
                "verdict": "PASS",
                "coverageState": "Indexed, not submitted in sitemap",
            },
            "mobile_usability_result": {"verdict": "PASS"},
            "rich_results_result": None,
        }
        result = UrlInspectionResult.model_validate(data)
        assert result.inspection_result_link is not None
        assert result.index_status_result["verdict"] == "PASS"

    def test_url_inspection_response(self):
        """Test UrlInspectionResponse parsing."""
        data = {
            "inspection_result": {
                "inspection_result_link": "https://search.google.com/...",
                "index_status_result": {"verdict": "PASS"},
            }
        }
        response = UrlInspectionResponse.model_validate(data)
        assert response.inspection_result.index_status_result["verdict"] == "PASS"


class TestGSCResource:
    """Tests for GSCResource methods."""

    @pytest.fixture
    def mock_http(self):
        """Create a mock HTTP client."""
        return MagicMock()

    @pytest.fixture
    def gsc_resource(self, mock_http):
        """Create a GSCResource with mock HTTP client."""
        return GSCResource(mock_http)

    @pytest.fixture(autouse=True)
    def mock_project_domain(self):
        """Mock PROJECT_DOMAIN environment variable for all tests."""
        with patch.dict(os.environ, {"PROJECT_DOMAIN": "example.com"}):
            yield

    def test_query_minimal(self, gsc_resource, mock_http):
        """Test query with minimal parameters."""
        mock_http.post.return_value = {
            "rows": [
                {
                    "keys": ["test query"],
                    "clicks": 10.0,
                    "impressions": 100.0,
                    "ctr": 0.1,
                    "position": 5.0,
                }
            ]
        }

        result = gsc_resource.query(
            start_date="2024-01-01",
            end_date="2024-01-31",
        )

        mock_http.post.assert_called_once_with(
            "/gsc/searchanalytics/query",
            json={
                "project_domain": "example.com",
                "startDate": "2024-01-01",
                "endDate": "2024-01-31",
            },
        )
        assert len(result.rows) == 1
        assert result.rows[0].clicks == 10.0

    def test_query_with_all_parameters(self, gsc_resource, mock_http):
        """Test query with all parameters."""
        mock_http.post.return_value = {"rows": []}

        result = gsc_resource.query(
            start_date="2024-01-01",
            end_date="2024-01-31",
            dimensions=["query", "page"],
            search_type="web",
            dimension_filter_groups=[
                {
                    "filters": [
                        {"dimension": "query", "operator": "contains", "expression": "seo"}
                    ]
                }
            ],
            aggregation_type="byPage",
            row_limit=100,
            start_row=0,
            data_state="final",
        )

        call_args = mock_http.post.call_args
        assert call_args[0][0] == "/gsc/searchanalytics/query"
        payload = call_args[1]["json"]
        assert payload["project_domain"] == "example.com"
        assert payload["startDate"] == "2024-01-01"
        assert payload["endDate"] == "2024-01-31"
        assert payload["dimensions"] == ["query", "page"]
        assert payload["searchType"] == "web"
        assert payload["aggregationType"] == "byPage"
        assert payload["rowLimit"] == 100
        assert payload["startRow"] == 0
        assert payload["dataState"] == "final"

    def test_get_site(self, gsc_resource, mock_http):
        """Test get_site method."""
        mock_http.post.return_value = {
            "site_url": "https://example.com/",
            "permission_level": "siteOwner",
        }

        result = gsc_resource.get_site()

        mock_http.post.assert_called_once_with(
            "/gsc/site",
            json={"project_domain": "example.com"},
        )
        assert result.site_url == "https://example.com/"
        assert result.permission_level == "siteOwner"

    def test_list_sitemaps(self, gsc_resource, mock_http):
        """Test list_sitemaps method."""
        mock_http.post.return_value = {
            "sitemap": [
                {"path": "https://example.com/sitemap.xml"},
            ]
        }

        result = gsc_resource.list_sitemaps()

        mock_http.post.assert_called_once_with(
            "/gsc/sitemaps",
            json={"project_domain": "example.com"},
        )
        assert len(result.sitemap) == 1

    def test_get_sitemap(self, gsc_resource, mock_http):
        """Test get_sitemap method."""
        mock_http.post.return_value = {
            "path": "https://example.com/sitemap.xml",
            "last_submitted": "2024-01-15T10:00:00Z",
        }

        result = gsc_resource.get_sitemap("https://example.com/sitemap.xml")

        mock_http.post.assert_called_once_with(
            "/gsc/sitemaps/get",
            json={
                "project_domain": "example.com",
                "feedpath": "https://example.com/sitemap.xml",
            },
        )
        assert result.path == "https://example.com/sitemap.xml"

    def test_inspect_url_minimal(self, gsc_resource, mock_http):
        """Test inspect_url with minimal parameters."""
        mock_http.post.return_value = {
            "inspection_result": {
                "index_status_result": {"verdict": "PASS"},
            }
        }

        result = gsc_resource.inspect_url("https://example.com/page")

        mock_http.post.assert_called_once_with(
            "/gsc/url-inspection/inspect",
            json={
                "project_domain": "example.com",
                "inspectionUrl": "https://example.com/page",
            },
        )
        assert result.inspection_result.index_status_result["verdict"] == "PASS"

    def test_inspect_url_with_language(self, gsc_resource, mock_http):
        """Test inspect_url with language code."""
        mock_http.post.return_value = {
            "inspection_result": {
                "index_status_result": {"verdict": "PASS"},
            }
        }

        result = gsc_resource.inspect_url(
            "https://example.com/page",
            language_code="de",
        )

        call_args = mock_http.post.call_args
        payload = call_args[1]["json"]
        assert payload["project_domain"] == "example.com"
        assert payload["inspectionUrl"] == "https://example.com/page"
        assert payload["languageCode"] == "de"

    def test_query_without_project_domain_env(self, mock_http):
        """Test that query raises error when PROJECT_DOMAIN is not set."""
        # Remove the PROJECT_DOMAIN from environment
        with patch.dict(os.environ, {}, clear=True):
            # Make sure PROJECT_DOMAIN is not set
            if "PROJECT_DOMAIN" in os.environ:
                del os.environ["PROJECT_DOMAIN"]

            gsc = GSCResource(mock_http)
            with pytest.raises(RuntimeError, match="PROJECT_DOMAIN environment variable is not set"):
                gsc.query(start_date="2024-01-01", end_date="2024-01-31")
