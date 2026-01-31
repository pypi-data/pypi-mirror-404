"""Tests for custom exceptions."""

import pytest

from agentberlin.exceptions import (
    AgentBerlinAPIError,
    AgentBerlinAuthenticationError,
    AgentBerlinConnectionError,
    AgentBerlinError,
    AgentBerlinNotFoundError,
    AgentBerlinRateLimitError,
    AgentBerlinServerError,
    AgentBerlinValidationError,
)


class TestExceptions:
    """Tests for exception classes."""

    def test_base_exception(self):
        """Test base AgentBerlinError."""
        exc = AgentBerlinError("Test error", details={"key": "value"})
        assert exc.message == "Test error"
        assert exc.details == {"key": "value"}
        assert str(exc) == "Test error"

    def test_authentication_error(self):
        """Test AgentBerlinAuthenticationError."""
        exc = AgentBerlinAuthenticationError("Invalid token")
        assert isinstance(exc, AgentBerlinError)
        assert exc.message == "Invalid token"

    def test_api_error_with_status_code(self):
        """Test AgentBerlinAPIError with status code."""
        exc = AgentBerlinAPIError(
            message="Bad request",
            status_code=400,
            error_code="INVALID_INPUT",
            details={"field": "project_domain"},
        )
        assert exc.status_code == 400
        assert exc.error_code == "INVALID_INPUT"

    def test_not_found_error(self):
        """Test AgentBerlinNotFoundError."""
        exc = AgentBerlinNotFoundError(
            message="Domain not found",
            status_code=404,
        )
        assert isinstance(exc, AgentBerlinAPIError)
        assert exc.status_code == 404

    def test_rate_limit_error(self):
        """Test AgentBerlinRateLimitError."""
        exc = AgentBerlinRateLimitError(
            message="Rate limit exceeded",
            retry_after=60,
        )
        assert exc.status_code == 429
        assert exc.retry_after == 60

    def test_server_error(self):
        """Test AgentBerlinServerError."""
        exc = AgentBerlinServerError(
            message="Internal server error",
            status_code=500,
        )
        assert isinstance(exc, AgentBerlinAPIError)
        assert exc.status_code == 500

    def test_validation_error(self):
        """Test AgentBerlinValidationError."""
        exc = AgentBerlinValidationError(
            message="Invalid project_domain",
            field="project_domain",
        )
        assert exc.field == "project_domain"

    def test_connection_error(self):
        """Test AgentBerlinConnectionError."""
        exc = AgentBerlinConnectionError("Connection timed out")
        assert isinstance(exc, AgentBerlinError)
        assert exc.message == "Connection timed out"

    def test_exception_hierarchy(self):
        """Test exception inheritance hierarchy."""
        # All exceptions should inherit from AgentBerlinError
        assert issubclass(AgentBerlinAuthenticationError, AgentBerlinError)
        assert issubclass(AgentBerlinAPIError, AgentBerlinError)
        assert issubclass(AgentBerlinValidationError, AgentBerlinError)
        assert issubclass(AgentBerlinConnectionError, AgentBerlinError)

        # API-specific errors should inherit from AgentBerlinAPIError
        assert issubclass(AgentBerlinNotFoundError, AgentBerlinAPIError)
        assert issubclass(AgentBerlinRateLimitError, AgentBerlinAPIError)
        assert issubclass(AgentBerlinServerError, AgentBerlinAPIError)
