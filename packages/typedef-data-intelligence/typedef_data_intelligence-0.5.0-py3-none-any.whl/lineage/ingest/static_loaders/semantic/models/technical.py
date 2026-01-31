"""Technical analysis models for Passes 1-4."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from .base import Evidence

# Pass 1: Relation Analysis Models


class RelationUse(BaseModel):
    """One occurrence of a relation in the query, with scope tracking."""

    alias: str = Field(
        description=(
            "Alias exactly as used in SQL (e.g., 'ss', 'd1', 'ms'). "
            "If no alias was provided, use the base name (e.g., 'store_sales'). "
            "MUST be unique among all relations."
        )
    )
    base: str = Field(
        description=(
            "Underlying relation identifier as written (no alias). "
            "Examples: 'store_sales', 'date_dim', 'sales.customer', 'cs_ui' (CTE name), "
            "'<subquery>' for subqueries."
        )
    )
    kind: Literal["table", "view", "cte", "subquery", "table_function"] = Field(
        description=(
            "Relation kind inferred from context: "
            "'table'/'view' for physical objects; 'cte' for WITH-named relations; "
            "'subquery' for an inline SELECT with an alias; "
            "'table_function' for function-in-FROM (e.g., UNNEST). "
            "If uncertain, prefer 'table' vs 'cte' based on presence in WITH."
        )
    )
    scope: str = Field(
        description=(
            "Scope label for where this alias lives:\n"
            "- 'outer'              → alias is in the OUTERMOST query's FROM/JOIN list (e.g., 'ms', 'customer').\n"
            "- 'subquery:<alias>'   → alias appears INSIDE the subquery identified by <alias> (e.g., "
            " 'subquery:ms' for tables used inside ( ... ) AS ms ). Use only the nearest enclosing subquery alias.\n"
            "- 'cte:<name>'         → alias appears inside the CTE body named <name> (e.g., 'cte:cs_ui').\n"
            "Rules:\n"
            "• Choose EXACTLY ONE scope per relation occurrence.\n"
            "• For nested subqueries, use the nearest enclosing subquery alias (do NOT create dotted paths).\n"
            "• If you cannot determine the scope confidently, OMIT the relation rather than guessing."
        )
    )
    catalog: Optional[str] = Field(
        None,
        description="Catalog/database if explicitly qualified in SQL (e.g., 'db1'); else null.",
    )
    schema_name: Optional[str] = Field(
        None,
        description="Schema if explicitly qualified in SQL (e.g., 'public'); else null.",
    )
    is_temp: bool = Field(
        False,
        description="True if a temp/transient relation is clearly indicated by the SQL;",
    )
    evidence: List[Evidence] = Field(
        default_factory=list,
        description="Offsets into canonical_sql where this alias/base appears. Optional.",
    )


class AliasMapping(BaseModel):
    """Single alias to base mapping entry (Fenic-compatible)."""

    alias: str = Field(description="The alias used in SQL")
    base: str = Field(description="The base relation name")


class SelfJoinGroup(BaseModel):
    """Group of aliases that reference the same base relation (Fenic-compatible)."""

    base: str = Field(description="The base relation name")
    aliases: List[str] = Field(
        description="List of distinct aliases referencing this base"
    )


class RelationAnalysis(BaseModel):
    """Analysis of relations & aliases in the SQL query.

    Fenic-compatible version using Lists instead of Dicts.
    """

    relations: List[RelationUse] = Field(
        default_factory=list,
        description=(
            "Every relation occurrence with its alias and scope. "
            "Include tables/views referenced in FROM, CTEs referenced in the query body, "
            "subqueries (as alias only), and table functions. "
            "Each 'alias' must be unique."
        ),
    )

    alias_mappings: List[AliasMapping] = Field(
        default_factory=list,
        description=(
            "List of alias to base relation mappings. "
            "For subqueries, map alias to '<subquery>'. For CTEs, map alias to the CTE name."
        ),
    )

    driving_relations: List[str] = Field(
        default_factory=list,
        description=(
            "Aliases from the OUTERMOST FROM clause in left-to-right order "
            "(the aliases that define the top-level rowset). "
            "All entries here have scope='outer'. "
            "If multiple top-level relations are listed, return all in appearance order."
        ),
    )

    from_clause_order: List[str] = Field(
        default_factory=list,
        description=(
            "All relation aliases in the OUTERMOST FROM (and explicit JOIN chain) "
            "in the exact left-to-right order they appear after canonicalization. "
            "Use this to enforce stable (left,right) ordering in later passes. "
            "All entries here have scope='outer'."
        ),
    )

    self_join_groups: List[SelfJoinGroup] = Field(
        default_factory=list,
        description=(
            "Groups of aliases that reference the SAME base relation within the SAME scope. "
            "Used to detect self-joins."
        ),
    )

    subqueries: List[str] = Field(
        default_factory=list,
        description=(
            "Aliases that refer to subqueries (inline SELECTs). "
            "These must also appear in 'relations' with kind='subquery' and scope='outer' "
            "(because the subquery alias itself lives in the outer FROM)."
        ),
    )

    cte_defs: List[str] = Field(
        default_factory=list,
        description=(
            "Names of CTEs defined in any WITH clause (deduplicated), exactly as written. "
            "This lists definitions; actual uses inside the CTE body should appear as relations "
            "with scope='cte:<name>'."
        ),
    )

    tables: List[str] = Field(
        default_factory=list,
        description=(
            "Base table/view names mentioned anywhere (deduplicated, unaliased names as written). "
            "This is a convenience index; authoritative aliasing and scope are in 'relations'."
        ),
    )


# Pass 2: Column Analysis Models


class ColumnRef(BaseModel):
    """One column reference attributed to an alias within a specific scope."""

    alias: str = Field(
        description="Relation alias that owns this column (e.g., 'ss', 'd1', 'ms')."
    )
    column: str = Field(
        description="Column name without alias (e.g., 'ss_store_sk', 's_city')."
    )
    scope: str = Field(
        description=(
            "Scope of the alias: 'outer' | 'subquery:<alias>' | 'cte:<name>'. "
            "Must match the scope from relation analysis for this alias."
        )
    )
    evidence: Optional[Evidence] = Field(
        default=None,
        description="Span for a representative occurrence of this column (optional but recommended).",
    )


class ColumnsByAlias(BaseModel):
    """Mapping of alias to its columns (Fenic-compatible)."""

    alias: str = Field(description="The relation alias")
    columns: List[str] = Field(
        description="List of column names available for this alias in its scope"
    )


class ColumnAnalysis(BaseModel):
    """Analysis of column references and the allow-list for each relation.

    Fenic-compatible version using Lists instead of Dicts.
    """

    columns_by_alias: List[ColumnsByAlias] = Field(
        default_factory=list,
        description=(
            "Allow-list: alias -> unique list of column names available for that alias in its scope. "
            "For base table aliases: include columns that are actually referenced. "
            "For subquery aliases: include the subquery's projected column names (output names). "
            "Example: [{'alias': 'store_sales', 'columns': ['ss_store_sk', ...]}, "
            "{'alias': 'ms', 'columns': ['ss_customer_sk','s_city','amt','profit']}, ...]"
        ),
    )

    column_refs: List[ColumnRef] = Field(
        default_factory=list,
        description=(
            "Flat list of (alias, column, scope) triplets for auditing. "
            "Each entry should correspond to a referenced `<alias>.<column>` or to a subquery output column."
        ),
    )

    unresolved_unqualified: List[str] = Field(
        default_factory=list,
        description=(
            "Column names that appeared unqualified in the outer scope but could not be uniquely attributed "
            "to a single alias (ambiguous). Leave empty if none."
        ),
    )


# Pass 3: Join Edge Analysis Models


class JoinClause(BaseModel):
    """Emit EXACTLY ONE JoinClause per DISTINCT unordered pair of relations.

    Emit one JoinClause per DISTINCT unordered pair of relations that are connected
    by column-to-column predicates anywhere in the query (ON or WHERE). If any predicate
    links a pair (A,B), DO NOT emit a CROSS join for that pair.

    Pair ordering:
    - Use the alias that appears earlier in the outermost FROM as `left`, and the other as `right`.
      (This enforces a stable (left,right) so duplicates like (B,A) cannot appear.)

    Join precedence:
    - If SQL explicitly uses LEFT/RIGHT/FULL between A and B → use that type.
    - Else if any column-to-column predicate links A and B (even if SQL shows CROSS JOIN) → type=INNER.
    - Only emit type=CROSS when NO column-to-column predicate exists anywhere between A and B.

    Qualification:
    - Fully qualify both sides in `equi_condition` as <alias>.<column>.
    - For subqueries, use ONLY the alias (never paste the subquery text).

    Raw join condition:
    - Many real-world joins are NOT pure equi-joins (ranges, OR, COALESCE, 1=1 + later filters, etc.).
      To preserve semantic fidelity, we also capture a broader `raw_condition` which may include
      functions, literals, OR groups, BETWEEN, etc.
    - `equi_condition` remains the strict, equi-join-only subset used for downstream reasoning (e.g., filter exclusion).

    Normalization & effective type:
    - INNER joins: `effective_type` MUST be "INNER" and `normalized_equi_condition` MUST equal `equi_condition`.
    - OUTER joins (LEFT/RIGHT/FULL): set `effective_type` to "INNER" ONLY if a later predicate null-kills the preserved side;
      in that case push that predicate into `normalized_equi_condition` (ON predicates AND pushed predicates).
      Otherwise leave `effective_type == type` and `normalized_equi_condition == equi_condition`.
    - CROSS joins: `equi_condition` MUST be empty, `effective_type` MUST be "CROSS".
    """

    type: Literal["INNER", "LEFT", "RIGHT", "FULL", "CROSS"] = Field(
        description=(
            "SQL join type as written or implied by precedence. "
            "Comma-FROM or CROSS JOIN plus an equality predicate in WHERE ⇒ use INNER. "
            "Only use CROSS if no column-to-column predicate exists anywhere for this pair."
        )
    )

    left: str = Field(
        description=(
            "Left relation alias exactly as used in SQL. "
            "Choose the alias that appears earlier in the outermost FROM to enforce a stable order."
        )
    )

    right: str = Field(
        description=(
            "Right relation alias exactly as used in SQL (must not be empty). "
            "Never paste subquery SQL; use the alias."
        )
    )

    equi_condition: str = Field(
        description=(
            "Join condition ONLY (no ON/USING). "
            "For INNER/LEFT/RIGHT/FULL: include ONLY column-to-column predicates between LEFT and RIGHT "
            "joined with AND, fully qualified (<alias>.<col> = <alias>.<col>). "
            "Do NOT include literals, IN/BETWEEN, NULL checks, or single-table filters. "
            "For CROSS: MUST be an empty string."
        )
    )

    raw_condition: str = Field(
        default="",
        description=(
            "Raw join predicate expression (no ON/USING keyword). "
            "This may include non-equi join logic (ranges, OR, functions, literals, BETWEEN, etc.). "
            "It should still only reference the LEFT/RIGHT aliases (no third-alias leakage). "
            "For CROSS or joins without an explicit predicate, this may be empty."
        ),
    )

    effective_type: Literal["INNER", "LEFT", "RIGHT", "FULL", "CROSS"] = Field(
        description=(
            "For INNER: 'INNER'. For CROSS: 'CROSS'. "
            "For OUTER joins, set to 'INNER' ONLY if a later null-killing predicate exists; "
            "otherwise equal to `type`."
        )
    )

    normalized_equi_condition: str = Field(
        description=(
            "If an OUTER join was null-killed and `effective_type` became INNER, push the null-killing "
            "predicate(s) into the join and return the combined condition here. "
            "Otherwise (including all INNER and CROSS joins), this MUST equal `equi_condition`."
        )
    )

    normalized_raw_condition: str = Field(
        default="",
        description=(
            "Normalized version of `raw_condition`. If an OUTER join was null-killed and `effective_type` became INNER, "
            "push the null-killing predicate(s) into this field as well. Otherwise, this should equal `raw_condition`."
        ),
    )


class JoinEdgeAnalysis(BaseModel):
    """Analysis of join edges between relations.

    Uses constrained inputs from RelationAnalysis and ColumnAnalysis to ensure accuracy:
    - Relations with scopes and from_clause_order from RelationAnalysis
    - Column allow-list from ColumnAnalysis
    - Canonical SQL as reference

    Rules:
    1) One edge per unordered pair (A,B). If multiple equi-predicates link the pair, AND them in one equi_condition.
    2) Precedence: explicit LEFT/RIGHT/FULL > INNER (if any column-to-column predicate exists) > CROSS (only if no predicates exist).
    3) Equi_condition: ONLY column-to-column predicates between LEFT and RIGHT, fully qualified, using column allow-list. No literals/IN/BETWEEN/IS NULL/etc.
    4) Side ordering: choose LEFT as the alias that appears earlier in from_clause_order; the other is RIGHT.
    5) Normalization/effective_type:
       - INNER: effective_type="INNER", normalized_equi_condition==equi_condition.
       - OUTER: effective_type becomes "INNER" only if a later null-killing predicate exists; push it into normalized_equi_condition.
       - CROSS: equi_condition="", effective_type="CROSS".
    6) Scope discipline: inside subqueries/CTEs, only use aliases valid in that scope. For subquery aliases at outer scope, use only the columns the subquery projects.
    """

    joins: List[JoinClause] = Field(
        default_factory=list,
        description=(
            "Final, deduplicated join edges. "
            "EXACTLY ONE JoinClause per unordered pair of relations. "
            "Do not include any pair more than once. "
            "Do not emit CROSS for a pair that has any column-to-column predicate anywhere."
        ),
    )


# Pass 4: Filter Analysis Models


class FilterAnalysis(BaseModel):
    """Analysis of filter predicates by clause (WHERE, HAVING, QUALIFY).

    Uses constrained inputs from all previous passes:
    - Relations & scopes from RelationAnalysis
    - Column allow-list from ColumnAnalysis
    - Join conditions from JoinEdgeAnalysis (to exclude them from filters)
    - Canonical SQL as reference

    Rules:
    1) Single-table only: Include only predicates that reference columns from a SINGLE alias (or literal-only).
    2) Allow-list validation: Every column must appear in columns_by_alias for its alias.
    3) Join exclusion: Do NOT include column=column predicates across aliases (those belong to joins).
    4) Clause fidelity: Keep predicates in their original clause (WHERE/HAVING/QUALIFY).
    5) Null-killing detection: For OUTER joins, identify WHERE predicates that null-kill the preserved side.
    6) Preserve SQL verbatim (except whitespace normalization).
    """

    where: List[str] = Field(
        default_factory=list,
        description=(
            "Predicates from WHERE clause. "
            "Include ONLY single-table predicates or literal predicates. "
            "Exclude any predicate that references columns from two or more aliases."
        ),
    )

    having: List[str] = Field(
        default_factory=list,
        description=(
            "Predicates from HAVING clause. "
            "Typically filters on aggregated values. "
            "Same single-table rule applies."
        ),
    )

    qualify: List[str] = Field(
        default_factory=list,
        description=(
            "Predicates from QUALIFY clause (for window functions). "
            "Same single-table rule applies."
        ),
    )

    null_killing_on_outer: List[str] = Field(
        default_factory=list,
        description=(
            "WHERE predicates that null-kill OUTER joins. "
            "For LEFT join: predicates on right alias. "
            "For RIGHT join: predicates on left alias. "
            "For FULL join: predicates on either side."
        ),
    )

    unresolved_predicates: List[str] = Field(
        default_factory=list,
        description=(
            "Predicates with unqualified columns that couldn't be uniquely resolved. "
            "These need manual review."
        ),
    )

    normalized_predicates: List[str] = Field(
        default_factory=list,
        description=(
            "Optional: Normalized versions of predicates. "
            "E.g., 'd_year IN (2000, 2001, 2002)' -> 'd_year BETWEEN 2000 AND 2002'"
        ),
    )
