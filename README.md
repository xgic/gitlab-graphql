# XGIC GitLab GraphQL Client (`xgic-gitlab-graphql`)

The official XGIC GitLab GraphQL Client — a clean, extensible, Python-first client for GitLab’s GraphQL API (Python namespace: `xgic.gitlab.graphql`).

**Goal:** Replace fragile CLI-based automation (`glab`) with a reliable, strongly-typed Python library that Grok Build (and humans) can use comfortably. Start with Issues + child Tasks (proper Work Item hierarchy), Merge Requests, Labels, Milestones, and Releases. Designed from day one to grow into full GraphQL coverage and structured data (estimates, actuals, etc.).

## Why This Exists

- GitLab CLI escaping problems with long descriptions and complex content
- Need for real hierarchical Tasks instead of Markdown checklists
- Desire to move work data into structured, queryable fields
- Grok Build works best when it can simply `import` a well-designed Python library

## Key Features (Phase 1)

- High-level methods: `create_issue()`, `create_task(parent_id)`, `create_issue_with_tasks()`, `create_merge_request()`
- Proper parent-child Task hierarchy via GitLab Work Items
- Clean data models (`Issue`, `Task`, `MergeRequest`) instead of raw dicts
- Centralized error handling and GraphQL execution
- Minimal dependencies (just `requests`)
- Cross-platform (Windows + Linux)
- Easy to install and reuse across projects

## Installation (Development)

```bash
git clone https://github.com/xgic/gitlab-graphql.git
cd gitlab-graphql
pip install -e ".[dev]"
```

Or later via PyPI once published.

Python >= 3.12 required. Uses uv/hatch/ruff/pyright recommended. No Makefiles.

## Quick Start (Python)

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
    labels=["feature", "backend"],
)

# Create child tasks under it
task1 = client.create_task(
    parent_id=issue.id,
    title="Design database schema",
    description="..."
)

task2 = client.create_task(
    parent_id=issue.id,
    title="Implement API endpoints",
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

## License

TBD (likely MIT or Apache 2.0)

## Contributing

Follow the coding standards defined in the project (clean architecture, strong typing, Google-influenced Python style where applicable, comprehensive error handling). All changes should be made via feature branches with clear PR descriptions.
