"""GraphQL Operations Module for XGIC GitLab GraphQL Client.

This module is the single source of truth for all GraphQL query and mutation
strings used by the XGIC GitLab GraphQL Client (`xgic.gitlab.graphql`).

It also provides thin, pure helper functions that construct the exact
variable dictionaries required by GitLab's Work Items API, with special
attention to the `hierarchyWidget` used to create parent-child relationships
(Issues → Tasks).

Design principles:
- No business logic or side effects here.
- All GraphQL knowledge is centralized (easy to audit when GitLab changes).
- Thin wrappers return ready-to-use `{"query": ..., "variables": ...}` or
  just the `input` payload so `GitLabClient._execute()` stays clean.
- Follows XGIC Python Namespace Convention and modern Python typing.

This file is intentionally kept at implementation-skeleton level so Grok Build
(or any engineer) can directly implement from it with minimal additional research.
"""

from __future__ import annotations

from typing import Any

# =============================================================================
# WORK ITEM TYPE RESOLUTION
# =============================================================================
# GitLab requires the global ID of the desired Work Item Type ("Issue" or "Task")
# when creating work items. These IDs are resolved per namespace.

WORK_ITEM_TYPES_QUERY: str = """
query GetWorkItemTypes($fullPath: ID!) {
  namespace(fullPath: $fullPath) {
    workItemTypes {
      nodes {
        id
        name
      }
    }
  }
}
"""


def build_work_item_types_variables(full_path: str) -> dict[str, Any]:
    """Build variables for WORK_ITEM_TYPES_QUERY.

    Args:
        full_path: GitLab namespace path, e.g. "group/subgroup/project"

    Returns:
        Variables dict ready for GraphQL execution.
    """
    return {"fullPath": full_path}


# =============================================================================
# workItemCreate MUTATION (Core for Issues and Tasks)
# =============================================================================
# This is the primary mutation for creating both parent Issues and child Tasks.
# The hierarchyWidget field is the key mechanism for establishing parent-child
# relationships in GitLab's unified Work Items model.

WORK_ITEM_CREATE_MUTATION: str = """
mutation WorkItemCreate($input: WorkItemCreateInput!) {
  workItemCreate(input: $input) {
    workItem {
      id
      iid
      title
      description
      webUrl
      state
      createdAt
      updatedAt
      author {
        username
        name
      }
      assignees {
        nodes {
          username
          name
        }
      }
      taskCompletionStatus {
        completedCount
        count
      }
      labels {
        nodes {
          title
        }
      }
      # Request widgets so that hierarchy information (parent) is available
      # for Task.from_graphql() to parse the parent_id correctly.
      widgets {
        __typename
        ... on WorkItemWidgetHierarchy {
          parent {
            id
            iid
            title
          }
        }
      }
    }
    errors
  }
}
"""


def build_work_item_create_input(
    namespace_path: str,
    title: str,
    description: str = "",
    work_item_type_id: str | None = None,
    hierarchy_parent_id: str | None = None,
    label_names: list[str] | None = None,
    milestone_id: str | None = None,
) -> dict[str, Any]:
    """Construct the `input` payload for the workItemCreate mutation.

    This helper encapsulates the correct structure for:
    - Creating a standalone Issue (no hierarchy_parent_id)
    - Creating a Task that is a child of an existing Issue (hierarchy_parent_id provided)

    The `hierarchyWidget` field on WorkItemCreateInput is the official way
    (as of GitLab 2025/2026) to establish parent-child relationships at creation time.

    Args:
        namespace_path: Full path of the project or group (e.g. "xgic/internal-tools")
        title: Title of the new work item
        description: Markdown description
        work_item_type_id: Global ID of the Work Item Type (e.g. gid://gitlab/WorkItems::Type/TASK).
                           Must be obtained via WORK_ITEM_TYPES_QUERY first.
        hierarchy_parent_id: Global ID of the parent Work Item (only for child Tasks).
                             Example: "gid://gitlab/WorkItem/123456"
        label_names: Optional list of label titles to apply
        milestone_id: Optional global ID of a milestone

    Returns:
        Dictionary suitable for the `variables` argument of GraphQL execution:
        {"input": { ... all fields ... }}

    Example for a child Task:
        build_work_item_create_input(
            namespace_path="group/project",
            title="Implement login button",
            work_item_type_id=task_type_id,
            hierarchy_parent_id=parent_issue_global_id
        )
    """
    input_payload: dict[str, Any] = {
        "namespacePath": namespace_path,
        "title": title,
        "description": description or "",
    }

    if work_item_type_id:
        input_payload["workItemTypeId"] = work_item_type_id

    if hierarchy_parent_id:
        # This is the critical piece for parent-child relationships.
        # GitLab expects the hierarchyWidget at the top level of the input.
        input_payload["hierarchyWidget"] = {"parentId": hierarchy_parent_id}

    if label_names:
        input_payload["labelNames"] = label_names

    if milestone_id:
        input_payload["milestoneId"] = milestone_id

    return {"input": input_payload}


# =============================================================================
# FUTURE OPERATIONS (Placeholders)
# =============================================================================
# These will be implemented as the client scope expands (Merge Requests,
# Releases, Milestones, time tracking via custom fields / notes, etc.).

CREATE_MERGE_REQUEST_MUTATION: str = """
# Placeholder - to be implemented when create_merge_request() is added to public API
mutation CreateMergeRequest($input: MergeRequestCreateInput!) {
  mergeRequestCreate(input: $input) {
    mergeRequest {
      id
      iid
      title
      webUrl
    }
    errors
  }
}
"""


def build_create_merge_request_input(
    project_path: str,
    title: str,
    source_branch: str,
    target_branch: str = "main",
    description: str = "",
    label_names: list[str] | None = None,
) -> dict[str, Any]:
    """Placeholder builder for Merge Request creation variables.
    Will be completed when the corresponding public method is implemented.
    """
    return {
        "input": {
            "projectPath": project_path,
            "title": title,
            "sourceBranch": source_branch,
            "targetBranch": target_branch,
            "description": description,
            "labelNames": label_names or [],
        }
    }


# =============================================================================
# PAGINATION & LIST QUERIES (Cursor-based per GitLab Relay style)
# =============================================================================
# GitLab GraphQL uses keyset/cursor pagination with pageInfo.
# Use first/after (or last/before). pageInfo supplies endCursor + hasNextPage.

WORK_ITEMS_QUERY: str = """
query GetWorkItems($fullPath: ID!, $first: Int = 20, $after: String) {
  namespace(fullPath: $fullPath) {
    workItems(first: $first, after: $after) {
      nodes {
        id
        iid
        title
        description
        webUrl
        state
        createdAt
        updatedAt
        author {
          username
          name
        }
        assignees {
          nodes {
            username
            name
          }
        }
        labels {
          nodes {
            title
          }
        }
        widgets {
          __typename
          ... on WorkItemWidgetHierarchy {
            parent {
              id
              iid
              title
            }
          }
        }
      }
      pageInfo {
        hasNextPage
        endCursor
        hasPreviousPage
        startCursor
      }
    }
  }
}
"""


def build_work_items_variables(
    full_path: str, first: int = 20, after: str | None = None
) -> dict[str, Any]:
    """Variables for WORK_ITEMS_QUERY with cursor pagination support."""
    vars: dict[str, Any] = {"fullPath": full_path, "first": first}
    if after:
        vars["after"] = after
    return vars


CURRENT_USER_QUERY: str = """
query CurrentUser {
  currentUser {
    id
    username
    name
    email
    webUrl
    state
  }
}
"""


# =============================================================================
# UTILITY / DEBUG HELPERS
# =============================================================================


def get_mutation_name(mutation_string: str) -> str:
    """Extract the mutation/query name from a GraphQL string (useful for logging)."""
    for line in mutation_string.strip().splitlines():
        line = line.strip()
        if line.startswith("mutation ") or line.startswith("query "):
            return line.split()[1].split("(")[0]
    return "unknown"


# End of operations.py
