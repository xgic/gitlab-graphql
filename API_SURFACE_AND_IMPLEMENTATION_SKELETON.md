# GitLab GraphQL Client — Public API Surface & Implementation Skeleton

**Document Version:** 1.0  
**Date:** June 27, 2026  
**Status:** Proposed / Architecture-Level Definition  
**Related ADR:** ADR-001-GitLab-GraphQL-Client.md

---

## 1. Purpose of This Document

This document finalizes the **exact public API surface** of the `GitLabClient` class at the architecture level. It also provides a detailed **implementation skeleton** (algorithmic + structural) for the high-value convenience method `create_issue_with_tasks`.

The goal is to give Grok Build (and human developers) a clear, stable contract to program against while the internal GraphQL details, models, and operations are still being implemented.

All design decisions follow:
- Clean Architecture / Separation of Concerns
- SOLID principles (especially SRP and OCP)
- Strong typing and explicit contracts
- Resilience and observability for automation use cases (Grok Build)
- Future extensibility toward structured fields (estimates, actuals, custom widgets) and MCP wrapper

---

## 2. Finalized Public API Surface

### 2.1 GitLabClient Class Overview

**Module:** `src/xgic/gitlab/graphql/client.py`  
**Primary Responsibility:** Provide a high-level, opinionated, type-safe facade over GitLab’s GraphQL API for Work Items and related entities. Hide all raw GraphQL query/mutation construction, response parsing, error mapping, and authentication details.

**Design Constraints (Phase 1):**
- Synchronous only (async client is a future extension point)
- Minimal dependencies: only `requests` (plus standard library)
- All public methods return rich domain models (`Issue`, `Task`, `MergeRequest`) or structured result dicts — never raw dicts or JSON
- Every network call goes through the private `_execute()` method (centralized error handling, logging hook, retry policy)
- The class is **not** a God object: complex orchestration lives in dedicated high-level methods; low-level GraphQL lives in `graphql/operations.py`

### 2.2 Constructor

```python
def __init__(
    self,
    token: str,
    *,
    url: str = "https://gitlab.com",
    timeout: int = 30,
    verify_ssl: bool = True,
) -> None:
    """
    Initialize the GitLab GraphQL client.

    Args:
        token: GitLab Personal Access Token (or Project/Group Access Token) with `api` scope.
        url: Base GitLab instance URL. Defaults to SaaS.
        timeout: Per-request timeout in seconds.
        verify_ssl: Whether to verify TLS certificates (set False only for self-signed dev instances).

    Raises:
        ValueError: If token is empty or whitespace.
    """
```

**Notes:**
- Token is stored only in the config object; never logged.
- `verify_ssl=False` is provided for developer convenience but should be avoided in production (security best practice).

### 2.3 Core Public Methods (Phase 1 Scope)

#### `create_issue`

```python
def create_issue(
    self,
    title: str,
    description: str = "",
    labels: Optional[List[str]] = None,
    milestone_id: Optional[str] = None,
    issue_type: str = "issue",
    confidential: bool = False,
) -> Issue:
    """
    Create a new Work Item of type Issue (or other supported top-level type).

    This is the primary method for creating parent work items.

    Returns:
        Issue model populated with id (global), iid, web_url, state, etc.

    Raises:
        ValidationError: If title is empty.
        GraphQLError: If GitLab returns GraphQL errors (e.g., invalid labels).
        GitLabError: On network / HTTP failures.
    """
```

#### `create_task`

```python
def create_task(
    self,
    parent_id: str,
    title: str,
    description: str = "",
    assignee_ids: Optional[List[str]] = None,
) -> Task:
    """
    Create a Task as a proper child Work Item under the given parent.

    The parent-child relationship is established immediately via the
    WorkItem hierarchy widget in the GraphQL mutation.

    Args:
        parent_id: Global ID of the parent Work Item (format: gid://gitlab/WorkItem/123456).

    Returns:
        Task model with parent_id populated from the hierarchy widget response.

    Raises:
        ValidationError: If parent_id or title missing/invalid format.
        GraphQLError: If parent does not exist or hierarchy widget fails.
    """
```

#### `create_issue_with_tasks` (Primary Convenience Method for Grok Build)

```python
def create_issue_with_tasks(
    self,
    issue_title: str,
    issue_description: str = "",
    tasks: List[Dict[str, str]],
    labels: Optional[List[str]] = None,
    milestone_id: Optional[str] = None,
    fail_fast: bool = False,
) -> Dict[str, Any]:
    """
    High-level orchestrated method: create a parent Issue and multiple child Tasks
    in one logical operation.

    This is the **recommended entry point** for Grok Build when the goal is to
    break down complex work into structured, queryable Tasks instead of
    maintaining long Markdown checklists inside a single issue description.

    Behavior on partial failure:
    - Default (fail_fast=False): Continue creating remaining tasks. Return both
      successes and structured error information.
    - fail_fast=True: Stop on first failure and raise immediately (useful for
      strict CI/CD or when atomicity is more important than partial progress).

    Return contract (always a dict for easy inspection by Grok Build):
    {
        "issue": Issue,                    # The created parent
        "tasks": List[Task],               # Successfully created children
        "partial_errors": Optional[List[Dict]],  # Details of any failures
        "success_count": int,
        "total_requested": int,
        "web_url": str                     # Convenience: parent issue URL
    }

    Preconditions:
    - `tasks` must be a non-empty list of dicts, each containing at least a "title" key.
    - All titles must be non-empty strings.

    Postconditions:
    - If any tasks were created, the parent issue exists and at least one child exists.
    - The returned Task objects have their `parent_id` correctly set.
    """
```

#### `create_merge_request`

```python
def create_merge_request(
    self,
    title: str,
    description: str = "",
    source_branch: str,
    target_branch: str = "main",
    labels: Optional[List[str]] = None,
) -> MergeRequest:
    """
    Create a new Merge Request.

    Phase 1 scope is intentionally minimal. Future versions will add
    support for draft status, assignee, reviewer, etc.
    """
```

### 2.4 Future Extension Points (Documented for Design)

These are **not** implemented in Phase 1 but the architecture must accommodate them without breaking changes:

- `get_work_item(work_item_id: str) -> BaseWorkItem`
- `update_work_item(work_item_id: str, **fields) -> BaseWorkItem`  
  (Especially important later for setting `time_estimate`, `spent_time`, custom widgets, status, etc.)
- `list_work_items(namespace_path: str, filters: dict) -> List[BaseWorkItem]`
- `add_time_tracking(...)`, `set_estimate(...)`, etc. (structured data vision)

The `update_work_item` method will be the key enabler for moving estimates/actuals out of Markdown and into proper GitLab fields.

### 2.5 Error Model (Cross-Cutting)

```python
# In exceptions.py
class GitLabError(Exception): ...
class GraphQLError(GitLabError): ...
class ValidationError(GitLabError): ...
class PartialFailureError(GitLabError): ...  # Optional, for create_issue_with_tasks
```

All public methods document the exact exception types they can raise.

---

## 3. Implementation Skeleton for `create_issue_with_tasks`

### 3.1 Architectural Role

`create_issue_with_tasks` is a **Facade / Orchestrator** method. It does **not** contain GraphQL strings. It coordinates calls to the lower-level `create_issue` and `create_task` methods (which themselves delegate to `_execute` + operations module).

This keeps the GraphQL complexity encapsulated and makes the high-level method easy to test with mocks.

### 3.2 Detailed Algorithm (Architecture-Level Pseudo-code)

```python
def create_issue_with_tasks(self, issue_title, issue_description, tasks, labels=None, milestone_id=None, fail_fast=False):
    # === Step 0: Input Validation (fail fast, no network call) ===
    if not tasks or not isinstance(tasks, list):
        raise ValidationError("tasks must be a non-empty list of dictionaries")
    for i, t in enumerate(tasks):
        if not isinstance(t, dict) or not t.get("title"):
            raise ValidationError(f"Task at index {i} must be a dict with non-empty 'title'")

    created_tasks: List[Task] = []
    partial_errors: List[Dict[str, Any]] = []

    # === Step 1: Create Parent Issue ===
    try:
        parent_issue: Issue = self.create_issue(
            title=issue_title,
            description=issue_description,
            labels=labels,
            milestone_id=milestone_id,
            issue_type="issue",
        )
    except Exception as exc:
        # Parent creation is critical — fail immediately
        raise GitLabError(f"Failed to create parent issue: {exc}") from exc

    # === Step 2: Create Child Tasks (best-effort or fail-fast) ===
    for idx, task_spec in enumerate(tasks):
        task_title = task_spec["title"]
        task_description = task_spec.get("description", "")

        try:
            task: Task = self.create_task(
                parent_id=parent_issue.id,   # Global ID required by hierarchy widget
                title=task_title,
                description=task_description,
            )
            created_tasks.append(task)
        except Exception as exc:
            error_info = {
                "index": idx,
                "title": task_title,
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
            partial_errors.append(error_info)

            if fail_fast:
                raise PartialFailureError(
                    f"Failed to create task #{idx} ('{task_title}'). "
                    f"Parent issue {parent_issue.iid} was created. "
                    f"Partial tasks created: {len(created_tasks)}"
                ) from exc
            # else: continue (resilient mode — recommended default for Grok Build)

    # === Step 3: Build Structured Result ===
    result = {
        "issue": parent_issue,
        "tasks": created_tasks,
        "partial_errors": partial_errors if partial_errors else None,
        "success_count": len(created_tasks),
        "total_requested": len(tasks),
        "web_url": parent_issue.web_url,
        "success": len(partial_errors) == 0,
    }

    if partial_errors:
        # Future: emit structured log event or metric for observability
        # e.g., logger.warning("create_issue_with_tasks partial failure", extra=result)
        pass

    return result
```

### 3.3 Key Design Decisions & Rationale

| Decision | Rationale | Alignment with Vision |
|----------|-----------|-----------------------|
| **Continue on error by default** (`fail_fast=False`) | Grok Build often works on complex, long-running tasks. Losing partial progress is worse than having some tasks created. | Resilience for automation |
| **Return structured dict instead of custom dataclass** | Easy for Grok Build / LLM to parse and reason about (`success_count`, `partial_errors`). No new model class needed in Phase 1. | Grok Build friendliness |
| **Parent creation is atomic (fail fast)** | If the parent cannot be created, there is no point proceeding. The parent is the anchor for all child hierarchy. | Data integrity |
| **No automatic rollback / cleanup** | GitLab does not provide easy transactional multi-mutation support for Work Items. Documented limitation. Future: optional "cleanup on failure" via separate delete calls (dangerous). | Honest API contract |
| **Use global ID (`parent_issue.id`) for `create_task`** | Required by GitLab’s Work Item hierarchy widget in GraphQL. The model’s `from_graphql` ensures this is always populated correctly. | Correct use of GitLab Work Items model |
| **Validation before any network call** | Cheap failure, clear error messages, no wasted API quota. | Performance + UX |
| **Extensibility hook for idempotency** | Later we can add an optional `idempotency_key` or pre-check "does task with this title already exist under parent?" using a hierarchy query. | Supports reliable automation |

### 3.4 Observability & Reliability Considerations (to be implemented)

- `_execute` will eventually support basic retry with exponential backoff for transient errors (5xx, rate limit).
- All public methods should accept an optional `request_id` or use `contextvars` for tracing (future).
- Structured logging of the final result dict (success/failure counts) is highly recommended.
- For production use with Grok Build, wrap calls in try/except at the script level and surface `partial_errors` clearly.

---

## 4. How This Supports the Overall Vision

- Moves work breakdown from fragile Markdown checklists → proper hierarchical Work Items.
- Enables future structured fields (estimates, actuals, custom status) via the same `update_work_item` extension point.
- Gives Grok Build a reliable, high-level primitive (`create_issue_with_tasks`) that dramatically reduces prompt complexity and escaping issues previously seen with `glab`.
- The architecture is deliberately **open for extension** (MCP wrapper, async client, full Work Item CRUD, reporting queries) without requiring changes to existing call sites.

---

## 5. Next Recommended Architectural Steps

1. Finalize `models.py` (especially how `Task.from_graphql` extracts the parent from the hierarchy widget).
2. Define the exact GraphQL mutation strings + variable shapes in `graphql/operations.py` (still at architecture / pseudo level if desired).
3. Define the internal `_execute` implementation details + error mapping strategy.
4. Create a minimal test strategy (unit tests for the orchestrator using mocks of `create_issue` / `create_task`).

---

**This document, together with ADR-001, README.md, ARCHITECTURE.md, and GROK_BUILD_INTEGRATION.md, provides a complete, self-contained architecture package** that a fresh Grok Build session can use to implement the client correctly and consistently.

Would you like me to now create the next artifact (e.g., detailed models definition or the GraphQL operations contract), or make any adjustments to this API surface before we lock it?