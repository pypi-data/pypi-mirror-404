"""Keywords resource for Agent Berlin SDK."""

from typing import Optional

from .._http import HTTPClient
from ..models.search import KeywordSearchResponse
from ..utils import get_project_domain


class KeywordsResource:
    """Resource for keyword operations.

    Example:
        results = client.keywords.search(query="digital marketing", limit=20)
        for kw in results.keywords:
            print(f"{kw.keyword}: volume={kw.volume}, difficulty={kw.difficulty}")
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def search(
        self,
        query: str,
        *,
        limit: Optional[int] = None,
    ) -> KeywordSearchResponse:
        """Search for keywords by semantic query.

        Returns relevant keywords with metadata including search volume,
        difficulty, CPC, and intent classification. The project domain is automatically populated.

        Args:
            query: Search query for semantic matching.
            limit: Maximum results (default: 10, max: 50).

        Returns:
            KeywordSearchResponse with matching keywords and metadata.
        """
        payload: dict[str, object] = {
            "project_domain": get_project_domain(),
            "query": query,
        }
        if limit is not None:
            payload["limit"] = limit

        data = self._http.post("/keywords/search", json=payload)
        return KeywordSearchResponse.model_validate(data)
