"""Pass 4: Filter Analysis using SQLGlot AST traversal.

Extracts filter predicates from WHERE, HAVING, and QUALIFY clauses.
Separates single-table filters from join predicates.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Set

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
)
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    FilterAnalysis,
    JoinEdgeAnalysis,
    RelationAnalysis,
)

logger = logging.getLogger(__name__)


def _get_referenced_aliases(expr: exp.Expression) -> Set[str]:
    """Get all table aliases referenced in an expression."""
    aliases: Set[str] = set()
    for col in expr.find_all(exp.Column):
        if col.table:
            aliases.add(col.table)
    return aliases


def _split_and_predicates(expr: Optional[exp.Expression]) -> List[exp.Expression]:
    """Split AND predicates into individual expressions.

    Args:
        expr: Expression that may contain ANDs

    Returns:
        List of individual predicate expressions
    """
    if not expr:
        return []

    predicates: List[exp.Expression] = []

    if isinstance(expr, exp.And):
        predicates.extend(_split_and_predicates(expr.left))
        predicates.extend(_split_and_predicates(expr.right))
    else:
        predicates.append(expr)

    return predicates


def _is_cross_alias_predicate(expr: exp.Expression) -> bool:
    """Check if a predicate references columns from multiple aliases.

    Cross-alias predicates like `a.col = b.col` belong in join analysis,
    not filter analysis.

    Args:
        expr: The predicate expression

    Returns:
        True if predicate references 2+ aliases
    """
    aliases = _get_referenced_aliases(expr)
    return len(aliases) >= 2


def _is_null_killing_on_outer(
    expr: exp.Expression,
    outer_join_preserved: Dict[str, str],
) -> bool:
    """Check if predicate null-kills an outer join's preserved side.

    Args:
        expr: The predicate expression
        outer_join_preserved: Mapping of preserved alias → join type

    Returns:
        True if this predicate null-kills an outer join
    """
    aliases = _get_referenced_aliases(expr)

    # Check if any referenced alias is preserved by an outer join
    for alias in aliases:
        if alias in outer_join_preserved:
            # This predicate references a preserved side
            # Check if it's a null-killer (rejects NULLs)
            from lineage.ingest.static_loaders.semantic.deterministic.null_killing import (
                _is_null_killer,
            )

            if _is_null_killer(expr):
                return True

    return False


def analyze_filters(
    ast: exp.Expression,
    relation_analysis: RelationAnalysis,
    column_analysis: ColumnAnalysis,
    join_analysis: Optional[JoinEdgeAnalysis] = None,
    dialect: Optional[str] = None,
) -> FilterAnalysis:
    """Extract filter predicates from SQL using AST traversal.

    Args:
        ast: Pre-parsed and optionally qualified SQL expression
        relation_analysis: Output from analyze_relations()
        column_analysis: Output from analyze_columns()
        join_analysis: Optional output from analyze_joins() for null-killing detection
        dialect: SQL dialect (for logging/debugging)

    Returns:
        FilterAnalysis with categorized predicates

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        where_predicates: List[str] = []
        having_predicates: List[str] = []
        qualify_predicates: List[str] = []
        null_killing_on_outer: List[str] = []
        unresolved_predicates: List[str] = []

        # Build valid aliases set
        valid_aliases = {rel.alias for rel in relation_analysis.relations}

        # Build columns by alias for validation
        alias_columns: Dict[str, Set[str]] = {}
        for cba in column_analysis.columns_by_alias:
            alias_columns[cba.alias] = set(cba.columns)

        # Build map of preserved sides in outer joins
        outer_join_preserved: Dict[str, str] = {}
        if join_analysis:
            for join in join_analysis.joins:
                if join.type == "LEFT":
                    outer_join_preserved[join.right] = "LEFT"
                elif join.type == "RIGHT":
                    outer_join_preserved[join.left] = "RIGHT"
                elif join.type == "FULL":
                    outer_join_preserved[join.left] = "FULL"
                    outer_join_preserved[join.right] = "FULL"

        # Extract WHERE predicates
        for where in ast.find_all(exp.Where):
            for pred in _split_and_predicates(where.this):
                # Skip cross-alias predicates (those are joins)
                if _is_cross_alias_predicate(pred):
                    continue

                pred_sql = pred.sql(pretty=False)
                aliases = _get_referenced_aliases(pred)

                # Validate that aliases are known
                unknown_aliases = aliases - valid_aliases
                if unknown_aliases:
                    # Check if these are unqualified columns
                    has_unqualified = any(
                        not col.table for col in pred.find_all(exp.Column)
                    )
                    if has_unqualified:
                        unresolved_predicates.append(pred_sql)
                        continue

                where_predicates.append(pred_sql)

                # Check for null-killing on outer joins
                if _is_null_killing_on_outer(pred, outer_join_preserved):
                    null_killing_on_outer.append(pred_sql)

        # Extract HAVING predicates
        for having in ast.find_all(exp.Having):
            for pred in _split_and_predicates(having.this):
                if _is_cross_alias_predicate(pred):
                    continue
                having_predicates.append(pred.sql(pretty=False))

        # Extract QUALIFY predicates
        for qualify in ast.find_all(exp.Qualify):
            for pred in _split_and_predicates(qualify.this):
                if _is_cross_alias_predicate(pred):
                    continue
                qualify_predicates.append(pred.sql(pretty=False))

        return FilterAnalysis(
            where=where_predicates,
            having=having_predicates,
            qualify=qualify_predicates,
            null_killing_on_outer=null_killing_on_outer,
            unresolved_predicates=unresolved_predicates,
            normalized_predicates=[],  # Could add normalization later
        )

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze filters: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing filters: {e}") from e
