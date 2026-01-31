"""MCP server for data query operations using FastMCP.

This server automatically exposes all DataQueryBackend protocol methods as MCP tools,
eliminating boilerplate and keeping the server in sync with protocol changes.
"""
from __future__ import annotations

from fastmcp import FastMCP

from lineage.backends.data_query.protocol import DataQueryBackend
from lineage.backends.mcp_auto import auto_expose_protocol


def create_data_query_server(backend: DataQueryBackend, name: str = "data-query") -> FastMCP:
    """Create a FastMCP server for data queries.

    All DataQueryBackend protocol methods are automatically exposed as MCP tools
    with their original docstrings, signatures, and async handling.

    The following tools are automatically available:
    - execute_query: Execute SQL queries
    - get_table_schema: Get table schema information
    - preview_table: Preview table data
    - list_databases: List available databases
    - list_schemas: List schemas in a database
    - list_tables: List tables in a schema
    - validate_query: Validate SQL without executing
    - get_query_plan: Get query execution plan
    - profile_table: Profile table statistics (NEW!)
    - profile_column: Profile column statistics (NEW!)
    - get_semantic_views: Get semantic views (NEW!)

    Args:
        backend: Data query backend implementation
        name: Server name

    Returns:
        Configured FastMCP server with all protocol methods as tools
    """
    mcp = FastMCP(name)

    # Automatically expose all protocol methods as MCP tools
    # (Excludes internal methods like get_backend_type)
    auto_expose_protocol(
        mcp=mcp,
        backend=backend,
        protocol_class=DataQueryBackend,
        exclude_methods={"get_backend_type"},
    )

    return mcp
