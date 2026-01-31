"""Pass 5: Grouping Analysis using SQLGlot AST traversal.

Extracts SELECT items, GROUP BY expressions, and determines result grain.
This is one of the more challenging passes because source_aliases resolution
may require schema information.
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
    GroupingAnalysis,
    RelationAnalysis,
    SelectItem,
)

logger = logging.getLogger(__name__)


# Aggregate functions that indicate a measure
AGGREGATE_FUNCTIONS = {
    "SUM",
    "COUNT",
    "AVG",
    "MIN",
    "MAX",
    "STDDEV",
    "VARIANCE",
    "VAR_POP",
    "VAR_SAMP",
    "STDDEV_POP",
    "STDDEV_SAMP",
    "COVAR_POP",
    "COVAR_SAMP",
    "CORR",
    "PERCENTILE_CONT",
    "PERCENTILE_DISC",
    "LISTAGG",
    "STRING_AGG",
    "GROUP_CONCAT",
    "ARRAY_AGG",
    "COLLECT_LIST",
    "COLLECT_SET",
    "APPROX_COUNT_DISTINCT",
    "HLL_COUNT_DISTINCT",
    "COUNT_IF",
    "SUM_IF",
    "AVG_IF",
    "MEDIAN",
    "MODE",
    "FIRST_VALUE",  # Not always aggregate, but often used with aggregation
    "LAST_VALUE",  # Same
    "ANY_VALUE",
    "ARBITRARY",
}


def _is_inside_window(node: exp.Expression, root: exp.Expression) -> bool:
    """Check if a node is inside a Window expression."""
    parent = node.parent
    while parent and parent != root:
        if isinstance(parent, exp.Window):
            return True
        parent = parent.parent
    return False


def _has_aggregate_function(expr: exp.Expression) -> bool:
    """Check if an expression contains an aggregate function (not in a window).

    Only counts aggregates at the current scope, not in subqueries or windows.
    Window functions like SUM(...) OVER (...) are NOT aggregates because they
    don't collapse rows - they compute per-row values.

    Args:
        expr: The expression to check

    Returns:
        True if expression contains a true aggregate function (not windowed)
    """
    for func in expr.find_all(exp.Func):
        # Skip functions inside subqueries
        parent = func.parent
        in_subquery = False
        while parent and parent != expr:
            if isinstance(parent, exp.Subquery):
                in_subquery = True
                break
            parent = parent.parent

        if in_subquery:
            continue

        # Skip functions inside window expressions
        if _is_inside_window(func, expr):
            continue

        func_name = type(func).__name__.upper()
        if func_name in AGGREGATE_FUNCTIONS:
            return True

        # Also check AggFunc base class
        if isinstance(func, exp.AggFunc):
            return True

    return False


def _is_literal_expression(expr: exp.Expression) -> bool:
    """Check if an expression is a literal value (NULL, string, number, boolean).

    Literals don't reference any tables or columns, so they correctly have
    no source_aliases. Also handles CAST(literal AS type) which is common
    for typed NULL values.

    Args:
        expr: The expression to check

    Returns:
        True if the expression is a literal value (possibly wrapped in CAST)
    """
    # Unwrap Alias if present
    if isinstance(expr, exp.Alias):
        expr = expr.this

    # Direct literal types
    if isinstance(expr, (exp.Literal, exp.Null, exp.Boolean)):
        return True

    # Check for negated literals (e.g., -1, -3.14)
    if isinstance(expr, exp.Neg) and isinstance(expr.this, exp.Literal):
        return True

    # Check for CAST(literal AS type) - common for typed NULLs like CAST(NULL AS TEXT)
    if isinstance(expr, exp.Cast):
        inner = expr.this
        if isinstance(inner, (exp.Literal, exp.Null, exp.Boolean)):
            return True
        # Also handle CAST(-1 AS INT) etc.
        if isinstance(inner, exp.Neg) and isinstance(inner.this, exp.Literal):
            return True

    return False


def _extract_source_aliases(
    expr: exp.Expression,
    valid_aliases: Set[str],
    alias_columns: Dict[str, Set[str]],
) -> List[str]:
    """Extract source aliases from an expression.

    Args:
        expr: The expression to analyze
        valid_aliases: Set of valid relation aliases
        alias_columns: Map of alias → column names

    Returns:
        List of unique source aliases referenced
    """
    aliases: Set[str] = set()

    for col in expr.find_all(exp.Column):
        if col.table and col.table in valid_aliases:
            aliases.add(col.table)
        elif not col.table:
            # Unqualified column - try to resolve
            col_name = col.name
            for alias, columns in alias_columns.items():
                if col_name in columns:
                    aliases.add(alias)
                    break  # Take first match (may be ambiguous)

    return sorted(list(aliases))


def _extract_group_by(select: exp.Select) -> List[str]:
    """Extract GROUP BY expressions from a SELECT.

    Args:
        select: The SELECT expression

    Returns:
        List of GROUP BY expressions as strings
    """
    group_by: List[str] = []

    group = select.find(exp.Group)
    if group:
        for expr in group.expressions:
            group_by.append(expr.sql(pretty=False))

    return group_by


def _extract_aggregate_expressions(select: exp.Select) -> List[str]:
    """Extract aggregate expressions from SELECT items (excluding window functions).

    Args:
        select: The SELECT expression

    Returns:
        List of true aggregate expression strings (not windowed)
    """
    measures: List[str] = []

    for projection in select.expressions:
        if _has_aggregate_function(projection):
            # Get just the expression, not the alias
            if isinstance(projection, exp.Alias):
                measures.append(projection.this.sql(pretty=False))
            else:
                measures.append(projection.sql(pretty=False))

    return measures


def analyze_grouping(
    ast: exp.Expression,
    relation_analysis: RelationAnalysis,
    column_analysis: ColumnAnalysis,
    scope: str = "outer",
    dialect: Optional[str] = None,
) -> GroupingAnalysis:
    """Extract grouping information for a specific scope.

    Args:
        ast: Pre-parsed SQL expression
        relation_analysis: Output from analyze_relations()
        column_analysis: Output from analyze_columns()
        scope: The scope to analyze ('outer', 'cte:<name>', 'subquery:<alias>')
        dialect: SQL dialect (for logging/debugging)

    Returns:
        GroupingAnalysis for the specified scope

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        # Build valid aliases for this scope
        valid_aliases: Set[str] = set()
        for rel in relation_analysis.relations:
            if rel.scope == scope:
                valid_aliases.add(rel.alias)

        # Build columns by alias
        alias_columns: Dict[str, Set[str]] = {}
        for cba in column_analysis.columns_by_alias:
            alias_columns[cba.alias] = set(cba.columns)

        # Find the SELECT for this scope
        target_select: Optional[exp.Select] = None

        if scope == "outer":
            # Find outermost SELECT
            for select in ast.find_all(exp.Select):
                # Check this SELECT isn't in a CTE or subquery.
                #
                # Note: dbt/Snowflake compiled SQL often wraps UNION branches as:
                #   (SELECT ...) UNION ALL (SELECT ...)
                # SQLGlot represents those parentheses as exp.Subquery nodes *without an alias*.
                # Those are not "real" derived tables and should still be treated as outer scope.
                parent = select.parent
                in_nested = False
                while parent:
                    if isinstance(parent, (exp.CTE, exp.Subquery)):
                        if isinstance(parent, exp.Subquery):
                            # Treat alias-less wrapper subqueries as outer if:
                            # - this subquery has no alias, and
                            # - it's at the root, or it's directly under a set operation (UNION/INTERSECT/EXCEPT)
                            parent_alias = getattr(parent, "alias", None)
                            # SQLGlot uses empty-string alias for many alias-less subqueries.
                            has_alias = bool(parent_alias)
                            is_wrapper = (not has_alias) and (
                                parent.parent is None
                                or isinstance(parent.parent, (exp.Union, exp.Intersect, exp.Except))
                            )
                            if is_wrapper:
                                parent = parent.parent
                                continue
                        in_nested = True
                        break
                    parent = parent.parent
                if not in_nested:
                    target_select = select
                    break
        elif scope.startswith("cte:"):
            cte_name = scope[4:]
            for cte in ast.find_all(exp.CTE):
                if cte.alias == cte_name:
                    target_select = cte.find(exp.Select)
                    break
        elif scope.startswith("subquery:"):
            subquery_alias = scope[9:]
            for subquery in ast.find_all(exp.Subquery):
                if subquery.alias == subquery_alias:
                    target_select = subquery.find(exp.Select)
                    break

        if not target_select:
            # No SELECT found for this scope
            return GroupingAnalysis(
                select=[],
                group_by=[],
                is_aggregated=False,
                result_grain=[],
                measures=[],
            )

        # Extract SELECT items
        select_items: List[SelectItem] = []
        for projection in target_select.expressions:
            # Get expression and alias
            if isinstance(projection, exp.Alias):
                expr_str = projection.this.sql(pretty=False)
                alias = projection.alias
            else:
                expr_str = projection.sql(pretty=False)
                alias = projection.alias_or_name if hasattr(projection, "alias_or_name") else expr_str

            # Check if this is a literal value
            is_literal = _is_literal_expression(projection)

            # Extract source aliases
            source_aliases = _extract_source_aliases(
                projection, valid_aliases, alias_columns
            )

            select_items.append(
                SelectItem(
                    expr=expr_str,
                    alias=alias,
                    source_aliases=source_aliases,
                    is_literal=is_literal,
                )
            )

        # Extract GROUP BY
        group_by = _extract_group_by(target_select)

        # Extract measures (aggregate expressions)
        measures = _extract_aggregate_expressions(target_select)

        # Determine is_aggregated - use measures list instead of kind
        has_group_by = len(group_by) > 0
        has_aggregates = len(measures) > 0
        is_aggregated = has_group_by or has_aggregates

        # Build set of aggregate expressions for grain computation
        # We need to identify which SELECT expressions are aggregates
        aggregate_exprs: Set[str] = set()
        for projection in target_select.expressions:
            if _has_aggregate_function(projection):
                if isinstance(projection, exp.Alias):
                    aggregate_exprs.add(projection.this.sql(pretty=False))
                else:
                    aggregate_exprs.add(projection.sql(pretty=False))

        # Compute result_grain
        # Grain = GROUP BY expressions + non-aggregate SELECT expressions
        result_grain: List[str] = []
        grain_set: Set[str] = set()

        # Add GROUP BY expressions
        for g in group_by:
            if g not in grain_set:
                grain_set.add(g)
                result_grain.append(g)

        # Add non-aggregate SELECT expressions (dimensions)
        for item in select_items:
            if item.expr not in aggregate_exprs:
                if item.expr not in grain_set:
                    grain_set.add(item.expr)
                    result_grain.append(item.expr)

        return GroupingAnalysis(
            select=select_items,
            group_by=group_by,
            is_aggregated=is_aggregated,
            result_grain=result_grain,
            measures=measures,
        )

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze grouping: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing grouping: {e}") from e
