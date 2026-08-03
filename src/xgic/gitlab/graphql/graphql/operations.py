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

# Minimum selection set for create responses: fields that exist across GitLab.com
# and varied self-hosted schemas. Optional fields (e.g. taskCompletionStatus) are
# NOT requested on create — some instances reject them on WorkItem (see #41).
# Models treat missing optional fields as None.
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
      # Assignees, labels, and hierarchy live on widgets on many GitLab versions
      # (not top-level WorkItem fields). Keep create selection conservative.
      widgets {
        __typename
        ... on WorkItemWidgetAssignees {
          assignees {
            nodes {
              username
              name
            }
          }
        }
        ... on WorkItemWidgetLabels {
          labels {
            nodes {
              title
            }
          }
        }
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
    label_ids: list[str] | None = None,
    assignee_ids: list[str] | None = None,
    milestone_id: str | None = None,
) -> dict[str, Any]:
    """Construct the `input` payload for the workItemCreate mutation.

    This helper encapsulates the correct structure for:
    - Creating a standalone Issue (no hierarchy_parent_id)
    - Creating a Task that is a child of an existing Issue (hierarchy_parent_id provided)

    The `hierarchyWidget` field on WorkItemCreateInput is the official way
    (as of GitLab 2025/2026) to establish parent-child relationships at creation time.

    Args:
        namespace_path: Full path of the project or group (e.g. from config / env).
        title: Title of the new work item
        description: Markdown description
        work_item_type_id: Global ID of the Work Item Type (e.g. gid://gitlab/WorkItems::Type/TASK).
                           Must be obtained via WORK_ITEM_TYPES_QUERY first.
        hierarchy_parent_id: Global ID of the parent Work Item (only for child Tasks).
        label_names: Deprecated for create on many schemas; prefer ``label_ids``.
            Kept for API compatibility — callers should resolve names to IDs.
        label_ids: Optional list of label global IDs for ``labelsWidget``.
        assignee_ids: Optional list of user global IDs (e.g. ``gid://gitlab/User/<id>``)
        milestone_id: Optional global ID of a milestone

    Returns:
        Dictionary suitable for the `variables` argument of GraphQL execution:
        {"input": { ... all fields ... }}
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

    # WorkItemWidgetLabelsCreateInput requires labelIds on schemas that reject
    # top-level labelNames (common on self-hosted Work Items).
    if label_ids:
        input_payload["labelsWidget"] = {"labelIds": list(label_ids)}
    elif label_names:
        # Last-resort: some GitLab.com versions still accept labelNames.
        # Prefer client-side resolution to label_ids for portability.
        input_payload["labelNames"] = list(label_names)

    if assignee_ids:
        # Work items use assigneesWidget (not a top-level assigneeIds field).
        input_payload["assigneesWidget"] = {"assigneeIds": list(assignee_ids)}

    if milestone_id:
        input_payload["milestoneId"] = milestone_id

    return {"input": input_payload}


PROJECT_LABELS_BY_TITLE_QUERY: str = """
query ProjectLabelsByTitle($fullPath: ID!, $search: String) {
  project(fullPath: $fullPath) {
    labels(searchTerm: $search, first: 50) {
      nodes {
        id
        title
      }
    }
  }
}
"""


# =============================================================================
# MERGE REQUEST CREATE
# =============================================================================

CREATE_MERGE_REQUEST_MUTATION: str = """
mutation CreateMergeRequest($input: MergeRequestCreateInput!) {
  mergeRequestCreate(input: $input) {
    mergeRequest {
      id
      iid
      title
      description
      webUrl
      state
      sourceBranch
      targetBranch
      labels {
        nodes {
          title
        }
      }
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
    labels: list[str] | None = None,
    assignee_ids: list[str] | None = None,
    remove_source_branch: bool | None = None,
) -> dict[str, Any]:
    """Build variables for ``mergeRequestCreate``.

    Args:
        project_path: Full project path (e.g. ``group/project``).
        title: MR title.
        source_branch: Source branch name.
        target_branch: Target branch name (default ``main``).
        description: Optional Markdown description.
        labels: Optional label **titles** (GitLab ``labels`` string list).
        assignee_ids: Optional user global IDs.
        remove_source_branch: Optional delete-source-branch flag.
    """
    input_payload: dict[str, Any] = {
        "projectPath": project_path,
        "title": title,
        "sourceBranch": source_branch,
        "targetBranch": target_branch,
        "description": description or "",
    }
    if labels:
        # MergeRequestCreateInput uses a list of label titles (not label GIDs).
        input_payload["labels"] = [str(x).strip() for x in labels if str(x).strip()]
    if assignee_ids:
        input_payload["assigneeIds"] = list(assignee_ids)
    if remove_source_branch is not None:
        input_payload["removeSourceBranch"] = bool(remove_source_branch)
    return {"input": input_payload}


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
        labels {
          nodes {
            title
          }
        }
        widgets {
          __typename
          ... on WorkItemWidgetAssignees {
            assignees {
              nodes {
                username
                name
              }
            }
          }
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
