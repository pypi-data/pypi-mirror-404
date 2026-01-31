"""Custom exceptions for the Agent Berlin SDK.

Exception hierarchy:
    AgentBerlinError (base)
    ├── AgentBerlinAuthenticationError  - Token missing or invalid
    ├── AgentBerlinAPIError             - API returned an error
    │   ├── AgentBerlinNotFoundError    - Resource not found (404)
    │   ├── AgentBerlinRateLimitError   - Rate limit exceeded (429)
    │   └── AgentBerlinServerError      - Server error (5xx)
    ├── AgentBerlinValidationError      - Invalid parameters
    └── AgentBerlinConnectionError      - Network/connection issues
"""

from typing import Any, Dict, Optional


class AgentBerlinError(Exception):
    """Base exception for all Agent Berlin SDK errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgentBerlinAuthenticationError(AgentBerlinError):
    """Raised when authentication fails or token is missing."""

    pass


class AgentBerlinAPIError(AgentBerlinError):
    """Raised when the API returns an error response."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.status_code = status_code
        self.error_code = error_code


class AgentBerlinNotFoundError(AgentBerlinAPIError):
    """Raised when a requested resource is not found (404)."""

    pass


class AgentBerlinRateLimitError(AgentBerlinAPIError):
    """Raised when rate limit is exceeded (429)."""

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, status_code=429, details=details)
        self.retry_after = retry_after


class AgentBerlinServerError(AgentBerlinAPIError):
    """Raised when the server returns a 5xx error."""

    pass


class AgentBerlinValidationError(AgentBerlinError):
    """Raised when request parameters fail validation."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message, details)
        self.field = field


class AgentBerlinConnectionError(AgentBerlinError):
    """Raised when there's a network or connection error."""

    pass
