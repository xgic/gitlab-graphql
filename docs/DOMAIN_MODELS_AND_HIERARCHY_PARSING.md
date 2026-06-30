# DOMAIN_MODELS_AND_HIERARCHY_PARSING.md

**XGIC GitLab GraphQL Client – Domain Models and Hierarchy Widget Parsing**  
**Version:** 1.0  
**Date:** June 27, 2026  
**Status:** Architecture Definition – Phase 1

---

## 1. Overview and Design Rationale

The domain models form the **type-safe contract** between the raw GraphQL responses and all higher-level client code (including Grok Build automation). 

We deliberately chose **Python dataclasses** + **Factory Method pattern** (`from_graphql`) for the following architectural reasons:

- Excellent IDE autocompletion and static analysis support (aligns with Google Python Style Guide).
- Immutable-by-default semantics reduce accidental mutation bugs in long-running automation scripts.
- Clear separation between *transport shape* (GraphQL) and *domain shape* (Python objects).
- Easy to extend with new fields or new Work Item types without breaking existing code.
- Natural fit for future structured data (estimates, actuals, custom widgets) instead of dumping everything into Markdown descriptions.

**Non-goals for Phase 1:**
- Full Work Item type coverage (Epics, Incidents, Test Cases, etc.).
- Async model variants.
- Pydantic or other heavy validation libraries (keep dependencies minimal — only `requests` + stdlib).

---

## 2. Core Modeling Principles

1. **Everything is a Work Item (or related entity)**  
   GitLab is moving toward a unified Work Items model. `BaseWorkItem` captures the common surface.

2. **Widgets are first-class citizens**  
   GitLab exposes rich behavior through the `widgets` array on Work Items. We parse only what we need today but design the parsing logic to be extensible.

3. **Hierarchy is explicit, not implicit**  
   Parent-child relationships between an Issue and its Tasks are **not** stored in a simple `parent_id` field at the top level. They live inside the `WorkItemWidgetHierarchy`. Our models surface this cleanly.

4. **Graceful degradation**  
   Missing widgets, partial data, or future GraphQL schema changes must never crash the client. We log warnings and return best-effort objects.

5. **Factory methods own the mapping**  
   All GraphQL → Python translation lives in `from_graphql()`. Business logic never sees raw dicts.

---

## 3. Detailed Model Definitions

### 3.1 BaseWorkItem

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any

@dataclass(frozen=True)
class BaseWorkItem:
    """
    Base class for all GitLab Work Items (Issues, Tasks, and future types).
    Contains fields common across the Work Items domain.
    """
    id: str                           # Global ID: "gid://gitlab/WorkItem/12345"
    iid: int                          # Project-scoped IID (human readable)
    title: str
    description: Optional[str] = None
    web_url: Optional[str] = None
    state: str = "opened"             # "opened", "closed", etc.
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    author: Optional[Dict[str, Any]] = None
    assignees: List[Dict[str, Any]] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    milestone: Optional[Dict[str, Any]] = None

    @classmethod
    def from_graphql(cls, data: Dict[str, Any]) -> "BaseWorkItem":
        """Factory. Subclasses override to add type-specific fields."""
        if not data:
            raise ValueError("Cannot create BaseWorkItem from empty GraphQL data")

        return cls(
            id=data.get("id"),
            iid=data.get("iid"),
            title=data.get("title", ""),
            description=data.get("description"),
            web_url=data.get("webUrl"),
            state=data.get("state", "opened"),
            created_at=cls._parse_datetime(data.get("createdAt")),
            updated_at=cls._parse_datetime(data.get("updatedAt")),
            author=data.get("author"),
            assignees=data.get("assignees", {}).get("nodes", []) if data.get("assignees") else [],
            labels=[node.get("title") for node in data.get("labels", {}).get("nodes", [])],
            milestone=data.get("milestone"),
        )

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
```

### 3.2 Issue

```python
@dataclass(frozen=True)
class Issue(BaseWorkItem):
    """
    Represents a primary Work Item (usually of type 'issue').
    Contains task completion status for visibility into child Tasks.
    """
    issue_type: str = "issue"
    task_completion_status: Optional[Dict[str, Any]] = None
    # Future: time_tracking: Optional[Dict] = None, custom_fields: Dict = field(default_factory=dict)

    @classmethod
    def from_graphql(cls, data: Dict[str, Any]) -> "Issue":
        base = super().from_graphql(data)
        return cls(
            **base.__dict__,
            issue_type=data.get("type", "issue").lower(),
            task_completion_status=data.get("taskCompletionStatus"),
            # widgets can be parsed here if needed for Issue-level hierarchy info
        )
```

### 3.3 Task (Critical – Hierarchy Support)

```python
@dataclass(frozen=True)
class Task(BaseWorkItem):
    """
    Represents a lightweight child Task under a parent Work Item.
    The parent relationship is extracted from the WorkItemWidgetHierarchy.
    """
    parent_id: Optional[str] = None   # Global ID of the parent Work Item

    @classmethod
    def from_graphql(cls, data: Dict[str, Any]) -> "Task":
        base = super().from_graphql(data)
        parent_id = cls._extract_parent_id_from_widgets(data.get("widgets", []))
        return cls(
            **base.__dict__,
            parent_id=parent_id,
        )

    @staticmethod
    def _extract_parent_id_from_widgets(widgets: List[Dict[str, Any]]) -> Optional[str]:
        """
        Exact algorithm for parsing the hierarchy widget.

        GitLab returns Work Items with a 'widgets' array. One of the widgets
        will have __typename == 'WorkItemWidgetHierarchy' when the item
        participates in a parent-child relationship.

        Structure (simplified real example):
        {
          "widgets": [
            { "__typename": "WorkItemWidgetHierarchy",
              "parent": { "id": "gid://gitlab/WorkItem/98765", "iid": 42, "title": "Parent Issue" },
              "children": { "nodes": [...] }
            },
            { "__typename": "WorkItemWidgetAssignees", ... },
            ...
          ]
        }

        Returns the parent's global ID or None if this is a top-level item
        or the hierarchy widget is absent/malformed.
        """
        if not widgets:
            return None

        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            if widget.get("__typename") == "WorkItemWidgetHierarchy":
                parent = widget.get("parent")
                if isinstance(parent, dict):
                    return parent.get("id")
                # parent can be null for root-level items
                return None
        return None
```

### 3.4 MergeRequest (Non-WorkItem entity)

```python
@dataclass(frozen=True)
class MergeRequest:
    """Lightweight model for Merge Requests (not a Work Item)."""
    id: str
    iid: int
    title: str
    description: Optional[str] = None
    web_url: Optional[str] = None
    state: str = "opened"
    source_branch: str = ""
    target_branch: str = "main"
    labels: List[str] = field(default_factory=list)

    @classmethod
    def from_graphql(cls, data: Dict[str, Any]) -> "MergeRequest":
        if not data:
            raise ValueError("Cannot create MergeRequest from empty data")
        return cls(
            id=data.get("id"),
            iid=data.get("iid"),
            title=data.get("title", ""),
            description=data.get("description"),
            web_url=data.get("webUrl"),
            state=data.get("state", "opened"),
            source_branch=data.get("sourceBranch", ""),
            target_branch=data.get("targetBranch", "main"),
            labels=[node.get("title") for node in data.get("labels", {}).get("nodes", [])],
        )
```

---

## 4. Hierarchy Widget Parsing – Detailed Explanation

### Why the widget system exists
GitLab’s Work Items model uses a **widget architecture** so that different capabilities (hierarchy, assignees, time tracking, custom fields, etc.) can be added orthogonally without bloating the core Work Item type.

### Exact parsing rules implemented in `_extract_parent_id_from_widgets`

1. Iterate over the `widgets` list returned in the GraphQL response.
2. Match on the discriminant field `"__typename": "WorkItemWidgetHierarchy"`.
3. If found, read the `parent` object.
4. Return `parent.id` (global ID) if present; otherwise `None`.
5. If no hierarchy widget exists at all → return `None` (this Work Item has no parent).

**Edge cases handled:**
- `widgets` key missing entirely → treat as no hierarchy.
- `widgets` is empty list → no hierarchy.
- `parent` key is `null` or absent → top-level item (valid for standalone Tasks or root Issues).
- Future widgets added by GitLab → ignored safely (we only care about `WorkItemWidgetHierarchy`).
- Malformed widget entries → skipped without crashing.

This algorithm is intentionally **narrow and defensive**. It will continue to work even if GitLab adds many new widgets.

### Creating the relationship (the other direction)
When **creating** a Task as a child, we do **not** use the parsing logic. Instead, the `create_task` / `workItemCreate` mutation includes a `hierarchyWidget` input:

```graphql
hierarchyWidget: {
  parent: { id: "gid://gitlab/WorkItem/PARENT_ID" }
}
```

The model layer only needs to support reading the relationship today.

---

## 5. Extensibility Points for Future Widgets

The current design makes adding new structured fields straightforward:

- Add a new dataclass field (e.g., `time_tracking: Optional[Dict]`).
- In the relevant `from_graphql`, look for the corresponding widget (e.g., `WorkItemWidgetTimeTracking`).
- Extract the nested data.

Example future addition (estimates / actuals):

```python
# In Issue or a new TimeTrackableWorkItem mixin
time_tracking = None
for widget in data.get("widgets", []):
    if widget.get("__typename") == "WorkItemWidgetTimeTracking":
        time_tracking = widget.get("timeTracking")
        break
```

This keeps the models aligned with GitLab’s own evolving widget system and supports the long-term goal of moving away from unstructured Markdown.

---

## 6. Mapping Reference (GraphQL → Python)

| GraphQL Field / Widget                  | Python Model Field          | Notes |
|-----------------------------------------|-----------------------------|-------|
| `id`                                    | `id`                        | Global ID (gid://...) |
| `iid`                                   | `iid`                       | Project-scoped |
| `title`, `description`, `webUrl`        | Same                        | Direct |
| `state`, `createdAt`, `updatedAt`       | Same                        | Direct + datetime parsing |
| `author`, `assignees.nodes`             | `author`, `assignees`       | User objects |
| `labels.nodes[].title`                  | `labels: List[str]`         | Flattened for convenience |
| `milestone`                             | `milestone`                 | Object or null |
| `taskCompletionStatus`                  | `task_completion_status`    | On Issue only |
| `widgets[]` + `__typename == WorkItemWidgetHierarchy` → `parent.id` | `parent_id` (Task only) | **Critical hierarchy logic** |
| `type`                                  | `issue_type`                | On Issue |

---

## 7. Robustness and Error Handling Strategy

- All `from_graphql` methods are **defensive**: they never assume presence of optional fields.
- Unknown or future widgets are silently ignored.
- Date parsing failures return `None` instead of raising (prevents one bad date from breaking an entire automation run).
- Empty or malformed top-level data raises a clear `ValueError` so callers can decide how to handle it.
- Logging of warnings for unexpected widget structures is recommended in the implementation (but not required in the model itself).

---

## 8. Summary of Architectural Benefits

- **Type safety & discoverability** for Grok Build and human developers.
- **Explicit hierarchy** instead of fragile Markdown checklists.
- **Extensible widget parsing** foundation for estimates, actuals, and custom fields.
- **Minimal dependencies** and clean separation of concerns.
- **Resilient to GitLab schema evolution** in the Work Items area.

This model layer, combined with the previously defined `GitLabClient` public API and the `create_issue_with_tasks` orchestration method, gives us a solid, professional foundation for reliable GitLab automation.

---

**End of Document**

*This file is part of the complete architecture package for the XGIC GitLab GraphQL Client (`xgic-gitlab-graphql`, namespace `xgic.gitlab.graphql`). It should be read together with:*
- `ADR-001-GitLab-GraphQL-Client.md`
- `ARCHITECTURE.md`
- `API_SURFACE_AND_IMPLEMENTATION_SKELETON.md`
- `GROK_BUILD_INTEGRATION.md`