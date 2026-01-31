"""Analytics resource for Agent Berlin SDK."""

from .._http import HTTPClient
from ..models.analytics import AnalyticsResponse
from ..utils import get_project_domain


class AnalyticsResource:
    """Resource for analytics operations.

    Example:
        analytics = client.analytics.get()
        print(f"Visibility: {analytics.visibility.current_percentage}%")
        print(f"LLM Sessions: {analytics.traffic.llm_sessions}")
    """

    def __init__(self, http: HTTPClient) -> None:
        self._http = http

    def get(self) -> AnalyticsResponse:
        """Get analytics data for the project.

        Fetch analytics dashboard data including visibility, traffic,
        topics, and competitors. The project domain is automatically populated.

        Returns:
            AnalyticsResponse with comprehensive analytics data.

        Raises:
            AgentBerlinNotFoundError: If the domain doesn't exist.
            AgentBerlinAPIError: If the API returns an error.
        """
        data = self._http.post(
            "/analytics",
            json={"project_domain": get_project_domain()},
        )
        return AnalyticsResponse.model_validate(data)
