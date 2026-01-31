"""Pass 8: Output Shape Analysis using SQLGlot AST traversal.

Extracts output shape characteristics:
- ORDER BY with direction
- LIMIT and OFFSET
- SELECT DISTINCT
- Set operations (UNION, INTERSECT, EXCEPT)
"""

from __future__ import annotations

import logging
from typing import List, Optional

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
)
from lineage.ingest.static_loaders.semantic.models import (
    OrderByItem,
    OutputShapeAnalysis,
    SetOperation,
)

logger = logging.getLogger(__name__)


def _find_scope_select(ast: exp.Expression, scope: str) -> Optional[exp.Select]:
    """Find the SELECT statement for a given scope."""
    if scope == "outer":
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
    elif scope.startswith("cte:"):
        cte_name = scope[4:]
        for cte in ast.find_all(exp.CTE):
            if cte.alias == cte_name:
                return cte.find(exp.Select)
    elif scope.startswith("subquery:"):
        subquery_alias = scope[9:]
        for subquery in ast.find_all(exp.Subquery):
            if subquery.alias == subquery_alias:
                return subquery.find(exp.Select)

    return None


def _extract_order_by_items(expr: exp.Expression) -> List[OrderByItem]:
    """Extract ORDER BY items from an expression (SELECT, Union, etc.).

    Args:
        expr: The expression (SELECT, Union, Intersect, Except, etc.)

    Returns:
        List of OrderByItem with expression and direction
    """
    items: List[OrderByItem] = []

    order = expr.find(exp.Order)
    if order:
        for expr_item in order.expressions:
            # Check for Ordered expression with direction
            if isinstance(expr_item, exp.Ordered):
                expr_str = expr_item.this.sql(pretty=False)
                direction = "DESC" if expr_item.args.get("desc") else "ASC"
            else:
                expr_str = expr_item.sql(pretty=False)
                direction = "ASC"  # Default

            items.append(OrderByItem(expr=expr_str, dir=direction))

    return items


def _extract_limit(expr: exp.Expression) -> Optional[int]:
    """Extract LIMIT value from an expression (SELECT, Union, etc.).

    Args:
        expr: The expression (SELECT, Union, Intersect, Except, etc.)

    Returns:
        LIMIT value as integer, or None
    """
    limit = expr.find(exp.Limit)
    if limit and limit.expression:
        try:
            return int(limit.expression.this)
        except (ValueError, AttributeError):
            # Try direct value
            try:
                return int(str(limit.expression))
            except ValueError:
                return None
    return None


def _extract_offset(expr: exp.Expression) -> Optional[int]:
    """Extract OFFSET value from an expression (SELECT, Union, etc.).

    Args:
        expr: The expression (SELECT, Union, Intersect, Except, etc.)

    Returns:
        OFFSET value as integer, or None
    """
    offset = expr.find(exp.Offset)
    if offset and offset.expression:
        try:
            return int(offset.expression.this)
        except (ValueError, AttributeError):
            try:
                return int(str(offset.expression))
            except ValueError:
                return None
    return None


def _is_select_distinct(select: exp.Select) -> bool:
    """Check if SELECT uses DISTINCT.

    Args:
        select: The SELECT expression

    Returns:
        True if DISTINCT is present
    """
    distinct = select.args.get("distinct")
    return bool(distinct)


def _extract_set_operations(ast: exp.Expression) -> List[SetOperation]:
    """Extract set operations (UNION, INTERSECT, EXCEPT).

    Args:
        ast: The full AST

    Returns:
        List of SetOperation with type and position
    """
    operations: List[SetOperation] = []
    position = 1

    # Look for Union, Intersect, Except at the top level
    for node in ast.find_all(exp.Union):
        distinct = node.args.get("distinct") is not False
        op_name = "UNION" if distinct else "UNION ALL"
        operations.append(SetOperation(op=op_name, position=position))
        position += 1

    for node in ast.find_all(exp.Intersect):
        distinct = node.args.get("distinct") is not False
        op_name = "INTERSECT" if distinct else "INTERSECT ALL"
        operations.append(SetOperation(op=op_name, position=position))
        position += 1

    for node in ast.find_all(exp.Except):
        distinct = node.args.get("distinct") is not False
        op_name = "EXCEPT" if distinct else "EXCEPT ALL"
        operations.append(SetOperation(op=op_name, position=position))
        position += 1

    return operations


def analyze_output(
    ast: exp.Expression,
    scope: str = "outer",
    dialect: Optional[str] = None,
) -> OutputShapeAnalysis:
    """Extract output shape characteristics for a specific scope.

    Args:
        ast: Pre-parsed SQL expression
        scope: The scope to analyze ('outer', 'cte:<name>', 'subquery:<alias>')
        dialect: SQL dialect (for logging/debugging)

    Returns:
        OutputShapeAnalysis with order, limit, distinct, and set operations

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        # For outer scope, check if the root is a set operation (Union/Intersect/Except)
        # In that case, ORDER BY and LIMIT are attached to the Union node, not a SELECT
        if scope == "outer" and isinstance(ast, (exp.Union, exp.Intersect, exp.Except)):
            # Extract ORDER BY, LIMIT, OFFSET from the Union node
            order_by = _extract_order_by_items(ast)
            limit = _extract_limit(ast)
            offset = _extract_offset(ast)
            # DISTINCT on UNION branches is different from DISTINCT on UNION result
            # For now, we don't extract DISTINCT from UNION branches
            select_distinct = False
            # Extract set operations
            set_ops = _extract_set_operations(ast)

            return OutputShapeAnalysis(
                order_by=order_by,
                limit=limit,
                offset=offset,
                select_distinct=select_distinct,
                set_ops=set_ops,
            )

        # Find the SELECT for this scope
        target_select = _find_scope_select(ast, scope)

        if not target_select:
            return OutputShapeAnalysis(
                order_by=[],
                limit=None,
                offset=None,
                select_distinct=False,
                set_ops=[],
            )

        # Extract components from SELECT
        order_by = _extract_order_by_items(target_select)
        limit = _extract_limit(target_select)
        offset = _extract_offset(target_select)
        select_distinct = _is_select_distinct(target_select)

        # Set operations are at the AST level, not per-scope
        set_ops = _extract_set_operations(ast) if scope == "outer" else []

        return OutputShapeAnalysis(
            order_by=order_by,
            limit=limit,
            offset=offset,
            select_distinct=select_distinct,
            set_ops=set_ops,
        )

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze output: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing output: {e}") from e
