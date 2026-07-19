# XGIC GitLab GraphQL Client

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://github.com/xgic/gitlab-graphql/actions/workflows/ci.yml/badge.svg)](https://github.com/xgic/gitlab-graphql/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/xgic-gitlab-graphql.svg)](https://pypi.org/project/xgic-gitlab-graphql/)
[![Python](https://img.shields.io/pypi/pyversions/xgic-gitlab-graphql.svg)](https://pypi.org/project/xgic-gitlab-graphql/)
[![Release](https://img.shields.io/github/v/release/xgic/gitlab-graphql)](https://github.com/xgic/gitlab-graphql/releases)

**XGIC GitLab GraphQL Client** (`xgic-gitlab-graphql`) — a clean, extensible, Python-first client for GitLab’s GraphQL API (namespace: `xgic.gitlab.graphql`).

**Goal:** Replace fragile CLI-based automation (`glab`) with a reliable, strongly-typed Python library that Grok Build (and humans) can use comfortably. Start with Issues + child Tasks (proper Work Item hierarchy), Merge Requests, Labels, Milestones, and Releases. Designed from day one to grow into full GraphQL coverage and structured data (estimates, actuals, etc.).

## Why this exists

- Official GitLab CLI escaping problems with long descriptions and complex content
- Need for real hierarchical Tasks instead of Markdown checklists
- Desire to move work data into structured, queryable fields
- Grok Build works best when it can simply `import` a well-designed Python library

## Key features (phase 1)

- High-level methods: `create_issue()`, `create_task(parent_id)`, `create_issue_with_tasks()` (create_merge_request() is a placeholder stub)
- Proper parent-child Task hierarchy via GitLab Work Items
- Clean data models (`Issue`, `Task`, `MergeRequest`) instead of raw dicts
- Centralized error handling and GraphQL execution
- Minimal dependencies (just `requests`)
- Cross-platform (Windows + Linux)
- Easy to install and reuse across projects

## Testing

See [TESTING.md](TESTING.md) for unit vs opt-in integration tests and the env contract (GITLAB_URL, GITLAB_TOKEN).

## Installation

```bash
uv pip install xgic-gitlab-graphql
```

### Development (editable)

```bash
git clone https://github.com/xgic/gitlab-graphql.git
cd gitlab-graphql
uv pip install -e ".[dev]"
```

Python **3.14+** required. Build/smoke with **uv**. Official releases use OIDC Trusted Publishing ([python-package-release.md](https://github.com/xgic/ai/blob/main/docs/python-package-release.md)). No Makefiles.

## Quick start (Python)

```python
from xgic.gitlab.graphql import GitLabClient

client = GitLabClient(
    token="glpat-xxxxxxxxxxxxxxxxxxxx",
    url="https://gitlab.com"   # or your self-hosted instance
)

# Create a parent issue
issue = client.create_issue(
    title="Implement new reporting feature",
    description="High-level description here...",
    namespace_path="group/project",
    labels=["feature", "backend"],
)

# Create child tasks under it
task1 = client.create_task(
    parent_id=issue.id,
    title="Design database schema",
    description="...",
    namespace_path="group/project",
)

task2 = client.create_task(
    parent_id=issue.id,
    title="Implement API endpoints",
    namespace_path="group/project",
)

print(f"Issue created: {issue.web_url}")
print(f"Tasks created under it.")
```

**Recommended for Grok Build:** Use the convenience method `create_issue_with_tasks(...)` whenever possible.

## Project Structure

See `docs/ARCHITECTURE.md` and `docs/development-workflow.md` for layout and responsibilities.

## Documentation

- [docs/ADR-001-GitLab-GraphQL-Client.md](docs/ADR-001-GitLab-GraphQL-Client.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md](docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md)
- [docs/development-workflow.md](docs/development-workflow.md)
- [docs/grok-playbooks.md](docs/grok-playbooks.md)
- [docs/GROK_BUILD_INTEGRATION.md](docs/GROK_BUILD_INTEGRATION.md)

## Engineering Tooling Philosophy

- Build backend: hatchling (namespace packages, uv)
- Environment / packaging: uv + pip
- Linting / formatting: ruff (Google docstrings)
- Type checking: pyright (strict)
- Testing: pytest
- Primary interface: Python library (import, not CLI)

Follows XGIC CLI standard + no Makefiles noted throughout.

## Status

Core client implemented (auth, queries/mutations for work items hierarchy + pagination, models, common queries). Base standards in place. Phase 1 complete for initial use cases.

See CHANGELOG.md for details.

## Multi-repo standards

Portfolio standards, ADRs, and community health:

- https://github.com/xgic/ai
- [Community health](https://github.com/xgic/ai/blob/main/docs/community-health.md)
- [BASE-STANDARDS](https://github.com/xgic/ai/blob/main/docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md)
- [Python namespace convention](https://github.com/xgic/ai/blob/main/docs/xgic-python-namespace-convention.md)

## License

Copyright 2026 XGIC.  
Licensed under the [Apache License, Version 2.0](LICENSE).  
See [NOTICE](NOTICE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Use GitHub Flow: issue-named branches, Conventional Commits, human review in the GitHub UI before merge to `main`.
