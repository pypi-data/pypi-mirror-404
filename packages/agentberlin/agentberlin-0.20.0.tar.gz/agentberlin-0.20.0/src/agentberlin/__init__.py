"""Agent Berlin Python SDK.

A Python SDK for Agent Berlin - AI-powered SEO and AEO automation.

Example:
    from agentberlin import AgentBerlin

    # Set AGENTBERLIN_TOKEN environment variable or pass token directly
    client = AgentBerlin()

    # Get analytics
    analytics = client.analytics.get(project_domain="example.com")

    # Search pages
    pages = client.pages.search(project_domain="example.com", query="SEO tips")

    # Search keywords
    keywords = client.keywords.search(project_domain="example.com", query="marketing")

    # Get brand profile
    profile = client.brand.get_profile(project_domain="example.com")

    # Search using Google Custom Search
    results = client.google_cse.search(query="best seo tools")
"""

from .client import AgentBerlin
from .config import RetryConfig
from .exceptions import (
    AgentBerlinAPIError,
    AgentBerlinAuthenticationError,
    AgentBerlinConnectionError,
    AgentBerlinError,
    AgentBerlinNotFoundError,
    AgentBerlinRateLimitError,
    AgentBerlinServerError,
    AgentBerlinValidationError,
)
from .utils import get_project_domain

__version__ = "0.20.0"

__all__ = [
    "AgentBerlin",
    "RetryConfig",
    "AgentBerlinError",
    "AgentBerlinAuthenticationError",
    "AgentBerlinAPIError",
    "AgentBerlinNotFoundError",
    "AgentBerlinRateLimitError",
    "AgentBerlinServerError",
    "AgentBerlinValidationError",
    "AgentBerlinConnectionError",
    "get_project_domain",
]
