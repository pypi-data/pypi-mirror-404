# ruff: noqa: I001
"""Presentation/report tooling for Pydantic agents."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from lineage.agent.pydantic.tools.common import ToolError, tool_error, safe_tool
from lineage.agent.pydantic.tools.data import logger
from lineage.agent.pydantic.types import (
    AgentDeps,
    MarkdownCellResult,
    ChartCellResult,
    TableCellResult,
    ListReportCellsResult,
    CellMetadata,
    CreateReportResult,
    ModifyCellResult,
    DeleteCellResult,
    MermaidCellResult,
    ReportPreview,
)
from lineage.agent.pydantic.utils import push_preview_tab
from lineage.agent.utils.visualization import ChartType
from lineage.backends.data_query.protocol import QueryResult
from lineage.backends.threads.models import Artifact
from pydantic_ai import FunctionToolset, RunContext

presentation_toolset = FunctionToolset()

# ============================================================================
# Helper Functions for State Updates
# ============================================================================


def _update_report_state(
    ctx: RunContext[AgentDeps],
    report_id: str,
    *,
    auto_open: bool = False,
) -> None:
    """Update active_reports state with latest report data from backend.

    This triggers automatic state_update events via AG-UI protocol.
    """
    if not ctx.deps.reports_backend:
        return

    try:
        # Fetch latest report from backend
        report = ctx.deps.reports_backend.get_report(report_id)

        # Convert cells to dict format for state
        cells_data = [cell.model_dump() for cell in report.cells]

        version = (
            report.updated_at.isoformat()
            if hasattr(report.updated_at, "isoformat")
            else str(report.updated_at)
        )

        # Update state (triggers automatic state_update event)
        ctx.deps.state.active_reports[report_id] = ReportPreview(
            report_id=report.report_id,
            title=report.title,
            cell_count=len(report.cells),
            last_updated=report.updated_at,
            cells=cells_data,
        )

        logger.debug(f"Updated report state for {report_id}: {len(report.cells)} cells")

        push_preview_tab(
            ctx.deps.state,
            tab_id=f"report_{report_id}",
            title=report.title,
            tool_name="report_preview",
            tab_type="report",
            data={
                "type": "report",
                "reportId": report.report_id,
                "reportTitle": report.title,
                "version": version,
            },
            auto_open=auto_open,
        )
    except Exception as e:
        logger.warning(f"Failed to update report state for {report_id}: {e}")


# ============================================================================
# New Cell-Based Report Building Tools (Backend-Only Architecture)
# ============================================================================


@presentation_toolset.tool
@safe_tool
async def create_report(
    ctx: RunContext[AgentDeps],
    title: str,
) -> CreateReportResult | ToolError:
    """Create a new report in the backend and track as artifact.

    The report_id is tracked in agent state's artifact list (ephemeral, this run only).
    At the end of the run, these artifacts will be saved to the thread store along
    with a summary of what happened in this run.

    Args:
        ctx: Runtime context with dependencies.
        title: Title for the report

    Returns:
        CreateReportResult with report_id and confirmation

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    try:
        # Create report in backend
        report_id = ctx.deps.reports_backend.create_report(title=title)

        artifact = Artifact(
            type="report",
            id=report_id,
            run_id=ctx.deps.run_id,
            title=title,
            created_at=datetime.now(),
        )
        ctx.deps.threads_backend.add_artifact(
            thread_id=ctx.deps.thread_id,
            run_id=ctx.deps.run_id,
            artifact=artifact,
        )

        # Create result for frontend
        result = CreateReportResult(
            report_id=report_id,
            title=title,
            message=f"Created report '{title}' (ID: {report_id})",
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id, auto_open=True)

        logger.info(f"Created report {report_id}: {title} (tracked as artifact)")
        return result
    except Exception as e:
        logger.error(f"Error creating report '{title}': {e}")
        return tool_error(f"Error creating report '{title}': {e}")


@presentation_toolset.tool
@safe_tool
async def add_markdown_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    content: str,
    cell_id: Optional[str] = None,
) -> MarkdownCellResult | ToolError:
    """Add a markdown cell to a report (immediately saved to backend).

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID to add cell to (from create_report result or thread context artifacts)
        content: Markdown content (supports headers, lists, tables, bold, italic, etc.)
        cell_id: Optional cell ID (auto-generated if not provided)

    Returns:
        MarkdownCellResult with cell metadata

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    cell_id = cell_id or f"cell_{uuid.uuid4().hex[:8]}"

    # Save directly to backend
    from lineage.backends.reports.protocol import CellData
    try:
        cell_data = CellData(
            cell_id=cell_id,
            cell_type="markdown",
            cell_number=1,  # Will be auto-assigned by backend
            data={"content": content},
        )

        ctx.deps.reports_backend.add_cells(
            report_id=report_id,
            cells=[cell_data],
        )

        # Create result for frontend rendering
        result = MarkdownCellResult(
            cell_id=cell_id,
            content=content,
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Added markdown cell {cell_id} to report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error adding markdown cell {cell_id} to report {report_id}: {e}")
        return tool_error(f"Error adding markdown cell {cell_id} to report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def add_chart_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    data: QueryResult,
    chart_type: ChartType,
    title: str,
    x_column: str,
    y_column: str,
    cell_id: Optional[str] = None,
) -> ChartCellResult | ToolError:
    """Add a chart cell to a report (immediately saved to backend).

    The data is stored as raw rows for frontend Recharts rendering.

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID to add cell to (from create_report result or thread context artifacts)
        data: Query results with columns and rows
        chart_type: Chart type (bar, line, scatter, pie, area)
        title: Chart title
        x_column: Column for x-axis
        y_column: Column for y-axis
        cell_id: Optional cell ID (auto-generated if not provided)

    Returns:
        ChartCellResult with cell metadata and data

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    cell_id = cell_id or f"cell_{uuid.uuid4().hex[:8]}"

    # Convert query result format (columns + rows) to list of dicts
    data_list = [dict(zip(data.columns, row, strict=False)) for row in data.rows]

    # Save directly to backend
    from lineage.backends.reports.protocol import CellData

    try:
        cell_data = CellData(
            cell_id=cell_id,
            cell_type="chart",
            cell_number=1,  # Will be auto-assigned by backend
            data={
                "chart_type": chart_type,
                "title": title,
                "columns": data.columns,
                "data": data_list,
                "x_column": x_column,
                "y_column": y_column,
            },
        )

        ctx.deps.reports_backend.add_cells(
            report_id=report_id,
            cells=[cell_data],
        )

        # Create result for frontend rendering
        result = ChartCellResult(
            cell_id=cell_id,
            chart_type=chart_type,
            title=title,
            columns=data.columns,
            data=data_list,
            x_column=x_column,
            y_column=y_column,
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Added {chart_type} chart cell {cell_id} to report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error adding chart cell {cell_id} to report {report_id}: {e}")
        return tool_error(f"Error adding chart cell {cell_id} to report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def add_table_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    data: QueryResult,
    title: Optional[str] = None,
    cell_id: Optional[str] = None,
) -> TableCellResult | ToolError:
    """Add a table cell to a report (immediately saved to backend).

    The data is stored as raw rows for frontend InteractiveTable rendering.

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID to add cell to (from create_report result or thread context artifacts)
        data: Query results with columns and rows
        title: Optional table title
        cell_id: Optional cell ID (auto-generated if not provided)

    Returns:
        TableCellResult with cell metadata and data

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    cell_id = cell_id or f"cell_{uuid.uuid4().hex[:8]}"

    # Convert query result format (columns + rows) to list of dicts
    data_list = [dict(zip(data.columns, row, strict=False)) for row in data.rows]

    # Save directly to backend
    from lineage.backends.reports.protocol import CellData

    try:
        cell_data = CellData(
            cell_id=cell_id,
            cell_type="table",
            cell_number=1,  # Will be auto-assigned by backend
            data={
                "title": title,
                "columns": data.columns,
                "data": data_list,
            },
        )

        ctx.deps.reports_backend.add_cells(
            report_id=report_id,
            cells=[cell_data],
        )

        # Create result for frontend rendering
        result = TableCellResult(
            cell_id=cell_id,
            title=title,
            columns=data.columns,
            data=data_list,
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Added table cell {cell_id} to report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error adding table cell {cell_id} to report {report_id}: {e}")
        return tool_error(f"Error adding table cell {cell_id} to report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def add_mermaid_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    diagram: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    cell_id: Optional[str] = None,
) -> MermaidCellResult | ToolError:
    """Add a mermaid diagram cell to a report for lineage/architecture visuals."""
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    if not diagram.strip():
        return tool_error("Mermaid diagram content cannot be empty")

    cell_id = cell_id or f"cell_{uuid.uuid4().hex[:8]}"

    from lineage.backends.reports.protocol import CellData

    try:
        cell_data = CellData(
            cell_id=cell_id,
            cell_type="mermaid",
            cell_number=1,
            data={
                "diagram": diagram,
                "title": title,
                "description": description,
            },
        )

        ctx.deps.reports_backend.add_cells(report_id=report_id, cells=[cell_data])

        result = MermaidCellResult(
            cell_id=cell_id,
            title=title,
            diagram=diagram,
        )

        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Added mermaid cell {cell_id} to report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error adding mermaid cell {cell_id} to report {report_id}: {e}")
        return tool_error(f"Error adding mermaid cell {cell_id} to report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def list_report_cells(
    ctx: RunContext[AgentDeps],
    report_id: str,
) -> ListReportCellsResult | ToolError:
    """List all cells in a report from backend storage.

    Returns cell metadata for reference when modifying or deleting cells.

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID to list cells from (from create_report result or thread context artifacts)

    Returns:
        ListReportCellsResult with cells list and total count

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    try:
        # Get report from backend
        report = ctx.deps.reports_backend.get_report(report_id)

        cells_metadata = []
        for cell in report.cells:
            # Generate preview based on cell type
            if cell.cell_type == "markdown":
                content = cell.data.get("content", "")
                preview = content[:100] if isinstance(content, str) else str(content)[:100]
            elif cell.cell_type == "chart":
                chart_type = cell.data.get("chart_type", "unknown")
                title = cell.data.get("title", "Untitled")
                preview = f"{chart_type} chart: {title}"
            elif cell.cell_type == "table":
                title = cell.data.get("title")
                data = cell.data.get("data", [])
                preview = f"Table ({len(data)} rows)" + (f": {title}" if title else "")
            elif cell.cell_type == "mermaid":
                title = cell.data.get("title")
                preview = "Mermaid diagram" + (f": {title}" if title else "")
            else:
                preview = f"{cell.cell_type} cell"

            cells_metadata.append(
                CellMetadata(
                    cell_id=cell.cell_id,
                    cell_number=cell.cell_number,
                    cell_type=cell.cell_type,
                    preview=preview,
                )
            )

        result = ListReportCellsResult(
            cells=cells_metadata,
            total_count=len(cells_metadata),
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        logger.info(f"Listed {len(cells_metadata)} cells from report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error listing cells for report {report_id}: {e}")
        return tool_error(f"Error listing cells for report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def modify_report_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    cell_number: int,
    content: str,
) -> ModifyCellResult | ToolError:
    """Modify an existing cell's content in the backend.

    Currently only supports modifying markdown cells. Use cell_number from
    list_report_cells() to identify which cell to modify.

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID containing the cell (from create_report result or thread context artifacts)
        cell_number: Cell position (1-indexed)
        content: New markdown content for the cell

    Returns:
        ModifyCellResult with confirmation

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    try:
        # Get the current cell to preserve cell_id
        current_cell = ctx.deps.reports_backend.get_cell(
            report_id,
            cell_number
        )

        if current_cell.cell_type != "markdown":
            return tool_error(
                f"Can only modify markdown cells (cell {cell_number} is {current_cell.cell_type})"
            )

        # Create updated cell data
        from lineage.backends.reports.protocol import CellData

        updated_cell_data = CellData(
            cell_id=current_cell.cell_id,
            cell_type="markdown",
            cell_number=cell_number,
            data={"content": content},
        )

        # Modify in backend
        ctx.deps.reports_backend.modify_cell(
            report_id,
            cell_number,
            updated_cell_data
        )

        # Create result for frontend
        result = ModifyCellResult(
            report_id=report_id,
            cell_number=cell_number,
            message=f"Modified cell {cell_number}",
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Modified cell {cell_number} in report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error modifying cell {cell_number} in report {report_id}: {e}")
        return tool_error(f"Error modifying cell {cell_number} in report {report_id}: {e}")


@presentation_toolset.tool
@safe_tool
async def delete_report_cell(
    ctx: RunContext[AgentDeps],
    report_id: str,
    cell_number: int,
) -> DeleteCellResult | ToolError:
    """Delete a cell from a report in the backend.

    Subsequent cells will be automatically renumbered. Use cell_number from
    list_report_cells() to identify which cell to delete.

    Args:
        ctx: Runtime context with dependencies.
        report_id: Report ID containing the cell (from create_report result or thread context artifacts)
        cell_number: Cell position (1-indexed)

    Returns:
        DeleteCellResult with confirmation

    """
    if not ctx.deps.reports_backend:
        return tool_error("No reports backend configured")

    try:
        # Delete from backend (automatically renumbers subsequent cells)
        ctx.deps.reports_backend.delete_cell(
            report_id,
            cell_number
        )

        # Create result for frontend
        result = DeleteCellResult(
            report_id=report_id,
            cell_number=cell_number,
            message=f"Deleted cell {cell_number} (subsequent cells renumbered)",
        )

        # Store in tool_results for frontend rendering
        tool_call_id = ctx.tool_call_id or "unknown"
        ctx.deps.state.tool_results[tool_call_id] = result

        # Update active_reports state (triggers automatic state_update event)
        _update_report_state(ctx, report_id)

        logger.info(f"Deleted cell {cell_number} from report {report_id}")
        return result
    except Exception as e:
        logger.error(f"Error deleting cell {cell_number} from report {report_id}: {e}")
        return tool_error(f"Error deleting cell {cell_number} from report {report_id}: {e}")


def generate_standalone_html(report) -> str:
    """Generate a standalone HTML file with embedded report data.

    The HTML includes:
    - typedef.ai styling
    - Embedded cell data as JSON
    - Client-side JavaScript to render charts (using Chart.js or similar)
    - Print-optimized CSS

    Args:
        report: Report object from backend

    Returns:
        HTML string
    """
    import json

    # Convert cells to JSON for embedding
    # Use model_dump to get full cell structure (not just .data payload)
    cells_json = json.dumps([cell.model_dump() for cell in report.cells], indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{report.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
    <style>
        /* typedef.ai Design System */
        :root {{
            --bg-primary: #111111;
            --bg-card: rgba(17, 17, 17, 0.8);
            --border-light: rgba(130, 157, 243, 0.3);
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --analyst-color: #829df3;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            margin: 0;
            padding: 20px;
            line-height: 1.6;
        }}

        .report-container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        .report-header {{
            margin-bottom: 40px;
            border-bottom: 1px solid var(--border-light);
            padding-bottom: 20px;
        }}

        .report-title {{
            font-size: 32px;
            font-weight: 600;
            margin: 0 0 10px 0;
        }}

        .report-meta {{
            color: var(--text-secondary);
            font-size: 14px;
        }}

        .cell {{
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            page-break-inside: avoid;
        }}

        .cell-markdown {{
            /* Markdown-specific styles */
        }}

        .cell-markdown h1, .cell-markdown h2, .cell-markdown h3 {{
            color: var(--analyst-color);
            margin-top: 0;
        }}

        .cell-chart {{
            /* Chart-specific styles */
        }}
        .cell-mermaid {{
            /* Mermaid-specific styles */
        }}

        .mermaid-diagram {{
            background: rgba(15, 15, 15, 0.6);
            border: 1px solid rgba(130, 157, 243, 0.2);
            border-radius: 8px;
            padding: 12px;
            overflow-x: auto;
        }}


        .cell-chart h3 {{
            color: var(--analyst-color);
            margin-top: 0;
            margin-bottom: 20px;
        }}

        .chart-wrapper {{
            position: relative;
            width: 100%;
            height: 400px;
            margin: 20px 0;
        }}

        .chart-canvas {{
            width: 100% !important;
            height: 100% !important;
        }}

        .cell-table {{
            /* Table-specific styles */
        }}

        .cell-table h3 {{
            color: var(--analyst-color);
            margin-top: 0;
            margin-bottom: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}

        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border-light);
        }}

        th {{
            background: rgba(130, 157, 243, 0.1);
            color: var(--analyst-color);
            font-weight: 600;
        }}

        /* Print Styles */
        @media print {{
            body {{
                background: white;
                color: black;
            }}

            .cell {{
                page-break-inside: avoid;
                border: 1px solid #ccc;
                margin-bottom: 20px;
            }}

            .chart-wrapper {{
                height: 400px;
                page-break-inside: avoid;
            }}

            .chart-canvas {{
                width: 100% !important;
                height: 100% !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <h1 class="report-title">{report.title}</h1>
            <div class="report-meta">
                Generated: {report.created_at.strftime("%Y-%m-%d %H:%M:%S")} | {len(report.cells)} cells
            </div>
        </div>

        <div id="cells-container"></div>
    </div>

    <script>
        // Embedded report data
        const reportCells = {cells_json};

        // Render cells
        const container = document.getElementById('cells-container');

        reportCells.forEach((cell, index) => {{
            const cellDiv = document.createElement('div');
            cellDiv.className = `cell cell-${{cell.cell_type}}`;

            // Access nested data field
            const cellData = cell.data;

            if (cell.cell_type === 'markdown') {{
                cellDiv.innerHTML = marked.parse(cellData.content);
            }}
            else if (cell.cell_type === 'chart') {{
                const title = document.createElement('h3');
                title.textContent = cellData.title;
                cellDiv.appendChild(title);

                // Create wrapper div for height containment
                const wrapper = document.createElement('div');
                wrapper.className = 'chart-wrapper';

                const canvas = document.createElement('canvas');
                canvas.className = 'chart-canvas';
                canvas.id = `chart-${{index}}`;
                wrapper.appendChild(canvas);
                cellDiv.appendChild(wrapper);

                // Render chart after DOM update
                setTimeout(() => {{
                    renderChart(canvas, cellData);
                }}, 0);
            }}
            else if (cell.cell_type === 'table') {{
                if (cellData.title) {{
                    const title = document.createElement('h3');
                    title.textContent = cellData.title;
                    cellDiv.appendChild(title);
                }}

                const table = document.createElement('table');
                const thead = document.createElement('thead');
                const tbody = document.createElement('tbody');

                // Headers
                const headerRow = document.createElement('tr');
                cellData.columns.forEach(col => {{
                    const th = document.createElement('th');
                    th.textContent = col;
                    headerRow.appendChild(th);
                }});
                thead.appendChild(headerRow);

                // Rows
                cellData.data.forEach(row => {{
                    const tr = document.createElement('tr');
                    cellData.columns.forEach(col => {{
                        const td = document.createElement('td');
                        td.textContent = row[col];
                        tr.appendChild(td);
                    }});
                    tbody.appendChild(tr);
                }});

                table.appendChild(thead);
                table.appendChild(tbody);
                cellDiv.appendChild(table);
            }}
            else if (cell.cell_type === 'mermaid') {{
                if (cellData.title) {{
                    const title = document.createElement('h3');
                    title.textContent = cellData.title;
                    cellDiv.appendChild(title);
                }}

                if (cellData.description) {{
                    const desc = document.createElement('p');
                    desc.textContent = cellData.description;
                    cellDiv.appendChild(desc);
                }}

                const diagramContainer = document.createElement('div');
                diagramContainer.className = 'mermaid-diagram';
                diagramContainer.id = `mermaid-diagram-${{index}}`;
                cellDiv.appendChild(diagramContainer);

                setTimeout(() => {{
                    renderMermaidDiagram(diagramContainer, cellData.diagram);
                }}, 0);
            }}

            container.appendChild(cellDiv);
        }});

        // Chart rendering function
        // cellData is already the nested data object (not the full cell)
        function renderChart(canvas, cellData) {{
            const ctx = canvas.getContext('2d');

            // Prepare data for Chart.js
            const labels = cellData.data.map(row => row[cellData.x_column]);
            const values = cellData.data.map(row => row[cellData.y_column]);

            const chartType = cellData.chart_type === 'bar' ? 'bar' :
                             cellData.chart_type === 'line' ? 'line' :
                             cellData.chart_type === 'scatter' ? 'scatter' :
                             cellData.chart_type === 'pie' ? 'pie' : 'bar';

            new Chart(ctx, {{
                type: chartType,
                data: {{
                    labels: labels,
                    datasets: [{{
                        label: cellData.y_column,
                        data: values,
                        backgroundColor: 'rgba(130, 157, 243, 0.6)',
                        borderColor: 'rgba(130, 157, 243, 1)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        title: {{
                            display: false
                        }},
                        legend: {{
                            display: false
                        }}
                    }}
                }}
            }});
        }}
        async function renderMermaidDiagram(container, diagram) {{
            if (!diagram) {{
                container.innerHTML = '<div style="color:#ff7676;">Mermaid diagram content missing.</div>';
                return;
            }}

            if (typeof mermaid === 'undefined') {{
                container.innerHTML = '<div style="color:#ff7676;">Mermaid library not loaded.</div>';
                return;
            }}

            try {{
                mermaid.initialize({{
                    startOnLoad: false,
                    securityLevel: "strict",
                    theme: "dark",
                    flowchart: {{
                        htmlLabels: false
                    }},
                }});

                const id = `mermaid-export-${{Math.random().toString(36).slice(2)}}`;
                const {{ svg }} = await mermaid.render(id, diagram);
                container.innerHTML = svg;
            }} catch (error) {{
                console.error("Failed to render mermaid diagram", error);
                container.innerHTML = '<div style="color:#ff7676;">Unable to render mermaid diagram.</div>';
            }}
        }}
    </script>
</body>
</html>
"""
    return html