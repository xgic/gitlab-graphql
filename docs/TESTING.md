# Testing

## Unit tests

```bash
uv pip install -e ".[dev]"
uv run pytest tests/ -q
```

Unit tests are fully mocked. Fixtures use **synthetic** namespace paths and GraphQL IDs only (for example `example-group/example-project`). Do not embed real private hosts, production project paths, or private usernames.

## Integration tests (opt-in)

Set `GITLAB_INTEGRATION=1` and provide configuration via environment variables:

| Variable | Purpose |
|----------|---------|
| `GITLAB_URL` | Base URL of a **non-production** GitLab EE instance |
| `GITLAB_TOKEN` | Token with API access to the test project only |
| `GITLAB_TEST_NAMESPACE_PATH` | Project path for CRUD exercises (dedicated test project) |
| `GITLAB_TEST_ASSIGNEE_ID` | Optional user global ID for assignee exercises |

Never point integration tests at production coordination projects. Prefer a dedicated GitLab EE stack (for example the XGIC GitLab Docker Compose template with a non-production GHCR orchestration image once available) and a project reserved for automated tests.

## Related standards

- Public multi-repo policy: [BASE-STANDARDS](https://github.com/xgic/ai/blob/main/docs/BASE-STANDARDS-FOR-ORCHESTRATED-REPOS.md) (configuration over hard-coding; zero private leakage)
