# Semantic Analysis Tests

This directory contains tests for the hybrid deterministic + LLM semantic analysis pipeline.

## Test Organization

### Golden Snapshot Tests

| File                                  | Purpose                                                                                                                                 |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `test_deterministic_passes_golden.py` | Validates all 8 deterministic passes (relations, columns, joins, filters, grouping, windows, output) against committed golden snapshots |
| `test_targeted_heuristics_golden.py`  | Validates heuristic classification (time columns, semantic roles, PII, watermarks) against golden snapshots                             |

Golden tests use SQL fixtures from `tests/fixtures/semantic_sql/` and compare outputs against expected JSON in `tests/fixtures/semantic_expected/`.

### Validation Tests

| File                                   | Purpose                                                              |
| -------------------------------------- | -------------------------------------------------------------------- |
| `test_fixture_star_requires_schema.py` | Enforces that fixtures using `SELECT *` must provide schema metadata |

### Unit Tests (`deterministic/`)

Per-pass unit tests using minimal prerequisites:

| File                        | Pass | What it Tests                                          |
| --------------------------- | ---- | ------------------------------------------------------ |
| `test_pass_01_relations.py` | 1    | Relation extraction (tables, CTEs, subqueries, scopes) |
| `test_pass_02_columns.py`   | 2    | Column resolution by alias                             |
| `test_pass_03_joins.py`     | 3    | Join extraction (types, conditions, aliases)           |
| `test_pass_04_filters.py`   | 4    | WHERE/HAVING/QUALIFY predicates                        |
| `test_pass_05_grouping.py`  | 5    | GROUP BY, aggregation detection, result grain          |
| `test_pass_07_windows.py`   | 7    | Window functions (PARTITION BY, ORDER BY, frames)      |
| `test_pass_08_output.py`    | 8    | DISTINCT, LIMIT, ORDER BY, set operations              |

### Targeted Heuristics Tests (`deterministic/targeted/`)

| File                            | Purpose                                                        |
| ------------------------------- | -------------------------------------------------------------- |
| `test_column_classification.py` | LLM + heuristic column classification (includes PII detection) |
| `test_time_classification.py`   | Time column detection heuristics                               |
| `test_incremental_watermark.py` | Watermark detection for incremental models                     |

### Integration Tests (`integration/`)

| File                         | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `test_fenic_struct_merge.py` | Fenic DataFrame struct/array coalesce behavior |

## Adding New Fixtures

1. Create SQL file: `tests/fixtures/semantic_sql/<name>.sql`
2. (Optional) Add schema metadata: `tests/fixtures/semantic_sql/<name>.meta.json`
3. Generate golden: `uv run lineage-regen-semantic-goldens --fixture <name>`
4. Review and commit: `tests/fixtures/semantic_expected/<name>.json`

## Running Tests

```bash
# All semantic tests
uv run pytest tests/ingest/static_loaders/semantic/ -v

# Golden tests only
uv run pytest tests/ingest/static_loaders/semantic/test_*_golden.py -v

# Deterministic pass tests
uv run pytest tests/ingest/static_loaders/semantic/deterministic/ -v

# Targeted heuristics tests
uv run pytest tests/ingest/static_loaders/semantic/deterministic/targeted/ -v
```

## Regenerating Goldens

```bash
# Hermetic mode (no LLM, CI-safe)
uv run lineage-regen-semantic-goldens

# Single fixture
uv run lineage-regen-semantic-goldens --fixture fact_table

# With LLM (business semantics, requires API keys)
uv run lineage-regen-semantic-goldens --with-llm --concurrency 2
```
