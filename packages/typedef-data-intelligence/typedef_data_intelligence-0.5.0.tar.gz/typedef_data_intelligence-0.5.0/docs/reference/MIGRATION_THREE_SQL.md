# Migration Guide: Three-Layer SQL Normalization

This document covers breaking changes introduced in the `feat/three-layer-sql` branch.

## Breaking Changes

### 1. `ModelDetailsResult.compiled_sql` renamed to `canonical_sql`

The `compiled_sql` field on `ModelDetailsResult` has been renamed to `canonical_sql` to accurately reflect that the returned SQL is the physically-agnostic canonical form (catalog stripped, SELECT \* expanded, semantically canonicalized).

**Before:**

```python
details = storage.get_model_details(model_id)
sql = details.compiled_sql
```

**After:**

```python
details = storage.get_model_details(model_id)
sql = details.canonical_sql
```

### 2. `InferredRelation` drops `catalog` and `schema_name` fields

The `InferredRelation` node no longer stores `catalog` or `schema_name` properties. These were redundant with the physical layer and caused confusion between logical and physical concerns.

### 3. Source fingerprints now exclude database

Source fingerprints (`compute_source_fingerprint`) now exclude the `database` parameter from the hash computation. This makes fingerprints agnostic to database-level clones (common in CI/benchmarking environments).

**Impact:** All source fingerprints will be invalidated on first load after upgrade. Sources will be detected as "modified" and reprocessed.

### 4. Model fingerprints now schema-aware

`compute_model_fingerprint_result` now accepts an optional `schema` parameter. When provided, `SELECT *` is expanded using the schema before hashing, making fingerprints sensitive to upstream column changes.

**Impact:** All model fingerprints will be invalidated on first load after upgrade if schema is now provided. Models will be detected as "modified" and reprocessed.

## Recommended Upgrade Steps

1. Pull the latest code
2. Reinitialize the graph database:
   ```bash
   uv run lineage init
   ```
3. Reload with full semantic analysis:
   ```bash
   uv run lineage load-dbt-full <path-to-target/> --verbose
   ```

This will rebuild all nodes, edges, and semantic analysis from scratch, ensuring consistency with the new schema and fingerprint logic.
