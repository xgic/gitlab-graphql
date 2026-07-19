"""Minimal Test Skeleton for XGIC GitLab GraphQL Client

This file provides a production-oriented starting point for unit testing
the `GitLabClient`. It focuses on the most critical paths:

- Client initialization and configuration validation
- Core execution and error translation (_execute)
- High-level orchestration (create_issue_with_tasks)
- Proper use of domain models and custom exceptions

Run with:
    uv run pytest tests/test_client.py -q --tb=short

Integration tests that hit a real GitLab instance should be marked
with @pytest.mark.integration and skipped by default.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from xgic.gitlab.graphql import GitLabClient
from xgic.gitlab.graphql.exceptions import (
    AuthenticationError,
    WorkItemCreationError,
)
from xgic.gitlab.graphql.models import Issue, Task

# -------------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------------


@pytest.fixture
def mock_client() -> GitLabClient:
    """Returns a GitLabClient with network calls (_execute) fully mocked.
    This is the recommended way to test the client in unit tests.
    """
    client = GitLabClient(token="glpat-test-token-for-testing-only")
    # Patch the expensive network method
    client._execute = MagicMock()  # type: ignore[method-assign]
    client._get_work_item_type_id = MagicMock(
        return_value="gid://gitlab/WorkItems::Type/1"
    )  # type: ignore[method-assign]
    return client


@pytest.fixture
def sample_issue_data() -> dict[str, Any]:
    """Minimal realistic GraphQL response for an Issue."""
    return {
        "id": "gid://gitlab/WorkItem/12345",
        "iid": 42,
        "title": "Implement new checkout flow",
        "description": "Detailed description here...",
        "webUrl": "https://gitlab.com/group/project/-/issues/42",
        "state": "opened",
        "createdAt": "2026-06-27T10:00:00Z",
        "updatedAt": "2026-06-27T10:05:00Z",
        "author": {"username": "test-user"},
        "labels": {"nodes": [{"title": "feature"}]},
        "taskCompletionStatus": {"completedCount": 0, "count": 3},
    }


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Minimal realistic GraphQL response for a child Task."""
    return {
        "id": "gid://gitlab/WorkItem/12346",
        "iid": 43,
        "title": "Design UI mockups",
        "description": "Create Figma designs",
        "webUrl": "https://gitlab.com/group/project/-/issues/43",
        "state": "opened",
        "createdAt": "2026-06-27T10:10:00Z",
        "widgets": [
            {
                "__typename": "WorkItemWidgetHierarchy",
                "parent": {"id": "gid://gitlab/WorkItem/12345"},
            }
        ],
    }


# -------------------------------------------------------------------------
# Initialization & Configuration Tests
# -------------------------------------------------------------------------


def test_client_rejects_empty_token():
    with pytest.raises(ValueError, match="GitLab token cannot be empty"):
        GitLabClient(token="")


def test_client_accepts_valid_token():
    client = GitLabClient(token="glpat-valid-token")
    assert client.config.token == "glpat-valid-token"
    assert client.config.base_url == "https://gitlab.com"


# -------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------


def test_issue_from_graphql(sample_issue_data: dict[str, Any]):
    issue = Issue.from_graphql(sample_issue_data)
    assert isinstance(issue, Issue)
    assert issue.iid == 42
    assert "checkout" in issue.title


def test_build_work_item_create_input_includes_assignees_and_labels() -> None:
    from xgic.gitlab.graphql.graphql.operations import build_work_item_create_input

    # Synthetic fixture values only — never real private host/project/user IDs.
    ns = "example-group/example-project"
    user_gid = "gid://gitlab/User/9001"
    parent_gid = "gid://gitlab/WorkItem/2002"
    type_gid = "gid://gitlab/WorkItems::Type/5"

    payload = build_work_item_create_input(
        namespace_path=ns,
        title="Child task",
        work_item_type_id=type_gid,
        hierarchy_parent_id=parent_gid,
        label_names=["type:docs", "priority:high"],
        assignee_ids=[user_gid],
    )["input"]
    assert payload["namespacePath"] == ns
    assert payload["labelNames"] == ["type:docs", "priority:high"]
    assert payload["assigneesWidget"] == {"assigneeIds": [user_gid]}
    assert payload["hierarchyWidget"] == {"parentId": parent_gid}


def test_assignees_from_widget() -> None:
    data = {
        "id": "gid://gitlab/WorkItem/99",
        "iid": 99,
        "title": "Assigned item",
        "widgets": [
            {
                "__typename": "WorkItemWidgetAssignees",
                "assignees": {
                    "nodes": [{"username": "xgic", "name": "XGIC"}],
                },
            }
        ],
    }
    item = Issue.from_graphql(data)
    assert len(item.assignees) == 1
    assert item.assignees[0]["username"] == "xgic"


def test_task_from_graphql_extracts_parent(sample_task_data: dict[str, Any]):
    task = Task.from_graphql(sample_task_data)
    assert isinstance(task, Task)
    assert task.parent_id == "gid://gitlab/WorkItem/12345"


# -------------------------------------------------------------------------
# Error Handling in _execute
# -------------------------------------------------------------------------


def test_execute_raises_authentication_error_on_401(monkeypatch):
    client = GitLabClient(token="glpat-test")
    mock_response = MagicMock()
    mock_response.status_code = 401
    monkeypatch.setattr(client.session, "post", lambda *a, **k: mock_response)

    with pytest.raises(AuthenticationError):
        client._execute("{ foo }")


# -------------------------------------------------------------------------
# High-Level Orchestration: create_issue_with_tasks
# -------------------------------------------------------------------------


def test_create_issue_with_tasks_happy_path(
    mock_client: GitLabClient,
    sample_issue_data: dict[str, Any],
    sample_task_data: dict[str, Any],
):
    """Happy path: parent Issue + 2 child Tasks are created successfully."""
    # Arrange
    mock_client._execute.side_effect = [
        {"workItemCreate": {"workItem": sample_issue_data}},  # parent
        {"workItemCreate": {"workItem": sample_task_data}},  # task 1
        {"workItemCreate": {"workItem": sample_task_data}},  # task 2
    ]
    mock_client._get_work_item_type_id.side_effect = [
        "gid://gitlab/WorkItems::Type/1",  # issue
        "gid://gitlab/WorkItems::Type/2",  # task
        "gid://gitlab/WorkItems::Type/2",  # task
    ]

    result = mock_client.create_issue_with_tasks(
        issue_title="Implement new checkout flow",
        issue_description="...",
        tasks=[
            {"title": "Design UI mockups"},
            {"title": "Implement backend"},
        ],
        namespace_path="group/project",
    )

    assert "issue" in result
    assert len(result["tasks"]) == 2
    assert result["success_count"] == 2
    assert not result["partial_failure"]


# -------------------------------------------------------------------------
# Pagination and Query Features
# -------------------------------------------------------------------------


def test_list_work_items_returns_page(
    mock_client: GitLabClient, sample_issue_data: dict[str, Any]
):
    mock_client._execute.return_value = {
        "namespace": {
            "workItems": {
                "nodes": [sample_issue_data],
                "pageInfo": {"hasNextPage": False, "endCursor": None},
            }
        }
    }
    page = mock_client.list_work_items("group/project", first=5)
    assert "items" in page
    assert page["has_next_page"] is False


def test_get_current_user(mock_client: GitLabClient):
    mock_client._execute.return_value = {"currentUser": {"username": "test-user"}}
    user = mock_client.get_current_user()
    assert user["username"] == "test-user"


def test_create_issue_with_tasks_partial_failure(
    mock_client: GitLabClient,
    sample_issue_data: dict[str, Any],
    sample_task_data: dict[str, Any],
):
    """One task fails, but the method continues and reports the failure."""
    mock_client._execute.side_effect = [
        {"workItemCreate": {"workItem": sample_issue_data}},  # parent OK
        {"workItemCreate": {"workItem": sample_task_data}},  # task 1 OK
        Exception("GitLab rate limit exceeded"),  # task 2 fails
    ]

    tasks_spec = [
        {"title": "Design UI", "description": ""},
        {"title": "Implement backend", "description": ""},
    ]

    result = mock_client.create_issue_with_tasks(
        issue_title="Feature with partial tasks",
        issue_description="...",
        tasks=tasks_spec,
        namespace_path="group/project",
        fail_fast=False,
    )

    assert result["partial_failure"] is True
    assert result["success_count"] == 1
    assert len(result["failed_tasks"]) == 1
    assert result["failed_tasks"][0]["title"] == "Implement backend"


def test_create_issue_with_tasks_fail_fast(
    mock_client: GitLabClient,
    sample_issue_data: dict[str, Any],
):
    """When fail_fast=True, the first task failure should raise immediately."""
    mock_client._execute.side_effect = [
        {"workItemCreate": {"workItem": sample_issue_data}},
        Exception("Network error on first task"),
    ]

    with pytest.raises(WorkItemCreationError):
        mock_client.create_issue_with_tasks(
            issue_title="Fail fast test",
            issue_description="",
            tasks=[{"title": "Task that will fail", "description": ""}],
            namespace_path="group/project",
            fail_fast=True,
        )


# -------------------------------------------------------------------------
# Integration tests (opt-in via environment — never hard-code hosts/paths)
# -------------------------------------------------------------------------
# Required when GITLAB_INTEGRATION=1:
#   GITLAB_URL, GITLAB_TOKEN, GITLAB_TEST_NAMESPACE_PATH
# Optional:
#   GITLAB_TEST_ASSIGNEE_ID (user global ID for assignee exercises)
#
# Use a dedicated non-production GitLab EE + test project only.
# Never hard-code private hosts, production project paths, or real user IDs.


@pytest.mark.integration
@pytest.mark.skipif(
    __import__("os").environ.get("GITLAB_INTEGRATION") != "1",
    reason="Set GITLAB_INTEGRATION=1 and config env vars for live GitLab tests",
)
def test_integration_config_env_present() -> None:
    """Guard: integration mode must be fully configured, not hard-coded."""
    import os

    required = ("GITLAB_URL", "GITLAB_TOKEN", "GITLAB_TEST_NAMESPACE_PATH")
    missing = [k for k in required if not os.environ.get(k)]
    assert not missing, f"Missing integration env: {missing}"


# -------------------------------------------------------------------------
# Notes for Future Test Expansion
# -------------------------------------------------------------------------
"""
Recommended future additions:

1. Use `pytest-responses` or `responses` library for more realistic
   HTTP-level mocking of `_execute`.

2. Full integration suite against a dedicated non-production GitLab EE
   (config via env only; see test_integration_config_env_present).

3. Test coverage target: >= 85% on client.py and operations.py for Phase 1.
"""
