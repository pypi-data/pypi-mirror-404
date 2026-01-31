"""Technical analysis prompts for Passes 1-4."""

# Pass 1 - Relation Analysis (no prompt needed - uses semantic.extract directly)

# Pass 2 - Column Analysis (no prompt needed - uses semantic.extract directly)

# Pass 3 - Join Edge Analysis prompt template
# Uses relation_analysis and column_analysis from previous passes
JOIN_EDGE_EXTRACTION_PROMPT = """
You are performing Join Edge Extraction using constrained inputs from previous analyses.

RELATIONS (from Relation Analysis):
{% for rel in relation_analysis.relations %}
- {{ rel.alias }} ({{ rel.base }}) in scope: {{ rel.scope }}
{% endfor %}

FROM CLAUSE ORDER (outer scope):
{% for alias in relation_analysis.from_clause_order %}
- {{ alias }}
{% endfor %}

COLUMNS ALLOW-LIST (from Column Analysis):
{% for alias_cols in column_analysis.columns_by_alias %}
{{ alias_cols.alias }}: {% for col in alias_cols.columns %}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

CANONICAL SQL:
{{ canonical_sql }}

EXTRACTION RULES:
1. ONE edge per unordered pair (A,B). If multiple equi-predicates link the pair, AND them in one equi_condition.
2. Precedence: explicit LEFT/RIGHT/FULL > INNER (if any column-to-column predicate exists) > CROSS (only if no predicates exist).
3. equi_condition: ONLY column-to-column predicates between LEFT and RIGHT, fully qualified using the allow-list. No literals/IN/BETWEEN/IS NULL/etc.
4. raw_condition: the full predicate expression between LEFT and RIGHT (no ON/USING keyword):
   - This MAY include functions, literals, OR, BETWEEN, ranges, etc.
   - It can come from ON/USING, or from WHERE in comma-join / CROSS JOIN + WHERE style queries.
   - raw_condition MUST reference only the LEFT and RIGHT aliases (no third-alias leakage).
   - For USING joins, you may represent it as explicit equality predicates (e.g., "a.id = b.id").
   - For CROSS joins, raw_condition MUST be empty.

   EXAMPLE: For a join with predicate "a.id = b.id AND a.date BETWEEN b.start AND b.end":
   - equi_condition: "a.id = b.id" (equi-join only, no BETWEEN)
   - raw_condition: "a.id = b.id AND a.date BETWEEN b.start AND b.end" (full predicate)

5. Side ordering: LEFT = alias appearing earlier in from_clause_order; RIGHT = the other.
6. Normalization/effective_type:
   - INNER: effective_type="INNER", normalized_equi_condition==equi_condition, normalized_raw_condition==raw_condition
   - OUTER: effective_type becomes "INNER" only if null-killing predicate exists; push it into BOTH normalized_equi_condition and normalized_raw_condition
   - CROSS: equi_condition="", raw_condition="", effective_type="CROSS"
7. Scope discipline: inside subqueries/CTEs, only use aliases valid in that scope.

IMPORTANT:
- Do NOT include the same pair twice
- Do NOT emit CROSS for a pair that has ANY column-to-column predicate
- Use ONLY columns from the allow-list above
- Fully qualify all columns as alias.column

Extract the join edges following these rules strictly.
"""

# Pass 4 - Filter Analysis prompt template
# Uses all previous passes to constrain filter extraction
FILTER_EXTRACTION_PROMPT = """
You are performing PASS 4 — Filter Extraction by clause.

RELATIONS (from Pass 1):
{% for rel in relation_analysis.relations %}
- {{ rel.alias }} ({{ rel.base }}) in scope: {{ rel.scope }}
{% endfor %}

COLUMNS ALLOW-LIST (from Pass 2):
{% for alias_cols in column_analysis.columns_by_alias %}
{{ alias_cols.alias }}: {% for col in alias_cols.columns %}{{ col }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

JOINS (from Pass 3 - these predicates should NOT appear in filters):
{% for join in join_analysis.joins %}
- {{ join.left }} {{ join.type }} JOIN {{ join.right }}
  Equi condition: {{ join.equi_condition }}
  Effective type: {{ join.effective_type }}
{% endfor %}

CANONICAL SQL:
{{ canonical_sql }}

EXTRACTION RULES:
1. SINGLE-TABLE ONLY: Include only predicates that reference columns from a SINGLE alias (or literal-only predicates).
2. ALLOW-LIST VALIDATION: Every column must appear in the allow-list for its alias. If unqualified and uniquely resolvable, qualify it; else add to unresolved_predicates.
3. JOIN EXCLUSION: Do NOT include any column=column predicates that appear in the JOINS section above. Those belong to joins, not filters.
4. CLAUSE FIDELITY: Keep predicates in their original clause:
   - WHERE: row-level filters before aggregation
   - HAVING: filters on aggregated values
   - QUALIFY: filters on window functions
5. NULL-KILLING DETECTION: For each OUTER join from Pass 3:
   - LEFT join (left preserved): any WHERE predicate on the right alias → add to null_killing_on_outer
   - RIGHT join (right preserved): any WHERE predicate on the left alias → add to null_killing_on_outer
   - FULL join: WHERE predicates on either side → add to null_killing_on_outer
6. PRESERVE SQL: Keep predicates verbatim (preserve parentheses, OR groups). Only normalize whitespace.

IMPORTANT EXCLUSIONS:
- Exclude predicates that reference ≥2 aliases (they're likely join conditions)
- Exclude predicates already listed in JOINS above
- Exclude predicates with columns not in the allow-list

Extract filters following these rules strictly. Return predicates grouped by clause.
"""
