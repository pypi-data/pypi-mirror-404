"""Configuration for the Agent Berlin SDK."""

from dataclasses import dataclass, field
from typing import Optional

DEFAULT_BASE_URL = "https://backend.agentberlin.ai/sdk"
DEFAULT_TIMEOUT = 120

# Retry configuration defaults
DEFAULT_MAX_RETRIES = 5
DEFAULT_RETRY_BASE_DELAY = 30.0  # seconds
DEFAULT_MAX_RETRY_DELAY = 120.0  # seconds
DEFAULT_RETRY_JITTER = 5.0  # seconds (max random jitter)


@dataclass
class RetryConfig:
    """Retry configuration.

    Attributes:
        max_retries: Maximum number of retry attempts (0 to disable).
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.
        jitter: Maximum random jitter added to delay in seconds.
    """

    max_retries: int = DEFAULT_MAX_RETRIES
    base_delay: float = DEFAULT_RETRY_BASE_DELAY
    max_delay: float = DEFAULT_MAX_RETRY_DELAY
    jitter: float = DEFAULT_RETRY_JITTER


@dataclass
class Config:
    """SDK configuration.

    Attributes:
        base_url: Base URL for the Agent Berlin API.
        timeout: Request timeout in seconds.
        retry: Retry configuration.
    """

    base_url: str = DEFAULT_BASE_URL
    timeout: int = DEFAULT_TIMEOUT
    retry: Optional[RetryConfig] = field(default=None)

    def __post_init__(self) -> None:
        if self.retry is None:
            self.retry = RetryConfig()
