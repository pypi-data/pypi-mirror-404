# Semantic Graph Schema Design

This document maps semantic analysis JSON artifacts to first-class graph nodes and edges, enabling Cypher-based exploration of inferred SQL semantics.

## Overview

The semantic analysis pipeline (10+ passes) extracts rich metadata from SQL queries. Currently, this data is stored as JSON in `InferredSemanticModel.full_analysis`. This design formalizes all artifacts into typed graph nodes and edges, making them queryable via Cypher.

## Design Principles

1. **Inference Naming**: All nodes/edges use `Inferred*` or `INFERRED_*` prefixes to indicate LLM-derived metadata
2. **Scope Preservation**: Per-scope analysis (outer, subquery:_, cte:_) is preserved via scope properties
3. **Evidence Tracking**: Source offsets and confidence signals are stored where applicable
4. **Backward Compatibility**: `full_analysis` JSON is retained for migration/debugging

## Mapping: JSON → Graph

### Pass 1: Relation Analysis

**JSON Structure**: `relation_analysis.relations[]`

**Graph Nodes**:

- `InferredRelation` (new)
  - Properties: `alias`, `base`, `kind` (table/view/cte/subquery), `scope`, `catalog`, `schema_name`, `is_temp`
  - ID: `{semantic_model_id}.relation.{alias}.{scope}`
  - Relationships:
    - `HAS_RELATION`: `InferredSemanticModel` → `InferredRelation`
    - `RESOLVES_TO_MODEL`: `InferredRelation` → `DbtModel` (when base resolves to a model)

**Graph Edges**:

- `HAS_RELATION`: Links semantic model to relation uses
- `RESOLVES_TO_MODEL`: Links relation alias to actual DbtModel (when resolvable)

### Pass 2: Column Analysis

**JSON Structure**: `column_analysis.columns_by_alias[]`, `column_analysis.column_refs[]`

**Graph Nodes**:

- `InferredColumnRef` (new)
  - Properties: `alias`, `column`, `scope`, `evidence` (optional offsets)
  - ID: `{semantic_model_id}.column.{alias}.{column}.{scope}`
  - Relationships:
    - `HAS_COLUMN_REF`: `InferredSemanticModel` → `InferredColumnRef`
    - `RESOLVES_TO_COLUMN`: `InferredColumnRef` → `DbtColumn` (when resolvable)

**Graph Edges**:

- `HAS_COLUMN_REF`: Links semantic model to column references
- `RESOLVES_TO_COLUMN`: Links column reference to actual DbtColumn

### Pass 3: Join Edge Analysis

**JSON Structure**: `join_analysis.joins[]`

**Graph Nodes**:

- `JoinEdge` (existing, enhanced)
  - Add properties: `left_model_id`, `right_model_id` (resolved DbtModel/DbtSource IDs)
  - Add property: `scope` (where join occurs)
  - Add property: `confidence` (optional, based on resolution success)
  - Relationships:
    - `HAS_JOIN_EDGE`: `InferredSemanticModel` → `JoinEdge` (existing)
    - `INFERRED_JOINS_WITH`: `DbtModel`/`DbtSource` → `JoinEdge` (new, when left/right resolved)
    - `JOINS_LEFT_MODEL`: `JoinEdge` → `DbtModel`/`DbtSource` (new, via left_model_id)
    - `JOINS_RIGHT_MODEL`: `JoinEdge` → `DbtModel`/`DbtSource` (new, via right_model_id)

**Graph Edges**:

- `INFERRED_JOINS_WITH`: Links DbtModel/DbtSource to JoinEdge nodes (bidirectional, weighted by count)
- `JOINS_LEFT_MODEL` / `JOINS_RIGHT_MODEL`: Direct links from JoinEdge to resolved models

### Pass 4: Filter Analysis

**JSON Structure**: `filter_analysis.where[]`, `filter_analysis.having[]`, `filter_analysis.qualify[]`

**Graph Nodes**:

- `InferredFilter` (new)
  - Properties: `predicate`, `clause` (WHERE/HAVING/QUALIFY), `scope`, `alias` (single-table filters)
  - ID: `{semantic_model_id}.filter.{clause}.{index}.{scope}`
  - Relationships:
    - `HAS_FILTER`: `InferredSemanticModel` → `InferredFilter`
    - `FILTERS_RELATION`: `InferredFilter` → `InferredRelation` (when alias resolvable)

**Graph Edges**:

- `HAS_FILTER`: Links semantic model to filter predicates
- `FILTERS_RELATION`: Links filter to relation it applies to

### Pass 5: Grouping Analysis

**JSON Structure**: `grouping_by_scope[]` (per-scope)

**Graph Nodes**:

- `InferredGroupingScope` (new)
  - Properties: `scope`, `is_aggregated`, `group_by` (list), `result_grain` (list), `measures` (list)
  - ID: `{semantic_model_id}.grouping.{scope}`
  - Relationships:
    - `HAS_GROUPING_SCOPE`: `InferredSemanticModel` → `InferredGroupingScope`
    - `HAS_SELECT_ITEM`: `InferredGroupingScope` → `InferredSelectItem` (new, for each SELECT item)

- `InferredSelectItem` (new)
  - Properties: `expr`, `alias`, `kind` (dimension/measure), `source_aliases` (list)
  - ID: `{semantic_model_id}.select.{scope}.{alias}`
  - Relationships:
    - `HAS_SELECT_ITEM`: `InferredGroupingScope` → `InferredSelectItem`

**Graph Edges**:

- `HAS_GROUPING_SCOPE`: Links semantic model to per-scope grouping analysis
- `HAS_SELECT_ITEM`: Links grouping scope to SELECT items

### Pass 6: Time Analysis

**JSON Structure**: `time_by_scope[]` (per-scope)

**Graph Nodes**:

- `InferredTimeScope` (new)
  - Properties: `scope`, `time_scope` (TimeScope object), `normalized_time_scope` (NormalizedTimeScope), `time_buckets` (list), `time_columns` (list)
  - ID: `{semantic_model_id}.time.{scope}`
  - Relationships:
    - `HAS_TIME_SCOPE`: `InferredSemanticModel` → `InferredTimeScope`

**Graph Edges**:

- `HAS_TIME_SCOPE`: Links semantic model to per-scope time analysis
- Note: `TimeWindow` node already exists for outer scope normalized_time_scope

### Pass 7: Window Analysis

**JSON Structure**: `window_by_scope[]` (per-scope)

**Graph Nodes**:

- `InferredWindowScope` (new)
  - Properties: `scope`, `windows` (list of WindowSpec)
  - ID: `{semantic_model_id}.window_scope.{scope}`
  - Relationships:
    - `HAS_WINDOW_SCOPE`: `InferredSemanticModel` → `InferredWindowScope`
    - `HAS_WINDOW_SPEC`: `InferredWindowScope` → `WindowFunction` (existing nodes)

**Graph Edges**:

- `HAS_WINDOW_SCOPE`: Links semantic model to per-scope window analysis
- `HAS_WINDOW_SPEC`: Links window scope to WindowFunction nodes

### Pass 8: Output Shape Analysis

**JSON Structure**: `output_by_scope[]` (per-scope)

**Graph Nodes**:

- `InferredOutputShape` (new)
  - Properties: `scope`, `order_by` (list of OrderByItem), `limit`, `offset`, `select_distinct`, `set_ops` (list)
  - ID: `{semantic_model_id}.output.{scope}`
  - Relationships:
    - `HAS_OUTPUT_SHAPE`: `InferredSemanticModel` → `InferredOutputShape`

**Graph Edges**:

- `HAS_OUTPUT_SHAPE`: Links semantic model to per-scope output shape

### Pass 9: Audit Analysis

**JSON Structure**: `audit_analysis.findings[]`, `audit_analysis.suggested_patches[]`

**Graph Nodes**:

- `InferredAuditFinding` (new)
  - Properties: `code`, `severity` (error/warning/info), `message`, `where` (JSON pointer), `context` (FindingContext)
  - ID: `{semantic_model_id}.audit.{code}.{index}`
  - Relationships:
    - `HAS_AUDIT_FINDING`: `InferredSemanticModel` → `InferredAuditFinding`

- `InferredAuditPatch` (new)
  - Properties: `op` (add/replace/remove), `path` (JSON pointer), `value`, `rationale`
  - ID: `{semantic_model_id}.patch.{index}`
  - Relationships:
    - `HAS_AUDIT_PATCH`: `InferredSemanticModel` → `InferredAuditPatch`

**Graph Edges**:

- `HAS_AUDIT_FINDING`: Links semantic model to audit findings
- `HAS_AUDIT_PATCH`: Links semantic model to suggested patches

### Pass 10: Business Semantics

**JSON Structure**: `business_semantics.*`

**Graph Nodes**:

- `InferredMeasure`, `InferredDimension`, `InferredFact`, `InferredSegment` (existing)
- No new nodes needed, already formalized

**Graph Edges**:

- Existing edges: `HAS_MEASURE`, `HAS_DIMENSION`, `HAS_FACT`, `HAS_SEGMENT`

### Pass 10a: Grain Humanization

**JSON Structure**: `grain_humanization.tokens[]`

**Graph Nodes**:

- `InferredGrainToken` (new)
  - Properties: `input_expr`, `normalized_term`, `is_measure`, `dropped`
  - ID: `{semantic_model_id}.grain_token.{index}`
  - Relationships:
    - `HAS_GRAIN_TOKEN`: `InferredSemanticModel` → `InferredGrainToken`

**Graph Edges**:

- `HAS_GRAIN_TOKEN`: Links semantic model to grain tokens

## Alias Resolution

A critical enhancement: resolve SQL aliases to actual `DbtModel` nodes.

**Process**:

1. Extract `relation_analysis.relations[]` to create `InferredRelation` nodes
2. For each relation with `kind="table"` or `kind="view"`:
   - Build qualified name: `{catalog}.{schema_name}.{base}` or `{base}` if unqualified
   - Query graph: `MATCH (m:DbtModel {relation_name: $qualified}) RETURN m.id`
   - If found, create `RESOLVES_TO_MODEL` edge: `InferredRelation` → `DbtModel`
3. For `JoinEdge` nodes:
   - Resolve `left_alias` and `right_alias` via `InferredRelation` → `DbtModel` lookup
   - Set `left_model_id` and `right_model_id` properties on `JoinEdge`
   - Create `INFERRED_JOINS_WITH` edges: `DbtModel` → `JoinEdge` (bidirectional)

**Confidence Scoring**:

- `high`: Alias resolved to exactly one model
- `medium`: Alias resolved via partial match or schema inference
- `low`: Alias could not be resolved
- Store as `confidence` property on `JoinEdge` and `InferredRelation`

## Query Patterns

### Find all joins between two models

```cypher
MATCH (m1:DbtModel {id: $model1})
MATCH (m2:DbtModel {id: $model2})
MATCH (m1)-[:INFERRED_JOINS_WITH]->(je:JoinEdge)<-[:INFERRED_JOINS_WITH]-(m2)
RETURN je.join_type, je.equi_condition, je.confidence
```

### Find all filters on a specific relation

```cypher
MATCH (m:DbtModel {id: $model})
MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)
MATCH (ism)-[:HAS_FILTER]->(f:InferredFilter)
MATCH (f)-[:FILTERS_RELATION]->(r:InferredRelation {alias: $alias})
RETURN f.predicate, f.clause
```

### Find all models that join with a given model

```cypher
MATCH (m:DbtModel {id: $model})
MATCH (m)-[:INFERRED_JOINS_WITH]->(je:JoinEdge)
MATCH (je)-[:JOINS_LEFT_MODEL|JOINS_RIGHT_MODEL]->(other:DbtModel)
WHERE other.id <> $model
RETURN DISTINCT other.id, other.name
```

### Find all audit errors for a model

```cypher
MATCH (m:DbtModel {id: $model})
MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)
MATCH (ism)-[:HAS_AUDIT_FINDING]->(af:InferredAuditFinding)
WHERE af.severity = 'error'
RETURN af.code, af.message, af.where
```

## Migration Strategy

1. **Backfill Existing Data**: Create migration utility that:
   - Iterates over all `InferredSemanticModel` nodes
   - Parses `full_analysis` JSON
   - Creates new graph nodes/edges per mapping above
   - Resolves aliases to models where possible
   - Marks migration version on `InferredSemanticModel`

2. **Dual-Write Period**: During transition:
   - Continue writing `full_analysis` JSON (backward compatibility)
   - Also write new graph nodes/edges (new functionality)
   - Agents can query either source

3. **Cutover**: Once migration complete:
   - Update all consumers to use graph nodes
   - Deprecate JSON parsing (keep for debugging)
   - Update documentation

## Benefits

1. **Cypher Queryable**: All semantic metadata accessible via standard graph queries
2. **Type Safety**: Typed nodes/edges prevent schema drift
3. **Performance**: Indexed graph queries faster than JSON parsing
4. **Composability**: Join clustering, lineage analysis, etc. can traverse graph directly
5. **Agent-Friendly**: Clear schema enables better Cypher generation by AI agents
