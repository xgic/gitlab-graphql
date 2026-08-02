# Compatibility and support policy

This document defines **official support** for the published package
[`xgic-gitlab-graphql`](https://pypi.org/project/xgic-gitlab-graphql/) against **GitLab EE**
(self-managed or SaaS GraphQL API).

## Primary install path

**Consumers and Grok Build** must use the **PyPI package** as the primary interface:

```bash
uv pip install xgic-gitlab-graphql
# pin the package version used for automation / validation as appropriate:
uv pip install "xgic-gitlab-graphql==0.1.2"
```

- Package index: https://pypi.org/project/xgic-gitlab-graphql/
- Editable installs (`uv pip install -e .`) are for **developing this repository only**, not for production automation or default agent workflows.

## GitLab EE version support (authoritative)

The **minimum supported version** for this product is a **GitLab EE** version, not a client package version.

| Rule | Policy |
|------|--------|
| **Official GitLab floor** | Align with versions **GitLab maintains** under the [GitLab release and maintenance policy](https://docs.gitlab.com/policy/maintenance/) (current stable for bug fixes; current + previous two monthly releases for security backports, as GitLab publishes). |
| **Post-upgrade baseline** | After lab and production are upgraded to **GitLab’s current EE stable** release, validate Work Item workflows using PyPI client **0.1.2**. If validation passes, that **GitLab EE stable version** (e.g. `N.M.P-ee`) becomes the **minimum supported GitLab EE version** for this client line until a later client release raises the floor. |
| **Do not** | Specialize the client solely so an **out-of-window / outdated** self-managed pin keeps working. |
| **Raise minimum GitLab EE** | When new client features need newer GraphQL/Work Item APIs, document the new **GitLab EE** floor on that **client** release (CHANGELOG + this file). |
| **Defensive GraphQL** | Optional fields, widgets, and schema differences may be handled in **future** client releases when needed for **GitLab-supported** EE versions—not as a permanent exception for unsupported EE pins. |

Re-evaluate the matrix on **every client package release**.

### Minimum GitLab EE (after validation)

| Status | GitLab EE minimum | How established |
|--------|-------------------|-----------------|
| **Pending** | _TBD — set to the current stable EE version string after successful validation_ | Upgrade lab + production to current stable → smoke with PyPI `xgic-gitlab-graphql==0.1.2` (issue + child task, labels/assignees as used by XGIC) → record version below |
| **Set** | _fill after validation_ | Dated **Tested** row proves the floor |

Do **not** put private hostnames in this public file—only public version strings (e.g. `18.11.2-ee`, `19.2.1-ee`).

## Client package versions (tooling, not the support floor)

| Client package (PyPI) | Role |
|-----------------------|------|
| **0.1.2** | Current published package used for **post-upgrade validation** against current GitLab EE stable. Preferred pin for Grok Build / automation until a newer package release is declared. |
| Newer releases | May require a **higher GitLab EE minimum** if they depend on newer APIs; document in that release’s CHANGELOG + this file. |
| Pre-0.1.2 | Not recommended for new automation. |

The support **floor** remains a **GitLab EE** version. Client package versions are what you install to talk to that GitLab.

### Tested matrix (fill after upgrade)

| Date (UTC) | GitLab EE (tested) | Client (PyPI) | Result | Notes |
|------------|--------------------|---------------|--------|--------|
| _pending_ | _current stable after upgrade_ | 0.1.2 | _TBD_ | Issue/task hierarchy smoke; if OK, set **Minimum GitLab EE** to this EE version |

## Related

- Issue tracking Work Item create schema portability: [#41](https://github.com/xgic/gitlab-graphql/issues/41)
- Compatibility-only PR held until post-upgrade validation: [#44](https://github.com/xgic/gitlab-graphql/pull/44) (draft / do not merge solely for outdated EE)
