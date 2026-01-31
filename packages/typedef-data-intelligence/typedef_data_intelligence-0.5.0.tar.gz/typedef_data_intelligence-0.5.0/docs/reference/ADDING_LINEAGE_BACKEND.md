# Adding a New LineageStorage Backend

This guide documents the standardized process for implementing a new lineage storage backend. Follow these steps to add support for a new graph database (e.g., FalkorDB, ArangoDB, TigerGraph).

## Table of Contents

1. [Overview](#overview)
2. [LineageStorage Protocol](#lineagestorage-protocol)
3. [Implementation Checklist](#implementation-checklist)
4. [Step-by-Step Guide](#step-by-step-guide)
5. [Code Style Requirements](#code-style-requirements)
6. [Testing & Validation](#testing--validation)
7. [Example: FalkorDB Adapter](#example-falkordb-adapter)

## Overview

The lineage storage system uses a **protocol-based architecture** where all backends implement the same `LineageStorage` protocol. This enables:

- **Backend Swappability**: Switch between FalkorDB, FalkorDBLite, or other graph databases without changing calling code
- **Minimal Implementation**: Only 2 core methods required (`upsert_node`, `create_edge`)
- **Type Safety**: Pydantic models for nodes and edges with validation
- **Unified Configuration**: Single YAML config format for all backends

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    LineageStorage Protocol                   │
│  • upsert_node(node: BaseNode)                              │
│  • create_edge(from_node, to_node, edge: GraphEdge)         │
│  • execute_raw_query(query: str) → RawLineageQueryResult    │
│  • get_graph_schema() → Dict[str, Any]                      │
│  • find_models_by_relation(...) → List[str]                 │
│  • compute_join_graph(), cluster_join_graph(), etc.         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │ implements
         ┌────────────────────┼────────────────────┐
         │                    │                    │
┌────────▼────────┐  ┌────────▼────────┐  ┌───────▼──────┐
│ FalkorDBLite    │  │ FalkorDB        │  │ YourAdapter  │
│ (embedded)      │  │ (client/server) │  │ (new!)       │
└─────────────────┘  └─────────────────┘  └──────────────┘
```

## LineageStorage Protocol

### Core Methods (Required)

#### 1. `upsert_node(node: BaseNode) -> None`

Create or update a node in the graph. The node is a Pydantic model that includes:

- `node.node_label` (ClassVar): NodeLabel enum value (e.g., `NodeLabel.DBT_MODEL`)
- `node.id` (computed property): Unique identifier
- `node.model_dump()`: All properties as a dict

**Example:**

```python
from lineage.backends.lineage.models.semantic_views import SemanticView

view = SemanticView(
    name="sv_arr_reporting",
    database="DEMO_DB",
    schema="MARTS",
    provider="snowflake",
    measures=[...],
)

storage.upsert_node(view)
# Creates node with:
#   label: "SemanticView"
#   id: "semantic_view.snowflake.DEMO_DB.MARTS.sv_arr_reporting"
#   properties: {name: "sv_arr_reporting", database: "DEMO_DB", ...}
```

**Implementation pattern:**

```python
def upsert_node(self, node: BaseNode) -> None:
    label = node.node_label.value  # Extract string from enum
    id = node.id  # Use computed property
    properties = node.model_dump()  # Get all properties

    # Backend-specific upsert logic
    # For Cypher-based: MERGE (n:Label {id: $id}) SET n = $properties
    # For AQL-based: UPSERT {_key: $id} INSERT $properties UPDATE $properties
```

#### 2. `create_edge(from_node, to_node, edge: GraphEdge) -> None`

Create a relationship between two nodes. Accepts:

- `from_node`: Either a `BaseNode` object or `NodeIdentifier` (lightweight ID+label)
- `to_node`: Either a `BaseNode` object or `NodeIdentifier`
- `edge`: A `GraphEdge` Pydantic model with edge type and properties

**Example:**

```python
from lineage.backends.lineage.models import DbtModel, NodeIdentifier, DependsOn
from lineage.backends.types import NodeLabel

# Option 1: With full node objects
model_a = DbtModel(name="orders", ...)
model_b = DbtModel(name="customers", ...)
edge = DependsOn(type="model", direct=True)
storage.create_edge(model_a, model_b, edge)

# Option 2: With lightweight identifiers (when you only have IDs)
from_id = NodeIdentifier(id="model.demo.orders", node_label=NodeLabel.DBT_MODEL)
to_id = NodeIdentifier(id="model.demo.customers", node_label=NodeLabel.DBT_MODEL)
edge = DependsOn(type="model", direct=True)
storage.create_edge(from_id, to_id, edge)
```

**Implementation pattern:**

```python
from typing import Union
from lineage.backends.lineage.models.base import BaseNode, NodeIdentifier, GraphEdge


def create_edge(
    self,
    from_node: Union[BaseNode, NodeIdentifier],
    to_node: Union[BaseNode, NodeIdentifier],
    edge: GraphEdge,
) -> None:
    # Extract IDs and labels
    from_id = from_node.id if isinstance(from_node, BaseNode) else from_node.id
    from_label = from_node.node_label if isinstance(from_node, BaseNode) else from_node.node_label
    to_id = to_node.id if isinstance(to_node, BaseNode) else to_node.id
    to_label = to_node.node_label if isinstance(to_node, BaseNode) else to_node.node_label

    # Extract edge type and properties
    edge_type = edge.edge_type.value  # EdgeType enum → string
    properties = edge.model_dump()  # All edge properties

    # Backend-specific edge creation logic
    # For Cypher: MERGE (a:FromLabel {id: $from_id})-[r:EDGE_TYPE]->(b:ToLabel {id: $to_id}) SET r = $properties
```

#### 3. `execute_raw_query(query: str) -> RawLineageQueryResult`

Execute a query in the backend's native language (Cypher, AQL, etc.) and return standardized results.

**Returns:**

```python
class RawLineageQueryResult(BaseModel):
    rows: List[Dict[str, Any]]  # List of result rows as dicts
    count: int                   # Number of rows
    query: str                   # The executed query
```

**Example:**

```python
result = storage.execute_raw_query("MATCH (m:DbtModel) RETURN m.name, m.schema")
for row in result.rows:
    print(row["name"], row["schema"])
```

### Query Methods

#### 4. `get_graph_schema() -> Dict[str, Any]`

Return the complete graph schema. Default implementation loads from `schema.yaml`, but backends with native introspection (like KùzuDB) can override.

**Returns:**

```python
{
    "node_tables": {
        "Model": {"columns": {"id": "STRING", "name": "STRING", ...}},
        "Source": {"columns": {...}},
        ...
    },
    "relationship_tables": {
        "DEPENDS_ON": {"columns": {"type": "STRING", "direct": "BOOLEAN"}},
        ...
    }
}
```

#### 5. `find_models_by_relation(database, schema, table) -> List[str]`

Find model IDs matching a table reference. Used for linking semantic views to dbt models.

**Default implementation** (Cypher-based, provided by `BaseLineageStorage`):

```python
def find_models_by_relation(self, *, database: Optional[str] = None, schema: str, table: str) -> List[str]:
    query = f"""
        MATCH (m:DbtModel)
        WHERE LOWER(m.schema) = LOWER('{schema}')
          AND LOWER(m.name) = LOWER('{table}')
        RETURN m.id AS model_id
    """
    result = self.execute_raw_query(query)
    return [row["model_id"] for row in result.rows]
```

### Optional Methods

These have default implementations in `BaseLineageStorage` but can be overridden for optimization:

- `find_upstream(node_id: str, depth: int) -> List[str]`: Find upstream dependencies
- `compute_join_graph() -> List[JoinEdge]`: Compute join graph from semantic analysis
- `cluster_join_graph(min_count: int) -> Dict[int, List[str]]`: Cluster models by joins
- `store_clusters(clusters: Dict[int, List[str]]) -> None`: Store join clusters
- `get_clusters() -> List[ClusterInfo]`: Retrieve join clusters

## Implementation Checklist

- [ ] **Step 1**: Add backend type to `LineageStorageType` enum
- [ ] **Step 2**: Create backend configuration class (Pydantic model)
- [ ] **Step 3**: Implement adapter class
  - [ ] Connection/initialization logic
  - [ ] `upsert_node()` method
  - [ ] `create_edge()` method
  - [ ] `execute_raw_query()` method
  - [ ] `ensure_schema()` method (create indexes/constraints)
  - [ ] `recreate_schema()` method (drop all data)
  - [ ] `get_agent_hints()` method (query language documentation)
  - [ ] Optional: Override `get_graph_schema()` if backend has introspection
- [ ] **Step 4**: Update factory to instantiate your adapter
- [ ] **Step 5**: Create example configuration file
- [ ] **Step 6**: Add Python client library to dependencies
- [ ] **Step 7**: Test with real dbt project

## Step-by-Step Guide

### Step 1: Add Backend Type to Enum

**File:** `src/lineage/backends/types.py`

Add your backend to the `LineageStorageType` enum:

```python
class LineageStorageType(str, Enum):
    """Lineage storage backend types."""

    FALKORDB = "falkordb"
    FALKORDBLITE = "falkordblite"
    YOUR_BACKEND = "your_backend"  # ← Add your backend here
```

### Step 2: Create Configuration Class

**File:** `src/lineage/backends/config.py`

Add a Pydantic configuration model for your backend:

```python
class FalkorDBLineageConfig(BaseLineageConfig):
    """FalkorDB lineage backend configuration."""

    backend: Literal["falkordb"] = "falkordb"
    host: str = Field(default="localhost", description="FalkorDB host")
    port: int = Field(default=6379, ge=1, le=65535, description="FalkorDB port")
    password: str = Field(..., description="FalkorDB password (use ${ENV_VAR} for security)")
    graph_name: str = Field(default="lineage", description="FalkorDB graph name")
```

Then add to the `LineageConfig` union:

```python
LineageConfig = Union[
    FalkorDBLineageConfig,
    FalkorDBLiteLineageConfig,
    YourBackendLineageConfig,  # ← Add here
]
```

### Step 3: Implement Adapter

**File:** `src/lineage/backends/lineage/falkordb_adapter.py`

Create your adapter class. Use **absolute imports** at the top of the file:

````python
"""FalkorDB adapter implementing LineageStorage protocol.

FalkorDB is a Redis-based graph database with Cypher query support.
Key characteristics:
- Redis protocol (default port 6379)
- Cypher query language (with some limitations)
- Manual index creation required
- No regex support, no temporal arithmetic
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Union

# Absolute imports (preferred style)
from lineage.backends.lineage.base import BaseLineageStorage
from lineage.backends.lineage.protocol import RawLineageQueryResult
from lineage.backends.types import EdgeType, NodeLabel
from lineage.backends.lineage.models.base import BaseNode, NodeIdentifier, GraphEdge

logger = logging.getLogger(__name__)

try:
    from falkordb import FalkorDB
except ImportError as exc:
    raise ImportError(
        "falkordb is required for FalkorDB backend. Install with: pip install falkordb"
    ) from exc


class FalkorDBAdapter(BaseLineageStorage):
    """FalkorDB adapter implementing LineageStorage protocol.

    This adapter connects to FalkorDB (Redis-based graph database) and implements
    the minimal LineageStorage interface: upsert_node(), create_edge(), execute_raw_query().

    All specific node/edge operations are inherited from BaseLineageStorage.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: str = "",
        graph_name: str = "lineage",
        read_only: bool = False,
    ):
        """Initialize FalkorDB adapter.

        Args:
            host: FalkorDB/Redis host
            port: FalkorDB/Redis port (default: 6379)
            password: Authentication password
            graph_name: Name of the graph to use
            read_only: If True, prevent write operations
        """
        self.host = host
        self.port = port
        self.password = password
        self.graph_name = graph_name
        self.read_only = read_only

        # Create client
        self.client = FalkorDB(host=host, port=port, password=password)

        # Select graph
        self.graph = self.client.select_graph(graph_name)

        logger.info(f"Connected to FalkorDB at {host}:{port}, graph={graph_name} (read_only={read_only})")

    def close(self):
        """Close the FalkorDB client connection."""
        if self.client:
            # FalkorDB client may not have explicit close, but Redis connection does
            # self.client.close()  # Check FalkorDB API
            logger.info("FalkorDB connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # ---- Schema Management ----

    def ensure_schema(self) -> None:
        """Create indexes on commonly queried properties.

        FalkorDB requires manual index creation (no automatic indexing).
        Note: FalkorDB may not support unique constraints.
        """
        if self.read_only:
            logger.warning("Cannot ensure schema in read-only mode")
            return

        indexes = [
            # Node indexes
            "CREATE INDEX FOR (n:Model) ON (n.id)",
            "CREATE INDEX FOR (n:Source) ON (n.id)",
            "CREATE INDEX FOR (n:DbtColumn) ON (n.id)",
            "CREATE INDEX FOR (n:Job) ON (n.id)",
            "CREATE INDEX FOR (n:Dataset) ON (n.id)",
            "CREATE INDEX FOR (n:Run) ON (n.id)",
            "CREATE INDEX FOR (n:SemanticView) ON (n.id)",
            # Additional indexes for commonly queried properties
            "CREATE INDEX FOR (n:Model) ON (n.name)",
            "CREATE INDEX FOR (n:Source) ON (n.name)",
        ]

        for index in indexes:
            try:
                self.graph.query(index)
                logger.debug(f"Created index: {index[:60]}...")
            except Exception as e:
                logger.debug(f"Index creation skipped (may exist): {e}")

        logger.info("Schema ensured: indexes created")

    def recreate_schema(self) -> None:
        """Drop all data and recreate indexes.

        WARNING: This destroys all data in the graph!
        """
        if self.read_only:
            raise ValueError("Cannot recreate schema in read-only mode")

        # Delete all nodes and relationships
        logger.warning("Deleting all nodes and relationships...")
        self.graph.query("MATCH (n) DETACH DELETE n")

        # Recreate indexes
        self.ensure_schema()
        logger.info("Schema recreated successfully")

    # ---- Core Generic Methods ----

    def upsert_node(self, node: BaseNode) -> None:
        """Generic node upsert - works for ALL node types."""
        if self.read_only:
            raise ValueError("Cannot write in read-only mode")

        label = node.node_label.value
        id = node.id
        properties = node.model_dump()

        # Filter out None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Build Cypher MERGE query
        # Note: FalkorDB uses SET prop = NULL instead of REMOVE for property deletion
        params = {"id": id}
        set_clauses = []

        for key, value in properties.items():
            param_key = f"prop_{key}"
            params[param_key] = value
            set_clauses.append(f"n.{key} = ${param_key}")

        set_clause = ", ".join(set_clauses) if set_clauses else ""

        if set_clause:
            query = f"""
            MERGE (n:{label} {{id: $id}})
            ON CREATE SET {set_clause}
            ON MATCH SET {set_clause}
            """
        else:
            query = f"MERGE (n:{label} {{id: $id}})"

        self.graph.query(query, params)

    def create_edge(
        self,
        from_node: Union[BaseNode, NodeIdentifier],
        to_node: Union[BaseNode, NodeIdentifier],
        edge: GraphEdge,
    ) -> None:
        """Generic edge creation - works for ALL edge types."""
        if self.read_only:
            raise ValueError("Cannot write in read-only mode")

        # Extract IDs and labels from nodes/identifiers
        from_id = from_node.id if isinstance(from_node, BaseNode) else from_node.id
        from_label = (from_node.node_label if isinstance(from_node, BaseNode)
                      else from_node.node_label)
        to_id = to_node.id if isinstance(to_node, BaseNode) else to_node.id
        to_label = (to_node.node_label if isinstance(to_node, BaseNode)
                    else to_node.node_label)

        # Extract edge type and properties
        edge_type = edge.edge_type.value
        properties = edge.model_dump()

        # Filter None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Build Cypher query
        params = {"from_id": from_id, "to_id": to_id}

        query = f"""
        MATCH (a:{from_label.value} {{id: $from_id}}), (b:{to_label.value} {{id: $to_id}})
        MERGE (a)-[r:{edge_type}]->(b)
        """

        # Add properties if they exist
        if properties:
            set_clauses = []
            for key, value in properties.items():
                param_key = f"prop_{key}"
                params[param_key] = value
                set_clauses.append(f"r.{key} = ${param_key}")
            set_clause = ", ".join(set_clauses)
            query += f"\nON CREATE SET {set_clause}\nON MATCH SET {set_clause}"

        self.graph.query(query, params)

    def execute_raw_query(self, query: str) -> RawLineageQueryResult:
        """Execute a raw Cypher query and return results."""
        result = self.graph.query(query)

        # Convert result to list of dicts
        rows = []
        if result.result_set:
            for record in result.result_set:
                row_dict = {}
                for i, key in enumerate(result.header):
                    value = record[i]
                    # Convert FalkorDB objects to dicts if needed
                    if hasattr(value, "__dict__"):
                        row_dict[key] = dict(value)
                    else:
                        row_dict[key] = value
                rows.append(row_dict)

        return RawLineageQueryResult(rows=rows, count=len(rows), query=query)

    def get_agent_hints(self) -> str:
        """Get FalkorDB-specific hints for AI agents writing Cypher queries."""
        return """
## FalkorDB Cypher Dialect Hints

You are querying a **FalkorDB** graph database. FalkorDB is Redis-based with Cypher support but has some limitations.

### Key Limitations

**❌ NO Regex Support:**
- Cannot use regex operators like `=~`
- Use `CONTAINS`, `STARTS WITH`, `ENDS WITH` instead

**Examples:**
```cypher
-- ❌ Wrong (no regex in FalkorDB)
MATCH (m:DbtModel)
WHERE m.name =~ '(?i).*fct.*'
RETURN m

-- ✅ Correct (use CONTAINS)
MATCH (m:DbtModel)
WHERE m.name CONTAINS 'fct' OR m.name CONTAINS 'FCT'
RETURN m
````

**❌ NO Temporal Arithmetic:**

- No date/time functions like `datetime()`, `duration()`
- Store timestamps as strings or integers

**⚠️ Property Deletion:**

- Use `SET prop = NULL` instead of `REMOVE prop`

**⚠️ Relationship Uniqueness:**

- FalkorDB has a quirk with relationship patterns
- Add explicit relationship reference: `WHERE ID(e) >= 0` if needed

### Supported Features

**✅ Standard Cypher:**

- `MATCH`, `WHERE`, `RETURN`, `WITH`, `UNWIND`
- Node and relationship patterns
- Aggregations: `COUNT`, `SUM`, `AVG`, `MIN`, `MAX`, `COLLECT`

**✅ String Functions:**

- `toLower()`, `toUpper()`, `trim()`, `substring()`, `split()`
- `CONTAINS`, `STARTS WITH`, `ENDS WITH`

**✅ Collections:**

- `COLLECT()`, `UNWIND`, `size()`, `head()`, `tail()`

### Common Query Patterns

**Finding models by name:**

```cypher
MATCH (m:DbtModel)
WHERE m.name CONTAINS 'customer'
RETURN m.id, m.name
```

**Case-insensitive search:**

```cypher
MATCH (m:DbtModel)
WHERE toLower(m.name) CONTAINS 'fct'
RETURN m
```

**Filtering with multiple conditions:**

```cypher
MATCH (m:DbtModel)
WHERE m.name STARTS WITH 'fct_'
  AND m.materialization = 'table'
RETURN m
```

Remember: **No regex, no temporal functions** in FalkorDB!
""".strip()

````

### Step 4: Update Factory

**File:** `src/lineage/backends/lineage/factory.py`

Add import at top (absolute import):

```python
from lineage.backends.config import (
    FalkorDBLineageConfig,
    FalkorDBLiteLineageConfig,
    YourBackendLineageConfig,  # ← Add import
)
````

Add factory branch:

```python
def create_storage(config: "LineageConfig", read_only: bool = False) -> LineageStorage:
    """Create storage adapter from unified configuration."""
    # ... existing branches ...

    elif isinstance(config, FalkorDBLineageConfig):
        from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter
        return FalkorDBAdapter(
            host=config.host,
            port=config.port,
            password=config.password,
            graph_name=config.graph_name,
            read_only=read_only,
        )

    else:
        raise ValueError(f"Unknown lineage config type: {type(config)}")
```

### Step 5: Create Example Configuration

**File:** `config.falkordb.example.yml`

```yaml
# Example Configuration for FalkorDB Lineage Backend

# Lineage Backend (Graph Database)
lineage:
  backend: falkordb
  host: localhost
  port: 6379 # Redis default
  password: ${FALKORDB_PASSWORD} # Use environment variable for security
  graph_name: lineage

  # Data Population Settings (for load-dbt-full)
  population:
    model: google/gemini-2.5-flash-lite
    max_semantic_workers: 64
    max_profiling_workers: 8
    enable_semantic: true
    enable_clustering: true
    enable_profiling: false
    enable_semantic_views: true

# Data Backend (Data Warehouse)
data:
  backend: duckdb
  db_path: demo_finance.duckdb
  allowed_schemas:
    - marts
  allowed_table_patterns:
    - fct_*
    - dim_*

# Agent Runtime Configuration
agent:
  model: anthropic:claude-sonnet-4-5-20250929
```

### Step 6: Add Dependencies

**File:** `pyproject.toml`

Add the Python client library to optional dependencies:

```toml
[project.optional-dependencies]
# ... existing dependencies ...
falkordb = ["falkordb>=4.0.0"]  # Check latest version
```

### Step 7: Test Your Implementation

#### Setup

```bash
# Start FalkorDB via Docker
docker run -p 6379:6379 falkordb/falkordb

# Install dependencies
uv sync --extra falkordb

# Set environment variables
export FALKORDB_PASSWORD=""  # Empty for local dev
```

#### Initialize Schema

```bash
lineage init --config config.falkordb.yml
```

#### Load dbt Project

```bash
lineage load-dbt-full path/to/dbt/target --config config.falkordb.yml
```

#### Query Data

```bash
# Via agent
lineage-agent --config config.falkordb.yml -i

# Direct query (Python)
from lineage.backends.config import UnifiedConfig
from lineage.backends.lineage.factory import create_storage

config = UnifiedConfig.from_yaml("config.falkordb.yml")
storage = create_storage(config.lineage)

result = storage.execute_raw_query("MATCH (m:DbtModel) RETURN m.name LIMIT 10")
for row in result.rows:
    print(row["name"])
```

## Code Style Requirements

### Import Style

**✅ Prefer absolute imports:**

```python
# Good
from lineage.backends.types import NodeLabel, EdgeType
from lineage.backends.lineage.models.base import BaseNode, GraphEdge

# Avoid
from ..types import NodeLabel  # Relative import
```

**✅ Place imports at top of file:**

```python
# Good - imports at top
from __future__ import annotations
import json
import logging
from typing import Any, Dict

from lineage.backends.lineage.base import BaseLineageStorage
from lineage.backends.lineage.models.base import BaseNode

# Only use local imports for circular dependencies
if TYPE_CHECKING:
    from lineage.backends.config import LineageConfig
```

**❌ Avoid local imports unless necessary:**

```python
# Bad - local import without reason
def create_storage(...):
    from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter  # Move to top
    return FalkorDBAdapter(...)

# Good - local import only if circular dependency
def create_storage(...):
    # Import here to avoid circular dependency
    from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter
    return FalkorDBAdapter(...)
```

### General Style

- Follow PEP 8 (4-space indentation, ~100 character lines)
- Use type hints for all parameters and return values
- Add docstrings to all public methods
- Log important operations (connection, schema creation, errors)
- Raise descriptive exceptions with helpful error messages

## Testing & Validation

### Unit Tests

Create basic unit tests for your adapter:

```python
# tests/test_falkordb_adapter.py
import pytest
from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter
from lineage.backends.lineage.models import SemanticView, SemanticMeasure


@pytest.fixture
def storage():
    """Create FalkorDB storage for testing."""
    adapter = FalkorDBAdapter(host="localhost", port=6379, password="")
    adapter.recreate_schema()
    yield adapter
    adapter.close()


def test_upsert_node(storage):
    """Test upserting a node."""
    view = SemanticView(
        name="test_view",
        database="TEST_DB",
        schema="PUBLIC",
        provider="snowflake",
    )

    storage.upsert_node(view)

    # Query to verify
    result = storage.execute_raw_query(
        f"MATCH (v:SemanticView {{id: '{view.id}'}}) RETURN v.name AS name"
    )
    assert len(result.rows) == 1
    assert result.rows[0]["name"] == "test_view"


def test_create_edge(storage):
    """Test creating an edge."""
    from lineage.backends.lineage.models import DbtModel, NodeIdentifier, DependsOn
    from lineage.backends.types import NodeLabel

    # Create nodes
    model_a = DbtModel(name="orders", database="db", schema="schema", ...)
    model_b = DbtModel(name="customers", database="db", schema="schema", ...)
    storage.upsert_node(model_a)
    storage.upsert_node(model_b)

    # Create edge
    edge = DependsOn(type="model", direct=True)
    storage.create_edge(model_a, model_b, edge)

    # Query to verify
    result = storage.execute_raw_query(
        f"MATCH (a {{id: '{model_a.id}'}})-[r:DEPENDS_ON]->(b {{id: '{model_b.id}'}}) RETURN r"
    )
    assert len(result.rows) == 1
```

### Integration Tests

Test with a real dbt project:

```bash
# 1. Start FalkorDB
docker run -p 6379:6379 falkordb/falkordb

# 2. Initialize and load
lineage init --config config.falkordb.yml
lineage load-dbt-full path/to/dbt/target --config config.falkordb.yml

# 3. Verify data
lineage-agent --config config.falkordb.yml "How many models are in the graph?"

# 4. Run queries
lineage-agent --config config.falkordb.yml "What are the top 5 models by downstream dependencies?"
```

## Example: FalkorDB Adapter

For a complete reference implementation, see:

- `src/lineage/backends/lineage/falkordb_adapter.py`
- `src/lineage/backends/config.py` (FalkorDBLineageConfig)
- `config.falkordb.example.yml`

The FalkorDB adapter demonstrates:

- Connection management with context manager
- Schema management with indexes
- Cypher query execution with parameter binding
- Backend-specific optimizations
- Agent hints for query language dialect (FalkorDB Cypher limitations)

## Summary

Adding a new LineageStorage backend requires:

1. ✅ Add backend type to enum (`types.py`)
2. ✅ Create configuration class (`config.py`)
3. ✅ Implement adapter with 3 core methods:
   - `upsert_node(node: BaseNode)`
   - `create_edge(from_node, to_node, edge: GraphEdge)`
   - `execute_raw_query(query: str)`
4. ✅ Update factory (`factory.py`)
5. ✅ Create example config (`config.{backend}.example.yml`)
6. ✅ Add dependencies (`pyproject.toml`)
7. ✅ Test with dbt project

The protocol-based architecture ensures all backends work identically from the caller's perspective, while allowing backend-specific optimizations where needed.
