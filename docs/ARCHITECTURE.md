# Architecture & Design — XGIC GitLab GraphQL Client

This document describes the high-level architecture, package structure, module responsibilities, and key design decisions for the **XGIC GitLab GraphQL Client** (`xgic-gitlab-graphql`, import namespace `xgic.gitlab.graphql`).

## Design Goals

1. **Reliability first** — Eliminate shell escaping and fragility issues seen with CLI tools.
2. **Python-native experience** — Grok Build (and humans) interact via clean `import` and method calls, not shell commands.
3. **Clean separation of concerns** — GraphQL details hidden from consumers.
4. **Extensibility by design** — Easy to add new entities, structured fields (estimates/actuals), and eventually an MCP wrapper.
5. **Strong typing & maintainability** — Use modern Python (dataclasses, type hints, factory methods) for IDE support and safety.
6. **Minimal dependencies** — Only `requests` for HTTP in Phase 1.
7. **Cross-platform** — Works on Windows and Linux without modification.
8. **Modern, optimal tooling** — Use `hatchling` + `uv` for packaging and workflows (see ADR-001 for the full build backend evaluation).

## Recommended Package Structure

```
xgic-gitlab-graphql/
├── src/
│   └── xgic/
│       └── gitlab/
│           └── graphql/
│               ├── __init__.py                 # Public exports (GitLabClient, models, exceptions)
│               ├── client.py                   # Main GitLabClient class + public API
│               ├── config.py                   # GitLabConfig (URL, token, timeout, etc.)
│               ├── models.py                   # Dataclass models: Issue, Task, MergeRequest, BaseWorkItem
│               ├── exceptions.py               # Custom exception hierarchy (GitLabError, GraphQLError, etc.)
│               ├── graphql/
│               │   ├── __init__.py
│               │   ├── queries.py              # Reusable query strings (read operations)
│               │   └── operations.py           # Mutation strings + thin wrapper functions
│               └── utils/
│                   ├── __init__.py
│                   └── validators.py           # Input validation helpers (optional in Phase 1)
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_models.py
│   └── test_operations.py
├── pyproject.toml                      # Modern Python packaging (PEP 621)
├── README.md
├── ARCHITECTURE.md
├── ADR-001-GitLab-GraphQL-Client.md
└── LICENSE
```

## Build System

- **Backend**: `hatchling.build` (chosen over `setuptools` for superior PEP 420 implicit namespace support (`xgic.*`), cleaner defaults, and better `uv` integration).
- **Recommended workflow tool**: `uv` (https://github.com/astral-sh/uv) for creating environments, installing dependencies, building, and publishing.
- **Rationale**: See the dedicated evaluation in ADR-001. This choice aligns with XGIC's principle of selecting optimal modern tooling for every component.
- **Local development**: `uv venv && uv pip install -e ".[dev]"` or simply `pip install -e ".[dev]"` if preferred.

## Module Responsibilities

### `client.py` — The Public Face
- Contains the `GitLabClient` class.
- Exposes only high-level, intent-revealing methods:
  - `create_issue(...)`
  - `create_task(parent_id, ...)`
  - `create_issue_with_tasks(issue_title, tasks=[...])` ← **highly recommended for Grok Build**
  - `create_merge_request(...)`
  - Future: `update_work_item(...)`, `get_work_item(...)`, bulk operations, etc.
- All GraphQL execution funnels through a private `_execute(query, variables)` method.
- Handles authentication header injection, timeout, basic retry logic, and error translation.
- Returns rich model objects (`Issue`, `Task`, etc.), never raw dicts.

### `config.py`
- Simple dataclass or Pydantic model (Phase 1 can stay lightweight).
- Holds base URL, token, timeout, and any future connection settings.
- Central place for environment variable fallbacks (e.g., `GITLAB_TOKEN`, `GITLAB_URL`).

### `models.py`
- Uses `@dataclass` for clean, immutable-friendly data containers (Pydantic where applicable in future).
- `BaseWorkItem` as common base for Issue / Task (DRY).
- Each model has a `from_graphql(cls, data: dict)` classmethod.
- Added for full support.
- Easy to extend later with new fields (estimates, actuals, custom widgets, hierarchy info).
- Provides `web_url`, human-readable `iid`, global `id`, etc.

### `exceptions.py`
- `GitLabError` — base for all client errors.
- `GraphQLError` — wraps GraphQL `errors` array with helpful messages.
- `AuthenticationError`, `RateLimitError`, `ValidationError` as needed.
- Keeps error handling consistent and actionable.

### `graphql/operations.py` (and `queries.py`)
- **Never** put raw GraphQL strings in `client.py`.
- All mutation strings live here (or in small helper functions that return the string + variables).
- Keeps the client clean and makes it easy to evolve or version queries.
- Thin wrapper functions can assemble the final payload if needed.

### `utils/validators.py`
- Optional in early phases.
- Central place for title length checks, label validation, ID format validation, etc.
- Prevents bad data from reaching GitLab.

## Key Design Patterns & Decisions

- **Centralized execution** (`_execute`): Single place for HTTP, auth, error checking, logging, and future retry / circuit-breaker logic.
- **Factory methods on models** (`from_graphql`): All GraphQL → Python object mapping lives with the model. Easy to test and evolve.
- **High-level convenience methods**: `create_issue_with_tasks()` orchestrates the creation of a parent + multiple children in one logical call. This is the method Grok Build should prefer.
- **No CLI layer**: Deliberately avoided. The package is a library, not a command-line tool.
- **MCP readiness**: Once the client is solid, an MCP server can be added as a thin wrapper that exposes the same public methods via the Model Context Protocol. No changes needed to core logic.
- **Strong typing throughout**: Full use of `typing`, dataclasses, and clear return types. Aligns with modern Python best practices and makes Grok Build’s code generation safer.
- **Error transparency**: GraphQL errors are turned into clear Python exceptions instead of being swallowed or returned as dicts.

## How Grok Build Interacts With This Architecture

Grok Build does **not** shell out to a CLI. Instead:

1. It runs `pip install -e .` (or equivalent) inside its environment.
2. It imports the package: `from xgic.gitlab.graphql import GitLabClient`
3. It instantiates the client with a securely provided token.
4. It calls high-level methods directly in generated Python code.

This completely bypasses shell escaping issues and gives Grok Build proper Python objects and error handling.

Example instruction you can give Grok Build:
> “Install the xgic-gitlab-graphql package, then use GitLabClient from xgic.gitlab.graphql to create a new feature issue titled ‘X’ with these three child tasks: … Use the create_issue_with_tasks method.”

## Future Extensibility Points

- Add new high-level methods without touching `_execute`.
- Extend models with new fields (estimates, actuals, progress, custom widgets).
- Add async client variant (`AsyncGitLabClient`) sharing most logic.
- Add MCP server package that imports and exposes the same client methods.
- Add query helpers and reporting capabilities once write operations are solid.

## Testing Strategy (High Level)

- Unit tests for models (`from_graphql` mapping).
- Unit tests for `_execute` error paths and happy paths (mocked responses).
- Integration tests (optional, against a test GitLab instance or GitLab.com sandbox) for the most critical flows: `create_issue_with_tasks`.
- Cross-platform checks on Windows + Linux.

## Phase 1 Delivered

- Auth + centralized _execute
- Work Items hierarchy (create + parse)
- Cursor pagination (Relay/pageInfo)
- Basic queries (list, current user)
- Full base standards and package setup per public exemplary rules

## Non-Goals (Phase 1)

- Full GraphQL coverage
- Async support
- MCP server implementation
- Rich reporting / analytics
- GUI or CLI wrapper (the package is intentionally a library)

These are explicitly deferred so we can deliver a rock-solid core quickly.

---

This architecture keeps the package simple enough to implement incrementally while being robust enough to support years of growth and Grok Build automation.
