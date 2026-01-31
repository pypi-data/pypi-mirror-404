"""ArtifactViewer widget for displaying tool outputs.

The main container widget that manages artifact display and history.
"""
import logging
import math
import re
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from lineage.tui.screens.chat import RunStats

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.widgets import (
    Button,
    DataTable,
    Label,
    ListItem,
    ListView,
    Markdown,
    Static,
    TabbedContent,
    TabPane,
)

from lineage.backends.reports.protocol import CellData
from lineage.tui.widgets.artifacts.artifact_types import (
    ArtifactData,
    ClickableMarkdown,
    ExportReportRequest,
)
from lineage.tui.widgets.artifacts.cell_renderers import (
    _render_cell,
    _render_chart_cell,
    _render_mermaid_cell,
)
from lineage.tui.widgets.artifacts.formatters import (
    _format_lineage_node_card,
    _format_node_card,
)
from lineage.tui.widgets.artifacts.helpers import (
    _create_temp_dir,
    _detect_display_type,
    _escape_markdown,
    _get_short_name,
    _get_type_icon,
    _group_nodes_by_type,
    _render_as_table,
    _truncate,
)

logger = logging.getLogger(__name__)


class ArtifactViewer(Container):
    """Container for displaying artifacts (tables, charts, reports) with history."""

    def __init__(self):
        """Initialize the artifact viewer."""
        super().__init__(id="artifact-viewer")
        self.reports: List[ArtifactData] = []
        self.activities: List[ArtifactData] = []  # All non-report artifacts + run summaries

        self.title = Label("Artifact Preview", id="artifact-title")
        self.report_list = ListView(id="report-list")
        self.activity_list = ListView(id="activity-list")
        self.content_area = VerticalScroll(id="artifact-content")

        # Index for quick artifact lookup by ID
        self._artifact_index: Dict[str, ArtifactData] = {}

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield self.title
        with Horizontal(id="artifact-split-view"):
            with Vertical(id="artifact-sidebar"):
                with TabbedContent(initial="activity"):
                    with TabPane("Activity", id="activity"):
                        yield self.activity_list
                    with TabPane("Reports", id="reports"):
                        yield self.report_list
            yield self.content_area

    def on_list_view_selected(self, event: ListView.Selected):
        """Handle artifact selection."""
        # Determine which list triggered the event
        if event.list_view.id == "activity-list":
            source_list = self.activities
        else:
            source_list = self.reports

        if not source_list:
            return

        index = event.list_view.index
        if index is not None and 0 <= index < len(source_list):
            self._render_artifact(source_list[index])

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses, including Export HTML button."""
        button_id = event.button.id or ""
        if button_id.startswith("export-report-"):
            # Get report_id and artifact_id from button attributes
            report_id = getattr(event.button, "report_id", None)
            artifact_id = getattr(event.button, "artifact_id", None)
            if report_id and artifact_id:
                # Emit export request message to be handled by AgentChat
                self.post_message(ExportReportRequest(report_id, artifact_id))
            event.stop()

    def _add_artifact(self, artifact: ArtifactData) -> str:
        """Add artifact to history and display it.

        Returns:
            The artifact ID
        """
        # Determine target list based on artifact type
        # Reports go to Reports tab, everything else goes to Activity tab
        if artifact.type == "report":
            target_list = self.reports
            target_view = self.report_list
        else:
            # All non-report artifacts (queries, charts, activity summaries, etc.)
            target_list = self.activities
            target_view = self.activity_list

        # Check for existing artifact to update (for reports mainly)
        existing_index = -1
        if artifact.type == "report":
            for i, existing in enumerate(target_list):
                # Check if it's the same report ID (fuzzy match on title or ID)
                existing_id = existing.data.get("title")
                new_id = artifact.data.get("title")
                if existing_id and new_id and existing_id == new_id:
                    existing_index = i
                    break

        icon = {
            "table": "📊",
            "chart": "📈",
            "report": "📄",
            "mermaid": "🔀",
            "graph": "🔍",
            "lineage": "🌳",
            "activity": "⚡",
            "command": "🧰",
        }.get(artifact.type, "📦")

        display_title = artifact.title
        title_widget = Static(f"{icon} {display_title}", classes="history-title")

        # Add to index for quick lookup
        self._artifact_index[artifact.id] = artifact

        if existing_index >= 0:
            # Update existing
            old_artifact = target_list[existing_index]
            if old_artifact.id in self._artifact_index:
                del self._artifact_index[old_artifact.id]
            target_list[existing_index] = artifact
            self._artifact_index[artifact.id] = artifact
            # Re-render if selected
            if target_view.index == existing_index:
                self._render_artifact(artifact)
        else:
            # Add new
            target_list.append(artifact)
            target_view.append(ListItem(title_widget))

            # Select in list (harmless - just updates list selection)
            new_index = len(target_list) - 1
            target_view.index = new_index

            # Determine which tab this artifact belongs to (only 2 tabs now)
            artifact_tab = "reports" if artifact.type == "report" else "activity"

            # Get currently active tab
            try:
                tabbed_content = self.query_one(TabbedContent)
                active_tab = tabbed_content.active
            except NoMatches:
                active_tab = "activity"  # Default fallback

            # Only auto-render if user is on this artifact's tab (preserves user's current view)
            # Activity summaries don't auto-render (user can click to see them)
            if artifact.type != "activity" and artifact_tab == active_tab:
                self._render_artifact(artifact)

        return artifact.id

    def select_artifact_by_id(self, artifact_id: str) -> bool:
        """Select and display an artifact by its ID.

        Args:
            artifact_id: The ID of the artifact to select

        Returns:
            True if artifact was found and selected, False otherwise
        """
        artifact = self._artifact_index.get(artifact_id)
        if not artifact:
            return False

        # Find which list contains this artifact and select it
        if artifact.type == "report":
            target_list = self.reports
            target_view = self.report_list
        else:
            # All non-report artifacts are in the activity list
            target_list = self.activities
            target_view = self.activity_list

        try:
            index = target_list.index(artifact)
            target_view.index = index
            self._render_artifact(artifact)
            return True
        except ValueError:
            return False

    def _render_artifact(self, artifact: ArtifactData):
        """Render the specified artifact in the content area."""
        self.title.update(f"{artifact.title}")
        self.content_area.remove_children()

        try:
            artifact.render_func(self, artifact.data)
        except Exception as e:
            logger.error(f"Error rendering artifact: {e}")
            self.content_area.mount(Label(f"❌ Error displaying artifact: {e}", classes="error-label"))

    def update_report_cells(self, artifact_id: str, cells: List[CellData]) -> bool:
        """Update an existing report artifact with new cells.

        Args:
            artifact_id: The ID of the report artifact to update
            cells: The updated list of CellData models

        Returns:
            True if updated successfully, False if artifact not found
        """
        artifact = self._artifact_index.get(artifact_id)
        if not artifact:
            return False

        artifact.data["cells"] = cells

        # Only re-render if user is on Reports tab (don't steal focus from other tabs)
        try:
            tabbed_content = self.query_one(TabbedContent)
            if tabbed_content.active == "reports":
                self._render_artifact(artifact)
        except NoMatches:
            # Fallback: render anyway if we can't determine tab
            self._render_artifact(artifact)
        return True

    def update_report_html_path(self, artifact_id: str, html_path: str) -> bool:
        """Update an existing report artifact with HTML export path.

        Args:
            artifact_id: The ID of the report artifact to update
            html_path: Path to the exported HTML file

        Returns:
            True if updated successfully, False if artifact not found
        """
        artifact = self._artifact_index.get(artifact_id)
        if not artifact:
            return False

        artifact.data["html_path"] = html_path

        # Only re-render if user is on Reports tab
        try:
            tabbed_content = self.query_one(TabbedContent)
            if tabbed_content.active == "reports":
                self._render_artifact(artifact)
        except NoMatches:
            self._render_artifact(artifact)
        return True

    def mark_report_ready(self, artifact_id: str) -> bool:
        """Mark a report as ready for export (shows the Export button).

        Call this when the agent run completes to enable the Export HTML button.

        Args:
            artifact_id: The ID of the report artifact

        Returns:
            True if updated successfully, False if artifact not found
        """
        artifact = self._artifact_index.get(artifact_id)
        if not artifact:
            return False

        artifact.data["is_ready"] = True

        # Only re-render if user is on Reports tab
        try:
            tabbed_content = self.query_one(TabbedContent)
            if tabbed_content.active == "reports":
                self._render_artifact(artifact)
        except NoMatches:
            self._render_artifact(artifact)
        return True

    # --- Public Methods called by AgentChat ---

    def show_table(
        self,
        title: str,
        columns: List[str],
        rows: List[List[Any]],
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a table artifact.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            table = DataTable()
            table.add_columns(*data["columns"])
            table.add_rows(data["rows"])
            viewer.content_area.mount(table)

        artifact_id = f"table-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="table",
                title=title,
                data={"columns": columns, "rows": rows},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_chart(
        self,
        title: str,
        chart_data: dict,
        chart_type: str,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a chart artifact with clickable link to open PNG.

        Generates PNG and shows data preview with link to open full image.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            # Create output directory for chart PNG
            output_dir = _create_temp_dir(prefix="chart_tui_")

            # Build cell data structure
            cell = {
                "cell_type": "chart",
                "data": {
                    "title": data["title"],
                    "chart_type": data["chart_type"],
                    "data": data["chart_data"].get("data", []),
                    "x_column": data["chart_data"].get("x_column"),
                    "y_column": data["chart_data"].get("y_column"),
                },
            }

            # Render using cell renderer
            content = _render_chart_cell(cell, output_dir)
            viewer.content_area.mount(ClickableMarkdown(content, classes="chart-artifact"))

        artifact_id = f"chart-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="chart",
                title=title,
                data={"title": title, "chart_data": chart_data, "chart_type": chart_type},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_command_output(
        self,
        title: str,
        command: str,
        working_dir: str,
        exit_code: int,
        stdout: str,
        stderr: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display CLI command output (bash/dbt) with stdout/stderr."""

        def render(viewer, data):
            def _wrap_code_block(text: str) -> list[str]:
                """Wrap text in a safe code fence that won't be closed by content."""
                backtick_runs = re.findall(r"`+", text)
                max_ticks = max((len(run) for run in backtick_runs), default=0)
                fence = "`" * max(3, max_ticks + 1)
                return [fence, text, fence]

            content_parts = [f"# {data['title']}", ""]
            content_parts.append(f"**Command:** `{_escape_markdown(data['command'])}`")
            content_parts.append(f"**Working Dir:** `{_escape_markdown(data['working_dir'])}`")
            status = "✅ success" if data["exit_code"] == 0 else f"❌ exit {data['exit_code']}"
            content_parts.append(f"**Status:** {status}")
            content_parts.append("")

            stdout_text = data.get("stdout") or ""
            stderr_text = data.get("stderr") or ""

            content_parts.append("## Stdout")
            content_parts.append("")
            if stdout_text.strip():
                content_parts.extend(_wrap_code_block(stdout_text))
            else:
                content_parts.append("*No stdout*")
            content_parts.append("")

            if stderr_text.strip():
                content_parts.append("## Stderr")
                content_parts.append("")
                content_parts.extend(_wrap_code_block(stderr_text))
                content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="command-output"))

        artifact_id = f"command-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="command",
                title=title,
                data={
                    "title": title,
                    "command": command,
                    "working_dir": working_dir,
                    "exit_code": exit_code,
                    "stdout": stdout,
                    "stderr": stderr,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_graph_result(
        self,
        title: str,
        nodes: List[Any],
        query_description: str = "",
        display_hint: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display graph query results with smart rendering based on structure.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            nodes_data = data.get("nodes", [])
            desc = data.get("description", "")
            hint = data.get("display_hint")

            content_parts = [f"# {data['title']}"]
            content_parts.append("")

            if desc:
                content_parts.append(f"*{_escape_markdown(desc)}*")
                content_parts.append("")

            if not nodes_data:
                content_parts.append("*No results*")
                viewer.content_area.mount(Markdown("\n".join(content_parts)))
                return

            # Detect display type
            display_type = hint or _detect_display_type(nodes_data)

            if display_type == "scalar":
                # Single value display
                if len(nodes_data) == 1 and isinstance(nodes_data[0], dict):
                    for k, v in nodes_data[0].items():
                        content_parts.append(f"**{k}:** {v}")
                        content_parts.append("")
            elif display_type == "table":
                # Table view for aggregations/projections
                content_parts.append(_render_as_table(nodes_data))
                content_parts.append("")
            else:  # cards (default)
                # Current behavior - typed cards
                content_parts.append(f"**Found {len(nodes_data)} results**")
                content_parts.append("")
                by_type = _group_nodes_by_type(nodes_data)
                for node_type, items in by_type.items():
                    icon = _get_type_icon(node_type)
                    content_parts.append(f"- {icon} **{node_type}**: {len(items)}")
                content_parts.append("")
                content_parts.append("---")
                content_parts.append("")

                max_cards = 10
                cards_rendered = 0
                for node in nodes_data:
                    if cards_rendered >= max_cards:
                        remaining = len(nodes_data) - max_cards
                        if remaining > 0:
                            content_parts.append(f"*... and {remaining} more*")
                        break
                    if isinstance(node, dict):
                        content_parts.append(_format_node_card(node))
                        content_parts.append("---")
                        content_parts.append("")
                        cards_rendered += 1

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="graph-result"))

        artifact_id = f"graph-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="graph",
                title=title,
                data={"title": title, "nodes": nodes, "description": query_description, "display_hint": display_hint},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_lineage(
        self,
        title: str,
        root: str,
        nodes: List[Any],
        direction: str,
        query_description: str = "",
        hops: Optional[List[Any]] = None,
        edges: Optional[List[Any]] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display lineage as a structured tree view.

        Args:
            title: Title for the lineage display
            root: Root node identifier
            nodes: List of LineageOverviewNode dicts (lightweight, with semantic_summary)
            direction: Direction of lineage traversal
            query_description: Human-readable description
            hops: Column lineage hops (for column lineage only)
            edges: List of LineageRelationship dicts (from_id, to_id, edge_type)
            tool_call_id: Optional tool call ID for state tracking

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            root_id = data["root"]
            nodes_data = data["nodes"]
            dir_type = data["direction"]
            desc = data.get("description", "")
            hops = data.get("hops") or []
            edges = data.get("edges") or []

            content_parts = [f"# Lineage: {_escape_markdown(root_id)}", ""]

            if desc:
                content_parts.append(f"*{_escape_markdown(desc)}*")
                content_parts.append("")

            content_parts.append(f"**Direction:** {dir_type}")
            content_parts.append(f"**Found {len(nodes_data)} nodes, {len(edges)} edges**")
            content_parts.append("")

            # Hop summary (for column lineage)
            if hops:
                transforms = []
                for hop in hops:
                    if isinstance(hop, dict):
                        transforms.extend([str(t) for t in hop.get("transformations", [])])
                unique_transforms = []
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
                    content_parts.append(f"{idx}. `{from_id}` → `{to_id}`  via {t_str}")
                content_parts.append("")

            # Node type summary
            by_type = _group_nodes_by_type(nodes_data)
            for node_type, items in by_type.items():
                icon = _get_type_icon(node_type)
                content_parts.append(f"- {icon} **{node_type}**: {len(items)}")
            content_parts.append("")

            # Show dependency edges (for relation lineage)
            if edges:
                content_parts.append("### Dependencies")
                depends_on = [e for e in edges if isinstance(e, dict) and e.get("edge_type") == "DEPENDS_ON"]
                builds = [e for e in edges if isinstance(e, dict) and e.get("edge_type") == "BUILDS"]

                if depends_on:
                    for edge in depends_on[:15]:  # Limit to 15 edges
                        from_name = _get_short_name(edge.get("from_id", "?"))
                        to_name = _get_short_name(edge.get("to_id", "?"))
                        content_parts.append(f"  `{from_name}` → `{to_name}`")
                    if len(depends_on) > 15:
                        content_parts.append(f"  *... and {len(depends_on) - 15} more dependencies*")

                if builds:
                    content_parts.append("")
                    content_parts.append("### Builds (Logical → Physical)")
                    for edge in builds[:10]:
                        from_name = _get_short_name(edge.get("from_id", "?"))
                        to_name = _get_short_name(edge.get("to_id", "?"))
                        content_parts.append(f"  `{from_name}` ⟶ `{to_name}`")
                    if len(builds) > 10:
                        content_parts.append(f"  *... and {len(builds) - 10} more builds*")

                content_parts.append("")

            content_parts.append("---")
            content_parts.append("")

            # Show hop-level transformations if available (for column lineage)
            if hops:
                content_parts.append("### Transformations")
                for hop in hops:
                    if not isinstance(hop, dict):
                        continue
                    from_id = hop.get("from_id") or "?"
                    to_id = hop.get("to_id") or "?"
                    transforms = hop.get("transformations") or []
                    if transforms:
                        t_str = ", ".join(str(t) for t in transforms)
                    else:
                        t_str = "DERIVES_FROM"
                    content_parts.append(f"- `{from_id}` → `{to_id}` : {t_str}")
                content_parts.append("")

            # Node cards with semantic summaries
            max_cards = 10
            cards_rendered = 0
            for node in nodes_data:
                if cards_rendered >= max_cards:
                    remaining = len(nodes_data) - max_cards
                    if remaining > 0:
                        content_parts.append(
                            f"*... and {remaining} more nodes (use get_model_details for specifics)*"
                        )
                    break
                if isinstance(node, dict):
                    content_parts.append(_format_lineage_node_card(node))
                    content_parts.append("---")
                    content_parts.append("")
                    cards_rendered += 1

            viewer.content_area.mount(
                Markdown("\n".join(content_parts), classes="lineage-result")
            )

        artifact_id = f"lineage-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="lineage",
                title=title,
                data={
                    "title": title,
                    "root": root,
                    "nodes": nodes,
                    "direction": direction,
                    "description": query_description,
                    "hops": hops or [],
                    "edges": edges or [],
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_model_details(
        self,
        title: str,
        model_details: Dict[str, Any],
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display detailed model information from get_model_details.

        Args:
            title: Title for the display
            model_details: ModelDetailsResult as dict
            tool_call_id: Optional tool call ID for state tracking

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            details = data["model_details"]
            content_parts = [f"# {_escape_markdown(details.get('model_name', 'Model'))}"]
            content_parts.append("")

            # Basic info
            if details.get("description"):
                content_parts.append(f"*{_escape_markdown(details['description'])}*")
                content_parts.append("")

            mat = details.get("materialization", "model")
            path = details.get("original_path", "")
            content_parts.append(f"**Materialization:** {mat}")
            if path:
                content_parts.append(f"**Path:** `{path}`")
            content_parts.append("")

            # Semantic analysis section
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

                # Measures
                measures = details.get("measures") or []
                if measures:
                    content_parts.append("### Measures")
                    for m in measures:
                        name = m.get("name", "?")
                        expr = m.get("expr", "")
                        agg = m.get("agg_function", "")
                        content_parts.append(f"- **{name}**: `{expr}` ({agg})")
                    content_parts.append("")

                # Dimensions
                dimensions = details.get("dimensions") or []
                if dimensions:
                    content_parts.append("### Dimensions")
                    for d in dimensions:
                        name = d.get("name", "?")
                        source = d.get("source", "")
                        pii = " ⚠ PII" if d.get("is_pii") else ""
                        content_parts.append(f"- **{name}**{pii} (from: {source})")
                    content_parts.append("")

                # Facts
                facts = details.get("facts") or []
                if facts:
                    content_parts.append("### Facts")
                    for f in facts:
                        name = f.get("name", "?")
                        source = f.get("source", "")
                        content_parts.append(f"- **{name}** (from: {source})")
                    content_parts.append("")

            # Columns section
            columns = details.get("columns") or []
            if columns:
                content_parts.append("## Columns")
                content_parts.append("")
                for col in columns[:20]:  # Limit to 20 columns
                    name = col.get("name", "?")
                    dtype = col.get("data_type", "")
                    desc = col.get("description", "")
                    dtype_str = f" `{dtype}`" if dtype else ""
                    desc_str = f" - {_truncate(desc, 50)}" if desc else ""
                    content_parts.append(f"- **{name}**{dtype_str}{desc_str}")
                if len(columns) > 20:
                    content_parts.append(f"*... and {len(columns) - 20} more columns*")
                content_parts.append("")

            # Macros section
            macros = details.get("macros") or []
            if macros:
                content_parts.append("## Macro Dependencies")
                content_parts.append("")
                for macro in macros[:15]:
                    name = macro.get("name", "?")
                    pkg = macro.get("package_name", "")
                    pkg_str = f" ({pkg})" if pkg else ""
                    content_parts.append(f"- `{name}`{pkg_str}")
                if len(macros) > 15:
                    content_parts.append(f"*... and {len(macros) - 15} more macros*")
                content_parts.append("")

            # SQL section (if included)
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

            viewer.content_area.mount(
                Markdown("\n".join(content_parts), classes="model-details")
            )

        artifact_id = f"model-details-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="model_details",
                title=title,
                data={"model_details": model_details},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_report(
        self,
        title: str,
        report_path: Optional[str] = None,
        message: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a simple report artifact (path optional).

        For cellular reports with multiple cell types, use show_report_cells().

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            msg_lines = ["# Report", ""]
            if data.get("title"):
                msg_lines.append(f"**Title:** {data['title']}")
            if data.get("report_path"):
                msg_lines.append(f"**Path:** `{data['report_path']}`")
                msg_lines.append("")
                msg_lines.append(
                    f"[Open in Browser]({data['report_path']})"
                )
            elif data.get("message"):
                msg_lines.append(data["message"])

            viewer.content_area.mount(
                ClickableMarkdown("\n".join(msg_lines), classes="report-output")
            )

        artifact_id = f"report-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="report",
                title=title or "Report",
                data={
                    "title": title,
                    "report_path": report_path,
                    "message": message,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_report_cells(
        self,
        title: str,
        report_id: str,
        cells: List[CellData],
        html_path: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a full cellular report with all cell types.

        Renders each cell type appropriately:
        - markdown: Native Rich markdown
        - table: Markdown table format
        - chart: Title + data preview + clickable link to PNG
        - mermaid: Source + mermaid.live link + clickable PNG link

        Args:
            title: Report title
            report_id: Unique report identifier
            cells: List of CellData Pydantic models
            html_path: Optional path to HTML export for "Open in Browser"
            tool_call_id: Optional tool call ID for linking

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            # Create output directory for any generated PNGs
            output_dir = _create_temp_dir(prefix="report_tui_")

            # Add Export button only when report is ready (has cells and is_ready flag)
            # Use unique ID each render to avoid Textual widget ID collision
            if data.get("is_ready") and not data.get("html_path") and data.get("report_id"):
                btn_id = f"export-report-{uuid.uuid4().hex[:8]}"
                export_btn = Button(
                    "Export HTML",
                    id=btn_id,
                    variant="primary",
                    classes="export-btn",
                )
                # Store report_id and artifact_id on the button for the click handler
                export_btn.report_id = data["report_id"]
                export_btn.artifact_id = data.get("artifact_id")
                viewer.content_area.mount(export_btn)

            parts = []

            # Header with title
            parts.append(f"# {data['title']}")
            parts.append("")

            # Open in Browser link if HTML path provided
            if data.get("html_path"):
                parts.append(f"[Open Full Report in Browser]({data['html_path']})")
                parts.append("")

            parts.append("---")
            parts.append("")

            # Render each cell
            for cell in data.get("cells", []):
                cell_content = _render_cell(cell, output_dir)
                parts.append(cell_content)
                parts.append("")
                parts.append("---")
                parts.append("")

            viewer.content_area.mount(
                ClickableMarkdown("\n".join(parts), classes="report-cells")
            )

        artifact_id = f"report-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="report",
                title=title or "Report",
                data={
                    "title": title,
                    "report_id": report_id,
                    "cells": cells,
                    "html_path": html_path,
                    "artifact_id": artifact_id,  # Include for export button
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_mermaid(
        self,
        title: str,
        diagram: str,
        description: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a Mermaid diagram artifact with clickable links.

        Shows mermaid.live link and optional PNG link. Click to open externally.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            diagram_text = data["diagram"]
            desc = data.get("description", "")

            # Create output directory for mermaid PNG
            output_dir = _create_temp_dir(prefix="mermaid_tui_")

            parts = []

            # Add description if present
            if desc:
                parts.append(f"*{desc}*")
                parts.append("")

            # Build cell data structure
            cell = {
                "cell_type": "mermaid",
                "data": {
                    "title": data["title"],
                    "diagram": diagram_text,
                },
            }

            # Render using cell renderer
            cell_content = _render_mermaid_cell(cell, output_dir)
            parts.append(cell_content)

            viewer.content_area.mount(ClickableMarkdown("\n".join(parts), classes="mermaid-artifact"))

        artifact_id = f"mermaid-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="mermaid",
                title=title,
                data={"title": title, "diagram": diagram, "description": description},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_search_results(
        self,
        search_term: str,
        results: List[Any],
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display fuzzy search results with match scores.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            term = data["term"]
            items = data["results"]

            content_parts = [f'# 🔎 Search: "{term}"']
            content_parts.append("")

            if not items:
                content_parts.append("*No matches found*")
            else:
                # Normalize scores 0-100 within this result set
                raw_scores = [item.get("score", 0) or 0 for item in items]
                max_score = max(raw_scores) if raw_scores else 0

                for i, item in enumerate(items[:10], 1):
                    raw_score = item.get("score", 0) or 0
                    norm_score = 0
                    if max_score > 0:
                        norm_score = int(round((raw_score / max_score) * 100))
                    stars = "⭐" * math.ceil(norm_score / 20.0)
                    name = item.get("name", "Unknown")
                    model_id = item.get("id", "")
                    # Put raw score in hover tooltip via markdown link title
                    name_with_tooltip = f'[{name}](# "raw score: {raw_score}")'
                    content_parts.append(f"**{i}. {stars} {name_with_tooltip}** ({norm_score})")
                    content_parts.append("")
                    content_parts.append(f"`{model_id}`")
                    content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="search-results"))

        artifact_id = f"search-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="search",
                title=f"Search: {search_term}",
                data={"term": search_term, "results": results},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_model_semantics(
        self,
        model_id: str,
        model_name: str,
        grain: str,
        intent: str,
        measures: List,
        dimensions: List,
        facts: List,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display model semantic analysis.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            content_parts = [f"## 🧠 {data['name']}"]
            content_parts.append("")

            if data.get("grain"):
                content_parts.append(f"**Grain:** {data['grain']}")
                content_parts.append("")
            if data.get("intent"):
                content_parts.append(f"**Intent:** {data['intent']}")
                content_parts.append("")

            measures_data = data.get("measures", [])
            if measures_data:
                content_parts.append(f"📏 **Measures** ({len(measures_data)}):")
                content_parts.append("")
                for m in measures_data[:10]:
                    if isinstance(m, dict):
                        name = m.get("name", "?")
                        agg = m.get("agg_function", "")
                        content_parts.append(f"- {name} ({agg})")
                content_parts.append("")

            dims_data = data.get("dimensions", [])
            if dims_data:
                content_parts.append(f"📐 **Dimensions** ({len(dims_data)}):")
                content_parts.append("")
                dim_names = [d.get("name") if isinstance(d, dict) else str(d) for d in dims_data[:15]]
                # Break into multiple lines for readability
                for i in range(0, len(dim_names), 5):
                    chunk = dim_names[i : i + 5]
                    content_parts.append(f"- {', '.join(chunk)}")
                content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="model-semantics"))

        artifact_id = f"semantics-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="semantics",
                title=f"Semantics: {model_name or model_id}",
                data={
                    "name": model_name or model_id,
                    "grain": grain,
                    "intent": intent,
                    "measures": measures,
                    "dimensions": dimensions,
                    "facts": facts,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_join_patterns(
        self,
        model_id: str,
        model_name: str,
        cluster_id: str,
        cluster_pattern: str,
        join_partners: List,
        join_edges: List,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display join patterns and cluster membership.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            name = data["name"]
            content_parts = [f"## 🔗 {name} - Joins", ""]

            if data.get("cluster_id"):
                content_parts.append(f"**Cluster:** {data['cluster_pattern']} (Cluster {data['cluster_id']})")
                content_parts.append("")

            partners = data.get("partners", [])
            if partners:
                content_parts.append("**Join Partners:**")
                for p in partners[:8]:
                    if isinstance(p, dict):
                        pname = p.get("name", "?")
                        content_parts.append(f"  • {pname}")
                content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="join-patterns"))

        artifact_id = f"joins-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="joins",
                title=f"Joins: {model_name or model_id}",
                data={
                    "name": model_name or model_id,
                    "cluster_id": cluster_id,
                    "cluster_pattern": cluster_pattern,
                    "partners": join_partners,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_impact_tree(
        self,
        model_id: str,
        model_name: str,
        affected_models: List,
        total: int,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display downstream impact as a clear list grouped by depth.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            name = data["name"]
            affected = data["affected"]
            total_count = data["total"]

            content_parts = [f"## 📉 Impact: {name}"]
            content_parts.append("")

            if total_count == 0:
                content_parts.append("*No downstream dependencies*")
            else:
                content_parts.append(f"**Affects {total_count} models:**")
                content_parts.append("")

                # Group by depth
                by_depth = {}
                for m in affected:
                    depth = m.get("depth", 0)
                    by_depth.setdefault(depth, []).append(m)

                # Direct dependents (depth 1)
                if 1 in by_depth:
                    content_parts.append("**Direct:**")
                    content_parts.append("")
                    for m in by_depth[1][:10]:
                        mname = m.get("name", "?")
                        content_parts.append(f"- {mname}")
                    if len(by_depth[1]) > 10:
                        content_parts.append(f"- *(... and {len(by_depth[1]) - 10} more)*")
                    content_parts.append("")

                # Indirect (depth 2+)
                deeper = []
                for depth in sorted(k for k in by_depth.keys() if k > 1):
                    deeper.extend(by_depth[depth])

                if deeper:
                    content_parts.append(f"**Indirect (depth 2+):** {len(deeper)} models")
                    content_parts.append("")
                    for m in deeper[:10]:
                        mname = m.get("name", "?")
                        mdepth = m.get("depth", "?")
                        content_parts.append(f"- {mname} (depth {mdepth})")
                    if len(deeper) > 10:
                        content_parts.append(f"- *(... and {len(deeper) - 10} more)*")
                    content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="impact-tree"))

        artifact_id = f"impact-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="impact",
                title=f"Impact: {model_name or model_id}",
                data={"name": model_name or model_id, "affected": affected_models, "total": total},
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_activity_summary(self, run_stats: "RunStats") -> str:
        """Display an activity summary for a completed run.

        Args:
            run_stats: RunStats object with run metrics

        Returns:
            The artifact ID
        """
        # Import here to avoid circular dependency
        from lineage.tui.screens.chat import RunStats as RunStatsType

        def render(viewer, data):
            stats: RunStatsType = data["stats"]
            content_parts = ["## ⚡ Activity Summary", ""]

            # Duration
            if stats.duration_seconds is not None:
                content_parts.append(f"**Duration:** {stats.duration_seconds:.1f}s")
            content_parts.append(f"**Tool Calls:** {stats.tool_call_count}")
            content_parts.append("")

            # Tool call list with durations
            if stats.tool_calls:
                content_parts.append("### Steps")
                content_parts.append("")
                for i, tc in enumerate(stats.tool_calls, 1):
                    duration_str = ""
                    if tc.duration_seconds is not None:
                        duration_str = f" ({tc.duration_seconds:.1f}s)"
                    # Show link indicator if artifact was created
                    link_indicator = " → 📎" if tc.artifact_id else ""
                    content_parts.append(f"{i}. {tc.display_text}{duration_str}{link_indicator}")
                content_parts.append("")

            # User query (truncated)
            if stats.user_message:
                truncated = stats.user_message[:100]
                if len(stats.user_message) > 100:
                    truncated += "..."
                content_parts.append(f"**Your question:** {truncated}")
                content_parts.append("")

            # Response stats
            if stats.response_char_count:
                content_parts.append(f"**Response:** {stats.response_char_count:,} chars")
                content_parts.append("")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="activity-summary"))

        # Create a short title from user message
        title_preview = run_stats.user_message[:30] if run_stats.user_message else "Run"
        if run_stats.user_message and len(run_stats.user_message) > 30:
            title_preview += "..."

        artifact_id = f"activity-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="activity",
                title=title_preview,
                data={"stats": run_stats},
                render_func=render,
            )
        )

    def show_ticket(
        self,
        ticket_id: str,
        title: str,
        status: str,
        priority: str,
        description: str = "",
        assigned_to: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a single ticket details artifact.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            content_parts = [f"## 🎫 {data['title']}", ""]

            # Status and priority badges
            status_icons = {
                "open": "🔵",
                "in_progress": "🟡",
                "in_review": "🟠",
                "done": "🟢",
                "closed": "⚫",
                "cancelled": "❌",
            }
            priority_icons = {
                "urgent": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
            }
            status_icon = status_icons.get(data["status"].lower(), "⚪")
            priority_icon = priority_icons.get(data["priority"].lower(), "⚪")

            content_parts.append(f"**ID:** `{data['ticket_id']}`")
            content_parts.append(f"**Status:** {status_icon} {data['status']}")
            content_parts.append(f"**Priority:** {priority_icon} {data['priority']}")
            if data.get("assigned_to"):
                content_parts.append(f"**Assigned to:** {data['assigned_to']}")
            if data.get("created_by"):
                content_parts.append(f"**Created by:** {data['created_by']}")
            if data.get("tags"):
                content_parts.append(f"**Tags:** {', '.join(data['tags'])}")
            content_parts.append("")

            if data.get("description"):
                content_parts.append("### Description")
                content_parts.append("")
                content_parts.append(data["description"])

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="ticket-details"))

        artifact_id = f"ticket-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="ticket",
                title=f"🎫 {title[:30]}{'...' if len(title) > 30 else ''}",
                data={
                    "ticket_id": ticket_id,
                    "title": title,
                    "status": status,
                    "priority": priority,
                    "description": description,
                    "assigned_to": assigned_to,
                    "created_by": created_by,
                    "tags": tags or [],
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_ticket_list(
        self,
        tickets: List[Dict[str, Any]],
        count: int,
        filter_info: Optional[str] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a list of tickets artifact.

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            tickets_data = data["tickets"]
            total_count = data["count"]
            filter_str = data.get("filter_info", "")

            content_parts = ["## 📋 Tickets", ""]

            if filter_str:
                content_parts.append(f"*Filtered by: {filter_str}*")
                content_parts.append("")

            content_parts.append(f"**Found:** {total_count} ticket{'s' if total_count != 1 else ''}")
            content_parts.append("")

            if not tickets_data:
                content_parts.append("*No tickets match the criteria*")
            else:
                # Status and priority icons
                status_icons = {
                    "open": "🔵",
                    "in_progress": "🟡",
                    "in_review": "🟠",
                    "done": "🟢",
                    "closed": "⚫",
                }
                priority_icons = {
                    "urgent": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🟢",
                }

                for t in tickets_data[:20]:  # Limit display to 20
                    t_id = t.get("id", "?")[:12]
                    t_title = t.get("title", "Untitled")[:50]
                    if len(t.get("title", "")) > 50:
                        t_title += "..."
                    t_status = t.get("status", "unknown")
                    t_priority = t.get("priority", "medium")
                    status_icon = status_icons.get(t_status.lower(), "⚪")
                    priority_icon = priority_icons.get(t_priority.lower(), "⚪")

                    content_parts.append(f"- {priority_icon}{status_icon} **{t_id}**: {t_title}")

                if len(tickets_data) > 20:
                    content_parts.append(f"- *... and {len(tickets_data) - 20} more*")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="ticket-list"))

        artifact_id = f"tickets-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="ticket_list",
                title=f"📋 {count} Ticket{'s' if count != 1 else ''}",
                data={
                    "tickets": tickets,
                    "count": count,
                    "filter_info": filter_info,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_todos(
        self,
        todos: List[Dict[str, Any]],
        summary: Optional[Dict[str, int]] = None,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a list of todos artifact.

        Args:
            todos: List of todo items (each with id, content, status, priority)
            summary: Optional summary dict with counts (total, pending, in_progress, completed)
            tool_call_id: Optional tool call ID for linking

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            todos_data = data["todos"]
            summary_data = data.get("summary")

            content_parts = ["## Todo List", ""]

            # Show summary if provided
            if summary_data:
                total = summary_data.get("total", len(todos_data))
                pending = summary_data.get("pending", 0)
                in_progress = summary_data.get("in_progress", 0)
                completed = summary_data.get("completed", 0)

                parts = []
                if pending > 0:
                    parts.append(f"{pending} pending")
                if in_progress > 0:
                    parts.append(f"{in_progress} in progress")
                if completed > 0:
                    parts.append(f"{completed} completed")

                if parts:
                    content_parts.append(f"**Summary:** {', '.join(parts)} ({total} total)")
                else:
                    content_parts.append(f"**Total:** {total}")
                content_parts.append("")

            if not todos_data:
                content_parts.append("*No todos*")
            else:
                # Status and priority icons
                status_icons = {
                    "pending": "O",
                    "in_progress": "*",
                    "completed": "X",
                }
                priority_icons = {
                    "high": "[!]",
                    "medium": "[-]",
                    "low": "[ ]",
                }

                for todo in todos_data:
                    todo_id = todo.get("id", "?")
                    content = todo.get("content", "Untitled")
                    status = todo.get("status", "pending")
                    priority = todo.get("priority", "medium")

                    status_icon = status_icons.get(status, "O")
                    priority_icon = priority_icons.get(priority, "[-]")

                    # Truncate long content
                    display_content = content
                    if len(display_content) > 60:
                        display_content = display_content[:60] + "..."

                    content_parts.append(f"- {priority_icon}{status_icon} **{todo_id}**: {display_content}")

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="todo-list"))

        # Generate title from summary if available
        if summary:
            total = summary.get("total", len(todos))
            pending = summary.get("pending", 0)
            in_progress = summary.get("in_progress", 0)
            parts = []
            if pending > 0:
                parts.append(f"{pending} pending")
            if in_progress > 0:
                parts.append(f"{in_progress} in progress")
            if completed := summary.get("completed", 0):
                parts.append(f"{completed} completed")
            title = f"Todos: {', '.join(parts)}" if parts else f"{total} Todo{'s' if total != 1 else ''}"
        else:
            count = len(todos)
            title = f"{count} Todo{'s' if count != 1 else ''}"

        artifact_id = f"todos-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="todo_list",
                title=title,
                data={
                    "todos": todos,
                    "summary": summary,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )

    def show_ticket_update(
        self,
        ticket_id: str,
        action: str,
        message: str,
        tool_call_id: Optional[str] = None,
    ) -> str:
        """Display a ticket update action artifact.

        Args:
            ticket_id: The ticket ID that was updated
            action: The action performed (e.g., "updated", "commented", "closed")
            message: Success message from the operation
            tool_call_id: Optional tool call ID for linking

        Returns:
            The artifact ID
        """

        def render(viewer, data):
            action_icons = {
                "created": "🎫",
                "updated": "🔄",
                "commented": "💬",
                "assigned": "👤",
                "closed": "✅",
                "reopened": "🔓",
            }
            icon = action_icons.get(data["action"].lower(), "📝")

            content_parts = [f"## {icon} Ticket {data['action'].title()}", ""]
            content_parts.append(f"**Ticket:** `{data['ticket_id']}`")
            content_parts.append("")
            content_parts.append(data["message"])

            viewer.content_area.mount(Markdown("\n".join(content_parts), classes="ticket-update"))

        artifact_id = f"ticket-action-{uuid.uuid4().hex[:8]}"
        return self._add_artifact(
            ArtifactData(
                id=artifact_id,
                type="ticket_update",
                title=f"Ticket {action}",
                data={
                    "ticket_id": ticket_id,
                    "action": action,
                    "message": message,
                },
                render_func=render,
                tool_call_id=tool_call_id,
            )
        )
