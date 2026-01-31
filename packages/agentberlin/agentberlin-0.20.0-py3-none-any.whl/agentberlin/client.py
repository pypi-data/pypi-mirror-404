"""Main client class for Agent Berlin SDK.

Example:
    from agentberlin import AgentBerlin

    client = AgentBerlin()  # Uses AGENTBERLIN_TOKEN env var

    # Get analytics
    analytics = client.analytics.get(project_domain="example.com")
    print(f"Traffic: {analytics.traffic.total_sessions}")

    # Search pages
    pages = client.pages.search(project_domain="example.com", query="SEO tips")
    for page in pages.pages:
        print(f"  - {page.title}: {page.url}")
"""

import os
from typing import Optional

from ._http import HTTPClient
from .config import DEFAULT_BASE_URL, DEFAULT_TIMEOUT, Config, RetryConfig
from .exceptions import AgentBerlinAuthenticationError
from .resources.analytics import AnalyticsResource
from .resources.brand import BrandResource
from .resources.files import FilesResource
from .resources.google_cse import GoogleCSEResource
from .resources.gsc import GSCResource
from .resources.keywords import KeywordsResource
from .resources.pages import PagesResource
from .resources.serpapi import SerpApiResource


class AgentBerlin:
    """Client for the Agent Berlin API.

    Args:
        token: API token. If not provided, reads from AGENTBERLIN_TOKEN env var.
        base_url: Base URL for the API. Defaults to https://backend.agentberlin.ai/sdk
        timeout: Request timeout in seconds. Defaults to 120.
        retry: Retry configuration. Defaults to RetryConfig() with 5 retries,
               30s base delay, 120s max delay. Pass RetryConfig(max_retries=0)
               to disable retries.

    Raises:
        AgentBerlinAuthenticationError: If no token is provided or found in env.

    Attributes:
        analytics: Analytics resource for fetching analytics data.
        pages: Pages resource for searching and getting page details.
        keywords: Keywords resource for semantic keyword search.
        brand: Brand resource for managing brand profiles.
        google_cse: Google Custom Search resource for simple Google web searches.
        serpapi: SerpApi resource for multi-engine search (Google, Bing) with
                 various search types (web, news, images, videos, shopping).
        files: Files resource for uploading workflow output files.
        gsc: Google Search Console resource for search analytics and URL inspection.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        retry: Optional[RetryConfig] = None,
    ) -> None:
        # Get token from parameter or environment
        self._token = token or os.environ.get("AGENTBERLIN_TOKEN")
        if not self._token:
            raise AgentBerlinAuthenticationError(
                "No API token provided. Set AGENTBERLIN_TOKEN environment variable "
                "or pass token parameter to AgentBerlin()."
            )

        # Initialize config
        self._config = Config(
            base_url=base_url or DEFAULT_BASE_URL,
            timeout=timeout,
            retry=retry,
        )

        # Initialize HTTP client
        self._http = HTTPClient(
            token=self._token,
            base_url=self._config.base_url,
            timeout=self._config.timeout,
            retry_config=self._config.retry,
        )

        # Initialize resources
        self.analytics = AnalyticsResource(self._http)
        self.pages = PagesResource(self._http)
        self.keywords = KeywordsResource(self._http)
        self.brand = BrandResource(self._http)
        self.google_cse = GoogleCSEResource(self._http)
        self.serpapi = SerpApiResource(self._http)
        self.files = FilesResource(self._http)
        self.gsc = GSCResource(self._http)

    def __repr__(self) -> str:
        return f"AgentBerlin(base_url='{self._config.base_url}')"
