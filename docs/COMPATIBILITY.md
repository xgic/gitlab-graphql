# Compatibility and support policy

This document defines **official support** for the published package
[`xgic-gitlab-graphql`](https://pypi.org/project/xgic-gitlab-graphql/) against **GitLab EE**
(self-managed or SaaS GraphQL API).

## Primary install path

**Consumers and Grok Build** must use the **PyPI package** as the primary interface:

```bash
uv pip install xgic-gitlab-graphql
# pin when integrating automation:
uv pip install "xgic-gitlab-graphql==0.1.2"
```

- Package index: https://pypi.org/project/xgic-gitlab-graphql/
- Editable installs (`uv pip install -e .`) are for **developing this repository only**, not for production automation or default agent workflows.

## GitLab EE version support

| Rule | Policy |
|------|--------|
| **Official GitLab floor** | Align with versions **GitLab maintains** under the [GitLab release and maintenance policy](https://docs.gitlab.com/policy/maintenance/) (current stable for bug fixes; current + previous two monthly releases for security backports, as GitLab publishes). |
| **Do not** | Specialize the client solely so an **out-of-window / outdated** self-managed pin keeps working. |
| **Raise minimum GitLab** | When new client features need newer GraphQL/Work Item APIs, document the new floor on that **client** release. |
| **Defensive GraphQL** | Optional fields, widgets, and schema differences may be handled in **future** client releases when needed for **GitLab-supported** versions—not as a permanent exception for unsupported EE pins. |

Re-evaluate the matrix on **every client release**.

## Client version support (working rule)

| Client version | Status (until post-upgrade validation) |
|----------------|------------------------------------------|
| **0.1.2** (PyPI) | **Candidate minimum**: after lab + production GitLab EE are on **current stable**, validate Work Item create (issue + child task, labels/assignees as used by XGIC). If validation passes, **0.1.2 becomes the minimum supported client version** going forward. |
| Newer releases | May raise minimum GitLab EE and/or client floor; document in that release’s CHANGELOG + this file. |
| Pre-0.1.2 | Not official for new automation. |

Update this section with a dated **Tested** row after validation (GitLab EE version string + client version + date). Do **not** put private hostnames in this public file.

### Tested matrix (fill after upgrade)

| Date (UTC) | Client (PyPI) | GitLab EE (tested) | Result | Notes |
|------------|---------------|--------------------|--------|--------|
| _pending_ | 0.1.2 | _current stable after upgrade_ | _TBD_ | Issue/task hierarchy smoke |

## Related

- Issue tracking Work Item create schema portability: [#41](https://github.com/xgic/gitlab-graphql/issues/41)
- Compatibility-only PR held until post-upgrade validation: [#44](https://github.com/xgic/gitlab-graphql/pull/44) (draft / do not merge solely for outdated EE)
