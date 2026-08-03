# Release process (this package)

**Authority:** [XGIC public Python package release process](https://github.com/xgic/ai/blob/main/docs/python-package-release.md)  
**Workflow:** [`.github/workflows/release.yml`](../.github/workflows/release.yml)  
**Package:** [`xgic-gitlab-graphql`](https://pypi.org/project/xgic-gitlab-graphql/)

This document is the **repo-local** checklist. It does not replace the hub standard; it makes the RC → TestPyPI → final → PyPI path hard to skip for agents and operators.

## Non-negotiable order

| Step | Version in `pyproject.toml` | Git tag | Index | GitHub Release |
|------|----------------------------|---------|-------|----------------|
| 1. RC | `X.Y.ZrcN` (e.g. `0.1.4rc1`) | `vX.Y.ZrcN` | **TestPyPI** | Prerelease **required** after TestPyPI smoke |
| 2. Final | `X.Y.Z` (e.g. `0.1.4`) | `vX.Y.Z` | **PyPI** | Final **required** after PyPI smoke |

**Never** cut a final tag (`vX.Y.Z` without `rc`) before a successful RC for the same `X.Y.Z` line has been published to TestPyPI and smoked.

CI enforces this: the Release workflow **fails final tags** unless a prior `vX.Y.Zrc*` tag exists (job `Require prior RC tag`).

## Operator / agent sequence

### A. Release candidate (TestPyPI)

1. Feature/fix work merged to `main` with human UI approval.  
2. Open a **release-candidate** PR that only:
   - Sets `project.version` to `X.Y.Zrc1` (or next `rcN`)
   - Updates `CHANGELOG.md` for the RC  
3. Human review/merge.  
4. Tag and push: `git tag -a vX.Y.Zrc1 -m "vX.Y.Zrc1"` → `git push origin vX.Y.Zrc1`  
5. Confirm **Release** workflow: Publish to TestPyPI → Smoke install (TestPyPI) → GitHub Release (prerelease).  
6. **Stop** if smoke fails. Fix and cut `rcN+1`.

### B. Final (PyPI)

1. Open a **final** PR that sets `project.version` to `X.Y.Z` (drop `rc`).  
2. Human review/merge.  
3. Tag and push: `git tag -a vX.Y.Z -m "vX.Y.Z"` → `git push origin vX.Y.Z`  
4. Confirm **Release** workflow: Require prior RC → Publish to PyPI → Smoke (PyPI) → GitHub Release (final).

## Forbidden shortcuts

- Tagging `vX.Y.Z` immediately after a feature merge without RC  
- “Skip TestPyPI because CI already passed on main”  
- Publishing with long-lived tokens or from a workstation  
- Agent merge of release PRs; agents must not push release tags without an explicit human LGTM for **that** RC/final step  

## Incident: `v0.1.3` (2026-08-03)

`v0.1.3` was tagged and published to **PyPI** without a prior `v0.1.3rcN` / TestPyPI publish. That violated hub §5 / §7–8 and this package’s historical pattern (`v0.1.2rc1` then `v0.1.2`).

- **Root cause:** operator path (agent-assisted) jumped to a final version bump and final tag.  
- **Not a workflow bug:** `release.yml` correctly routes only `*rc*` tags to TestPyPI; a final tag never hits TestPyPI.  
- **Remediation:** `require-prior-rc` job + this doc + AGENTS checklist (this PR).  
- **Do not yank** `0.1.3` solely for process (non-security). Future lines **must** use RC first (e.g. `0.1.4rc1` → `0.1.4`).

## Related

- Hub: https://github.com/xgic/ai/blob/main/docs/python-package-release.md  
- Compat / support floor: [COMPATIBILITY.md](COMPATIBILITY.md)  
