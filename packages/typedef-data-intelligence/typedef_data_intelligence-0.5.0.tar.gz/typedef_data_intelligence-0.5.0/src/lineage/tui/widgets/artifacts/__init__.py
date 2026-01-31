"""Artifact widgets for displaying tool outputs.

This module provides widgets for displaying various artifact types including
tables, charts, reports, lineage, and more in the TUI.
"""
from lineage.tui.widgets.artifacts.artifact_types import (
    ArtifactData,
    ClickableMarkdown,
    ExportReportRequest,
)
from lineage.tui.widgets.artifacts.builders import (
    build_graph_result_widget,
    build_impact_tree_widget,
    build_join_patterns_widget,
    build_lineage_widget,
    build_model_details_widget,
    build_plan_widget,
    build_search_results_widget,
    build_table_widget,
)
from lineage.tui.widgets.artifacts.cell_renderers import (
    _convert_mermaid_to_ascii,
    _render_cell,
    _render_chart_cell,
    _render_markdown_cell,
    _render_mermaid_cell,
    _render_table_cell,
)
from lineage.tui.widgets.artifacts.formatters import (
    TOOL_DISPLAY_INFO,
    _format_lineage_node_card,
    _format_node_card,
)
from lineage.tui.widgets.artifacts.helpers import (
    _create_temp_dir,
    _detect_display_type,
    _escape_markdown,
    _get_node_type,
    _get_short_name,
    _get_type_icon,
    _group_nodes_by_type,
    _render_as_table,
    _truncate,
)
from lineage.tui.widgets.artifacts.viewer import ArtifactViewer

__all__ = [
    # Main viewer class
    "ArtifactViewer",
    # Types
    "ArtifactData",
    "ClickableMarkdown",
    "ExportReportRequest",
    # Builders
    "build_graph_result_widget",
    "build_impact_tree_widget",
    "build_join_patterns_widget",
    "build_lineage_widget",
    "build_model_details_widget",
    "build_plan_widget",
    "build_search_results_widget",
    "build_table_widget",
    # Cell renderers
    "_convert_mermaid_to_ascii",
    "_render_cell",
    "_render_chart_cell",
    "_render_markdown_cell",
    "_render_mermaid_cell",
    "_render_table_cell",
    # Formatters
    "TOOL_DISPLAY_INFO",
    "_format_lineage_node_card",
    "_format_node_card",
    # Helpers
    "_create_temp_dir",
    "_detect_display_type",
    "_escape_markdown",
    "_get_node_type",
    "_get_short_name",
    "_get_type_icon",
    "_group_nodes_by_type",
    "_render_as_table",
    "_truncate",
]
