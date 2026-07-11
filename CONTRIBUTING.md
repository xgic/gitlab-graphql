# Contributing to XGIC GitLab GraphQL Client

Thank you for contributing to [xgic/gitlab-graphql](https://github.com/xgic/gitlab-graphql).

## Process

1. Open an issue for non-trivial work (use the YAML issue forms).
2. Create a dedicated short-lived branch from latest `main` that includes the tracking issue number in the name.
3. Use [Conventional Commits](https://www.conventionalcommits.org/).
4. Open a pull request against `main`.
5. A maintainer reviews and approves in the **GitHub UI** before merge.

## Coding standards

- Python **3.14+** (`requires-python` in `pyproject.toml`)
- Ruff, Pyright, pytest
- Prefer the XGIC CLI direction; no new Makefiles
- Positive, professional tone
- Public-safe content only (no private hosts, private tracker IDs, internal paths, or secrets)

## Multi-repo standards

Link portfolio standards rather than copying them:

- https://github.com/xgic/ai
- Community health: https://github.com/xgic/ai/blob/main/docs/community-health.md
- BASE-STANDARDS: https://github.com/xgic/ai/blob/main/docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md

## Status reports (local only)

Grok Build sessions may write temporary status reports under `.xgic/` (gitignored). Session ID: `XGIC GitLab GraphQL Client`.

## License

Contributions are under the same license as this repository (see `LICENSE` / package metadata).
