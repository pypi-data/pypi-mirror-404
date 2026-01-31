## Semantic SQL fixtures (hermetic)

These SQL files are used by pytest to validate the deterministic + targeted
semantic analysis stack without requiring any external dbt project or warehouse.

### Files

- **`simple_aggregation.sql`**: GROUP BY + aggregates + ORDER BY + LIMIT
- **`tpc_ds_style.sql`**: multi-join, time bucketing-ish columns, `BETWEEN` range
- **`fact_table.sql`**: typical fact + dimension joins with potential PII columns
- **`window_dedup.sql`**: window function + subquery scope + outer filter
- **`comma_join_where_join.sql`**: comma join with join predicate in WHERE
- **`cte_scopes.sql`**: multiple CTEs to exercise scope labels (`cte:*`) and outer SELECT
- **`sf_set_ops_intersect_except.sql`**: set operations (INTERSECT/EXCEPT)
- **`sf_pivot.sql`**: Snowflake PIVOT clause
- **`sf_qualify_window_filter.sql`**: QUALIFY with a window filter (ROW_NUMBER)
- **`sf_correlated_subquery.sql`**: correlated scalar subquery + EXISTS
- **`sf_select_star_exclude.sql`**: Snowflake `SELECT * EXCLUDE (...)`
- **`sf_select_star_no_schema.sql`**: Snowflake `SELECT *` with **no schema** (intentional; validates fallback/incompleteness behavior)
- **`sf_struct_array_usage.sql`**: ARRAY/OBJECT construction + path access + array indexing
- **`sf_nested_unnest_flatten.sql`**: nested flatten over JSON array-of-objects
- **`mm_*.sql`**: real compiled SQL vendored from Mattermost (`dialect: snowflake` in adjacent `*.meta.json`)
