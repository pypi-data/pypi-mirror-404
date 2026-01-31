"""Business semantic models for Passes 10-10a."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Valid business domains for multi-domain classification
VALID_DOMAINS = [
    "sales",  # Orders, revenue, customers, transactions, deals, pipeline
    "finance",  # ARR, MRR, billing, invoices, payments, accounting
    "marketing",  # Campaigns, leads, conversions, attribution, channels
    "product",  # Usage, features, events, sessions, telemetry
    "hr",  # Employees, payroll, hiring, headcount
    "operations",  # Inventory, shipping, logistics, supply chain
    "support",  # Tickets, cases, SLAs, customer service
]

# Domain inference patterns (table/column name substrings → domains)
DOMAIN_PATTERNS: dict[str, list[str]] = {
    "sales": [
        "store_sales", "orders", "order", "customer", "transaction", "deal",
        "pipeline", "revenue", "booking", "sales", "purchase", "buyer",
        "seller", "cart", "checkout", "payment",
    ],
    "finance": [
        "arr", "mrr", "billing", "invoice", "payment", "accounting",
        "fiscal", "budget", "expense", "cost", "profit", "margin",
        "ledger", "journal", "receivable", "payable", "tax",
    ],
    "marketing": [
        "campaign", "lead", "conversion", "attribution", "channel", "ad",
        "impression", "click", "utm", "funnel", "audience", "segment",
        "email", "newsletter", "promotion",
    ],
    "product": [
        "usage", "feature", "event", "session", "telemetry", "active_user",
        "dau", "mau", "wau", "retention", "engagement", "pageview",
        "action", "behavior", "activity", "login", "signup",
    ],
    "hr": [
        "employee", "payroll", "hiring", "headcount", "staff", "personnel",
        "salary", "compensation", "benefit", "leave", "attendance",
        "performance", "review", "candidate", "applicant",
    ],
    "operations": [
        "inventory", "shipping", "logistics", "supply_chain", "warehouse",
        "fulfillment", "shipment", "delivery", "stock", "sku", "vendor",
        "supplier", "procurement",
    ],
    "support": [
        "ticket", "case", "sla", "customer_service", "incident", "issue",
        "help_desk", "support", "escalation", "resolution", "feedback",
        "complaint", "nps", "csat",
    ],
}


def infer_domains_heuristic(
    table_names: list[str],
    column_names: list[str],
) -> list[str]:
    """Infer business domains from table and column names using pattern matching.

    This provides a heuristic fallback when LLM inference is unavailable.

    Args:
        table_names: List of table/relation names in the query
        column_names: List of column names in the query

    Returns:
        List of inferred domain names (may be empty if no patterns match)
    """
    # Combine and lowercase all names for matching
    all_names = [n.lower() for n in table_names + column_names]
    all_text = " ".join(all_names)

    matched_domains: set[str] = set()

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern in all_text:
                matched_domains.add(domain)
                break  # One match per domain is enough

    return sorted(matched_domains)

# Pass 10: Business Semantics Models


class BusinessMeasure(BaseModel):
    """A business measure extracted from the query."""

    name: str = Field(
        description="Raw SQL column name (the SELECT alias), NOT a display name. "
        "Must match actual column references in SQL for agent cross-referencing. "
        "Examples: 'total_revenue', 'customer_count', 'avg_order_value'."
    )
    expr: str = Field(
        description="Exact aggregate expression as written (e.g., 'SUM(ss_net_profit)')."
    )
    source_alias: str = Field(
        description="Alias providing the raw column(s) for this measure (from Pass 5 source_aliases)."
    )
    default_agg: Literal[
        "SUM", "COUNT", "AVG", "MIN", "MAX", "COUNT_DISTINCT", "OTHER"
    ] = Field(
        description="Aggregation implied by expr (e.g., 'SUM' for SUM(...); 'COUNT_DISTINCT' for COUNT(DISTINCT ...); 'OTHER' if not one of these)."
    )


class BusinessDimension(BaseModel):
    """A business dimension extracted from the query."""

    name: str = Field(
        description="Raw SQL column name (the SELECT alias), NOT a display name. "
        "Must match actual column references in SQL for agent cross-referencing. "
        "Examples: 'customer_id', 's_city', 'product_category'."
    )
    source: str = Field(
        description="Fully-qualified source in this scope: <alias>.<column> or a verbatim expression used in SELECT (e.g., 'SUBSTRING(s_city, 1, 30)')."
    )
    pii: bool = Field(
        default=False,
        description="True if clearly personally identifiable (name, email, phone); False if clearly not; null if uncertain.",
    )


class BusinessFact(BaseModel):
    """A business fact extracted from the query.

    Facts are non-aggregated numeric or date columns from fact tables that represent
    observations or events (e.g., order_id, transaction_date, unit_price).
    They are typically part of the grain but are NOT dimensions used for grouping.
    """

    name: str = Field(
        description="Raw SQL column name (the SELECT alias), NOT a display name. "
        "Must match actual column references in SQL for agent cross-referencing. "
        "Examples: 'order_id', 'transaction_date', 'unit_price'."
    )
    source: str = Field(
        description="Fully-qualified source in this scope: <alias>.<column> (e.g., 'orders.order_id')."
    )
    is_grain_defining: bool = Field(
        default=True,
        description="True if this fact is part of the grain (e.g., order_id). False for other factual attributes.",
    )


class SegmentRule(BaseModel):
    """A business segment/filter rule."""

    name: str = Field(
        description="Short snake_case label derived from the predicate meaning (e.g., 'large_household', 'medium_staffed_store')."
    )
    rule: str = Field(
        description="Verbatim single-table predicate from Pass 4 WHERE/HAVING (no joins)."
    )


class BusinessTimeWindow(BaseModel):
    """Time window information for the query."""

    column: Optional[str] = Field(
        default=None,
        description="Qualified time column for the OUTER scope if present; else null. Use Pass 6 normalized scope if available.",
    )
    start: Optional[str] = Field(default=None, description="Start of time range")
    end: Optional[str] = Field(default=None, description="End of time range")
    end_exclusive: bool = Field(
        default=False, description="Whether end is exclusive"
    )
    attributes: List[str] = Field(
        default_factory=list,
        description="Other time-related attributes used as filters (e.g., d_dow), verbatim and qualified.",
    )


class BusinessSemantics(BaseModel):
    """Business Semantics Analysis (derived from Passes 1–8, outer scope focus).

    DESIGN DECISION: OUTER SCOPE ONLY
    ---------------------------------
    BusinessSemantics intentionally describes only the OUTER (final) scope of a query,
    not intermediate CTEs or subqueries. This is by design, not a gap:

    1. **Consumer-focused**: Agents and catalogs care about what the model *delivers*
       (final output grain, measures, dimensions), not internal implementation details.

    2. **CTE/subquery agnostic**: CTEs are implementation details that may be refactored
       without changing the model's business semantics. A model that computes revenue
       via CTE vs inline subquery has identical business meaning.

    3. **Technical analysis covers internals**: The `grouping_by_scope`, `window_by_scope`,
       and other `*_by_scope` dicts in technical passes capture per-scope computation
       details for those who need them (e.g., debugging, optimization).

    4. **Simpler mental model**: Users asking "what does this model produce?" get a
       clear answer without wading through intermediate computation scopes.

    For per-scope technical details, use the GroupingAnalysis and other technical models
    which support multi-scope analysis via `grouping_by_scope["cte:name"]` etc.

    Inputs you MUST use (provided in the prompt together with canonical_sql):
      • Pass 1: relations (aliases, scopes), from_clause_order
      • Pass 2: columns_by_alias (allow-list)
      • Pass 3: joins (JoinClause[])
      • Pass 4: filters (WHERE/HAVING)  — single-table/literal predicates only
      • Pass 5: select/grouping/result_grain  — measures vs dimensions, result_grain
      • Pass 6: time (time_scope, normalized_time_scope, time_columns)
      • Pass 8: output shape (order_by, limit, select_distinct)

    Guardrails:
      • Use ONLY identifiers discovered in earlier passes; do not invent tables/columns.

      • **Measures** (aggregated metrics): From Pass 5 'select' items whose expr contains aggregate functions
        - Also use Pass 5 'measures' list which contains aggregate expressions
        - Must contain aggregation function (SUM, COUNT, AVG, MIN, MAX, COUNT_DISTINCT)
        - Examples: SUM(revenue), COUNT(DISTINCT customer_id), AVG(order_value)

      • **Dimensions** (descriptive attributes): From Pass 5 'select' items whose expr does NOT contain aggregate functions
        - Typically from dimension tables (customers, products, stores, dates)
        - Used for grouping/filtering (e.g., customer_name, product_category, region)
        - Do NOT include fact table IDs/dates (those are facts)

      • **Facts** (non-aggregated observations): From fact table columns in Pass 5 'select'
        - Grain-defining: IDs, dates that uniquely identify rows (order_id, transaction_date)
        - Measurements: Non-aggregated numeric values (unit_price, quantity, discount)
        - Must come from the central fact table, NOT dimension tables
        - Examples: order_id (grain-defining), unit_price (measurement)

      • Grain text should be a short human string derived from Pass 5 'result_grain' (e.g., 'per ticket × customer × city').
      • Fact alias: pick the alias of the central fact table (often fct_*, fact_*, or contains 'sales'/'orders'/'transactions')
      • Time window: prefer Pass 6 normalized_time_scope (if in outer scope), else null. Attributes = Pass 6 time_columns (outer scope).
      • Segments: derive from Pass 4 WHERE single-table predicates that read like business slices (e.g., ranges/IN/equalities). Keep rule verbatim.
      • PII: set True for obvious identifiers (e.g., columns named like first_name, last_name, email, phone); False for non-PII; null if unsure.
      • Intent: infer from ordering/limit + aggregation (e.g., 'review_list', 'ranking', 'comparison'); if ambiguous, use 'unknown'.
      • Do NOT restate business logic beyond what prior passes reveal; this pass is a compact summary for agents/UI.

    Output is a single object summarizing the OUTER scope.
    """

    fact_alias: Optional[str] = Field(
        default=None,
        description="Alias most responsible for measures (often the fact table alias). Null if unclear.",
    )
    grain_human: str = Field(
        description="Short human-readable grain derived from Pass 5 result_grain (e.g., 'per ticket × customer × city')."
    )
    grain_keys: List[str] = Field(
        default_factory=list,
        description="Verbatim expressions that define the grain (Pass 5 result_grain).",
    )
    measures: List[BusinessMeasure] = Field(
        default_factory=list, description="Business measures."
    )
    dimensions: List[BusinessDimension] = Field(
        default_factory=list, description="Business dimensions."
    )
    facts: List[BusinessFact] = Field(
        default_factory=list, description="Business facts from the fact table."
    )
    time: BusinessTimeWindow = Field(
        default_factory=BusinessTimeWindow, description="Time window & attributes."
    )
    segments: List[SegmentRule] = Field(
        default_factory=list, description="Named business slices derived from filters."
    )
    intent: Literal[
        "review_list", "ranking", "comparison", "aggregation", "time_series", "snapshot", "unknown"
    ] = Field(description="High-level intent inferred from grouping/ordering/limit.")
    ordering: List[str] = Field(
        default_factory=list,
        description="ORDER BY expressions in the outer scope, verbatim.",
    )
    limit: Optional[int] = Field(
        default=None, description="LIMIT in the outer scope if present."
    )
    pii_columns: List[str] = Field(
        default_factory=list, description="Qualified columns flagged as PII."
    )
    domains: List[
        Literal[
            "sales", "finance", "marketing", "product", "hr", "operations", "support"
        ]
    ] = Field(
        default_factory=list,
        description=(
            "Business domains this query relates to (multi-label). "
            "Infer from table names, column patterns, and measure semantics. "
            "E.g., store_sales→sales; arr/mrr→finance; campaigns→marketing. "
            "A model can belong to multiple domains (e.g., sales+finance for revenue reporting)."
        ),
    )


# Pass 10a: Grain Humanization Models


class GrainToken(BaseModel):
    """A token representing one element of the grain."""

    input_expr: str = Field(description="One verbatim entry from result_grain")
    normalized_term: str = Field(
        description="Short human token derived ONLY from input_expr (e.g., 'ss_ticket_number' -> 'ticket', 'store.s_city' -> 'city')."
    )
    is_measure: bool = Field(
        description="True if this token matches a measure alias/name you were told to drop."
    )
    dropped: bool = Field(
        description="True if token should be excluded from the final phrase (e.g., because it is a measure)."
    )


class GrainHumanization(BaseModel):
    """Grain Humanization Analysis - converts result grain into a human-readable phrase like 'per ticket × customer × city'.

    Guardrails:
      • Use ONLY the provided result_grain strings; do not invent entities.
      • For each result_grain item, output exactly one GrainToken with a normalized_term.
      • You may use light, generic normalization: drop schema/alias prefixes, trim suffixes like _id/_sk,
        map common name parts (first_name/last_name -> 'customer'), and unwrap simple functions like SUBSTRING(col,...)->col.
      • Mark tokens that are measures (provided separately) as dropped=True.
      • The final phrase is built from NON-dropped tokens, in order, lower-cased, joined by ' × ', prefixed by 'per '.
      • If nothing remains, return 'per row'.
    """

    grain_human: str = Field(
        description="The final human phrase, e.g., 'per ticket × customer × city'."
    )
    tokens: List[GrainToken] = Field(
        description="Aligned mapping from result_grain to normalized tokens."
    )
