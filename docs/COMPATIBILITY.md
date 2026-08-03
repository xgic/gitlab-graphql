# Compatibility and support policy

This document defines **official support** for the published package
[`xgic-gitlab-graphql`](https://pypi.org/project/xgic-gitlab-graphql/) against **GitLab EE**
(self-managed or SaaS GraphQL API).

## Primary install path

**Consumers and Grok Build** must use the **PyPI package** as the primary interface:

```bash
uv pip install xgic-gitlab-graphql
# pin the package version used for automation / validation as appropriate:
uv pip install "xgic-gitlab-graphql==0.1.3"
```

- Package index: https://pypi.org/project/xgic-gitlab-graphql/
- Editable installs (`uv pip install -e .`) are for **developing this repository only**, not for production automation or default agent workflows.

## GitLab EE version support (authoritative)

The **minimum supported version** for this product is a **GitLab EE** version, not a client package version.

| Rule | Policy |
|------|--------|
| **Official GitLab floor** | Align with versions **GitLab maintains** under the [GitLab release and maintenance policy](https://docs.gitlab.com/policy/maintenance/) (current stable for bug fixes; current + previous two monthly releases for security backports, as GitLab publishes). |
| **Post-upgrade baseline** | After lab and production are upgraded to **GitLab’s current EE stable** release, validate Work Item workflows using a **released** PyPI client. If validation passes, that **GitLab EE stable version** (e.g. `N.M.P-ee`) becomes the **minimum supported GitLab EE version** for this client line until a later client release raises the floor. |
| **Do not** | Specialize the client solely so an **out-of-window / outdated** self-managed pin keeps working. |
| **Raise minimum GitLab EE** | When new client features need newer GraphQL/Work Item APIs, document the new **GitLab EE** floor on that **client** release (CHANGELOG + this file). |
| **Defensive GraphQL** | Optional fields, widgets, and schema differences may be handled in client releases when needed for **GitLab-supported** EE versions—not as a permanent exception for unsupported EE pins. |

Re-evaluate the matrix on **every client package release**.

### Minimum GitLab EE (after validation)

| Status | GitLab EE minimum | How established |
|--------|-------------------|-----------------|
| **Set** | **`19.2.1-ee`** | Lab + production on GitLab EE **19.2.1-ee**; green Work Item create smoke with PyPI **`xgic-gitlab-graphql==0.1.3`** (issue + child task hierarchy). See **Tested** row below. |

Do **not** put private hostnames in this public file—only public version strings (e.g. `18.11.2-ee`, `19.2.1-ee`).

## Client package versions (tooling, not the support floor)

| Client package (PyPI) | Role |
|-----------------------|------|
| **0.1.3** | Current published package. Portable Work Item create selection (no hard dependency on `taskCompletionStatus` / top-level labels). Preferred pin for Grok Build / automation. |
| **0.1.2** | Previous pin; fails Work Item create on some self-hosted schemas missing `taskCompletionStatus` (see [#41](https://github.com/xgic/gitlab-graphql/issues/41)). Not recommended for new automation against EE 19.2.x. |
| Newer releases | May require a **higher GitLab EE minimum** if they depend on newer APIs; document in that release’s CHANGELOG + this file. |
| Pre-0.1.2 | Not recommended for new automation. |

The support **floor** remains a **GitLab EE** version. Client package versions are what you install to talk to that GitLab.

### Tested matrix

| Date (UTC) | GitLab EE (tested) | Client (PyPI) | Result | Notes |
|------------|--------------------|---------------|--------|--------|
| 2026-08-03 | 19.2.1-ee | 0.1.3 | **PASS** | `create_issue_with_tasks` issue + child task hierarchy on self-hosted GitLab EE after portable create fix ([#44](https://github.com/xgic/gitlab-graphql/pull/44), release [#46](https://github.com/xgic/gitlab-graphql/pull/46) / `v0.1.3`) |
| 2026-08-02 | 19.2.1-ee | 0.1.2 | **FAIL** | `taskCompletionStatus` not on `WorkItem` at create selection; upgrade alone did not fix ([#41](https://github.com/xgic/gitlab-graphql/issues/41)) |

## Related

- Work Item create schema portability: [#41](https://github.com/xgic/gitlab-graphql/issues/41)
- Portable create fix: [#44](https://github.com/xgic/gitlab-graphql/pull/44)
- Package release 0.1.3: [#46](https://github.com/xgic/gitlab-graphql/pull/46) / tag `v0.1.3`
