"""Tests for the main AgentBerlin client."""

import os
from unittest.mock import patch

import pytest

from agentberlin import AgentBerlin
from agentberlin.exceptions import AgentBerlinAuthenticationError


class TestClientInitialization:
    """Tests for client initialization."""

    def test_init_with_token(self, mock_token):
        """Test initialization with explicit token."""
        client = AgentBerlin(token=mock_token)
        assert client._token == mock_token

    def test_init_with_env_token(self, mock_env_token):
        """Test initialization with environment variable token."""
        client = AgentBerlin()
        assert client._token == mock_env_token

    def test_init_without_token_raises_error(self):
        """Test that missing token raises AgentBerlinAuthenticationError."""
        with patch.dict(os.environ, {}, clear=True):
            # Ensure AGENTBERLIN_TOKEN is not set
            if "AGENTBERLIN_TOKEN" in os.environ:
                del os.environ["AGENTBERLIN_TOKEN"]

            with pytest.raises(AgentBerlinAuthenticationError) as exc_info:
                AgentBerlin()

            assert "AGENTBERLIN_TOKEN" in str(exc_info.value)

    def test_init_with_custom_base_url(self, mock_token):
        """Test initialization with custom base URL."""
        custom_url = "https://custom.api.example.com/sdk"
        client = AgentBerlin(token=mock_token, base_url=custom_url)
        assert client._config.base_url == custom_url

    def test_init_with_custom_timeout(self, mock_token):
        """Test initialization with custom timeout."""
        client = AgentBerlin(token=mock_token, timeout=60)
        assert client._config.timeout == 60

    def test_client_has_all_resources(self, mock_token):
        """Test that client has all expected resources."""
        client = AgentBerlin(token=mock_token)

        assert hasattr(client, "analytics")
        assert hasattr(client, "pages")
        assert hasattr(client, "keywords")
        assert hasattr(client, "brand")
        assert hasattr(client, "serp")
        assert hasattr(client, "gsc")

    def test_client_repr(self, mock_token):
        """Test client string representation."""
        client = AgentBerlin(token=mock_token)
        repr_str = repr(client)

        assert "AgentBerlin" in repr_str
        assert "base_url" in repr_str
