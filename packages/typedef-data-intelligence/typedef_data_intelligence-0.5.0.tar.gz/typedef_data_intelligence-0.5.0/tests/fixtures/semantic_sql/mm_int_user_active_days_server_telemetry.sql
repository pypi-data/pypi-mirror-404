with tmp as (
    select
        cast(received_at as date) as received_at_date,
        cast(mtp.timestamp as date) as activity_date,
        server_id,
        user_id,
        case when lower(to_varchar(ua.user_agent:browser_family)) = 'electron' then 'IS_DESKTOP' 
        when lower(to_varchar(ua.user_agent:browser_family)) != 'electron' and ua.user_agent:browser_family is not null then 'IS_WEBAPP' end as client_type
        from 
        "ANALYTICS_BRANDON".dbt_staging.stg_mm_telemetry_prod__tracks mtp 
    left join "ANALYTICS_BRANDON".int_product.int_user_agents ua
        on mtp.context_user_agent = ua.context_user_agent
    where
        -- Exclude items without user ids, such as server side telemetry etc
        user_id is not null
        -- Exclude items without server ids
        and server_id is not null
        -- Exclude items with missing timestamps
        and mtp.timestamp is not null
        and received_at <= current_timestamp

        -- this filter will only be applied on an incremental run
        and received_at >= (select max(received_at_date) from "ANALYTICS_BRANDON".int_product.int_user_active_days_server_telemetry)

    group by received_at_date, activity_date, server_id, user_id, client_type
    order by received_at_date
)
select
    -- Surrogate key required as it's both a good practice, as well as allows merge incremental strategy.
    md5(cast(coalesce(cast(activity_date as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(server_id as TEXT), '_dbt_utils_surrogate_key_null_') || '-' || coalesce(cast(user_id as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as daily_user_id
    , activity_date
    , server_id
    , user_id
    , true as is_active
    -- Required for incremental loading
    -- Use max to ensure that the most recent received_at_date is used
    , max(received_at_date) as received_at_date
    , 
  
    sum(
      
      case
      when client_type = 'IS_DESKTOP'
        then 1
      else 0
      end
    )
    
      
            as "IS_DESKTOP"
      
    
    ,
  
    sum(
      
      case
      when client_type = 'IS_WEBAPP'
        then 1
      else 0
      end
    )
    
      
            as "IS_WEBAPP"
      
    
    
  

    from tmp
where
    activity_date >= '2018-01-01'
group by 
    activity_date, server_id, user_id


