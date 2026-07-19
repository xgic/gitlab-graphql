# AI Agent Instructions for XGIC GitLab GraphQL Client

**This is the primary context document for AI coding assistants (especially Grok Build) when working in this repository.**

Read this file completely before starting any significant work.

## How We Work Together (Collaboration Principles)

- Positive, constructive, forward-looking language only.
- **Hard security (absolute):** zero private leakage on every public surface—files, issues, **PR/issue/Discussion bodies and comments**, commits, package metadata, and agent output destined for public artifacts.
- Git management + mandatory review gate: every change must receive explicit review and approval before push or merge to main.
  - Grok produces drafts only.
  - "Review and approval required before any remote action or merge to main — see AGENTS.md and BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md."
  - Approval performed in GitHub web UI.
- Commit discipline: detailed Conventional Commits. Atomic. Squash related. Include relevant tests/docs.
- XGIC CLI standard + no Makefiles noted throughout.
- Use ruff, pyright, pytest, hatchling/uv. Python >= 3.14.
- All artifacts complete fields (labels, assignees where possible).

## Hard security (public surfaces)

**Forbidden** on this public repository:

- Private hosts or internal URLs
- Private tracker paths, work-item links, or private project issue/MR URLs
- Private tracker IDs, private hub names, or private repository identities
- Private local filesystem paths as required documentation
- Hard-coded private project paths, usernames, or real user/work-item GIDs in source or tests
- Restating portfolio hard-security rules inside PR/issue bodies (rules live in this file and multi-repo standards)

**Allowed on project artifacts:** technical change summary only; full `https://github.com/xgic/...` URLs; same-repo `#N`. When work is coordinated privately, omit that fact from public artifacts entirely.

**Configuration over hard-coding:** `GitLabConfig` / env (`GITLAB_URL`, `GITLAB_TOKEN`, `GITLAB_TEST_NAMESPACE_PATH`, …). Unit tests use synthetic fixtures only. Integration tests (opt-in) use a dedicated non-production GitLab—never production coordination projects.

**Pre-publish checklist** (every public PR/issue body, comment, commit, and test change):

1. No private hosts / internal URLs  
2. No private tracker IDs, private hub/repo names, or private work-item links  
3. No private local paths  
4. No hard-coded private paths/user IDs in tests or examples  
5. No rule restatement in project artifacts  
6. Labels applied  

**Before close:** verify every Markdown checklist item on the issue/PR, mark completed items `- [x]`, and do not close with unchecked required items unless a human documents a waiver. Reviewers (human or future AI) apply the same gate.

Violations are security incidents: sanitize immediately. Multi-repo policy: https://github.com/xgic/ai/blob/main/docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md

## Session Startup Checklist (Run First)

1. grok inspect
2. git status --short + git remote -v
3. Review AGENTS.md, docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md, pyproject.toml, and relevant plan sections.
4. Use gh to list current open issues/PRs/CI for this project.
5. Confirm status reporting support (exact ID "XGIC GitLab GraphQL Client").
6. Review GitLab GraphQL API docs (EE) and best practices.
7. Ensure all artifacts complete required fields and use proper tracking.
8. Confirm drafts are **public-safe** (hard security scan above).

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
