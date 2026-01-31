# Ingest

This module provides data ingestion pipelines for loading metadata from various sources into lineage backends. It supports both **static loaders** (dbt artifacts, semantic views, data profiles) and **dynamic loaders** (OpenLineage runtime events).

## Purpose

The ingest module bridges raw metadata sources and the lineage graph:

```
Raw Sources → Static Loaders → Lineage Backend
                    ↓
        (dbt, Snowflake, SQL analysis)

Runtime Events → OpenLineage Loader → Lineage Backend
                        ↓
            (job runs, errors, datasets)
```

## Architecture Overview

```
Ingest Module
├── Static Loaders (compile-time metadata)
│   ├── dbt Loader           → Parse manifest.json, catalog.json
│   ├── Semantic Analyzer    → LLM-powered SQL analysis (Fenic)
│   ├── Semantic Views       → Snowflake semantic model loading
│   ├── Profiling            → Data statistics & quality metrics
│   └── SQLGlot Lineage      → Column-level lineage extraction
│
└── Dynamic Loaders (runtime metadata)
    └── OpenLineage           → Job/run/dataset event streaming
```

## Directory Structure

```bash
ingest/
├── static_loaders/              # Compile-time metadata ingestion
│   ├── dbt/                     # dbt project metadata
│   │   ├── dbt_loader.py        # Main loader entry point
│   │   ├── builder.py           # Manifest/catalog parsing
│   │   └── config.py            # Configuration models
│   │
│   ├── semantic/                # LLM-powered semantic SQL analysis
│   │   ├── analyzer.py          # CLI entry point
│   │   ├── loader.py            # Load semantic metadata into graph
│   │   ├── runner.py            # Orchestrate analysis pipeline
│   │   ├── models/              # Pydantic models for analysis results
│   │   │   ├── analytical.py    # Technical analysis (joins, windows, etc.)
│   │   │   ├── business.py      # Business semantics (measures, dimensions)
│   │   │   ├── technical.py     # Technical metadata (CTEs, complexity)
│   │   │   └── validation.py    # Validation results
│   │   ├── passes/              # 11 sequential analysis passes
│   │   │   ├── pass_01_relations.py      # CTE and subquery extraction
│   │   │   ├── pass_02_columns.py        # Column identification
│   │   │   ├── pass_03_joins.py          # Join analysis
│   │   │   ├── pass_04_filters.py        # WHERE clause analysis
│   │   │   ├── pass_05_grouping.py       # GROUP BY analysis
│   │   │   ├── pass_06_time.py           # Temporal logic
│   │   │   ├── pass_07_windows.py        # Window functions
│   │   │   ├── pass_08_output.py         # Output columns
│   │   │   ├── pass_09_audit.py          # Code quality checks
│   │   │   ├── pass_10_business.py       # Business semantics
│   │   │   ├── pass_10a_grain.py         # Grain analysis
│   │   │   └── pass_11_summary.py        # Final summary
│   │   ├── pipeline/            # Analysis pipeline orchestration
│   │   │   ├── dag.py           # DAG representation
│   │   │   ├── executor.py      # Pipeline execution engine
│   │   │   └── dependencies.py  # Pass dependencies
│   │   ├── prompts/             # LLM prompt templates
│   │   │   ├── analytical.py    # Prompts for technical analysis
│   │   │   ├── business.py      # Prompts for business semantics
│   │   │   ├── technical.py     # Prompts for technical metadata
│   │   │   └── validation.py    # Prompts for validation
│   │   ├── utils/               # Utility functions
│   │   │   ├── data_loaders.py  # Load SQL files into Fenic DataFrames
│   │   │   ├── extractors.py    # Extract metadata from analysis results
│   │   │   └── sql_operations.py # SQL canonicalization, parsing
│   │   ├── config/              # Configuration
│   │   │   ├── session.py       # Fenic session management
│   │   │   └── settings.py      # Pipeline settings
│   │   └── output/              # Result exporters
│   │       ├── exporters.py     # JSON/Parquet export
│   │       └── reporters.py     # Console reporting
│   │
│   ├── semantic_views/          # Snowflake semantic model ingestion
│   │   ├── loader.py            # Load semantic views into graph
│   │   └── parser.py            # Parse Snowflake YAML/DDL
│   │
│   ├── profiling/               # Data profiling
│   │   └── loader.py            # Load profile statistics into graph
│   │
│   └── sqlglot/                 # SQLGlot-based lineage
│       ├── sqlglot_lineage.py   # Column-level lineage extraction
│       └── config.py            # SQLGlot configuration
│
└── openlineage/                 # Runtime event ingestion
    ├── collector.py             # FastAPI server for event collection
    ├── loader.py                # Load events into lineage graph
    ├── parser.py                # Parse OpenLineage event format
    └── models.py                # OpenLineage data models
```

## Static Loaders

Static loaders process compile-time metadata (dbt artifacts, semantic models, data profiles).

### 1. dbt Loader (`static_loaders/dbt/`)

**Purpose:** Parse dbt artifacts (`manifest.json`, `catalog.json`, `run_results.json`) and load models, sources, columns, and dependencies into the lineage graph.

**Entry Point:** `dbt_loader.py`

**Key Components:**

- **`DbtArtifacts`** - Parses dbt JSON artifacts
- **`DbtModelNode`** - Represents a dbt model with metadata
- **`DbtSourceNode`** - Represents a dbt source
- **`DbtColumn`** - Column-level metadata

**Usage:**

```python
from lineage.ingest.static_loaders.dbt.dbt_loader import load_dbt_artifacts
from lineage.backends.lineage.factory import create_storage

storage = create_storage(config.lineage)
load_dbt_artifacts(
    target_path=Path("dbt_project/target"),
    storage=storage,
    run_semantic_analysis=True,  # Enable semantic analysis
)
```

**CLI Usage:**

```bash
# Load dbt artifacts without semantic analysis
uv run lineage load-dbt-models ../dbt_project/target/

# Load with semantic analysis (full)
uv run lineage load-dbt-full ../dbt_project/target/ --verbose
```

**What Gets Loaded:**

- Models (nodes in manifest.json)
- Sources (external tables)
- Columns (with types, descriptions, tests)
- Dependencies (DEPENDS_ON edges)
- Tests (from schema.yml files)
- Tags and metadata

### 2. Semantic Analyzer (`static_loaders/semantic/`)

**Purpose:** Use LLMs (via Fenic) to extract business semantics from SQL queries - measures, dimensions, grain, join patterns, time logic.

**Architecture:**

- **Multi-pass pipeline** - 11 sequential analysis passes
- **Fenic-powered** - Uses Fenic DataFrame API for parallel LLM inference
- **DAG execution** - Passes have explicit dependencies
- **Checkpointing** - Save/resume intermediate results

**11 Analysis Passes:**

| Pass | Name      | Purpose                                   | Example Output                   |
| ---- | --------- | ----------------------------------------- | -------------------------------- |
| 1    | Relations | Extract CTEs, subqueries                  | `WITH monthly_arr AS (...)`      |
| 2    | Columns   | Identify input/output columns             | `customer_id`, `arr_amount`      |
| 3    | Joins     | Analyze join patterns                     | `JOIN dim_customers ON ...`      |
| 4    | Filters   | Extract WHERE clause logic                | `status = 'active'`              |
| 5    | Grouping  | GROUP BY analysis                         | `GROUP BY customer_id, month`    |
| 6    | Time      | Temporal logic (date filters, windows)    | `date >= '2024-01-01'`           |
| 7    | Windows   | Window function analysis                  | `ROW_NUMBER() OVER (...)`        |
| 8    | Output    | Output column semantics                   | `SUM(arr) AS total_arr`          |
| 9    | Audit     | Code quality checks                       | Complexity score, best practices |
| 10   | Business  | Business semantics (measures, dimensions) | `total_arr` is a measure         |
| 10a  | Grain     | Determine grain of aggregation            | Per customer × month             |
| 11   | Summary   | Final summary & validation                | Grain, intent, key metrics       |

**Execution Model:**

```
load_sql_files()
      ↓
Fenic DataFrame (sql, filename)
      ↓
Pass 1 → Pass 2 → Pass 3 → ... → Pass 11
  ↓        ↓         ↓              ↓
New columns added to DataFrame at each pass
      ↓
Extract results & load into graph
```

**Usage:**

```python
from lineage.ingest.static_loaders.semantic.runner import analyze_model_sql

results = analyze_model_sql(
    compiled_sql="SELECT customer_id, SUM(revenue) FROM orders GROUP BY customer_id",
    model_name="fct_revenue",
    dialect="duckdb",
    verbose=True,
    default_model="google/gemini-2.5-flash-lite"
)

# Results contain:
# - business_analysis: {measures: [...], dimensions: [...], grain: "..."}
# - join_analysis: {joins: [...], join_types: [...]}
# - time_analysis: {has_time_logic: true, ...}
# - etc.
```

**Parallel Execution:**

```python
# For loading many models in parallel
from lineage.ingest.static_loaders.semantic.config.session import create_session

session = create_session(default_model="google/gemini-2.5-flash-lite")

# Analyze multiple models concurrently
async def analyze_all(models):
    tasks = [
        analyze_model_sql(model.sql, model.name, session=session)
        for model in models
    ]
    results = await asyncio.gather(*tasks)
    return results

# Stop session once after all complete
session.stop()
```

**Configuration:**

```python
# config/settings.py
class PipelineSettings(BaseModel):
    max_workers: int = 64           # Max parallel workers
    verbose: bool = False           # Verbose output
    checkpoint: bool = False        # Enable checkpointing
    skip_passes: List[str] = []     # Skip specific passes
```

**CLI Usage:**

```bash
# Analyze single SQL file
uv run python -m lineage.ingest.static_loaders.semantic.analyzer \
  query.sql \
  --output-dir ./results \
  --export-json

# Analyze directory of SQL files
uv run python -m lineage.ingest.static_loaders.semantic.analyzer \
  sql_files/ \
  --compact \
  --export-parquet
```

### 3. Semantic Views Loader (`static_loaders/semantic_views/`)

**Purpose:** Load Snowflake semantic models (views, dimensions, measures) into the lineage graph.

**Snowflake Semantic Models:**

- Semantic views (business-friendly tables)
- Dimensions (attributes for slicing/filtering)
- Measures (aggregatable metrics)
- Time dimensions (temporal attributes)

**Usage:**

```python
from lineage.ingest.static_loaders.semantic_views.loader import load_semantic_views

load_semantic_views(
    data_backend=snowflake_backend,  # DataQueryBackend
    storage=lineage_storage,         # LineageStorage
)
```

**What Gets Loaded:**

- Semantic views as nodes
- Dimensions with semantic types
- Measures with aggregation functions
- Relationships to underlying tables

### 4. Profiling Loader (`static_loaders/profiling/`)

**Purpose:** Load data profile statistics (row counts, null percentages, distinct counts, distributions) into the lineage graph.

**Usage:**

```python
from lineage.ingest.static_loaders.profiling.loader import load_table_profiles

load_table_profiles(
    data_backend=duckdb_backend,
    storage=lineage_storage,
    tables=[("marts", "fct_revenue"), ("marts", "dim_customers")],
)
```

**What Gets Loaded:**

- Row counts
- Column statistics (nulls, distinct values, min/max, avg, stddev)
- Top value distributions
- Profile timestamps

### 5. SQLGlot Lineage (`static_loaders/sqlglot/`)

**Purpose:** Extract column-level lineage from SQL queries using SQLGlot parser.

**Capabilities:**

- Trace column lineage through transformations
- Identify source columns for each output column
- Handle complex SQL (CTEs, subqueries, window functions)

**Usage:**

```python
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import extract_column_lineage

lineage = extract_column_lineage(
    sql="SELECT customer_id, SUM(amount) AS total FROM orders GROUP BY customer_id",
    dialect="duckdb"
)
# Returns: {output_column: [source_columns], ...}
```

## Dynamic Loaders

Dynamic loaders process runtime metadata (job executions, errors, performance metrics).

### OpenLineage Loader (`openlineage/`)

**Purpose:** Collect and load OpenLineage events (job runs, dataset reads/writes, errors) from dbt and other tools.

**Architecture:**

```
dbt-ol run → OpenLineage Events → FastAPI Collector → Parser → Loader → Graph
```

**Components:**

1. **Collector (`collector.py`)** - FastAPI server that receives OpenLineage events
2. **Parser (`parser.py`)** - Parse and validate OpenLineage event format
3. **Loader (`loader.py`)** - Load events into lineage graph as Job/Run/Dataset nodes
4. **Models (`models.py`)** - Pydantic models for OpenLineage events

**Event Types:**

- `START` - Job execution started
- `RUNNING` - Job in progress
- `COMPLETE` - Job finished successfully
- `FAIL` - Job failed with error
- `ABORT` - Job aborted

**Usage:**

**1. Start Collector Server:**

```bash
uv run lineage serve --config config.yml
# Starts FastAPI server on http://localhost:8080
```

**2. Run dbt with OpenLineage:**

```bash
export OPENLINEAGE_URL=http://localhost:8080/api/v1/lineage
export OPENLINEAGE_NAMESPACE=dbt://my_project
export OPENLINEAGE_DISABLED=false

uv run --with dbt-ol dbt-ol run
# Events automatically sent to collector
```

**3. Query Runtime Metadata:**

```cypher
# Find failed runs
MATCH (r:Run {status: 'FAIL'})-[:INSTANCE_OF]->(j:Job)
RETURN j.name, r.error_info, r.start_time

# Find datasets written by job
MATCH (j:Job {name: 'dbt.fct_revenue'})-[:WRITES]->(d:Dataset)
RETURN d.name, d.namespace
```

**Event Capture (for testing):**

```bash
export CAPTURE_EVENTS_DIR=./captured_events
uv run lineage serve

# Events saved to ./captured_events/*.json for replay/testing
```

**What Gets Loaded:**

- Job nodes (dbt models as jobs)
- Run nodes (executions with status, timing, errors)
- Dataset nodes (tables read/written)
- Edges: INSTANCE_OF (Run → Job), READS (Job → Dataset), WRITES (Job → Dataset)
- Error patterns aggregated across runs

## Common Workflows

### Loading a dbt Project with Semantic Analysis

```bash
# 1. Build dbt artifacts
cd dbt_project/
dbt compile
dbt docs generate

# 2. Initialize lineage graph
cd ../
uv run lineage init --config config.yml

# 3. Load dbt + semantic analysis
uv run lineage load-dbt-full dbt_project/target/ \
  --config config.yml \
  --verbose \
  --max-concurrent 32

# What happens:
# - Loads dbt models, sources, columns
# - Runs semantic analysis on all models (parallel)
# - Creates join clusters
# - Loads semantic views (if Snowflake)
```

### Running Semantic Analysis Standalone

```bash
# Analyze a single SQL file
uv run python -m lineage.ingest.static_loaders.semantic.analyzer \
  query.sql \
  --export-json \
  --output-dir ./results

# Analyze multiple files
uv run python -m lineage.ingest.static_loaders.semantic.analyzer \
  sql_files/ \
  --compact \
  --export-by-pass \
  --skip-audit
```

### Collecting OpenLineage Events

```bash
# Terminal 1: Start collector
uv run lineage serve --config config.yml

# Terminal 2: Run dbt with OpenLineage
cd dbt_project/
export OPENLINEAGE_URL=http://localhost:8080/api/v1/lineage
export OPENLINEAGE_NAMESPACE=dbt://my_project
uv run --with dbt-ol dbt-ol run

# Events streamed in real-time to lineage graph
```

### Profiling Tables

```bash
# Profile specific tables
uv run lineage profile-tables \
  --config config.yml \
  --schema marts \
  --tables "fct_*,dim_*"

# Profile all tables in schema
uv run lineage profile-schema marts --config config.yml
```

## Configuration

Ingestion is configured via `config.yml`:

```yaml
lineage:
  backend: falkordb
  host: localhost
  port: 6379
  graph_name: lineage_graph
  population:
    model: google/gemini-2.5-flash-lite # LLM for semantic analysis
    max_semantic_workers: 64 # Parallel workers
    max_profiling_workers: 8
    enable_semantic: true # Run semantic analysis
    enable_clustering: true # Cluster models by joins
    enable_profiling: false # Profile data (slow)
    enable_semantic_views: true # Load Snowflake semantic views
    model_filter: "fct_" # Only analyze models matching filter

data:
  backend: snowflake
  account: ${SNOWFLAKE_ACCOUNT}
  warehouse: COMPUTE_WH
  database: ANALYTICS

agent:
  analyst:
    model: anthropic:claude-haiku-4-5
  data_engineer:
    model: anthropic:claude-sonnet-4-5-20250929
```

**Environment Variables:**

- `ANTHROPIC_API_KEY` - For Claude models
- `OPENAI_API_KEY` - For GPT models
- `GEMINI_API_KEY` - For Gemini models
- `CAPTURE_EVENTS_DIR` - Enable OpenLineage event capture

## Key Design Patterns

### 1. Multi-Pass Pipeline (Semantic Analysis)

Each pass:

1. Receives Fenic DataFrame with prior pass results
2. Uses LLM to extract specific metadata
3. Adds new columns to DataFrame
4. Returns enriched DataFrame for next pass

**Benefits:**

- Clear separation of concerns
- Incremental complexity building
- Easy to add/remove passes
- Cacheable intermediate results

### 2. Shared Session (Parallel Inference)

For parallel semantic analysis:

```python
# DON'T: Create session per model (causes asyncio conflicts)
for model in models:
    session = create_session()
    analyze_model_sql(model.sql, session=session)
    session.stop()  # ❌ Multiple event loops

# DO: Share session across all models
session = create_session()
for model in models:
    analyze_model_sql(model.sql, session=session)
session.stop()  # ✅ Single event loop
```

### 3. Protocol-Based Loading

All loaders accept protocol interfaces:

```python
def load_dbt_artifacts(
    target_path: Path,
    storage: LineageStorage,  # Protocol, not concrete type
    ...
) -> None:
    # Works with any LineageStorage implementation
    storage.upsert_node(model_node)
```

### 4. Event Streaming (OpenLineage)

FastAPI + SSE for real-time events:

```python
@app.post("/api/v1/lineage")
async def receive_event(event: dict):
    _loader.load_event(event)
    return {"status": "ok"}
```

## Performance Optimization

### Semantic Analysis Performance

**Parallel Execution:**

- Set `max_semantic_workers` in config (default: 64)
- Use fast/cheap model for bulk processing: `google/gemini-2.5-flash-lite`
- Share Fenic session across all models

**Skip Passes:**

```python
settings.pipeline.skip_passes = ["time", "window", "audit"]
# Skips time, window, and audit passes for faster analysis
```

**Model Filtering:**

```yaml
lineage:
  population:
    model_filter: "fct_" # Only analyze models starting with "fct_"
```

**Checkpointing:**

```bash
# Enable checkpointing to resume failed runs
uv run python -m lineage.ingest.static_loaders.semantic.analyzer \
  sql_files/ \
  --checkpoint \
  --checkpoint-mode selective
```

### dbt Loading Performance

**Incremental Loading:**

- Skip semantic analysis: `load-dbt-models` (10x faster)
- Enable only needed features:
  ```yaml
  population:
    enable_semantic: true
    enable_clustering: true
    enable_profiling: false # Slow for large tables
    enable_semantic_views: false # Only if using Snowflake
  ```

## Testing

```bash
# Test dbt loader
uv run pytest tests/ingest/test_dbt_loader.py -v

# Test semantic analysis
uv run pytest tests/ingest/test_semantic_analysis.py -v

# Test OpenLineage collector
uv run pytest tests/ingest/test_openlineage.py -v

# Integration tests (require backends)
uv run pytest tests/ingest/integration/ -m integration
```

## Troubleshooting

### Semantic Analysis Hanging

**Symptom:** Analysis hangs at the end or during parallel execution.

**Cause:** Multiple `session.stop()` calls or asyncio event loop conflicts.

**Solution:**

1. Use shared Fenic session pattern
2. Call `session.stop()` only once after all analyses complete
3. See `runner.py` for reference implementation

### dbt Loader Fails with Missing Columns

**Symptom:** `KeyError` when loading dbt artifacts.

**Cause:** dbt version mismatch or incomplete artifacts.

**Solution:**

1. Run `dbt compile` and `dbt docs generate` to regenerate artifacts
2. Check dbt version compatibility (tested with dbt 1.5+)
3. Ensure `target/manifest.json` and `target/catalog.json` exist

### OpenLineage Events Not Appearing

**Symptom:** dbt runs but no events in graph.

**Cause:** OpenLineage not configured or collector not running.

**Solution:**

1. Verify collector is running: `curl http://localhost:8080/health`
2. Check environment variables: `echo $OPENLINEAGE_URL`
3. Enable debug logging: `export OPENLINEAGE_DEBUG=true`
4. Check captured events: `ls $CAPTURE_EVENTS_DIR`

### Out of Memory During Semantic Analysis

**Symptom:** Process killed or OOM error during bulk analysis.

**Cause:** Too many parallel workers or large SQL files.

**Solution:**

1. Reduce `max_semantic_workers` in config (try 16 or 32)
2. Use model filtering to analyze subsets
3. Enable checkpointing to resume from failures

## Related Documentation

- **Backends:** `../backends/README.md` - Storage backend protocols
- **Agent System:** `../agent/README.md` - How agents use ingested metadata
- **Architecture:** `../../docs/architecture/ARCHITECTURE.md` - System design
- **Semantic Analysis:** `../../docs/reference/README_SEMANTIC.md` - Deep dive on semantic analysis
- **OpenLineage:** `../../docs/reference/README_OPENLINEAGE.md` - OpenLineage integration guide
