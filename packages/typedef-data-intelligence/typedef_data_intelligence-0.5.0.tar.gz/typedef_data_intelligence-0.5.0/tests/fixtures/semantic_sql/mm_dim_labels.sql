select
     issue_id,
     value::string as label
from
    "ANALYTICS_BRANDON".dbt_staging.stg_mattermost_jira__issues,
    lateral FLATTEN(INPUT => labels)


