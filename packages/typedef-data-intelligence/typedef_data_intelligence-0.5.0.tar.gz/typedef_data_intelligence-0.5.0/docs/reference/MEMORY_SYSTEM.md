# Persistent Memory System for PydanticAI Agents

## Overview

The memory system provides **persistent, contextual memory** for PydanticAI agents using temporal knowledge graphs. Agents can store and recall:

- **User-specific memory**: Preferences, recent queries, personalized context
- **Organization-wide memory**: Data patterns, common joins, metric definitions, discovered insights

### Key Features

✅ **Multi-tenant isolation**: Separate graphs per user/organization
✅ **Temporal knowledge graphs**: Powered by FalkorDB + Graphiti
✅ **Hybrid search**: Semantic embeddings + keyword matching + graph traversal
✅ **Graceful degradation**: System works without memory backend
✅ **Auto-pattern capture**: Automatic discovery and storage of data patterns

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PydanticAI Agents                     │
│    (Analyst, Data Quality, Data Engineering)             │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────▼──────────┐
            │   Memory Tools      │
            │  (store/recall)     │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  MemoryStorage      │
            │    Protocol         │
            └──────────┬──────────┘
                       │
      ┌────────────────┴────────────────┐
      │                                  │
┌─────▼─────────┐            ┌──────────▼─────────┐
│ User Memory   │            │ Organization Memory│
│ (per user_id) │            │  (per org_id)      │
└───────────────┘            └────────────────────┘
      │                                  │
      └────────────────┬─────────────────┘
                       │
            ┌──────────▼──────────┐
            │  FalkorDB + Graphiti│
            │ Temporal Knowledge  │
            │       Graphs        │
            └─────────────────────┘
```

## Quick Start

### 1. Configuration

Add memory configuration to your `config.yml`:

```yaml
memory:
  enabled: true # Enable memory backend
  backend: falkordb
  host: localhost
  port: 6379
  username: "" # Optional
  password: ${FALKOR_PASSWORD} # Use env var for security
  default_org_id: "my_org"

lineage:
  backend: falkordb
  # ... lineage config ...

data:
  backend: duckdb
  # ... data config ...

agent:
  analyst:
    model: anthropic:claude-haiku-4-5
  data_engineer:
    model: anthropic:claude-sonnet-4-5-20250929
```

### 2. Installation

Install Graphiti dependencies:

```bash
pip install graphiti-core graphiti-core-falkordb
```

### 3. Start FalkorDB

Using Docker:

```bash
docker run -p 6379:6379 falkordb/falkordb:latest
```

### 4. Set User Context in Frontend

When calling the agent API, pass user context in headers:

```typescript
const response = await fetch("http://localhost:8000/agents/analyst", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-User-Id": "alice@company.com", // User identifier
    "X-Org-Id": "acme_corp", // Organization identifier
  },
  body: JSON.stringify({ message: "What is our ARR?" }),
});
```

### 5. Run Backend

```bash
export UNIFIED_CONFIG=/path/to/config.yml
export FALKOR_PASSWORD=your-password  # If using password auth
python webui/backend_pydantic.py
```

## Agent Tools

Agents automatically get memory tools when memory backend is enabled. No code changes needed!

### User Memory Tools

#### `store_user_preference`

Store user-specific preferences:

```python
# Agent automatically uses this when user expresses preferences
store_user_preference(
    key="default_chart_type",
    value="bar",
    category="visualization",
    description="User prefers bar charts for metrics"
)
```

#### `recall_user_context`

Search user's memory:

```python
# Agent automatically uses this to personalize responses
recall_user_context(
    query="chart preferences",
    limit=5
)
```

### Organization Memory Tools

#### `store_data_pattern`

Store discovered data patterns:

```python
# Agent automatically uses this when discovering patterns
store_data_pattern(
    pattern_type="common_join",
    pattern_name="arr_to_customers",
    description="ARR fact commonly joined to customers on customer_id",
    models_involved=["fct_arr_reporting", "dim_customers"],
    example_usage="JOIN dim_customers USING (customer_id)"
)
```

#### `recall_data_pattern`

Search organization's patterns:

```python
# Agent automatically uses this to leverage collective knowledge
recall_data_pattern(
    query="ARR metric joins",
    limit=5
)
```

### Hybrid Search Tool

#### `search_memories`

Search both user and org memory:

```python
# Most powerful - searches everything
search_memories(
    query="ARR metric calculations and chart preferences",
    scope="both",  # "user", "org", or "both"
    limit=10
)
```

## Memory Patterns

### User Memory Patterns

**1. Visualization Preferences**

```python
# User: "I prefer line charts for time series"
store_user_preference(
    key="time_series_chart_type",
    value="line",
    category="visualization",
    description="User prefers line charts for time series metrics"
)
```

**2. Default Filters**

```python
# User: "Always show me last 90 days by default"
store_user_preference(
    key="default_date_range",
    value="90_days",
    category="filters",
    description="User's default date range is last 90 days"
)
```

**3. Recent Queries**

```python
# Automatically stored when user asks questions
Episode(
    name="arr_by_customer_query",
    content="User asked about ARR trends by customer segment",
    episode_type=EpisodeType.USER_QUERY,
    source_description="Analyst session"
)
```

### Organization Memory Patterns

**1. Common Joins**

```python
# Discovered when agent executes joins
store_data_pattern(
    pattern_type="common_join",
    pattern_name="fct_orders_to_dim_customers",
    description="Orders fact joined to customers on customer_id",
    models_involved=["fct_orders", "dim_customers"],
    example_usage="JOIN dim_customers USING (customer_id)",
    confidence=0.95
)
```

**2. Metric Definitions**

```python
# Discovered when agent analyzes semantic views
store_data_pattern(
    pattern_type="metric_definition",
    pattern_name="ARR",
    description="Annual Recurring Revenue = SUM of subscription amounts",
    models_involved=["fct_arr_reporting_monthly"],
    example_usage="SUM(subscription_amount)",
    confidence=0.99
)
```

**3. Data Grain Patterns**

```python
# Discovered when agent analyzes model structure
store_data_pattern(
    pattern_type="grain",
    pattern_name="fct_orders_grain",
    description="fct_orders is at order line item grain (one row per line item)",
    models_involved=["fct_orders"],
    confidence=0.90
)
```

**4. Data Quality Patterns**

```python
# Discovered when agent troubleshoots issues
store_data_pattern(
    pattern_type="data_quality_issue",
    pattern_name="customer_null_emails",
    description="dim_customers has ~5% null email addresses",
    models_involved=["dim_customers"],
    confidence=0.85
)
```

## Auto-Capture with Memory Observer

For advanced usage, you can use `MemoryObserver` to automatically capture patterns:

```python
from lineage.agent.pydantic.memory_observer import MemoryObserver

observer = MemoryObserver(memory_backend=memory)

# After semantic view query
observer.observe_semantic_query(
    org_id="acme_corp",
    view_name="sv_arr_reporting",
    query_pattern="Group by customer_id, product_type",
    dimensions=["customer_id", "product_type"],
    measures=["total_arr"],
    discovered_by="analyst_agent"
)

# After discovering a join
observer.observe_join_pattern(
    org_id="acme_corp",
    models=["fct_arr", "dim_customers"],
    join_condition="customer_id",
    discovered_by="analyst_agent"
)

# After defining a metric
observer.observe_metric_definition(
    org_id="acme_corp",
    metric_name="ARR",
    calculation="SUM(subscription_amount)",
    source_model="fct_arr_reporting_monthly",
    discovered_by="analyst_agent"
)
```

## Advanced Configuration

### Multiple Organizations

Each organization gets its own isolated memory graph:

```
org_memory_acme_corp    → Graph for acme_corp
org_memory_startup_inc  → Graph for startup_inc
```

### Memory Statistics

Get statistics about memory usage:

```python
# User stats
stats = memory.get_stats(user_id="alice")
print(f"Alice has {stats['episode_count']} memories")

# Org stats
stats = memory.get_stats(org_id="acme_corp")
print(f"Org has {stats['entity_count']} entities")
```

### Clear Memory

```python
# Clear user memory (GDPR compliance)
memory.clear_user_memory(user_id="alice")

# Clear organization memory (reset after major schema changes)
memory.clear_org_memory(org_id="acme_corp")
```

## Troubleshooting

### Memory Backend Not Available

**Symptom**: Agents work but don't remember anything

**Solution**: Check that:

1. `memory.enabled=true` in config.yml
2. FalkorDB is running: `docker ps | grep falkordb`
3. graphiti-core is installed: `pip list | grep graphiti`

### User Context Not Set

**Symptom**: All memories stored under "anonymous" user

**Solution**: Ensure frontend passes X-User-Id header:

```javascript
headers: {
  'X-User-Id': 'alice@company.com',
  'X-Org-Id': 'acme_corp'
}
```

### Memory Search Returns Nothing

**Symptom**: `recall_user_context()` returns empty results

**Solution**:

1. Check that memories were stored: `memory.get_stats(user_id="alice")`
2. Try broader search queries (Graphiti uses semantic search)
3. Check FalkorDB logs for errors

## Implementation Details

### Graph Naming Convention

- User graphs: `user_memory_{sanitized_user_id}`
- Org graphs: `org_memory_{sanitized_org_id}`

User/org IDs are sanitized (alphanumeric + \_ - only).

### Temporal Knowledge Graphs

Graphiti maintains temporal validity for all entities and relationships:

- `valid_at`: When the information became valid
- `invalid_at`: When the information became invalid (optional)

This enables point-in-time queries and temporal reasoning.

### Hybrid Search Algorithm

Graphiti's search combines:

1. **Semantic embeddings**: Vector similarity using embeddings
2. **BM25 keyword matching**: Classic keyword search
3. **Graph distance reranking**: Prioritizes connected entities

### Performance Considerations

- **First query latency**: Initial graph creation takes ~1-2s
- **Subsequent queries**: Sub-10ms with FalkorDB's sparse matrix representation
- **Storage**: ~1KB per episode (depends on content)

## Best Practices

### ✅ Do

- Store high-confidence patterns (>0.8 confidence)
- Use descriptive pattern names
- Include example usage in patterns
- Store successful query patterns
- Leverage organization memory for shared knowledge

### ❌ Don't

- Store sensitive data (passwords, PII)
- Store every single query (be selective)
- Use memory for caching (use Redis instead)
- Store low-confidence patterns (<0.5)
- Hardcode user_id/org_id (use headers)

## Security

### Data Privacy

- User memory is isolated per user_id
- Organization memory is shared within org_id
- No cross-org data leakage (separate graphs)

### Authentication

- FalkorDB supports username/password auth
- Use environment variables for passwords: `${FALKOR_PASSWORD}`
- Consider TLS for production deployments

### GDPR Compliance

Users can request memory deletion:

```python
# Delete all user memory
memory.clear_user_memory(user_id="alice@company.com")
```

## Future Enhancements

Potential improvements:

- [ ] Temporal queries ("What did I ask last week?")
- [ ] Memory expiration policies (TTL for old memories)
- [ ] Memory importance scoring (prioritize important memories)
- [ ] Cross-user pattern discovery (privacy-preserving)
- [ ] Memory export/import (backup/restore)
- [ ] Additional graph backend support
- [ ] Vector similarity search optimization

## References

- [FalkorDB Documentation](https://docs.falkordb.com)
- [Graphiti GitHub](https://github.com/getzep/graphiti)
- [Graphiti + FalkorDB Integration](https://docs.falkordb.com/agentic-memory/graphiti.html)
- [PydanticAI Documentation](https://ai.pydantic.dev)
