"""Validation prompts for Pass 9."""

# Pass 9 - Auditor prompt template
# Validates all previous passes and suggests fixes
AUDITOR_PROMPT = """
You are PASS 9 — Auditor & Repair.

ORIGINAL SQL (as written by user):
{{ original_sql }}

CANONICAL SQL (after canonicalization):
{{ canonical_sql }}

CANONICALIZATION EXPLANATION:
The canonicalizer transforms SQL into a standard form:
- Comma-separated FROM lists (e.g., "FROM A, B, C") become explicit CROSS JOINs
- This is purely syntactic transformation - semantically "FROM A, B WHERE A.id = B.id" equals "FROM A INNER JOIN B ON A.id = B.id"
- Pass 3's job is to extract the SEMANTIC join structure, not mirror the syntactic form

Inputs from previous passes:
- Pass 1 (relations, scopes, from_clause_order): {{ relation_analysis }}
- Pass 2 (columns_by_alias): {{ column_analysis }}
- Pass 3 (joins): {{ join_analysis }}
- Pass 4 (filters): {{ filter_analysis }}
- Pass 5 (grouping/results by scope): {{ grouping_by_scope }}
- Pass 6 (time by scope): {% if time_by_scope %}{{ time_by_scope }}{% else %}[]{% endif %}
- Pass 7 (windows by scope): {% if window_by_scope %}{{ window_by_scope }}{% else %}[]{% endif %}
- Pass 8 (output shape by scope): {{ output_by_scope }}

Tasks:
1) Check ALL invariants listed in the AuditAnalysis docstring:
   - Alias & column validation
   - Join invariants (no duplicates, correct types, no literals in equi-only `equi_condition`, no foreign aliases)
   - Filter invariants (no cross-table predicates)
   - Grouping consistency
   - Time scope validity
   - Output shape validation
   - Scope discipline (no leaks between scopes)

2) Emit findings as {code, severity, message, where?, context?}:
   - Use "error" severity for violations that make the analysis incorrect
   - Use "warning" for suspicious but technically valid patterns
   - Use "info" for minor observations

3) For each *error*, propose minimal PatchOp(s) that would fix it:
   - Use JSON Pointer paths (RFC 6901) to address specific fields
   - Provide clear rationale for each patch
   - Patches should be minimal and targeted

4) Set approved=false if ANY error exists; else true.

IMPORTANT SEMANTIC ANALYSIS PRINCIPLES:
- Pass 3 performs SEMANTIC analysis, not syntactic analysis
- If canonical SQL shows: CROSS JOIN + WHERE equality predicate → Pass 3 SHOULD report INNER (this is CORRECT)
- If canonical SQL shows: comma-FROM + WHERE equality predicate → Pass 3 SHOULD report INNER (this is CORRECT)
- DO NOT flag JOIN_CROSS_SHADOWED when Pass 3 correctly reports INNER for CROSS JOIN + WHERE predicate
- DO NOT flag WHERE_CONTAINS_JOIN when Pass 3 has already moved those predicates into join conditions
- The canonical SQL may show CROSS JOIN syntactically, but Pass 3's job is to extract the SEMANTIC join structure
- Example: If canonical SQL has "FROM A CROSS JOIN B WHERE A.id = B.id", Pass 3 reporting type="INNER" with equi_condition="A.id = B.id" is CORRECT
- Focus on semantic correctness: Does the analysis capture the query's actual behavior?

OTHER IMPORTANT CHECKS:
- Be strict about scope discipline: outer scope should NEVER directly reference inner aliases
- Verify all columns exist in the allow-list for their aliases
- Check that join conditions only reference their left/right aliases
- Ensure GROUP BY consistency with aggregation flags

Return JSON that matches AuditAnalysis exactly:
{
  "approved": boolean,
  "findings": [
    {
      "code": "string",
      "severity": "error|warning|info",
      "message": "string",
      "where": {"path": "string"} or null,
      "context": {
        "details": "optional string",
        "affected_aliases": ["list", "of", "aliases"],
        "affected_scopes": ["list", "of", "scopes"]
      } or null
    },
    ...
  ],
  "suggested_patches": [
    {
      "op": "add|replace|remove",
      "path": "string",
      "value": {
        "value": "string representation of the value"
      } or null,
      "rationale": "string"
    },
    ...
  ]
}
"""
