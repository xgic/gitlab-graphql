# Base Standards for Orchestrated Repos (Public Exemplary Variant)

**Purpose**: This living document defines the minimum set of documentation, common architecture patterns, and AI collaboration standards that must exist on public exemplary repositories orchestrated under the XGIC portfolio. It is a sanitized, public-only variant of the authoritative standards.

Public exemplary repos (such as this one) receive this sanitized subset. Emphasis is on exemplary open-source process, agent ergonomics, living guides, external-contributor simulation, and strict adherence to security boundaries.

**Last major update**: 2026 — Public variant for gitlab-graphql and future public launches.

## Hard Security Rule (Non-Negotiable — Zero Exposure)

**Zero exposure (absolute)**: No mentions, names, details, architectures, experiments, timelines, strategies, links, or any information that would reveal the existence, identity, or structure of any private repositories or private coordination hubs may ever be placed in any public XGIC repository (this repo or any other public one). This includes documentation, prompts, code, issues, PRs, READMEs, or any Grok output.

All detailed coordination, private project work, and anything involving private repos or sensitive strategy lives *exclusively* in the authoritative private AI orchestration repository.

Public repositories and public sessions must remain completely silent on private details and structures. Only the most abstract high-level references are permissible when essential.

Violations are treated as security incidents. Human review is mandatory to prevent leakage.

## Mandatory Sanitization Rule (Non-Negotiable — Core of Hard Security)

**Never include private GitLab issue numbers, private URLs, private repo paths, or direct links to private issues/MRs in any public file, source comment, commit message, PR body, issue, changelog, or artifact.**

- Replace with high-level text.
- Reference only public GitHub issues/PRs from *this repository*.
- Enforce via pre-change verification, human review, and periodic leak scans.

## Mandatory Review Gate Before Main (Beta-Era Rule)

**While Grok Build is in beta, every change must receive at least one explicit code review and approval before it is pushed or merged to the primary branch (main).**

- "Code review" includes docs, AGENTS.md, playbooks, scripts, and source.
- The human must inspect the proposal/diff, run verification steps, and give explicit approval **before** any push or merge to main.
- For public exemplary repos: real PR + approval(s), consistent with the external-contributor-simulation model.
- Grok always produces clean professional draft artifacts (Draft PRs carrying explicit "Review and approval required before any remote action or merge to main" language in the body) and pauses for approval.
- **Mandatory code review in platform UI**: All Pull Requests must undergo explicit code review performed directly in the GitHub web interface.

**Review and approval required before any remote action or merge to main.**

## Minimum Required Artifacts (The Base Set)

Every public exemplary orchestrated repo must have (at minimum) the following:

1. Hard security / private leakage rule (this document and AGENTS.md).
2. Pure flow + branch protection: Strict GitHub Flow. main is always stable. All work on short-lived branches. Merge only after required human review(s) + checks pass.
3. Standard labels and templates: Consistent labels. `.github/ISSUE_TEMPLATE/` and `PULL_REQUEST_TEMPLATE.md` with standard fields and practical checklists (no restatement of rules or gate procedures from AGENTS.md or BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md).
4. The review gate (documented in CONTRIBUTING.md + AGENTS.md).
5. Root project instruction file: `AGENTS.md`.
6. CONTRIBUTING.md (at `.github/CONTRIBUTING.md`).
7. README.md: Purpose, quick start, security note, high-level status.
8. docs/ skeleton:
   - development-workflow.md (or orchestration-workflow.md)
   - architecture.md (or ARCHITECTURE.md)
   - grok-playbooks.md
   - BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md (this file)
9. Lightweight AI memory: DEV-JOURNAL.md , GROK-TASKS.md
10. .gitignore: Comprehensive, includes `.xgic/` (never commit).
11. Commit discipline: Detailed Conventional Commits. Atomic. Squash related small changes. Positive framing.
12. xde as the standard for container / environment orchestration tasks (no Makefiles).
13. Grok usage rules: clean professional drafts carrying the exact gate sentence. Mandatory review and approval on every remote action.

See AGENTS.md and the primary coordination for full details (high-level only in public).

## XGIC CLI standard + no Makefiles noted throughout

All orchestrated repos follow the XGIC CLI standard. No Makefiles are created or retained. Use Python-native tooling, pyproject.toml scripts, uv, hatch, ruff, pytest, etc.

## Python 3.14 standardization (new development only; see ADR 0002)
- All *new* Python code and projects shall use Python 3.14 as the minimum (latest stable).
- `pyproject.toml`: `requires-python = ">=3.14"`
- Containerized environments: official `python:3.14.6-slim` (pinned) base image.
- Update classifiers, CI, devcontainer.json, Dockerfiles, READMEs, AGENTS.md, and local standards to reflect this.
- Existing projects: optional migration; no forced changes unless part of new work.
- Fallback to 3.12 only after exhausting options (documented).
- Reference: public multi-repo standards at https://github.com/xgic/ai (docs/xgic-python-namespace-convention.md and docs/adr/).

## Session Status Reporting

Every Grok Build session supports status reporting with exact ID "XGIC GitLab GraphQL Client".

Reports are generated on trigger and saved to `.xgic/grok-build/status-report.md` (never committed).

## End of BASE-STANDARDS
