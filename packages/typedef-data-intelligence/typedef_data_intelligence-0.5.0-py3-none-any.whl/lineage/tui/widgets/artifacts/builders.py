"""Builder functions for artifact widgets.

Contains functions that build reusable Textual widgets for various artifact types.
These can be used both by the ArtifactViewer sidebar and for standalone rendering.
"""
import math
from typing import Any, Dict, List, Optional

from textual.widgets import DataTable, Markdown

from lineage.tui.widgets.artifacts.formatters import (
    _format_lineage_node_card,
    _format_node_card,
)
from lineage.tui.widgets.artifacts.helpers import (
    _detect_display_type,
    _escape_markdown,
    _get_short_name,
    _get_type_icon,
    _group_nodes_by_type,
    _render_as_table,
    _truncate,
)


def build_table_widget(*, columns: List[str], rows: List[List[Any]]) -> DataTable:
    """Build a DataTable widget for a table artifact."""
    table = DataTable()
    table.add_columns(*columns)
    table.add_rows(rows)
    return table


def build_graph_result_widget(
    *,
    title: str,
    nodes: List[Any],
    query_description: str = "",
    display_hint: Optional[str] = None,
) -> Markdown:
    """Build a Markdown widget for graph query results."""
    content_parts = [f"# {title}", ""]
    if query_description:
        content_parts.append(f"*{_escape_markdown(query_description)}*")
        content_parts.append("")

    if not nodes:
        content_parts.append("*No results*")
        return Markdown("\n".join(content_parts), classes="graph-result")

    display_type = display_hint or _detect_display_type(nodes)
    if display_type == "scalar":
        if len(nodes) == 1 and isinstance(nodes[0], dict):
            for k, v in nodes[0].items():
                content_parts.append(f"**{k}:** {v}")
                content_parts.append("")
    elif display_type == "table":
        content_parts.append(_render_as_table(nodes))
        content_parts.append("")
    else:
        content_parts.append(f"**Found {len(nodes)} results**")
        content_parts.append("")
        by_type = _group_nodes_by_type(nodes)
        for node_type, items in by_type.items():
            icon = _get_type_icon(node_type)
            content_parts.append(f"- {icon} **{node_type}**: {len(items)}")
        content_parts.append("")
        content_parts.append("---")
        content_parts.append("")

        max_cards = 10
        cards_rendered = 0
        for node in nodes:
            if cards_rendered >= max_cards:
                remaining = len(nodes) - max_cards
                if remaining > 0:
                    content_parts.append(f"*... and {remaining} more*")
                break
            if isinstance(node, dict):
                content_parts.append(_format_node_card(node))
                content_parts.append("---")
                content_parts.append("")
                cards_rendered += 1

    return Markdown("\n".join(content_parts), classes="graph-result")


def build_search_results_widget(*, search_term: str, results: List[Any]) -> Markdown:
    """Build a Markdown widget for search results."""
    content_parts = [f'# 🔎 Search: "{search_term}"', ""]
    if not results:
        content_parts.append("*No matches found*")
        return Markdown("\n".join(content_parts), classes="search-results")

    raw_scores = [item.get("score", 0) or 0 for item in results if isinstance(item, dict)]
    max_score = max(raw_scores) if raw_scores else 0
    for i, item in enumerate([r for r in results if isinstance(r, dict)][:10], 1):
        raw_score = item.get("score", 0) or 0
        norm_score = int(round((raw_score / max_score) * 100)) if max_score > 0 else 0
        stars = "⭐" * math.ceil(norm_score / 20.0)
        name = item.get("name", "Unknown")
        model_id = item.get("id", "")
        name_with_tooltip = f'[{name}](# "raw score: {raw_score}")'
        content_parts.append(f"**{i}. {stars} {name_with_tooltip}** ({norm_score})")
        content_parts.append("")
        content_parts.append(f"`{model_id}`")
        content_parts.append("")

    return Markdown("\n".join(content_parts), classes="search-results")


def build_join_patterns_widget(
    *,
    model_name: str,
    cluster_id: Optional[str] = None,
    cluster_pattern: Optional[str] = None,
    join_partners: Optional[List[Any]] = None,
) -> Markdown:
    """Build a Markdown widget for join patterns."""
    content_parts = [f"## 🔗 {model_name} - Joins", ""]
    if cluster_id:
        content_parts.append(f"**Cluster:** {cluster_pattern} (Cluster {cluster_id})")
        content_parts.append("")

    partners = join_partners or []
    if partners:
        content_parts.append("**Join Partners:**")
        for p in partners[:8]:
            if isinstance(p, dict):
                pname = p.get("name", "?")
                content_parts.append(f"  - {pname}")
        content_parts.append("")

    return Markdown("\n".join(content_parts), classes="join-patterns")


def build_impact_tree_widget(
    *,
    model_name: str,
    affected_models: List[Any],
    total: int,
) -> Markdown:
    """Build a Markdown widget for downstream impact."""
    content_parts = [f"## 📉 Impact: {model_name}", ""]
    if total == 0:
        content_parts.append("*No downstream dependencies*")
        return Markdown("\n".join(content_parts), classes="impact-tree")

    content_parts.append(f"**Affects {total} models:**")
    content_parts.append("")

    by_depth: Dict[int, List[Dict[str, Any]]] = {}
    for m in affected_models:
        if not isinstance(m, dict):
            continue
        depth = m.get("depth", 0)
        by_depth.setdefault(int(depth or 0), []).append(m)

    if 1 in by_depth:
        content_parts.append("**Direct:**")
        content_parts.append("")
        for m in by_depth[1][:10]:
            content_parts.append(f"- {m.get('name', '?')}")
        if len(by_depth[1]) > 10:
            content_parts.append(f"- *(... and {len(by_depth[1]) - 10} more)*")
        content_parts.append("")

    deeper: List[Dict[str, Any]] = []
    for depth in sorted(k for k in by_depth.keys() if k > 1):
        deeper.extend(by_depth[depth])
    if deeper:
        content_parts.append(f"**Indirect (depth 2+):** {len(deeper)} models")
        content_parts.append("")
        for m in deeper[:10]:
            content_parts.append(f"- {m.get('name', '?')} (depth {m.get('depth', '?')})")
        if len(deeper) > 10:
            content_parts.append(f"- *(... and {len(deeper) - 10} more)*")
        content_parts.append("")

    return Markdown("\n".join(content_parts), classes="impact-tree")


def build_plan_widget(*, plan: Dict[str, Any]) -> Markdown:
    """Build a Markdown widget for a Plan artifact."""
    title = plan.get("title") or "Plan"
    goal = plan.get("goal") or ""
    status = (plan.get("status") or "draft").lower()
    locked = " 🔒" if status == "final" else ""

    content_parts: List[str] = [f"# 🧭 {title}{locked}", ""]
    if goal:
        content_parts.append(f"**Goal:** {_escape_markdown(goal)}")
        content_parts.append("")

    content_parts.append(f"**Status:** {status}")
    content_parts.append("")

    sections = plan.get("sections") or []
    if sections:
        content_parts.append("## Sections")
        content_parts.append("")
        for s in sections:
            if not isinstance(s, dict):
                continue
            stitle = s.get("title") or s.get("section_id") or "Section"
            content_parts.append(f"### {stitle}")
            content_parts.append("")
            body = s.get("content_markdown") or ""
            if body:
                content_parts.append(str(body))
            content_parts.append("")

    steps = plan.get("steps") or []
    content_parts.append("## Steps")
    content_parts.append("")
    if not steps:
        content_parts.append("*No steps yet*")
    else:
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict):
                continue
            text = step.get("content") or ""
            risk = step.get("risk")
            deps = step.get("dependencies") or []
            risk_str = f" _(risk: {risk})_" if risk else ""
            content_parts.append(f"{i}. {text}{risk_str}")
            if deps:
                content_parts.append(f"   - depends_on: {', '.join(str(d) for d in deps)}")
    content_parts.append("")

    return Markdown("\n".join(content_parts), classes="plan-preview")


def build_lineage_widget(*, lineage: Dict[str, Any]) -> Markdown:
    """Build a Markdown widget for lineage results."""
    root_id = lineage.get("root") or lineage.get("identifier") or "?"
    nodes_data = lineage.get("nodes") or []
    dir_type = lineage.get("direction") or "unknown"
    desc = lineage.get("description") or lineage.get("query_description") or ""
    hops = lineage.get("hops") or []
    edges = lineage.get("edges") or []

    content_parts = [f"# Lineage: {_escape_markdown(root_id)}", ""]
    if desc:
        content_parts.append(f"*{_escape_markdown(desc)}*")
        content_parts.append("")

    content_parts.append(f"**Direction:** {dir_type}")
    content_parts.append(f"**Found {len(nodes_data)} nodes, {len(edges)} edges**")
    content_parts.append("")

    # Hop summary (for column lineage)
    if hops:
        transforms: List[str] = []
        for hop in hops:
            if isinstance(hop, dict):
                transforms.extend([str(t) for t in hop.get("transformations", [])])
        unique_transforms: List[str] = []
        for t in transforms:
            if t not in unique_transforms:
                unique_transforms.append(t)
        if unique_transforms:
            palette = ", ".join(unique_transforms[:8])
            more = "" if len(unique_transforms) <= 8 else f" (+{len(unique_transforms)-8} more)"
            content_parts.append(f"**Transform palette:** {palette}{more}")
        content_parts.append(f"**Hops:** {len(hops)}")
        content_parts.append("")

        content_parts.append("### Hop Steps")
        for idx, hop in enumerate(hops, start=1):
            if not isinstance(hop, dict):
                continue
            from_id = hop.get("from_id") or "?"
            to_id = hop.get("to_id") or "?"
            transformations = hop.get("transformations") or []
            t_str = ", ".join(str(t) for t in transformations) if transformations else "DERIVES_FROM"
            content_parts.append(f"{idx}. `{from_id}` -> `{to_id}`  via {t_str}")
        content_parts.append("")

    # Node type summary
    if isinstance(nodes_data, list):
        by_type = _group_nodes_by_type([n for n in nodes_data if isinstance(n, dict)])
        for node_type, items in by_type.items():
            icon = _get_type_icon(node_type)
            content_parts.append(f"- {icon} **{node_type}**: {len(items)}")
        content_parts.append("")

    # Dependencies (relation lineage)
    if edges:
        content_parts.append("### Dependencies")
        depends_on = [e for e in edges if isinstance(e, dict) and e.get("edge_type") == "DEPENDS_ON"]
        builds = [e for e in edges if isinstance(e, dict) and e.get("edge_type") == "BUILDS"]

        if depends_on:
            for edge in depends_on[:15]:
                from_name = _get_short_name(edge.get("from_id", "?"))
                to_name = _get_short_name(edge.get("to_id", "?"))
                content_parts.append(f"  `{from_name}` -> `{to_name}`")
            if len(depends_on) > 15:
                content_parts.append(f"  *... and {len(depends_on) - 15} more dependencies*")

        if builds:
            content_parts.append("")
            content_parts.append("### Builds (Logical -> Physical)")
            for edge in builds[:10]:
                from_name = _get_short_name(edge.get("from_id", "?"))
                to_name = _get_short_name(edge.get("to_id", "?"))
                content_parts.append(f"  `{from_name}` -> `{to_name}`")
            if len(builds) > 10:
                content_parts.append(f"  *... and {len(builds) - 10} more builds*")

        content_parts.append("")

    content_parts.append("---")
    content_parts.append("")

    # Node cards with semantic summaries
    max_cards = 10
    cards_rendered = 0
    for node in nodes_data:
        if cards_rendered >= max_cards:
            remaining = len(nodes_data) - max_cards
            if remaining > 0:
                content_parts.append(f"*... and {remaining} more nodes (use get_model_details for specifics)*")
            break
        if isinstance(node, dict):
            content_parts.append(_format_lineage_node_card(node))
            content_parts.append("---")
            content_parts.append("")
            cards_rendered += 1

    return Markdown("\n".join(content_parts), classes="lineage-result")


def build_model_details_widget(*, model_details: Dict[str, Any]) -> Markdown:
    """Build a Markdown widget for model details."""
    details = model_details
    content_parts = [f"# {_escape_markdown(details.get('model_name', 'Model'))}", ""]

    if details.get("description"):
        content_parts.append(f"*{_escape_markdown(details['description'])}*")
        content_parts.append("")

    mat = details.get("materialization", "model")
    path = details.get("original_path", "")
    content_parts.append(f"**Materialization:** {mat}")
    if path:
        content_parts.append(f"**Path:** `{path}`")
    content_parts.append("")

    if any(details.get(f) for f in ["grain", "intent", "analysis_summary", "measures", "dimensions", "facts"]):
        content_parts.append("## Semantic Analysis")
        content_parts.append("")

        if details.get("grain"):
            content_parts.append(f"**Grain:** {_escape_markdown(details['grain'])}")
        if details.get("intent"):
            content_parts.append(f"**Intent:** {_escape_markdown(details['intent'])}")

        flags = []
        if details.get("has_aggregations"):
            flags.append("aggregations")
        if details.get("has_window_functions"):
            flags.append("window functions")
        if flags:
            content_parts.append(f"**Features:** {', '.join(flags)}")

        if details.get("analysis_summary"):
            content_parts.append("")
            content_parts.append(f"{_escape_markdown(details['analysis_summary'])}")

        content_parts.append("")

        measures = details.get("measures") or []
        if measures:
            content_parts.append("### Measures")
            for m in measures:
                if not isinstance(m, dict):
                    continue
                name = m.get("name", "?")
                expr = m.get("expr", "")
                agg = m.get("agg_function", "")
                content_parts.append(f"- **{name}**: `{expr}` ({agg})")
            content_parts.append("")

        dimensions = details.get("dimensions") or []
        if dimensions:
            content_parts.append("### Dimensions")
            for d in dimensions:
                if not isinstance(d, dict):
                    continue
                name = d.get("name", "?")
                source = d.get("source", "")
                pii = " (PII)" if d.get("is_pii") else ""
                content_parts.append(f"- **{name}**{pii} (from: {source})")
            content_parts.append("")

        facts = details.get("facts") or []
        if facts:
            content_parts.append("### Facts")
            for f in facts:
                if not isinstance(f, dict):
                    continue
                name = f.get("name", "?")
                source = f.get("source", "")
                content_parts.append(f"- **{name}** (from: {source})")
            content_parts.append("")

    columns = details.get("columns") or []
    if columns:
        content_parts.append("## Columns")
        content_parts.append("")
        for col in columns[:20]:
            if not isinstance(col, dict):
                continue
            name = col.get("name", "?")
            dtype = col.get("data_type", "")
            desc = col.get("description", "")
            dtype_str = f" `{dtype}`" if dtype else ""
            desc_str = f" - {_truncate(desc, 50)}" if desc else ""
            content_parts.append(f"- **{name}**{dtype_str}{desc_str}")
        if len(columns) > 20:
            content_parts.append(f"*... and {len(columns) - 20} more columns*")
        content_parts.append("")

    macros = details.get("macros") or []
    if macros:
        content_parts.append("## Macro Dependencies")
        content_parts.append("")
        for macro in macros[:15]:
            if not isinstance(macro, dict):
                continue
            name = macro.get("name", "?")
            pkg = macro.get("package_name", "")
            pkg_str = f" ({pkg})" if pkg else ""
            content_parts.append(f"- `{name}`{pkg_str}")
        if len(macros) > 15:
            content_parts.append(f"*... and {len(macros) - 15} more macros*")
        content_parts.append("")

    if details.get("compiled_sql") or details.get("raw_sql"):
        content_parts.append("## SQL")
        content_parts.append("")
        sql = details.get("compiled_sql") or details.get("raw_sql") or ""
        if len(sql) > 2000:
            sql = sql[:2000] + "\n... (truncated)"
        content_parts.append("```sql")
        content_parts.append(sql)
        content_parts.append("```")
        content_parts.append("")

    return Markdown("\n".join(content_parts), classes="model-details")
