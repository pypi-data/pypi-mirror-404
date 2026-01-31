"""Pages resource for Agent Berlin SDK."""

from typing import Optional, Union

from .._http import HTTPClient
from ..models.search import PageDetailResponse, PageSearchResponse
from ..utils import get_project_domain


class PagesResource:
    """Resource for page operations.

    Example:
        # Search for pages
        results = client.pages.search(
            query="SEO best practices",
            limit=20
        )

        # Get page details
        page = client.pages.get(url="https://example.com/blog/seo-tips")
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search(
        self,
        query: str,
        *,
        domain: Optional[str] = None,
        limit: Optional[int] = None,
        status_code: Optional[Union[int, str]] = None,
        topic: Optional[str] = None,
        page_type: Optional[str] = None,
    ) -> PageSearchResponse:
        """Search for pages by semantic query.

        Can search your brand's pages, competitor pages, or all indexed pages.
        The project domain is automatically populated.

        Args:
            query: Search query for semantic matching.
            domain: Optional filter to a specific domain.
            limit: Maximum results (default: 10, max: 50).
            status_code: Filter by HTTP status (200, 404, 'error', 'redirect', 'success').
            topic: Filter by topic name.
            page_type: Filter by page type ('pillar' or 'landing').

        Returns:
            PageSearchResponse with matching pages.
        """
        payload: dict[str, object] = {
            "project_domain": get_project_domain(),
            "query": query,
        }
        if domain is not None:
            payload["domain"] = domain
        if limit is not None:
            payload["limit"] = limit
        if status_code is not None:
            payload["status_code"] = status_code
        if topic is not None:
            payload["topic"] = topic
        if page_type is not None:
            payload["page_type"] = page_type

        data = self._http.post("/pages/search", json=payload)
        return PageSearchResponse.model_validate(data)

    def get(
        self,
        url: str,
        *,
        content_length: Optional[int] = None,
    ) -> PageDetailResponse:
        """Get detailed information about a specific page.

        The project domain is automatically populated.

        Args:
            url: The page URL to look up.
            content_length: Max characters of content to return (default: 0).

        Returns:
            PageDetailResponse with page metadata, links, and topic info.
        """
        payload: dict[str, object] = {
            "project_domain": get_project_domain(),
            "url": url,
        }
        if content_length is not None:
            payload["content_length"] = content_length

        data = self._http.post("/pages/get", json=payload)
        return PageDetailResponse.model_validate(data)
