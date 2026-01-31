"""Cell rendering functions for report artifacts.

Contains functions that render different cell types (markdown, table, chart, mermaid)
into markdown strings for display in reports.
"""
from pathlib import Path
from typing import Any, Dict, Union

from lineage.backends.reports.protocol import CellData
from lineage.tui.widgets.image import (
    build_mermaid_live_url,
    render_chart_to_png,
    render_mermaid_to_png,
)


def _normalize_cell(cell: Union[CellData, Dict[str, Any]]) -> CellData:
    """Convert a dict to CellData if needed."""
    if isinstance(cell, CellData):
        return cell
    # Handle dict input - provide defaults for required fields
    return CellData(
        cell_id=cell.get("cell_id", ""),
        cell_type=cell.get("cell_type", cell.get("type", "markdown")),
        cell_number=cell.get("cell_number", 0),
        data=cell.get("data", {}),
    )


def _render_markdown_cell(data: Dict[str, Any]) -> str:
    """Render a markdown cell - passes through natively."""
    content = data.get("content", "")
    return content


def _render_table_cell(data: Dict[str, Any]) -> str:
    """Render a table cell as markdown table."""
    columns = data.get("columns", [])
    rows = data.get("rows", [])
    title = data.get("title", "")

    parts = []
    if title:
        parts.append(f"### {title}")
        parts.append("")

    if not columns or not rows:
        parts.append("*No data*")
        return "\n".join(parts)

    # Build markdown table
    header = "| " + " | ".join(str(c) for c in columns) + " |"
    separator = "|" + "|".join(["---" for _ in columns]) + "|"

    table_rows = []
    for row in rows[:50]:  # Limit to 50 rows
        if isinstance(row, dict):
            row_vals = [str(row.get(c, ""))[:50] for c in columns]
        elif isinstance(row, (list, tuple)):
            row_vals = [str(v)[:50] for v in row]
        else:
            row_vals = [str(row)]
        table_rows.append("| " + " | ".join(row_vals) + " |")

    parts.extend([header, separator] + table_rows)

    if len(rows) > 50:
        parts.append(f"*... and {len(rows) - 50} more rows*")

    return "\n".join(parts)


def _render_chart_cell(data: Dict[str, Any], output_dir: Path) -> str:
    """Render a chart cell with title, data preview, and open button."""
    title = data.get("title", "Chart")
    chart_type = data.get("chart_type", "line")
    chart_data = data.get("data", [])
    x_column = data.get("x_column", "")
    y_column = data.get("y_column", "")

    parts = [f"### 📊 {title}", f"**Type:** {chart_type}", ""]

    # Extract data for PNG generation
    if isinstance(chart_data, list) and chart_data and x_column and y_column:
        x_data = [row.get(x_column) for row in chart_data if isinstance(row, dict)]
        y_data = []
        for row in chart_data:
            if isinstance(row, dict):
                val = row.get(y_column)
                try:
                    y_data.append(float(val) if val is not None else 0.0)
                except (ValueError, TypeError):
                    y_data.append(0.0)

        # Generate PNG
        png_path = render_chart_to_png(
            chart_type=chart_type,
            title=title,
            x_data=x_data,
            y_data=y_data,
            x_label=x_column,
            y_label=y_column,
            output_dir=output_dir,
        )

        if png_path and png_path.exists():
            parts.append(f"[Open Chart Image]({png_path})")
            parts.append("")

        # Data preview
        parts.append("**Data Preview:**")
        parts.append(f"| {x_column} | {y_column} |")
        parts.append("|---|---|")
        for _i, (x, y) in enumerate(zip(x_data[:5], y_data[:5], strict=False)):
            parts.append(f"| {str(x)[:20]} | {y} |")
        if len(x_data) > 5:
            parts.append(f"*... and {len(x_data) - 5} more rows*")
    else:
        parts.append("*Chart data not available*")

    return "\n".join(parts)


def _render_mermaid_cell(data: Dict[str, Any], output_dir: Path) -> str:
    """Render a mermaid cell with source, mermaid.live link, and open PNG button."""
    title = data.get("title", "Diagram")
    diagram = data.get("diagram", "")

    parts = [f"### 🔀 {title}", ""]

    if diagram:
        # Build mermaid.live URL
        live_url = build_mermaid_live_url(diagram)
        parts.append(f"[View on mermaid.live]({live_url})")
        parts.append("")

        # Try to generate PNG
        png_path = render_mermaid_to_png(diagram, output_dir)
        if png_path and png_path.exists():
            parts.append(f"[Open PNG Image]({png_path})")
            parts.append("")

        # Show source code
        parts.append("**Source:**")
        parts.append("```mermaid")
        parts.append(diagram)
        parts.append("```")
    else:
        parts.append("*No diagram content*")

    return "\n".join(parts)


def _render_cell(cell: Union[CellData, Dict[str, Any]], output_dir: Path) -> str:
    """Dispatch to appropriate cell renderer based on cell type.

    Args:
        cell: Either a CellData Pydantic model or a dict with cell_type and data fields.
        output_dir: Directory for writing generated assets (charts, PNGs).

    Returns:
        Rendered markdown string for the cell.
    """
    normalized = _normalize_cell(cell)

    if normalized.cell_type == "markdown":
        return _render_markdown_cell(normalized.data)
    elif normalized.cell_type == "table":
        return _render_table_cell(normalized.data)
    elif normalized.cell_type == "chart":
        return _render_chart_cell(normalized.data, output_dir)
    elif normalized.cell_type == "mermaid":
        return _render_mermaid_cell(normalized.data, output_dir)
    else:
        # Unknown type - try to render as markdown
        return _render_markdown_cell(normalized.data)


def _convert_mermaid_to_ascii(diagram: str) -> str:
    """Convert simple Mermaid diagrams to ASCII art representation.

    This is a best-effort conversion for common diagram types.
    Complex diagrams will fall back to showing the raw Mermaid syntax.
    """
    lines = diagram.strip().split('\n')
    if not lines:
        return diagram

    first_line = lines[0].strip().lower()

    # Handle flowchart/graph diagrams
    if first_line.startswith(('graph ', 'flowchart ')):
        # Extract nodes and edges
        nodes = {}
        edges = []

        for line in lines[1:]:
            line = line.strip()
            if not line or line.startswith('%'):
                continue

            # Parse edges: A --> B, A --- B, A --text--> B
            if '-->' in line or '---' in line or '--' in line:
                # Simple parsing for common patterns
                parts = line.replace('-->', ' --> ').replace('---', ' --- ').split()
                if len(parts) >= 3:
                    src = parts[0].split('[')[0].split('(')[0]  # Strip labels
                    dst = parts[-1].split('[')[0].split('(')[0]
                    edges.append((src, dst))
                    nodes[src] = nodes.get(src, src)
                    nodes[dst] = nodes.get(dst, dst)

            # Parse node definitions: A[Label]
            elif '[' in line:
                node_id = line.split('[')[0].strip()
                label = line.split('[')[1].split(']')[0] if ']' in line else node_id
                nodes[node_id] = label

        # Build ASCII representation
        if nodes and edges:
            result = ["┌─ Flowchart ─┐", ""]
            for src, dst in edges:
                src_label = nodes.get(src, src)
                dst_label = nodes.get(dst, dst)
                result.append(f"  [{src_label}] ──► [{dst_label}]")
            result.append("")
            return '\n'.join(result)

    # Handle ER diagrams
    if first_line.startswith('erdiagram'):
        result = ["┌─ ER Diagram ─┐", ""]
        for line in lines[1:]:
            line = line.strip()
            if '||' in line or '}|' in line or '|{' in line:
                # Parse entity relationship: ENTITY1 ||--o{ ENTITY2
                parts = line.split()
                if len(parts) >= 3:
                    result.append(f"  {parts[0]} ◄──► {parts[-1]}")
        result.append("")
        return '\n'.join(result) if len(result) > 3 else diagram

    # Handle sequence diagrams
    if first_line.startswith('sequencediagram'):
        result = ["┌─ Sequence Diagram ─┐", ""]
        for line in lines[1:]:
            line = line.strip()
            if '->>' in line or '-->>' in line:
                parts = line.split('->>')
                if len(parts) >= 2:
                    src = parts[0].strip()
                    rest = parts[1].split(':')
                    dst = rest[0].strip()
                    msg = rest[1].strip() if len(rest) > 1 else ""
                    result.append(f"  {src} ─────► {dst}: {msg}")
            elif '->' in line:
                parts = line.split('->')
                if len(parts) >= 2:
                    src = parts[0].strip()
                    rest = parts[1].split(':')
                    dst = rest[0].strip()
                    msg = rest[1].strip() if len(rest) > 1 else ""
                    result.append(f"  {src} ────► {dst}: {msg}")
        result.append("")
        return '\n'.join(result) if len(result) > 3 else diagram

    # Default: return original with formatting hint
    return diagram
