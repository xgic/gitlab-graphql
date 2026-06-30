"""XGIC GitLab GraphQL Client.

Public exports for `xgic.gitlab.graphql`.

Recommended usage:
    from xgic.gitlab.graphql import GitLabClient
"""

from .client import GitLabClient
from .config import GitLabConfig
from .exceptions import (
    AuthenticationError,
    ConfigurationError,
    GitLabError,
    GraphQLError,
    WorkItemCreationError,
)
from .models import BaseWorkItem, Issue, MergeRequest, Task

__all__ = [
    "GitLabClient",
    "GitLabConfig",
    "GitLabError",
    "GraphQLError",
    "AuthenticationError",
    "WorkItemCreationError",
    "ConfigurationError",
    "BaseWorkItem",
    "Issue",
    "Task",
    "MergeRequest",
]
