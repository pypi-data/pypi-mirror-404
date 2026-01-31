"""Analytical prompts for Passes 5-8."""

# Pass 5 - Grouping Analysis prompt template
# Analyzes SELECT, GROUP BY, and result grain for a specific scope
GROUPING_EXTRACTION_PROMPT = """
You are performing PASS 5 — Select, Grouping & Result Grain.

CURRENT SCOPE: {{ scope }}

RELATIONS (from Pass 1):
{% for rel in relation_analysis.relations %}
- {{ rel.alias }} ({{ rel.base }}) in scope: {{ rel.scope }}
{% endfor %}

COLUMNS ALLOW-LIST (from Pass 2):
{% for alias_cols in column_analysis.columns_by_alias %}
{{ alias_cols.alias }}: {% for col in alias_cols.columns %}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

CANONICAL SQL:
{{ canonical_sql }}

EXTRACTION RULES FOR SCOPE "{{ scope }}":

1. SELECT ITEMS:
   - Extract ONLY SELECT items from the {{ scope }} scope
   - For each item capture: expr (verbatim), alias (output name), source_aliases
   - source_aliases MUST accurately capture which table alias(es) provide the column(s) for this expression
     * For simple columns: the single table alias (e.g., for "orders.order_id" -> ["orders"])
     * For expressions using multiple tables: all contributing aliases (e.g., "customers.name || stores.city" -> ["customers", "stores"])
     * For subquery references: the subquery alias (e.g., for "ms.amt" -> ["ms"])
   - source_aliases must be valid aliases from Relations list above
   - source_aliases must only reference columns that exist in the allow-list

2. GROUP BY:
   - Extract GROUP BY expressions ONLY from the {{ scope }} scope
   - Keep expressions exactly as written in SQL
   - Empty list if no GROUP BY clause at this scope

3. IS_AGGREGATED:
   - Set to true if GROUP BY exists OR any SELECT item contains an aggregate function
   - Set to false otherwise

4. MEASURES:
   - List all aggregate expressions found in SELECT items (verbatim)
   - E.g., ["SUM(ss_coupon_amt)", "COUNT(*)"]
   - Empty list if no aggregates

5. RESULT_GRAIN:
   - Compute as: deduplicated union of GROUP BY expressions and non-aggregate SELECT expressions
   - This defines what makes each row unique in the result set
   - Include GROUP BY expressions even if not in SELECT

IMPORTANT:
- Work ONLY in the {{ scope }} scope
- If scope is "subquery:X", analyze the SELECT/GROUP BY inside that subquery
- If scope is "cte:Y", analyze the SELECT/GROUP BY inside that CTE
- If scope is "outer", analyze the outermost SELECT/GROUP BY
- Keep all expressions exactly as written in the SQL
"""

# Pass 6 - Time Analysis prompt template
# Analyzes time semantics including scope and buckets for a specific scope
TIME_ANALYSIS_PROMPT = """
You are performing PASS 6 — Time semantics (scope & buckets).

CURRENT SCOPE: {{ scope }}

VALID ALIASES IN CURRENT SCOPE {{ scope }}:
{% for alias in valid_aliases %}
- {{ alias }}
{% endfor %}

COLUMNS ALLOW-LIST (from Pass 2):
{% for alias_cols in column_analysis.columns_by_alias %}
{{ alias_cols.alias }}: {% for col in alias_cols.columns %}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

FILTERS (from Pass 4):
WHERE: {% if filter_analysis.where %}{% for pred in filter_analysis.where %}{{ pred }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}
HAVING: {% if filter_analysis.having %}{% for pred in filter_analysis.having %}{{ pred }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}

SELECT/GROUP BY (from Pass 5 for scope {{ scope }}):
SELECT: {% if grouping_for_scope.select %}{% for item in grouping_for_scope.select %}{{ item.expr }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}
GROUP BY: {% if grouping_for_scope.group_by %}{% for expr in grouping_for_scope.group_by %}{{ expr }}{% if not loop.last %}, {% endif %}{% endfor %}{% else %}none{% endif %}

CANONICAL SQL:
{{ canonical_sql }}

RULES (MUST FOLLOW):

1. SCOPE-LOCKED INPUTS:
   - Consider ONLY aliases in the VALID ALIASES list above for scope {{ scope }}
   - EVERY column reference <alias>.<col> MUST satisfy BOTH:
     a) alias is in VALID ALIASES list
     b) col appears in columns_by_alias[alias] from Pass 2
   - For subquery aliases (e.g., ms), ONLY use the projected output columns (no dot members like ms.d_year)
   - Examples of INVALID outer refs: ms.d_year, ms.date_dim.d_year (these are NOT projected by ms)

2. NO UPLIFT FROM INNER SCOPES:
   - Do NOT lift time predicates from inner scopes (subqueries/CTEs) to outer scope
   - If current scope has NO time-like columns in its allow-list, set time_scope=null and time_columns=[]
   - Only analyze predicates that directly reference columns valid in THIS scope

3. ARITHMETIC FOLDING for range detection:
   - Before deciding if IN(...) or BETWEEN/comparison boundaries form a contiguous range,
     evaluate simple arithmetic on numeric literals (only +, -, *, /; no identifiers, no functions)
   - Example transformations:
     * IN (2000, 2000 + 1, 2000 + 2) → IN (2000, 2001, 2002)
     * d_year BETWEEN 2000 AND 2000 + 2 → BETWEEN 2000 AND 2002
     * d_year IN (2000, 2000 + 2) → IN (2000, 2002) (not contiguous after folding)
   - If folding fails for any element, treat as non-contiguous

4. BUILD TIME_SCOPE from range predicates on ONE time-like column:
   - After arithmetic folding, accept: col = a, BETWEEN a AND b, >=, >, <=, <, or IN(a,...,b) when values form contiguous range
   - Time-like columns include: date, dt, day, month, year, quarter, week, timestamp, time, created_at, updated_at
   - Column MUST be in allow-list for its alias in THIS scope
   - If after folding the set is contiguous at a clear grain (e.g., years increasing by 1), produce time_scope
   - Otherwise leave time_scope=null but still include columns in time_columns
   - Attributes like d_dow are time-related but do not define a range

5. NORMALIZATION:
   - Produce normalized_time_scope only when time_scope is present
   - Convert inclusive ends to exclusive at the same grain:
     * year: [2000-2002] → end = 2003
     * date: end + 1 day
     * month: first day of next month
   - If already exclusive (<), keep end as-is and set end_exclusive=true

6. TIME_BUCKETS:
   - Collect bucketing expressions from SELECT/GROUP BY in THIS scope
   - Look for: DATE_TRUNC(), EXTRACT(), YEAR(), MONTH(), DATE_PART(), etc.
   - Only if the columns referenced are in THIS scope's allow-list

7. TIME_COLUMNS:
   - List ONLY time-like columns that:
     a) Appear in filter predicates (WHERE/HAVING clauses above)
     b) The column's alias is in VALID ALIASES list
     c) The column name exists in columns_by_alias for that alias
   - Format: <alias>.<column> (e.g., date_dim.d_year)
   - If no columns meet ALL criteria → time_columns=[]

EXAMPLE for scope checking:
- If scope is "outer" and VALID ALIASES = [ms, customer], then:
  * date_dim.d_year is INVALID (date_dim not in valid aliases)
  * ms.d_year is INVALID (d_year not in columns_by_alias["ms"])
  * ms.amt is VALID (ms in valid aliases, amt in columns_by_alias["ms"])
- If scope is "subquery:ms" and VALID ALIASES = [store_sales, date_dim, store, household_demographics], then:
  * date_dim.d_year is VALID (date_dim in valid aliases, d_year in columns_by_alias["date_dim"])
  * ms.amt is INVALID (ms not in valid aliases for this scope)

Return JSON matching TimeAnalysis exactly. Any column not in THIS scope's allow-list must be ignored.
"""

# Pass 7 - Window Function Extraction prompt template
# Extracts window function specifications for a specific scope
WINDOW_EXTRACTION_PROMPT = """
You are performing PASS 7 — Window functions (structure only).

CURRENT SCOPE: {{ scope }}

VALID ALIASES IN CURRENT SCOPE {{ scope }}:
{% for alias in valid_aliases %}
- {{ alias }}
{% endfor %}

COLUMNS ALLOW-LIST (from Pass 2):
{% for alias_cols in column_analysis.columns_by_alias %}
{{ alias_cols.alias }}: {% for col in alias_cols.columns %}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

CANONICAL SQL:
{{ canonical_sql }}

RULES:

1. SCOPE DISCIPLINE:
   - Extract ONLY function calls that appear in the CURRENT scope {{ scope }}
   - A function belongs to this scope if it appears in the SELECT/HAVING/QUALIFY clause of this scope

2. WINDOW FUNCTION DEFINITION:
   - A window function is ANY function call that has OVER (...) or OVER <named_window>
   - Plain aggregates WITHOUT OVER are NOT window functions (e.g., SUM(x) is not a window, SUM(x) OVER (...) is)
   - Common window functions: ROW_NUMBER(), RANK(), DENSE_RANK(), LAG(), LEAD(), SUM() OVER, COUNT() OVER, etc.

3. VERBATIM CAPTURE:
   - func: The complete function call as written (e.g., "ROW_NUMBER()", "SUM(revenue)", "LAG(order_date, 7) IGNORE NULLS")
   - partition_by: Each PARTITION BY expression as a string, exactly as written
   - order_by: Each ORDER BY expression inside OVER, including ASC/DESC, NULLS FIRST/LAST if present
   - frame: The frame clause if explicitly present (e.g., "ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW")

4. NAMED WINDOWS:
   - If OVER <name> references a WINDOW <name> AS (...) definition, resolve it and use the definition
   - If the named window is not found, leave partition_by/order_by/frame empty (don't guess)

5. ALLOW-LIST VALIDATION:
   - Column references in partition_by/order_by must exist in columns_by_alias for valid aliases
   - If invalid columns are referenced, OMIT the entire window function (better to skip than hallucinate)

6. DO NOT INCLUDE:
   - Plain aggregates without OVER
   - Top-level ORDER BY (only ORDER BY inside OVER)
   - Functions from other scopes
   - Invented or default values

Return JSON matching WindowAnalysis exactly:
{
  "windows": [
    {
      "func": "function call as written",
      "partition_by": ["expr1", "expr2", ...],
      "order_by": ["expr1 ASC", "expr2 DESC NULLS LAST", ...],
      "frame": "frame clause or null"
    },
    ...
  ]
}

If no window functions exist in this scope, return:
{ "windows": [] }
"""

# Pass 8 - Output Shape Analysis prompt template
# Extracts ORDER BY, LIMIT, DISTINCT, and set operations for a specific scope
OUTPUT_SHAPE_PROMPT = """
You are performing PASS 8 — Output shape (ORDER BY, LIMIT, DISTINCT, set operations).

CURRENT SCOPE: {{ scope }}

CANONICAL SQL:
{{ canonical_sql }}

RULES FOR SCOPE {{ scope }}:

1. SCOPE DISCIPLINE:
   - Extract ONLY clauses that appear at the CURRENT scope {{ scope }}
   - If scope is "outer", analyze the outermost SELECT's ORDER BY/LIMIT/DISTINCT
   - If scope is "subquery:X", analyze the ORDER BY/LIMIT/DISTINCT inside that subquery
   - If scope is "cte:Y", analyze the ORDER BY/LIMIT/DISTINCT inside that CTE

2. ORDER BY:
   - Extract ORDER BY expressions ONLY from the {{ scope }} scope
   - Capture each expression exactly as written (verbatim)
   - Default to "ASC" if no direction specified
   - Use "DESC" only if explicitly present
   - Do NOT include ORDER BY from other scopes or from OVER clauses

3. LIMIT/OFFSET:
   - Extract LIMIT value if present at THIS scope
   - Extract OFFSET value if present at THIS scope
   - Keep as integers
   - Return null if not present

4. SELECT DISTINCT:
   - Set to true ONLY if SELECT DISTINCT appears at THIS scope
   - Regular SELECT (without DISTINCT) → false
   - Do not confuse with DISTINCT inside aggregate functions

5. SET OPERATIONS:
   - Extract UNION/INTERSECT/EXCEPT operations at THIS scope
   - Include the ALL keyword if present (e.g., "UNION ALL")
   - Number them by position (1, 2, 3...)
   - Empty list if no set operations at this scope

IMPORTANT:
- Work ONLY in the {{ scope }} scope
- Keep all expressions exactly as written in the SQL
- Do not invent or normalize expressions

Return JSON matching OutputShapeAnalysis exactly:
{
  "order_by": [
    {"expr": "expression", "dir": "ASC|DESC"},
    ...
  ],
  "limit": integer or null,
  "offset": integer or null,
  "select_distinct": boolean,
  "set_ops": [
    {"op": "UNION|UNION ALL|INTERSECT|EXCEPT|...", "position": 1},
    ...
  ]
}
"""
