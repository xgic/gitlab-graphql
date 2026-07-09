# GRAPHQL_OPERATIONS_CONTRACT.md

**XGIC GitLab GraphQL Client**  
**Python Namespace:** `xgic.gitlab.graphql`  
**Distribution:** `xgic-gitlab-graphql`  
**Status:** Architecture Contract — Phase 1

---

## 1. Purpose

This document defines the **exact GraphQL operation shapes** (mutations and supporting queries) that the `GitLabClient` implementation must use. It serves as the contract between the high-level Python API (`create_issue`, `create_task`, `create_issue_with_tasks`) and the underlying GitLab Work Items GraphQL API.

All implementations in `src/xgic/gitlab/graphql/graphql/operations.py` **must** conform to this contract. This ensures:

- Correct parent-child hierarchy using the Work Items model
- Future-proofing as GitLab evolves the Work Items API
- Clean separation between domain logic and raw GraphQL
- Consistent error and response handling

This contract is derived from GitLab’s official Work Items GraphQL schema (as of GitLab 18.x / mid-2026) and aligns with the domain models defined in `DOMAIN_MODELS_AND_HIERARCHY_PARSING.md`.

---

## 2. Core Principles

1. **Work Items over legacy Issues API** — All hierarchy-capable entities use `workItemCreate`.
2. **Top-level widgets for create** — For `workItemCreate`, hierarchy is passed via top-level `hierarchyWidget` (not nested in `widgets` array for creation). Labels/milestones use dedicated top-level fields.
3. **Global IDs everywhere** — Use `gid://gitlab/WorkItem/...` and `gid://gitlab/WorkItems::Type/...` IDs.
4. **Two-phase creation for hierarchy** — Parent first, then children with `hierarchyWidget`.
5. **Resilient orchestration** — `create_issue_with_tasks` continues on individual task failures (documented in `API_SURFACE_AND_IMPLEMENTATION_SKELETON.md`).
6. **First-class error surfacing** — GraphQL `errors` array is always checked.

---

## 3. Required Pre-Query: Obtaining Work Item Type IDs

Before any `workItemCreate`, the client **must** resolve the correct `workItemTypeId` for the desired type ("Issue", "Task", etc.) within the target namespace.

**Recommended supporting query shape** (to be implemented in `operations.py`):

```graphql
query GetWorkItemTypes($namespacePath: ID!) {
  namespace(fullPath: $namespacePath) {
    workItemTypes {
      nodes {
        id
        name
      }
    }
  }
}
```

**Expected usage in client:**
- Cache the mapping `{"Issue": "...", "Task": "..."}` per namespace for the session.
- `workItemTypeId` for Task is required when creating child tasks.

---

## 4. Primary Mutation: `workItemCreate`

**Mutation name:** `workItemCreate`  
**Introduced:** GitLab 15.1 (stable for basic use; hierarchy widget experimental → production in 18.2+)

### 4.1 Input Type: `WorkItemCreateInput`

```graphql
input WorkItemCreateInput {
  namespacePath: String
  projectPath: String          # Alternative to namespacePath
  workItemTypeId: WorkItemsTypeID!
  title: String!
  description: String
  confidential: Boolean
  # ... other top-level fields

  widgets: [WorkItemWidgetCreateInput!]
}
```

### 4.2 Widget Input for Hierarchy (Critical for Tasks)

When creating a **child Task**, include exactly one hierarchy widget:

```graphql
input WorkItemWidgetCreateInput {
  # Discriminated by presence of one of the following
  hierarchyWidget: WorkItemWidgetHierarchyCreateInput
  # (other widgets: labelsWidget, milestoneWidget, etc. — out of Phase 1 scope)
}

input WorkItemWidgetHierarchyCreateInput {
  parentId: WorkItemID!          # Global ID of the parent Work Item (Issue or other)
}
```

**Example payload shape for creating a child Task:**

```json
{
  "input": {
    "namespacePath": "group/project",
    "workItemTypeId": "gid://gitlab/WorkItems::Type/TASK_TYPE_ID",
    "title": "Implement login endpoint",
    "description": "Add JWT-based authentication...",
    "hierarchyWidget": {
      "parentId": "gid://gitlab/WorkItem/987654321"
    }
  }
}
```

**Important rules:**
- `parentId` **must** be the global Work Item ID returned from a previous `workItemCreate` (or fetched via query).
- `hierarchyWidget` is top-level in the `input` for create (not wrapped in `widgets` array).
- Creating a top-level Issue omits `hierarchyWidget`.

---

## 5. Response Shape Expectations

All `workItemCreate` calls must request at minimum:

```graphql
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
    author { ... }
    # For hierarchy responses (when querying existing items)
    widgets {
      ... on WorkItemWidgetHierarchy {
        parent {
          id
        }
        children {
          nodes { id title state }
        }
      }
    }
  }
  errors
}
```

The Python `from_graphql` factory methods in `models.py` (`Issue.from_graphql`, `Task.from_graphql`) are responsible for parsing the `widgets` array to extract `parent_id` (see `DOMAIN_MODELS_AND_HIERARCHY_PARSING.md` for the exact algorithm).

---

## 6. Operation Contracts for Phase 1 Public Methods

### 6.1 `create_issue(...)`

**Internal operation:** Single `workItemCreate` call.  
**Widgets used:** None (or labels/milestone in future phases).  
**workItemTypeId:** Resolved "Issue" type for the namespace.  
**Return:** `Issue` model instance.

### 6.2 `create_task(parent_id: str, ...)`

**Internal operation:** Single `workItemCreate` call.  
**Required widget:** One `hierarchyWidget` with `parentId`.  
**workItemTypeId:** Resolved "Task" type.  
**Return:** `Task` model instance (with `parent_id` populated via widget parsing).

### 6.3 `create_issue_with_tasks(...)` (Orchestrator)

This is a **facade / orchestration method** — it does **not** contain raw GraphQL.

**Algorithm (high-level contract):**
1. Validate inputs (non-empty title, tasks list, valid parent namespace).
2. Resolve work item type IDs for "Issue" and "Task".
3. Execute `workItemCreate` for the parent Issue → obtain global `parent_id`.
4. For each task in the list:
   - Execute `workItemCreate` with `hierarchyWidget.parentId = parent_id`
   - On success: append `Task` model to results
   - On failure: append structured error to `partial_errors` (never raise unless `fail_fast=True`)
5. Return structured dict:
   ```python
   {
       "issue": Issue(...),
       "tasks": [Task, ...],
       "partial_errors": [...],
       "task_count": int,
       "success_count": int,
       "web_url": str
   }
   ```

This contract guarantees **resilience** for Grok Build usage (one bad task description does not destroy the whole feature).

---

## 7. Error Handling Contract

- HTTP-level errors → raise `GitLabError`
- GraphQL `errors` array present → raise `GraphQLError` (or collect in `partial_errors` for orchestration methods)
- Missing `workItemTypeId` for "Task" → clear client-side validation error before any network call
- Invalid `parentId` format → client-side validation

---

## 8. Future Extensibility Points (Documented for Later Phases)

- Adding `labelsWidget`, `milestoneWidget`, `assigneesWidget` to `widgets` array
- Time tracking widgets (estimates / actuals) once GitLab exposes them
- `workItemUpdate` mutation for updating hierarchy, status, estimates
- Batch mutations or `workItemCreate` with multiple hierarchy children (if GitLab adds support)
- Async client variant using `httpx`

---

## 9. References & Alignment

- **ADR-001-GitLab-GraphQL-Client.md** — Overall decision and scope
- **API_SURFACE_AND_IMPLEMENTATION_SKELETON.md** — Public method signatures
- **DOMAIN_MODELS_AND_HIERARCHY_PARSING.md** — How responses are turned into `Issue` / `Task` objects
- **pyproject.toml** — Build system (`hatchling` + `uv`)
- Official GitLab docs: Work Items widgets and GraphQL reference (docs.gitlab.com)

---

**Document Owner:** XGIC  
**Last Updated:** June 2026  
**Next Review Trigger:** GitLab 18.3+ Work Items schema changes or addition of native time-tracking widgets

---

*This contract ensures that the XGIC GitLab GraphQL Client remains the most reliable bridge between Grok Build automation and GitLab’s structured Work Items model, eliminating fragile Markdown checklists while enabling future structured data (estimates, actuals, reporting).*
