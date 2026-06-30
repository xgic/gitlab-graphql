"""Domain models for the XGIC GitLab GraphQL Client.

Uses frozen dataclasses + from_graphql factory methods per the architecture
defined in docs/DOMAIN_MODELS_AND_HIERARCHY_PARSING.md.

These provide clean, typed objects instead of raw dicts for all consumers
including Grok Build.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class BaseWorkItem:
    """Base class for all GitLab Work Items (Issues, Tasks, and future types)."""

    id: str  # Global ID: "gid://gitlab/WorkItem/12345"
    iid: int  # Project-scoped IID (human readable)
    title: str
    description: str | None = None
    web_url: str | None = None
    state: str = "opened"
    created_at: datetime | None = None
    updated_at: datetime | None = None
    author: dict[str, Any] | None = None
    assignees: list[dict[str, Any]] = field(default_factory=list)
    labels: list[str] = field(default_factory=list)
    milestone: dict[str, Any] | None = None

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> BaseWorkItem:
        """Factory. Subclasses override to add type-specific fields."""
        if not data:
            raise ValueError("Cannot create BaseWorkItem from empty GraphQL data")

        return cls(
            id=data.get("id", ""),
            iid=data.get("iid") or 0,
            title=data.get("title", ""),
            description=data.get("description"),
            web_url=data.get("webUrl"),
            state=data.get("state", "opened"),
            created_at=cls._parse_datetime(data.get("createdAt")),
            updated_at=cls._parse_datetime(data.get("updatedAt")),
            author=data.get("author"),
            assignees=(
                data.get("assignees", {}).get("nodes", [])
                if data.get("assignees")
                else []
            ),
            labels=[
                node.get("title") for node in data.get("labels", {}).get("nodes", [])
            ],
            milestone=data.get("milestone"),
        )

    @staticmethod
    def _parse_datetime(dt_str: str | None) -> datetime | None:
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None


@dataclass(frozen=True)
class Issue(BaseWorkItem):
    """Represents a primary Work Item (usually of type 'issue')."""

    issue_type: str = "issue"
    task_completion_status: dict[str, Any] | None = None

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> Issue:
        # Construct via base then update (frozen-safe via replace or direct)
        base = BaseWorkItem.from_graphql(data)
        return cls(
            id=base.id,
            iid=base.iid,
            title=base.title,
            description=base.description,
            web_url=base.web_url,
            state=base.state,
            created_at=base.created_at,
            updated_at=base.updated_at,
            author=base.author,
            assignees=base.assignees,
            labels=base.labels,
            milestone=base.milestone,
            issue_type=data.get("type", "issue").lower(),
            task_completion_status=data.get("taskCompletionStatus"),
        )


@dataclass(frozen=True)
class Task(BaseWorkItem):
    """Represents a child Task under a parent Work Item. Hierarchy via widget."""

    parent_id: str | None = None  # Global ID of the parent Work Item

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> Task:
        base = BaseWorkItem.from_graphql(data)
        parent_id = cls._extract_parent_id_from_widgets(data.get("widgets", []))
        return cls(
            id=base.id,
            iid=base.iid,
            title=base.title,
            description=base.description,
            web_url=base.web_url,
            state=base.state,
            created_at=base.created_at,
            updated_at=base.updated_at,
            author=base.author,
            assignees=base.assignees,
            labels=base.labels,
            milestone=base.milestone,
            parent_id=parent_id,
        )

    @staticmethod
    def _extract_parent_id_from_widgets(
        widgets: list[dict[str, Any]],
    ) -> str | None:
        """Parse WorkItemWidgetHierarchy for parent ID."""
        if not widgets:
            return None
        for widget in widgets:
            if not isinstance(widget, dict):
                continue
            if widget.get("__typename") == "WorkItemWidgetHierarchy":
                parent = widget.get("parent")
                if isinstance(parent, dict):
                    return parent.get("id")
                return None
        return None


@dataclass(frozen=True)
class MergeRequest:
    """Lightweight model for Merge Requests (not a Work Item)."""

    id: str
    iid: int
    title: str
    description: str | None = None
    web_url: str | None = None
    state: str = "opened"
    source_branch: str = ""
    target_branch: str = "main"
    labels: list[str] = field(default_factory=list)

    @classmethod
    def from_graphql(cls, data: dict[str, Any]) -> MergeRequest:
        if not data:
            raise ValueError("Cannot create MergeRequest from empty data")
        return cls(
            id=data.get("id", ""),
            iid=data.get("iid") or 0,
            title=data.get("title", ""),
            description=data.get("description"),
            web_url=data.get("webUrl"),
            state=data.get("state", "opened"),
            source_branch=data.get("sourceBranch", ""),
            target_branch=data.get("targetBranch", "main"),
            labels=[
                node.get("title") for node in data.get("labels", {}).get("nodes", [])
            ],
        )


# End of models.py
