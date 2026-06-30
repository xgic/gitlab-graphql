# Changelog

All notable changes to the **XGIC GitLab GraphQL Client** (`xgic-gitlab-graphql`) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Core GitLabClient with token auth, GraphQL execution, error hierarchy.
- Work Item creation: create_issue, create_task, create_issue_with_tasks (proper hierarchy via widgets).
- Cursor-based pagination support (list_work_items, iter_work_items, _execute_paginated helper).
- Common queries: get_current_user, list/iter work items.
- Domain models: BaseWorkItem, Issue, Task, MergeRequest with from_graphql factories.
- Full package layout (xgic.gitlab.graphql namespace), __init__ exports.
- pyproject.toml updated: Python >=3.12, pydantic (applicable), ruff (Google), pyright, hatchling, pytest.
- Base standards: AGENTS.md, docs/, .github templates, .gitignore, CONTRIBUTING.md, DEV-JOURNAL, GROK-TASKS, LICENSE.
- Pagination follows GitLab Relay-style (pageInfo, first/after).
- Example usage script.

### Changed
- Updated tooling to XGIC CLI standard + no Makefiles.
- README, ARCHITECTURE references, docs aligned.

### Security / Public
- All artifacts sanitized. No private details.

See ADR-001 and primary plan for context (high-level only).


### Fixed
- 

### Security
- 

## [0.1.0] - 2026-07-01

### Added
- Initial public release of the XGIC GitLab GraphQL Client.
- `GitLabClient` with high-level methods: `create_issue()`, `create_task()`, `create_issue_with_tasks()`, and `create_merge_request()`.
- Full support for GitLab Work Items hierarchy (parent Issues with child Tasks via `hierarchyWidget`).
- Rich domain models (`BaseWorkItem`, `Issue`, `Task`) with explicit GraphQL response mapping and hierarchy widget parsing.
- Modern Python packaging using `hatchling` + `uv` with the official `xgic.gitlab.graphql` namespace.
- Comprehensive error handling, configuration via environment variables, and context manager support.
- Designed for reliable automation with Grok Build and other AI agents (Python-first, no shell escaping issues).

### Changed
- N/A (initial release)

[Unreleased]: https://github.com/xgic/gitlab-graphql/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xgic/gitlab-graphql/releases/tag/v0.1.0

---

## Release Process Notes (XGIC Internal)

This section documents the recommended release workflow for the `xgic-gitlab-graphql` repository. It aligns with XGIC’s commitment to selecting optimal, modern tooling and Conventional Commits.

### Prerequisites
- Use **`uv`** as the primary package and environment manager.
- Follow **[Conventional Commits](https://www.conventionalcommits.org/)** for all commit messages (enables future automation).
- Keep `CHANGELOG.md` up to date manually during early versions (consider `commitizen` or `standard-version` later).

### Recommended Release Steps

1. **Prepare the release**
   - Ensure `main` is up to date and all CI checks pass.
   - Update `CHANGELOG.md` under `[Unreleased]` with user-facing changes.
   - Commit the changelog update using Conventional Commits style:
     ```bash
     git commit -m "docs(changelog): prepare v0.2.0 release notes"
     ```

2. **Version bump**
   ```bash
   # Recommended: use hatch for clean version management
   uv run hatch version minor   # or patch / major
   ```

3. **Build the distribution**
   ```bash
   uv build
   ```
   This produces `dist/xgic_gitlab_graphql-<version>-py3-none-any.whl` and the source tarball.

4. **Publish to PyPI** (when ready for public release)
   ```bash
   uv publish
   ```
   Or use `hatch publish` if preferred.

5. **Create GitHub Release**
   - Go to **Releases** → **Draft a new release**
   - Select the new tag (created by `hatch version` or manually)
   - Paste the relevant section from `CHANGELOG.md` into the release notes
   - Mark as "Latest release" when appropriate

6. **Post-release**
   - Merge the release commit back to `main` if using release branches.
   - Announce internally (and publicly once the repo is public) via appropriate XGIC channels.
   - Update any dependent internal projects (e.g., `xgic.cli.*` packages).

### Pre-release / Alpha / Beta Workflow
Use PEP 440 compliant suffixes:
```bash
uv run hatch version 0.2.0a1
uv build
uv publish
```

### Notes
- The project intentionally keeps a **minimal dependency footprint** (`requests` only). New dependencies must be justified in an ADR update.
- All releases must respect the **XGIC Python Namespace Convention** (`xgic.gitlab.graphql`).
- For the initial private phase, publishing may be limited to an internal PyPI mirror or direct `pip install -e .` usage until the repository goes public.

This process ensures traceability, reproducibility, and alignment with XGIC’s engineering standards across all internal and client projects.
