"""XGIC GitLab GraphQL Client - Core Implementation

This module contains the main `GitLabClient` class that provides a clean,
high-level, Pythonic interface over GitLab's GraphQL Work Items API.

It is the primary entry point for all consumers (including Grok Build).

Design goals:
- Hide all GraphQL complexity behind simple, strongly-typed methods.
- Centralized error handling and execution in `_execute()`.
- Rich domain models (`Issue`, `Task`) instead of raw dictionaries.
- Resilient orchestration for `create_issue_with_tasks()` (the most important
  high-level method for structured work tracking).
- Follows XGIC Python Namespace Convention (`xgic.gitlab.graphql`).
- Ready for future extension (estimates, actuals, custom fields, MCP wrapper, etc.).

This is a complete implementation skeleton. Grok Build (or any engineer) can
directly implement from it. Production hardening (retries, logging, metrics,
idempotency, circuit breaker) can be added later without changing the public API.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import requests

from .config import GitLabConfig
from .exceptions import (
    AuthenticationError,
    GitLabError,
    GraphQLError,
    WorkItemCreationError,
)
from .graphql.operations import (
    CURRENT_USER_QUERY,
    WORK_ITEM_CREATE_MUTATION,
    WORK_ITEM_TYPES_QUERY,
    WORK_ITEMS_QUERY,
    build_work_item_create_input,
    build_work_item_types_variables,
    build_work_items_variables,
)
from .models import BaseWorkItem, Issue, MergeRequest, Task


class GitLabClient:
    """High-level client for GitLab GraphQL Work Items operations.

    Primary usage (recommended for Grok Build and scripts):

        from xgic.gitlab.graphql import GitLabClient

        client = GitLabClient(token="glpat-...")
        result = client.create_issue_with_tasks(
            issue_title="Implement new checkout flow",
            issue_description="...",
            tasks=[
                {"title": "Design UI", "description": "..."},
                {"title": "Implement backend", "description": "..."},
            ],
            namespace_path="group/project",
        )

    The client is intentionally synchronous and lightweight. Async support can
    be added later via a separate `AsyncGitLabClient` if needed.
    """

    def __init__(
        self,
        token: str,
        *,
        url: str = "https://gitlab.com",
        timeout: int = 30,
        verify_ssl: bool = True,
    ) -> None:
        """Initialize the GitLab client.

        Args:
            token: GitLab Personal Access Token (or Project/Group Access Token)
                   with at least `api` scope.
            url: Base URL of the GitLab instance (default: gitlab.com).
            timeout: Request timeout in seconds.
            verify_ssl: Whether to verify SSL certificates (set False only for
                        self-signed internal instances).
        """
        if not token or not token.strip():
            raise ValueError("GitLab token cannot be empty")

        self.config = GitLabConfig(
            token=token.strip(),
            base_url=url.rstrip("/"),
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
                "User-Agent": "xgic-gitlab-graphql-client/1.0",
            }
        )

        # Simple in-memory cache for work item type IDs (per namespace)
        self._work_item_type_cache: dict[str, str] = {}

    # -------------------------------------------------------------------------
    # Core Execution Layer
    # -------------------------------------------------------------------------

    def _execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Centralized method for executing all GraphQL operations.

        This is the single place where HTTP + GraphQL error handling,
        authentication, and future concerns (retries, rate limiting, logging)
        should live.

        Raises:
            AuthenticationError: On 401/403 responses.
            GraphQLError: When GitLab returns errors in the response body.
            GitLabError: For network, timeout, or unexpected failures.
        """
        payload: dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = self.session.post(
                self.config.graphql_url,
                json=payload,
                timeout=self.config.timeout,
                verify=self.config.verify_ssl,
            )

            # Handle HTTP-level authentication / permission errors early
            if response.status_code in (401, 403):
                raise AuthenticationError(
                    f"Authentication failed (HTTP {response.status_code}). "
                    "Check that your token has the required 'api' scope."
                )

            response.raise_for_status()
            result: dict[str, Any] = response.json()

            # GitLab often returns HTTP 200 even when GraphQL errors exist
            if "errors" in result and result["errors"]:
                raise GraphQLError(result["errors"])

            return result.get("data", {})

        except requests.exceptions.Timeout as exc:
            raise GitLabError(
                f"Request to GitLab timed out after {self.config.timeout}s"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise GitLabError(f"HTTP request to GitLab failed: {exc}") from exc
        except ValueError as exc:  # JSON decode error
            raise GitLabError("Invalid JSON response received from GitLab") from exc

    # -------------------------------------------------------------------------
    # Work Item Type Resolution (with simple caching)
    # -------------------------------------------------------------------------

    def _get_work_item_type_id(self, work_item_type: str, namespace_path: str) -> str:
        """Resolve the global ID of a Work Item Type ("Issue" or "Task").

        GitLab requires the `workItemTypeId` when creating work items.
        We cache the result per namespace to avoid repeated queries.

        Args:
            work_item_type: "issue" or "task" (case-insensitive)
            namespace_path: Full path of the project/group (e.g. "group/project")

        Returns:
            Global ID string, e.g. "gid://gitlab/WorkItems::Type/1"
        """
        cache_key = f"{namespace_path}:{work_item_type.lower()}"
        if cache_key in self._work_item_type_cache:
            return self._work_item_type_cache[cache_key]

        data = self._execute(
            WORK_ITEM_TYPES_QUERY,
            build_work_item_types_variables(namespace_path),
        )

        try:
            nodes = data["namespace"]["workItemTypes"]["nodes"]
            for node in nodes:
                if node["name"].lower() == work_item_type.lower():
                    type_id = node["id"]
                    self._work_item_type_cache[cache_key] = type_id
                    return type_id

            raise GitLabError(
                f"Work item type '{work_item_type}' not found in namespace '{namespace_path}'"
            )
        except (KeyError, TypeError) as exc:
            raise GitLabError(
                "Unexpected response structure while resolving work item type"
            ) from exc

    # -------------------------------------------------------------------------
    # Public API - Issue & Task Creation
    # -------------------------------------------------------------------------

    def create_issue(
        self,
        title: str,
        description: str = "",
        *,
        namespace_path: str,
        labels: list[str] | None = None,
        milestone_id: str | None = None,
    ) -> Issue:
        """Create a new Issue (or other top-level work item type).

        This is a thin wrapper around the workItemCreate mutation.
        """
        if not title or not title.strip():
            raise ValueError("Issue title cannot be empty")
        if not namespace_path:
            raise ValueError("namespace_path is required")

        issue_type_id = self._get_work_item_type_id("issue", namespace_path)

        variables = build_work_item_create_input(
            namespace_path=namespace_path,
            title=title.strip(),
            description=description,
            work_item_type_id=issue_type_id,
            label_names=labels,
            milestone_id=milestone_id,
        )

        data = self._execute(WORK_ITEM_CREATE_MUTATION, variables)
        work_item_data = data.get("workItemCreate", {}).get("workItem")

        if not work_item_data:
            errors = data.get("workItemCreate", {}).get("errors", [])
            raise WorkItemCreationError(
                f"Failed to create issue: {errors}",
                parent_issue_id=None,
            )

        return Issue.from_graphql(work_item_data)

    def create_task(
        self,
        parent_id: str,
        title: str,
        description: str = "",
        *,
        namespace_path: str,
        assignee_ids: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> Task:
        """Create a Task as a proper child of an existing parent work item.

        The parent-child relationship is established via the `hierarchyWidget`
        in the mutation input (handled by `build_work_item_create_input`).
        """
        if not parent_id:
            raise ValueError("parent_id is required")
        if not title or not title.strip():
            raise ValueError("Task title cannot be empty")
        if not namespace_path:
            raise ValueError("namespace_path is required")

        task_type_id = self._get_work_item_type_id("task", namespace_path)

        variables = build_work_item_create_input(
            namespace_path=namespace_path,
            title=title.strip(),
            description=description,
            work_item_type_id=task_type_id,
            hierarchy_parent_id=parent_id,
            label_names=labels,
        )

        data = self._execute(WORK_ITEM_CREATE_MUTATION, variables)
        work_item_data = data.get("workItemCreate", {}).get("workItem")

        if not work_item_data:
            errors = data.get("workItemCreate", {}).get("errors", [])
            raise WorkItemCreationError(
                f"Failed to create task: {errors}",
                parent_issue_id=parent_id,
            )

        return Task.from_graphql(work_item_data)

    # -------------------------------------------------------------------------
    # High-Value Orchestration Method (Primary entry point for Grok Build)
    # -------------------------------------------------------------------------

    def create_issue_with_tasks(
        self,
        issue_title: str,
        issue_description: str,
        tasks: list[dict[str, str]],
        *,
        namespace_path: str,
        labels: list[str] | None = None,
        fail_fast: bool = False,
    ) -> dict[str, Any]:
        """Create a parent Issue and multiple child Tasks in one coordinated operation.

        This is the recommended high-level method for Grok Build and automation
        scripts. It replaces fragile Markdown checklists with proper hierarchical
        Work Items that support individual status, assignees, and reporting.

        Args:
            issue_title: Title of the parent Issue.
            issue_description: Description of the parent Issue.
            tasks: List of task dictionaries, each containing at minimum:
                   {"title": "...", "description": "..."}
            namespace_path: Full GitLab path (e.g. "group/project").
            labels: Optional labels to apply to the parent Issue.
            fail_fast: If True, stop immediately on the first task creation failure.
                       If False (default), continue and report partial failures.

        Returns:
            A rich result dictionary:
            {
                "issue": Issue,                    # The created parent
                "tasks": List[Task],               # Successfully created tasks
                "failed_tasks": List[Dict],        # Details of any failures
                "success_count": int,
                "total_tasks": int,
                "web_url": str,                    # URL of the parent Issue
                "partial_failure": bool,
            }

        Raises:
            WorkItemCreationError: If fail_fast=True and a task fails, or if the
                                   parent Issue itself cannot be created.
        """
        if not tasks:
            raise ValueError("At least one task must be provided")

        # 1. Create the parent Issue first (fail fast if this fails)
        parent_issue = self.create_issue(
            title=issue_title,
            description=issue_description,
            namespace_path=namespace_path,
            labels=labels,
        )

        created_tasks: list[Task] = []
        failed_tasks: list[dict[str, Any]] = []

        # 2. Create child tasks
        for idx, task_spec in enumerate(tasks):
            task_title = task_spec.get("title", "").strip()
            task_description = task_spec.get("description", "")

            if not task_title:
                failed_tasks.append(
                    {
                        "index": idx,
                        "title": task_title or "<missing title>",
                        "error": "Task title cannot be empty",
                    }
                )
                if fail_fast:
                    raise WorkItemCreationError(
                        "Task title cannot be empty",
                        parent_issue_id=parent_issue.id,
                        failed_tasks=failed_tasks,
                    )
                continue

            try:
                task = self.create_task(
                    parent_id=parent_issue.id,
                    title=task_title,
                    description=task_description,
                    namespace_path=namespace_path,
                )
                created_tasks.append(task)
            except Exception as exc:  # Broad catch to support partial success
                failure_info = {
                    "index": idx,
                    "title": task_title,
                    "error": str(exc),
                }
                failed_tasks.append(failure_info)

                if fail_fast:
                    raise WorkItemCreationError(
                        f"Failed to create task #{idx}: {task_title}",
                        parent_issue_id=parent_issue.id,
                        failed_tasks=failed_tasks,
                    ) from exc

        # 3. Build structured result
        success_count = len(created_tasks)
        total_tasks = len(tasks)
        partial_failure = len(failed_tasks) > 0

        return {
            "issue": parent_issue,
            "tasks": created_tasks,
            "failed_tasks": failed_tasks,
            "success_count": success_count,
            "total_tasks": total_tasks,
            "web_url": parent_issue.web_url,
            "partial_failure": partial_failure,
        }

    # -------------------------------------------------------------------------
    # Pagination helper (Relay cursor style)
    # -------------------------------------------------------------------------

    def _execute_paginated(
        self,
        query: str,
        variables: dict[str, Any],
        data_path: list[str],
        page_size: int = 20,
    ) -> Iterator[dict[str, Any]]:
        """Generic cursor-based pagination executor.

        Yields individual nodes from paged connections.
        Consumers can collect or process stream-style.
        """
        after: str | None = None
        while True:
            vars_copy = dict(variables)
            vars_copy["first"] = page_size
            if after:
                vars_copy["after"] = after
            data = self._execute(query, vars_copy)
            # Navigate to connection e.g. ["namespace", "workItems"]
            current: Any = data
            for key in data_path:
                current = current.get(key, {}) if isinstance(current, dict) else {}
            nodes = current.get("nodes", []) if isinstance(current, dict) else []
            yield from nodes
            page_info = current.get("pageInfo", {}) if isinstance(current, dict) else {}
            if not page_info.get("hasNextPage"):
                break
            after = page_info.get("endCursor")
            if not after:
                break

    # -------------------------------------------------------------------------
    # Query features (common use cases)
    # -------------------------------------------------------------------------

    def list_work_items(
        self,
        namespace_path: str,
        *,
        first: int = 20,
        after: str | None = None,
    ) -> dict[str, Any]:
        """List work items (Issues + Tasks) under a namespace with cursor pagination.

        Returns a page result:
            {
                "items": List[BaseWorkItem | Issue | Task],
                "page_info": {"hasNextPage": bool, "endCursor": str | None, ...},
                "has_next_page": bool,
                "end_cursor": str | None,
            }
        Use end_cursor with after= for subsequent pages, or iterate _execute_paginated.
        """
        if not namespace_path:
            raise ValueError("namespace_path is required")

        data = self._execute(
            WORK_ITEMS_QUERY,
            build_work_items_variables(namespace_path, first=first, after=after),
        )
        wi = data.get("namespace", {}).get("workItems", {})
        nodes = wi.get("nodes", [])
        page_info = wi.get("pageInfo", {})

        # Best-effort map to models; default to BaseWorkItem
        items = []
        for n in nodes:
            # Heuristic: presence of hierarchy parent indicates Task
            if any(
                w.get("__typename") == "WorkItemWidgetHierarchy" and w.get("parent")
                for w in n.get("widgets", [])
            ):
                items.append(Task.from_graphql(n))
            else:
                items.append(Issue.from_graphql(n))

        return {
            "items": items,
            "page_info": page_info,
            "has_next_page": page_info.get("hasNextPage", False),
            "end_cursor": page_info.get("endCursor"),
        }

    def iter_work_items(
        self, namespace_path: str, *, page_size: int = 20
    ) -> Iterator[BaseWorkItem | Issue | Task]:
        """Convenience iterator over all work items using internal pagination."""
        for node in self._execute_paginated(
            WORK_ITEMS_QUERY,
            {"fullPath": namespace_path},
            data_path=["namespace", "workItems"],
            page_size=page_size,
        ):
            if any(
                w.get("__typename") == "WorkItemWidgetHierarchy" and w.get("parent")
                for w in node.get("widgets", [])
            ):
                yield Task.from_graphql(node)
            else:
                yield Issue.from_graphql(node)

    def get_current_user(self) -> dict[str, Any]:
        """Return basic info about the authenticated user."""
        data = self._execute(CURRENT_USER_QUERY)
        return data.get("currentUser", {})

    # -------------------------------------------------------------------------
    # Placeholder for future expansion
    # -------------------------------------------------------------------------

    def create_merge_request(
        self,
        title: str,
        source_branch: str,
        *,
        namespace_path: str,
        target_branch: str = "main",
        description: str = "",
        labels: list[str] | None = None,
    ) -> MergeRequest:
        """Placeholder for Merge Request creation.

        Will be implemented when the corresponding GraphQL mutation and
        builder in operations.py are completed.
        """
        raise NotImplementedError(
            "create_merge_request() is not yet implemented. "
            "See GRAPHQL_OPERATIONS_CONTRACT.md for the planned shape."
        )

    # -------------------------------------------------------------------------
    # Convenience / Future Methods (stubs for extensibility)
    # -------------------------------------------------------------------------

    def get_work_item(self, work_item_id: str) -> Any:
        """Placeholder for retrieving a work item by global ID."""
        raise NotImplementedError("Not yet implemented")

    def update_work_item(self, work_item_id: str, **fields: Any) -> Any:
        """Placeholder for future structured updates (estimates, actuals, status, etc.).
        This will become the primary method for moving away from free-text
        description fields.
        """
        raise NotImplementedError("Not yet implemented")

    # -------------------------------------------------------------------------
    # Resource Management (Context Manager Support)
    # -------------------------------------------------------------------------

    def __enter__(self) -> GitLabClient:
        """Enable use as a context manager: `with GitLabClient(...) as client:`"""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Ensure the underlying session is closed when exiting the context."""
        self.close()

    def close(self) -> None:
        """Close the underlying requests.Session to release connections."""
        if hasattr(self, "session") and self.session:
            self.session.close()

    def __repr__(self) -> str:
        return (
            f"GitLabClient(url={self.config.base_url!r}, "
            f"timeout={self.config.timeout}, verify_ssl={self.config.verify_ssl})"
        )


# End of client.py
