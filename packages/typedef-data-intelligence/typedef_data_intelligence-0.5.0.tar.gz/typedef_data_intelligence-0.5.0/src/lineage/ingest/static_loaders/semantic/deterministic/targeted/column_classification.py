"""Comprehensive Column Classification.

Unified column classification that combines technical structure with business semantics.
This pass classifies columns on multiple orthogonal dimensions:

1. **semantic_role**: What business concept does the column represent?
   - surrogate_key, natural_key, foreign_key, flag, bucket_label, metric, attribute, timestamp

2. **derivation**: How is the value computed?
   - direct, aggregated, calculated, conditional, window, cast

3. **table_type**: What kind of table does this column come from?
   - fact, dimension, bridge, unknown

4. **business_name**: Human-readable name for the column

5. **PII detection**: Is this column personally identifiable information?
   - is_pii, pii_type, pii_confidence

Architecture:
- Each column is classified INDIVIDUALLY in its own LLM call
- Fenic parallelizes these calls automatically
- Context (relations, sibling columns, grouping) is passed for reference but not classified
- Query-level metadata (intent, domain) is computed via heuristics after column classification
- PII is detected per-column with full context (better than batch detection)

This approach ensures:
- Consistent processing time regardless of column count
- No risk of output token overflow for large models
- Better parallelization via Fenic's batch processing
- Better PII detection with full column context

Examples:
Uses Fenic's native MapExampleCollection to provide few-shot examples.
"""

from __future__ import annotations

import functools
import logging
import re
from typing import Any, Dict, List, Literal, Optional

import fenic
import polars as pl
from pydantic import BaseModel, Field

from lineage.ingest.static_loaders.semantic.deterministic.graph_enrichment import (
    ColumnLineageFeatures,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cardinality Threshold Constants
# ---------------------------------------------------------------------------
# These thresholds define the boundaries between cardinality levels.
# Used in LLM prompts and heuristic classification to ensure consistency.
CARDINALITY_LOW_THRESHOLD = 100  # Values below this are "low" cardinality
CARDINALITY_HIGH_THRESHOLD = 10_000  # Values above this are "high" cardinality
# Values between LOW and HIGH thresholds are "medium" cardinality


# Prompt for SINGLE column classification (row-by-row processing)
SINGLE_COLUMN_CLASSIFICATION_PROMPT = """
Classify this single SELECT column.

## Column to Classify
- Alias: {{ column.alias }}
- Expression: {{ column.expr }}
- Source tables: {{ column.source_aliases }}

## Query Context (for reference)
### Relations in Query
{% for rel in relations %}
- {{ rel.alias }} (base: {{ rel.base }}, kind: {{ rel.kind }})
{% endfor %}

### Other Columns in Query (for context only)
{% for sib in sibling_columns %}
- {{ sib.alias }}: {{ sib.expr }}
{% endfor %}

### Query Structure
- is_aggregated: {{ grouping_context.is_aggregated }}
- group_by: {{ grouping_context.group_by }}

## Classification Rules

### 1. semantic_role (what business concept does this represent?)

- **"surrogate_key"**: Hash/MD5 for deduplication or synthetic keys
  - Patterns: MD5(...), HASH(...), UUID(), SHA256(...)
  - Examples: `MD5(customer_id || order_id)`, `daily_user_id`

- **"natural_key"**: Business identifier that naturally identifies a record
  - Examples: `order_id`, `customer_id`, `product_sku`, `email`

- **"foreign_key"**: Reference to another table's primary key
  - Patterns: Usually `*_id` columns that join to dimension/fact tables
  - Examples: `customer_id` (in orders table), `product_id`

- **"flag"**: Boolean indicators (is_*, has_*, can_*)
  - Examples: `is_active`, `has_subscription`, `is_deleted`

- **"bucket_label"**: Categorical bucket/label, often from CASE statements
  - Examples: `IS_DESKTOP`, `IS_WEBAPP`, `tier_name`, `segment`
  - Often produces 0/1 or string labels

- **"metric"**: Business measure (numeric values used in calculations)
  - Examples: `revenue`, `total_amount`, `order_count`, `average_price`

- **"attribute"**: Descriptive property (non-key, non-metric)
  - Examples: `customer_name`, `product_description`, `status`

- **"timestamp"**: Time/date column
  - Examples: `created_at`, `order_date`, `activity_date`

### 2. derivation (how is it computed?)

- **"direct"**: Simple column reference (t.column)
- **"aggregated"**: Aggregate function (SUM, COUNT, AVG, MAX, MIN)
- **"calculated"**: Arithmetic or string expression (a + b, CONCAT)
- **"conditional"**: CASE/IF/IIF logic
- **"window"**: Window function (ROW_NUMBER, LAG, LEAD, RANK)
- **"cast"**: Type conversion only (CAST, ::type)

### 3. table_type (what kind of source table?)

Based on the source table(s):
- **"fact"**: Central fact/event table (orders, transactions, sales, events)
  - Table names often include: fct_, fact_, stg_, int_
- **"dimension"**: Descriptive lookup table (customers, products, stores, dates)
  - Table names often include: dim_, dimension_, lookup_, ref_
- **"bridge"**: Many-to-many relationship table
- **"unknown"**: Cannot determine

### 4. business_name

A clean, business-friendly name for this column:
- Strip technical prefixes (ss_, c_, d_)
- Convert snake_case to Title Case
- Examples: "ss_net_profit" -> "Net Profit", "c_last_name" -> "Last Name"

### 5. Additional Fields

- **is_categorical**: True if column represents categories even if numeric (0/1 flags, buckets)
- **cardinality_hint**: "low" (<100 values), "medium" (100-10,000), "high" (>10,000), null if unknown

### 6. Time-related signal

- **is_time_related**: True if the column represents time/date or a time-derived attribute
  - Examples: created_at, order_date, DATE_TRUNC('month', ...), EXTRACT(year FROM ...),
    d_year, fiscal_quarter, week_of_year, timestamp columns
  - False for metrics, IDs, flags, and non-time attributes

### 7. PII Detection (is this Personally Identifiable Information?)

Determine if this column contains PII based on name, expression, and context:

**Definitely PII (high confidence):**
- **"name"**: First name, last name, full name (first_name, last_name, customer_name)
- **"email"**: Email addresses (email, email_address, contact_email)
- **"phone"**: Phone numbers (phone, mobile, cell, telephone)
- **"address"**: Physical addresses (address, street, postal_code, zip_code)
- **"ssn"**: Social Security Numbers (ssn, social_security, tax_id)
- **"credit_card"**: Card numbers (card_number, cc_number)
- **"dob"**: Birth dates (dob, birth_date, date_of_birth, birthday)

**Likely PII (medium confidence):**
- **"ip_address"**: IP addresses (ip, ip_address, client_ip)
- **"device_id"**: Device identifiers (device_id, imei, mac_address)
- **"account_number"**: Financial accounts (account_number, routing_number)

**NOT PII:**
- Technical IDs: order_id, product_id, session_id, transaction_id
- Metrics: amount, count, total, revenue
- Timestamps: created_at, updated_at, order_date
- Status fields: is_active, status, state

Set `is_pii=true` if the column contains PII, with `pii_type` and `pii_confidence`.

Return JSON classification for this single column.
"""


# Prompt for query-level metadata (separate LLM call after column classification)
QUERY_METADATA_PROMPT = """
Analyze the query structure and classified columns to determine query-level metadata.

## Relations in Query
{% for rel in relations %}
- {{ rel.alias }} (base: {{ rel.base }}, kind: {{ rel.kind }})
{% endfor %}

## Classified Columns
{% for col in classified_columns %}
- {{ col.column_alias }}: semantic_role={{ col.semantic_role }}, derivation={{ col.derivation }}, table_type={{ col.table_type }}
{% endfor %}

## Query Structure
- is_aggregated: {{ grouping_context.is_aggregated }}
- group_by: {{ grouping_context.group_by }}
- has_limit: {{ grouping_context.has_limit }}
- has_order_by: {{ grouping_context.has_order_by }}
- has_window_functions: {{ grouping_context.has_window_functions }}

## Determine

### 1. fact_alias
Which relation alias is the primary fact table? Look for:
- Tables with fct_, fact_, stg_, int_ prefixes
- Tables that are the main source of metrics
- Tables that other tables join TO (not FROM)

### 2. intent
What is the query trying to accomplish?
- **"review_list"**: Non-aggregated query with LIMIT (browsing/sampling data)
- **"ranking"**: ORDER BY a metric with LIMIT (top-N analysis)
- **"aggregation"**: GROUP BY with aggregations (metrics/reporting)
- **"comparison"**: Multiple GROUP BY dimensions (cross-dimensional analysis)
- **"time_series"**: Time column in GROUP BY (trend analysis)
- **"snapshot"**: Point-in-time state of entities
- **"unknown"**: Cannot determine

Return JSON with fact_alias and intent.
"""


class QueryMetadata(BaseModel):
    """Query-level metadata determined by LLM analysis."""

    fact_alias: Optional[str] = Field(
        default=None, description="Primary fact table alias"
    )
    intent: Literal[
        "review_list", "ranking", "comparison", "aggregation", "time_series", "snapshot", "unknown"
    ] = Field(
        default="unknown",
        description="High-level query intent",
    )


class ColumnClassification(BaseModel):
    """Classification result for a single column."""

    column_alias: str = Field(description="The output column alias")
    expr: str = Field(description="Original expression")

    # Semantic role - what does this column represent?
    semantic_role: Literal[
        "surrogate_key",
        "natural_key",
        "foreign_key",
        "flag",
        "bucket_label",
        "metric",
        "attribute",
        "timestamp",
    ] = Field(description="What business concept this column represents")
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="Heuristic confidence in semantic_role classification",
    )

    # Derivation type - how is it computed? (orthogonal to semantic role)
    derivation: Literal[
        "direct",
        "aggregated",
        "calculated",
        "conditional",
        "window",
        "cast",
    ] = Field(description="How the column value is derived")

    # Table type - what kind of source table?
    table_type: Literal["fact", "dimension", "bridge", "unknown"] = Field(
        description="Type of source table"
    )

    # Business-friendly name
    business_name: str = Field(description="Business-friendly name for this column")

    # Additional classification fields
    is_categorical: bool = Field(
        description="True if column represents categories, even if numeric (0/1, buckets)"
    )
    cardinality_hint: Optional[Literal["low", "medium", "high"]] = Field(
        default=None,
        description=f"Expected cardinality: low (<{CARDINALITY_LOW_THRESHOLD}), medium ({CARDINALITY_LOW_THRESHOLD}-{CARDINALITY_HIGH_THRESHOLD:,}), high (>{CARDINALITY_HIGH_THRESHOLD:,})",
    )
    is_time_related: bool = Field(
        default=False,
        description="True if the column represents time/date or a time-derived attribute",
    )

    # PII detection fields
    is_pii: bool = Field(
        default=False,
        description="True if this column contains Personally Identifiable Information"
    )
    pii_type: Optional[
        Literal[
            "name",
            "email",
            "phone",
            "address",
            "ssn",
            "credit_card",
            "dob",
            "ip_address",
            "device_id",
            "account_number",
            "other",
        ]
    ] = Field(default=None, description="Type of PII if is_pii is True")
    pii_confidence: Optional[Literal["high", "medium", "low"]] = Field(
        default=None,
        description="Confidence level for PII detection: high (definite), medium (likely), low (maybe)",
    )


class ColumnClassificationResult(BaseModel):
    """Result of column classification for all columns in a query."""

    classifications: List[ColumnClassification] = Field(
        default_factory=list, description="Classification for each column"
    )

    # Query-level metadata (computed via heuristics after column classification)
    fact_alias: Optional[str] = Field(
        default=None, description="Primary fact table alias if identified"
    )
    intent: Literal[
        "review_list", "ranking", "comparison", "aggregation", "time_series", "snapshot", "unknown"
    ] = Field(
        default="unknown",
        description="High-level query intent",
    )

    # Key detection (aggregated from individual classifications)
    primary_key_candidates: List[str] = Field(
        default_factory=list,
        description="Column aliases that could be primary keys (natural_key + surrogate_key)",
    )
    has_surrogate_keys: bool = Field(
        default=False, description="True if any surrogate keys detected"
    )

    # PII aggregates (computed from individual column classifications)
    pii_columns: List[str] = Field(
        default_factory=list,
        description="Column aliases containing PII (where is_pii=True)",
    )
    high_risk_pii_count: int = Field(
        default=0,
        description="Number of columns with high-confidence PII",
    )


class ColumnContext(BaseModel):
    """Context about a column for classification."""

    alias: str = Field(description="Output column alias")
    expr: str = Field(description="Column expression SQL")
    source_aliases: List[str] = Field(default_factory=list)
    lineage_features: Optional[ColumnLineageFeatures] = Field(
        default=None,
        description="Optional graph-enriched lineage features for this column",
    )


class RelationContext(BaseModel):
    """Context about a relation for classification."""

    alias: str
    base: str
    kind: str


class GroupingContext(BaseModel):
    """Context about query grouping structure."""

    is_aggregated: bool = False
    group_by: List[str] = Field(default_factory=list)
    has_limit: bool = False
    has_order_by: bool = False
    has_window_functions: bool = False


class SiblingColumnContext(BaseModel):
    """Lightweight context about sibling columns (for reference only)."""

    alias: str
    expr: str = Field(default="", description="Column expression SQL")


def extract_classification_context(
    grouping_analysis: Dict[str, Any],
    relation_analysis: Dict[str, Any],
    column_features: Optional[Dict[str, Any]] = None,
) -> tuple[List[ColumnContext], List[RelationContext], GroupingContext]:
    """Extract context from deterministic analysis for classification.

    Args:
        grouping_analysis: Output from deterministic grouping pass
        relation_analysis: Output from deterministic relations pass
        column_features: Optional mapping of column alias -> lineage features

    Returns:
        Tuple of (columns, relations, grouping_context)
    """
    columns: List[ColumnContext] = []
    for item in grouping_analysis.get("select", []):
        alias = item.get("alias", "")
        lineage: Optional[ColumnLineageFeatures] = None
        if column_features and alias in column_features:
            try:
                lineage = ColumnLineageFeatures.model_validate(column_features[alias])
            except Exception:
                lineage = None
        columns.append(
            ColumnContext(
                alias=alias,
                expr=item.get("expr", ""),
                source_aliases=item.get("source_aliases", []),
                lineage_features=lineage,
            )
        )

    relations: List[RelationContext] = []
    for rel in relation_analysis.get("relations", []):
        relations.append(
            RelationContext(
                alias=rel.get("alias", ""),
                base=rel.get("base", ""),
                kind=rel.get("kind", "table"),
            )
        )

    # Extract grouping context
    grouping_context = GroupingContext(
        is_aggregated=grouping_analysis.get("is_aggregated", False),
        group_by=grouping_analysis.get("group_by", []),
        has_limit=grouping_analysis.get("has_limit", False),
        has_order_by=grouping_analysis.get("has_order_by", False),
        has_window_functions=grouping_analysis.get("has_window_functions", False),
    )

    return columns, relations, grouping_context


def build_single_column_examples() -> Any:
    """Build few-shot examples for single column classification.

    Returns:
        MapExampleCollection with single column examples
    """
    from fenic.core.types.semantic_examples import MapExample, MapExampleCollection

    examples = MapExampleCollection()

    # Example 1: Surrogate key (MD5 hash)
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "daily_user_id",
                    "expr": "MD5(COALESCE(c.customer_id, '') || '-' || o.order_date)",
                    "source_aliases": ["c", "o"],
                },
                "relations": [
                    {"alias": "o", "base": "fct_orders", "kind": "table"},
                    {"alias": "c", "base": "dim_customers", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "total_revenue", "expr": "SUM(o.order_total)"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["daily_user_id"],
                    "has_limit": False,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="daily_user_id",
                expr="MD5(COALESCE(c.customer_id, '') || '-' || o.order_date)",
                semantic_role="surrogate_key",
                derivation="calculated",
                table_type="fact",
                business_name="Daily User ID",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 2: Aggregated metric
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "total_revenue",
                    "expr": "SUM(o.order_total)",
                    "source_aliases": ["o"],
                },
                "relations": [
                    {"alias": "o", "base": "fct_orders", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "order_date", "expr": "o.order_date"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["order_date"],
                    "has_limit": False,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="total_revenue",
                expr="SUM(o.order_total)",
                semantic_role="metric",
                derivation="aggregated",
                table_type="fact",
                business_name="Total Revenue",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 3: Bucket label (CASE statement producing 0/1)
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "is_desktop",
                    "expr": "CASE WHEN e.platform = 'desktop' THEN 1 ELSE 0 END",
                    "source_aliases": ["e"],
                },
                "relations": [
                    {"alias": "e", "base": "fct_events", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "user_id", "expr": "e.user_id"},
                    {"alias": "event_count", "expr": "COUNT(*)"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["is_desktop"],
                    "has_limit": False,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="is_desktop",
                expr="CASE WHEN e.platform = 'desktop' THEN 1 ELSE 0 END",
                semantic_role="bucket_label",
                derivation="conditional",
                table_type="fact",
                business_name="Is Desktop",
                is_categorical=True,
                cardinality_hint="low",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 4: Flag column
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "is_active",
                    "expr": "u.is_active",
                    "source_aliases": ["u"],
                },
                "relations": [
                    {"alias": "u", "base": "dim_users", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "user_id", "expr": "u.user_id"},
                    {"alias": "user_name", "expr": "u.user_name"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["user_id"],  # Non-aggregated but selecting with key
                    "has_limit": True,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="is_active",
                expr="u.is_active",
                semantic_role="flag",
                derivation="direct",
                table_type="dimension",
                business_name="Is Active",
                is_categorical=True,
                cardinality_hint="low",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 5: Timestamp column
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "activity_date",
                    "expr": "DATE_TRUNC('day', e.created_at)",
                    "source_aliases": ["e"],
                },
                "relations": [
                    {"alias": "e", "base": "fct_events", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "user_id", "expr": "e.user_id"},
                    {"alias": "event_count", "expr": "COUNT(*)"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["activity_date"],
                    "has_limit": False,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="activity_date",
                expr="DATE_TRUNC('day', e.created_at)",
                semantic_role="timestamp",
                derivation="calculated",
                table_type="fact",
                business_name="Activity Date",
                is_categorical=False,
                cardinality_hint="medium",
                is_time_related=True,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 6: Foreign key in fact table
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "customer_id",
                    "expr": "o.customer_id",
                    "source_aliases": ["o"],
                },
                "relations": [
                    {"alias": "o", "base": "fct_orders", "kind": "table"},
                    {"alias": "c", "base": "dim_customers", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "order_date", "expr": "o.order_date"},
                    {"alias": "order_total", "expr": "SUM(o.order_total)"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["order_id"],  # Non-aggregated SELECT
                    "has_limit": False,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="customer_id",
                expr="o.customer_id",
                semantic_role="foreign_key",
                derivation="direct",
                table_type="fact",
                business_name="Customer ID",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 7: Natural key in dimension table
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "user_id",
                    "expr": "u.user_id",
                    "source_aliases": ["u"],
                },
                "relations": [
                    {"alias": "u", "base": "dim_users", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "user_name", "expr": "u.user_name"},
                    {"alias": "email", "expr": "u.email"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["user_id"],  # Non-aggregated dimension query
                    "has_limit": True,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="user_id",
                expr="u.user_id",
                semantic_role="natural_key",
                derivation="direct",
                table_type="dimension",
                business_name="User ID",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=False,
                pii_type=None,
                pii_confidence=None,
            ),
        )
    )

    # Example 8: PII - Email address (high confidence)
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "customer_email",
                    "expr": "c.email_address",
                    "source_aliases": ["c"],
                },
                "relations": [
                    {"alias": "c", "base": "dim_customers", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "customer_name", "expr": "c.customer_name"},
                    {"alias": "order_count", "expr": "COUNT(o.order_id)"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["customer_id"],  # Non-aggregated customer lookup
                    "has_limit": False,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="customer_email",
                expr="c.email_address",
                semantic_role="attribute",
                derivation="direct",
                table_type="dimension",
                business_name="Customer Email",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=True,
                pii_type="email",
                pii_confidence="high",
            ),
        )
    )

    # Example 9: PII - Full name (high confidence)
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "full_name",
                    "expr": "CONCAT(c.first_name, ' ', c.last_name)",
                    "source_aliases": ["c"],
                },
                "relations": [
                    {"alias": "c", "base": "dim_customers", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "customer_id", "expr": "c.customer_id"},
                    {"alias": "email", "expr": "c.email"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["customer_id"],  # Non-aggregated customer view
                    "has_limit": False,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="full_name",
                expr="CONCAT(c.first_name, ' ', c.last_name)",
                semantic_role="attribute",
                derivation="calculated",
                table_type="dimension",
                business_name="Full Name",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=True,
                pii_type="name",
                pii_confidence="high",
            ),
        )
    )

    # Example 10: PII - IP address (medium confidence)
    examples.create_example(
        MapExample(
            input={
                "column": {
                    "alias": "client_ip",
                    "expr": "e.ip_address",
                    "source_aliases": ["e"],
                },
                "relations": [
                    {"alias": "e", "base": "fct_events", "kind": "table"},
                ],
                "sibling_columns": [
                    {"alias": "event_type", "expr": "e.event_type"},
                    {"alias": "event_count", "expr": "COUNT(*)"},
                ],
                "grouping_context": {
                    "is_aggregated": False,
                    "group_by": ["event_id"],  # Non-aggregated event log
                    "has_limit": True,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=ColumnClassification(
                column_alias="client_ip",
                expr="e.ip_address",
                semantic_role="attribute",
                derivation="direct",
                table_type="fact",
                business_name="Client IP",
                is_categorical=False,
                cardinality_hint="high",
                is_time_related=False,
                is_pii=True,
                pii_type="ip_address",
                pii_confidence="medium",
            ),
        )
    )

    return examples


def build_query_metadata_examples() -> Any:
    """Build few-shot examples for query-level metadata classification.

    Returns:
        MapExampleCollection with query metadata examples
    """
    from fenic.core.types.semantic_examples import MapExample, MapExampleCollection

    examples = MapExampleCollection()

    # Example 1: Time series sales analysis
    examples.create_example(
        MapExample(
            input={
                "relations": [
                    {"alias": "o", "base": "fct_orders", "kind": "table"},
                    {"alias": "c", "base": "dim_customers", "kind": "table"},
                ],
                "classified_columns": [
                    {"column_alias": "order_month", "semantic_role": "timestamp", "derivation": "calculated", "table_type": "fact"},
                    {"column_alias": "total_revenue", "semantic_role": "metric", "derivation": "aggregated", "table_type": "fact"},
                    {"column_alias": "customer_segment", "semantic_role": "attribute", "derivation": "direct", "table_type": "dimension"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["order_month", "customer_segment"],
                    "has_limit": False,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=QueryMetadata(
                fact_alias="o",
                domain="sales",
                intent="time_series",
            ),
        )
    )

    # Example 2: Top-N ranking
    examples.create_example(
        MapExample(
            input={
                "relations": [
                    {"alias": "p", "base": "fct_pipeline", "kind": "table"},
                    {"alias": "r", "base": "dim_sales_reps", "kind": "table"},
                ],
                "classified_columns": [
                    {"column_alias": "rep_name", "semantic_role": "attribute", "derivation": "direct", "table_type": "dimension"},
                    {"column_alias": "total_pipeline", "semantic_role": "metric", "derivation": "aggregated", "table_type": "fact"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["rep_name"],
                    "has_limit": True,
                    "has_order_by": True,
                    "has_window_functions": False,
                },
            },
            output=QueryMetadata(
                fact_alias="p",
                domain="sales",
                intent="ranking",
            ),
        )
    )

    # Example 3: Finance ARR aggregation
    examples.create_example(
        MapExample(
            input={
                "relations": [
                    {"alias": "s", "base": "fct_subscriptions", "kind": "table"},
                ],
                "classified_columns": [
                    {"column_alias": "product_tier", "semantic_role": "attribute", "derivation": "direct", "table_type": "fact"},
                    {"column_alias": "arr", "semantic_role": "metric", "derivation": "aggregated", "table_type": "fact"},
                    {"column_alias": "customer_count", "semantic_role": "metric", "derivation": "aggregated", "table_type": "fact"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["product_tier"],
                    "has_limit": False,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=QueryMetadata(
                fact_alias="s",
                domain="finance",
                intent="aggregation",
            ),
        )
    )

    # Example 4: Product usage comparison
    examples.create_example(
        MapExample(
            input={
                "relations": [
                    {"alias": "e", "base": "fct_events", "kind": "table"},
                    {"alias": "u", "base": "dim_users", "kind": "table"},
                ],
                "classified_columns": [
                    {"column_alias": "is_desktop", "semantic_role": "bucket_label", "derivation": "conditional", "table_type": "fact"},
                    {"column_alias": "user_segment", "semantic_role": "attribute", "derivation": "direct", "table_type": "dimension"},
                    {"column_alias": "event_count", "semantic_role": "metric", "derivation": "aggregated", "table_type": "fact"},
                ],
                "grouping_context": {
                    "is_aggregated": True,
                    "group_by": ["is_desktop", "user_segment"],
                    "has_limit": False,
                    "has_order_by": False,
                    "has_window_functions": False,
                },
            },
            output=QueryMetadata(
                fact_alias="e",
                domain="product",
                intent="comparison",
            ),
        )
    )

    return examples


@functools.lru_cache(maxsize=1)
def get_single_column_examples() -> Any:
    """Get cached single column examples collection."""
    return build_single_column_examples()


@functools.lru_cache(maxsize=1)
def get_query_metadata_examples() -> Any:
    """Get cached query metadata examples collection."""
    return build_query_metadata_examples()


def heuristic_classify_single_column(
    column: ColumnContext,
    relations: List[RelationContext],
    grouping_context: GroupingContext,
) -> ColumnClassification:
    """Classify a single column using heuristics (no LLM).

    Args:
        column: The column to classify
        relations: Query relations for context
        grouping_context: Query grouping structure

    Returns:
        ColumnClassification for this column
    """
    FACT_TABLE_PATTERNS = {
        "fct_",
        "fact_",
        "stg_",
        "int_",
        "_fact",
        "_fct",
        "orders",
        "sales",
        "transactions",
        "events",
        "logs",
    }

    DIM_TABLE_PATTERNS = {
        "dim_",
        "dimension_",
        "lookup_",
        "ref_",
        "_dim",
        "customers",
        "products",
        "stores",
        "dates",
        "users",
    }

    HASH_FUNCS = {"md5", "hash", "sha256", "sha1", "uuid"}
    FLAG_PATTERNS = re.compile(r"^(is_|has_|can_|should_|was_)", re.IGNORECASE)
    TIMESTAMP_PATTERNS = {
        "date",
        "time",
        "timestamp",
        "_at",
        "created",
        "updated",
        "modified",
    }
    AGG_FUNCS = {"sum", "count", "avg", "min", "max", "stddev", "variance"}
    WINDOW_FUNCS = {
        "row_number",
        "rank",
        "dense_rank",
        "lag",
        "lead",
        "first_value",
        "last_value",
    }
    TIME_FUNCS = {
        "date_trunc",
        "datetrunc",
        "extract",
        "dateadd",
        "date_add",
        "date_sub",
        "datediff",
        "to_date",
        "to_timestamp",
        "timestamp",
        "date",
    }

    # PII detection patterns (merged from pii_detection.py)
    HIGH_CONFIDENCE_PII_PATTERNS: Dict[str, str] = {
        "name": r"(first_name|last_name|full_name|customer_name|user_name|employee_name)",
        "email": r"(email|email_address|e_mail|contact_email)",
        "phone": r"(phone|phone_number|mobile|cell|telephone|fax)",
        "address": r"(address|street|postal_code|zip_code|city.*state|home_address)",
        "ssn": r"(ssn|social_security|tax_id|national_id)",
        "credit_card": r"(card_number|cc_number|credit_card|card_num)",
        "dob": r"(dob|birth_date|date_of_birth|birthday)",
    }

    MEDIUM_CONFIDENCE_PII_PATTERNS: Dict[str, str] = {
        # Use word boundaries (\b) to prevent false positives like "Stripe" matching "ip"
        "ip_address": r"\b(ip|ip_address|client_ip|remote_ip|source_ip)\b",
        "device_id": r"\b(device_id|imei|mac_address|hardware_id|device_identifier)\b",
        "account_number": r"\b(account_number|routing_number|bank_account)\b",
    }

    # Build alias -> table_type mapping
    alias_to_type: Dict[str, str] = {}
    for rel in relations:
        base = rel.base.lower()
        if any(p in base for p in FACT_TABLE_PATTERNS):
            alias_to_type[rel.alias] = "fact"
        elif any(p in base for p in DIM_TABLE_PATTERNS):
            alias_to_type[rel.alias] = "dimension"
        else:
            alias_to_type[rel.alias] = "unknown"

    expr_lower = column.expr.lower()
    alias_lower = column.alias.lower()

    # Determine table type from source aliases
    table_type: Literal["fact", "dimension", "bridge", "unknown"] = "unknown"
    for src in column.source_aliases:
        if src in alias_to_type:
            table_type = alias_to_type[src]
            break

    # Determine derivation type
    derivation: Literal[
        "direct", "aggregated", "calculated", "conditional", "window", "cast"
    ]
    if any(f"{func}(" in expr_lower for func in AGG_FUNCS):
        derivation = "aggregated"
    elif any(f"{func}(" in expr_lower for func in WINDOW_FUNCS):
        derivation = "window"
    elif "case " in expr_lower or "iff(" in expr_lower:
        derivation = "conditional"
    elif "cast(" in expr_lower or "::" in column.expr:
        derivation = "cast"
    elif any(op in column.expr for op in ["+", "-", "*", "/", "||", "concat"]):
        derivation = "calculated"
    else:
        derivation = "direct"

    # Graph-enriched lineage hints: avoid labeling as purely direct when lineage
    # indicates transformation or multi-hop ancestry.
    if column.lineage_features:
        if (
            derivation == "direct"
            and (
                column.lineage_features.has_transformation
                or column.lineage_features.max_depth > 1
                or column.lineage_features.fan_in > 1
            )
        ):
            derivation = "calculated"

    def _is_time_related(alias: str, expr: str) -> bool:
        text = f"{alias} {expr}".lower()
        if any(p in text for p in TIMESTAMP_PATTERNS):
            return True
        return any(func in text for func in TIME_FUNCS)

    # Determine semantic role
    semantic_role: Literal[
        "surrogate_key",
        "natural_key",
        "foreign_key",
        "flag",
        "bucket_label",
        "metric",
        "attribute",
        "timestamp",
    ]

    # Check for surrogate key (hash functions)
    if any(f"{func}(" in expr_lower for func in HASH_FUNCS):
        semantic_role = "surrogate_key"
    # Check for flags
    elif FLAG_PATTERNS.match(alias_lower):
        semantic_role = "flag"
    # Check for bucket labels (CASE producing 0/1 or categories)
    elif derivation == "conditional" and (
        " then 1 " in expr_lower or " then 0 " in expr_lower
    ):
        semantic_role = "bucket_label"
    # Check for timestamps
    elif any(p in alias_lower for p in TIMESTAMP_PATTERNS):
        semantic_role = "timestamp"
    # Check for metrics (aggregated expression)
    elif derivation == "aggregated":
        semantic_role = "metric"
    # Check for natural keys (in dimension table)
    elif (
        alias_lower.endswith("_id") or alias_lower == "id"
    ) and table_type == "dimension":
        semantic_role = "natural_key"
    # Check for foreign keys (in fact table)
    elif alias_lower.endswith("_id") or alias_lower == "id":
        semantic_role = "foreign_key"
    else:
        semantic_role = "attribute"

    # Lineage-aware semantic role adjustment and confidence
    confidence: Literal["high", "medium", "low"] = "medium"
    lineage_direct = False
    if column.lineage_features:
        lineage_direct = (
            column.lineage_features.fan_in <= 1
            and column.lineage_features.max_depth <= 1
            and not column.lineage_features.has_transformation
            and column.lineage_features.min_edge_confidence == "direct"
        )

        # Downgrade key classifications when lineage indicates derived values
        if semantic_role in ("surrogate_key", "natural_key", "foreign_key") and not lineage_direct:
            semantic_role = "attribute"
            confidence = "low"
        elif semantic_role in ("surrogate_key", "natural_key", "foreign_key") and lineage_direct:
            confidence = "high"
        elif semantic_role == "metric" and column.lineage_features.fan_in > 1:
            confidence = "high"
        elif semantic_role == "timestamp" and lineage_direct:
            confidence = "high"

    # Default confidence for common deterministic patterns
    if confidence == "medium":
        if semantic_role == "metric" and derivation in ("aggregated", "window"):
            confidence = "high"
        elif semantic_role in ("flag", "bucket_label") and (
            FLAG_PATTERNS.match(alias_lower) or derivation == "conditional"
        ):
            confidence = "high"
        elif semantic_role == "timestamp" and any(p in alias_lower for p in TIMESTAMP_PATTERNS):
            confidence = "high"

    # Determine cardinality hint
    cardinality_hint: Optional[Literal["low", "medium", "high"]] = None
    if semantic_role == "flag" or semantic_role == "bucket_label":
        cardinality_hint = "low"
    elif semantic_role in ("surrogate_key", "natural_key", "foreign_key"):
        cardinality_hint = "high"
    elif semantic_role == "timestamp":
        cardinality_hint = "medium"

    # Determine if categorical
    is_categorical = semantic_role in ("flag", "bucket_label") or (
        derivation == "conditional" and semantic_role == "attribute"
    )

    # Generate business name
    business_name = _generate_business_name(column.alias)

    # PII Detection (heuristic)
    is_pii = False
    pii_type: Optional[
        Literal[
            "name", "email", "phone", "address", "ssn", "credit_card",
            "dob", "ip_address", "device_id", "account_number", "other"
        ]
    ] = None
    pii_confidence: Optional[Literal["high", "medium", "low"]] = None

    combined = f"{alias_lower} {expr_lower}"

    # Check high confidence PII patterns first
    for ptype, pattern in HIGH_CONFIDENCE_PII_PATTERNS.items():
        if re.search(pattern, combined, re.IGNORECASE):
            is_pii = True
            pii_type = ptype  # type: ignore[assignment]
            pii_confidence = "high"
            break

    # Check medium confidence PII patterns if no high confidence match
    if not is_pii:
        for ptype, pattern in MEDIUM_CONFIDENCE_PII_PATTERNS.items():
            if re.search(pattern, combined, re.IGNORECASE):
                is_pii = True
                pii_type = ptype  # type: ignore[assignment]
                pii_confidence = "medium"
                break

    is_time_related = _is_time_related(column.alias, column.expr)

    return ColumnClassification(
        column_alias=column.alias,
        expr=column.expr,
        semantic_role=semantic_role,
        confidence=confidence,
        derivation=derivation,
        table_type=table_type,
        business_name=business_name,
        is_categorical=is_categorical,
        cardinality_hint=cardinality_hint,
        is_time_related=is_time_related,
        is_pii=is_pii,
        pii_type=pii_type,
        pii_confidence=pii_confidence,
    )


def heuristic_column_classification(
    grouping_analysis: Dict[str, Any],
    relation_analysis: Dict[str, Any],
    column_features: Optional[Dict[str, Any]] = None,
) -> ColumnClassificationResult:
    """Classify all columns using heuristics (no LLM).

    This is a fallback when LLM is not available or for testing.

    Args:
        grouping_analysis: Output from deterministic grouping pass
        relation_analysis: Output from deterministic relations pass
        column_features: Optional mapping of column alias -> lineage features

    Returns:
        ColumnClassificationResult based on heuristics
    """
    columns, relations, grouping_context = extract_classification_context(
        grouping_analysis, relation_analysis, column_features
    )

    classifications: List[ColumnClassification] = []
    for col in columns:
        classification = heuristic_classify_single_column(
            col, relations, grouping_context
        )
        classifications.append(classification)

    # Aggregate query-level metadata from individual classifications (heuristic fallback)
    return _aggregate_classification_result_heuristic(classifications, relations, grouping_context)


def _aggregate_classification_result_heuristic(
    classifications: List[ColumnClassification],
    relations: List[RelationContext],
    grouping_context: GroupingContext,
) -> ColumnClassificationResult:
    """Aggregate individual column classifications into a query-level result using heuristics.

    This is a fallback when LLM is not available.

    Args:
        classifications: Individual column classifications
        relations: Query relations
        grouping_context: Query grouping structure

    Returns:
        ColumnClassificationResult with aggregated metadata (heuristic-based)
    """
    # Find primary key candidates
    primary_key_candidates = [
        c.column_alias
        for c in classifications
        if c.semantic_role in ("natural_key", "surrogate_key")
    ]

    # Check for surrogate keys
    has_surrogate_keys = any(
        c.semantic_role == "surrogate_key" for c in classifications
    )

    # Find fact alias from relations (heuristic)
    fact_alias = None
    FACT_PATTERNS = {"fct_", "fact_", "stg_", "int_", "_fact", "_fct"}
    for rel in relations:
        if any(p in rel.base.lower() for p in FACT_PATTERNS):
            fact_alias = rel.alias
            break

    # Determine query intent from grouping context and classifications (heuristic)
    intent: Literal[
        "review_list", "ranking", "comparison", "aggregation", "time_series", "snapshot", "unknown"
    ] = "unknown"

    if grouping_context.is_aggregated:
        # Check for time series (timestamp in group by)
        time_cols_in_group_by = [
            c
            for c in classifications
            if c.semantic_role == "timestamp"
            and c.column_alias in grouping_context.group_by
        ]
        if time_cols_in_group_by:
            intent = "time_series"
        elif len(grouping_context.group_by) > 1:
            intent = "comparison"
        else:
            intent = "aggregation"
    elif grouping_context.has_limit:
        if grouping_context.has_order_by:
            intent = "ranking"
        else:
            intent = "review_list"

    # Aggregate PII columns from individual classifications
    pii_columns = [c.column_alias for c in classifications if c.is_pii]
    high_risk_pii_count = sum(
        1 for c in classifications if c.is_pii and c.pii_confidence == "high"
    )

    return ColumnClassificationResult(
        classifications=classifications,
        fact_alias=fact_alias,
        domain=None,  # Heuristics can't reliably determine domain
        intent=intent,
        primary_key_candidates=primary_key_candidates,
        has_surrogate_keys=has_surrogate_keys,
        pii_columns=pii_columns,
        high_risk_pii_count=high_risk_pii_count,
    )


def classify_query_metadata(
    classifications: List[ColumnClassification],
    relations: List[RelationContext],
    grouping_context: GroupingContext,
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> QueryMetadata:
    """Classify query-level metadata using LLM.

    This is a separate LLM call that runs AFTER column classification,
    using the classified columns as input to determine fact_alias, domain, and intent.

    Args:
        classifications: Individual column classifications (already classified)
        relations: Query relations
        grouping_context: Query grouping structure
        session: Fenic session for LLM calls
        model_size: T-shirt size for LLM
        use_examples: Whether to use few-shot examples

    Returns:
        QueryMetadata with fact_alias, domain, and intent
    """
    # Create lightweight column summaries for the prompt
    classified_columns = [
        {
            "column_alias": c.column_alias,
            "semantic_role": c.semantic_role,
            "derivation": c.derivation,
            "table_type": c.table_type,
        }
        for c in classifications
    ]

    # Build input row
    rows = [
        {
            "relations": [r.model_dump() for r in relations],
            "classified_columns": classified_columns,
            "grouping_context": grouping_context.model_dump(),
        }
    ]

    # Create Polars DataFrame with explicit schema to avoid type inference issues
    schema = get_query_metadata_input_schema()
    polars_df = pl.DataFrame(rows, schema=schema)

    # Convert to Fenic DataFrame
    df = session.create_dataframe(polars_df)

    examples = get_query_metadata_examples() if use_examples else None

    df = df.with_column(
        "metadata",
        fenic.semantic.map(
            QUERY_METADATA_PROMPT,
            response_format=QueryMetadata,
            relations=fenic.col("relations"),
            classified_columns=fenic.col("classified_columns"),
            grouping_context=fenic.col("grouping_context"),
            model_alias=model_size,
            max_output_tokens=4096,
            request_timeout=60,
            strict=False,
            examples=examples,
        ),
    )

    results = df.to_pylist()
    if results:
        metadata_dict = results[0].get("metadata")
        if isinstance(metadata_dict, dict):
            return QueryMetadata(**metadata_dict)

    # Fallback to defaults
    return QueryMetadata()


def _build_query_metadata_batch_schema() -> pl.Schema:
    """Build explicit Polars schema for batched query metadata classification.

    Includes model_id for tracking results back to their models.
    """
    relation_struct = pl.Struct({
        "alias": pl.String,
        "base": pl.String,
        "kind": pl.String,
    })

    classified_column_struct = pl.Struct({
        "column_alias": pl.String,
        "semantic_role": pl.String,
        "derivation": pl.String,
        "table_type": pl.String,
    })

    grouping_struct = pl.Struct({
        "is_aggregated": pl.Boolean,
        "group_by": pl.List(pl.String),
        "has_limit": pl.Boolean,
        "has_order_by": pl.Boolean,
        "has_window_functions": pl.Boolean,
    })

    return pl.Schema({
        "model_id": pl.String,
        "relations": pl.List(relation_struct),
        "classified_columns": pl.List(classified_column_struct),
        "grouping_context": grouping_struct,
    })


def classify_query_metadata_batch(
    models_data: List[Dict[str, Any]],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> Dict[str, QueryMetadata]:
    """Classify query-level metadata for multiple models in a single batch.

    Args:
        models_data: List of dicts with keys:
            - model_id: str
            - classifications: List[ColumnClassification]
            - relations: List[RelationContext]
            - grouping_context: GroupingContext
        session: Fenic session for LLM calls
        model_size: T-shirt size for LLM
        use_examples: Whether to use few-shot examples

    Returns:
        Dict mapping model_id -> QueryMetadata
    """
    if not models_data:
        return {}

    # Build rows for all models
    rows = []
    for model_data in models_data:
        model_id = model_data["model_id"]
        classifications = model_data["classifications"]
        relations = model_data["relations"]
        grouping_context = model_data["grouping_context"]

        classified_columns = [
            {
                "column_alias": c.column_alias,
                "semantic_role": c.semantic_role,
                "derivation": c.derivation,
                "table_type": c.table_type,
            }
            for c in classifications
        ]

        rows.append({
            "model_id": model_id,
            "relations": [r.model_dump() for r in relations],
            "classified_columns": classified_columns,
            "grouping_context": grouping_context.model_dump(),
        })

    # Create single DataFrame with all models
    schema = _build_query_metadata_batch_schema()
    polars_df = pl.DataFrame(rows, schema=schema)
    df = session.create_dataframe(polars_df)

    examples = get_query_metadata_examples() if use_examples else None

    # Run single batched classification
    df = df.with_column(
        "metadata",
        fenic.semantic.map(
            QUERY_METADATA_PROMPT,
            response_format=QueryMetadata,
            relations=fenic.col("relations"),
            classified_columns=fenic.col("classified_columns"),
            grouping_context=fenic.col("grouping_context"),
            model_alias=model_size,
            max_output_tokens=4096,
            request_timeout=60,
            strict=False,
            examples=examples,
        ),
    )

    # Collect and map back to model_ids
    results = df.to_pylist()
    metadata_by_model: Dict[str, QueryMetadata] = {}

    for row in results:
        model_id = row.get("model_id")
        metadata_dict = row.get("metadata")
        if model_id and isinstance(metadata_dict, dict):
            metadata_by_model[model_id] = QueryMetadata(**metadata_dict)
        elif model_id:
            metadata_by_model[model_id] = QueryMetadata()

    return metadata_by_model


def _generate_business_name(alias: str) -> str:
    """Generate a business-friendly name from a column alias."""
    # Remove common prefixes
    prefixes = ["ss_", "c_", "d_", "s_", "p_", "cd_", "sr_", "ws_", "wr_", "i_"]
    name = alias
    for prefix in prefixes:
        if name.lower().startswith(prefix):
            name = name[len(prefix) :]
            break

    # Replace underscores with spaces and title case
    name = name.replace("_", " ").title()

    return name


def add_column_classification_column(
    df: "fenic.DataFrame",
    model_size: str = "micro",
    use_examples: bool = True,
) -> "fenic.DataFrame":
    """Add column classification to DataFrame using row-by-row LLM processing.

    IMPORTANT: The input DataFrame should have ONE ROW PER COLUMN to classify.
    Each row should contain:
    - 'column': The column to classify (ColumnContext dict)
    - 'relations': List of relations in the query (for context)
    - 'sibling_columns': List of other columns (for context, not classified)
    - 'grouping_context': Query grouping structure (for context)

    Fenic will parallelize the LLM calls across rows automatically.

    Args:
        df: DataFrame with one row per column to classify
        model_size: T-shirt size for LLM (micro recommended for single column)
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        DataFrame with 'classification' column added (ColumnClassification per row)
    """
    examples = get_single_column_examples() if use_examples else None

    return df.with_column(
        "classification",
        fenic.semantic.map(
            SINGLE_COLUMN_CLASSIFICATION_PROMPT,
            response_format=ColumnClassification,
            column=fenic.col("column"),
            relations=fenic.col("relations"),
            sibling_columns=fenic.col("sibling_columns"),
            grouping_context=fenic.col("grouping_context"),
            model_alias=model_size,
            max_output_tokens=2048,  # Keep high for reasoning tokens
            request_timeout=300,
            strict=False,
            examples=examples,
        ),
    )


def _build_classification_input_schema() -> pl.Schema:
    """Build explicit Polars schema for column classification input rows.

    This avoids type inference issues with empty lists and null values.
    """
    # Column context struct: {alias: str, expr: str, source_aliases: List[str]}
    column_struct = pl.Struct({
        "alias": pl.String,
        "expr": pl.String,
        "source_aliases": pl.List(pl.String),
    })

    # Relation context struct: {alias: str, base: str, kind: str}
    relation_struct = pl.Struct({
        "alias": pl.String,
        "base": pl.String,
        "kind": pl.String,
    })

    # Sibling column struct: {alias: str, expr: str}
    sibling_struct = pl.Struct({
        "alias": pl.String,
        "expr": pl.String,
    })

    # Grouping context struct
    grouping_struct = pl.Struct({
        "is_aggregated": pl.Boolean,
        "group_by": pl.List(pl.String),
        "has_limit": pl.Boolean,
        "has_order_by": pl.Boolean,
        "has_window_functions": pl.Boolean,
    })

    return pl.Schema({
        "model_id": pl.String,
        "column_index": pl.Int64,
        "column": column_struct,
        "relations": pl.List(relation_struct),
        "sibling_columns": pl.List(sibling_struct),
        "grouping_context": grouping_struct,
    })


@functools.lru_cache(maxsize=1)
def get_classification_input_schema() -> pl.Schema:
    """Get cached Polars schema for classification input rows."""
    return _build_classification_input_schema()


def _build_query_metadata_input_schema() -> pl.Schema:
    """Build explicit Polars schema for query metadata classification input.

    This avoids type inference issues with empty lists.
    """
    # Relation struct: {alias: str, base: str, kind: str}
    relation_struct = pl.Struct({
        "alias": pl.String,
        "base": pl.String,
        "kind": pl.String,
    })

    # Classified column summary struct
    classified_column_struct = pl.Struct({
        "column_alias": pl.String,
        "semantic_role": pl.String,
        "derivation": pl.String,
        "table_type": pl.String,
    })

    # Grouping context struct
    grouping_struct = pl.Struct({
        "is_aggregated": pl.Boolean,
        "group_by": pl.List(pl.String),
        "has_limit": pl.Boolean,
        "has_order_by": pl.Boolean,
        "has_window_functions": pl.Boolean,
    })

    return pl.Schema({
        "relations": pl.List(relation_struct),
        "classified_columns": pl.List(classified_column_struct),
        "grouping_context": grouping_struct,
    })


@functools.lru_cache(maxsize=1)
def get_query_metadata_input_schema() -> pl.Schema:
    """Get cached Polars schema for query metadata input rows."""
    return _build_query_metadata_input_schema()


def explode_columns_for_classification(
    grouping_analysis: Dict[str, Any],
    relation_analysis: Dict[str, Any],
    model_id: str,
) -> List[Dict[str, Any]]:
    """Explode columns into individual rows for parallel classification.

    Args:
        grouping_analysis: Output from deterministic grouping pass
        relation_analysis: Output from deterministic relations pass
        model_id: Model identifier (for tracking)

    Returns:
        List of dicts, one per column, ready for DataFrame creation
    """
    columns, relations, grouping_context = extract_classification_context(
        grouping_analysis, relation_analysis
    )

    # Create sibling column context (lightweight, just alias and expr)
    sibling_contexts = [
        SiblingColumnContext(alias=c.alias, expr=c.expr).model_dump() for c in columns
    ]

    rows = []
    for i, col in enumerate(columns):
        # Exclude current column from siblings
        siblings = sibling_contexts[:i] + sibling_contexts[i + 1 :]

        rows.append(
            {
                "model_id": model_id,
                "column_index": i,
                "column": col.model_dump(),
                "relations": [r.model_dump() for r in relations],
                "sibling_columns": siblings,
                "grouping_context": grouping_context.model_dump(),
            }
        )

    return rows


def reassemble_classifications(
    classified_rows: List[Dict[str, Any]],
) -> List[ColumnClassification]:
    """Reassemble individual column classifications from DataFrame rows.

    Args:
        classified_rows: List of dicts with 'classification' key containing
            ColumnClassification dicts

    Returns:
        List of ColumnClassification objects, sorted by column_index
    """
    # Sort by column index to maintain order
    sorted_rows = sorted(classified_rows, key=lambda r: r.get("column_index", 0))

    classifications = []
    for row in sorted_rows:
        classification_dict = row.get("classification")
        if isinstance(classification_dict, dict):
            classifications.append(ColumnClassification(**classification_dict))
        elif isinstance(classification_dict, ColumnClassification):
            classifications.append(classification_dict)

    return classifications


def build_classification_result(
    classifications: List[ColumnClassification],
    relations: List[RelationContext],
    grouping_context: GroupingContext,
    query_metadata: QueryMetadata,
) -> ColumnClassificationResult:
    """Build the final classification result from components.

    Args:
        classifications: Individual column classifications
        relations: Query relations
        grouping_context: Query grouping structure
        query_metadata: LLM-classified query-level metadata

    Returns:
        Complete ColumnClassificationResult
    """
    # Find primary key candidates from classifications
    primary_key_candidates = [
        c.column_alias
        for c in classifications
        if c.semantic_role in ("natural_key", "surrogate_key")
    ]

    # Check for surrogate keys
    has_surrogate_keys = any(
        c.semantic_role == "surrogate_key" for c in classifications
    )

    # Aggregate PII columns from individual classifications
    pii_columns = [c.column_alias for c in classifications if c.is_pii]
    high_risk_pii_count = sum(
        1 for c in classifications if c.is_pii and c.pii_confidence == "high"
    )

    return ColumnClassificationResult(
        classifications=classifications,
        fact_alias=query_metadata.fact_alias,
        intent=query_metadata.intent,
        primary_key_candidates=primary_key_candidates,
        has_surrogate_keys=has_surrogate_keys,
        pii_columns=pii_columns,
        high_risk_pii_count=high_risk_pii_count,
    )


def classify_columns(
    grouping_analysis: Dict[str, Any],
    relation_analysis: Dict[str, Any],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> ColumnClassificationResult:
    """Classify columns using LLM with row-by-row processing.

    Architecture:
    1. Each column is classified INDIVIDUALLY in its own LLM call
       (Fenic parallelizes these automatically)
    2. Query-level metadata (fact_alias, domain, intent) is classified
       in a SEPARATE LLM call using the column classifications as input

    This ensures:
    - Consistent processing time regardless of column count
    - No risk of output token overflow for large models
    - Better parallelization via Fenic's batch processing
    - LLM-powered query-level insights (not just heuristics)

    Args:
        grouping_analysis: Output from deterministic grouping pass
        relation_analysis: Output from deterministic relations pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro recommended for single column)
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        ColumnClassificationResult with classifications for each column
    """
    columns, relations, grouping_context = extract_classification_context(
        grouping_analysis, relation_analysis
    )

    if not columns:
        return ColumnClassificationResult(classifications=[])

    # Step 1: Explode columns into individual rows
    rows = explode_columns_for_classification(
        grouping_analysis, relation_analysis, model_id="single_model"
    )

    # Step 2: Create Polars DataFrame with explicit schema to avoid type inference issues
    # (empty lists like group_by: [] or sibling_columns: [] cause "cannot infer element type" errors)
    schema = get_classification_input_schema()
    polars_df = pl.DataFrame(rows, schema=schema)

    # Step 3: Convert to Fenic DataFrame
    df = session.create_dataframe(polars_df)

    # Step 4: Add classification column (Fenic parallelizes LLM calls)
    df = add_column_classification_column(df, model_size=model_size, use_examples=use_examples)

    # Step 5: Collect results and reassemble classifications
    results = df.to_pylist()
    classifications = reassemble_classifications(results)

    # Step 6: Classify query-level metadata using LLM (separate call)
    query_metadata = classify_query_metadata(
        classifications=classifications,
        relations=relations,
        grouping_context=grouping_context,
        session=session,
        model_size=model_size,
        use_examples=use_examples,
    )

    # Step 7: Build final result
    return build_classification_result(
        classifications=classifications,
        relations=relations,
        grouping_context=grouping_context,
        query_metadata=query_metadata,
    )


def classify_columns_batch(
    models_data: List[Dict[str, Any]],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> Dict[str, ColumnClassificationResult]:
    """Classify columns for multiple models in a single batched LLM call.

    This is more efficient than classify_columns() when processing many models,
    as it consolidates all columns from all models into a single Fenic batch.

    Architecture:
    1. Explode ALL columns from ALL models into one DataFrame
    2. Run one semantic.map() call (Fenic batches LLM requests)
    3. Group results back by model_id
    4. Run query metadata classification for each model

    Args:
        models_data: List of dicts with keys:
            - model_id: str
            - grouping_analysis: Dict from deterministic grouping pass
            - relation_analysis: Dict from deterministic relations pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro recommended)
        use_examples: Whether to use few-shot examples

    Returns:
        Dict mapping model_id -> ColumnClassificationResult
    """
    if not models_data:
        return {}

    # Step 1: Explode all columns from all models into rows
    all_rows: List[Dict[str, Any]] = []
    model_contexts: Dict[str, Dict[str, Any]] = {}  # Store context for reassembly

    for model_data in models_data:
        model_id = model_data["model_id"]
        grouping_analysis = model_data["grouping_analysis"]
        relation_analysis = model_data["relation_analysis"]

        # Extract context for this model
        columns, relations, grouping_context = extract_classification_context(
            grouping_analysis, relation_analysis
        )

        if not columns:
            continue

        # Store context for later reassembly
        model_contexts[model_id] = {
            "relations": relations,
            "grouping_context": grouping_context,
        }

        # Explode columns into rows with model_id for tracking
        rows = explode_columns_for_classification(
            grouping_analysis, relation_analysis, model_id=model_id
        )
        all_rows.extend(rows)

    if not all_rows:
        return {}

    # Step 2: Create single Polars DataFrame with explicit schema
    schema = get_classification_input_schema()
    polars_df = pl.DataFrame(all_rows, schema=schema)

    # Step 3: Convert to Fenic DataFrame and run classification (single batch)
    df = session.create_dataframe(polars_df)
    df = add_column_classification_column(df, model_size=model_size, use_examples=use_examples)

    # Step 4: Collect results and group by model_id
    results = df.to_pylist()

    # Group classified rows by model_id
    rows_by_model: Dict[str, List[Dict[str, Any]]] = {}
    for row in results:
        mid = row.get("model_id", "unknown")
        if mid not in rows_by_model:
            rows_by_model[mid] = []
        rows_by_model[mid].append(row)

    # Step 5: Reassemble column classifications for each model
    classifications_by_model: Dict[str, List[ColumnClassification]] = {}
    for model_id, model_rows in rows_by_model.items():
        if model_id not in model_contexts:
            continue
        classifications_by_model[model_id] = reassemble_classifications(model_rows)

    # Step 6: Batch query metadata classification for all models
    query_metadata_input = [
        {
            "model_id": model_id,
            "classifications": classifications_by_model[model_id],
            "relations": model_contexts[model_id]["relations"],
            "grouping_context": model_contexts[model_id]["grouping_context"],
        }
        for model_id in classifications_by_model
    ]

    query_metadata_by_model = classify_query_metadata_batch(
        query_metadata_input,
        session=session,
        model_size=model_size,
        use_examples=use_examples,
    )

    # Step 7: Build final classification results
    classification_results: Dict[str, ColumnClassificationResult] = {}
    for model_id, classifications in classifications_by_model.items():
        ctx = model_contexts[model_id]
        query_metadata = query_metadata_by_model.get(model_id, QueryMetadata())

        classification_results[model_id] = build_classification_result(
            classifications=classifications,
            relations=ctx["relations"],
            grouping_context=ctx["grouping_context"],
            query_metadata=query_metadata,
        )

    return classification_results
