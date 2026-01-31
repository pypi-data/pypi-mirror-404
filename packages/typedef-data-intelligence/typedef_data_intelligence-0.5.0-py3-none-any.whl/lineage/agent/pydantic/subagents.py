from __future__ import annotations
from typing import Optional
from lineage.agent.prompt_loader import load_prompt
from lineage.agent.pydantic.tools.memory import memory_toolset
from lineage.agent.pydantic.tools.todos import todo_list_manager_toolset
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.data_query.protocol import DataQueryBackend
from lineage.backends.memory.protocol import MemoryStorage
from lineage.backends.tickets.protocol import TicketStorage
from pydantic_ai import Agent, Tool
from lineage.agent.pydantic.types import AgentDeps
from lineage.agent.pydantic.tools.data import list_tables, preview_table, execute_query, \
    query_semantic_view
from lineage.agent.pydantic.tools.graph import list_semantic_views, list_semantic_dimensions, list_semantic_facts, \
    get_semantic_view_schema, query_graph, list_semantic_measures
from lineage.agent.pydantic.utils import create_model

def create_metadata_explorer_subagent(
    lineage: LineageStorage,
    data_backend: Optional[DataQueryBackend] = None,
    memory_backend: Optional[MemoryStorage] = None,
    model: str = "anthropic:claude-haiku-4-5",
) -> tuple[Agent, AgentDeps]:
    """Create data explorer subagent with all tools directly attached.

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

    Note: Graph schema is embedded directly in the prompt for better performance.

    Args:
        lineage: Lineage storage backend
        data_backend: Optional data warehouse backend
        memory_backend: Optional memory backend for persistent memory
        ticket_storage: Optional ticket storage backend
        model: PydanticAI model identifier

    Returns:
        Tuple of (agent, dependencies)
    """

    system_prompt = load_prompt("metadata_explorer", data_backend=data_backend, lineage_backend=lineage)

    # Build tool list (removed get_graph_schema - schema is in prompt)
    tools = [
        Tool(query_graph),
    ]

    toolsets = [todo_list_manager_toolset]
    if memory_backend:
        toolsets.append(memory_toolset)

    agent = Agent(
        model=create_model(model),
        deps_type=AgentDeps,
        system_prompt=system_prompt,
        retries=2,
        tools=tools,
        toolsets=toolsets,
    )

    # Create dependencies
    deps = AgentDeps(
        lineage=lineage,
        data_backend=data_backend,
        memory_backend=memory_backend,
    )
    return agent, deps