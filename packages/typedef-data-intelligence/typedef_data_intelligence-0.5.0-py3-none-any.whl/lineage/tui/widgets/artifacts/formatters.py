"""Node card formatting functions for artifact widgets.

Contains functions that format graph nodes into markdown card representations,
and common tool display mappings for the TUI.
"""
from typing import Dict

from lineage.tui.widgets.artifacts.helpers import (
    _escape_markdown,
    _get_node_type,
    _get_type_icon,
    _truncate,
)

# Tool display info mapping for friendly UI presentation across screens
TOOL_DISPLAY_INFO: Dict[str, Dict[str, str]] = {
    # Knowledge Graph
    "query_graph": {"verb": "Exploring Knowledge Graph", "icon": "🔍"},
    "get_graph_schema": {"verb": "Getting graph structure", "icon": "🌐"},
    "get_relation_lineage": {"verb": "Tracing lineage", "icon": "🌳"},
    "search_models": {"verb": "Searching models", "icon": "🔎"},
    "get_model_semantics": {"verb": "Analyzing model", "icon": "🧠"},
    "get_join_patterns": {"verb": "Mapping joins", "icon": "🔗"},
    "get_downstream_impact": {"verb": "Checking impact", "icon": "📉"},
    # Warehouse Discovery
    "list_databases": {"verb": "Discovering databases", "icon": "📁"},
    "list_schemas": {"verb": "Discovering schemas", "icon": "📂"},
    "list_tables": {"verb": "Discovering tables", "icon": "📋"},
    "get_table_schema": {"verb": "Inspecting table structure", "icon": "🔬"},
    # Warehouse Data
    "execute_query": {"verb": "Running SQL query", "icon": "🔎"},
    "preview_table": {"verb": "Sampling table data", "icon": "👀"},
    # Semantic Views
    "list_semantic_views": {"verb": "Listing semantic views", "icon": "📊"},
    "list_semantic_measures": {"verb": "Listing measures", "icon": "📏"},
    "list_semantic_dimensions": {"verb": "Listing dimensions", "icon": "📐"},
    "query_semantic_view": {"verb": "Querying semantic view", "icon": "🎯"},
    # Reports
    "create_report": {"verb": "Creating report", "icon": "📄"},
    "add_markdown_cell": {"verb": "Adding content", "icon": "📝"},
    "add_chart_cell": {"verb": "Adding chart", "icon": "📈"},
    "add_mermaid_cell": {"verb": "Adding diagram", "icon": "🔀"},
    "add_table_cell": {"verb": "Adding table", "icon": "📊"},
    # Tickets
    "create_ticket": {"verb": "Creating ticket", "icon": "🎫"},
    "list_tickets": {"verb": "Fetching tickets", "icon": "📋"},
    "get_ticket": {"verb": "Loading ticket", "icon": "🔖"},
    "update_ticket": {"verb": "Updating ticket", "icon": "🔄"},
    "add_ticket_comment": {"verb": "Adding comment", "icon": "💬"},
    "assign_ticket": {"verb": "Assigning ticket", "icon": "👤"},
    "close_ticket": {"verb": "Closing ticket", "icon": "✅"},
    "reopen_ticket": {"verb": "Reopening ticket", "icon": "🔓"},
    # Memory
    "store_memory": {"verb": "Saving to memory", "icon": "💾"},
    "search_memory": {"verb": "Searching memory", "icon": "🔍"},
    # CLI tools
    "bash": {"verb": "Running bash command", "icon": "🧰"},
    "dbt_cli": {"verb": "Running dbt command", "icon": "🧰"},
    "dbt_run": {"verb": "Running dbt models", "icon": "🧰"},
    "dbt_test": {"verb": "Running dbt tests", "icon": "🧰"},
    "dbt_build": {"verb": "Building dbt models", "icon": "🧰"},
    "dbt_compile": {"verb": "Compiling dbt models", "icon": "🧰"},
    # Plan tools
    "create_plan": {"verb": "Creating plan", "icon": "📋"},
    "get_plan": {"verb": "Loading plan", "icon": "📋"},
    "get_active_plan": {"verb": "Loading active plan", "icon": "📋"},
    "add_plan_section": {"verb": "Adding section", "icon": "📝"},
    "update_plan_section": {"verb": "Updating section", "icon": "📝"},
    "add_plan_step": {"verb": "Adding step", "icon": "📌"},
    "update_plan_step": {"verb": "Updating step", "icon": "📝"},
    "add_plan_question": {"verb": "Adding question", "icon": "❓"},
    "update_plan_question": {"verb": "Updating question", "icon": "📝"},
    "answer_plan_question": {"verb": "Answering question", "icon": "✅"},
    "finalize_plan": {"verb": "Finalizing plan", "icon": "✅"},
    "reopen_plan": {"verb": "Reopening plan", "icon": "🔓"},
    # Filesystem tools
    "read_file": {"verb": "Reading file", "icon": "📖"},
    "write_file": {"verb": "Writing file", "icon": "💾"},
    "edit_file": {"verb": "Editing file", "icon": "📝"},
    "glob_files": {"verb": "Finding files", "icon": "🔍"},
    "grep_files": {"verb": "Searching files", "icon": "🔎"},
    # Git tools
    "git_status": {"verb": "Checking git status", "icon": "📊"},
    "git_diff": {"verb": "Viewing changes", "icon": "📝"},
    "git_add": {"verb": "Staging changes", "icon": "➕"},
    "git_commit": {"verb": "Committing changes", "icon": "💾"},
    "git_branch": {"verb": "Managing branch", "icon": "🌿"},
    "git_push": {"verb": "Pushing changes", "icon": "🚀"},
    "git_log": {"verb": "Viewing history", "icon": "📜"},
    # Graph tools
    "get_model_details": {"verb": "Loading model details", "icon": "📋"},
    "get_column_lineage": {"verb": "Tracing column lineage", "icon": "🔗"},
    "search_graph_nodes": {"verb": "Searching graph", "icon": "🔍"},
}


def _format_node_card(node: dict) -> str:
    """Format a node into a compact, readable markdown card based on its type."""
    node_type = _get_node_type(node)
    icon = _get_type_icon(node_type)
    raw_name = node.get("name") or node.get("id") or "Unknown"
    name = _escape_markdown(raw_name)

    def prop(key: str, default: str = "") -> str:
        val = node.get(key, default)
        return _escape_markdown(val) if val else default

    # --- DbtModel ---
    if node_type == "DbtModel":
        mat = prop("materialization", "model")
        path = prop("original_path", "")
        path_line = f"  Path: `{path}`" if path else ""
        return f"**{icon} {name}** ({mat}){path_line}\n"

    # --- Physical Tables/Views ---
    if node_type in ("PhysicalTable", "PhysicalView"):
        fqn = prop("fqn", "")
        env = prop("environment", "")
        wh = prop("warehouse_type", "")
        env_str = f"{env}" if env else ""
        wh_str = f" ({wh})" if wh else ""
        return f"**{icon} {name}**  `{fqn}`\n  Env: {env_str}{wh_str}\n"

    # --- PhysicalIncrementalModel ---
    if node_type == "PhysicalIncrementalModel":
        fqn = prop("fqn", "")
        env = prop("environment", "")
        strategy = prop("materialization_strategy", "incremental")
        return f"**{icon} {name}**  `{fqn}`\n  Env: {env} | Strategy: {strategy}\n"

    # --- PhysicalMaterializedView ---
    if node_type == "PhysicalMaterializedView":
        fqn = prop("fqn", "")
        env = prop("environment", "")
        return f"**{icon} {name}**  `{fqn}`\n  Env: {env} | Materialized View\n"

    # --- PhysicalEphemeral ---
    if node_type == "PhysicalEphemeral":
        model_id = prop("id", "")
        return f"**{icon} {name}**  (ephemeral/CTE)\n  ID: `{model_id}`\n"

    # --- Semantic Analysis ---
    if node_type == "InferredSemanticModel":
        grain = prop("grain_human", "unknown")
        intent = prop("intent", "")
        flags = []
        if node.get("has_aggregations"):
            flags.append("agg")
        if node.get("has_window_functions"):
            flags.append("window")
        flag_str = ", ".join(flags) if flags else ""
        flag_line = f" [{flag_str}]" if flag_str else ""
        return f"**{icon} Semantic**{flag_line}  Grain: {grain}\n  {intent}\n"

    # --- Measures/Dimensions ---
    if node_type == "InferredMeasure":
        expr = prop("expr", "")
        agg = prop("agg_function", "")
        return f"  {icon} **{name}**: `{expr}` ({agg})\n"

    if node_type == "InferredDimension":
        source = prop("source", "")
        pii = " ⚠ PII" if node.get("is_pii") else ""
        return f"  {icon} **{name}**{pii}  from: {source}\n"

    # --- Columns ---
    if node_type in ("DbtColumn", "PhysicalColumn"):
        dtype = prop("data_type", "?")
        nullable = node.get("nullable")
        null_str = ""
        if nullable is not None:
            null_str = " NULL" if nullable else " NOT NULL"
        parent = prop("parent_id", "")
        parent_str = f"  ← {parent}" if parent else ""
        return f"  📍 **{name}** `{dtype}`{null_str}{parent_str}\n"

    # --- DbtSource ---
    if node_type == "DbtSource":
        loader = prop("loader", "")
        uid = prop("unique_id", "")
        loader_str = f"  Loader: {loader}" if loader else ""
        return f"**{icon} {name}**{loader_str}\n  ID: `{uid}`\n"

    # --- JoinCluster ---
    if node_type == "JoinCluster":
        cid = prop("cluster_id", "?")
        pattern = prop("pattern", "")
        count = prop("model_count", "0")
        return f"**{icon} Cluster {cid}**  {count} models\n  Pattern: {pattern}\n"

    # --- Fallback: show only useful fields ---
    useful_keys = ["id", "name", "fqn", "database", "schema_name", "environment"]
    lines = [f"**{icon} {name}** ({node_type})"]
    for key in useful_keys:
        if key in node and node[key] and key != "name":
            val = _truncate(str(node[key]), 45)
            lines.append(f"  {key}: `{val}`")
    return "\n".join(lines[:4]) + "\n"


def _format_lineage_node_card(node: dict) -> str:
    """Format a LineageOverviewNode into a compact markdown card with semantic summary.

    Optimized for the new lightweight lineage nodes that include semantic_summary.
    """
    node_type = node.get("type", "Unknown")
    icon = _get_type_icon(node_type)
    raw_name = node.get("name") or node.get("id") or "Unknown"
    name = _escape_markdown(raw_name)

    lines = []

    # Header with type icon and name
    mat = node.get("materialization", "")
    mat_str = f" ({mat})" if mat else ""
    lines.append(f"**{icon} {name}**{mat_str}")

    # Add semantic summary if present
    semantic = node.get("semantic_summary")
    if semantic and isinstance(semantic, dict):
        # Grain and intent on same line
        grain = semantic.get("grain_human", "")
        intent = semantic.get("intent", "")
        if grain:
            lines.append(f"  Grain: {_escape_markdown(grain)}")
        if intent:
            lines.append(f"  Intent: {_truncate(_escape_markdown(intent), 80)}")

        # Flags
        flags = []
        if semantic.get("has_aggregations"):
            flags.append("agg")
        if semantic.get("has_window_functions"):
            flags.append("window")
        if flags:
            lines.append(f"  Features: [{', '.join(flags)}]")

        # Analysis summary (truncated)
        summary = semantic.get("analysis_summary", "")
        if summary:
            lines.append(f"  {_truncate(_escape_markdown(summary), 100)}")

    # For physical nodes, show FQN
    fqn = node.get("fqn")
    if fqn and node_type != "DbtModel":
        lines.append(f"  `{_escape_markdown(fqn)}`")

    return "\n".join(lines) + "\n"
