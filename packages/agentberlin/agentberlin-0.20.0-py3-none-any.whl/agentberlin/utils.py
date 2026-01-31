"""Utility functions for Agent Berlin SDK."""

import os


def get_project_domain() -> str:
    """Get the project domain from the environment.

    Returns:
        The project domain string.

    Raises:
        RuntimeError: If PROJECT_DOMAIN environment variable is not set.
    """
    domain = os.environ.get("PROJECT_DOMAIN")
    if not domain:
        raise RuntimeError(
            "PROJECT_DOMAIN environment variable is not set. "
            "This function should only be called within workflow scripts."
        )
    return domain
