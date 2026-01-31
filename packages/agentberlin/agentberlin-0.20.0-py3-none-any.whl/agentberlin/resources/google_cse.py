"""Google Custom Search resource for Agent Berlin SDK."""

from typing import Optional

from .._http import HTTPClient
from ..models.google_cse import GoogleCSEResponse


class GoogleCSEResource:
    """Resource for Google Custom Search Engine operations.

    Provides access to Google Custom Search for simple, fast web searches.

    Example:
        results = client.google_cse.search(
            query="best seo tools",
            max_results=5,
            country="us",
            language="lang_en"
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
        max_results: Optional[int] = None,
        country: Optional[str] = None,
        language: Optional[str] = None,
    ) -> GoogleCSEResponse:
        """Search using Google Custom Search Engine.

        Returns titles, URLs, and snippets of top-ranking pages.

        Args:
            query: The search query to execute.
            max_results: Number of results (1-10, default: 10).
            country: ISO 3166-1 alpha-2 country code (e.g., 'us', 'gb', 'de').
            language: ISO 639-1 language code prefixed with 'lang_'
                     (e.g., 'lang_en', 'lang_de', 'lang_fr').

        Returns:
            GoogleCSEResponse with search results.
        """
        payload: dict[str, object] = {"query": query}
        if max_results is not None:
            payload["max_results"] = max_results
        if country is not None:
            payload["country"] = country
        if language is not None:
            payload["language"] = language

        data = self._http.post("/google-cse/search", json=payload)
        return GoogleCSEResponse.model_validate(data)
