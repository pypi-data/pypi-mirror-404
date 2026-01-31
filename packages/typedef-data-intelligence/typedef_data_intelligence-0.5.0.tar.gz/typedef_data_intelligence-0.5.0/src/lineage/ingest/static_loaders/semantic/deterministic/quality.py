"""Quality and ambiguity diagnostics for deterministic SQL analysis.

This module intentionally does NOT change the pydantic analysis models.
Instead, it computes "sidecar" quality signals that can be used to decide
when to fall back to LLM-based technical passes or to gate targeted passes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlglot import exp

from lineage.ingest.static_loaders.semantic.deterministic.graph_enrichment import (
    RelationHint,
)
from lineage.ingest.static_loaders.semantic.models import (
    FilterAnalysis,
    GroupingAnalysis,
    JoinEdgeAnalysis,
    RelationAnalysis,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached


@dataclass(frozen=True)
class PassQuality:
    """Quality signal for a single deterministic pass."""

    pass_name: str
    completeness_score: Optional[float] = None
    unresolved_count: int = 0
    total_count: int = 0

    ambiguous_count: int = 0
    ambiguity_score: float = 0.0

    partial_count: int = 0
    partial_score: float = 0.0

    # Human-friendly examples (small sample) for debugging
    examples: List[str] = field(default_factory=list)

    def should_fallback(self, ambiguity_threshold: float) -> bool:
        """Whether this pass should fall back based on ambiguity/partialness."""
        return self.ambiguity_score > ambiguity_threshold or self.partial_score > ambiguity_threshold


def _get_cte_names(ast: exp.Expression) -> Set[str]:
    cte_names: Set[str] = set()
    for with_clause in ast.find_all(exp.With):
        for cte in with_clause.expressions:
            if isinstance(cte, exp.CTE) and cte.alias:
                cte_names.add(cte.alias)
    return cte_names


def _scope_label(node: exp.Expression, cte_names: Set[str]) -> str:
    """Best-effort scope labeling consistent with deterministic passes.

    We only need to distinguish 'outer' from nested scopes for ambiguity signals.
    """
    current = node.parent
    while current:
        if isinstance(current, exp.CTE):
            if current.alias:
                return f"cte:{current.alias}"
            return "cte:<unknown>"
        if isinstance(current, exp.Subquery):
            if current.alias:
                return f"subquery:{current.alias}"
            return "subquery:<unknown>"
        current = current.parent
    return "outer"


def build_alias_to_schema_columns(
    schema: Optional[Dict[str, Any]],
    relation_analysis: RelationAnalysis,
    relation_hints: Optional[Dict[str, RelationHint]] = None,
) -> Dict[str, Set[str]]:
    """Build alias -> set(columns) from SQLGlot schema + relation analysis.

    Schema format: {catalog: {schema: {table: {col: type}}}}
    """
    alias_to_cols: Dict[str, Set[str]] = {}
    if not schema:
        return alias_to_cols

    alias_to_base = {am.alias: am.base for am in relation_analysis.alias_mappings}

    for rel in relation_analysis.relations:
        alias = rel.alias
        base = alias_to_base.get(alias, rel.base)
        hint = None
        if relation_hints:
            hint = relation_hints.get(alias) or relation_hints.get(base)
        if not base or base.startswith("<"):
            continue

        candidates: List[str] = [base]
        if "." in base:
            candidates.append(base.split(".")[-1])
        if hint and hint.physical_fqn:
            candidates.append(hint.physical_fqn)
            if "." in hint.physical_fqn:
                candidates.append(hint.physical_fqn.split(".")[-1])
        seen: Set[str] = set()
        deduped: List[str] = []
        for c in candidates:
            key = c.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(c)

        cols: Set[str] = set()
        for catalog_data in schema.values():
            if not isinstance(catalog_data, dict):
                continue
            for schema_data in catalog_data.values():
                if not isinstance(schema_data, dict):
                    continue
                for candidate in deduped:
                    table_cols = schema_data.get(candidate)
                    if isinstance(table_cols, dict):
                        cols.update(table_cols.keys())

        if cols:
            alias_to_cols[alias] = cols

    return alias_to_cols


def find_unqualified_ambiguities_in_scope(
    ast: exp.Expression,
    scope: str,
    valid_aliases: Set[str],
    alias_to_schema_columns: Dict[str, Set[str]],
    limit_examples: int = 5,
) -> Tuple[int, List[str]]:
    """Count ambiguous unqualified column references within a scope.

    Ambiguous = unqualified column name that could belong to 2+ aliases based on schema.
    """
    if not alias_to_schema_columns or not valid_aliases:
        return 0, []

    cte_names = _get_cte_names(ast)

    ambiguous_count = 0
    examples: List[str] = []

    for col in ast.find_all(exp.Column):
        if col.table:
            continue
        if _scope_label(col, cte_names) != scope:
            continue
        col_name = col.name
        if not col_name:
            continue

        matches = []
        col_upper = col_name.upper()
        for alias in valid_aliases:
            cols = alias_to_schema_columns.get(alias)
            if not cols:
                continue
            if col_name in cols or col_upper in {c.upper() for c in cols}:
                matches.append(alias)

        if len(matches) >= 2:
            ambiguous_count += 1
            if len(examples) < limit_examples:
                examples.append(f"{col_name} -> {sorted(matches)}")

    return ambiguous_count, examples


def grouping_ambiguity_quality(
    ast: exp.Expression,
    grouping: GroupingAnalysis,
    relation_analysis: RelationAnalysis,
    schema: Optional[Dict[str, Any]],
    scope: str = "outer",
    relation_hints: Optional[Dict[str, RelationHint]] = None,
) -> PassQuality:
    """Compute ambiguity signals for grouping/select items within a scope.

    Counts unqualified column references that match columns in 2+ aliases' schemas.
    This is a conservative proxy for "we can't deterministically attribute lineage."
    """
    alias_to_cols = build_alias_to_schema_columns(schema, relation_analysis, relation_hints)
    valid_aliases = {r.alias for r in relation_analysis.relations if r.scope == scope}

    ambiguous_count = 0
    examples: List[str] = []

    if alias_to_cols and valid_aliases:
        for item in grouping.select:
            if item.is_literal:
                continue
            try:
                parsed = parse_sql_cached(f"SELECT {item.expr}")
            except Exception:
                continue
            for col in parsed.find_all(exp.Column):
                if col.table:
                    continue
                col_name = col.name
                if not col_name:
                    continue
                matches = []
                col_upper = col_name.upper()
                for alias in valid_aliases:
                    cols = alias_to_cols.get(alias)
                    if not cols:
                        continue
                    if col_name in cols or col_upper in {c.upper() for c in cols}:
                        matches.append(alias)
                if len(matches) >= 2:
                    ambiguous_count += 1
                    if len(examples) < 5:
                        examples.append(f"select:{item.alias} uses {col_name} -> {sorted(matches)}")

    total = len([i for i in grouping.select if not i.is_literal]) or 0
    ambiguity_score = (ambiguous_count / total) if total else 0.0
    return PassQuality( # nosec: B106
        pass_name="grouping_analysis",
        ambiguous_count=ambiguous_count,
        ambiguity_score=ambiguity_score,
        total_count=total,
        examples=examples,
    )


def filter_ambiguity_quality(
    ast: exp.Expression,
    filter_analysis: FilterAnalysis,
    relation_analysis: RelationAnalysis,
    schema: Optional[Dict[str, Any]],
    scope: str = "outer",
    relation_hints: Optional[Dict[str, RelationHint]] = None,
) -> PassQuality:
    """Compute ambiguity signals for filters within a scope.

    Counts unqualified column references inside predicates that could match columns
    from 2+ aliases based on schema.
    """
    alias_to_cols = build_alias_to_schema_columns(schema, relation_analysis, relation_hints)
    valid_aliases = {r.alias for r in relation_analysis.relations if r.scope == scope}

    ambiguous_count = 0
    examples: List[str] = []

    def _scan_predicate(pred_str: str) -> None:
        nonlocal ambiguous_count, examples
        try:
            parsed = parse_sql_cached(f"SELECT * WHERE {pred_str}")
        except Exception:
            return
        for col in parsed.find_all(exp.Column):
            if col.table:
                continue
            col_name = col.name
            if not col_name:
                continue
            matches = []
            col_upper = col_name.upper()
            for alias in valid_aliases:
                cols = alias_to_cols.get(alias)
                if not cols:
                    continue
                if col_name in cols or col_upper in {c.upper() for c in cols}:
                    matches.append(alias)
            if len(matches) >= 2:
                ambiguous_count += 1
                if len(examples) < 5:
                    examples.append(f"{col_name} in {pred_str} -> {sorted(matches)}")

    if alias_to_cols and valid_aliases:
        for pred in filter_analysis.where:
            _scan_predicate(pred)
        for pred in filter_analysis.having:
            _scan_predicate(pred)
        for pred in filter_analysis.qualify:
            _scan_predicate(pred)

    total = len(filter_analysis.where) + len(filter_analysis.having) + len(filter_analysis.qualify)
    ambiguity_score = (ambiguous_count / total) if total else 0.0
    return PassQuality( # nosec: B106
        pass_name="filter_analysis",
        ambiguous_count=ambiguous_count,
        ambiguity_score=ambiguity_score,
        total_count=total,
        examples=examples,
    )


def join_partial_quality(join_analysis: JoinEdgeAnalysis) -> PassQuality:
    """Compute a conservative partialness signal for join analysis.

    Our join schema only encodes column-to-column equi predicates. For non-equi joins
    (ranges, OR, functions, 1=1), having an empty `equi_condition` is expected and should
    not force an LLM fallback. We treat only INNER joins with empty equi predicates
    as partial, because those often indicate missed USING/CAST/paren extraction.
    """
    joins = join_analysis.joins or []
    total = len(joins)
    # Be conservative: an empty equi-join condition is not necessarily "wrong".
    # Many real-world joins are non-equi (ranges, OR, function expressions, etc.),
    # and our join schema only allows column-to-column predicates.
    #
    # However, INNER joins missing both the equi condition AND the raw condition are
    # a strong signal that we failed to extract join semantics (or the join had no
    # predicate at all, which should be represented as CROSS in our schema).
    partial = sum(
        1
        for j in joins
        if (
            j.type == "INNER"
            and not (j.equi_condition or "").strip()
            and not (getattr(j, "raw_condition", "") or "").strip()
        )
    )
    partial_score = (partial / total) if total else 0.0

    examples: List[str] = []
    for j in joins:
        if (
            j.type == "INNER"
            and not (j.equi_condition or "").strip()
            and not (getattr(j, "raw_condition", "") or "").strip()
        ):
            if len(examples) < 5:
                examples.append(f"{j.type} {j.left}->{j.right} missing_join_predicates")

    return PassQuality( # nosec: B106
        pass_name="join_analysis",
        total_count=total,
        partial_count=partial,
        partial_score=partial_score,
        examples=examples,
    )

