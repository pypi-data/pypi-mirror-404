"""Pass 2: Column Analysis using SQLGlot AST traversal.

Extracts column references and builds allow-lists for each relation.
Handles qualified (table.column) and unqualified (column) references.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.deterministic.graph_enrichment import (
    RelationHint,
)
from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
)
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    ColumnRef,
    ColumnsByAlias,
    RelationAnalysis,
)

logger = logging.getLogger(__name__)


def _get_scope_label(node: exp.Expression, cte_names: Set[str]) -> str:
    """Determine the scope label for a node based on its ancestors."""
    current = node.parent
    while current:
        if isinstance(current, exp.CTE):
            cte_alias = current.alias
            if cte_alias:
                return f"cte:{cte_alias}"

        if isinstance(current, exp.Subquery):
            subquery_alias = current.alias
            if subquery_alias:
                return f"subquery:{subquery_alias}"

        current = current.parent

    return "outer"


def _get_cte_names(ast: exp.Expression) -> Set[str]:
    """Extract all CTE names from WITH clauses."""
    cte_names: Set[str] = set()
    for with_clause in ast.find_all(exp.With):
        for cte in with_clause.expressions:
            if isinstance(cte, exp.CTE) and cte.alias:
                cte_names.add(cte.alias)
    return cte_names


def _extract_pivot_columns(ast: exp.Expression) -> Dict[str, Set[str]]:
    """Extract synthetic columns created by PIVOT/UNPIVOT operations.

    Returns a mapping of table alias -> set of synthetic column names.

    UNPIVOT creates:
    - A value column (from expressions)
    - A name column (from the FOR clause)

    PIVOT creates dynamic columns based on the pivot values.
    """
    pivot_columns: Dict[str, Set[str]] = defaultdict(set)

    for pivot in ast.find_all(exp.Pivot):
        # Find the table this pivot is attached to
        parent = pivot.parent
        table_alias = None
        if isinstance(parent, exp.Table):
            table_alias = parent.alias or parent.name

        if pivot.args.get("unpivot"):
            # UNPIVOT: extract value column(s) and name column
            # Value column(s) - from expressions
            for expr in pivot.expressions:
                if isinstance(expr, exp.Column):
                    col_name = expr.name
                    if table_alias:
                        pivot_columns[table_alias].add(col_name)
                    # Also add without alias for unqualified reference resolution
                    pivot_columns["__synthetic__"].add(col_name)

            # Name column - from the IN clause (FOR <name> IN (...))
            in_expr = pivot.find(exp.In)
            if in_expr:
                name_col = in_expr.this
                if isinstance(name_col, exp.Column):
                    col_name = name_col.name
                    if table_alias:
                        pivot_columns[table_alias].add(col_name)
                    pivot_columns["__synthetic__"].add(col_name)

    return pivot_columns


def _extract_pivot_input_columns(ast: exp.Expression) -> Set[str]:
    """Extract columns that are consumed by UNPIVOT (become values, not columns).

    These columns appear in the IN clause and are transformed into values,
    not available as columns after the UNPIVOT operation.
    """
    consumed_columns: Set[str] = set()

    for pivot in ast.find_all(exp.Pivot):
        if pivot.args.get("unpivot"):
            in_expr = pivot.find(exp.In)
            if in_expr:
                for col in in_expr.expressions:
                    if isinstance(col, exp.Column):
                        consumed_columns.add(col.name)

    return consumed_columns


def _extract_lateral_columns(ast: exp.Expression) -> Dict[str, Set[str]]:
    """Extract synthetic columns created by LATERAL table functions.

    Snowflake's LATERAL FLATTEN creates columns: SEQ, KEY, PATH, INDEX, VALUE, THIS
    These are exposed via the TableAlias columns attribute.

    Returns a mapping of lateral alias -> set of synthetic column names.
    """
    lateral_columns: Dict[str, Set[str]] = defaultdict(set)

    for lateral in ast.find_all(exp.Lateral):
        alias = lateral.alias
        if not alias:
            continue

        # SQLGlot parses the output columns into the TableAlias
        table_alias = lateral.args.get("alias")
        if isinstance(table_alias, exp.TableAlias):
            # Get column names from the TableAlias columns list
            for col in table_alias.columns:
                if hasattr(col, "name"):
                    lateral_columns[alias].add(col.name)

        # If no columns defined, add standard Snowflake FLATTEN columns
        if not lateral_columns[alias]:
            # Standard columns from Snowflake FLATTEN
            lateral_columns[alias].update(
                {"SEQ", "KEY", "PATH", "INDEX", "VALUE", "THIS"}
            )

    return lateral_columns


def _extract_subquery_projections(subquery: exp.Subquery) -> Set[str]:
    """Extract projected column names from a subquery.

    Returns the output column names (aliases) that the subquery exposes.
    """
    projections: Set[str] = set()

    # Find the SELECT inside the subquery
    select = subquery.find(exp.Select)
    if not select:
        return projections

    for projection in select.expressions:
        # Get the output name (alias or column name)
        if hasattr(projection, "alias") and projection.alias:
            projections.add(projection.alias)
        elif isinstance(projection, exp.Column):
            projections.add(projection.name)
        elif hasattr(projection, "name") and projection.name:
            projections.add(projection.name)
        elif isinstance(projection, exp.Star):
            # Can't resolve * without schema
            pass

    return projections


def _candidate_schema_bases(
    base: str,
    hint: Optional[RelationHint],
) -> List[str]:
    """Generate candidate table names for schema lookup."""
    candidates: List[str] = []
    if base:
        candidates.append(base)
        if "." in base:
            candidates.append(base.split(".")[-1])
    if hint and hint.physical_fqn:
        candidates.append(hint.physical_fqn)
        if "." in hint.physical_fqn:
            candidates.append(hint.physical_fqn.split(".")[-1])
    # Deduplicate while preserving order
    seen: Set[str] = set()
    out: List[str] = []
    for c in candidates:
        if not c:
            continue
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _get_containing_select_table(column: exp.Column) -> Optional[str]:
    """Find the single table in the FROM clause of the column's containing SELECT.

    This is used as a fallback for UNION branches where the table isn't in the schema.
    If the SELECT has exactly one table (no joins), we can safely attribute the column
    to that table.

    Args:
        column: The Column expression to analyze

    Returns:
        The table alias/name if exactly one table in FROM, None otherwise
    """
    # Walk up to find the containing SELECT
    parent = column.parent
    containing_select = None
    while parent:
        if isinstance(parent, exp.Select):
            containing_select = parent
            break
        parent = parent.parent

    if not containing_select:
        return None

    # Check if this SELECT has exactly one table and no joins
    from_clause = containing_select.find(exp.From)
    if not from_clause or not from_clause.this:
        return None

    # Check for any joins - if there are joins, we can't safely resolve
    joins = list(containing_select.find_all(exp.Join))
    if joins:
        return None

    # Get the single table
    if isinstance(from_clause.this, exp.Table):
        return from_clause.this.alias or from_clause.this.name

    return None


def _resolve_unqualified_column(
    column_name: str,
    scope_aliases: Set[str],
    alias_to_columns: Dict[str, Set[str]],
    column_node: Optional[exp.Column] = None,
) -> Optional[str]:
    """Try to resolve an unqualified column to a single alias.

    Args:
        column_name: The unqualified column name
        scope_aliases: Aliases valid in the current scope
        alias_to_columns: Known columns for each alias (from schema or previous analysis)
        column_node: Optional Column expression for fallback resolution

    Returns:
        The alias if uniquely resolved, None if ambiguous or not found
    """
    # If we have column info, try to find a unique match
    # Use case-insensitive comparison for Snowflake compatibility
    column_upper = column_name.upper()
    matches = []
    for alias in scope_aliases:
        if alias in alias_to_columns:
            # Check both exact match and case-insensitive match
            if column_name in alias_to_columns[alias]:
                matches.append(alias)
            elif column_upper in {c.upper() for c in alias_to_columns[alias]}:
                matches.append(alias)

    if len(matches) == 1:
        return matches[0]

    # Fallback: If no matches from schema and we have the column node,
    # try to resolve via the containing SELECT's single FROM table.
    # This handles UNION branches where source tables aren't in the schema.
    if len(matches) == 0 and column_node is not None:
        single_table = _get_containing_select_table(column_node)
        if single_table and single_table in scope_aliases:
            return single_table

    return None


def analyze_columns(
    ast: exp.Expression,
    relation_analysis: RelationAnalysis,
    schema: Optional[Dict] = None,
    dialect: Optional[str] = None,  # noqa: ARG001 - reserved for future logging
    relation_hints: Optional[Dict[str, RelationHint]] = None,
) -> ColumnAnalysis:
    """Extract column references from SQL using AST traversal.

    Args:
        ast: Pre-parsed and optionally qualified SQL expression
        relation_analysis: Output from analyze_relations()
        schema: Optional SQLGlot-compatible schema for column resolution
        dialect: SQL dialect (for logging/debugging)
        relation_hints: Optional graph-derived hints for relation resolution

    Returns:
        ColumnAnalysis with column references and allow-lists

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        cte_names = _get_cte_names(ast)

        # Build alias → base mapping from relation analysis
        alias_to_base = {am.alias: am.base for am in relation_analysis.alias_mappings}

        # Build scope → aliases mapping
        scope_to_aliases: Dict[str, Set[str]] = defaultdict(set)
        for rel in relation_analysis.relations:
            scope_to_aliases[rel.scope].add(rel.alias)

        # Extract PIVOT/UNPIVOT synthetic columns
        pivot_columns = _extract_pivot_columns(ast)
        pivot_input_columns = _extract_pivot_input_columns(ast)
        synthetic_columns = pivot_columns.get("__synthetic__", set())

        # Extract LATERAL table function columns (e.g., Snowflake FLATTEN)
        lateral_columns = _extract_lateral_columns(ast)

        # Collect columns by alias and scope
        alias_scope_columns: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        column_refs: List[ColumnRef] = []
        unresolved_unqualified: List[str] = []

        # Build schema-based column info if available
        alias_to_schema_columns: Dict[str, Set[str]] = defaultdict(set)
        if schema:
            for rel in relation_analysis.relations:
                base = alias_to_base.get(rel.alias, rel.base)
                hint = None
                if relation_hints:
                    hint = relation_hints.get(rel.alias) or relation_hints.get(base)
                base_candidates = _candidate_schema_bases(base, hint)
                # Navigate schema structure: {catalog: {schema: {table: {col: type}}}}
                for catalog_data in schema.values():
                    if not isinstance(catalog_data, dict):
                        continue
                    for schema_data in catalog_data.values():
                        if not isinstance(schema_data, dict):
                            continue
                        for candidate in base_candidates:
                            if candidate in schema_data:
                                cols = schema_data[candidate]
                                alias_to_schema_columns[rel.alias].update(
                                    cols.keys()
                                )

        # Add PIVOT/UNPIVOT synthetic columns to the schema columns for each alias
        for alias, pivot_cols in pivot_columns.items():
            if alias != "__synthetic__":
                alias_to_schema_columns[alias].update(pivot_cols)

        # Add LATERAL table function columns to the schema columns
        for alias, lat_cols in lateral_columns.items():
            alias_to_schema_columns[alias].update(lat_cols)

        # Extract column references
        for column in ast.find_all(exp.Column):
            column_name = column.name
            table_ref = column.table  # May be None for unqualified

            scope = _get_scope_label(column, cte_names)
            valid_aliases = scope_to_aliases.get(scope, set())

            if table_ref:
                # Qualified column: table.column
                alias = table_ref
                if alias in valid_aliases or alias in alias_to_base:
                    alias_scope_columns[alias][scope].add(column_name)
                    column_refs.append(
                        ColumnRef(
                            alias=alias,
                            column=column_name,
                            scope=scope,
                            evidence=None,
                        )
                    )
            else:
                # Unqualified column - try to resolve
                resolved_alias = _resolve_unqualified_column(
                    column_name,
                    valid_aliases,
                    alias_to_schema_columns,
                    column_node=column,
                )

                if resolved_alias:
                    alias_scope_columns[resolved_alias][scope].add(column_name)
                    column_refs.append(
                        ColumnRef(
                            alias=resolved_alias,
                            column=column_name,
                            scope=scope,
                            evidence=None,
                        )
                    )
                elif column_name in synthetic_columns:
                    # Synthetic column from PIVOT/UNPIVOT - mark as resolved to synthetic source
                    # Don't add to unresolved since we know where it comes from
                    pass
                elif column_name in pivot_input_columns:
                    # Column consumed by UNPIVOT - these become values, not columns
                    # Don't add to unresolved since this is expected behavior
                    pass
                elif scope == "outer":
                    # Only track unresolved for outer scope
                    if column_name not in unresolved_unqualified:
                        unresolved_unqualified.append(column_name)

        # Extract subquery projections for subquery aliases
        for subquery in ast.find_all(exp.Subquery):
            if subquery.alias:
                projections = _extract_subquery_projections(subquery)
                parent_scope = _get_scope_label(subquery, cte_names)
                for proj in projections:
                    alias_scope_columns[subquery.alias][parent_scope].add(proj)

        # Build columns_by_alias list
        columns_by_alias: List[ColumnsByAlias] = []
        all_aliases = set(alias_scope_columns.keys())

        for alias in sorted(all_aliases):
            # Merge columns from all scopes for this alias
            all_columns: Set[str] = set()
            for scope_cols in alias_scope_columns[alias].values():
                all_columns.update(scope_cols)

            if all_columns:
                columns_by_alias.append(
                    ColumnsByAlias(
                        alias=alias,
                        columns=sorted(list(all_columns)),
                    )
                )

        return ColumnAnalysis(
            columns_by_alias=columns_by_alias,
            column_refs=column_refs,
            unresolved_unqualified=unresolved_unqualified,
        )

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze columns: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing columns: {e}") from e
