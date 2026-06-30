"""Configuration management for the XGIC GitLab GraphQL Client.

This module provides a clean, immutable configuration object used by
GitLabClient. It follows XGIC engineering standards for simplicity,
type safety, and ease of use with Grok Build.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GitLabConfig:
    """Immutable configuration for connecting to GitLab's GraphQL API.

    This dataclass is frozen to prevent accidental mutation after creation.
    It is designed to be instantiated once and passed into GitLabClient.

    Attributes:
        token: GitLab Personal Access Token (required). Must have `api` scope.
        base_url: Base URL of the GitLab instance (default: https://gitlab.com).
        timeout: Request timeout in seconds.
        verify_ssl: Whether to verify SSL certificates (set to False only for
                    self-signed certificates in internal environments).
    """

    token: str
    base_url: str = "https://gitlab.com"
    timeout: int = 30
    verify_ssl: bool = True

    def __post_init__(self) -> None:
        """Validate configuration on creation."""
        if not self.token or not isinstance(self.token, str):
            raise ConfigurationError(
                "GitLab token is required and must be a non-empty string."
            )

        if not self.base_url or not isinstance(self.base_url, str):
            raise ConfigurationError("base_url must be a non-empty string.")

        if self.timeout <= 0:
            raise ConfigurationError("timeout must be a positive integer.")

        # Normalize base_url (remove trailing slash)
        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @property
    def graphql_url(self) -> str:
        """Return the complete GraphQL endpoint URL."""
        return f"{self.base_url}/api/graphql"

    @classmethod
    def from_env(
        cls,
        token_env_var: str = "GITLAB_TOKEN",
        url_env_var: str = "GITLAB_URL",
    ) -> GitLabConfig:
        """Create a GitLabConfig instance from environment variables.

        This is a convenience method for scripts and Grok Build usage.

        Args:
            token_env_var: Name of the environment variable containing the token.
            url_env_var: Name of the environment variable containing the base URL.

        Raises:
            ConfigurationError: If the required token environment variable is not set.
        """
        token = os.getenv(token_env_var)
        if not token:
            raise ConfigurationError(
                f"Environment variable '{token_env_var}' is not set. "
                "Please set it to your GitLab Personal Access Token."
            )

        base_url = os.getenv(url_env_var, "https://gitlab.com")
        return cls(token=token, base_url=base_url)

    def __repr__(self) -> str:
        """Safe representation that does not leak the token."""
        return (
            f"GitLabConfig(base_url={self.base_url!r}, "
            f"timeout={self.timeout}, verify_ssl={self.verify_ssl})"
        )


# Import here to avoid circular import at module level
from .exceptions import ConfigurationError  # noqa: E402
