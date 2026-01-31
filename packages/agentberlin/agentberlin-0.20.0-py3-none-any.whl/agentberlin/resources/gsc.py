"""Google Search Console resource for Agent Berlin SDK."""

from typing import Any, Dict, List, Optional

from .._http import HTTPClient
from ..models.gsc import (
    SearchAnalyticsResponse,
    SiteInfo,
    Sitemap,
    SitemapListResponse,
    UrlInspectionResponse,
)
from ..utils import get_project_domain


class GSCResource:
    """Resource for Google Search Console operations.

    Provides access to Search Console data through the Agent Berlin API.
    The site context is determined by the sandbox's PROJECT_DOMAIN environment
    variable, so methods don't require explicit siteUrl parameters.

    Example:
        # Search analytics query
        result = client.gsc.query(
            start_date="2024-01-01",
            end_date="2024-01-31",
            dimensions=["query", "page"],
            row_limit=100,
        )
        for row in result.rows:
            print(f"{row.keys}: {row.clicks} clicks")

        # Get site info
        site = client.gsc.get_site()
        print(f"Site: {site.site_url}")

        # List sitemaps
        sitemaps = client.gsc.list_sitemaps()
        for sm in sitemaps.sitemap:
            print(f"Sitemap: {sm.path}")

        # Inspect URL
        inspection = client.gsc.inspect_url("https://example.com/page")
        print(inspection.inspection_result.index_status_result)
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def query(
        self,
        start_date: str,
        end_date: str,
        *,
        dimensions: Optional[List[str]] = None,
        search_type: Optional[str] = None,
        dimension_filter_groups: Optional[List[Dict[str, Any]]] = None,
        aggregation_type: Optional[str] = None,
        row_limit: Optional[int] = None,
        start_row: Optional[int] = None,
        data_state: Optional[str] = None,
    ) -> SearchAnalyticsResponse:
        """Query search analytics data.

        Fetch search performance data including clicks, impressions, CTR,
        and position metrics.

        Args:
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format.
            dimensions: Dimensions to group by. Options: 'query', 'page',
                'country', 'device', 'searchAppearance', 'date'.
            search_type: Type of search. Options: 'web', 'image', 'video',
                'news', 'discover', 'googleNews'.
            dimension_filter_groups: Filters for the query. Each group contains
                a list of dimension filters with 'dimension', 'operator', and
                'expression' fields.
            aggregation_type: How data is aggregated. Options: 'auto',
                'byPage', 'byProperty'.
            row_limit: Maximum number of rows to return (default 1000, max 25000).
            start_row: Zero-based index of the first row to return.
            data_state: Data freshness. Options: 'final', 'all'.

        Returns:
            SearchAnalyticsResponse with rows of analytics data.

        Raises:
            AgentBerlinValidationError: If dates are invalid.
            AgentBerlinAPIError: If the API returns an error.
        """
        project_domain = get_project_domain()
        payload: Dict[str, Any] = {
            "project_domain": project_domain,
            "startDate": start_date,
            "endDate": end_date,
        }

        if dimensions is not None:
            payload["dimensions"] = dimensions
        if search_type is not None:
            payload["searchType"] = search_type
        if dimension_filter_groups is not None:
            payload["dimensionFilterGroups"] = dimension_filter_groups
        if aggregation_type is not None:
            payload["aggregationType"] = aggregation_type
        if row_limit is not None:
            payload["rowLimit"] = row_limit
        if start_row is not None:
            payload["startRow"] = start_row
        if data_state is not None:
            payload["dataState"] = data_state

        data = self._http.post("/gsc/searchanalytics/query", json=payload)
        return SearchAnalyticsResponse.model_validate(data)

    def get_site(self) -> SiteInfo:
        """Get information about the current site.

        Returns the site URL and permission level for the site associated
        with the current sandbox.

        Returns:
            SiteInfo with site URL and permission level.

        Raises:
            AgentBerlinAPIError: If the API returns an error.
        """
        project_domain = get_project_domain()
        data = self._http.post("/gsc/site", json={"project_domain": project_domain})
        return SiteInfo.model_validate(data)

    def list_sitemaps(self) -> SitemapListResponse:
        """List all sitemaps for the current site.

        Returns information about all sitemaps submitted for the site.

        Returns:
            SitemapListResponse with list of sitemaps.

        Raises:
            AgentBerlinAPIError: If the API returns an error.
        """
        project_domain = get_project_domain()
        data = self._http.post("/gsc/sitemaps", json={"project_domain": project_domain})
        return SitemapListResponse.model_validate(data)

    def get_sitemap(self, feedpath: str) -> Sitemap:
        """Get details of a specific sitemap.

        Args:
            feedpath: URL of the sitemap to retrieve.

        Returns:
            Sitemap with details about the sitemap.

        Raises:
            AgentBerlinNotFoundError: If the sitemap doesn't exist.
            AgentBerlinAPIError: If the API returns an error.
        """
        project_domain = get_project_domain()
        data = self._http.post(
            "/gsc/sitemaps/get",
            json={"project_domain": project_domain, "feedpath": feedpath},
        )
        return Sitemap.model_validate(data)

    def inspect_url(
        self,
        url: str,
        *,
        language_code: Optional[str] = None,
    ) -> UrlInspectionResponse:
        """Inspect a URL's index status.

        Get detailed information about how Google sees a specific URL,
        including indexing status, mobile usability, and rich results.

        Args:
            url: The fully-qualified URL to inspect.
            language_code: Optional language code for localized results
                (e.g., 'en-US', 'de').

        Returns:
            UrlInspectionResponse with inspection results.

        Raises:
            AgentBerlinValidationError: If URL is invalid.
            AgentBerlinAPIError: If the API returns an error.
        """
        project_domain = get_project_domain()
        payload: Dict[str, Any] = {
            "project_domain": project_domain,
            "inspectionUrl": url,
        }

        if language_code is not None:
            payload["languageCode"] = language_code

        data = self._http.post("/gsc/url-inspection/inspect", json=payload)
        return UrlInspectionResponse.model_validate(data)
