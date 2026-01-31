"""Pass 7: Window Analysis using SQLGlot AST traversal.

Extracts window function specifications including:
- Function calls with OVER clause
- PARTITION BY expressions
- ORDER BY expressions
- Frame specifications
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
    WindowAnalysis,
    WindowSpec,
)

logger = logging.getLogger(__name__)


def _extract_partition_by(window: exp.Window) -> List[str]:
    """Extract PARTITION BY expressions from a window specification.

    Args:
        window: The Window expression

    Returns:
        List of PARTITION BY expressions as strings
    """
    partition_by: List[str] = []

    partition = window.args.get("partition_by")
    if partition:
        if isinstance(partition, list):
            for expr in partition:
                partition_by.append(expr.sql(pretty=False))
        else:
            partition_by.append(partition.sql(pretty=False))

    return partition_by


def _extract_order_by(window: exp.Window) -> List[str]:
    """Extract ORDER BY expressions from a window specification.

    Includes direction (ASC/DESC) and NULLS FIRST/LAST if present.

    Args:
        window: The Window expression

    Returns:
        List of ORDER BY expressions as strings
    """
    order_by: List[str] = []

    order = window.args.get("order")
    if order:
        if isinstance(order, exp.Order):
            for expr in order.expressions:
                order_by.append(expr.sql(pretty=False))
        elif isinstance(order, list):
            for expr in order:
                order_by.append(expr.sql(pretty=False))
        else:
            order_by.append(order.sql(pretty=False))

    return order_by


def _extract_frame(window: exp.Window) -> str:
    """Extract frame specification from a window.

    Args:
        window: The Window expression

    Returns:
        Frame specification as string, or empty if not present
    """
    # Check for various frame-related args
    spec = window.args.get("spec")
    if spec:
        return spec.sql(pretty=False)

    # Check for rows/range specification
    rows = window.args.get("rows")
    if rows:
        return f"ROWS {rows.sql(pretty=False)}"

    range_spec = window.args.get("range")
    if range_spec:
        return f"RANGE {range_spec.sql(pretty=False)}"

    return ""


def _find_scope_select(ast: exp.Expression, scope: str) -> Optional[exp.Select]:
    """Find the SELECT statement for a given scope.

    Args:
        ast: The full AST
        scope: Scope label ('outer', 'cte:<name>', 'subquery:<alias>')

    Returns:
        The SELECT for this scope, or None
    """
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


def analyze_windows(
    ast: exp.Expression,
    scope: str = "outer",
    dialect: Optional[str] = None,
) -> WindowAnalysis:
    """Extract window function specifications for a specific scope.

    Args:
        ast: Pre-parsed SQL expression
        scope: The scope to analyze ('outer', 'cte:<name>', 'subquery:<alias>')
        dialect: SQL dialect (for logging/debugging)

    Returns:
        WindowAnalysis with window specifications

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        windows: List[WindowSpec] = []

        # Find the SELECT for this scope
        target_select = _find_scope_select(ast, scope)
        if not target_select:
            return WindowAnalysis(windows=[])

        # Find all Window expressions in this SELECT
        for window in target_select.find_all(exp.Window):
            # Check this window belongs to this scope (not nested)
            parent = window.parent
            in_nested = False
            while parent and parent != target_select:
                if isinstance(parent, (exp.Subquery, exp.CTE)):
                    in_nested = True
                    break
                parent = parent.parent

            if in_nested and scope == "outer":
                continue

            # Get the function expression
            func_expr = window.this
            func_str = func_expr.sql(pretty=False) if func_expr else ""

            # Extract window specification
            partition_by = _extract_partition_by(window)
            order_by = _extract_order_by(window)
            frame = _extract_frame(window)

            windows.append(
                WindowSpec(
                    func=func_str,
                    partition_by=partition_by,
                    order_by=order_by,
                    frame=frame,
                )
            )

        return WindowAnalysis(windows=windows)

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze windows: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing windows: {e}") from e
