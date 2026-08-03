# Testing

## Unit tests (default)

- Use **synthetic fixtures only** (fictional hosts, project paths, IDs).
- Do **not** hard-code real production hosts, private project paths, or real user IDs.
- Configuration is injected via `GitLabConfig` / environment variables (see package docs).

```bash
pytest
```

## Integration tests (opt-in)

Integration tests talk to a **non-production** GitLab EE Docker Compose instance (lab).  
They must **never** target production coordination projects.

### Environment contract

| Variable | Required | Purpose |
|----------|----------|---------|
| `GITLAB_URL` | Yes | Lab base URL (operator-local) |
| `GITLAB_TOKEN` | Yes | Lab token with least privilege for the test project |
| `GITLAB_TEST_NAMESPACE_PATH` | Recommended | Path of a disposable lab group/project for CRUD |

If these variables are unset, integration tests should skip (not fail against production defaults).

### Lab stack (reference)

Use the public Docker Compose template:

- https://github.com/xgic/gitlab  
- Orchestration image: `ghcr.io/xgic/xgic-gitlab`  
- Distinct Compose project name for the lab (example: `xgic-gitlab-lab`)

Private operator runbook for lab stand-up lives in the private coordination hub (not linked from public artifacts).

### Safety checklist

1. `GITLAB_URL` is a lab / non-production endpoint  
2. Token cannot write production groups  
3. Unit tests still pass without any lab env vars  
