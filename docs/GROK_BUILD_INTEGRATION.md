# Grok Build Integration Guide — XGIC GitLab GraphQL Client

This document explains exactly how Grok Build should interact with the **XGIC GitLab GraphQL Client** (`xgic-gitlab-graphql`, import namespace `xgic.gitlab.graphql`) and why this approach is dramatically more reliable than using the GitLab CLI.

## Core Principle

**Grok Build should treat the XGIC GitLab GraphQL Client (`xgic-gitlab-graphql`) as a normal Python library it installs and imports — not as a CLI tool it shells out to.**

This single decision eliminates the escaping, quoting, and fragility problems that appear when Grok Build tries to build long `glab issue create ...` or `glab work-items create ...` commands containing large descriptions or complex data.

## How Grok Build Uses the Client (Recommended Flow)

### 1. Installation (one-time per environment)

Grok Build runs:

```bash
pip install -e /path/to/gitlab-graphql
# or once published:
# pip install xgic-gitlab-graphql
```

### 2. Import and Instantiation

In any Python code it generates or runs:

```python
from xgic.gitlab.graphql import GitLabClient

client = GitLabClient(
    token="glpat-XXXXXXXXXXXXXXXXXXXX",   # securely provided (env var or config)
    url="https://gitlab.com"              # or your self-hosted GitLab
)
```

### 3. Preferred High-Level Methods

Grok Build should prefer these methods (they hide all GraphQL complexity):

```python
# Best for most automation scenarios
result = client.create_issue_with_tasks(
    issue_title="Implement user authentication refactor",
    issue_description="""High-level description of the feature.
Can contain multiple paragraphs.""",
    tasks=[
        {"title": "Design new auth flow", "description": "Details..."},
        {"title": "Implement backend changes", "description": "Details..."},
        {"title": "Update frontend and tests", "description": "Details..."},
    ],
    labels=["refactor", "security", "backend"]
)

# Or step-by-step when more control is needed
issue = client.create_issue(title=..., description=..., labels=...)
task = client.create_task(parent_id=issue.id, title=..., description=...)
```

### 4. Error Handling

Grok Build should catch the client’s exceptions:

```python
from xgic.gitlab.graphql.exceptions import GitLabError, GraphQLError

try:
    issue = client.create_issue(...)
except GraphQLError as e:
    print(f"GitLab rejected the request: {e}")
except GitLabError as e:
    print(f"Unexpected GitLab communication error: {e}")
```

## Why This Is Much Better Than CLI Usage

| Aspect                    | GitLab CLI (`glab`)                          | XGIC GitLab GraphQL Client (`xgic-gitlab-graphql`) |
|---------------------------|----------------------------------------------|-------------------------------------------------|
| Long descriptions         | Requires heavy shell escaping                | Passed as normal Python strings                 |
| Complex / nested data     | Very fragile                                 | Native Python objects and lists                 |
| Hierarchical Tasks        | Limited / awkward                            | First-class via `create_task(parent_id=...)`    |
| Error handling            | Parse text output                            | Proper Python exceptions with clear messages    |
| Grok Build reliability    | Frequent escaping / quoting bugs             | Direct function calls — extremely reliable      |
| Structured fields later   | Hard (text in description)                   | Easy (add fields to models and methods)         |
| Reusability               | Script-by-script                             | Single shared package across all projects       |

## Example Prompts You Can Give Grok Build

**Good prompt:**
> “We now have the XGIC GitLab GraphQL Client (`xgic-gitlab-graphql`). First make sure it is installed with `pip install -e .`. Then use `GitLabClient` from `xgic.gitlab.graphql` to create a new Issue titled ‘Add audit logging’ with four child Tasks. Use the `create_issue_with_tasks` method. Put the issue in the backend project and label it ‘audit’ and ‘security’.”

**Bad prompt (avoid):**
> “Use `glab issue create` and then `glab work-items create` with lots of flags and escaped JSON…”

## Token & Authentication Guidance for Grok Build

- Never hard-code tokens in prompts or generated code.
- Instruct Grok Build to read the token from an environment variable (`os.environ.get("GITLAB_TOKEN")`) or a secure config file.
- Use a token with the minimum required scopes (`api` or `read_api` + `write_repository` as needed).
- Document the required scopes clearly in the package README.

## Future: MCP Wrapper (Planned)

Once the core `GitLabClient` is solid and widely used, we may add an MCP server that exposes the same high-level methods through the Model Context Protocol. 

At that point Grok Build could discover the available operations automatically. Until then, the Python import approach above remains the recommended and most reliable integration method.

## Summary for New Grok Build Sessions

1. Point Grok Build at this repository (or the installed package).
2. Tell it to read `README.md`, `ARCHITECTURE.md`, and this file.
3. Instruct it to **install the package** (`xgic-gitlab-graphql`) and then **import and use `GitLabClient` from `xgic.gitlab.graphql`** — never fall back to raw `glab` or `curl` for complex operations.
4. Prefer `create_issue_with_tasks(...)` for any work that involves an issue plus multiple child tasks.

This pattern gives us reliable, maintainable, and future-proof GitLab automation.
