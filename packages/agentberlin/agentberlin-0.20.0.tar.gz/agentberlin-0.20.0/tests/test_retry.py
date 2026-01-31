"""Tests for HTTP client retry logic."""

from unittest.mock import Mock, patch

import pytest
import requests

from agentberlin._http import HTTPClient
from agentberlin.config import RetryConfig
from agentberlin.exceptions import (
    AgentBerlinConnectionError,
    AgentBerlinNotFoundError,
    AgentBerlinRateLimitError,
    AgentBerlinServerError,
)


class TestRetryLogic:
    """Tests for HTTP client retry logic."""

    def test_success_no_retry(self):
        """Successful request should not retry."""
        client = HTTPClient(token="test", base_url="http://test.com")
        with patch.object(client._session, "get") as mock_get:
            mock_get.return_value = Mock(ok=True, content=b"{}", json=lambda: {})
            client.get("/test")
            assert mock_get.call_count == 1

    def test_retry_on_timeout(self):
        """Should retry on timeout."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.Timeout(),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):  # Skip actual sleep
                client.get("/test")
            assert mock_get.call_count == 2

    def test_retry_on_connection_error(self):
        """Should retry on connection error."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.ConnectionError("Connection refused"),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.get("/test")
            assert mock_get.call_count == 2

    def test_retry_on_503(self):
        """Should retry on 503 Service Unavailable."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = [
                Mock(
                    ok=False,
                    status_code=503,
                    text="Service Unavailable",
                    content=b"{}",
                    json=lambda: {},
                    headers={},
                ),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.get("/test")
            assert mock_get.call_count == 2

    def test_retry_on_500(self):
        """Should retry on 500 Internal Server Error."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = [
                Mock(
                    ok=False,
                    status_code=500,
                    text="Internal Server Error",
                    content=b"{}",
                    json=lambda: {},
                    headers={},
                ),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.get("/test")
            assert mock_get.call_count == 2

    def test_retry_on_429(self):
        """Should retry on 429 Rate Limit."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = [
                Mock(
                    ok=False,
                    status_code=429,
                    text="Rate Limited",
                    content=b"{}",
                    json=lambda: {},
                    headers={},
                ),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.get("/test")
            assert mock_get.call_count == 2

    def test_no_retry_on_404(self):
        """Should not retry on 404."""
        config = RetryConfig(max_retries=3, base_delay=0.01)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.return_value = Mock(
                ok=False,
                status_code=404,
                text="Not Found",
                content=b"{}",
                json=lambda: {},
                headers={},
            )
            with pytest.raises(AgentBerlinNotFoundError):
                client.get("/test")
            assert mock_get.call_count == 1

    def test_no_retry_on_401(self):
        """Should not retry on 401 Unauthorized."""
        config = RetryConfig(max_retries=3, base_delay=0.01)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.return_value = Mock(
                ok=False,
                status_code=401,
                text="Unauthorized",
                content=b"{}",
                json=lambda: {},
                headers={},
            )
            from agentberlin.exceptions import AgentBerlinAuthenticationError

            with pytest.raises(AgentBerlinAuthenticationError):
                client.get("/test")
            assert mock_get.call_count == 1

    def test_no_retry_on_400(self):
        """Should not retry on 400 Bad Request."""
        config = RetryConfig(max_retries=3, base_delay=0.01)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.return_value = Mock(
                ok=False,
                status_code=400,
                text="Bad Request",
                content=b"{}",
                json=lambda: {},
                headers={},
            )
            from agentberlin.exceptions import AgentBerlinAPIError

            with pytest.raises(AgentBerlinAPIError):
                client.get("/test")
            assert mock_get.call_count == 1

    def test_max_retries_exhausted(self):
        """Should raise after max retries."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            with patch("time.sleep"):
                with pytest.raises(AgentBerlinConnectionError):
                    client.get("/test")
            assert mock_get.call_count == 3  # 1 initial + 2 retries

    def test_retry_after_header_respected(self):
        """Should use Retry-After header value."""
        config = RetryConfig(max_retries=1, base_delay=60.0, max_delay=120.0, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            with patch("time.sleep") as mock_sleep:
                mock_get.side_effect = [
                    Mock(
                        ok=False,
                        status_code=429,
                        text="Rate Limited",
                        content=b"{}",
                        json=lambda: {},
                        headers={"Retry-After": "5"},
                    ),
                    Mock(ok=True, content=b"{}", json=lambda: {}),
                ]
                client.get("/test")
                # Should sleep for 5 seconds (from header), not base_delay of 60
                mock_sleep.assert_called_with(5.0)

    def test_retry_after_capped_by_max_delay(self):
        """Retry-After should be capped by max_delay."""
        config = RetryConfig(max_retries=1, base_delay=10.0, max_delay=30.0, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            with patch("time.sleep") as mock_sleep:
                mock_get.side_effect = [
                    Mock(
                        ok=False,
                        status_code=429,
                        text="Rate Limited",
                        content=b"{}",
                        json=lambda: {},
                        headers={"Retry-After": "300"},  # Server says 300s
                    ),
                    Mock(ok=True, content=b"{}", json=lambda: {}),
                ]
                client.get("/test")
                # Should sleep for max_delay (30), not 300
                mock_sleep.assert_called_with(30.0)

    def test_retry_disabled(self):
        """max_retries=0 should disable retry."""
        config = RetryConfig(max_retries=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "get") as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout()
            with pytest.raises(AgentBerlinConnectionError):
                client.get("/test")
            assert mock_get.call_count == 1

    def test_exponential_backoff(self):
        """Verify exponential backoff calculation."""
        config = RetryConfig(max_retries=3, base_delay=1.0, max_delay=100.0, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )

        # Test delay calculation (0-indexed attempts)
        assert client._calculate_delay(0) == 1.0  # 1 * 2^0 = 1
        assert client._calculate_delay(1) == 2.0  # 1 * 2^1 = 2
        assert client._calculate_delay(2) == 4.0  # 1 * 2^2 = 4
        assert client._calculate_delay(3) == 8.0  # 1 * 2^3 = 8

    def test_exponential_backoff_capped(self):
        """Verify exponential backoff is capped at max_delay."""
        config = RetryConfig(max_retries=5, base_delay=10.0, max_delay=50.0, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )

        # 10 * 2^3 = 80, but should be capped at 50
        assert client._calculate_delay(3) == 50.0
        # 10 * 2^4 = 160, but should be capped at 50
        assert client._calculate_delay(4) == 50.0

    def test_post_retry(self):
        """POST requests should retry on transient errors."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "post") as mock_post:
            mock_post.side_effect = [
                requests.exceptions.Timeout(),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.post("/test", json={"data": "value"})
            assert mock_post.call_count == 2

    def test_patch_retry(self):
        """PATCH requests should retry on transient errors."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch.object(client._session, "patch") as mock_patch:
            mock_patch.side_effect = [
                requests.exceptions.Timeout(),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.patch("/test", json={"data": "value"})
            assert mock_patch.call_count == 2

    def test_upload_file_retry(self):
        """File upload should retry on transient errors."""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=0)
        client = HTTPClient(
            token="test", base_url="http://test.com", retry_config=config
        )
        with patch("requests.post") as mock_post:
            mock_post.side_effect = [
                requests.exceptions.Timeout(),
                Mock(ok=True, content=b"{}", json=lambda: {}),
            ]
            with patch("time.sleep"):
                client.upload_file("/test", b"file content", "test.txt")
            assert mock_post.call_count == 2

    def test_default_retry_config(self):
        """HTTPClient should use default RetryConfig if none provided."""
        client = HTTPClient(token="test", base_url="http://test.com")
        assert client._retry_config.max_retries == 5
        assert client._retry_config.base_delay == 30.0
        assert client._retry_config.max_delay == 120.0
        assert client._retry_config.jitter == 5.0


class TestRetryConfigDataclass:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """RetryConfig should have sensible defaults."""
        config = RetryConfig()
        assert config.max_retries == 5
        assert config.base_delay == 30.0
        assert config.max_delay == 120.0
        assert config.jitter == 5.0

    def test_custom_values(self):
        """RetryConfig should accept custom values."""
        config = RetryConfig(
            max_retries=10, base_delay=60.0, max_delay=180.0, jitter=10.0
        )
        assert config.max_retries == 10
        assert config.base_delay == 60.0
        assert config.max_delay == 180.0
        assert config.jitter == 10.0

    def test_disable_retry(self):
        """Setting max_retries=0 should disable retries."""
        config = RetryConfig(max_retries=0)
        assert config.max_retries == 0
