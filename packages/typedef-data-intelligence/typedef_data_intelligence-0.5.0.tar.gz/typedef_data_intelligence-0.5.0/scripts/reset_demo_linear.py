# see https://pypi.org/project/linear-api/
import os
from datetime import datetime
from textwrap import dedent

from linear_api import LinearClient, LinearIssueInput


def main():
    # by default, work as analyst agent user to prepopulate issues
    linear_analyst_api_key=os.getenv("LINEAR_ANALYST_API_KEY")
    linear_data_engineer_api_key=os.getenv("LINEAR_DATA_ENGINEER_API_KEY")

    linear_team_id=os.getenv("LINEAR_TEAM_ID")
    if (not linear_analyst_api_key and not linear_data_engineer_api_key) or not linear_team_id:
        print("No Linear API key or team ID found in environment variables.  Exiting.")
        return

    if linear_team_id != "2832d96a-37f9-427e-86df-8fcc6e5054f0":
        print("Warning: only resetting demo issues for DE Demo linear team.  Change your LINEAR_TEAM_ID variable.  Exiting.")
        return

    if linear_analyst_api_key:
        client = LinearClient(api_key=linear_analyst_api_key)
    else:
        client = LinearClient(api_key=linear_data_engineer_api_key)

    team = client.teams.get(linear_team_id)


    issue_ids = client.issues.get_by_team(team_name=team.name)

    de_user_id = client.users.get_id_by_name("data-engineer-agent")
    #analayst_user_id = client.users.get_id_by_name("analyst-agent")


    for issue_id in issue_ids:
        print("-"*70)
        #print(f"Deleting issue: {issue.name}")
        get_issue = client.issues.get(issue_id)
        print(f"Deleting issue: {get_issue.title}")
        client.issues.delete(issue_id)
        print("-"*70)

    # Seed with demo tickets for data engineer agent to work on
    create_issue_data = [

        LinearIssueInput(
                title="URGENT: ARR Data Pipeline - Zero Values Since October 2025",
                description=dedent(f"""## Alert: Data Ingestion Pipeline Failure

Detection Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Impact: ARR metrics reporting broken for recent timeperiods

## Problem

ARR reporting shows $0 values for all months from October 2025 onward:
  - Sept 2025: $274,096.50 ✓ (Last valid data point)
  - Oct 2025 - Feb 2026: $0.00 ✗ (Invalid)

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
                teamName=team.name,
                labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"]
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
                teamName=team.name,
                labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"]
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
                teamName=team.name,
                labelIds=["a1674aa9-e5f6-4c0a-a067-1372cc61a18d"]
            ),
    ]


    for new_issue_data in create_issue_data:
        create_issue = client.issues.create(new_issue_data)
        print(f"Created issue: {create_issue.title} assigned to {de_user_id}")

if __name__ == "__main__":
    main()
