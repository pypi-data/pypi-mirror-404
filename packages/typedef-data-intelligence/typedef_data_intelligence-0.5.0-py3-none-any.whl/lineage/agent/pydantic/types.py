"""Pydantic types for agent state and dependencies.

This module defines the state models and dependency structures used by
PydanticAI agents, including tool results, thinking blocks, and report previews.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import Tool

from lineage.backends.config import GitConfig
from lineage.backends.data_query.protocol import DataQueryBackend
from lineage.backends.lineage.protocol import (
    ColumnLineageResult as ProtocolColumnLineageResult,
)
from lineage.backends.lineage.protocol import (
    GraphSchemaFormat,
    LineageNode,
    LineageStorage,
)
from lineage.backends.lineage.protocol import (
    ModelMaterializationsResult as ProtocolModelMaterializationsResult,
)
from lineage.backends.lineage.protocol import (
    RelationLineageResult as ProtocolRelationLineageResult,
)
from lineage.backends.memory.protocol import MemoryStorage
from lineage.backends.reports.protocol import ReportsBackend
from lineage.backends.threads.models import ThreadContext
from lineage.backends.threads.protocol import ThreadsBackend
from lineage.backends.tickets.protocol import TicketStorage
from lineage.backends.todos.todo_manager import TodoItem, TodoListManager

# ============================================================================
# Filesystem Configuration
# ============================================================================


@dataclass
class FileSystemConfig:
    """Configuration for filesystem operations.

    Attributes:
        working_directory: Base directory for file operations (all paths relative to this)
        allowed_paths: Additional allowed paths outside working_directory (optional whitelist)
        read_only: If True, only read operations are allowed (for safer evaluation)
    """

    working_directory: Path
    allowed_paths: List[Path] = field(default_factory=list)
    read_only: bool = False


# ============================================================================
# Agent Configuration
# ============================================================================


@dataclass
class AgentConfig:
    """Configuration for creating a PydanticAI agent.

    This dataclass encapsulates all the variable aspects of agent creation,
    allowing for easy creation of custom agents for evaluations and testing.

    Attributes:
        prompt_name: Name of the prompt to load (e.g., "data_analyst", "data_quality")
        toolsets: List of toolsets to include in the agent
        tools: Optional list of direct tools (e.g., [Tool(execute_query)])
        retries: Number of retries for the agent (default: 2)
        agent_name: Name for the agent (used in AgentDeps)
        prompt_kwargs: Optional dict of extra kwargs to pass to load_prompt
        tool_white_list: If set, only keep toolsets whose names are in this list
        tool_black_list: If set, remove toolsets whose names are in this list
        individual_tool_white_list: If set, only keep individual tools in this list
        individual_tool_black_list: If set, remove individual tools in this list
    """

    prompt_name: str
    toolsets: List[Any]
    tools: Optional[List[Tool]] = None
    retries: int = 2
    agent_name: str = ""
    prompt_kwargs: Optional[Dict[str, Any]] = None
    tool_white_list: Optional[List[str]] = None
    tool_black_list: Optional[List[str]] = None
    individual_tool_white_list: Optional[List[str]] = None
    individual_tool_black_list: Optional[List[str]] = None

    def __post_init__(self) -> None:
        """Set agent_name from prompt_name if not explicitly provided."""
        if not self.agent_name:
            self.agent_name = self.prompt_name


# ============================================================================
# Tool Result Models
# ============================================================================


class GraphSchemaResult(BaseModel):
    """Result from get_graph_schema tool."""
    tool_name: str = "get_graph_schema"
    format: GraphSchemaFormat = "compact"
    graph_schema: Union[str, Dict[str, Any]] = Field(alias="schema")
    examples: Optional[Dict[str, str]] = None
    notes: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)
    error: Optional[str] = None


class QueryGraphResult(BaseModel):
    """Result from query_graph tool."""
    tool_name: str = "query_graph"
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    node_count: int = Field(default=0)
    error: Optional[str] = None
    query_description: Optional[str] = None
    display_hint: Optional[str] = None  # "table", "cards", "scalar", "list"


class GraphSearchResult(BaseModel):
    """Result from search_graph tool."""
    tool_name: str = "search_graph"
    term: str
    node_types: Optional[List[str]] = None
    matches: List[Dict[str, Any]] = Field(default_factory=list)
    match_count: int = Field(default=0)
    error: Optional[str] = None


class PreviewTableResult(BaseModel):
    """Result from preview_table tool."""
    tool_name: str = "preview_table"
    columns: List[str] = Field(default_factory=list)
    rows: List[Any] = Field(default_factory=list)
    row_count: int = Field(default=0)
    error: Optional[str] = None


class ExecuteQueryResult(BaseModel):
    """Result from execute_query tool."""
    tool_name: str = "execute_query"
    columns: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)
    row_count: int = Field(default=0)
    error: Optional[str] = None
    query: Optional[str] = None


# ============================================================================
# CLI Tool Results
# ============================================================================


class BashResult(BaseModel):
    """Result from bash tool."""

    tool_name: str = "bash"
    command: str
    exit_code: int
    stdout: str
    stderr: Optional[str] = None
    working_dir: str


class DbtResult(BaseModel):
    """Result from dbt_cli tool."""

    tool_name: str = "dbt_cli"
    command: str
    exit_code: int
    stdout: str
    stderr: Optional[str] = None
    project_dir: str


# Re-export protocol lineage types for tool use
# These are the canonical types - no wrapping needed
RelationLineageResult = ProtocolRelationLineageResult
ColumnLineageResult = ProtocolColumnLineageResult
ModelMaterializationsResult = ProtocolModelMaterializationsResult
RelationLineageNode = LineageNode  # Alias for clarity


class SearchModelsResult(BaseModel):
    """Result from search_models tool."""

    tool_name: str = "search_models"
    search_term: str
    results: List[Dict[str, Any]] = Field(default_factory=list)
    result_count: int = Field(default=0)


class JoinPatternsResult(BaseModel):
    """Result from get_join_patterns tool."""

    tool_name: str = "get_join_patterns"
    model_id: str
    model_name: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_pattern: Optional[str] = None
    cluster_size: int = Field(default=0)
    join_partners: List[Dict[str, Any]] = Field(default_factory=list)
    join_edges: List[Dict[str, Any]] = Field(default_factory=list)


class DownstreamImpactResult(BaseModel):
    """Result from get_downstream_impact tool."""

    tool_name: str = "get_downstream_impact"
    model_id: str
    model_name: Optional[str] = None
    affected_models: List[Dict[str, Any]] = Field(default_factory=list)
    total_affected: int = Field(default=0)
    max_depth: int = Field(default=0)


class ExecuteSqlForReportResult(BaseModel):
    """Result from execute_sql_for_report tool."""
    tool_name: str = "execute_sql_for_report"
    description: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int


class CreateVisualizationResult(BaseModel):
    """Result from create_visualization tool."""
    tool_name: str = "create_visualization"
    chart_path: str
    chart_type: str
    title: str


class SaveHtmlReportResult(BaseModel):
    """Result from save_html_report tool."""
    tool_name: str = "save_html_report"
    report_path: str
    url: str
    report_name: str


class StoreUserPreferenceResult(BaseModel):
    """Result from store_user_preference tool."""
    tool_name: str = "store_user_preference"
    success: bool
    message: str
    key: Optional[str] = None
    value: Optional[str] = None
    category: Optional[str] = None


class StoreDataPatternResult(BaseModel):
    """Result from store_data_pattern tool."""
    tool_name: str = "store_data_pattern"
    success: bool
    message: str
    pattern_type: Optional[str] = None
    pattern_name: Optional[str] = None
    confidence: Optional[float] = None
    models_involved: Optional[List[str]] = None


class StoreSessionSummaryResult(BaseModel):
    """Result from store_session_summary tool."""
    tool_name: str = "store_session_summary"
    success: bool
    message: str
    user_stored: bool
    org_stored: bool
    learning_count: Optional[int] = None


class ExecuteSemanticViewQueryResult(BaseModel):
    """Result from execute_semantic_view_query tool (validated SQL execution)."""
    tool_name: str = "execute_semantic_view_query"
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    validated_views: List[str]  # Views that were referenced and validated


class CreateTicketResult(BaseModel):
    """Result from create_ticket tool."""
    tool_name: str = "create_ticket"
    ticket_id: str
    title: str
    status: str
    priority: str
    message: str


class ListTicketsResult(BaseModel):
    """Result from list_tickets tool."""
    tool_name: str = "list_tickets"
    tickets: List[Dict[str, Any]] = Field(default_factory=list)
    count: int = Field(default=0)


class GetTicketResult(BaseModel):
    """Result from get_ticket tool."""
    tool_name: str = "get_ticket"
    ticket: Dict[str, Any]


class UpdateTicketResult(BaseModel):
    """Result from update_ticket tool."""
    tool_name: str = "update_ticket"
    ticket_id: str
    message: str


class AddTicketCommentResult(BaseModel):
    """Result from add_ticket_comment tool."""
    tool_name: str = "add_ticket_comment"
    ticket_id: str
    message: str


class MarkdownCellResult(BaseModel):
    """Result from add_markdown_cell tool."""
    tool_name: str = "add_markdown_cell"
    cell_id: str
    cell_type: str = "markdown"
    content: str


class ChartCellResult(BaseModel):
    """Result from add_chart_cell tool - stores raw data for frontend rendering."""
    tool_name: str = "add_chart_cell"
    cell_id: str
    cell_type: str = "chart"
    chart_type: str  # bar, line, pie, scatter, area
    title: str
    columns: List[str]
    data: List[Dict[str, Any]]  # Raw data rows for frontend Recharts rendering
    x_column: str
    y_column: str


class TableCellResult(BaseModel):
    """Result from add_table_cell tool - stores raw data for frontend rendering."""
    tool_name: str = "add_table_cell"
    cell_id: str
    cell_type: str = "table"
    title: Optional[str] = None
    columns: List[str]
    data: List[Dict[str, Any]]  # Raw data rows for frontend InteractiveTable


class CellMetadata(BaseModel):
    """Metadata about a cell in the current report."""
    cell_id: str
    cell_number: int  # 1-indexed position
    cell_type: str  # markdown, chart, table, mermaid
    preview: str  # First 100 chars or title


class MermaidCellResult(BaseModel):
    """Result from add_mermaid_cell tool."""
    tool_name: str = "add_mermaid_cell"
    cell_id: str
    cell_type: str = "mermaid"
    title: Optional[str] = None
    diagram: str


class ListReportCellsResult(BaseModel):
    """Result from list_report_cells tool."""
    tool_name: str = "list_report_cells"
    cells: List[CellMetadata] = Field(default_factory=list)
    total_count: int = 0


class CreateReportResult(BaseModel):
    """Result from create_report tool."""
    tool_name: str = "create_report"
    report_id: str
    title: str
    message: str


class SaveReportResult(BaseModel):
    """Result from save_report tool (deprecated - use create_report instead)."""
    tool_name: str = "save_report"
    report_id: str
    title: str
    saved_at: str
    cell_count: int


class ModifyCellResult(BaseModel):
    """Result from modify_report_cell tool."""
    tool_name: str = "modify_report_cell"
    report_id: str
    cell_number: int
    message: str


class DeleteCellResult(BaseModel):
    """Result from delete_report_cell tool."""
    tool_name: str = "delete_report_cell"
    report_id: str
    cell_number: int
    message: str


# ============================================================================
# Thinking Block Model
# ============================================================================


class ThinkingBlock(BaseModel):
    """Extended thinking content from Claude's reasoning process."""

    content: str
    """The thinking/reasoning content"""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    """When this thinking block was created"""

    tool_call_id: Optional[str] = None
    """Associated tool call ID if this thinking preceded a tool call"""


# ============================================================================
# State Model
# ============================================================================


class ReportPreview(BaseModel):
    """Preview data for a report in state snapshot."""
    report_id: str
    title: str
    cell_count: int
    last_updated: datetime
    cells: List[Dict[str, Any]] = Field(default_factory=list)
    """Cell data for frontend rendering"""


class AgentState(BaseModel):
    """State container for AG-UI protocol.

    Stores tool results keyed by tool_call_id for frontend generative UI rendering.
    Also stores thinking blocks from Claude's extended thinking feature.

    This state is automatically synced to frontend via AG-UI protocol state_update events.
    """

    tool_results: Dict[str, BaseModel] = Field(default_factory=dict)
    """Maps tool_call_id to tool result models"""

    thinking_blocks: List[ThinkingBlock] = Field(default_factory=list)
    """Extended thinking/reasoning blocks from Claude"""

    current_todos: List[TodoItem] = Field(default_factory=list)

    current_specialist: Optional[str] = None
    """Currently active specialist (for orchestrators)"""

    last_query: Optional[str] = None
    """Last query executed (for debugging)"""

    active_reports: Dict[str, ReportPreview] = Field(default_factory=dict)
    """Active reports keyed by report_id - updated when cells are added/modified"""

    preview_tabs: List[Dict[str, Any]] = Field(default_factory=list)
    """Preview pane tabs (queries, reports) for frontend rendering"""

    model_config = ConfigDict(arbitrary_types_allowed=True)


# ============================================================================
# Dependency Models
# ============================================================================


@dataclass
class AgentDeps:
    """Dependencies injected into agent.

    The state field is required by PydanticAI's AG-UI StateHandler protocol.
    It stores tool results and intermediate state for generative UI rendering.

    Memory fields (user_id, org_id, memory_backend) enable persistent memory:
    - user_id: Identifies the current user for user-specific memory
    - org_id: Identifies the organization for shared memory
    - memory_backend: Optional backend for storing/retrieving memories

    Filesystem and git fields enable code modification capabilities:
    - filesystem_config: Configuration for file read/write operations
    - git_config: Configuration for git operations (from backends/config.py)
    """

    lineage: LineageStorage
    thread_id: str
    run_id: str
    data_backend: Optional[DataQueryBackend] = None
    memory_backend: Optional[MemoryStorage] = None
    ticket_storage: Optional[TicketStorage] = None
    reports_backend: Optional[ReportsBackend] = None
    threads_backend: Optional[ThreadsBackend] = None
    todo_list_manager: TodoListManager = field(default_factory=TodoListManager)
    user_id: Optional[str] = None
    org_id: str = "default"
    agent_name: str = "agent"
    state: AgentState = field(default_factory=AgentState)
    thread_context: Optional[ThreadContext] = None
    # Filesystem and git configuration for code modification agents
    filesystem_config: Optional[FileSystemConfig] = None
    git_config: Optional[GitConfig] = None
