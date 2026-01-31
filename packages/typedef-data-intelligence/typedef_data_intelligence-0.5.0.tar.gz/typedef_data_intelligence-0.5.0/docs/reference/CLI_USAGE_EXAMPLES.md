# CLI Usage Examples for Semantic Views & Profiling

## Overview

The `load-dbt-full` command now supports:

- ✅ Loading semantic views from data warehouses (Snowflake, etc.)
- ✅ Profiling table data (row counts, column statistics)
- ✅ Semantic analysis (measures, dimensions, joins)
- ✅ Join graph clustering

## Basic Usage

### 1. Load dbt artifacts only (no analysis)

```bash
uv run lineage load-dbt-full target/ --no-semantic --no-clustering
```

### 2. Load with semantic analysis (default)

```bash
uv run lineage load-dbt-full target/ --verbose
```

### 3. Load with DuckDB profiling

```bash
uv run lineage load-dbt-full target/ \
    --enable-profiling \
    --data-backend-type duckdb \
    --data-db-path path/to/my_data.duckdb \
    --verbose
```

## Snowflake Semantic Views

### Setup Snowflake Credentials

```bash
export SNOWFLAKE_ACCOUNT=xyz12345.us-east-1
export SNOWFLAKE_USER=analyst
export SNOWFLAKE_WAREHOUSE=ANALYTICS_WH
export SNOWFLAKE_ROLE=ANALYST_ROLE
export SNOWFLAKE_DATABASE=ANALYTICS
export SNOWFLAKE_SCHEMA=MARTS
export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/private_key.pem
# Optional: if key is encrypted
export SNOWFLAKE_PRIVATE_KEY_PASSPHRASE=your_passphrase
```

### Load Semantic Views

```bash
uv run lineage load-dbt-full target/ \
    --enable-semantic-views \
    --data-backend-type snowflake \
    --verbose
```

### Full Pipeline (Everything Enabled)

```bash
# Set Snowflake credentials first
export SNOWFLAKE_ACCOUNT=xyz12345.us-east-1
export SNOWFLAKE_USER=analyst
# ... (other env vars)

uv run lineage load-dbt-full target/ \
    --enable-profiling \
    --enable-semantic-views \
    --data-backend-type snowflake \
    --verbose \
    --max-workers 32
```

## Command Options

```
Options:
  --backend-config PATH           Path to backend config YAML file
  --backend TEXT                  Backend type for default config
  --no-semantic                   Skip semantic analysis
  --no-clustering                 Skip join graph clustering
  --enable-profiling              Enable table data profiling
  --enable-semantic-views         Load semantic views from data warehouse
  --data-backend-type [duckdb|snowflake]
                                  Data backend type (required for profiling/semantic views)
  --data-db-path PATH            Path to data database (DuckDB)
  --model-filter TEXT            Filter models by substring (e.g., 'fct_' for facts only)
  --model TEXT                   Language model to use (default: google/gemini-2.5-flash-lite)
  --verbose                      Enable verbose output
  --max-workers INTEGER          Maximum concurrent semantic analysis tasks (default: 64)
```

## Pipeline Steps

When you run `load-dbt-full`, it executes these steps in order:

```
Step 1: Load dbt artifacts → Graph
  ↓ Models, Sources, Columns, Dependencies

Step 2: Load semantic views → Graph (if --enable-semantic-views)
  ↓ Fetch from Snowflake/warehouse
  ↓ Parse SQL to extract table references
  ↓ Create SemanticView nodes
  ↓ Create DRAWS_FROM edges to Models

Step 3: Profile table data → Graph (if --enable-profiling)
  ↓ Profile each materialized table
  ↓ Create TableProfile & ColumnProfile nodes

Step 4: Run semantic analysis → Graph (if not --no-semantic)
  ↓ Analyze SQL for each model
  ↓ Extract measures, dimensions, joins, etc.
  ↓ Create SemanticAnalysis nodes

Step 5: Cluster join graph → Graph (if not --no-clustering)
  ↓ Group models by join patterns
  ↓ Create JoinCluster nodes
```

## Real-World Examples

### Example 1: Finance dbt project with DuckDB profiling

```bash
cd dbt_projects/medallion-reference
uv run dbt run && uv run dbt docs generate

cd ../../
uv run lineage init  # Initialize graph DB

uv run lineage load-dbt-full \
    dbt_projects/medallion-reference/target/ \
    --enable-profiling \
    --data-backend-type duckdb \
    --data-db-path dbt_projects/medallion-reference/medallion-reference.duckdb \
    --verbose
```

### Example 2: Production warehouse with Snowflake semantic views

```bash
# 1. Set credentials
export SNOWFLAKE_ACCOUNT=prod_account.us-east-1
export SNOWFLAKE_USER=lineage_user
export SNOWFLAKE_WAREHOUSE=METADATA_WH
export SNOWFLAKE_ROLE=METADATA_READER
export SNOWFLAKE_DATABASE=ANALYTICS
export SNOWFLAKE_SCHEMA=MARTS
export SNOWFLAKE_PRIVATE_KEY_PATH=/secure/keys/lineage_key.pem

# 2. Run dbt
cd dbt_projects/production
uv run dbt run --target prod
uv run dbt docs generate --target prod

# 3. Load everything
cd ../../
uv run lineage load-dbt-full \
    dbt_projects/production/target/ \
    --enable-semantic-views \
    --enable-profiling \
    --data-backend-type snowflake \
    --model-filter "fct_,dim_" \
    --verbose \
    --max-workers 16
```

### Example 3: Fast iteration (skip analysis)

```bash
# Just load dbt structure, no analysis
uv run lineage load-dbt-full target/ \
    --no-semantic \
    --no-clustering
```

## Querying Results

After loading, you can query the graph to see semantic views:

```cypher
// Find all semantic views and their referenced models
MATCH (sv:SemanticView)-[:DRAWS_FROM]->(m:DbtModel)
RETURN sv.name, sv.provider, COLLECT(m.name) as models

// Find Snowflake semantic views with revenue measures
MATCH (sv:SemanticView)
WHERE sv.provider = 'snowflake'
  AND sv.measures CONTAINS 'revenue'
RETURN sv.name, sv.database, sv.schema, sv.measures

// Find most popular models (referenced by most views)
MATCH (m:DbtModel)<-[:DRAWS_FROM]-(sv:SemanticView)
RETURN m.name, COUNT(sv) as view_count
ORDER BY view_count DESC
LIMIT 10
```

## Troubleshooting

### "Data backend not provided"

Make sure you specify `--data-backend-type` when using `--enable-profiling` or `--enable-semantic-views`:

```bash
# ❌ Wrong
uv run lineage load-dbt-full target/ --enable-semantic-views

# ✅ Correct
uv run lineage load-dbt-full target/ \
    --enable-semantic-views \
    --data-backend-type snowflake
```

### "Password is empty but I am using private key"

This usually means the Snowflake private key couldn't be loaded. Check:

1. `SNOWFLAKE_PRIVATE_KEY_PATH` is set correctly
2. The key file exists and is readable
3. If the key is encrypted, set `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE`

### "No semantic views found"

This means:

1. The Snowflake schema has no semantic views, OR
2. You don't have permissions to see them

Verify with Snowflake directly:

```sql
SHOW SEMANTIC VIEWS IN DATABASE.SCHEMA;
```

### Storage backend methods not implemented

If you see errors like `upsert_semantic_view not found`, the storage backend (FalkorDB/FalkorDBLite) hasn't implemented the semantic view methods yet. See the implementation guide in `SEMANTIC_VIEWS_IMPLEMENTATION_SUMMARY.md`.

## Next Steps

Once you've loaded semantic views:

1. **Explore in Graph**: Use graph visualization tools to explore
2. **Query via MCP**: Use the lineage MCP server to query from Claude/AI
3. **Impact Analysis**: See which views are affected by model changes
4. **Semantic Alignment**: Compare Snowflake measures with dbt semantic analysis
