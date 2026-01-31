"""Test helpers for deterministic semantic pass-level tests.

These helpers intentionally run the minimum prerequisite passes needed for a given
assertion (a "slice test"), rather than snapshotting entire pipeline outputs.
"""

from __future__ import annotations

from lineage.ingest.static_loaders.semantic.deterministic import (
    analyze_columns,
    analyze_filters,
    analyze_grouping,
    analyze_joins,
    analyze_output,
    analyze_relations,
    analyze_windows,
)
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    FilterAnalysis,
    GroupingAnalysis,
    JoinEdgeAnalysis,
    OutputShapeAnalysis,
    RelationAnalysis,
    WindowAnalysis,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached
from sqlglot import exp


def parse(sql: str, *, dialect: str = "duckdb") -> exp.Expression:
    """Parse SQL to a SQLGlot AST using the project's cached parser."""
    return parse_sql_cached(sql, dialect)


def run_relations(sql: str, *, dialect: str = "duckdb") -> RelationAnalysis:
    """Run Pass 1 (relations) only."""
    ast = parse(sql, dialect=dialect)
    return analyze_relations(ast, dialect)


def run_columns(sql: str, *, dialect: str = "duckdb") -> tuple[RelationAnalysis, ColumnAnalysis]:
    """Run Pass 1 + Pass 2 (relations + columns)."""
    ast = parse(sql, dialect=dialect)
    rel = analyze_relations(ast, dialect)
    cols = analyze_columns(ast, rel, schema=None, dialect=dialect)
    return rel, cols


def run_joins(
    sql: str, *, dialect: str = "duckdb"
) -> tuple[RelationAnalysis, ColumnAnalysis, JoinEdgeAnalysis]:
    """Run Pass 1–3 (relations + columns + joins)."""
    ast = parse(sql, dialect=dialect)
    rel = analyze_relations(ast, dialect)
    cols = analyze_columns(ast, rel, schema=None, dialect=dialect)
    joins = analyze_joins(ast, rel, cols, dialect)
    return rel, cols, joins


def run_filters(
    sql: str, *, dialect: str = "duckdb"
) -> tuple[RelationAnalysis, ColumnAnalysis, JoinEdgeAnalysis, FilterAnalysis]:
    """Run Pass 1–4 (relations + columns + joins + filters)."""
    ast = parse(sql, dialect=dialect)
    rel = analyze_relations(ast, dialect)
    cols = analyze_columns(ast, rel, schema=None, dialect=dialect)
    joins = analyze_joins(ast, rel, cols, dialect)
    filt = analyze_filters(ast, rel, cols, joins, dialect)
    return rel, cols, joins, filt


def run_grouping(
    sql: str, *, dialect: str = "duckdb", scope: str = "outer"
) -> tuple[RelationAnalysis, ColumnAnalysis, GroupingAnalysis]:
    """Run Pass 1 + Pass 2 + Pass 5 for a given scope."""
    ast = parse(sql, dialect=dialect)
    rel = analyze_relations(ast, dialect)
    cols = analyze_columns(ast, rel, schema=None, dialect=dialect)
    grouping = analyze_grouping(ast, rel, cols, scope, dialect)
    return rel, cols, grouping


def run_windows(sql: str, *, dialect: str = "duckdb", scope: str = "outer") -> WindowAnalysis:
    """Run Pass 7 (windows) for a given scope."""
    ast = parse(sql, dialect=dialect)
    return analyze_windows(ast, scope, dialect)


def run_output(sql: str, *, dialect: str = "duckdb", scope: str = "outer") -> OutputShapeAnalysis:
    """Run Pass 8 (output shape) for a given scope."""
    ast = parse(sql, dialect=dialect)
    return analyze_output(ast, scope, dialect)

