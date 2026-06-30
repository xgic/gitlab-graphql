# Development Workflow — XGIC GitLab GraphQL Client

Follow GitHub Flow.

## Branching
- main is protected, stable.
- Create short-lived feature branches from main.
- Never commit directly to main.

## Commits
- Detailed Conventional Commits.
- Atomic and complete (include tests, docs).
- Squash related small changes into one detailed commit.
- Positive, forward-looking framing.

## Pre-commit checks
- ruff check + format.
- pyright type check.
- pytest.
- Security / leakage scan (high-level only, no private refs).
- After code changes, audit docs (README, examples, design docs) for synchronization with code (see code-doc-synchronization-report.md).

## PRs
- Open PR from branch.
- Review and approval required before any remote action or merge to main — see AGENTS.md and BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md.
- All checks must pass.
- Approval performed in GitHub web UI.
- Include "Closes #X", "Fixes #X", or "Resolves #X" in PR body/commits to auto-close issues on merge (see .github/workflows/auto-close-issues-on-merge.yml and PR template).

## No Makefiles
Use pyproject + uv/pip + ruff/pytest. See pyproject.toml.

## Status Reports
Support exact Session ID "XGIC GitLab GraphQL Client".
