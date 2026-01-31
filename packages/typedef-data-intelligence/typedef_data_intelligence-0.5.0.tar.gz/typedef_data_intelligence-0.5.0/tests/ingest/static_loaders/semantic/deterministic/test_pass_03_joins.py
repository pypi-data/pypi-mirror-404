from __future__ import annotations

from lineage.ingest.static_loaders.semantic.models import JoinClause, JoinEdgeAnalysis

from .helpers import run_joins


def _find_join(
    joins: JoinEdgeAnalysis,
    *,
    left: str,
    right: str,
    type_: str | None = None,
) -> JoinClause | None:
    for j in joins.joins:
        if j.left == left and j.right == right and (type_ is None or j.type == type_):
            return j
    return None


def test_pass_03_joins_extracts_inner_join_condition_and_orders_sides() -> None:
    sql = """
    SELECT *
    FROM b bb
    JOIN a aa ON bb.id = aa.id
    """
    _, _, joins = run_joins(sql)

    j = _find_join(joins, left="bb", right="aa", type_="INNER")
    assert j is not None
    assert "bb.id = aa.id" in j.equi_condition


def test_pass_03_joins_extracts_joins_inside_cte_bodies() -> None:
    sql = """
    WITH c AS (
      SELECT *
      FROM a
      JOIN b ON a.id = b.id
    )
    SELECT * FROM c
    """
    _, _, joins = run_joins(sql)

    # Ensure we don't regress to "outer-only join extraction".
    assert any(j.left == "a" and j.right == "b" and j.type == "INNER" for j in joins.joins)


def test_pass_03_joins_supports_using_clause() -> None:
    sql = """
    SELECT *
    FROM a
    JOIN b USING (id)
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="INNER")
    assert j is not None
    assert "a.id = b.id" in j.equi_condition


def test_pass_03_joins_supports_cast_wrapped_equijoins() -> None:
    sql = """
    SELECT *
    FROM a
    JOIN b ON CAST(a.id AS VARCHAR) = b.id
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="INNER")
    assert j is not None
    assert "a.id = b.id" in j.equi_condition


def test_pass_03_joins_treats_missing_on_as_cross_for_inner_join() -> None:
    sql = """
    SELECT *
    FROM a
    CROSS JOIN b
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="CROSS")
    assert j is not None
    assert j.equi_condition.strip() == ""


def test_pass_03_joins_keeps_natural_join_as_inner() -> None:
    sql = """
    SELECT *
    FROM a
    NATURAL JOIN b
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="INNER")
    assert j is not None
    assert j.equi_condition.strip() == ""


def test_pass_03_joins_keeps_natural_left_join_as_left() -> None:
    sql = """
    SELECT *
    FROM a
    NATURAL LEFT JOIN b
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="LEFT")
    assert j is not None
    assert j.equi_condition.strip() == ""


def test_pass_03_joins_populates_raw_condition_for_non_equi_join() -> None:
    sql = """
    SELECT *
    FROM a
    LEFT JOIN b ON COALESCE(a.id, a.alt_id) = b.id
    """
    _, _, joins = run_joins(sql)
    j = _find_join(joins, left="a", right="b", type_="LEFT")
    assert j is not None
    # equi-only condition should be empty (COALESCE wrapper is non-equi per schema)
    assert j.equi_condition.strip() == ""
    assert "COALESCE" in (j.raw_condition or "")

