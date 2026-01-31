"""Pass 1: Relation Analysis using SQLGlot AST traversal.

Extracts tables, CTEs, subqueries, aliases, and scopes deterministically.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple

from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.ingest.static_loaders.semantic.models import (
    AliasMapping,
    RelationAnalysis,
    RelationUse,
    SelfJoinGroup,
)

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """Raised when deterministic analysis fails and should fallback to LLM."""

    pass


def _get_scope_label(node: exp.Expression, cte_names: Set[str]) -> str:
    """Determine the scope label for a node based on its ancestors.

    Args:
        node: The expression node to analyze
        cte_names: Set of CTE names defined in WITH clause

    Returns:
        Scope label: 'outer', 'cte:<name>', or 'subquery:<alias>'
    """
    # Walk up the tree to find enclosing scope
    current = node.parent
    while current:
        # Check if we're inside a CTE definition
        if isinstance(current, exp.CTE):
            cte_alias = current.alias
            if cte_alias:
                return f"cte:{cte_alias}"

        # Check if we're inside a subquery with an alias
        if isinstance(current, exp.Subquery):
            subquery_alias = current.alias
            if subquery_alias:
                return f"subquery:{subquery_alias}"

        # Check for derived table in FROM
        if isinstance(current, exp.From) and current.parent:
            # Check if parent select is itself a subquery
            parent_select = current.parent
            if isinstance(parent_select, exp.Select):
                grandparent = parent_select.parent
                if isinstance(grandparent, exp.Subquery) and grandparent.alias:
                    return f"subquery:{grandparent.alias}"

        current = current.parent

    return "outer"


def _extract_table_parts(
    table: exp.Table,
) -> Tuple[str, Optional[str], Optional[str]]:
    """Extract base name, schema, and catalog from a Table node.

    Returns:
        Tuple of (base_name, schema_name, catalog_name)
    """
    base = table.name
    schema_name = table.db if hasattr(table, "db") and table.db else None
    catalog = table.catalog if hasattr(table, "catalog") and table.catalog else None
    return base, schema_name, catalog


def _infer_kind(
    node: exp.Expression, cte_names: Set[str]
) -> str:
    """Infer the kind of relation based on context.

    Args:
        node: The expression node (Table, Subquery, etc.)
        cte_names: Set of CTE names defined in WITH clause

    Returns:
        One of: 'table', 'view', 'cte', 'subquery', 'table_function'
    """
    if isinstance(node, exp.Subquery):
        return "subquery"

    if isinstance(node, exp.Table):
        # Check if this is a CTE reference
        if node.name in cte_names:
            return "cte"

        # Check for table function (like UNNEST, LATERAL, etc.)
        parent = node.parent
        if isinstance(parent, (exp.Lateral, exp.Unnest)):
            return "table_function"

        # Default to table (could be view, but we can't distinguish without schema)
        return "table"

    if isinstance(node, (exp.Lateral, exp.Unnest)):
        return "table_function"

    return "table"


def _get_cte_names(ast: exp.Expression) -> Set[str]:
    """Extract all CTE names defined in WITH clauses.

    Args:
        ast: The parsed SQL expression

    Returns:
        Set of CTE names
    """
    cte_names: Set[str] = set()

    for with_clause in ast.find_all(exp.With):
        for cte in with_clause.expressions:
            if isinstance(cte, exp.CTE) and cte.alias:
                cte_names.add(cte.alias)

    return cte_names


def _extract_from_clause_order(select: exp.Select) -> List[str]:
    """Extract aliases from FROM clause in left-to-right order.

    This includes the FROM table and all explicit JOINs.

    Args:
        select: The SELECT expression

    Returns:
        List of aliases in order of appearance
    """
    order: List[str] = []

    from_clause = select.find(exp.From)
    if from_clause and from_clause.this:
        # Get the first table/subquery in FROM
        first_relation = from_clause.this
        alias = _get_relation_alias(first_relation)
        if alias:
            order.append(alias)

    # Get JOIN tables in order
    for join in select.find_all(exp.Join):
        if join.this:
            alias = _get_relation_alias(join.this)
            if alias:
                order.append(alias)

    return order


def _get_relation_alias(node: exp.Expression) -> Optional[str]:
    """Get the alias for a relation node, falling back to base name."""
    if isinstance(node, exp.Table):
        return node.alias or node.name
    elif isinstance(node, exp.Subquery):
        return node.alias
    elif isinstance(node, exp.CTE):
        return node.alias
    elif hasattr(node, "alias") and node.alias:
        return node.alias
    elif hasattr(node, "name") and node.name:
        return node.name
    return None


def analyze_relations(
    ast: exp.Expression,
    dialect: Optional[str] = None,
) -> RelationAnalysis:
    """Extract relations using SQLGlot AST traversal.

    Args:
        ast: Pre-parsed and optionally qualified SQL expression
        dialect: SQL dialect (for logging/debugging)

    Returns:
        RelationAnalysis with all relation metadata

    Raises:
        AnalysisError: If analysis fails and should fall back to LLM
    """
    try:
        cte_names = _get_cte_names(ast)
        relations: List[RelationUse] = []
        alias_to_base: Dict[str, str] = {}
        base_to_aliases: Dict[str, List[str]] = defaultdict(list)
        tables_seen: Set[str] = set()
        subquery_aliases: List[str] = []

        # Track which aliases we've seen to avoid duplicates
        seen_aliases: Set[str] = set()

        # Extract tables from FROM, JOIN, etc.
        for table in ast.find_all(exp.Table):
            base, schema_name, catalog = _extract_table_parts(table)
            alias = table.alias or base
            scope = _get_scope_label(table, cte_names)
            kind = _infer_kind(table, cte_names)

            # Skip if we've already seen this alias in this scope
            alias_scope_key = f"{alias}:{scope}"
            if alias_scope_key in seen_aliases:
                continue
            seen_aliases.add(alias_scope_key)

            tables_seen.add(base)
            alias_to_base[alias] = base
            base_to_aliases[base].append(alias)

            relations.append(
                RelationUse(
                    alias=alias,
                    base=base,
                    kind=kind,
                    scope=scope,
                    catalog=catalog,
                    schema_name=schema_name,
                    is_temp=False,  # Can't reliably detect without schema info
                    evidence=[],
                )
            )

        # Extract subqueries with aliases
        for subquery in ast.find_all(exp.Subquery):
            alias = subquery.alias
            if alias and alias not in seen_aliases:
                scope = _get_scope_label(subquery, cte_names)
                alias_scope_key = f"{alias}:{scope}"
                if alias_scope_key not in seen_aliases:
                    seen_aliases.add(alias_scope_key)
                    subquery_aliases.append(alias)
                    alias_to_base[alias] = "<subquery>"

                    relations.append(
                        RelationUse(
                            alias=alias,
                            base="<subquery>",
                            kind="subquery",
                            scope=scope,
                            catalog=None,
                            schema_name=None,
                            is_temp=False,
                            evidence=[],
                        )
                    )

        # Extract LATERAL table functions (e.g., LATERAL FLATTEN in Snowflake)
        # These create synthetic aliases like _flattened with columns VALUE, KEY, etc.
        for lateral in ast.find_all(exp.Lateral):
            alias = lateral.alias
            if alias:
                scope = _get_scope_label(lateral, cte_names)
                alias_scope_key = f"{alias}:{scope}"
                if alias_scope_key not in seen_aliases:
                    seen_aliases.add(alias_scope_key)
                    alias_to_base[alias] = "<lateral>"

                    relations.append(
                        RelationUse(
                            alias=alias,
                            base="<lateral>",
                            kind="table_function",
                            scope=scope,
                            catalog=None,
                            schema_name=None,
                            is_temp=False,
                            evidence=[],
                        )
                    )

        # Build alias mappings list
        alias_mappings = [
            AliasMapping(alias=alias, base=base)
            for alias, base in alias_to_base.items()
        ]

        # Build self-join groups (bases with multiple aliases)
        self_join_groups = [
            SelfJoinGroup(base=base, aliases=sorted(aliases))
            for base, aliases in base_to_aliases.items()
            if len(aliases) > 1
        ]

        # Extract driving relations and from_clause_order from outer SELECT
        driving_relations: List[str] = []
        from_clause_order: List[str] = []

        # Find the outermost SELECT (not in CTE or subquery)
        outer_select = None
        for select in ast.find_all(exp.Select):
            # Check if this SELECT is in outer scope
            scope = _get_scope_label(select, cte_names)
            if scope == "outer":
                outer_select = select
                break

        if outer_select:
            from_clause_order = _extract_from_clause_order(outer_select)
            # Driving relation is the first in FROM
            if from_clause_order:
                driving_relations = [from_clause_order[0]]

        return RelationAnalysis(
            relations=relations,
            alias_mappings=alias_mappings,
            driving_relations=driving_relations,
            from_clause_order=from_clause_order,
            self_join_groups=self_join_groups,
            subqueries=subquery_aliases,
            cte_defs=sorted(list(cte_names)),
            tables=sorted(list(tables_seen)),
        )

    except SqlglotError as e:
        raise AnalysisError(f"SQLGlot failed to analyze relations: {e}") from e
    except Exception as e:
        raise AnalysisError(f"Unexpected error analyzing relations: {e}") from e
