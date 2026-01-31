"""Extract implicit source dependencies from compiled SQL.

dbt models using dynamic SQL generation (e.g., dbt_utils.get_relations_by_pattern(),
dbt_utils.union_relations()) bypass dbt's {{ source() }} macro. This means the
manifest's depends_on_sources is empty or incomplete.

This module parses compiled SQL to extract table references and identifies
sources not explicitly declared in depends_on_sources.

Usage:
    source_lookup = build_source_lookup(artifacts)
    for model in artifacts.iter_models():
        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect)
        for dep in implicit_deps:
            # Create DEPENDS_ON edge with inferred=True
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from lineage.ingest.static_loaders.dbt.dbt_loader import DbtArtifacts, DbtModelNode
from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
    analyze_relations,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ImplicitDependency:
    """Represents an implicit source dependency extracted from SQL.

    Attributes:
        source_id: The unique_id of the DbtSource (e.g., "source.project.schema.table")
        schema_name: The schema name used in the SQL
        table_name: The table name used in the SQL
    """

    source_id: str
    schema_name: Optional[str]
    table_name: str


def build_source_lookup(artifacts: DbtArtifacts) -> Dict[str, str]:
    """Build a lookup from {schema.table} -> source_unique_id.

    This creates multiple lookup keys for each source to maximize matching:
    - schema.identifier (primary key for matching compiled SQL)
    - identifier (fallback for unqualified references)

    Args:
        artifacts: DbtArtifacts instance containing sources

    Returns:
        Dictionary mapping normalized relation keys to source unique_ids.
        Keys are lowercase for case-insensitive matching.
    """
    lookup: Dict[str, str] = {}

    for source in artifacts.iter_sources():
        # Primary: schema.identifier (most common in compiled SQL)
        if source.schema and source.identifier:
            key = f"{source.schema}.{source.identifier}".lower()
            lookup[key] = source.unique_id

        # Secondary: just identifier (for unqualified references)
        if source.identifier:
            # Only add if not already present (avoid overwriting schema-qualified)
            identifier_key = source.identifier.lower()
            if identifier_key not in lookup:
                lookup[identifier_key] = source.unique_id

        # Also add database.schema.identifier for fully qualified refs
        if source.database and source.schema and source.identifier:
            fq_key = f"{source.database}.{source.schema}.{source.identifier}".lower()
            lookup[fq_key] = source.unique_id

    return lookup


def extract_implicit_source_deps(
    model: DbtModelNode,
    source_lookup: Dict[str, str],
    dialect: Optional[str] = None,
) -> List[ImplicitDependency]:
    """Extract implicit source dependencies from a model's compiled SQL.

    Parses the compiled SQL to find table references and matches them against
    known sources. Returns only dependencies that are NOT already in the model's
    explicit depends_on_sources.

    Args:
        model: DbtModelNode with compiled_sql
        source_lookup: Mapping from {schema.table} -> source_unique_id
        dialect: SQL dialect for parsing

    Returns:
        List of ImplicitDependency objects for sources found in SQL but not
        declared in depends_on_sources
    """
    if not model.compiled_sql:
        return []

    # Get explicit source deps to avoid duplicates
    explicit_source_ids: Set[str] = set(model.depends_on_sources or [])

    try:
        # Parse compiled SQL (uses cached AST)
        ast = parse_sql_cached(model.compiled_sql, dialect)

        # Analyze relations to get table references
        relation_analysis = analyze_relations(ast, dialect)

    except AnalysisError as e:
        logger.debug(
            f"Failed to analyze relations for implicit deps in {model.unique_id}: {e}"
        )
        return []
    except Exception as e:
        logger.debug(
            f"Unexpected error extracting implicit deps from {model.unique_id}: {e}"
        )
        return []

    implicit_deps: List[ImplicitDependency] = []
    seen_source_ids: Set[str] = set()

    for relation in relation_analysis.relations:
        # Skip non-table relations (CTEs, subqueries, table functions)
        if relation.kind != "table":
            continue

        # Build lookup keys to try (in order of specificity)
        keys_to_try: List[str] = []

        # Try catalog.schema.table for fully qualified (most specific)
        if relation.catalog and relation.schema_name and relation.base:
            keys_to_try.append(
                f"{relation.catalog}.{relation.schema_name}.{relation.base}".lower()
            )

        # Try schema.table next
        if relation.schema_name and relation.base:
            keys_to_try.append(f"{relation.schema_name}.{relation.base}".lower())

        # Try just table name as fallback
        if relation.base:
            keys_to_try.append(relation.base.lower())

        # Try to match against source lookup
        for key in keys_to_try:
            source_id = source_lookup.get(key)
            if source_id:
                # Skip if already explicit or already found
                if source_id in explicit_source_ids:
                    break
                if source_id in seen_source_ids:
                    break

                # Found an implicit dependency
                seen_source_ids.add(source_id)
                implicit_deps.append(
                    ImplicitDependency(
                        source_id=source_id,
                        schema_name=relation.schema_name,
                        table_name=relation.base,
                    )
                )
                break  # Found a match, no need to try other keys

    if implicit_deps:
        logger.debug(
            f"Found {len(implicit_deps)} implicit source deps for {model.unique_id}: "
            f"{[d.source_id for d in implicit_deps]}"
        )

    return implicit_deps
