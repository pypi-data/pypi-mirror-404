"""SerpApi resource for Agent Berlin SDK."""

from typing import Optional

from .._http import HTTPClient
from ..models.serpapi import SerpApiResponse


class SerpApiResource:
    """Resource for SerpApi search operations.

    Provides access to multiple search engines (Google, Bing) and search types
    (web, news, images, videos, shopping) through SerpApi.

    Example:
        # Google web search
        results = client.serpapi.search(
            query="best seo tools",
            engine="google",
            max_results=10,
        )

        # Bing search
        results = client.serpapi.search(
            query="best seo tools",
            engine="bing",
            country="us",
        )

        # Google News search
        results = client.serpapi.search(
            query="AI technology",
            engine="google",
            search_type="news",
        )

        # Mobile search results
        results = client.serpapi.search(
            query="best restaurants",
            device="mobile",
            country="us",
        )

        for result in results.results:
            print(f"{result.title}: {result.url}")
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search(
        self,
        query: str,
        *,
        engine: str = "google",
        search_type: str = "web",
        device: Optional[str] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
        max_results: Optional[int] = None,
    ) -> SerpApiResponse:
        """Search using SerpApi.

        Supports multiple search engines and search types for comprehensive
        SERP analysis.

        Args:
            query: The search query to execute.
            engine: Search engine to use. Options: 'google', 'bing'.
                   Default: 'google'.
            search_type: Type of search. Options: 'web', 'news', 'images',
                        'videos', 'shopping'. Default: 'web'.
                        Note: Non-web search types are only available for Google.
            device: Device type for results. Options: 'desktop', 'tablet',
                   'mobile'. Default: 'desktop'.
            country: ISO 3166-1 alpha-2 country code (e.g., 'us', 'gb', 'de').
            language: ISO 639-1 language code (e.g., 'en', 'de', 'fr').
            max_results: Number of results (1-100, default: 10).

        Returns:
            SerpApiResponse with search results and metadata.
        """
        payload: dict[str, object] = {
            "query": query,
            "engine": engine,
            "search_type": search_type,
        }
        if device is not None:
            payload["device"] = device
        if country is not None:
            payload["country"] = country
        if language is not None:
            payload["language"] = language
        if max_results is not None:
            payload["max_results"] = max_results

        data = self._http.post("/serpapi/search", json=payload)
        return SerpApiResponse.model_validate(data)
