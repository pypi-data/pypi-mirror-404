# Backends

This module provides protocol-based storage backend implementations for lineage graphs, data queries, memory, tickets, and todos. All backends follow a consistent protocol interface pattern, enabling easy swapping of implementations without changing calling code.

## Design Philosophy

The backends module follows a **protocol-oriented design**:

1. **Protocol Definition** - Abstract interface using Python's `Protocol` type
2. **Multiple Implementations** - Concrete adapters for different technologies
3. **Factory Pattern** - Create instances from unified configuration
4. **Type Safety** - Runtime-checkable protocols ensure implementation compliance

**Benefits:**

- Swap backends without changing agent code
- Test with mock backends
- Support multiple backend types simultaneously
- Type-safe polymorphism with static checking

## Architecture Overview

```
Agent System
     ↓
Protocols (Abstract Interfaces)
  ├─→ LineageStorage (graph databases)
  ├─→ DataQueryBackend (data warehouses)
  ├─→ MemoryStorage (agent memory)
  ├─→ TicketStorage (task management)
  └─→ TodoManager (todo lists)
     ↓
Implementations (Concrete Adapters)
  ├─→ KuzuAdapter, FalkorDBAdapter, Neo4jAdapter, PostgresAGEAdapter
  ├─→ DuckDBBackend, SnowflakeBackend, MCPBackend
  ├─→ FalkorDBMemoryAdapter
  ├─→ FilesystemTicketBackend
  └─→ TodoListManager
     ↓
Underlying Technology
  ├─→ KùzuDB, FalkorDB, Neo4j, PostgreSQL+AGE
  ├─→ DuckDB, Snowflake, MCP Servers
  └─→ Graphiti (temporal knowledge graphs)
```

## Directory Structure

```bash
backends/
├── lineage/                    # Lineage graph storage (property graphs)
│   ├── protocol.py             # LineageStorage protocol definition
│   ├── factory.py              # Factory for creating lineage backends
│   ├── base.py                 # Base adapter with shared utilities
│   ├── kuzu_adapter.py         # KùzuDB implementation (embedded)
│   ├── falkordb_adapter.py     # FalkorDB implementation (Redis-based)
│   ├── neo4j_adapter.py        # Neo4j implementation (server-based)
│   ├── postgres_age_adapter.py # PostgreSQL+AGE implementation
│   ├── schema_loader.py        # Graph schema loading (DDL)
│   └── models/                 # Pydantic models for graph data
│       ├── base.py             # Base node/edge classes
│       ├── dbt.py              # dbt model/source/column nodes
│       ├── semantic_analysis.py # Semantic metadata nodes
│       ├── semantic_views.py   # Snowflake semantic view nodes
│       ├── openlineage.py      # OpenLineage job/run/dataset nodes
│       ├── clustering.py       # Join cluster nodes
│       ├── profiling.py        # Data profile nodes
│       ├── tickets.py          # Ticket nodes
│       ├── edges.py            # Edge/relationship definitions
│       └── dto.py              # Data transfer objects
├── data_query/                 # Data warehouse query backends
│   ├── protocol.py             # DataQueryBackend protocol definition
│   ├── factory.py              # Factory for creating data backends
│   ├── duckdb_backend.py       # DuckDB implementation (embedded OLAP)
│   ├── snowflake_backend.py    # Snowflake implementation (cloud warehouse)
│   ├── mcp.py                  # MCP server integration
│   └── config.py               # Configuration models
├── memory/                     # Agent memory storage
│   ├── protocol.py             # MemoryStorage protocol definition
│   ├── factory.py              # Factory for creating memory backends
│   ├── falkordb_adapter.py     # FalkorDB+Graphiti implementation
│   └── models.py               # Episode, MemoryResult models
├── tickets/                    # Ticket management backends
│   ├── protocol.py             # TicketStorage protocol definition
│   ├── factory.py              # Factory for creating ticket backends
│   └── filesystem_backend.py   # Filesystem-based tickets
├── todos/                      # Todo list management
│   └── todo_manager.py         # In-memory todo list manager
├── config.py                   # Unified configuration (YAML-based)
├── types.py                    # Shared enums (LineageStorageType, DataBackendType)
└── mcp_auto.py                 # Auto-discover MCP servers
```

## Backend Types

### 1. Lineage Storage (`lineage/`)

**Purpose:** Store and query property graph representations of data lineage (dbt models, semantic metadata, OpenLineage events).

**Protocol:** `LineageStorage` (defined in `protocol.py`)

**Key Methods:**

```python
# Core node/edge operations (synchronous)
def upsert_node(node: BaseNode) -> None
def create_edge(from_node: Union[BaseNode, NodeIdentifier],
                to_node: Union[BaseNode, NodeIdentifier],
                edge: GraphEdge) -> None

# Querying
def query(cypher: str, params: dict) -> List[Dict]
def get_node(node_type: str, node_id: str) -> Optional[Dict]

# Semantic metadata
def get_semantic_view_schema(view_id: str) -> Optional[Dict]
def list_semantic_views() -> List[Dict]
def list_semantic_measures() -> List[Dict]

# Clustering
def create_join_edges(edges: List[JoinEdge]) -> None
def cluster_by_joins(min_cluster_size: int) -> List[ClusterInfo]
```

**Implementations:**

| Backend                | Technology        | Use Case                                                | Status        |
| ---------------------- | ----------------- | ------------------------------------------------------- | ------------- |
| **KuzuAdapter**        | KùzuDB (embedded) | Single-user, local development, embedded apps           | ✅ Production |
| **FalkorDBAdapter**    | FalkorDB (Redis)  | Multi-user, cloud deployment, fast graph queries        | ✅ Production |
| **Neo4jAdapter**       | Neo4j (server)    | Enterprise, advanced graph algorithms, Cypher ecosystem | ✅ Production |
| **PostgresAGEAdapter** | PostgreSQL+AGE    | Existing Postgres infrastructure, unified storage       | ✅ Beta       |

**Graph Schema:**

- 23 typed node types (DbtModel, DbtSource, DbtColumn, SemanticAnalysis, BusinessMeasure, BusinessDimension, SemanticView, etc.)
- 40+ typed relationship types (DEPENDS_ON, HAS_SEMANTIC_ANALYSIS, JOINS_WITH, HAS_MEASURE, etc.)
- See `models/` directory for Pydantic model definitions
- See `schema.yaml` for introspection schema

**Factory Usage:**

```python
from lineage.backends.config import UnifiedConfig
from lineage.backends.lineage.factory import create_storage

config = UnifiedConfig.from_yaml(Path("config.yml"))
storage = create_storage(config.lineage, read_only=False)

# Use protocol methods (synchronous)
storage.upsert_node(model_node)
results = storage.query("MATCH (m:DbtModel) RETURN m LIMIT 10", {})
```

### 2. Data Query Backend (`data_query/`)

**Purpose:** Execute SQL queries against data warehouses for data preview, analysis, and reporting.

**Protocol:** `DataQueryBackend` (defined in `protocol.py`)

**Key Methods:**

```python
# Query execution
async def execute_query(query: str, limit: int = None) -> QueryResult
async def validate_query(query: str) -> QueryValidationResult

# Schema discovery
async def list_databases() -> List[str]
async def list_schemas(database: str) -> List[str]
async def list_tables(database: str, schema: str) -> List[str]
async def get_table_schema(database: str, schema: str, table: str) -> TableSchema

# Data preview
async def preview_table(database: str, schema: str, table: str, limit: int) -> TablePreview

# Profiling
async def profile_table(database: str, schema: str, table: str) -> TableProfile

# Semantic views (Snowflake)
async def list_semantic_views() -> List[SemanticViewData]
async def query_semantic_view(view_name: str, ...) -> QueryResult
```

**Implementations:**

| Backend              | Technology        | Use Case                                    | Status        |
| -------------------- | ----------------- | ------------------------------------------- | ------------- |
| **DuckDBBackend**    | DuckDB (embedded) | Local analytics, prototyping, CI/CD testing | ✅ Production |
| **SnowflakeBackend** | Snowflake (cloud) | Enterprise data warehouse, semantic models  | ✅ Production |
| **MCPBackend**       | MCP Servers       | Connect to any MCP-enabled data source      | ✅ Beta       |

**SQL Dialect Hints:**
Each backend provides SQL dialect hints for agents:

```python
backend.get_sql_hints()
# Returns hints like "DuckDB uses || for string concat"
# or "Snowflake requires IDENTIFIER() for dynamic tables"
```

**Factory Usage:**

```python
from lineage.backends.config import UnifiedConfig
from lineage.backends.data_query.factory import create_backend

config = UnifiedConfig.from_yaml(Path("config.yml"))
data_backend = create_backend(config.data)

# Execute queries
result = await data_backend.execute_query("SELECT * FROM marts.fct_revenue")
print(result.rows)
```

### 3. Memory Storage (`memory/`)

**Purpose:** Store and retrieve agent memory using temporal knowledge graphs (preferences, learned patterns, context).

**Protocol:** `MemoryStorage` (defined in `protocol.py`)

**Key Methods:**

```python
# User-specific memory
async def store_user_memory(user_id: str, episode: Episode) -> None
async def search_user_memory(user_id: str, query: str, limit: int) -> List[MemoryResult]

# Organization-wide memory
async def store_org_memory(org_id: str, episode: Episode) -> None
async def search_org_memory(org_id: str, query: str, limit: int) -> List[MemoryResult]

# Hybrid search (user + org)
async def search_all(user_id: str, org_id: str, query: str, limit: int) -> List[MemoryResult]
```

**Implementations:**

| Backend                   | Technology          | Use Case                               | Status        |
| ------------------------- | ------------------- | -------------------------------------- | ------------- |
| **FalkorDBMemoryAdapter** | FalkorDB + Graphiti | Multi-tenant temporal knowledge graphs | ✅ Production |

**Memory Types (Episode):**

- `USER_PREFERENCE` - User preferences (e.g., "prefers bar charts")
- `DATA_PATTERN` - Learned data patterns (e.g., "ARR is stored in fct_arr_reporting_monthly")
- `INSIGHT` - Business insights (e.g., "churn rate increased in Q3")
- `QUERY_HISTORY` - Frequently asked questions and answers

**Factory Usage:**

```python
from lineage.backends.config import UnifiedConfig
from lineage.backends.memory.factory import create_memory

config = UnifiedConfig.from_yaml(Path("config.yml"))
memory = create_memory(config.memory)

# Store and search memories
from lineage.backends.memory.models import Episode, EpisodeType

episode = Episode(
    name="chart_preference",
    content="User alice prefers line charts for time series",
    episode_type=EpisodeType.USER_PREFERENCE,
    source_description="Analyst session 2025-01-24"
)
await memory.store_user_memory(user_id="alice", episode=episode)

results = await memory.search_user_memory(user_id="alice", query="chart preferences")
```

### 4. Ticket Storage (`tickets/`)

**Purpose:** Manage task tickets for data quality issues, pipeline failures, or feature requests.

**Protocol:** `TicketStorage` (defined in `protocol.py`)

**Key Methods:**

```python
async def create_ticket(ticket: Ticket) -> str  # Returns ticket_id
async def read_ticket(ticket_id: str) -> Optional[Ticket]
async def update_ticket(ticket_id: str, updates: Dict[str, Any]) -> None
async def list_tickets(status: Optional[str], assignee: Optional[str]) -> List[Ticket]
async def search_tickets(query: str) -> List[Ticket]
```

**Implementations:**

| Backend                     | Technology | Use Case                         | Status        |
| --------------------------- | ---------- | -------------------------------- | ------------- |
| **FilesystemTicketBackend** | JSON files | Local development, prototyping   | ✅ Production |
| (Future) **JiraBackend**    | Jira API   | Enterprise ticketing integration | 🚧 Planned    |

**Factory Usage:**

```python
from lineage.backends.config import UnifiedConfig
from lineage.backends.tickets.factory import create_ticket_storage

config = UnifiedConfig.from_yaml(Path("config.yml"))
tickets = create_ticket_storage(config.tickets)

# Create ticket
ticket_id = await tickets.create_ticket(Ticket(
    title="Fix ARR calculation",
    description="ARR calculation in fct_arr_reporting_monthly is incorrect",
    status="open",
    priority="high"
))
```

### 5. Todo Manager (`todos/`)

**Purpose:** Manage in-memory todo lists for agent task tracking.

**Implementation:** `TodoListManager` (in-memory only, no protocol needed)

**Usage:**

```python
from lineage.backends.todos.todo_manager import TodoListManager

todos = TodoListManager()
todos.add_todo("Load dbt artifacts")
todos.add_todo("Run semantic analysis")
todos.mark_completed(0)
print(todos.get_all())  # List all todos with status
```

## Configuration

All backends are configured via a unified YAML configuration file (`config.yml`):

```yaml
# config.yml
lineage:
  backend: falkordb # kuzu | falkordb | neo4j | postgres_age
  host: localhost
  port: 6379
  graph_name: lineage_graph
  population:
    model: google/gemini-2.5-flash-lite
    max_semantic_workers: 64
    enable_semantic: true
    enable_clustering: true

data:
  backend: snowflake # duckdb | snowflake | mcp
  account: ${SNOWFLAKE_ACCOUNT} # Environment variable interpolation
  username: ${SNOWFLAKE_USER}
  password: ${SNOWFLAKE_PASSWORD}
  warehouse: COMPUTE_WH
  database: ANALYTICS
  allowed_schemas: [marts]
  allowed_tables: ["fct_*", "dim_*"]

memory:
  backend: falkordb
  host: localhost
  port: 6379

tickets:
  backend: filesystem
  base_path: ./tickets

agent:
  analyst:
    model: anthropic:claude-haiku-4-5
  data_engineer:
    model: anthropic:claude-sonnet-4-5-20250929
```

**Loading Configuration:**

```python
from lineage.backends.config import UnifiedConfig
from pathlib import Path

config = UnifiedConfig.from_yaml(Path("config.yml"))

# Access sub-configs
print(config.lineage.backend)  # "falkordb"
print(config.data.backend)     # "snowflake"
print(config.agent.analyst.model)  # "anthropic:claude-haiku-4-5"
```

**Environment Variable Interpolation:**
Use `${VAR_NAME}` syntax to reference environment variables:

```yaml
data:
  password: ${SNOWFLAKE_PASSWORD} # Resolves to os.environ["SNOWFLAKE_PASSWORD"]
```

## Common Workflows

### Adding a New Lineage Backend

1. **Define Protocol Implementation:**

```python
# lineage/my_new_adapter.py
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.lineage.models.base import BaseNode, GraphEdge

class MyNewAdapter:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def upsert_node(self, node: BaseNode) -> None:
        # Implementation...
        pass

    async def create_edge(self, edge: GraphEdge) -> None:
        # Implementation...
        pass

    # ... implement all protocol methods
```

2. **Add Configuration Model:**

```python
# config.py
class MyNewLineageConfig(BaseLineageConfig):
    backend: Literal["my_new_backend"] = "my_new_backend"
    connection_string: str
```

3. **Update Factory:**

```python
# lineage/factory.py
def create_storage(config: LineageConfig, read_only: bool = False) -> LineageStorage:
    # ...
    elif isinstance(config, MyNewLineageConfig):
        from .my_new_adapter import MyNewAdapter
        return MyNewAdapter(connection_string=config.connection_string)
```

4. **Update Type Enum:**

```python
# types.py
class LineageStorageType(str, Enum):
    # ...
    MY_NEW_BACKEND = "my_new_backend"
```

### Adding a New Data Backend

Similar pattern as lineage backend:

1. Implement `DataQueryBackend` protocol
2. Add config model to `config.py`
3. Update `data_query/factory.py`
4. Update `DataBackendType` enum

### Testing with Mock Backends

```python
from typing import List, Dict, Any, Optional
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.lineage.models.base import BaseNode, GraphEdge

class MockLineageStorage:
    """Mock implementation for testing."""

    def __init__(self):
        self.nodes: Dict[str, BaseNode] = {}
        self.edges: List[GraphEdge] = []

    async def upsert_node(self, node: BaseNode) -> None:
        self.nodes[node.id] = node

    async def create_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)

    async def query(self, cypher: str, params: dict) -> List[Dict]:
        return []  # Simplified for testing

# Use in tests
mock_storage: LineageStorage = MockLineageStorage()
```

## Key Design Patterns

### 1. Protocol-Oriented Design

Use `Protocol` for interface definitions:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class LineageStorage(Protocol):
    async def upsert_node(self, node: BaseNode) -> None: ...
    async def query(self, cypher: str, params: dict) -> List[Dict]: ...
```

**Benefits:**

- Structural subtyping (duck typing with type safety)
- Runtime type checking with `isinstance(obj, Protocol)`
- No inheritance required

### 2. Factory Pattern

Use factory functions for object creation:

```python
def create_storage(config: LineageConfig, read_only: bool = False) -> LineageStorage:
    if isinstance(config, KuzuLineageConfig):
        return KuzuAdapter(config=config, read_only=read_only)
    elif isinstance(config, Neo4jLineageConfig):
        return Neo4jAdapter(uri=config.uri, ...)
    # ...
```

**Benefits:**

- Centralized instantiation logic
- Type-safe configuration handling
- Easy to add new backends

### 3. Unified Configuration

Single YAML file for all backends:

```python
class UnifiedConfig(BaseModel):
    lineage: LineageConfig
    data: DataConfig
    memory: Optional[MemoryConfig] = None
    tickets: Optional[TicketConfig] = None
    agent: AgentConfig = Field(default_factory=AgentConfig)
```

**Benefits:**

- Single source of truth
- Environment-specific configs (dev/staging/prod)
- Type-safe with Pydantic validation

### 4. Dependency Injection

Inject backends into agents via `AgentDeps`:

```python
@dataclass
class AgentDeps:
    lineage: LineageStorage
    data: DataQueryBackend
    memory: MemoryStorage
    tickets: TicketStorage
```

**Benefits:**

- Loose coupling
- Easy testing with mocks
- Clear dependencies

## Testing

```bash
# Test specific backend
uv run pytest tests/backends/test_kuzu_adapter.py -v

# Test protocol compliance
uv run pytest tests/backends/test_protocols.py

# Test factories
uv run pytest tests/backends/test_factories.py

# Integration tests (require running services)
uv run pytest tests/backends/integration/ -m integration
```

## Migration Guide

### Switching Lineage Backends

To switch from KùzuDB to FalkorDB:

1. **Update config.yml:**

```yaml
# Before
lineage:
  backend: kuzu
  db_path: lineage_store/lineage.kuzu

# After
lineage:
  backend: falkordb
  host: localhost
  port: 6379
  graph_name: lineage_graph
```

2. **Re-initialize schema:**

```bash
uv run lineage init --config config.yml
```

3. **Reload data:**

```bash
uv run lineage load-dbt-full ../dbt_project/target/ --config config.yml
```

**No code changes required!** Agents automatically use the new backend via protocols.

## Troubleshooting

### Backend Not Found Error

**Symptom:** `ValueError: Unknown lineage config type`

**Cause:** Config specifies an unknown backend type.

**Solution:**

1. Check `config.yml` for typos in `backend:` field
2. Ensure backend type is in `types.py` enum
3. Verify factory has handler for this config type

### Protocol Compliance Error

**Symptom:** `TypeError: 'MyAdapter' object does not implement protocol 'LineageStorage'`

**Cause:** Adapter implementation missing required protocol methods.

**Solution:**

1. Check protocol definition for all required methods
2. Ensure method signatures match exactly
3. Use type checker: `mypy src/lineage/backends/`

### Configuration Loading Error

**Symptom:** `ValidationError` when loading config

**Cause:** Invalid configuration format or missing required fields.

**Solution:**

1. Validate YAML syntax
2. Check all required fields are present
3. Use environment variables for secrets: `${VARIABLE_NAME}`

## Related Documentation

- **Agent System:** `../agent/README.md` - How agents use backends
- **Ingestion:** `../ingest/README.md` - How data is loaded into backends
- **Architecture:** `../../docs/architecture/ARCHITECTURE.md` - System design
- **Configuration:** `../../docs/reference/CONFIGURATION.md` - Detailed config reference
