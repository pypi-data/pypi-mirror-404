"""Pytest fixtures for Agent Berlin SDK tests."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_token():
    """Provide a mock token for testing."""
    return "test-token-12345"


@pytest.fixture
def mock_env_token(mock_token):
    """Mock the AGENTBERLIN_TOKEN environment variable."""
    with patch.dict(os.environ, {"AGENTBERLIN_TOKEN": mock_token}):
        yield mock_token
