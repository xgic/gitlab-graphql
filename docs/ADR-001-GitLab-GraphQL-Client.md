# ADR-001: Building a Reusable Python Client for GitLab GraphQL API

**Status:** Proposed  
**Date:** 2026-06-27  
**Deciders:** Development Team / Grok Build Automation Initiative  

## Context

Current GitLab work tracking relies heavily on the GitLab CLI (`glab`) for creating Issues, Merge Requests, and related entities. This approach frequently encounters reliability issues:

- Shell escaping problems with long descriptions, complex Markdown, and structured content.
- Accidental overwriting or corruption of issue descriptions during automation (e.g., Grok Build previously replaced entire descriptions with single characters across multiple merge requests).
- Use of Markdown checklists inside large description fields, which lack proper hierarchy, individual status tracking, traceability, and queryability.
- Difficulty generating reports or automating updates on sub-items.
- Limited support for structured data such as time estimates, actuals, and custom fields.

GitLab is evolving toward a unified **Work Items** model. In this model, **Tasks** are first-class child work items that can be linked to parent Issues (or other work items) via hierarchy widgets. This provides real parent-child relationships, individual assignees, status, and better structure than Markdown checklists.

The GraphQL API is the most capable and future-proof interface for creating and managing these hierarchical Work Items, complex relationships, and rich metadata. The REST API and CLI have limitations in this area.

The objective is to enable reliable, high-level automation (especially via Grok Build) for:
- Creating Issues (and other work item types)
- Creating Tasks as proper child items under Issues
- Managing Merge Requests, Labels, Milestones, and Releases
- Eventually supporting structured fields (estimates, actuals, status) instead of free-text Markdown

The solution must be:
- Reusable across projects and environments
- Installable via standard Python tooling (`pip`)
- Cross-platform (Windows + Linux)
- Easy for Grok Build to consume without shell escaping issues
- Designed for incremental growth toward full GraphQL coverage

## Decision

We will build the **XGIC GitLab GraphQL Client** — a lightweight, object-oriented Python package distributed as `xgic-gitlab-graphql` (Python import namespace: `xgic.gitlab.graphql`). It provides a clean, high-level abstraction over GitLab’s GraphQL API following the XGIC Python Namespace Convention.

**Core Principles:**
- **Python-first integration** — Primary interface is a Python library (not a CLI tool). This eliminates shell escaping problems and plays to Grok Build’s strongest integration capability (importing and using Python packages directly).
- **GraphQL as the primary backend** — All complex operations (especially Work Item hierarchy) go through GitLab’s GraphQL API.
- **Clean abstraction layer** — High-level methods (`create_issue()`, `create_task()`, `create_issue_with_tasks()`) hide GraphQL complexity, query construction, and response mapping.
- **Incremental & extensible design** — Start narrow (Phase 1 scope below) but architected from day one to eventually support the full range of GitLab GraphQL queries and mutations.
- **MCP as future extension, not starting point** — The core Python client will be built first and made solid. An MCP server wrapper can be added later as a thin, natural extension once the client is reliable. This avoids early complexity and benefits from potential maturation of the MCP protocol.
- **Professional engineering standards** — Follow clean architecture, separation of concerns, strong typing, comprehensive error handling, and maintainability practices suitable for long-term use with AI agents like Grok Build.

**Initial Scope (Phase 1)**
- Issues / Work Items (various types)
- Tasks as proper child work items with parent-child hierarchy
- Merge Requests
- Labels, Milestones, Releases (basic support)
- Core client infrastructure (auth, config, error handling, models)

**Future Scope (Phased)**
- Structured time tracking (estimates + actuals on work items)
- Custom fields and additional widgets
- Full GraphQL API coverage over time
- MCP server wrapper for deeper AI agent integration
- Querying, reporting, and bulk operations
- Async client variant if needed

## Considered Alternatives

We conducted a thorough evaluation of available options in June 2026 before selecting the approach documented in this ADR. The evaluation included analysis of official documentation, repository activity, release history, and practical testing of GraphQL capabilities.

### 1. Continue using or extending the GitLab CLI (`glab`)

**Description:** Rely primarily on the official GitLab CLI (`glab issue create`, `glab mr create`, etc.) called from shell scripts or directly by Grok Build.

**Evaluation:**
- **Advantages:** Simple for basic CRUD operations, officially supported, zero additional runtime dependencies.
- **Disadvantages:** 
  - Severe shell escaping problems with long descriptions, complex Markdown, and structured content (directly observed when Grok Build corrupted multiple merge request descriptions by replacing them with single characters).
  - No robust native support for creating Tasks as proper child work items with hierarchy widgets.
  - Fragile error handling and output parsing in automated scenarios.
  - Poor fit for the long-term goal of moving data into structured fields rather than free-text Markdown.
- **Conclusion:** Rejected due to fundamental reliability and capability limitations for the target use cases.

### 2. Use the official `python-gitlab` library (including its GraphQL support)

**Description:** Adopt the community-maintained official Python client for GitLab (`https://github.com/python-gitlab/python-gitlab`). As of version 8.4.0 (released May 28, 2026), this library added experimental GraphQL support.

**Evaluation:**
- **Advantages:** Officially supported, actively maintained, provides both REST and (experimental) GraphQL interfaces, good authentication and basic project management features.
- **Disadvantages:**
  - GraphQL support is explicitly marked as **experimental/beta** in v8.x.
  - Lacks pagination, built-in rate-limit handling, and robust retry logic for GraphQL.
  - No high-level domain models or convenience methods for Work Item hierarchy (parent-child Tasks via hierarchy widgets).
  - Still primarily oriented around the older Issues/Merge Requests REST model rather than the evolving unified Work Items model.
- **Conclusion:** Rejected for Phase 1. The library is excellent for general GitLab automation but does not yet provide the opinionated, high-level Work Items abstraction layer required for reliable hierarchical task creation and structured data goals.

### 3. Build System and Package Management Tooling (setuptools vs hatchling + uv)

**Description:** Choice of Python build backend (`setuptools.build_meta` vs `hatchling.build`) and package manager/workflow tool (`pip` vs `uv` from Astral).

**Evaluation:**
- `setuptools` remains the most widely used backend due to legacy projects and heavy customization needs (C extensions, complex package data). It works well but carries more configuration overhead for modern pure-Python libraries and implicit namespace packages (`xgic.*`).
- `hatchling` (from the Hatch project) offers cleaner defaults, superior native support for PEP 420 implicit namespace packages, faster builds, and better integration with modern workflows.
- `uv` (https://github.com/astral-sh/uv) is a high-performance Python package manager and resolver written in Rust. It excels at speed, lockfile handling, and reproducible environments. It has excellent support for both backends but pairs particularly smoothly with `hatchling` for new libraries.
- For the XGIC GitLab GraphQL Client (a new pure-Python library under the shared `xgic.*` namespace), `hatchling` + `uv` provides the best combination of simplicity, performance, future extensibility, and alignment with 2026 best practices for library development.

**Conclusion:** Selected `hatchling.build` as the build backend and recommend `uv` for development workflows, virtual environments, and publishing. This decision demonstrates XGIC's commitment to selecting optimal, modern tooling for every component. The `pyproject.toml` is configured accordingly.

**Current State of `python-gitlab` GraphQL Support (as of June 2026):**
- Provides `gitlab.GraphQL()` (synchronous) and `gitlab.AsyncGraphQL()` (asynchronous) classes.
- Exposes a simple `.execute(query: str, variables: dict = None)` method that performs a POST to the `/api/graphql` endpoint.
- Supports basic authentication via the existing session/token handling.

**Limitations of the GraphQL implementation (explicitly documented and verified):**
- No built-in support for pagination (cursors, `pageInfo`, etc.).
- No automatic rate-limit detection, backoff, or retry logic.
- No sophisticated error handling or partial response processing.
- Marked as **experimental / beta** and subject to breaking changes.
- Intended primarily for simple queries and mutations. Complex operations — especially those involving Work Item hierarchy widgets, parent-child relationships for Tasks, or rich metadata — require fully manual GraphQL query construction and response parsing.
- Lacks high-level domain abstractions: there are no built-in `Issue`, `Task`, or `WorkItem` model classes that understand hierarchy, task completion status, or structured fields.
- Does not provide convenience methods such as `create_task_as_child_of_issue()` or `create_issue_with_tasks()`.

**Conclusion:** While `python-gitlab` is an excellent, actively maintained library for REST operations and can serve as a low-level transport layer in the future, its current GraphQL support is too thin and low-level to serve as the foundation for the reliable, high-level automation layer we require. Rejected as the primary solution.

### 6. Data Modeling and Validation Approach (dataclasses + Factory Method vs Pydantic / msgspec)

**Description:** Choice of library/technology for defining domain models (`BaseWorkItem`, `Issue`, `Task`, etc.) and performing GraphQL response mapping / validation, particularly the custom hierarchy widget parsing required for parent-child Task relationships.

**Evaluation:**
- **Current approach (frozen dataclasses + explicit `from_graphql()` factory methods):** Zero additional runtime dependencies beyond the single `requests` library. Provides full, explicit control over custom parsing logic — especially the non-trivial extraction of `parent.id` from the `widgets` array returned by GitLab’s Work Item hierarchy widget. Excellent runtime performance, high readability, and strong IDE support via `dataclasses` and `typing`.
- **Pydantic v2 (`https://github.com/pydantic/pydantic`):** Powerful for complex nested validation, automatic type coercion, and JSON Schema / OpenAPI generation. However, it introduces a significant dependency (`pydantic` + `pydantic-core`), adds measurable runtime validation overhead, and would still require custom `model_validator` or `field_validator` logic for GitLab’s specific hierarchy widget structure. It increases installation size and contradicts the project’s “lightweight, minimal-dependency” philosophy for a client intended for broad use by Grok Build, scripts, and CI environments.
- **msgspec (`https://github.com/msgspec/msgspec`):** A high-performance, lightweight alternative that supports dataclasses/structs with optional validation. It was evaluated as a potential middle-ground upgrade path but deemed unnecessary for Phase 1, where GraphQL responses are relatively flat and the custom hierarchy parsing is better expressed explicitly for clarity and maintainability.
- **Conclusion:** Selected the existing `dataclasses` + Factory Method pattern. It delivers the optimal balance of minimal dependencies, explicit control over domain-specific parsing (hierarchy widgets), performance, and long-term maintainability. `msgspec` is noted as a future lightweight enhancement option should stronger validation or serialization performance become priorities without adopting the heavier Pydantic ecosystem.

### 3. Build a dedicated MCP server from the start

**Description:** Implement a Model Context Protocol (MCP) server that exposes GitLab operations directly to AI agents (Grok Build, Claude, Cursor, etc.).

**Evaluation:**
- **Advantages:** Native discoverability and invocation by modern AI coding agents; aligns with emerging AI tooling standards.
- **Disadvantages:**
  - Significantly higher upfront complexity (MCP protocol implementation, tool schema definition, context window impact).
  - MCP itself is still relatively new (introduced late 2024) and its long-term stability, best practices, and ecosystem support are not yet mature.
  - Risk of over-engineering: substantial effort would be spent on protocol concerns before validating that the core business logic (Issue + child Task creation) works reliably.
  - Debugging becomes harder because failures can occur in either the business logic or the MCP transport layer.
- **Conclusion:** Rejected for the initial phase. A far lower-risk path is to build a solid Python client first and later expose it via a thin MCP wrapper if the protocol matures and proves valuable.

### 4. Use a generic GraphQL client (e.g. `gql` from graphql-python) plus custom GitLab logic

**Description:** Leverage a mature, actively maintained generic Python GraphQL client library and write all GitLab-specific queries, mutations, models, and convenience methods on top of it.

**Evaluation:**
- **Advantages:** High-quality, well-tested transport layer with good typing and async support.
- **Disadvantages:** Still requires implementing nearly everything else we need (Work Item hierarchy handling, models with `from_graphql` factories, error taxonomy, configuration, the high-level `create_issue_with_tasks()` orchestration, etc.). This duplicates a large portion of the work a dedicated client would perform.
- **Conclusion:** Viable as a potential underlying transport in a future iteration, but not a complete solution on its own. Rejected as the starting point.

### 5. Build a purpose-built, high-level Python client library (Chosen)

**Description:** Create the **XGIC GitLab GraphQL Client** (distribution name `xgic-gitlab-graphql`, import namespace `xgic.gitlab.graphql`) — a focused, object-oriented Python package that provides a clean abstraction layer specifically tailored to GitLab Work Items, Tasks with hierarchy, Merge Requests, and future structured fields — using GraphQL under the hood and following the official XGIC namespace convention.

**Evaluation:**
- Directly addresses all observed pain points: eliminates shell escaping, provides proper parent-child Task support, enables structured data, and offers a simple API that Grok Build can import and use reliably.
- Full control over architecture, models, error handling, and extensibility.
- The core client can later serve as the foundation for an MCP server (thin wrapper) without architectural conflict.
- Aligns with professional engineering standards and the long-term vision of moving away from Markdown-heavy descriptions toward queryable, structured work data.
- **Conclusion:** Selected as the best balance of immediate value, long-term maintainability, and future flexibility.

**Summary of Evaluation:** After reviewing the official `python-gitlab` library documentation, release notes, source code, and conducting practical tests of its GraphQL capabilities in June 2026, no existing solution provided the combination of high-level Work Item abstractions, reliable hierarchy support, and Grok Build-friendly Python API that this project requires. Building a dedicated client is therefore the justified path.

## Rationale

- Python is Grok Build’s primary and most reliable integration mechanism. It can install packages and import classes directly — far more robust than shelling out to CLIs.
- A well-designed client removes the escaping and fragility problems observed with `glab`.
- Starting with the core client delivers immediate value for the most painful use cases (Issues + child Tasks) while keeping the door open for MCP.
- Designing for extensibility now prevents painful refactoring later when we add estimates, actuals, and full API coverage.
- Aligns with professional software engineering practices: clean architecture, strong typing, separation of concerns, and incremental delivery.
- Data modeling uses lightweight `dataclasses` + explicit Factory Methods rather than heavier validation libraries (Pydantic) or even lighter alternatives (msgspec) at this stage. This choice prioritizes minimal dependencies, explicit control over GitLab-specific hierarchy widget parsing, and runtime performance — consistent with the project’s lightweight, Grok Build-friendly philosophy.

## Consequences

**Positive:**
- Dramatically more reliable automation than CLI-based approach (no shell escaping).
- Clean, reusable, strongly-typed API that both humans and Grok Build can use comfortably.
- Proper hierarchical Tasks instead of fragile Markdown checklists → better traceability, status tracking, and reporting.
- Strong foundation for moving work data into structured fields (estimates, actuals, etc.).
- Low-risk path to adding MCP support later.
- Cross-project reusability and easy installation via `pip`.
- Reduced risk of data corruption during automation.

**Negative / Risks & Mitigations:**
- Initial development effort to build quality client infrastructure (mitigated by incremental delivery and clear architecture).
- Need to maintain GraphQL queries/mutations as GitLab evolves the Work Items model (mitigated by centralizing queries in one module and versioning where possible).
- GraphQL has some experimental/ evolving areas for Work Items (mitigated by starting with well-supported operations and adding guards).
- Token management and authentication security (mitigated by clear config handling, environment variables, and least-privilege guidance in docs).

## Next Steps

1. Finalize package structure and module responsibilities (see ARCHITECTURE.md).
2. Implement core `GitLabClient` class with `_execute()` central method and high-level public API (`create_issue`, `create_task`, `create_issue_with_tasks`, `create_merge_request`).
3. Define data models (`Issue`, `Task`, `MergeRequest`, etc.) using dataclasses and `from_graphql` factory methods.
4. Implement configuration, authentication, and custom exception hierarchy.
5. Add basic tests for cross-platform compatibility and error paths.
6. Create usage documentation and Grok Build integration guide.
7. Iterate on Phase 1 implementation until `create_issue_with_tasks` works reliably end-to-end.
8. Revisit this ADR after Phase 1 to confirm direction for MCP and structured fields.

This ADR will be updated as implementation reveals new constraints or opportunities.

---

**Related Documents**
- `README.md` – Project overview and quick start
- `ARCHITECTURE.md` – Detailed package structure and design decisions
- `docs/GROK_BUILD_INTEGRATION.md` – How Grok Build consumes the client
