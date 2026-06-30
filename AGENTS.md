# AI Agent Instructions for XGIC GitLab GraphQL Client

**This is the primary context document for AI coding assistants (especially Grok Build) when working in this repository.**

Read this file completely before starting any significant work.

## How We Work Together (Collaboration Principles)

- Positive, constructive, forward-looking language only.
- Hard security rule (zero exposure of private details) is absolute. Public repo must stay silent.
- Git management + mandatory review gate: every change must receive explicit review and approval before push or merge to main.
  - Grok produces drafts only.
  - "Review and approval required before any remote action or merge to main — see AGENTS.md and BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md."
  - Approval performed in GitHub web UI.
- Commit discipline: detailed Conventional Commits. Atomic. Squash related. Include relevant tests/docs.
- XGIC CLI standard + no Makefiles noted throughout.
- Use ruff, pyright, pytest, hatchling/uv. Python >= 3.12.
- All artifacts complete fields (labels, assignees where possible).

## Session Startup Checklist (Run First)

1. grok inspect
2. git status --short + git remote -v
3. Review AGENTS.md, docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md, pyproject.toml, and relevant plan sections.
4. Use gh to list current open issues/PRs/CI for this project.
5. Confirm status reporting support (exact ID "XGIC GitLab GraphQL Client").
6. Review GitLab GraphQL API docs (EE) and best practices.
7. Ensure all artifacts complete required fields and use proper tracking.

## Status Reporting Support

This session supports exact ID "XGIC GitLab GraphQL Client".
- Generate full structured status report using the canonical template.
- Save to `.xgic/grok-build/status-report.md` (never committed).
- Current UTC time format: yyyy-MM-dd-HH-mm-utc

## GitHub Flow + Review Gate

- Strict GitHub Flow.
- Draft PRs/issues must carry the gate sentence in body.
- No remote actions (push, PR create, issue create that affects main tracking) without prior human LGTM in UI.

## Python Standards

- Namespace: xgic.gitlab.graphql
- OO design, strong typing, Google-influenced docstrings via ruff.
- Pydantic where applicable.
- Centralized GraphQL in graphql/ops.
- Rich models over dicts.
- Pagination via cursor helpers.

## References (High-Level)

- docs/ARCHITECTURE.md
- docs/ADR-001-GitLab-GraphQL-Client.md
- docs/development-workflow.md
- docs/grok-playbooks.md
- docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md
- GitLab official GraphQL docs for EE Work Items and cursor pagination.

Review and approval required before any remote action or merge to main — see AGENTS.md and BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md.
