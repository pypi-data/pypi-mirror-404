"""PydanticAI-native orchestrator and specialist implementations.

This module provides a clean PydanticAI-based multi-agent system without wrapping
the Anthropic orchestrator. All agents are PydanticAI native with @agent.tool decorators.

Architecture:
    CopilotKit → PydanticAI Orchestrator → PydanticAI Specialists

Benefits:
    - 50% faster (no double wrapping)
    - Native AG-UI streaming
    - Tool calls visible automatically
    - Single framework end-to-end
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import logfire
from ag_ui.core import RunAgentInput
from pydantic_ai import Agent, Tool

from lineage.agent.prompt_loader import load_prompt
from lineage.agent.pydantic.tools.bash import bash_toolset
from lineage.agent.pydantic.tools.data import (
    data_exploration_toolset,
    execute_query,
    semantic_view_toolset,
)
from lineage.agent.pydantic.tools.dbt import dbt_toolset
from lineage.agent.pydantic.tools.filesystem import filesystem_toolset
from lineage.agent.pydantic.tools.git import git_toolset
from lineage.agent.pydantic.tools.graph import graph_exploration_toolset
from lineage.agent.pydantic.tools.memory import (
    memory_toolset,
)
from lineage.agent.pydantic.tools.presentation import (
    presentation_toolset,
)
from lineage.agent.pydantic.tools.ticketing import ticketing_toolset
from lineage.agent.pydantic.tools.todos import todo_list_manager_toolset
from lineage.agent.pydantic.types import AgentConfig, AgentDeps, FileSystemConfig
from lineage.agent.pydantic.utils import create_model
from lineage.backends.config import GitConfig
from lineage.backends.data_query.protocol import DataQueryBackend
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.memory.protocol import MemoryStorage
from lineage.backends.reports.protocol import ReportsBackend
from lineage.backends.threads.models import ThreadContext
from lineage.backends.threads.protocol import ThreadsBackend
from lineage.backends.tickets.protocol import TicketStorage

# NOTE: logfire.configure() should be called once by the application entry point
# (benchmark CLI, web API, CLI runner). We only instrument pydantic-ai here.
# instrument_pydantic_ai() is idempotent - safe to call multiple times.
logfire.instrument_pydantic_ai()
logger = logging.getLogger(__name__)

# ============================================================================
# Toolset Name Mapping (for white_list/black_list filtering)
# ============================================================================

# Map from user-friendly name to toolset object
TOOLSET_NAME_MAP = {
    "filesystem": filesystem_toolset,
    "git": git_toolset,
    "dbt": dbt_toolset,
    "bash": bash_toolset,
    "data_exploration": data_exploration_toolset,
    "semantic_view": semantic_view_toolset,
    "graph_exploration": graph_exploration_toolset,
    "ticketing": ticketing_toolset,
    "todo_list_manager": todo_list_manager_toolset,
    "presentation": presentation_toolset,
    "memory": memory_toolset,
}

# Reverse map to get name from toolset object (by identity)
TOOLSET_TO_NAME = {id(v): k for k, v in TOOLSET_NAME_MAP.items()}


def get_toolset_name(toolset: Any) -> Optional[str]:
    """Get the name of a toolset from its object.

    Args:
        toolset: A toolset object (e.g., filesystem_toolset)

    Returns:
        The name of the toolset if found in TOOLSET_NAME_MAP, else None
    """
    return TOOLSET_TO_NAME.get(id(toolset))


def filter_toolsets(
    toolsets: list[Any],
    white_list: Optional[list[str]] = None,
    black_list: Optional[list[str]] = None,
) -> list[Any]:
    """Filter toolsets based on white_list or black_list.

    This function should be called right before creating the Agent kwargs
    to apply any tool filtering specified in the benchmark configuration.

    Args:
        toolsets: List of toolset objects
        white_list: If set, only keep toolsets with these names
        black_list: If set, remove toolsets with these names

    Returns:
        Filtered list of toolset objects

    Raises:
        ValueError: If both white_list and black_list are specified
    """
    if white_list is None and black_list is None:
        return toolsets

    if white_list is not None and black_list is not None:
        raise ValueError("Cannot specify both tool_white_list and tool_black_list")

    result = []
    for toolset in toolsets:
        name = get_toolset_name(toolset)
        if white_list is not None:
            if name in white_list:
                result.append(toolset)
            else:
                logger.debug(f"Toolset '{name}' filtered out by white_list")
        elif black_list is not None:
            if name not in black_list:
                result.append(toolset)
            else:
                logger.debug(f"Toolset '{name}' filtered out by black_list")
    return result


# Mapping from toolset names to the backends they require
TOOLSET_BACKEND_REQUIREMENTS = {
    "graph_exploration": ["lineage"],
    "data_exploration": ["data_backend"],
    "semantic_view": ["data_backend"],
    "memory": ["memory_backend"],
    "ticketing": ["ticket_storage"],
    "presentation": ["reports_backend"],
    # filesystem, git, dbt, bash, todo_list_manager don't require optional backends
}


def get_required_backends(toolsets: list[Any]) -> set[str]:
    """Determine which backends are required by the given toolsets.

    Args:
        toolsets: List of toolset objects

    Returns:
        Set of backend names that are required (e.g., {"lineage", "data_backend"})
    """
    required = set()
    for toolset in toolsets:
        name = get_toolset_name(toolset)
        if name and name in TOOLSET_BACKEND_REQUIREMENTS:
            required.update(TOOLSET_BACKEND_REQUIREMENTS[name])
    return required


def filter_individual_tools(
    toolsets: list[Any],
    white_list: Optional[list[str]] = None,
    black_list: Optional[list[str]] = None,
) -> list[Any]:
    """Filter individual tools within toolsets using white_list or black_list.

    Uses the toolset's `filtered()` method to create wrapped toolsets that
    filter tools at runtime based on tool names.

    Args:
        toolsets: List of toolset objects
        white_list: If set, only keep tools with these names
        black_list: If set, remove tools with these names

    Returns:
        List of filtered toolset objects (wrapped with FilteredToolset)

    Raises:
        ValueError: If both white_list and black_list are specified
    """
    if white_list is None and black_list is None:
        return toolsets

    if white_list is not None and black_list is not None:
        raise ValueError("Cannot specify both individual_tool_white_list and individual_tool_black_list")

    result = []
    for toolset in toolsets:
        if white_list is not None:
            # Keep only tools in white_list
            filtered_toolset = toolset.filtered(
                lambda ctx, tool_def, wl=white_list: tool_def.name in wl
            )
            result.append(filtered_toolset)
            logger.debug(f"Applied individual tool white_list to toolset: keeping {white_list}")
        elif black_list is not None:
            # Remove tools in black_list
            filtered_toolset = toolset.filtered(
                lambda ctx, tool_def, bl=black_list: tool_def.name not in bl
            )
            result.append(filtered_toolset)
            logger.debug(f"Applied individual tool black_list to toolset: removing {black_list}")
    return result

# ============================================================================
# Generic Agent Factory
# ============================================================================


def create_agent(
    lineage: Optional[LineageStorage],
    input_data: RunAgentInput,
    config: AgentConfig,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
    filesystem_config: Optional[FileSystemConfig] = None,
    git_config: Optional[GitConfig] = None,
) -> tuple[Agent, AgentDeps]:
    """Generic factory function for creating PydanticAI agents.

    This function eliminates repetition by centralizing the agent creation logic.
    All agent-specific configuration is provided via the AgentConfig dataclass.

    Args:
        lineage: Lineage storage backend (None if lineage is not needed)
        input_data: Run agent input containing thread and run IDs
        config: AgentConfig with prompt name, toolsets, tools, retries, etc.
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs (injected into prompt)
        filesystem_config: Optional filesystem configuration for file operations
        git_config: Optional git configuration for git operations

    Returns:
        Tuple of (agent, dependencies)
    """
    # Build toolsets list (conditionally add memory_toolset)
    toolsets = list(config.toolsets)
    if memory_backend:
        toolsets.append(memory_toolset)

    # Apply toolset-level white_list/black_list filtering if specified
    toolsets = filter_toolsets(
        toolsets,
        white_list=config.tool_white_list,
        black_list=config.tool_black_list,
    )

    # Apply individual tool filtering if specified
    toolsets = filter_individual_tools(
        toolsets,
        white_list=config.individual_tool_white_list,
        black_list=config.individual_tool_black_list,
    )

    # Determine which backends are required based on remaining toolsets
    # and nullify backends that are no longer needed
    required_backends = get_required_backends(toolsets)
    if "lineage" not in required_backends:
        if lineage is not None:
            logger.debug("Nullifying lineage backend (graph_exploration toolset filtered out)")
        lineage = None
    if "data_backend" not in required_backends:
        if data_backend is not None:
            logger.debug("Nullifying data_backend (data_exploration/semantic_view toolsets filtered out)")
        data_backend = None
    if "memory_backend" not in required_backends:
        if memory_backend is not None:
            logger.debug("Nullifying memory_backend (memory toolset filtered out)")
        memory_backend = None
    if "ticket_storage" not in required_backends:
        if ticket_storage is not None:
            logger.debug("Nullifying ticket_storage (ticketing toolset filtered out)")
        ticket_storage = None
    if "reports_backend" not in required_backends:
        if reports_backend is not None:
            logger.debug("Nullifying reports_backend (presentation toolset filtered out)")
        reports_backend = None

    # Prepare prompt kwargs (after filtering, so prompt only includes relevant backends)
    prompt_kwargs = config.prompt_kwargs or {}
    prompt_kwargs.setdefault("data_backend", data_backend)
    if lineage:
        prompt_kwargs.setdefault("lineage_backend", lineage)
    prompt_kwargs.setdefault("ticket_storage", ticket_storage)
    prompt_kwargs.setdefault("thread_context", thread_context)
    if filesystem_config:
        prompt_kwargs.setdefault("filesystem_config", filesystem_config)
    if git_config:
        prompt_kwargs.setdefault("git_cfg", git_config)

    # Load prompt with Jinja template rendering
    system_prompt = load_prompt(config.prompt_name, **prompt_kwargs)

    # Create agent - only include tools if not None
    agent_kwargs = {
        "model": create_model(model),
        "deps_type": AgentDeps,
        "system_prompt": system_prompt,
        "retries": config.retries,
        "toolsets": toolsets,
    }
    if config.tools is not None:
        agent_kwargs["tools"] = config.tools

    agent = Agent(**agent_kwargs)

    # Create dependencies
    deps = AgentDeps(
        lineage=lineage,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        agent_name=config.agent_name,
        thread_id=input_data.thread_id,
        run_id=input_data.run_id,
        thread_context=thread_context,
        filesystem_config=filesystem_config,
        git_config=git_config,
    )

    return agent, deps


# ============================================================================
# Analyst Orchestrator
# ============================================================================


def create_analyst_orchestrator(
    lineage: LineageStorage,
    input_data: RunAgentInput,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create flattened analyst agent with MCP-based semantic view access.

    This agent answers questions about:
    - Business analytics and metrics from semantic views
    - Data exploration within curated semantic views
    - Reporting on pre-defined dimensions/measures

    IMPORTANT: This agent uses parameterized queries (no SQL required!) and is restricted
    to semantic views only. It cannot:
    - Access raw tables or staging/intermediate models
    - Execute Cypher queries against the lineage graph
    - Modify or create semantic views (use data engineering agent)

    Tools available (all directly attached, no delegation):
    - list_semantic_views_mcp: Browse all available semantic views
    - show_semantic_metrics_mcp: Show available metrics with aggregations
    - show_semantic_dimensions_mcp: Show available dimensions for grouping
    - query_semantic_view: Execute parameterized queries (no SQL!)
    - get_semantic_view_ddl: Get DDL for structure understanding
    - create_visualization: Create charts from query results
    - save_html_report: Save HTML reports
    - Memory tools: store/recall user preferences and data patterns
    - Ticket tools: create/list/update tickets for inter-agent communication

    Args:
        lineage: Lineage storage backend
        input_data: Run agent input containing thread and run IDs
        data_backend: Optional data warehouse backend (must support MCP)
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs (injected into prompt)

    Returns:
        Tuple of (agent, dependencies)
    """
    config = AgentConfig(
        prompt_name="data_analyst",
        toolsets=[ticketing_toolset, todo_list_manager_toolset, presentation_toolset, semantic_view_toolset],
        retries=5,
        agent_name="data_analyst",
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
    )


# ============================================================================
# Data Quality Orchestrator
# ============================================================================


def create_data_quality_orchestrator(
    lineage: LineageStorage,
    input_data: RunAgentInput,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create flattened data quality agent with all tools directly attached.

    This agent helps with:
    - Diagnosing operational issues and failures
    - Troubleshooting data quality problems
    - Generating diagnostic reports

    Tools available (all directly attached, no delegation):
    - query_graph: Execute Cypher queries for diagnostics (graph schema embedded in prompt)
    - preview_table: Preview table contents
    - execute_query: Execute SQL queries for data quality checks
    - save_html_report: Save diagnostic HTML reports
    - Memory tools: store/recall data quality patterns
    - Ticket tools: create/list/update tickets for inter-agent communication

    Note: Graph schema is embedded directly in the prompt for better performance.

    Args:
        lineage: Lineage storage backend
        input_data: Run agent input containing thread and run IDs
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs (injected into prompt)

    Returns:
        Tuple of (agent, dependencies)
    """
    config = AgentConfig(
        prompt_name="data_quality",
        toolsets=[
            ticketing_toolset,
            todo_list_manager_toolset,
            data_exploration_toolset,
            semantic_view_toolset,
            presentation_toolset,
            graph_exploration_toolset,
        ],
        tools=[Tool(execute_query)],
        retries=2,
        agent_name="data_quality",
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
    )


# ============================================================================
# Data Investigator Orchestrator (replaces Quality for reactive troubleshooting)
# ============================================================================


def create_data_investigator_orchestrator(
    lineage: LineageStorage,
    input_data: RunAgentInput,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create Data Investigator agent for reactive troubleshooting.

    This agent helps when users bring problems:
    - "Why is ARR wrong?"
    - "This dashboard doesn't look right"
    - "Revenue numbers don't match"

    Approach: Lineage first → Semantic analysis → Data validation

    Tools available:
    - Graph exploration: query_graph, get_logical_lineage, get_column_lineage
    - Data validation: preview_table, execute_query (sparingly)
    - Tickets: create/update for escalation to engineering
    - Reports: document findings with mermaid diagrams
    """
    config = AgentConfig(
        prompt_name="data_investigator",
        toolsets=[
            graph_exploration_toolset,  # Primary: lineage and semantic graph
            data_exploration_toolset,   # Secondary: data validation
            semantic_view_toolset,      # Native semantic views
            ticketing_toolset,          # Escalation
            presentation_toolset,       # Reports with mermaid
            todo_list_manager_toolset,
        ],
        tools=[Tool(execute_query)],
        retries=2,
        agent_name="data_investigator",
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
    )


# ============================================================================
# Data Insights Orchestrator (proactive patterns + semantic explanation)
# ============================================================================


def create_data_insights_orchestrator(
    lineage: LineageStorage,
    input_data: RunAgentInput,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create Data Insights agent for architecture explanation and pattern surfacing.

    This agent helps users understand their data:
    - "Explain this model to me"
    - "How do these tables join?"
    - "What measures are available?"
    - "What's the grain of this model?"

    Approach: Semantic metadata first → Lineage → Data examples

    Tools available:
    - Graph exploration: query_graph for semantic metadata (SemanticAnalysis, BusinessMeasure, etc.)
    - Lineage: get_logical_lineage, get_column_lineage
    - Data examples: preview_table (sparingly)
    - Reports: visualize with mermaid diagrams
    """
    config = AgentConfig(
        prompt_name="data_insights",
        toolsets=[
            graph_exploration_toolset,  # Primary: semantic metadata
            data_exploration_toolset,   # Secondary: examples
            semantic_view_toolset,      # Native semantic views
            presentation_toolset,       # Reports with mermaid
            todo_list_manager_toolset,
        ],
        tools=None,  # No direct execute_query - use exploration tools
        retries=2,
        agent_name="data_insights",
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
    )


# ============================================================================
# Data Engineering Orchestrator
# ============================================================================


def create_data_engineering_orchestrator(
    lineage: LineageStorage,
    input_data: RunAgentInput,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create flattened data engineering agent with all tools directly attached.

    This agent helps with:
    - Understanding existing models and dependencies
    - Testing and validating new SQL queries
    - Generating dbt code (future enhancement)

    Tools available (all directly attached, no delegation):
    - query_graph: Execute Cypher queries for model structure (graph schema embedded in prompt)
    - list_tables: Discover available tables
    - preview_table: Preview table contents
    - execute_query: Test and validate SQL queries
    - Memory tools: store/recall data model patterns
    - Ticket tools: create/list/update tickets for inter-agent communication

    Note: Graph schema is embedded directly in the prompt for better performance.

    Args:
        lineage: Lineage storage backend
        input_data: Run agent input containing thread and run IDs
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs (injected into prompt)

    Returns:
        Tuple of (agent, dependencies)
    """
    config = AgentConfig(
        prompt_name="data_engineer",
        toolsets=[
            graph_exploration_toolset,
            ticketing_toolset,
            todo_list_manager_toolset,
            data_exploration_toolset,
            semantic_view_toolset,
            presentation_toolset,
        ],
        tools=[Tool(execute_query)],
        retries=5,
        agent_name="data_engineering",
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
    )


# ============================================================================
# Data Engineer Copilot Orchestrator (Interactive Mode)
# ============================================================================


def create_data_engineer_copilot_orchestrator(
    lineage: Optional[LineageStorage],
    input_data: RunAgentInput,
    filesystem_config: FileSystemConfig,
    git_config: Optional[GitConfig] = None,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
) -> tuple[Agent, AgentDeps]:
    """Create INTERACTIVE data engineer copilot with full file/git/dbt capabilities.

    This agent works WITH a human in local CLI environment:
    - Explains reasoning so users learn dbt best practices
    - Asks clarifying questions before making significant changes
    - Confirms with user before multi-file refactors or schema changes
    - Shows work (queries being tested, lineage being checked)

    Capabilities:
    - Read, write, and edit files in the dbt project
    - Run git operations (status, diff, add, commit, branch, push)
    - Execute dbt commands (run, test, build, compile)
    - Query lineage graph and data warehouse (if lineage is provided)
    - Create/update tickets for tracking work

    Args:
        lineage: Lineage storage backend (None if lineage is not needed)
        input_data: Run agent input containing thread and run IDs
        filesystem_config: Configuration for file operations (working directory, etc.)
        git_config: Optional git configuration (from backends/config.py)
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs

    Returns:
        Tuple of (agent, dependencies)
    """
    # Build toolsets list with conditional git_toolset and graph_exploration_toolset
    toolsets = [
        filesystem_toolset,
        dbt_toolset,
        bash_toolset,
        data_exploration_toolset,
        semantic_view_toolset,
        ticketing_toolset,
        todo_list_manager_toolset,
    ]
    # Only include graph_exploration_toolset if lineage is provided
    if lineage:
        toolsets.append(graph_exploration_toolset)
    if git_config and git_config.enabled:
        toolsets.append(git_toolset)

    config = AgentConfig(
        prompt_name="data_engineer_copilot",
        toolsets=toolsets,
        tools=[Tool(execute_query)],
        retries=3,
        agent_name="data_engineer_copilot",
        prompt_kwargs={
            "filesystem_config": filesystem_config,
            "git_cfg": git_config,  # Note: parameter name is git_cfg
        },
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
        filesystem_config=filesystem_config,
        git_config=git_config,
    )


# ============================================================================
# Data Engineer Reconciler Orchestrator (Autonomous Mode)
# ============================================================================


def create_data_engineer_reconciler_orchestrator(
    lineage: Optional[LineageStorage],
    input_data: RunAgentInput,
    filesystem_config: FileSystemConfig,
    git_config: Optional[GitConfig] = None,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    reports_backend: Optional[ReportsBackend] = None,
    threads_backend: Optional[ThreadsBackend] = None,
    model: str = "anthropic:claude-sonnet-4-5-20250929",
    thread_context: Optional[ThreadContext] = None,
    tool_white_list: Optional[list[str]] = None,
    tool_black_list: Optional[list[str]] = None,
    individual_tool_white_list: Optional[list[str]] = None,
    individual_tool_black_list: Optional[list[str]] = None,
) -> tuple[Agent, AgentDeps]:
    """Create AUTONOMOUS data engineer reconciler for ticket processing.

    This agent runs in daemon mode to process tickets independently:
    - Works efficiently without human input
    - Updates ticket status throughout workflow
    - Completes tickets or asks for clarification via ticket comments
    - Proactively monitors for related issues

    Capabilities (same as copilot):
    - Read, write, and edit files in the dbt project
    - Run git operations (status, diff, add, commit, branch, push)
    - Execute dbt commands (run, test, build, compile)
    - Query lineage graph and data warehouse (if lineage is provided)
    - Create/update tickets for tracking work

    Args:
        lineage: Lineage storage backend (None if lineage is not needed)
        input_data: Run agent input containing thread and run IDs
        filesystem_config: Configuration for file operations (working directory, etc.)
        git_config: Optional git configuration (from backends/config.py)
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend for work tracking
        reports_backend: Optional reports backend for report management
        threads_backend: Optional threads backend for multi-run context persistence
        model: PydanticAI model identifier
        thread_context: Optional thread context from previous runs
        tool_white_list: If set, only keep toolsets with these names
        tool_black_list: If set, remove toolsets with these names
        individual_tool_white_list: If set, only keep individual tools with these names
        individual_tool_black_list: If set, remove individual tools with these names

    Returns:
        Tuple of (agent, dependencies)
    """
    # Build toolsets list with conditional ticketing_toolset, git_toolset, and graph_exploration_toolset
    toolsets = [
        filesystem_toolset,
        dbt_toolset,
        bash_toolset,
        data_exploration_toolset,
        semantic_view_toolset,
        todo_list_manager_toolset,
    ]
    # Only include graph_exploration_toolset if lineage is provided
    if lineage:
        toolsets.append(graph_exploration_toolset)
    if ticket_storage:
        toolsets.append(ticketing_toolset)
    if git_config and git_config.enabled:
        toolsets.append(git_toolset)

    config = AgentConfig(
        prompt_name="data_engineer_reconciler",
        toolsets=toolsets,
        tools=[Tool(execute_query)],
        retries=3,
        agent_name="data_engineer_reconciler",
        prompt_kwargs={
            "filesystem_config": filesystem_config,
            "git_cfg": git_config,  # Note: parameter name is git_cfg
        },
        tool_white_list=tool_white_list,
        tool_black_list=tool_black_list,
        individual_tool_white_list=individual_tool_white_list,
        individual_tool_black_list=individual_tool_black_list,
    )

    return create_agent(
        lineage=lineage,
        input_data=input_data,
        config=config,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
        reports_backend=reports_backend,
        threads_backend=threads_backend,
        model=model,
        thread_context=thread_context,
        filesystem_config=filesystem_config,
        git_config=git_config,
    )
