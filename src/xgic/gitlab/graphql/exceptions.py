"""Custom exceptions for the XGIC GitLab GraphQL Client.

These exceptions provide clear, actionable error information for both
human developers and Grok Build automation scripts.
"""

from typing import Any


class GitLabError(Exception):
    """Base exception for all errors raised by the XGIC GitLab GraphQL Client.

    Attributes:
        message: Human-readable error description.
        original_error: The underlying exception that caused this error, if any.
    """

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_error = original_error

    def __str__(self) -> str:
        if self.original_error:
            return f"{self.message} (caused by: {self.original_error})"
        return self.message


class GraphQLError(GitLabError):
    """Raised when the GitLab GraphQL API returns one or more errors.

    This typically indicates a problem with the query/mutation itself
    (e.g. invalid input, permission denied, validation failure).

    Attributes:
        errors: The raw list of error dictionaries returned by GitLab.
    """

    def __init__(
        self, errors: list[dict[str, Any]], message: str | None = None
    ) -> None:
        if message is None:
            # Create a concise summary for the first error
            if errors:
                first = errors[0]
                msg = first.get("message", "Unknown GraphQL error")
                if len(errors) > 1:
                    msg += f" (+{len(errors) - 1} more errors)"
                message = msg
            else:
                message = "GraphQL response contained errors but none were provided"

        super().__init__(message or "GraphQL error")
        self.errors = errors

    def __str__(self) -> str:
        return f"GraphQLError: {self.message}"


class AuthenticationError(GitLabError):
    """Raised when authentication fails (invalid or missing token)."""

    def __init__(
        self,
        message: str = "Authentication failed. Check your GitLab personal access token.",
    ) -> None:
        super().__init__(message)


class WorkItemCreationError(GitLabError):
    """Raised when creation of an Issue or Task fails.

    This can wrap partial failures when using create_issue_with_tasks().
    """

    def __init__(
        self,
        message: str,
        parent_issue_id: str | None = None,
        failed_tasks: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.parent_issue_id = parent_issue_id
        self.failed_tasks = failed_tasks or []


class ConfigurationError(GitLabError):
    """Raised for invalid client configuration (e.g. missing token, bad URL)."""

    pass
