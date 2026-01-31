from __future__ import annotations

from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    ColumnRef,
    ColumnsByAlias,
)

from .helpers import run_columns


def _has_column_ref(cols: ColumnAnalysis, *, alias: str, column: str, scope: str = "outer") -> bool:
    return any(
        isinstance(cr, ColumnRef)
        and cr.alias == alias
        and cr.column == column
        and cr.scope == scope
        for cr in cols.column_refs
    )


def _columns_for_alias(cols: ColumnAnalysis, alias: str) -> set[str]:
    for cba in cols.columns_by_alias:
        if isinstance(cba, ColumnsByAlias) and cba.alias == alias:
            return set(cba.columns)
    return set()


def test_pass_02_columns_unqualified_resolves_for_single_table_select() -> None:
    sql = "SELECT id FROM a"
    _, cols = run_columns(sql)

    assert cols.unresolved_unqualified == []
    assert _has_column_ref(cols, alias="a", column="id")


def test_pass_02_columns_unqualified_is_unresolved_when_ambiguous() -> None:
    sql = """
    SELECT id
    FROM a
    JOIN b ON a.id = b.id
    """
    _, cols = run_columns(sql)

    assert "id" in cols.unresolved_unqualified


def test_pass_02_columns_subquery_projections_are_exposed_on_subquery_alias() -> None:
    sql = """
    SELECT s.x, s.b
    FROM (SELECT a AS x, b FROM t) s
    """
    _, cols = run_columns(sql)

    assert {"x", "b"} <= _columns_for_alias(cols, "s")

