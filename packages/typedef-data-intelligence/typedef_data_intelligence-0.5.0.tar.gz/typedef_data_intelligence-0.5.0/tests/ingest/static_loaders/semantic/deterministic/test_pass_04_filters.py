from __future__ import annotations

from .helpers import run_filters


def test_pass_04_filters_excludes_cross_alias_predicates() -> None:
    sql = """
    SELECT *
    FROM a
    JOIN b ON a.id = b.id
    WHERE a.x = 1 AND a.id = b.id
    """
    _, _, _, filt = run_filters(sql)

    assert any(p == "a.x = 1" for p in filt.where)
    assert all("a.id = b.id" not in p for p in filt.where)


def test_pass_04_filters_excludes_non_equi_cross_alias_predicates_from_where() -> None:
    sql = """
    SELECT *
    FROM a, b
    WHERE a.x = 1
      AND a.id = b.id
      AND a.created_at >= b.start_time
      AND a.created_at <= b.end_time
    """
    _, _, joins, filt = run_filters(sql)

    # Single-table filters should remain
    assert any(p == "a.x = 1" for p in filt.where)
    # Cross-alias predicates should not appear in filters
    assert all("a.id = b.id" not in p for p in filt.where)
    assert all("a.created_at" not in p or "b." not in p for p in filt.where)

    # Join analysis should capture the equi + non-equi join semantics
    j = next((jj for jj in joins.joins if jj.left == "a" and jj.right == "b" and jj.type == "INNER"), None)
    assert j is not None
    assert "a.id = b.id" in (j.equi_condition or "")
    assert "a.created_at >= b.start_time" in (j.raw_condition or "")
    assert "a.created_at <= b.end_time" in (j.raw_condition or "")


def test_pass_04_filters_detects_null_killing_on_left_join_right_side() -> None:
    sql = """
    SELECT *
    FROM a
    LEFT JOIN b ON a.id = b.id
    WHERE b.flag = 1
    """
    _, _, _, filt = run_filters(sql)

    assert any("b.flag = 1" in p for p in filt.null_killing_on_outer)

