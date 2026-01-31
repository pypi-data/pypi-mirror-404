# Typedef Data Intelligence

A unified lineage management system that combines dbt semantic metadata with OpenLineage operational data in multiple graph database backends. Includes an intelligent multi-agent system for querying and analyzing data lineage.

**Key Features**:

- ✅ Unified lineage graph combining static dbt metadata + runtime OpenLineage data
- ✅ Multiple backend support: FalkorDBLite (embedded), FalkorDB (production)
- ✅ Semantic SQL analysis extracting business metadata (measures, dimensions, grain)
- ✅ Multi-agent orchestration system with streaming responses and memory
- ✅ MCP servers for AI agent integration
- ✅ Cursor-based pagination for efficient data passing between agents

## Quick Start

### 1. Install Dependencies

```bash
uv sync --all-extras
```

### 2. Initialize Database

```bash
uv run lineage init
```

### 3. Build dbt Project

```bash
cd dbt_projects/medallion-reference
export DBT_PROFILES_DIR=$(pwd)
uv run --with dbt-core --with dbt-duckdb dbt deps
uv run --with dbt-core --with dbt-duckdb dbt seed
uv run --with dbt-core --with dbt-duckdb dbt run
cd ../../
```

### 4. Load dbt with Semantic Analysis

```bash
# Load with full semantic analysis (recommended)
uv run lineage load-dbt-full dbt_projects/medallion-reference/target/ \
  --verbose

# OR: Use FalkorDB backend (production)
uv run lineage load-dbt-full dbt_projects/medallion-reference/target/ \
  --backend-config backend_configs/falkordb.yaml \
  --verbose
```

### 5. Query Semantic Metadata

```bash
uv run lineage query-semantics "model.medallion-reference.fct_arr_reporting_monthly"
```

### 6. Start Agent (Interactive Mode)

```bash
# Using default FalkorDBLite backend
uv run lineage-agent \
  --data-db dbt_projects/medallion-reference/medallion-reference.duckdb \
  --allowed-schemas marts \
  --allowed-tables "fct_*,dim_*" \
  --verbose \
  -i

# Or using FalkorDB backend (production)
uv run lineage-agent \
  --backend-config backend_configs/falkordb.yaml \
  --data-db dbt_projects/medallion-reference/medallion-reference.duckdb \
  --allowed-schemas marts \
  --allowed-tables "fct_*,dim_*" \
  -i
```

## Key Commands

### Semantic Analysis

```bash
# Load dbt with semantic analysis
uv run lineage load-dbt-full <path-to-dbt-target>/ --verbose

# Query semantic analysis for a model
uv run lineage query-semantics "model.demo_finance.fct_pipeline"

# Cluster models by join patterns
uv run lineage cluster-joins
```

### OpenLineage Collection

```bash
# Start collector
uv run lineage serve

# Run dbt with OpenLineage enabled
cd dbt_projects/demo_finance
OPENLINEAGE_URL=http://localhost:8080/api/v1/lineage \
OPENLINEAGE_NAMESPACE=dbt://demo_finance \
OPENLINEAGE_DISABLED=false \
uv run --with dbt-core --with dbt-duckdb --with ol dbt-ol run
```

### MCP Servers

```bash
# Lineage metadata MCP server
uv run lineage-mcp-lineage --db-path lineage_store/lineage.falkordb

# Data query MCP server
uv run lineage-mcp-data \
  --backend duckdb \
  --db-path dbt_projects/demo_finance/demo_finance.duckdb \
  --allowed-schemas marts \
  --allowed-tables "fct_*,dim_*"
```

## Graph Database Backends

The system supports multiple graph database backends:

### FalkorDBLite (Default)

- **Type**: Embedded graph database
- **Best for**: Development, single-user scenarios
- **Setup**: No external dependencies
- **Usage**: Default backend, no configuration needed

### FalkorDB

- **Type**: Redis-based graph database
- **Best for**: Production, multi-user scenarios
- **Setup**: Requires Docker or Redis with FalkorDB
- **Config**: `--backend-config backend_configs/falkordb.yaml`
- **Start**: `docker run -p 6379:6379 falkordb/falkordb`

See `backend_configs/` directory for configuration examples.

## Project Structure

```
typedef_data_intelligence/
├── src/lineage/
│   ├── agent/              # Multi-agent orchestration system
│   │   ├── orchestrators/  # Analyst, data engineer, data quality orchestrators
│   │   ├── subagents/      # Specialist agents (metadata, data, presenter, etc.)
│   │   └── tools/          # Agent tools (memory, cursor pagination, etc.)
│   ├── builder/            # dbt manifest parsing
│   ├── collector/          # OpenLineage event collection
│   ├── semantic/           # Semantic SQL analysis (Fenic-powered)
│   ├── storage/            # Graph database adapters (FalkorDB, FalkorDBLite)
│   └── mcp/                # MCP servers
├── backend_configs/        # Database backend configurations
├── docs/
│   ├── architecture/       # Architecture design documents
│   └── reference/          # Reference documentation
├── dbt_projects/
│   ├── medallion-reference/  # Primary demo project
│   └── healthdirect_chaos/   # Additional example project
└── lineage_store/          # Default FalkorDBLite database files
```

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Comprehensive guide for working with this project (recommended starting point)
- **[AGENTS.md](AGENTS.md)** - Multi-agent system guide (orchestrator + subagents)
- **[docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)** - System architecture and graph schema
- **[docs/architecture/SUBAGENT_ARCHITECTURE.md](docs/architecture/SUBAGENT_ARCHITECTURE.md)** - Multi-agent system design (detailed)
- **[docs/reference/README_SEMANTIC.md](docs/reference/README_SEMANTIC.md)** - Semantic analysis usage guide
- **[docs/reference/README_MCP.md](docs/reference/README_MCP.md)** - MCP server usage

## Multi-Agent System

The project includes a sophisticated orchestrator-subagent architecture with advanced features:

**Orchestrators**:

- **analyst** - Business intelligence agent for data analysis and reporting
- **data-engineer** - Data pipeline and modeling agent
- **data-quality** - Data quality monitoring and validation agent

**Subagents**:

- **metadata-explorer** - Queries semantic metadata and lineage (Cypher expert)
- **data-explorer** - Discovers tables, samples data, validates SQL queries
- **presenter** - Executes queries and creates polished reports with Plotly visualizations
- **troubleshooter** - Diagnoses operational issues and errors

**Advanced Features**:

- 🔄 **Streaming responses** - Real-time token streaming for immediate feedback
- 💾 **Persistent memory** - Agents learn from syntax errors and store knowledge
- 📊 **Cursor-based pagination** - Efficient data passing between agents (pre-executed queries)
- 🔍 **Automatic error learning** - Syntax errors automatically captured in memory
- 🎨 **Rich CLI output** - Formatted markdown, tables, and visualizations

See **[AGENTS.md](AGENTS.md)** for a complete guide or [docs/architecture/SUBAGENT_ARCHITECTURE.md](docs/architecture/SUBAGENT_ARCHITECTURE.md) for detailed architecture documentation.

## Example dbt Projects

The `dbt_projects/` directory contains example analytics projects:

### medallion-reference

Primary demo project with SaaS business metrics:

**Key Models**:

- `fct_arr_reporting_monthly` - Monthly ARR by subscription
- `fct_support_metrics_monthly` - Customer support ticket metrics
- `fct_pipeline` - Sales pipeline snapshot
- `dim_customers`, `dim_subscriptions`, `dim_accounts` - Dimension tables
- `stg_*` - Staging models (staging schema - restricted access)
- `int_*` - Intermediate models (intermediate schema - restricted access)

**Example Queries** (via agent):

- "Create a customer support health report comparing 2024 vs 2023"
- "What is the grain of fct_arr_reporting_monthly?"
- "Show me all revenue measures"
- "What models depend on stg_subscriptions?"
- "Analyze support ticket resolution time by priority"

**Note**: Only `marts` schema tables are accessible to agents by default. Staging and intermediate tables require data engineering tickets.

## Capture and Replay Events

The OpenLineage collector can capture events for testing:

```bash
# Capture events
export CAPTURE_EVENTS_DIR=./captured_events
uv run lineage serve

# Replay events
python scripts/replay_events.py ./captured_events --delay 100
```

Useful for:

- Reproducible test scenarios
- Debugging event processing
- Load testing

## Environment Variables

```bash
# Required for agent system and semantic analysis
export ANTHROPIC_API_KEY=your-key-here

# Optional: Alternative LLM providers for semantic analysis
export OPENAI_API_KEY=your-key-here
export GEMINI_API_KEY=your-key-here

# Optional for OpenLineage
export OPENLINEAGE_URL=http://localhost:8080/api/v1/lineage
export OPENLINEAGE_NAMESPACE=dbt://medallion-reference
export OPENLINEAGE_DISABLED=false
```

## Development

```bash
# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/lineage

# Format code
ruff format .

# Lint
ruff check .
```

## License

[Your license here]
