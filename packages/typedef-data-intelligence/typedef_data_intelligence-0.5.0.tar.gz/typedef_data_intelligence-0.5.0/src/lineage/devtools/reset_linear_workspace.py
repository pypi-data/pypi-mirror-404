#!/usr/bin/env python3
"""Reset Linear workspace - delete existing issues and seed demo tickets.

Usage:
    python reset_linear_workspace.py --team-id <team_id>
    python reset_linear_workspace.py  # Uses LINEAR_TEAM_ID from environment
"""
import argparse
import os
import sys
from datetime import datetime
from textwrap import dedent
from typing import Optional


def get_demo_issues(team_name: str) -> list:
    """Get the list of demo issues to create."""
    from linear_api import LinearIssueInput

    return [
        LinearIssueInput(
            title="URGENT: ARR Data Pipeline - Zero Values Since October 2025",
            description=dedent(f"""## Alert: Data Ingestion Pipeline Failure

Detection Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Impact: ARR metrics reporting broken for recent timeperiods

## Problem

ARR reporting shows $0 values for all months from October 2025 onward:
  - Sept 2025: $274,096.50 (Last valid data point)
  - Oct 2025 - Feb 2026: $0.00 (Invalid)

## Root Cause Investigation Needed
This pattern indicates a complete upstream ingestion failure rather than legitimate business data. Possible causes:
- ETL/data pipeline failure or interruption
- Source system disconnection (Salesforce, billing system, etc.)
- Database table truncation or schema change
- Missing transformation logic in dbt models
- Credential/authentication failure in pipeline orchestration

## Immediate Actions Required
- Check pipeline logs for October 2025 onward
- Verify source system connectivity and data availability
- Validate dbt model execution for SV_ARR_REPORTING
- Confirm ARR_FACTS table population status
- identify if root failure if this is indeed an actual failure
- Describe and trace through the lineage of the ARR calculation chain

## Data Location

Schema: marts
View: SV_ARR_REPORTING
Table: ARR_FACTS
Measure: ENDING_ARR
"""),
            priority=1,
            stateName="Todo",
            teamName=team_name,
            labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"],
        ),
        LinearIssueInput(
            title="CRITICAL: dbt Test Failures - dim_server_info Uniqueness Violations",
            description=dedent(f"""## Alert: Data Quality Test Failures Detected

Detection Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Severity: CRITICAL - Models run successfully but produce incorrect data

## Failed dbt Tests

```
unique_dim_server_info_server_id                    FAIL 48
dbt_utils_unique_combination_of_columns_...         FAIL 48
unique_dim_server_info_installation_id              FAIL 9
```

## Required Actions

Investigate the failed tests and identify the root cause. Fix the issue and ensure tests pass.

## dbt Project

mattermost-analytics
"""),
            priority=1,
            stateName="Todo",
            teamName=team_name,
            labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"],
        ),
        LinearIssueInput(
            title="Data Issue: Executive Report Showing Sudden Spike in Server Counts",
            description=dedent(f"""## Report Issue

Reported By: Data Analyst Team
Detection Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Observed Problem

The total server count in our executive report jumped up tremendously after the last deployment. This can't be right.

## Affected Metric

**Report:** Executive Server Metrics Dashboard
**Metric:** Total Active Servers (COUNT DISTINCT server_id from dim_server_info)
**Observation:** Sudden spike in server count after recent dbt deployment

## Additional Context

This metric is pulled from the dim_server_info table in the marts schema.

## dbt Project

mattermost-analytics
"""),
            priority=2,
            stateName="Todo",
            teamName=team_name,
            labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"],
        ),
    ]


def reset_workspace(
    team_id: str,
    api_key: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Reset Linear workspace - delete existing issues and seed demo tickets.

    Args:
        team_id: Linear team ID
        api_key: Linear API key (defaults to LINEAR_ANALYST_API_KEY or LINEAR_DATA_ENGINEER_API_KEY)
        dry_run: If True, only show what would be done

    Returns:
        True if successful, False otherwise
    """
    try:
        from linear_api import LinearClient
    except ImportError:
        print("Error: linear-api not installed")
        print("Run: pip install linear-api")
        return False

    # Get API key
    if not api_key:
        api_key = os.environ.get("LINEAR_ANALYST_API_KEY") or os.environ.get(
            "LINEAR_DATA_ENGINEER_API_KEY"
        )

    if not api_key:
        print("Error: No Linear API key found")
        print("Set LINEAR_ANALYST_API_KEY or LINEAR_DATA_ENGINEER_API_KEY")
        return False

    if not team_id:
        print("Error: No team ID provided")
        return False

    print(f"Connecting to Linear (team: {team_id})")

    client = LinearClient(api_key=api_key)

    # Get team info
    try:
        team = client.teams.get(team_id)
    except Exception as e:
        print(f"Error getting team: {e}")
        return False

    print(f"Team: {team.name}")

    # Safety check: only allow reset on the demo team (use ID, not name, since names are mutable)
    if team.id != "2832d96a-37f9-427e-86df-8fcc6e5054f0":
        print(f"Error: This script only runs on the demo team (ID: 2832d96a-37f9-427e-86df-8fcc6e5054f0), not '{team.id}'")
        print("Aborting to prevent accidental data loss.")
        return False

    # Get existing issues
    try:
        issue_ids = client.issues.get_by_team(team_name=team.name)
    except Exception as e:
        print(f"Error listing issues: {e}")
        return False

    print(f"Found {len(issue_ids)} existing issues")

    if dry_run:
        print("\nDRY RUN - would perform the following:")
        print(f"  1. Delete {len(issue_ids)} existing issues")
        print("  2. Create 3 demo issues")
        return True

    # Delete existing issues
    deleted_count = 0
    for issue_id in issue_ids:
        try:
            issue = client.issues.get(issue_id)
            print(f"  Deleting: {issue.title}")
            client.issues.delete(issue_id)
            deleted_count += 1
        except Exception as e:
            print(f"  Error deleting issue {issue_id}: {e}")

    print(f"Deleted {deleted_count} issues")

    # Create demo issues
    demo_issues = get_demo_issues(team.name)
    created_count = 0
    for issue_data in demo_issues:
        try:
            created = client.issues.create(issue_data)
            print(f"  Created: {created.title}")
            created_count += 1
        except Exception as e:
            print(f"  Error creating issue: {e}")

    print(f"Created {created_count} demo issues")
    return True


def main():
    """Main function for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Reset Linear workspace - delete issues and seed demo tickets"
    )
    parser.add_argument(
        "--team-id",
        help="Linear team ID (defaults to LINEAR_TEAM_ID env var)",
    )
    parser.add_argument(
        "--api-key",
        help="Linear API key (defaults to LINEAR_*_API_KEY env vars)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )

    args = parser.parse_args()

    team_id = args.team_id or os.environ.get("LINEAR_TEAM_ID")
    if not team_id:
        print("Error: Team ID required. Use --team-id or set LINEAR_TEAM_ID")
        sys.exit(1)

    success = reset_workspace(
        team_id=team_id,
        api_key=args.api_key,
        dry_run=args.dry_run,
    )
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
