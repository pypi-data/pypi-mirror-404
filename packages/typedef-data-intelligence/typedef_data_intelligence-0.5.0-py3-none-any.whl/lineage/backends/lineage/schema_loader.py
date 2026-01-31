"""Load and parse graph schema from YAML.

This module provides functions to:
1. Load the schema.yaml file
2. Generate KùzuDB DDL (CREATE NODE TABLE / CREATE REL TABLE)
3. Convert schema to get_graph_schema() format for API responses
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_schema() -> Dict[str, Any]:
    """Load schema YAML from file.

    Returns:
        Dictionary with 'nodes' and 'relationships' sections
    """
    schema_path = Path(__file__).parent / "schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def map_python_type_to_kuzu(py_type: str) -> str:
    """Map Python type to KùzuDB type.

    Args:
        py_type: Python type string (e.g., "str", "int", "list[str]")

    Returns:
        KùzuDB type string (e.g., "STRING", "INT64", "STRING[]")

    Example:
        >>> map_python_type_to_kuzu("str")
        'STRING'
        >>> map_python_type_to_kuzu("list[str]")
        'STRING[]'
    """
    mapping = {
        "str": "STRING",
        "int": "INT64",
        "bool": "BOOL",
        "float": "DOUBLE",
        "list[str]": "STRING[]",
        "dict": "MAP",
        "list[dict]": "MAP[]",
    }
    return mapping.get(py_type, py_type)


def map_python_type_to_cypher(py_type: str) -> str:
    """Map Python type to Neo4j Cypher type.

    Args:
        py_type: Python type string (e.g., "str", "int", "list[str]")

    Returns:
        Cypher type string (e.g., "String", "Integer", "List")

    Example:
        >>> map_python_type_to_cypher("str")
        'String'
        >>> map_python_type_to_cypher("list[str]")
        'List'
    """
    mapping = {
        "str": "String",
        "int": "Integer",
        "bool": "Boolean",
        "float": "Float",
        "list[str]": "List",
        "dict": "Map",
        "list[dict]": "List",
    }
    return mapping.get(py_type, py_type)


def generate_kuzu_node_ddl(node_name: str, node_def: Dict[str, Any]) -> str:
    r"""Generate KùzuDB CREATE NODE TABLE DDL from schema definition.

    Args:
        node_name: Name of the node type (e.g., "Model")
        node_def: Node definition from schema YAML

    Returns:
        KùzuDB DDL string for CREATE NODE TABLE

    Example:
        >>> generate_kuzu_node_ddl("Model", {...})
        'CREATE NODE TABLE Model(\\n  id STRING,\\n  name STRING,\\n  PRIMARY KEY (id)\\n);'
    """
    props = node_def["properties"]

    # Find primary key
    pk_cols = [col_name for col_name, col_def in props.items() if col_def.get("primary_key")]

    # Build column definitions (map Python types to KùzuDB types)
    columns = []
    for col_name, col_def in props.items():
        py_type = col_def["type"]
        kuzu_type = map_python_type_to_kuzu(py_type)
        columns.append(f"  {col_name} {kuzu_type}")

    # Build DDL
    ddl = f"CREATE NODE TABLE {node_name}(\n"
    ddl += ",\n".join(columns)

    # Add PRIMARY KEY clause
    if pk_cols:
        ddl += f",\n  PRIMARY KEY ({pk_cols[0]})"

    ddl += "\n);"

    return ddl


def generate_kuzu_rel_ddl(rel_name: str, rel_def: Dict[str, Any]) -> List[str]:
    """Generate KùzuDB CREATE REL TABLE DDL from schema definition.

    KùzuDB requires separate relationship tables for each (from, to) pair.
    For schemas with 'pairs:', we generate one table per pair.
    For legacy schemas with 'from'/'to', we preserve old behavior.

    Args:
        rel_name: Name of the relationship type (e.g., "DEPENDS_ON")
        rel_def: Relationship definition from schema YAML

    Returns:
        List of KùzuDB DDL strings (one per pair)

    Example:
        >>> # New format (pairs)
        >>> generate_kuzu_rel_ddl("BUILDS", {"pairs": [{"from": "DbtModel", "to": "PhysicalTable"}], ...})
        ['CREATE REL TABLE BUILDS_FROM_DbtModel_TO_PhysicalTable( FROM DbtModel TO PhysicalTable, ... );']

        >>> # Legacy format (from/to)
        >>> generate_kuzu_rel_ddl("DEPENDS_ON", {"from": "Model", "to": ["Model"], ...})
        ['CREATE REL TABLE DEPENDS_ON( FROM Model TO Model, ... );']
    """
    # Get multiplicity constraint (default to ONE_MANY for uniqueness)
    multiplicity = rel_def.get("multiplicity", "ONE_MANY")

    # Build properties string (map Python types to KùzuDB types)
    props_parts = []
    if "properties" in rel_def and rel_def["properties"]:
        for prop_name, prop_def in rel_def["properties"].items():
            py_type = prop_def["type"]
            kuzu_type = map_python_type_to_kuzu(py_type)
            props_parts.append(f"{prop_name} {kuzu_type}")

    props_str = ""
    if props_parts:
        props_str = ", " + ", ".join(props_parts)

    ddls = []

    # NEW FORMAT: pairs-based (schema v2)
    if "pairs" in rel_def:
        pairs = rel_def["pairs"]

        # If only one pair, use original relationship name
        if len(pairs) == 1:
            pair = pairs[0]
            from_type = pair["from"]
            to_type = pair["to"]
            table_name = rel_name
            ddl = f"CREATE REL TABLE {table_name}( FROM {from_type} TO {to_type}{props_str}, {multiplicity} );"
            ddls.append(ddl)
        else:
            # Multiple pairs - create separate table for each
            for pair in pairs:
                from_type = pair["from"]
                to_type = pair["to"]
                # Table name: EDGE_FROM_SourceType_TO_TargetType
                table_name = f"{rel_name}_FROM_{from_type}_TO_{to_type}"
                ddl = f"CREATE REL TABLE {table_name}( FROM {from_type} TO {to_type}{props_str}, {multiplicity} );"
                ddls.append(ddl)

    # LEGACY FORMAT: from/to (schema v1)
    else:
        from_type = rel_def["from"]
        to_types = rel_def["to"] if isinstance(rel_def["to"], list) else [rel_def["to"]]

        for to_type in to_types:
            table_name = rel_name
            ddl = f"CREATE REL TABLE {table_name}( FROM {from_type} TO {to_type}{props_str}, {multiplicity} );"
            ddls.append(ddl)

    return ddls


def get_all_node_names(schema: Dict[str, Any]) -> List[str]:
    """Get list of all node type names from schema.

    Args:
        schema: Loaded schema dictionary

    Returns:
        List of node type names
    """
    return list(schema["nodes"].keys())


def get_all_relationship_names(schema: Dict[str, Any]) -> List[str]:
    """Get list of all relationship type names from schema.

    Args:
        schema: Loaded schema dictionary

    Returns:
        List of relationship type names
    """
    return list(schema["relationships"].keys())


def schema_to_get_graph_schema_format(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert YAML schema to get_graph_schema() API format.

    This format is used by all backends to expose schema to agents/MCP tools.

    Args:
        schema: Loaded schema dictionary

    Returns:
        Dictionary with 'node_tables' and 'relationship_tables' sections

    Example:
        >>> result = schema_to_get_graph_schema_format(schema)
        >>> result["node_tables"]["Model"]["columns"]
        [{"name": "id", "type": "STRING"}, {"name": "name", "type": "STRING"}, ...]
    """
    result = {
        "node_tables": {},
        "relationship_tables": {}
    }

    # Convert nodes
    for node_name, node_def in schema["nodes"].items():
        columns = []
        for prop_name, prop_def in node_def["properties"].items():
            columns.append({
                "name": prop_name,
                "type": prop_def["type"]
            })
        result["node_tables"][node_name] = {
            "columns": columns,
            "description": node_def.get("description", "")
        }

    # Convert relationships
    for rel_name, rel_def in schema["relationships"].items():
        columns = []
        if "properties" in rel_def and rel_def["properties"]:
            for prop_name, prop_def in rel_def["properties"].items():
                columns.append({
                    "name": prop_name,
                    "type": prop_def["type"]
                })

        # NEW FORMAT: pairs-based (schema v2)
        if "pairs" in rel_def:
            # Extract unique from/to types from pairs
            from_types = list(set(pair["from"] for pair in rel_def["pairs"]))
            to_types = list(set(pair["to"] for pair in rel_def["pairs"]))

            result["relationship_tables"][rel_name] = {
                "columns": columns,
                "description": rel_def.get("description", ""),
                "pairs": rel_def["pairs"],  # Include full pairs info
                "from": from_types if len(from_types) > 1 else from_types[0],
                "to": to_types if len(to_types) > 1 else to_types[0]
            }

        # LEGACY FORMAT: from/to (schema v1)
        else:
            result["relationship_tables"][rel_name] = {
                "columns": columns,
                "description": rel_def.get("description", ""),
                "from": rel_def["from"],
                "to": rel_def["to"]
            }

    return result


# Domain display names for natural language summary
DOMAIN_DISPLAY_NAMES = {
    "dbt_logical": "dbt Logical Layer",
    "physical": "Physical Warehouse Layer",
    "semantic_inferred": "Semantic Layer (LLM-inferred)",
    "semantic_native": "Semantic Layer (Warehouse-native)",
    "runtime": "Runtime Operations (OpenLineage)",
    "lineage": "Data Lineage",
    "clustering": "Join Clustering",
    "profiling": "Data Profiling",
    "tickets": "Tickets",
}

# Order for displaying domains in summary
DOMAIN_ORDER = [
    "dbt_logical",
    "physical",
    "semantic_inferred",
    "semantic_native",
    "runtime",
    "lineage",
    "clustering",
    "profiling",
    "tickets",
]


def _group_schema_by_domain(schema: Dict[str, Any]) -> tuple:
    """Group nodes and relationships by domain.

    Args:
        schema: Loaded schema dictionary.

    Returns:
        Tuple of (nodes_by_domain, rels_by_domain) dictionaries.
    """
    nodes_by_domain: Dict[str, List[tuple]] = {}
    for node_name, node_def in schema["nodes"].items():
        domain = node_def.get("domain", "other")
        if domain not in nodes_by_domain:
            nodes_by_domain[domain] = []
        nodes_by_domain[domain].append((node_name, node_def))

    rels_by_domain: Dict[str, List[tuple]] = {}
    for rel_name, rel_def in schema["relationships"].items():
        domain = rel_def.get("domain", "other")
        if domain not in rels_by_domain:
            rels_by_domain[domain] = []
        rels_by_domain[domain].append((rel_name, rel_def))

    return nodes_by_domain, rels_by_domain


def _format_node_properties(
    node_def: Dict[str, Any],
    include_types: bool = False,
) -> List[str]:
    """Format node properties for display.

    Args:
        node_def: Node definition from schema.
        include_types: Whether to include type annotations.

    Returns:
        List of formatted property strings.
    """
    props = node_def.get("properties", {})
    prop_lines = []
    for prop_name, prop_def in props.items():
        # Skip internal search fields
        if prop_name.startswith("search_") or prop_name == "unique_id":
            continue
        if include_types:
            prop_type = prop_def.get("type", "unknown")
            is_pk = prop_def.get("primary_key", False)
            pk_marker = " (PK)" if is_pk else ""
            prop_lines.append(f"{prop_name}: {prop_type}{pk_marker}")
        else:
            prop_lines.append(prop_name)
    return prop_lines


def _format_relationship_pairs(rel_def: Dict[str, Any], max_pairs: int | None = 6) -> str:
    """Format relationship pairs for display.

    Args:
        rel_def: Relationship definition from schema.
        max_pairs: Maximum pairs to show before truncating. None for unlimited.

    Returns:
        Formatted string showing valid pairs.
    """
    if "pairs" in rel_def:
        pairs = rel_def["pairs"]
        limit = max_pairs if max_pairs else len(pairs)
        pair_strs = [f"{p['from']} → {p['to']}" for p in pairs[:limit]]
        if max_pairs and len(pairs) > max_pairs:
            pair_strs.append(f"... (+{len(pairs) - max_pairs} more)")
        return ", ".join(pair_strs)
    else:
        return rel_def.get("description", "")


def _generate_schema_text(
    schema: Dict[str, Any],
    header_lines: List[str],
    include_all_nodes: bool = False,
    include_property_types: bool = False,
    truncate_pairs: int | None = 6,
    include_rel_properties: bool = False,
) -> str:
    """Generate schema text with configurable detail level.

    Args:
        schema: Loaded schema dictionary.
        header_lines: Lines to include at the top of the output.
        include_all_nodes: If False, only show properties for core nodes.
        include_property_types: If True, include type annotations on properties.
        truncate_pairs: Max relationship pairs to show (None for all).
        include_rel_properties: If True, show relationship properties.

    Returns:
        Markdown-formatted schema string.
    """
    lines = header_lines.copy()
    nodes_by_domain, rels_by_domain = _group_schema_by_domain(schema)

    for domain in DOMAIN_ORDER:
        if domain not in nodes_by_domain and domain not in rels_by_domain:
            continue

        domain_display = DOMAIN_DISPLAY_NAMES.get(domain, domain)
        lines.append(f"### {domain_display}")
        lines.append("")

        domain_nodes = nodes_by_domain.get(domain, [])

        if include_all_nodes:
            # Show ALL nodes with properties
            for node_name, node_def in domain_nodes:
                desc = node_def.get("description", "")
                is_core = node_def.get("core", False)
                core_marker = " ⭐" if is_core else ""
                lines.append(f"**{node_name}**{core_marker}: {desc}")

                prop_lines = _format_node_properties(node_def, include_types=include_property_types)
                if prop_lines:
                    lines.append(f"  - Properties: {', '.join(prop_lines)}")
                lines.append("")
        else:
            # Separate core and non-core nodes
            core_nodes = [(n, d) for n, d in domain_nodes if d.get("core")]
            other_nodes = [(n, d) for n, d in domain_nodes if not d.get("core")]

            # Show core nodes with properties
            for node_name, node_def in core_nodes:
                desc = node_def.get("description", "")
                lines.append(f"**{node_name}**: {desc}")

                prop_lines = _format_node_properties(node_def, include_types=include_property_types)
                if prop_lines:
                    lines.append(f"  - Properties: {', '.join(prop_lines)}")
                lines.append("")

            # Show non-core nodes with just description
            if other_nodes:
                for node_name, node_def in other_nodes:
                    desc = node_def.get("description", "")
                    lines.append(f"**{node_name}**: {desc}")
                lines.append("")

        # Show relationships
        if domain in rels_by_domain:
            if include_rel_properties:
                # Detailed relationship format
                lines.append("**Relationships:**")
                for rel_name, rel_def in rels_by_domain[domain]:
                    desc = rel_def.get("description", "")
                    lines.append(f"- `{rel_name}`: {desc}")

                    if "pairs" in rel_def:
                        pairs_display = _format_relationship_pairs(rel_def, max_pairs=truncate_pairs)
                        lines.append(f"  - Valid pairs: {pairs_display}")

                    rel_props = rel_def.get("properties", {})
                    if rel_props:
                        prop_strs = [f"{k}: {v.get('type', 'unknown')}" for k, v in rel_props.items()]
                        lines.append(f"  - Properties: {', '.join(prop_strs)}")
            else:
                # Compact relationship format
                rel_summaries = []
                for rel_name, rel_def in rels_by_domain[domain]:
                    pairs_display = _format_relationship_pairs(rel_def, max_pairs=truncate_pairs)
                    rel_summaries.append(f"`{rel_name}`: {pairs_display}")

                if rel_summaries:
                    lines.append("**Relationships:**")
                    for rs in rel_summaries:
                        lines.append(f"- {rs}")

            lines.append("")

    return "\n".join(lines)


def generate_schema_summary(schema: Dict[str, Any] | None = None) -> str:
    """Generate a minimal schema summary for system prompt injection.

    This produces a highly condensed summary that:
    1. Groups nodes/relationships by domain
    2. Shows properties ONLY for core nodes (marked with core: true)
    3. Shows only names for non-core nodes
    4. Optimized for system prompt injection (~1,700 tokens)

    For full property details, use generate_schema_compact() instead.

    Args:
        schema: Loaded schema dictionary. If None, loads from file.

    Returns:
        Markdown-formatted schema summary string
    """
    if schema is None:
        schema = load_schema()

    header = [
        "## Knowledge Graph Schema",
        "",
        "The lineage graph models your dbt project at multiple levels.",
        "",
        "**IMPORTANT: You rarely need get_graph_schema().** This summary + specialized tools cover 95% of use cases:",
        "- `get_model_semantics()` - SQL, grain, measures, dimensions",
        "- `get_column_lineage()` - Column-level tracing",
        "- `get_relation_lineage()` - Model dependencies",
        "- `get_join_patterns()` - Join relationships",
        "- `get_downstream_impact()` - Impact analysis",
        "",
        "Only use `get_graph_schema(format='compact')` if you need exact property names for custom Cypher queries.",
        "",
    ]

    return _generate_schema_text(
        schema,
        header_lines=header,
        include_all_nodes=False,
        include_property_types=False,
        truncate_pairs=6,
        include_rel_properties=False,
    )


def generate_schema_compact(schema: Dict[str, Any] | None = None) -> str:
    """Generate a compact but complete schema in natural language format.

    This produces a full schema that:
    1. Groups nodes/relationships by domain
    2. Shows ALL properties for ALL nodes (with types)
    3. Shows all relationship pairs
    4. More detailed than summary, but still much smaller than JSON (~3-4k tokens)

    Use this when you need exact property names and types for Cypher queries.

    Args:
        schema: Loaded schema dictionary. If None, loads from file.

    Returns:
        Markdown-formatted complete schema string
    """
    if schema is None:
        schema = load_schema()

    header = [
        "## Knowledge Graph Schema (Complete)",
        "",
        "Full schema with all node types, properties, and relationships.",
        "",
    ]

    return _generate_schema_text(
        schema,
        header_lines=header,
        include_all_nodes=True,
        include_property_types=True,
        truncate_pairs=None,  # Show all pairs
        include_rel_properties=True,
    )


__all__ = [
    "load_schema",
    "map_python_type_to_kuzu",
    "map_python_type_to_cypher",
    "generate_kuzu_node_ddl",
    "generate_kuzu_rel_ddl",
    "get_all_node_names",
    "get_all_relationship_names",
    "schema_to_get_graph_schema_format",
    "generate_schema_summary",
    "generate_schema_compact",
]
