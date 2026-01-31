# Agent System

This module implements a PydanticAI-based agent system for data intelligence tasks. The current architecture uses **direct tool access** where each agent has a curated set of tools for their domain, avoiding delegation overhead.

## Architecture Overview

```
CopilotKit WebUI (via AG-UI)
    ├─→ /analyst → Data Analyst Agent (direct tool access)
    ├─→ /engineer → Data Engineer Agent (direct tool access)
    └─→ /quality → Data Quality Agent (direct tool access)

CLI Interface (via clai)
    ├─→ analyst → Data Analyst Agent
    ├─→ engineer → Data Engineer Agent
    └─→ quality → Data Quality Agent
```

**Key Benefits:**

- **Simplicity**: Single-level agent hierarchy (no delegation overhead)
- **Performance**: 50% faster than nested delegation patterns
- **Transparency**: Tool calls automatically visible in AG-UI
- **Single framework**: End-to-end PydanticAI

## Directory Structure

```
agent/
├── pydantic/               # Main PydanticAI implementation
│   ├── orchestrator.py     # Agent factory functions + prompt loading
│   ├── cli_agents.py       # CLI-ready agent instances (analyst, engineer, quality)
│   ├── subagents.py        # Helper subagent (metadata_explorer)
│   ├── types.py            # Shared types (AgentDeps)
│   ├── utils.py            # Utilities (model creation)
│   ├── memory_observer.py  # Memory observation for agents
│   ├── ag_ui_handler.py    # CopilotKit AG-UI integration
│   ├── cli_runner.py       # CLI execution wrapper
│   ├── prompts/            # Agent prompt YAML files
│   │   ├── data_analyst.yaml
│   │   ├── data_engineer.yaml.jinja
│   │   ├── data_quality.yaml.jinja
│   │   └── metadata_explorer.yaml.jinja
│   └── tools/              # PydanticAI tool implementations
│       ├── common.py       # Common tool utilities
│       ├── data.py         # Data warehouse query tools
│       ├── graph.py        # Lineage graph query tools
│       ├── memory.py       # Memory storage tools
│       ├── presentation.py # Visualization & reporting tools
│       ├── ticketing.py    # Ticket management tools
│       └── todos.py        # Todo list management tools
├── tools/                  # Legacy tool implementations
│   ├── executor.py         # Tool execution framework
│   ├── memory.py           # Memory tool wrappers
│   ├── tickets.py          # Ticket tool wrappers
│   ├── todo.py             # Todo tool wrappers
│   ├── cursor.py           # Cursor integration tools
│   └── git.py              # Git operations tools
├── utils/                  # Shared utilities
│   ├── visualization.py    # Chart creation (matplotlib, altair)
│   ├── cursor.py           # Cursor IDE integration
│   └── backend_hints.py    # SQL dialect hints
├── cli.py                  # Legacy CLI entry points
└── __init__.py
```

## Core Components

### 1. Agent Factory (`pydantic/orchestrator.py`)

Contains factory functions to create agent instances with appropriate tools:

- `create_analyst_orchestrator()` - Data Analyst agent with query/viz tools
- `create_data_engineering_orchestrator()` - Data Engineer agent with modeling/ticketing tools
- `create_data_quality_orchestrator()` - Data Quality agent with troubleshooting tools

**Key Functions:**

- `load_prompt(agent_name, data_backend, lineage_backend)` - Load agent prompts from YAML/Jinja templates
- `create_model(model_name, thinking_enabled)` - Create PydanticAI model instances

Each factory function:

1. Loads the appropriate prompt template (with SQL/graph hints injected)
2. Attaches domain-specific tools (graph, data, viz, memory, ticketing, todos)
3. Returns a PydanticAI Agent ready for use

### 2. CLI-Ready Agents (`pydantic/cli_agents.py`)

Pre-initialized agent instances for CLI use with `clai` command:

| Agent        | Command         | Purpose                               | Key Tools                                                |
| ------------ | --------------- | ------------------------------------- | -------------------------------------------------------- |
| **analyst**  | `clai analyst`  | SQL queries, reporting, visualization | `execute_query()`, `create_visualization()`, graph tools |
| **engineer** | `clai engineer` | dbt modeling, pipeline design         | Graph tools, data tools, ticketing                       |
| **quality**  | `clai quality`  | Data quality, troubleshooting         | Query tools, error analysis                              |

**Usage:**

```bash
# Interactive mode
clai -m lineage.agent.pydantic.cli_agents analyst

# Single question
clai -m lineage.agent.pydantic.cli_agents analyst "What semantic views are available?"

# With custom config
export UNIFIED_CONFIG=/path/to/config.yml
clai -m lineage.agent.pydantic.cli_agents engineer "Show marts schema models"
```

### 3. Helper Subagent (`pydantic/subagents.py`)

Currently contains one helper subagent that can be used by main agents:

**`create_metadata_explorer_subagent()`** - Graph metadata specialist

- Purpose: Cypher queries for model structure and dependencies
- Tools: `query_graph()` (with schema embedded in prompt)
- Future use: Could be called as a subagent by data engineer for complex metadata queries

### 4. Tools (`pydantic/tools/`)

PydanticAI-native tools organized by domain:

**Data Tools (`data.py`):**

- `list_tables()` - List available tables/views
- `preview_table()` - Sample rows from a table
- `execute_query()` - Execute SQL queries
- `query_semantic_view()` - Query Snowflake semantic views

**Graph Tools (`graph.py`):**

- `query_graph()` - Execute Cypher queries against lineage graph
- `list_semantic_views()` - List semantic models
- `list_semantic_dimensions()` - List dimension attributes
- `list_semantic_measures()` - List business measures
- `get_semantic_view_schema()` - Get semantic view schema

**Presentation Tools (`presentation.py`):**

- `create_visualization()` - Create charts (matplotlib, altair)
- `save_html_report()` - Generate HTML reports

**Memory Tools (`memory.py`):**

- `memory_toolset` - Create/search/update agent memories

**Ticketing Tools (`ticketing.py`):**

- `ticketing_toolset` - Create/read/update tickets

**Todo Tools (`todos.py`):**

- `todo_list_manager_toolset` - Manage todo lists

### 5. Types (`pydantic/types.py`)

Shared type definitions:

```python
@dataclass
class AgentDeps:
    """Dependencies injected into all agents."""
    lineage: LineageStorage
    data_backend: Optional[DataQueryBackend] = None
    memory_backend: Optional[MemoryStorage] = None
    ticket_storage: Optional[TicketStorage] = None
    todo_list_manager: TodoListManager = TodoListManager()
    user_id: Optional[str] = None  # For user-specific memory
    org_id: str = "default"  # For organization-wide memory
    agent_name: str = "agent"
    state: AgentState = field(default_factory=AgentState)  # AG-UI state

class AgentState(BaseModel):
    """State container for AG-UI protocol."""
    tool_results: Dict[str, BaseModel] = Field(default_factory=dict)
    thinking_blocks: List[ThinkingBlock] = Field(default_factory=list)
    current_todos: List[TodoItem] = Field(default_factory=list)
    current_specialist: Optional[str] = None
    last_query: Optional[str] = None
```

**Tool Result Models:**
The module also defines typed result models for all tools (e.g., `QueryGraphResult`, `ExecuteQueryResult`, `CreateVisualizationResult`) to ensure type-safe tool returns.

### 6. Prompt Templates (`pydantic/prompts/`)

YAML files with Jinja2 templating:

- `.yaml` - Static prompts
- `.yaml.j2` - Dynamic prompts with backend-specific hints

**Template Variables:**

- `{{ sql_hints }}` - SQL dialect hints from data backend
- `{{ graph_schema }}` - Lineage graph schema from lineage backend

## Common Workflows

### Adding a New Agent

1. **Create factory function in `orchestrator.py`:**

```python
def create_my_new_agent_orchestrator(
    lineage: LineageStorage,
    data_backend: DataQueryBackend,
    memory_backend: Optional[MemoryStorage] = None,
    ticket_storage: Optional[TicketStorage] = None,
    model: str = "anthropic:claude-haiku-4-5",
) -> tuple[Agent, AgentDeps]:
    """Create my new agent with appropriate tools."""

    # Load prompt with hints
    system_prompt = load_prompt("my_new_agent", data_backend, lineage)

    # Attach tools
    tools = [
        Tool(query_graph),
        Tool(execute_query),
        # ... other tools
    ]

    agent = Agent(
        model=create_model(model),
        deps_type=AgentDeps,
        system_prompt=system_prompt,
        tools=tools,
    )

    deps = AgentDeps(
        lineage=lineage,
        data_backend=data_backend,
        memory_backend=memory_backend,
        ticket_storage=ticket_storage,
    )

    return agent, deps
```

2. **Create prompt file:**
   - Add `prompts/my_new_agent.yaml` or `.yaml.jinja`
   - Include system prompt and tool usage guidelines

3. **Add to WebUI** (optional):
   - Update `webui/backend_pydantic.py` to expose the new agent
   - Add a new page in `webui/frontend/app/my-agent/page.tsx`

4. **Add to CLI** (optional):
   - Update `cli_agents.py` to initialize the new agent
   - Export as module-level variable for `clai` command

### Running CLI Agents

```bash
# Set config path
export UNIFIED_CONFIG=/path/to/config.yml

# Run data analyst agent (interactive)
clai -m lineage.agent.pydantic.cli_agents analyst

# Ask a single question
clai -m lineage.agent.pydantic.cli_agents analyst "What are the top 5 customers by ARR?"

# Run data engineer agent
clai -m lineage.agent.pydantic.cli_agents engineer "Design a new mart for churn analysis"

# Run data quality agent
clai -m lineage.agent.pydantic.cli_agents quality "Find failed runs in the last week"
```

### Integrating with CopilotKit WebUI

See `ag_ui_handler.py` for CopilotKit integration:

```python
from lineage.agent.pydantic.ag_ui_handler import create_orchestrator_with_ui

# Create orchestrator with AG-UI streaming
agent = create_orchestrator_with_ui(
    deps=agent_deps,
    model=model,
)

# Run with AG-UI context
result = await agent.run(
    user_message,
    deps=deps,
    context=AgentContext(session_id="...", ...),
)
```

## Testing

```bash
# Test orchestrator delegation logic
uv run pytest tests/agent/test_orchestrator.py

# Test specific tools
uv run pytest tests/agent/test_tools.py -k test_query_graph

# Test CLI agents
uv run pytest tests/agent/test_cli_agents.py
```

## Configuration

Agents are configured via `UnifiedConfig` (see `backends/config.py`):

```yaml
lineage:
  type: kuzu
  db_path: lineage_store/lineage.kuzu

data_query:
  type: duckdb
  db_path: demo_finance.duckdb
  allowed_schemas: [marts]
  allowed_tables: ["fct_*", "dim_*"]

memory:
  type: falkordb
  host: localhost
  port: 6379
  graph_name: agent_memory

tickets:
  type: filesystem
  base_path: ./tickets
```

## Key Design Patterns

### 1. Protocol-Based Backends

All agents use protocol interfaces (`LineageStorage`, `DataQueryBackend`, etc.) rather than concrete implementations. This enables:

- Backend swapping without agent code changes
- Testing with mock backends
- Multi-backend support

### 2. Dependency Injection

`AgentDeps` dataclass provides all backend dependencies:

- Injected at agent creation time
- Shared across orchestrator and specialists
- Immutable during execution

### 3. Tool Composition

Tools are composed into toolsets:

```python
memory_toolset = [create_memory, search_memories, update_memory]
ticketing_toolset = [create_ticket, read_ticket, update_ticket]
```

### 4. Prompt Templating

Jinja2 templates inject backend-specific context:

- SQL dialect hints for data backend
- Graph schema for lineage backend
- Reduces hallucinations by providing concrete examples

## Troubleshooting

### Agent Not Delegating to Specialists

**Symptom:** Orchestrator tries to execute queries directly instead of delegating.

**Cause:** Orchestrator has access to execution tools (should only have delegation tools).

**Solution:** Check `orchestrator.py` tool definitions - orchestrator should only have:

- Delegation tools (`delegate_to_*`)
- Memory/ticketing/todo tools (for planning)

### Tool Calls Not Visible in UI

**Symptom:** Tool executions happen but aren't shown in CopilotKit UI.

**Cause:** Not using native PydanticAI `@agent.tool` decorators.

**Solution:** Ensure all tools use `@agent.tool` decorator in agent definitions.

### Prompt Template Rendering Errors

**Symptom:** `KeyError` or `UndefinedError` when loading prompts.

**Cause:** Missing template variables or incorrect Jinja syntax.

**Solution:**

1. Check `load_prompt()` provides all required template variables
2. Validate Jinja syntax in `.yaml.jinja` files
3. Use `{{ variable | default('fallback') }}` for optional variables

## Related Documentation

- **Backends:** `../backends/README.md` - Protocol definitions and adapters
- **Ingestion:** `../ingest/README.md` - Data loading pipelines
- **Architecture:** `../../docs/architecture/SUBAGENT_ARCHITECTURE.md` - High-level design
- **Tools Reference:** `../../docs/reference/TOOL_CATALOG.md` - Comprehensive tool documentation
