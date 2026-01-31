"""Graph query tools for Pydantic agents."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.tools.data import logger
from lineage.agent.pydantic.types import (
    AgentDeps,
    DownstreamImpactResult,
    GraphSchemaResult,
    JoinPatternsResult,
    ModelMaterializationsResult,
    QueryGraphResult,
    SearchModelsResult,
)
from lineage.backends.lineage.protocol import (
    ColumnLineageResult,
    GraphSchemaFormat,
    ModelDetailsResult,
    RelationLineageResult,
)

graph_exploration_toolset = FunctionToolset()

@graph_exploration_toolset.tool
@safe_tool
async def get_graph_schema(
    ctx: RunContext[AgentDeps],
    format: GraphSchemaFormat = "compact",
) -> GraphSchemaResult | ToolError:
    """Get the graph database schema showing available node and relationship types.

    NOTE: The system prompt already contains a schema summary. Only call this tool if you need
    more detail than the summary provides (e.g., exact property names and types for Cypher queries).

    Args:
        ctx: Runtime context with dependencies.
        format: Output format:
            - "summary": Minimal schema (~1,700 tokens). Core nodes with key properties only.
              Usually not needed since this is already in the system prompt.
            - "compact" (default): Complete schema (~3-4k tokens). All nodes with all properties and types.
              Use when you need exact property names for Cypher queries.
            - "structured": Full JSON schema (~12k tokens). Use for programmatic access.

    Returns:
        Schema information including node tables, relationship tables, and their properties,
        plus example queries and helpful notes
    """
    try:
        schema = ctx.deps.lineage.get_graph_schema(format=format)

        # Build example queries for common use cases
        # we'll disable these for now, as they are covered by the tools.
        examples = {
#             "find_physical_lineage": """MATCH (pt:PhysicalTable)
# WHERE toLower(pt.fqn) = toLower('database.schema.table_name')
# OPTIONAL MATCH path = (pt)-[:BUILDS*..10]-(related)
# RETURN pt, path
# LIMIT 100""",
#             "find_logical_lineage": """MATCH (m:DbtModel)
# WHERE toLower(m.id) = toLower('model.project.model_name')
# OPTIONAL MATCH path = (m)-[:DEPENDS_ON*..10]-(related)
# RETURN m, path
# LIMIT 100""",
#             "trace_physical_column_lineage": """MATCH (pc:PhysicalColumn)
# WHERE toLower(pc.fqn) = toLower('database.schema.table.column')
# OPTIONAL MATCH path = (pc)-[:DERIVES_FROM*..10]-(related)
# RETURN pc, path
# LIMIT 100""",
#             "trace_logical_column_lineage": """MATCH (dc:DbtColumn)
# WHERE toLower(dc.id) = toLower('model.project.model_name.column_name')
# OPTIONAL MATCH path = (dc)-[:DERIVES_FROM*..10]-(related:DbtColumn)
# RETURN dc, path
# LIMIT 100""",
#             "find_upstream_tables": """MATCH (pt:PhysicalTable)
# WHERE toLower(pt.fqn) = toLower('database.schema.table_name')
# OPTIONAL MATCH path = (upstream)-[:BUILDS*..10]->(pt)
# RETURN pt, path
# LIMIT 100""",
#             "find_downstream_tables": """MATCH (pt:PhysicalTable)
# WHERE toLower(pt.fqn) = toLower('database.schema.table_name')
# OPTIONAL MATCH path = (pt)-[:BUILDS*..10]->(downstream)
# RETURN pt, path
# LIMIT 100""",
        }

        notes = (
            "Note: Schema names are lowercase in the graph. If you get 'No results found', "
            "try using toLower() in your WHERE clauses: WHERE toLower(pt.schema_name) = toLower('SchemaName')"
        )

        # Store typed result in state keyed by tool_call_id for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result = GraphSchemaResult(format=format, schema=schema, examples=examples, notes=notes)
        ctx.deps.state.tool_results[tool_call_id] = result

        return result
    except Exception as e:
        logger.error(f"Error getting graph schema: {e}")
        return tool_error(f"Error getting graph schema: {e}")

@graph_exploration_toolset.tool
@safe_tool
async def query_graph(
    ctx: RunContext[AgentDeps],
    cypher: str,
    query_description: str,
    display_hint: Optional[Literal["table", "cards", "scalar", "list"]] = None,
) -> QueryGraphResult | ToolError:
    """Execute a Cypher query against the lineage graph.

    Args:
        ctx: Runtime context with dependencies.
        cypher: Cypher query string (include filters directly in query)
        query_description: Human-readable description of what this query is looking for
            (e.g., "Finding all models related to ARR calculation")
        display_hint: Optional hint for how to display results in TUI
            - "table": Render as markdown table (good for aggregations/counts)
            - "cards": Render as typed node cards (good for node queries)
            - "scalar": Single value display (good for COUNT/SUM)
            - "list": Compact bullet list
            - None: Auto-detect based on result structure

    Returns:
        Query results as list of rows

    Note:
        Parameters are not supported - include filters directly in the query string.
        Example: MATCH (m:DbtModel) WHERE m.id = 'model.foo' RETURN m

        If no results found, remember: schema names are lowercase in the graph.
        Try using toLower() in WHERE clauses: WHERE toLower(pt.schema_name) = toLower('SchemaName')
    """
    try:
        result = ctx.deps.lineage.execute_raw_query(cypher)
        # execute_raw_query returns a dict with 'rows' key

        # Add helpful hint if no results
        error_msg = None
        if result.count == 0:
            error_msg = (
                "No results found. Note: Schema names are lowercase in the graph. "
                "Try using toLower() in your WHERE clauses: WHERE toLower(pt.schema_name) = toLower('SchemaName')"
            )

        # Store typed result in state keyed by tool_call_id for frontend generative UI
        tool_call_id = ctx.tool_call_id or "unknown"
        result_model = QueryGraphResult(
            nodes=result.rows,
            node_count=result.count,
            error=error_msg,
            query_description=query_description,
            display_hint=display_hint,
        )
        ctx.deps.state.tool_results[tool_call_id] = result_model

        return result_model
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        return tool_error(f"Error executing Cypher query: {e}")

@graph_exploration_toolset.tool
@safe_tool
async def get_relation_lineage(
    ctx: RunContext[AgentDeps],
    identifier: str,
    query_description: str,
    node_type: Literal["physical", "logical"],
    direction: Literal["upstream", "downstream", "both"] = "both",
    depth: int = 2,
    include_physical: bool = True,
) -> RelationLineageResult | ToolError:
    """Get lineage overview for a table/view/model (lightweight, token-efficient).

    Returns lightweight nodes with semantic summaries (no SQL) and dependency edges.
    Use get_model_details() to deep-dive into specific models for SQL, columns, or macros.

    Args:
        ctx: Runtime context with dependencies.
        identifier: PhysicalTable FQN (e.g., 'db.schema.table') or DbtModel ID (e.g., 'model.project.name').
        node_type: "physical" (start at warehouse table) or "logical" (start at dbt model).
        query_description: Human-readable description of what this lineage trace is for
            (e.g., "Tracing upstream dependencies of fct_revenue").
        direction: Which direction to traverse - "upstream", "downstream", or "both".
        depth: Maximum traversal depth.
        include_physical: Whether to include materialized physical tables in results, or only the logical models that build them.
    """
    try:
        # Backend returns typed, flattened, deduplicated result
        result = ctx.deps.lineage.get_relation_lineage(
            identifier=identifier,
            node_type=node_type,
            direction=direction,
            depth=depth,
            include_physical=include_physical,
        )
        # Add the human-readable description to the result
        result.query_description = query_description

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result
        return result
    except Exception as e:
        logger.error(f"Error getting relation lineage: {e}")
        return tool_error(f"Error getting relation lineage: {e}")

@graph_exploration_toolset.tool
@safe_tool
async def get_column_lineage(
    ctx: RunContext[AgentDeps],
    identifier: str,
    node_type: Literal["physical", "logical"],
    query_description: str,
    direction: str = "upstream",
    depth: int = 4,
) -> ColumnLineageResult | ToolError:
    """Get column lineage (trace where column values originate or are used).

    Args:
        ctx: Runtime context
        identifier: PhysicalColumn FQN or DbtColumn ID
        node_type: "physical" or "logical"
        query_description: Human-readable description of what this column trace is for
        direction: "upstream" (trace source) or "downstream" (trace usage)
        depth: Maximum traversal depth
    """
    try:
        # Backend returns typed, flattened, deduplicated result
        result = ctx.deps.lineage.get_column_lineage(
            identifier, node_type, direction, depth
        )
        # Add the human-readable description to the result
        result.query_description = query_description

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result
        return result
    except Exception as e:
        logger.error(f"Error getting column lineage: {e}")
        return tool_error(f"Error getting column lineage: {e}")

# ============================================================================
# Specialized Graph Exploration Tools
# ============================================================================


SearchableNodeType = Literal[
    "DbtModel",
    "DbtSource",
    "PhysicalTable",
    "PhysicalView",
    "DbtColumn",
    "PhysicalColumn",
    "InferredMeasure",
    "InferredDimension",
    "InferredFact",
    "InferredSemanticModel",
]


@graph_exploration_toolset.tool
@safe_tool
async def search_graph_nodes(
    ctx: RunContext[AgentDeps],
    search_term: str,
    node_type: SearchableNodeType = "DbtModel",
    limit: int = 10,
) -> SearchModelsResult | ToolError:
    """Search graph nodes using FalkorDB full-text index with relevance scoring.

    Searches across indexed text fields (name, description, compiled_sql, etc.)
    and returns results ranked by TF-IDF relevance score.

    **Fulltext Query Syntax:**
    - Simple term: `revenue` - matches nodes containing "revenue" in any indexed field
    - Prefix: `rev*` - matches "revenue", "review", "revised", etc.
    - Fuzzy: `%revnue%1` - matches "revenue" with 1 character edit distance (typo-tolerant)
    - Boolean AND: `revenue monthly` - both terms must be present (space = AND)
    - Boolean OR: `revenue|income` - matches either term
    - Boolean NOT: `revenue -monthly` - matches "revenue" but excludes "monthly"

    **Indexed Fields by Node Type:**
    - DbtModel: name, description, compiled_sql, raw_sql
    - DbtSource/DbtColumn: name, description
    - PhysicalTable/PhysicalView: name, fqn
    - InferredSemanticModel: intent, analysis_summary
    - InferredMeasure/Dimension/Fact: name, expr/source/description

    **Tips:**
    - Use prefix search (`arr*`) to find variations like "arr", "arr_monthly", "arr_reporting"
    - Use fuzzy search (`%reveune%1`) to handle typos
    - Combine operators: `revenue|arr monthly` for flexible matching

    Args:
        ctx: Runtime context with dependencies.
        search_term: Search query (supports fulltext operators above)
        node_type: Type of node to search (default: DbtModel)
        limit: Maximum results to return (default: 10)

    Returns:
        SearchModelsResult with ranked results including id, name, description, and score
    """
    try:
        results = ctx.deps.lineage.search_nodes(node_type, search_term, limit)

        formatted = []
        for r in results:
            node = r.get("node", {}) if isinstance(r, dict) else {}
            score = r.get("score", 0) if isinstance(r, dict) else 0
            formatted.append(
                {
                    "id": node.get("id") or node.get("fqn"),
                    "name": node.get("name"),
                    "description": node.get("description") or node.get("expr") or node.get("intent"),
                    "score": float(score) if score else 0,
                }
            )

        result_model = SearchModelsResult(
            search_term=search_term,
            results=formatted,
            result_count=len(formatted),
        )

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result_model

        return result_model
    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        return tool_error(f"Error searching nodes: {e}")


@graph_exploration_toolset.tool
@safe_tool
async def get_model_details(
    ctx: RunContext[AgentDeps],
    model_id: str,
    include_sql: bool = False,
    include_semantics: bool = False,
    include_columns: bool = False,
    include_macros: bool = False,
) -> ModelDetailsResult | ToolError:
    """Get detailed model information with optional includes.

    Use after get_relation_lineage to deep-dive into specific models.
    Only includes requested data to minimize token usage.

    Args:
        ctx: Runtime context with dependencies.
        model_id: DbtModel ID (e.g., "model.project.fct_revenue")
        include_sql: Include raw_sql and canonical_sql (token-heavy, use sparingly)
        include_semantics: Include full semantic analysis (grain, measures, dimensions, facts)
        include_columns: Include DbtColumn information
        include_macros: Include DbtMacro dependencies

    Returns:
        ModelDetailsResult with requested detail level
    """
    try:
        result = ctx.deps.lineage.get_model_details(
            model_id=model_id,
            include_sql=include_sql,
            include_semantics=include_semantics,
            include_columns=include_columns,
            include_macros=include_macros,
        )

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        return result
    except Exception as e:
        logger.error(f"Error getting model details: {e}")
        return tool_error(f"Error getting model details: {e}")


@graph_exploration_toolset.tool
@safe_tool
async def get_model_materializations(
    ctx: RunContext[AgentDeps],
    model_id: str,
) -> ModelMaterializationsResult | ToolError:
    """Get all physical warehouse locations (tables/views) for a dbt model.

    A single dbt model can be materialized in multiple environments (e.g., prod, dev, staging).
    This tool returns the exact database, schema, and table name for each environment.

    Args:
        ctx: Runtime context with dependencies.
        model_id: DbtModel ID (e.g., "model.project.fct_revenue")

    Returns:
        ModelMaterializationsResult containing materializations with environment, fqn, and warehouse type.
    """
    try:
        result = ctx.deps.lineage.get_model_materializations(model_id)

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        return result
    except Exception as e:
        logger.error(f"Error getting model materializations: {e}")
        return tool_error(f"Error getting model materializations: {e}")


@graph_exploration_toolset.tool
@safe_tool
async def get_join_patterns(
    ctx: RunContext[AgentDeps],
    model_id: str,
) -> JoinPatternsResult | ToolError:
    """Get join patterns and cluster membership for a model.

    Shows which models this joins with and what cluster it belongs to.

    Args:
        ctx: Runtime context with dependencies.
        model_id: DbtModel ID (e.g., "model.project.fct_revenue")

    Returns:
        JoinPatternsResult with cluster info and join partners
    """
    try:
        escaped_id = model_id.replace("'", "\\'")

        raw = ctx.deps.lineage.execute_raw_query(f"""
            MATCH (m:DbtModel {{id: '{escaped_id}'}})
            OPTIONAL MATCH (m)-[:IN_JOIN_CLUSTER]->(c:JoinCluster)
            OPTIONAL MATCH (c)<-[:IN_JOIN_CLUSTER]-(partner:DbtModel)
            WHERE partner.id <> '{escaped_id}'
            OPTIONAL MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(ism)-[:HAS_JOIN_EDGE]->(je:JoinEdge)
            RETURN m.name AS model_name,
                   c.cluster_id AS cluster_id,
                   c.pattern AS cluster_pattern,
                   c.model_count AS cluster_size,
                   COLLECT(DISTINCT partner) AS partners,
                   COLLECT(DISTINCT je) AS join_edges
        """)

        if not raw.rows:
            return JoinPatternsResult(
                model_id=model_id,
                join_partners=[],
                join_edges=[],
            )

        row = raw.rows[0]
        result_model = JoinPatternsResult(
            model_id=model_id,
            model_name=row.get("model_name"),
            cluster_id=row.get("cluster_id"),
            cluster_pattern=row.get("cluster_pattern"),
            cluster_size=int(row.get("cluster_size") or 0),
            join_partners=[p for p in row.get("partners", []) if p],
            join_edges=[e for e in row.get("join_edges", []) if e],
        )

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result_model

        return result_model
    except Exception as e:
        logger.error(f"Error getting join patterns: {e}")
        return tool_error(f"Error getting join patterns: {e}")


@graph_exploration_toolset.tool
@safe_tool
async def get_downstream_impact(
    ctx: RunContext[AgentDeps],
    model_id: str,
    depth: int = 2,
) -> DownstreamImpactResult | ToolError:
    """Get all models affected if this model changes (downstream dependencies).

    Critical for checking blast radius before modifying a model.

    Args:
        ctx: Runtime context with dependencies.
        model_id: DbtModel ID (e.g., "model.project.fct_revenue")
        depth: How many levels deep to traverse (default: 2)

    Returns:
        DownstreamImpactResult with affected models and their depths
    """
    try:
        escaped_id = model_id.replace("'", "\\'")

        raw = ctx.deps.lineage.execute_raw_query(f"""
            MATCH (m:DbtModel {{id: '{escaped_id}'}})
            OPTIONAL MATCH path = (downstream:DbtModel)-[:DEPENDS_ON*1..{depth}]->(m)
            WITH m, downstream, length(path) AS path_length
            RETURN m.name AS model_name,
                   downstream.id AS downstream_id,
                   downstream.name AS downstream_name,
                   path_length
            ORDER BY path_length
        """)

        # Build affected models list
        affected = []
        max_depth_seen = 0
        for row in raw.rows:
            if row.get("downstream_id"):
                depth_val = row.get("path_length", 0)
                affected.append({
                    "id": row.get("downstream_id"),
                    "name": row.get("downstream_name"),
                    "depth": depth_val,
                })
                max_depth_seen = max(max_depth_seen, depth_val)

        result_model = DownstreamImpactResult(
            model_id=model_id,
            model_name=raw.rows[0].get("model_name") if raw.rows else None,
            affected_models=affected,
            total_affected=len(affected),
            max_depth=max_depth_seen,
        )

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result_model

        return result_model
    except Exception as e:
        logger.error(f"Error getting downstream impact: {e}")
        return tool_error(f"Error getting downstream impact: {e}")
