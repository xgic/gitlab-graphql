# Changelog

All notable changes to the **XGIC GitLab GraphQL Client** (`xgic-gitlab-graphql`) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.4rc1] - 2026-08-03

Release candidate for TestPyPI (`create_merge_request` + portable Work Item create notes carried from 0.1.3 line).

### Added
- `GitLabClient.create_merge_request()` via GraphQL `mergeRequestCreate` (title, source/target branch, description, labels, assignees); `MergeRequestCreationError` on failure (#51 / #52).

### Fixed
- `workItemCreate` selection set no longer requests `taskCompletionStatus` or top-level `labels` (missing on some self-hosted WorkItem schemas). Labels/assignees read from widgets when present; optional completion status remains `None` on create (#41).
- Create path uses `labelsWidget.labelIds` after resolving label titles (schemas that reject top-level `labelNames`).

## [0.1.3] - 2026-08-02

### Fixed
- Portable Work Item create selection and labelsWidget IDs for self-hosted GitLab EE schemas missing `taskCompletionStatus` (https://github.com/xgic/gitlab-graphql/issues/41, https://github.com/xgic/gitlab-graphql/pull/44).

## [0.1.2rc1] - 2026-07-19

Release candidate for TestPyPI (same content as 0.1.2 final).

## [0.1.2] - 2026-07-19

### Fixed
- Work Item GraphQL selection set: read assignees via `WorkItemWidgetAssignees` (not top-level `assignees`) so create/list works on current GitLab EE.
- Wire `assignee_ids` through `create_issue` / `create_task` / `create_issue_with_tasks` via `assigneesWidget` so child Tasks can be assigned at create time.
- Propagate parent labels and assignees to child Tasks in `create_issue_with_tasks` (per-task override supported).
- Remove hard-coded private project/user identifiers from unit tests; use synthetic fixtures and env-driven integration config only.

## [0.1.1] - 2026-07-19

### Added
- GitHub Actions CI (pytest, ruff, uv package smoke) and OIDC release workflow for TestPyPI/PyPI.
- Release Environments `testpypi` / `pypi`.
- First public index publish path (TestPyPI RC `0.1.1rc1`, then PyPI `0.1.1`).
- Core GitLabClient with token auth, GraphQL execution, error hierarchy.
- Work Item creation: create_issue, create_task, create_issue_with_tasks (proper hierarchy via widgets).
- Cursor-based pagination support (list_work_items, iter_work_items, _execute_paginated helper).
- Common queries: get_current_user, list/iter work items.
