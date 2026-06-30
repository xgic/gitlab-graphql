#!/usr/bin/env python3
"""
XGIC GitLab GraphQL Client - Example Usage
==========================================

File: examples/create_feature_with_tasks.py

This short script demonstrates the **recommended Grok Build-friendly pattern**
for creating a parent Issue with multiple child Tasks using the high-level
`create_issue_with_tasks()` method.

Why this pattern is preferred for Grok Build and automation:
- Uses the Python client (no fragile shell escaping with long descriptions)
- Creates proper hierarchical Work Items (Tasks) instead of Markdown checklists
- Returns clean, structured objects with web URLs and status
- Easy to call from natural language instructions in Grok Build
- Resilient partial-failure handling built in

See also:
- docs/ADR-001-GitLab-GraphQL-Client.md
- XGIC_GROK_BUILD_QUICK_START.md
- docs/DOMAIN_MODELS_AND_HIERARCHY_PARSING.md
"""

import os
from typing import Any, Dict

from xgic.gitlab.graphql import GitLabClient
from xgic.gitlab.graphql.exceptions import GitLabError, WorkItemCreationError


def main() -> None:
    """Demonstrate creating a feature issue with structured child tasks."""

    # Best practice: Load token from environment (never hard-code)
    token = os.getenv("GITLAB_TOKEN")
    if not token:
        raise ValueError(
            "GITLAB_TOKEN environment variable is required.\n"
            "Export it before running: export GITLAB_TOKEN=glpat-xxxxxxxxxxxx"
        )

    # Initialize client (works with gitlab.com or self-hosted)
    client = GitLabClient(
        token=token,
        url="https://gitlab.com",           # Change to your GitLab instance if needed
        timeout=30,
    )

    print("🚀 Creating feature with structured child tasks via GraphQL...\n")

    # High-level call — the core Grok Build-friendly primitive
    result: Dict[str, Any] = client.create_issue_with_tasks(
        issue_title="Implement User Authentication with OAuth2 + SSO",
        issue_description=(
            "As a user, I want to authenticate using corporate SSO (OAuth2) "
            "so that I don't need to manage another set of credentials.\n\n"
            "This replaces the legacy username/password flow and improves our "
            "overall security posture and compliance."
        ),
        tasks=[
            {
                "title": "Design OAuth2 integration and select provider",
                "description": "Research providers, document chosen flow, and create architecture diagram.",
            },
            {
                "title": "Implement backend authorization code exchange endpoint",
                "description": "Create secure /auth/callback endpoint with proper token validation and session handling.",
            },
            {
                "title": "Update frontend login UI and callback handler",
                "description": "Add 'Login with Corporate SSO' button and handle the OAuth redirect + token storage.",
            },
        ],
        labels=["feature", "security", "oauth2", "sso"],
    )

    # Process structured result (much cleaner than parsing CLI output)
    issue = result["issue"]
    tasks = result["tasks"]
    failed = result.get("failed_tasks", [])

    print("✅ Success! Feature created with proper hierarchy.\n")
    print(f"   Parent Issue: {issue.title}")
    print(f"   Web URL:      {issue.web_url}")
    print(f"   Tasks created: {len(tasks)} / {len(tasks) + len(failed)}")

    for task in tasks:
        print(f"     • {task.title}")
        print(f"       {task.web_url}")

    if failed:
        print(f"\n⚠️  Partial failure: {len(failed)} task(s) could not be created.")
        for item in failed:
            print(f"     - {item['title']}: {item.get('error', 'Unknown error')}")

    print("\n💡 This structured approach gives us traceability, reporting, and")
    print("   easy status tracking — far better than long Markdown checklists.")


if __name__ == "__main__":
    try:
        main()
    except (GitLabError, WorkItemCreationError, ValueError) as exc:
        print(f"\n❌ Error: {exc}")
        raise
