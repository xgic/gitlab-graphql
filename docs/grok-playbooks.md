# Grok Playbooks — XGIC GitLab GraphQL Client

High-level guidance for Grok Build and humans.

## Common Tasks
- Add new GraphQL operation: update operations.py, add client method, tests, docs.
- Support new entity: extend models, add query/mutation in contract/ops, update client.
- Pagination: use built-in _execute_paginated + list_* / iter_* helpers.

## Testing
- Unit with mocks on _execute.
- Run: `python -m pytest` or `uv run pytest`.

## Packaging / Release
- Bump version in pyproject.toml.
- Update CHANGELOG.md.
- Human LGTM + PR.

## Status Reporting
Trigger with "session status report" or similar. Uses ID "XGIC GitLab GraphQL Client". Output to .xgic/grok-build/status-report.md (gitignored).

## Human Gate
All draft artifacts must contain:
"Review and approval per AGENTS.md and BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md."
Approval performed in GitHub web UI.
