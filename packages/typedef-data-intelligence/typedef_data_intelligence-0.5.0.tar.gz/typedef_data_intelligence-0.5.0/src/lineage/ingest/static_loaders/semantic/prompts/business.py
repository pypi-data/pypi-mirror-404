"""Business semantic prompts for Passes 10-10a."""

# Pass 10 - Business Semantics prompt template
# Extracts business meaning from technical analysis
BUSINESS_SEMANTICS_PROMPT = """
You are PASS 10 — Business Semantics (outer scope summary).

Inputs:
- Pass 1 (relations, scopes): {{ relation_analysis }}
- Pass 2 (columns_by_alias): {{ column_analysis }}
- Pass 3 (joins): {{ join_analysis }}
- Pass 4 (filters): {{ filter_analysis }}
- Pass 5 (grouping/result_grain for OUTER scope): {{ grouping_by_scope }}
- Pass 6 (time for OUTER scope): {{ time_by_scope }}
- Pass 8 (output shape for OUTER scope): {{ output_by_scope }}

Rules:
- IMPORTANT: Focus ONLY on the OUTER scope - find items where scope="outer" in the per-scope collections
- Use only identifiers from inputs; do not invent.

- **Measures** (aggregated metrics): Check BOTH approaches:
  a) Direct measures: From Pass5 grouping_by_scope outer scope, select items whose expr contains an aggregate function (SUM, COUNT, AVG, MIN, MAX)
  b) Also check the 'measures' list from Pass5 which contains aggregate expressions
  c) Inherited measures: If outer scope references a subquery, check that subquery's measures and track them as outer measures
  - Each measure MUST have an aggregation function (SUM, COUNT, AVG, MIN, MAX, COUNT_DISTINCT)
  - Example: {name: "total_revenue", expr: "SUM(revenue)", source_alias: "orders", default_agg: "SUM"}

- **Dimensions** (descriptive attributes for grouping/filtering):
  - From Pass5 grouping_by_scope outer scope, select items whose expr does NOT contain aggregate functions
  - Dimensions typically come from dimension tables (customers, products, stores, dates)
  - They are used to slice/dice data (e.g., customer_name, product_category, store_region, date)
  - Example: {name: "customer_name", source: "customers.name", pii: true}

- **Facts** (non-aggregated values from fact table):
  - Identify the central fact table alias from Pass1 relations (often named fct_*, fact_*, or contains 'sales', 'orders', 'transactions')
  - From Pass5 grouping_by_scope outer scope, find columns from the fact table that are:
    * Part of the grain (grain-defining): IDs, dates, timestamps that uniquely identify a row (e.g., order_id, transaction_date)
    * Factual measurements: Non-aggregated numeric values (e.g., unit_price, quantity, discount_amount)
  - Facts represent observations/events, NOT descriptive attributes
  - DO NOT include aggregated expressions (those are measures)
  - DO NOT include dimension table columns (those are dimensions)
  - Example: {name: "order_id", source: "orders.order_id", is_grain_defining: true}

- Grain: From Pass5 grouping_by_scope outer scope, set grain_keys=result_grain; grain_human = 'per ' + ' × '.join(humanized keys).
- Fact alias: Identify the central fact table (e.g., store_sales, fct_orders) - this is the table that contains the facts and measures
- Time: From Pass6 time_by_scope, find entry with scope="outer", use normalized_time_scope if available.
- Segments: from Pass4.where single-table predicates (exclude join-like). Create short snake_case names; rule verbatim.
- Intent heuristic: 
  • if is_aggregated=false and limit present => 'review_list'
  • if order_by contains measure and limit present => 'ranking'
  • if is_aggregated=true and multiple group_by => 'aggregation'
  • else 'unknown'
- PII: mark True for columns containing first_name, last_name, email, phone; False for clearly non-PII; null if unsure.
- ordering = From Pass8 output_by_scope, find entry with scope="outer", extract order_by expressions (just the expr field).
- limit = From Pass8 output_by_scope, find entry with scope="outer", extract limit value.

- **Domains** (multi-label business classification): Infer from table names, column patterns, and measure semantics.
  Valid domains: sales, finance, marketing, product, hr, operations, support
  Mapping hints:
  • sales: store_sales, orders, customers, transactions, deals, pipeline, revenue, bookings
  • finance: arr, mrr, billing, invoices, payments, accounting, fiscal, budget
  • marketing: campaigns, leads, conversions, attribution, channels, ads, impressions
  • product: usage, features, events, sessions, telemetry, active_users, dau, mau
  • hr: employees, payroll, hiring, headcount, staff, personnel
  • operations: inventory, shipping, logistics, supply_chain, warehouse, fulfillment
  • support: tickets, cases, sla, customer_service, incidents, issues
  A model can belong to multiple domains (e.g., ["sales", "finance"] for revenue reporting).
  If no clear domain signal, return empty list.

Return JSON matching BusinessSemantics.
"""

# Pass 10a - Grain Humanization prompt template
# Converts technical grain keys to human-readable format
GRAIN_HUMANIZATION_PROMPT = """
You are Pass 10a — Grain Humanization.

Inputs:
- result_grain (list of strings): {{ result_grain }}
- measure_names_to_drop (list of strings; case-insensitive): {{ measure_names }}

Rules you MUST follow:
1) Produce one GrainToken per result_grain entry (same order). Never add or remove entries.
2) Derive normalized_term ONLY from the input_expr using conservative edits:
   - strip alias/schema prefixes (foo.bar -> bar, c_last_name -> last_name)
   - unwrap simple function wrappers (e.g., SUBSTRING(col,...) -> col)
   - drop suffixes: _id, _sk, _number, _code, _key
   - collapse {first_name,last_name} to "customer", {c_first_name,c_last_name} to "customer"
   - rename: ticket_number->ticket, order_number->order, store_number->store
   - snake_case to words; lower-case
3) Mark is_measure=True and dropped=True ONLY if the input_expr (case-insensitive) matches any measure name to drop.
4) Keep dimension columns (dropped=False) unless they are measures or exact duplicates.
5) If a normalized_term already appears among non-dropped tokens, set dropped=True for the duplicate.
6) Build grain_human from NON-dropped tokens: "per " + " × ".join(normalized_term tokens).
7) If all tokens are dropped, set grain_human = "per row".
"""
