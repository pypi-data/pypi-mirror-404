"""Internal HTTP client for Agent Berlin SDK."""

import logging
import os
import random
import time
from typing import Any, Callable, Dict, Optional

import requests

from .config import RetryConfig
from .exceptions import (
    AgentBerlinAPIError,
    AgentBerlinAuthenticationError,
    AgentBerlinConnectionError,
    AgentBerlinNotFoundError,
    AgentBerlinRateLimitError,
    AgentBerlinServerError,
)

__version__ = "0.1.0"
logger = logging.getLogger("agentberlin")


class HTTPClient:
    """Internal HTTP client with authentication, error handling, and retry logic."""

    # Status codes that should trigger retry
    RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

    def __init__(
        self,
        token: str,
        base_url: str,
        timeout: int = 30,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._retry_config = retry_config or RetryConfig()
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": f"agentberlin-python/{__version__}",
            }
        )

        # Add workflow context headers if running inside a workflow sandbox
        workflow_id = os.environ.get("WORKFLOW_ID")
        workflow_run_id = os.environ.get("WORKFLOW_RUN_ID")
        if workflow_id:
            self._session.headers["X-Workflow-ID"] = workflow_id
        if workflow_run_id:
            self._session.headers["X-Workflow-Run-ID"] = workflow_run_id

    def _calculate_delay(self, attempt: int, retry_after: Optional[int] = None) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (0-indexed).
            retry_after: Server-specified retry delay (from Retry-After header).

        Returns:
            Delay in seconds.
        """
        if retry_after is not None:
            # Use server-specified delay, but cap it
            return min(retry_after, self._retry_config.max_delay)

        # Exponential backoff with jitter
        base = self._retry_config.base_delay * (2**attempt)
        jitter = random.uniform(0, self._retry_config.jitter)
        delay = min(base + jitter, self._retry_config.max_delay)
        return delay

    def _should_retry(self, exception: Exception) -> bool:
        """Determine if an exception should trigger a retry.

        Args:
            exception: The exception that was raised.

        Returns:
            True if the request should be retried.
        """
        # Retry on connection/timeout errors
        if isinstance(exception, AgentBerlinConnectionError):
            return True

        # Retry on specific server errors
        if isinstance(exception, AgentBerlinServerError):
            return True

        # Retry on rate limit
        if isinstance(exception, AgentBerlinRateLimitError):
            return True

        # Don't retry on auth, not found, validation, or other client errors
        return False

    def _get_retry_after(self, exception: Exception) -> Optional[int]:
        """Extract Retry-After value from exception if available."""
        if isinstance(exception, AgentBerlinRateLimitError):
            return exception.retry_after
        return None

    def _execute_with_retry(
        self,
        operation: Callable[[], requests.Response],
        operation_name: str,
    ) -> Dict[str, Any]:
        """Execute an HTTP operation with retry logic.

        Args:
            operation: Callable that performs the HTTP request.
            operation_name: Name of the operation for logging.

        Returns:
            Response data as dict.

        Raises:
            AgentBerlinAPIError: On API errors after retries exhausted.
            AgentBerlinConnectionError: On network errors after retries exhausted.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self._retry_config.max_retries + 1):
            try:
                response = operation()
                return self._handle_response(response)

            except requests.exceptions.Timeout:
                last_exception = AgentBerlinConnectionError(
                    f"Request timed out after {self._timeout}s"
                )
            except requests.exceptions.ConnectionError as e:
                last_exception = AgentBerlinConnectionError(f"Connection error: {e}")
            except requests.exceptions.RequestException as e:
                last_exception = AgentBerlinConnectionError(f"Request failed: {e}")
            except (AgentBerlinServerError, AgentBerlinRateLimitError) as e:
                last_exception = e
            except AgentBerlinAPIError:
                # Non-retryable API errors (auth, not found, validation)
                raise

            # Check if we should retry
            if not self._should_retry(last_exception):
                raise last_exception

            # Check if we have retries left
            if attempt >= self._retry_config.max_retries:
                logger.warning(
                    f"[{operation_name}] Max retries ({self._retry_config.max_retries}) "
                    f"exhausted. Last error: {last_exception}"
                )
                raise last_exception

            # Calculate delay and wait
            retry_after = self._get_retry_after(last_exception)
            delay = self._calculate_delay(attempt, retry_after)

            logger.info(
                f"[{operation_name}] Attempt {attempt + 1} failed: {last_exception}. "
                f"Retrying in {delay:.1f}s..."
            )
            time.sleep(delay)

        # Should not reach here, but just in case
        raise last_exception  # type: ignore

    def post(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a POST request with retry logic.

        Args:
            path: API endpoint path.
            json: Request body as dict.

        Returns:
            Response data as dict.

        Raises:
            AgentBerlinAPIError: On API errors.
            AgentBerlinConnectionError: On network errors.
        """
        url = f"{self._base_url}{path}"

        def operation() -> requests.Response:
            return self._session.post(url, json=json, timeout=self._timeout)

        return self._execute_with_retry(operation, f"POST {path}")

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a GET request with retry logic.

        Args:
            path: API endpoint path.
            params: Query parameters.

        Returns:
            Response data as dict.

        Raises:
            AgentBerlinAPIError: On API errors.
            AgentBerlinConnectionError: On network errors.
        """
        url = f"{self._base_url}{path}"

        def operation() -> requests.Response:
            return self._session.get(url, params=params, timeout=self._timeout)

        return self._execute_with_retry(operation, f"GET {path}")

    def patch(
        self,
        path: str,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make a PATCH request with retry logic.

        Args:
            path: API endpoint path.
            json: Request body as dict.

        Returns:
            Response data as dict.

        Raises:
            AgentBerlinAPIError: On API errors.
            AgentBerlinConnectionError: On network errors.
        """
        url = f"{self._base_url}{path}"

        def operation() -> requests.Response:
            return self._session.patch(url, json=json, timeout=self._timeout)

        return self._execute_with_retry(operation, f"PATCH {path}")

    def upload_file(
        self,
        path: str,
        file_data: bytes,
        filename: str,
        content_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Upload a file with retry logic.

        Args:
            path: API endpoint path.
            file_data: Raw bytes of the file.
            filename: Name of the file.
            content_type: MIME type of the file.

        Returns:
            Response data as dict.

        Raises:
            AgentBerlinAPIError: On API errors.
            AgentBerlinConnectionError: On network errors.
        """
        url = f"{self._base_url}{path}"
        files = {"file": (filename, file_data, content_type or "application/octet-stream")}
        headers = {
            "Authorization": f"Bearer {self._token}",
            "User-Agent": f"agentberlin-python/{__version__}",
        }

        def operation() -> requests.Response:
            return requests.post(url, files=files, headers=headers, timeout=self._timeout)

        return self._execute_with_retry(operation, f"UPLOAD {path}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle response and raise appropriate exceptions."""
        # Success
        if response.ok:
            if response.content:
                return response.json()  # type: ignore[no-any-return]
            return {}

        # Parse error response
        try:
            error_data = response.json()
            message = error_data.get("message", error_data.get("error", "Unknown error"))
            error_code = error_data.get("code")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
            error_code = None
            error_data = {}

        # Map status codes to exceptions
        if response.status_code == 401:
            raise AgentBerlinAuthenticationError(message, details=error_data)
        elif response.status_code == 404:
            raise AgentBerlinNotFoundError(
                message,
                status_code=404,
                error_code=error_code,
                details=error_data,
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise AgentBerlinRateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                details=error_data,
            )
        elif response.status_code >= 500:
            raise AgentBerlinServerError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=error_data,
            )
        else:
            raise AgentBerlinAPIError(
                message,
                status_code=response.status_code,
                error_code=error_code,
                details=error_data,
            )
