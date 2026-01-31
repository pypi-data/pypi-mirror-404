"""Data exploration and semantic query tools for Pydantic agents."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import AgentDeps
from lineage.agent.pydantic.utils import push_preview_tab
from lineage.backends.data_query.protocol import (
    NativeSemanticModelQueryFragment,
    QueryResult,
    TablePreview,
    TableSchema,
)

logger = logging.getLogger(__name__)

data_exploration_toolset = FunctionToolset()
semantic_view_toolset = FunctionToolset()


def _record_query_preview(
    ctx: RunContext[AgentDeps],
    *,
    tool_name: str,
    query_name: str,
    columns: List[str],
    rows: List[List[Any]],
    sql: Optional[str] = None,
    auto_open: bool = True,
    extra_data: Optional[Dict[str, Any]] = None,
) -> None:
    """Helper to push tabular previews into agent state."""
    data: Dict[str, Any] = {
        "type": "tabular",
        "columns": columns,
        "rows": rows,
        "queryName": query_name,
    }
    if sql:
        data["sql"] = sql
    if extra_data:
        data.update(extra_data)

    push_preview_tab(
        ctx.deps.state,
        title=query_name or tool_name,
        tool_name=tool_name,
        tab_type="tabular",
        data=data,
        auto_open=auto_open,
    )


@data_exploration_toolset.tool
@safe_tool
async def list_tables(
    ctx: RunContext[AgentDeps],
    database: str,
    schema: str,
) -> List[str] | ToolError:
    """List all tables in a schema.

    Args:
        ctx: Runtime context with agent dependencies
        database: Database name
        schema: Schema name

    Returns:
        List of table names in the schema
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="No data backend configured")

    try:
        tables = await ctx.deps.data_backend.list_tables(database, schema)
        return tables
    except Exception as e:
        logger.error(f"Error listing tables: {e}")
        return ToolError(error_message=str(e))

@data_exploration_toolset.tool
@safe_tool
async def list_databases(
    ctx: RunContext[AgentDeps],
) -> List[str] | ToolError:
    """List all databases.

    Args:
        ctx: Runtime context with agent dependencies
    Returns:
        List of database names
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="No data backend configured")

    try:
        databases = await ctx.deps.data_backend.list_databases()
        return databases
    except Exception as e:
        logger.error(f"Error listing databases: {e}")
        return ToolError(error_message=str(e))

@data_exploration_toolset.tool
@safe_tool
async def list_schemas(
    ctx: RunContext[AgentDeps],
    database: str,
) -> List[str] | ToolError:
    """List all schemas in a database.

    Args:
        ctx: Runtime context with agent dependencies
        database: Database name

    Returns:
        List of schema names in the database
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="No data backend configured")

    try:
        schemas = await ctx.deps.data_backend.list_schemas(database)
        return schemas
    except Exception as e:
        logger.error(f"Error listing schemas: {e}")
        return ToolError(error_message=str(e))

@data_exploration_toolset.tool
@safe_tool
async def get_table_schema(
    ctx: RunContext[AgentDeps],
    database: str,
    schema: str,
    table: str,
) -> TableSchema | ToolError:
    """Get schema information for a table.

    Args:
        ctx: Runtime context with agent dependencies
        database: Database name
        schema: Schema name
        table: Table name
    Returns:
        TableSchema with column definitions
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="No data backend configured")

    try:
        table_schema = await ctx.deps.data_backend.get_table_schema(database, schema, table)
        return table_schema
    except Exception as e:
        logger.error(f"Error getting table schema: {e}")
        return ToolError(error_message=str(e))


@data_exploration_toolset.tool
@safe_tool
async def preview_table(
    ctx: RunContext[AgentDeps],
    database: str,
    schema: str,
    table: str,
    limit: int = 10,
) -> TablePreview | ToolError:
    """Preview table structure and sample rows.

    Args:
        ctx: Runtime context with agent dependencies
        database: Database name
        schema: Schema name
        table: Table name
        limit: Number of rows to preview (default: 10)

    Returns:
        Column schema and sample rows
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="no backend configured")

    try:
        preview = await ctx.deps.data_backend.preview_table(database, schema, table, limit)
        return preview
    except Exception as e:
        logger.error(f"Error previewing table: {e}")
        return ToolError(error_message=str(e))

# This is purposely NOT part of the data_exploration_toolset
# Only agents that specifically need to execute SQL queries should wire this tool in.
@safe_tool
async def execute_query(
    ctx: RunContext[AgentDeps],
    sql: str,
    query_name: str = "SQL Query",
    limit: Optional[int] = None,
) -> QueryResult | ToolError:
    """Execute a SQL query against the data warehouse.

    Args:
        ctx: Runtime context with agent dependencies
        sql: SQL query string
        query_name: Descriptive name for this query (e.g., "Monthly Revenue Trends")
        limit: Optional row limit (default: None, uses query's LIMIT)

    Returns:
        Query results including columns and rows
    """
    if not ctx.deps.data_backend:
        return ToolError(error_message="no backend configured")

    try:
        result = await ctx.deps.data_backend.execute_query(sql, limit)
        # result is a QueryResult dataclass with .columns, .rows attributes

        # Set query_name if provided
        result.query_name = query_name

        # Store typed result in state keyed by tool_call_id for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        display_name = result.query_name or query_name or "SQL Query"
        _record_query_preview(
            ctx,
            tool_name="execute_query",
            query_name=display_name,
            columns=result.columns,
            rows=result.rows,
            sql=sql,
        )

        return result
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return ToolError(error_message=str(e))


@semantic_view_toolset.tool
@safe_tool
async def query_semantic_view(
    ctx: RunContext[AgentDeps],
    database_name: str,
    schema_name: str,
    view_name: str,
    query_name: str,
    measures: List[NativeSemanticModelQueryFragment],
    dimensions: List[NativeSemanticModelQueryFragment],
    facts: List[NativeSemanticModelQueryFragment],
    where_clause: Optional[str] = None,
    order_by: Optional[str] = None,
    limit: int = 10,
) -> QueryResult | ToolError:
    """Execute parameterized query on semantic view.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: name of the database in which the semantic view is located
        schema_name: name of the schema in which the semantic view is located
        view_name: name of the semantic view to query
        measures: List of measures like [{"table": "{semantic_table_name}", "name": "{measure_name}"}]
        dimensions: List of dimensions like [{"table": "{semantic_table_name}", "name": "{dimension_name}"}]
        facts: List of facts like [{"table": "{semantic_table_name}", "name": "{fact_name}"}]
        where_clause: Optional WHERE condition (e.g., "year = 2024")
        order_by: Optional ORDER BY clause (e.g., "{dimension_name} DESC")
        limit: Maximum rows to return (default: 10)
        query_name: Descriptive name for this query (e.g., "Q1 Revenue by Region")

    Returns:
        Query results with columns and rows

    Note:
        - Must include at least one of: measures, dimensions, or facts
        - Cannot combine facts with measures in same query
    """
    backend = ctx.deps.data_backend
    if not backend:
        return tool_error("No data backend configured")

    try:
        result = await backend.query_semantic_view(
            view_name=view_name,
            database_name=database_name,
            schema_name=schema_name,
            measures=measures,
            dimensions=dimensions,
            facts=facts,
            where_clause=where_clause,
            order_by=order_by,
            limit=limit,
        )

        # Set query_name if provided, fallback to view_name
        result.query_name = query_name or view_name

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        _record_query_preview(
            ctx,
            tool_name="query_semantic_view",
            query_name=result.query_name or view_name,
            columns=result.columns,
            rows=result.rows,
            extra_data={"semanticView": view_name},
        )

        return result
    except NotImplementedError as e:
        return ToolError(error_message=str(e))
    except Exception as e:
        logger.error(f"Error querying semantic view: {e}")
        return ToolError(error_message=str(e))

@semantic_view_toolset.tool
@safe_tool
async def list_semantic_views(
    ctx: RunContext[AgentDeps],
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    like: Optional[str] = None,
    starts_with: Optional[str] = None,
) -> list[dict[str, Any]] | ToolError:
    """List all semantic views in a schema.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: Database name
        schema_name: Schema name
        like: Pattern to filter view names (SQL LIKE syntax)
        starts_with: Prefix to filter view names
    Returns:
        List of semantic views
    """
    backend = ctx.deps.data_backend
    if not backend:
        return tool_error("No data backend configured")

    try:
        semantic_views = await backend.list_semantic_views(
            database_name=database_name,
            schema_name=schema_name,
            like=like,
            starts_with=starts_with,
        )
        return semantic_views
    except Exception as e:
        logger.error(f"Error listing semantic views: {e}")
        return ToolError(error_message=str(e))


@semantic_view_toolset.tool
@safe_tool
async def list_semantic_metrics(
    ctx: RunContext[AgentDeps],
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    view_name: Optional[str] = None,
    like: Optional[str] = None,
    starts_with: Optional[str] = None,
) -> QueryResult | ToolError:
    """List semantic metrics with optional database/schema filtering.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: Database name (optional)
        schema_name: Schema name (optional)
        view_name: View name (optional)
        like: Pattern to filter measure names (SQL LIKE syntax)
        starts_with: Prefix to filter measure names
    """
    backend = ctx.deps.data_backend
    if not backend:
        return ToolError(error_message="No data backend configured")

    try:
        measures = await backend.show_semantic_metrics(
            database_name=database_name,
            schema_name=schema_name,
            view_name=view_name,
            like=like,
            starts_with=starts_with,
        )
        return measures
    except Exception as e:
        logger.error(f"Error listing semantic metrics: {e}")
        return ToolError(error_message=str(e))


@semantic_view_toolset.tool
@safe_tool
async def list_semantic_dimensions(
    ctx: RunContext[AgentDeps],
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    view_name: Optional[str] = None,
    like: Optional[str] = None,
    starts_with: Optional[str] = None,
) -> QueryResult | ToolError:
    """List semantic dimensions with optional database/schema filtering.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: Database name (optional)
        schema_name: Schema name (optional)
        view_name: View name (optional)
        like: Pattern to filter dimension names (SQL LIKE syntax)
        starts_with: Prefix to filter dimension names
    """
    backend = ctx.deps.data_backend
    if not backend:
        return ToolError(error_message="No data backend configured")

    try:
        dimensions = await backend.show_semantic_dimensions(
            database_name=database_name,
            schema_name=schema_name,
            view_name=view_name,
            like=like,
            starts_with=starts_with,
        )
        return dimensions
    except Exception as e:
        logger.error(f"Error listing semantic dimensions: {e}")
        return ToolError(error_message=str(e))


@semantic_view_toolset.tool
@safe_tool
async def list_semantic_facts(
    ctx: RunContext[AgentDeps],
    database_name: Optional[str] = None,
    schema_name: Optional[str] = None,
    view_name: Optional[str] = None,
    like: Optional[str] = None,
    starts_with: Optional[str] = None,
) -> QueryResult | ToolError:
    """List semantic facts with optional database/schema filtering.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: Database name (optional)
        schema_name: Schema name (optional)
        view_name: View name (optional)
        like: Pattern to filter fact names (SQL LIKE syntax)
        starts_with: Prefix to filter fact names
    """
    backend = ctx.deps.data_backend
    if not backend:
        return ToolError(error_message="No data backend configured")

    try:
        facts = await backend.show_semantic_facts(
            database_name=database_name,
            schema_name=schema_name,
            view_name=view_name,
            like=like,
            starts_with=starts_with,
        )
        return facts
    except Exception as e:
        logger.error(f"Error listing semantic facts: {e}")
        return ToolError(error_message=str(e))

@semantic_view_toolset.tool
@safe_tool
async def get_semantic_view_ddl(
    ctx: RunContext[AgentDeps],
    database_name: str,
    schema_name: str,
    view_name: str,
) -> str | ToolError:
    """Get DDL for a semantic view.

    Args:
        ctx: Runtime context with agent dependencies
        database_name: Database name
        schema_name: Schema name
        view_name: Name of semantic view
    Returns:
        DDL for the semantic view
    """
    backend = ctx.deps.data_backend
    if not backend:
        return ToolError(error_message="No data backend configured")

    try:
        ddl = await backend.get_semantic_view_ddl(
            database_name=database_name,
            schema_name=schema_name,
            view_name=view_name,
        )
        return ddl
    except Exception as e:
        logger.error(f"Error getting semantic view DDL: {e}")
        return ToolError(error_message=str(e))