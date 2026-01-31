"""Pass 3: Join Edge Analysis using SQLGlot AST traversal.

Extracts join relationships between relations, including:
- Join type (INNER, LEFT, RIGHT, FULL, CROSS)
- Left and right aliases (ordered by FROM clause appearance)
- Join conditions (column-to-column predicates)
- Effective type after null-killing analysis (done in null_killing.py)
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Sequence, Set, Tuple

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
)
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    JoinClause,
    JoinEdgeAnalysis,
    RelationAnalysis,
)

logger = logging.getLogger(__name__)


def _split_and_predicates(expr: Optional[exp.Expression]) -> List[exp.Expression]:
    """Split a boolean expression by top-level AND into a flat list."""
    if not expr:
        return []
    if isinstance(expr, exp.And):
        return _split_and_predicates(expr.left) + _split_and_predicates(expr.right)
    return [expr]


def _get_referenced_aliases(expr: exp.Expression) -> Set[str]:
    """Return the set of table aliases referenced by columns in an expression."""
    aliases: Set[str] = set()
    for col in expr.find_all(exp.Column):
        if col.table:
            aliases.add(col.table)
    return aliases


def _unwrap_to_column(node: exp.Expression) -> Optional[exp.Column]:
    """Best-effort unwraps simple wrappers to a Column.

    Supports common patterns like:
    - (a.col)
    - CAST(a.col AS ...)
    - TRY_CAST(a.col AS ...)

    We intentionally do NOT unwrap arbitrary functions (e.g., COALESCE, SPLIT_PART)
    because those are not column-to-column equi predicates per the join schema.
    """
    current: Optional[exp.Expression] = node
    while current is not None:
        if isinstance(current, exp.Column):
            return current
        if isinstance(current, exp.Paren):
            current = current.this
            continue
        # sqlglot versions differ (e.g., SafeCast may not exist).
        if isinstance(current, (exp.Cast, exp.TryCast)) or current.__class__.__name__ in {
            "SafeCast",
            "TryCast",
        }:
            current = current.this
            continue
        break
    return None


def _is_natural_join(join: exp.Join) -> bool:
    """Return True if the join is a NATURAL join."""
    kind = (join.kind or "").upper()
    side = (join.side or "").upper()
    if side:
        kind = f"{side} {kind}".strip()
    method = (join.args.get("method") or "").upper()
    return bool(join.args.get("natural")) or "NATURAL" in kind or method == "NATURAL"


def _map_join_kind(join: exp.Join) -> str:
    """Map SQLGlot join kind to our join type string.

    Args:
        join: The Join expression

    Returns:
        One of: 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'
    """
    kind = (join.kind or "").upper()
    # SQLGlot dialects often represent LEFT/RIGHT/FULL as `join.side`
    # with `join.kind` reserved for SEMI/ANTI/CROSS, etc.
    side = (join.side or "").upper()
    if side:
        kind = f"{side} {kind}".strip()

    if "LEFT" in kind:
        return "LEFT"
    elif "RIGHT" in kind:
        return "RIGHT"
    elif "FULL" in kind or "OUTER" in kind:
        return "FULL"
    elif _is_natural_join(join):
        # NATURAL joins are inner joins with implicit USING columns.
        return "INNER"
    elif "CROSS" in kind:
        return "CROSS"
    else:
        # Default to INNER for regular JOIN
        return "INNER"


def _get_join_alias(node: exp.Expression) -> Optional[str]:
    """Get the alias for a join target."""
    if isinstance(node, exp.Table):
        return node.alias or node.name
    elif isinstance(node, exp.Subquery):
        return node.alias
    elif hasattr(node, "alias") and node.alias:
        return node.alias
    elif hasattr(node, "name") and node.name:
        return node.name
    return None


def _extract_join_condition_predicates(
    condition: Optional[exp.Expression],
) -> List[str]:
    """Extract column-to-column predicates from a join condition.

    Only includes predicates of the form alias.col = alias.col.
    Filters out literals, IN/BETWEEN, NULL checks, etc.

    Args:
        condition: The ON clause expression

    Returns:
        List of predicate strings
    """
    if not condition:
        return []

    predicates: List[str] = []

    # Handle AND expressions by recursing
    if isinstance(condition, exp.And):
        predicates.extend(_extract_join_condition_predicates(condition.left))
        predicates.extend(_extract_join_condition_predicates(condition.right))
        return predicates

    # Check if this is a column-to-column equality
    if isinstance(condition, exp.EQ):
        left_col = _unwrap_to_column(condition.left)
        right_col = _unwrap_to_column(condition.right)

        # Both sides should resolve to column references
        if left_col is not None and right_col is not None:
            left_sql = left_col.sql(pretty=False)
            right_sql = right_col.sql(pretty=False)
            predicates.append(f"{left_sql} = {right_sql}")

    return predicates


def _extract_using_predicates(
    using_expr: object,
    *,
    left_alias: str,
    right_alias: str,
) -> List[str]:
    """Extract equi-join predicates from a USING clause.

    SQLGlot dialects can represent USING as:
    - an expression-like object with an `.expressions` list
    - a raw list of identifier-like expressions
    """
    cols: List[str] = []

    def _coerce_name(e: object) -> Optional[str]:
        if isinstance(e, exp.Identifier):
            return e.this
        if isinstance(e, exp.Column):
            # For USING, column table is typically empty; take the column name
            return e.name
        if isinstance(e, exp.Expression) and hasattr(e, "name") and e.name:
            return str(e.name)
        if isinstance(e, str):
            return e
        return None

    # NOTE: sqlglot versions differ; some have an explicit Using node, some return a raw list.
    if isinstance(using_expr, exp.Expression) and hasattr(using_expr, "expressions"):
        for e in getattr(using_expr, "expressions", []) or []:
            n = _coerce_name(e)
            if n:
                cols.append(n)
    elif isinstance(using_expr, Sequence) and not isinstance(using_expr, (str, bytes)):
        for e in using_expr:
            n = _coerce_name(e)
            if n:
                cols.append(n)
    else:
        n = _coerce_name(using_expr)
        if n:
            cols.append(n)

    preds: List[str] = []
    for c in cols:
        preds.append(f"{left_alias}.{c} = {right_alias}.{c}")
    return preds


def _order_join_pair(
    alias1: str,
    alias2: str,
    from_clause_order: List[str],
) -> Tuple[str, str]:
    """Order a join pair according to FROM clause order.

    The alias that appears earlier in from_clause_order is 'left'.

    Args:
        alias1: First alias
        alias2: Second alias
        from_clause_order: List of aliases in FROM clause order

    Returns:
        Tuple of (left_alias, right_alias)
    """
    try:
        idx1 = from_clause_order.index(alias1)
    except ValueError:
        idx1 = float("inf")

    try:
        idx2 = from_clause_order.index(alias2)
    except ValueError:
        idx2 = float("inf")

    if idx1 <= idx2:
        return alias1, alias2
    else:
        return alias2, alias1


def _find_where_join_predicates(
    ast: exp.Expression,
    from_clause_order: List[str],
) -> Dict[Tuple[str, str], List[str]]:
    """Find join predicates in WHERE clause (comma-join style).

    Some queries use FROM a, b WHERE a.col = b.col instead of
    explicit JOINs. These are effectively INNER joins.

    Args:
        ast: The parsed SQL expression
        from_clause_order: Ordered aliases from FROM clause

    Returns:
        Dict mapping ordered (left, right) pairs to their predicates
    """
    where_joins: Dict[Tuple[str, str], List[str]] = {}
    valid_aliases = set(from_clause_order)

    # Find WHERE clause
    for where in ast.find_all(exp.Where):
        for eq in where.find_all(exp.EQ):
            left = eq.left
            right = eq.right

            if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                left_alias = left.table
                right_alias = right.table

                # Only include cross-alias predicates
                if (
                    left_alias
                    and right_alias
                    and left_alias != right_alias
                    and left_alias in valid_aliases
                    and right_alias in valid_aliases
                ):
                    ordered_pair = _order_join_pair(
                        left_alias, right_alias, from_clause_order
                    )
                    predicate = f"{left.sql(pretty=False)} = {right.sql(pretty=False)}"

                    if ordered_pair not in where_joins:
                        where_joins[ordered_pair] = []
                    where_joins[ordered_pair].append(predicate)

    return where_joins


def _find_where_cross_alias_predicates_for_select(
    select: exp.Select,
    from_clause_order: List[str],
) -> Dict[Tuple[str, str], Tuple[List[str], List[str]]]:
    """Find cross-alias predicates in a SELECT's WHERE clause.

    Returns a mapping of (left,right) -> (equi_predicates, raw_predicates).

    - equi_predicates are strict column-to-column equalities (fully qualified)
    - raw_predicates are any predicates that reference exactly two aliases (may be non-equi)
    """
    where = select.args.get("where")
    if not isinstance(where, exp.Where):
        return {}

    valid_aliases = set(from_clause_order)
    out: Dict[Tuple[str, str], Tuple[List[str], List[str]]] = {}

    for pred in _split_and_predicates(where.this):
        aliases = _get_referenced_aliases(pred)
        if len(aliases) != 2:
            continue
        if not aliases.issubset(valid_aliases):
            continue
        left_alias, right_alias = tuple(sorted(aliases))
        ordered_pair = _order_join_pair(left_alias, right_alias, from_clause_order)

        equi_preds, raw_preds = out.setdefault(ordered_pair, ([], []))
        raw_preds.append(pred.sql(pretty=False))

        if isinstance(pred, exp.EQ):
            lcol = _unwrap_to_column(pred.left)
            rcol = _unwrap_to_column(pred.right)
            if lcol is not None and rcol is not None and lcol.table and rcol.table and lcol.table != rcol.table:
                equi_preds.append(f"{lcol.sql(pretty=False)} = {rcol.sql(pretty=False)}")

    return out


def _find_outer_select(ast: exp.Expression) -> Optional[exp.Select]:
    """Find the outermost SELECT (not in CTE or subquery)."""
    for select in ast.find_all(exp.Select):
        parent = select.parent
        in_nested = False
        while parent:
            if isinstance(parent, (exp.CTE, exp.Subquery)):
                in_nested = True
                break
            parent = parent.parent
        if not in_nested:
            return select
    return None


def _is_direct_child_join(join: exp.Join, select: exp.Select) -> bool:
    """Check if a join is a direct child of this SELECT (not nested)."""
    parent = join.parent
    while parent:
        if parent == select:
            return True
        if isinstance(parent, (exp.Subquery, exp.CTE)):
            return False
        parent = parent.parent
    return False


def analyze_joins(
    ast: exp.Expression,
    relation_analysis: RelationAnalysis,
    column_analysis: ColumnAnalysis,
    dialect: Optional[str] = None,
) -> JoinEdgeAnalysis:
    """Extract join edges across all scopes using AST traversal.

    This pass originally only extracted joins from the outermost SELECT (a known
    limitation for real-world dbt models where key joins live inside CTEs).
    We now extract explicit JOINs and comma-join predicates from every SELECT
    (outer + CTE bodies + subqueries), and dedupe within each inferred scope.

    Args:
        ast: Pre-parsed and optionally qualified SQL expression
        relation_analysis: Output from analyze_relations()
        column_analysis: Output from analyze_columns()
        dialect: SQL dialect (for logging/debugging)

    Returns:
        JoinEdgeAnalysis with join clauses

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        joins: List[JoinClause] = []
        relations_by_alias: Dict[str, List[str]] = {}
        for r in relation_analysis.relations:
            relations_by_alias.setdefault(r.alias, []).append(r.scope)

        # Track seen joins to avoid duplicates (include scope to avoid alias collisions across scopes)
        seen_keys: Set[Tuple[str, str, str, str, str]] = set()

        # Build alias lookup for columns
        alias_columns: Dict[str, Set[str]] = {}
        for cba in column_analysis.columns_by_alias:
            alias_columns[cba.alias] = set(cba.columns)

        def _infer_scope(left: str, right: str) -> str:
            ls = set(relations_by_alias.get(left, []))
            rs = set(relations_by_alias.get(right, []))
            inter = ls.intersection(rs)
            if inter:
                # Prefer a non-outer scope if present (joins in CTE/subquery are high-signal)
                inter_sorted = sorted(inter, key=lambda s: (s == "outer", s))
                return inter_sorted[0]
            if ls:
                return sorted(ls, key=lambda s: (s == "outer", s))[0]
            if rs:
                return sorted(rs, key=lambda s: (s == "outer", s))[0]
            return "unknown"

        def _from_clause_order_for_select(select: exp.Select) -> List[str]:
            order: List[str] = []
            from_clause = select.args.get("from")
            if isinstance(from_clause, exp.From) and from_clause.this is not None:
                first = _get_join_alias(from_clause.this)
                if first:
                    order.append(first)
            for j in select.args.get("joins") or []:
                if isinstance(j, exp.Join) and j.this is not None:
                    a = _get_join_alias(j.this)
                    if a:
                        order.append(a)
            return order

        def _find_where_join_predicates_for_select(
            select: exp.Select,
            from_clause_order: List[str],
        ) -> Dict[Tuple[str, str], List[str]]:
            where_joins: Dict[Tuple[str, str], List[str]] = {}
            valid_aliases = set(from_clause_order)
            where = select.args.get("where")
            if not isinstance(where, exp.Where):
                return where_joins

            for eq in where.find_all(exp.EQ):
                left = eq.left
                right = eq.right
                if isinstance(left, exp.Column) and isinstance(right, exp.Column):
                    left_alias = left.table
                    right_alias = right.table
                    if (
                        left_alias
                        and right_alias
                        and left_alias != right_alias
                        and left_alias in valid_aliases
                        and right_alias in valid_aliases
                    ):
                        ordered_pair = _order_join_pair(
                            left_alias, right_alias, from_clause_order
                        )
                        predicate = f"{left.sql(pretty=False)} = {right.sql(pretty=False)}"
                        where_joins.setdefault(ordered_pair, []).append(predicate)
            return where_joins

        # Extract joins for every SELECT (outer + CTE + subquery)
        for select in ast.find_all(exp.Select):
            from_clause = select.args.get("from")
            if not isinstance(from_clause, exp.From):
                continue
            left_alias = _get_join_alias(from_clause.this) if from_clause.this else None
            if not left_alias:
                continue

            from_clause_order = _from_clause_order_for_select(select)
            if not from_clause_order:
                from_clause_order = relation_analysis.from_clause_order

            # Explicit JOIN chain for this SELECT
            for join in select.args.get("joins") or []:
                if not isinstance(join, exp.Join) or not join.this:
                    continue
                right_alias = _get_join_alias(join.this)
                if not right_alias:
                    continue

                join_type = _map_join_kind(join)
                condition_expr = join.args.get("on")
                using_expr = join.args.get("using")

                if using_expr is not None:
                    predicates = _extract_using_predicates(
                        using_expr, left_alias=left_alias, right_alias=right_alias
                    )
                else:
                    predicates = _extract_join_condition_predicates(condition_expr)

                # JOIN without ON/USING is only valid as CROSS/NATURAL; treat as CROSS for our schema.
                if (
                    join_type == "INNER"
                    and not _is_natural_join(join)
                    and not predicates
                    and condition_expr is None
                    and using_expr is None
                ):
                    join_type = "CROSS"

                equi_condition = " AND ".join(predicates) if predicates else ""
                if join_type == "CROSS":
                    raw_condition = ""
                elif using_expr is not None:
                    # Represent USING as explicit equality predicates (fully qualified).
                    raw_condition = equi_condition
                else:
                    raw_condition = (
                        condition_expr.sql(pretty=False) if condition_expr is not None else ""
                    )

                ordered_left, ordered_right = _order_join_pair(
                    left_alias, right_alias, from_clause_order
                )
                scope = _infer_scope(ordered_left, ordered_right)
                key = (scope, ordered_left, ordered_right, join_type, equi_condition)
                if key in seen_keys:
                    left_alias = right_alias
                    continue
                seen_keys.add(key)

                joins.append(
                    JoinClause(
                        type=join_type,
                        left=ordered_left,
                        right=ordered_right,
                        equi_condition=equi_condition,
                        raw_condition=raw_condition,
                        effective_type=join_type,
                        normalized_equi_condition=equi_condition,
                        normalized_raw_condition=raw_condition,
                    )
                )
                left_alias = right_alias

            # Comma-join predicates in WHERE for this SELECT
            where_pairs = _find_where_cross_alias_predicates_for_select(select, from_clause_order)
            for (left, right), (equi_preds, raw_preds) in where_pairs.items():
                equi_condition = " AND ".join(equi_preds) if equi_preds else ""
                raw_condition = " AND ".join(raw_preds) if raw_preds else ""
                scope = _infer_scope(left, right)
                key = (scope, left, right, "INNER", equi_condition)
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                joins.append(
                    JoinClause(
                        type="INNER",
                        left=left,
                        right=right,
                        equi_condition=equi_condition,
                        raw_condition=raw_condition,
                        effective_type="INNER",
                        normalized_equi_condition=equi_condition,
                        normalized_raw_condition=raw_condition,
                    )
                )

        return JoinEdgeAnalysis(joins=joins)

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze joins: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing joins: {e}") from e
