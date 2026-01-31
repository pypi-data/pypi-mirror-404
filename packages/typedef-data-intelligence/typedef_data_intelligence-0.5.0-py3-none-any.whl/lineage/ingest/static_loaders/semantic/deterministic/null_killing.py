"""Null-killing detection for outer joins.

Detects WHERE predicates that effectively convert LEFT/RIGHT/FULL joins
to INNER joins by rejecting NULL rows from the preserved side.

Examples of null-killing predicates:
- WHERE right.col IS NOT NULL
- WHERE right.col = 'value'
- WHERE right.col IN (...)
- WHERE right.col > 0

This is the "effective_type" analysis from the plan.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Set

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
)
from lineage.ingest.static_loaders.semantic.models import (
    FilterAnalysis,
    JoinClause,
    JoinEdgeAnalysis,
)

logger = logging.getLogger(__name__)


def _get_referenced_aliases(pred_ast: exp.Expression) -> Set[str]:
    """Get all table aliases referenced in a predicate."""
    aliases: Set[str] = set()
    for col in pred_ast.find_all(exp.Column):
        if col.table:
            aliases.add(col.table)
    return aliases


def _is_null_killer(pred_ast: exp.Expression) -> bool:
    """Check if a predicate would reject NULL rows.

    A predicate is a null-killer if it evaluates to FALSE or UNKNOWN
    when its columns are NULL. This includes:
    - IS NOT NULL
    - Equality comparisons (NULL = x is UNKNOWN, rejected by WHERE)
    - Inequality comparisons
    - IN expressions
    - BETWEEN expressions
    - LIKE expressions

    Args:
        pred_ast: Parsed predicate expression

    Returns:
        True if the predicate kills NULLs
    """
    # IS NOT NULL → kills NULLs
    if isinstance(pred_ast, exp.Not):
        inner = pred_ast.this
        if isinstance(inner, exp.Is) and isinstance(inner.expression, exp.Null):
            return True

    # Equality/comparison → rejects NULLs (NULL = x is UNKNOWN)
    if isinstance(
        pred_ast, (exp.EQ, exp.GT, exp.LT, exp.GTE, exp.LTE, exp.NEQ)
    ):
        return True

    # IN → rejects NULLs
    if isinstance(pred_ast, exp.In):
        return True

    # BETWEEN → rejects NULLs
    if isinstance(pred_ast, exp.Between):
        return True

    # LIKE → rejects NULLs
    if isinstance(pred_ast, exp.Like):
        return True

    # IS NULL is NOT a null-killer (it only returns true for NULLs)
    if isinstance(pred_ast, exp.Is) and isinstance(pred_ast.expression, exp.Null):
        return False

    # Compound: AND with any null-killer is a null-killer
    if isinstance(pred_ast, exp.And):
        return _is_null_killer(pred_ast.left) or _is_null_killer(pred_ast.right)

    # OR: only if BOTH sides are null-killers
    if isinstance(pred_ast, exp.Or):
        return _is_null_killer(pred_ast.left) and _is_null_killer(pred_ast.right)

    # Function calls that reference columns typically kill NULLs
    # (e.g., LENGTH(col) > 0, COALESCE not included as it handles NULLs)
    if isinstance(pred_ast, exp.Func):
        # Most functions return NULL if input is NULL, which fails WHERE
        # Exception: COALESCE, IFNULL, NVL, etc.
        func_name = pred_ast.name.upper() if hasattr(pred_ast, "name") else ""
        null_safe_funcs = {"COALESCE", "IFNULL", "NVL", "NVL2", "NULLIF", "ISNULL"}
        if func_name not in null_safe_funcs:
            return True

    return False


def _parse_predicate(predicate: str) -> Optional[exp.Expression]:
    """Try to parse a predicate string into an expression."""
    try:
        # Wrap in SELECT to parse as expression (uses global LRU cache)
        from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
            parse_sql_cached,
        )

        parsed = parse_sql_cached(f"SELECT * WHERE {predicate}")
        where = parsed.find(exp.Where)
        if where:
            return where.this
        return None
    except SqlglotError:
        return None


def detect_null_killing(
    join_analysis: JoinEdgeAnalysis,
    filter_analysis: FilterAnalysis,
) -> JoinEdgeAnalysis:
    """Detect WHERE predicates that null-kill outer joins.

    A LEFT JOIN becomes effectively INNER when the WHERE clause
    references the right side in a way that eliminates NULLs.

    Args:
        join_analysis: JoinEdgeAnalysis with basic join info
        filter_analysis: FilterAnalysis with WHERE predicates

    Returns:
        Updated JoinEdgeAnalysis with effective_type and normalized_equi_condition set

    Raises:
        AnalysisError: If analysis fails
    """
    try:
        updated_joins: List[JoinClause] = []

        for join in join_analysis.joins:
            # Non-outer joins don't need null-killing analysis
            if join.type not in ("LEFT", "RIGHT", "FULL"):
                updated_joins.append(
                    JoinClause(
                        type=join.type,
                        left=join.left,
                        right=join.right,
                        equi_condition=join.equi_condition,
                        raw_condition=getattr(join, "raw_condition", "") or "",
                        effective_type=join.type,
                        normalized_equi_condition=join.equi_condition,
                        normalized_raw_condition=getattr(join, "raw_condition", "") or "",
                    )
                )
                continue

            # Determine which side is preserved (can have NULLs introduced)
            if join.type == "LEFT":
                preserved_aliases = {join.right}
            elif join.type == "RIGHT":
                preserved_aliases = {join.left}
            else:  # FULL
                preserved_aliases = {join.left, join.right}

            # Check WHERE predicates for null-killers on preserved side
            null_killing_predicates: List[str] = []

            for predicate in filter_analysis.where:
                pred_ast = _parse_predicate(predicate)
                if not pred_ast:
                    continue

                referenced_aliases = _get_referenced_aliases(pred_ast)

                # Check if predicate references preserved side and kills NULLs
                if referenced_aliases & preserved_aliases:
                    if _is_null_killer(pred_ast):
                        null_killing_predicates.append(predicate)

            # Update join based on null-killing
            if null_killing_predicates:
                # Build normalized condition by combining ON + null-killers
                all_conditions = []
                if join.equi_condition:
                    all_conditions.append(join.equi_condition)
                all_conditions.extend(null_killing_predicates)
                normalized = " AND ".join(all_conditions)

                base_raw = (getattr(join, "raw_condition", "") or "").strip()
                if not base_raw:
                    # Best-effort: if raw is missing, fall back to equi-only condition.
                    base_raw = (join.equi_condition or "").strip()
                raw_parts: List[str] = []
                if base_raw:
                    raw_parts.append(base_raw)
                raw_parts.extend(null_killing_predicates)
                normalized_raw = " AND ".join(raw_parts)

                updated_joins.append(
                    JoinClause(
                        type=join.type,
                        left=join.left,
                        right=join.right,
                        equi_condition=join.equi_condition,
                        raw_condition=getattr(join, "raw_condition", "") or "",
                        effective_type="INNER",
                        normalized_equi_condition=normalized,
                        normalized_raw_condition=normalized_raw,
                    )
                )
            else:
                # No null-killing: effective_type = type
                raw_cond = getattr(join, "raw_condition", "") or ""
                updated_joins.append(
                    JoinClause(
                        type=join.type,
                        left=join.left,
                        right=join.right,
                        equi_condition=join.equi_condition,
                        raw_condition=raw_cond,
                        effective_type=join.type,
                        normalized_equi_condition=join.equi_condition,
                        normalized_raw_condition=raw_cond,
                    )
                )

        return JoinEdgeAnalysis(joins=updated_joins)

    except Exception as e:
        raise AnalysisError(f"Unexpected error detecting null-killing: {e}") from e
