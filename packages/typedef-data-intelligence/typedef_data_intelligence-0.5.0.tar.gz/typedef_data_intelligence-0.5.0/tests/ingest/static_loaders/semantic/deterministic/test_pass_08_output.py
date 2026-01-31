from __future__ import annotations

from .helpers import run_output


def test_pass_08_output_order_limit_offset_and_distinct() -> None:
    sql = """
    SELECT DISTINCT *
    FROM t
    ORDER BY a DESC
    LIMIT 10
    OFFSET 5
    """
    out = run_output(sql)

    assert out.select_distinct is True
    assert out.limit == 10
    assert out.offset == 5
    assert out.order_by
    assert out.order_by[0].expr == "a"
    assert out.order_by[0].dir == "DESC"


def test_pass_08_output_extracts_set_ops() -> None:
    sql = """
    SELECT 1 AS x
    UNION ALL
    SELECT 2 AS x
    """
    out = run_output(sql)

    assert len(out.set_ops) == 1
    assert out.set_ops[0].op == "UNION ALL"


def test_pass_08_output_union_with_order_by_and_limit() -> None:
    """ORDER BY and LIMIT on UNION queries are attached to the Union node, not SELECT."""
    sql = """
    (SELECT 1 AS x)
    UNION ALL
    (SELECT 2 AS x)
    ORDER BY 1
    LIMIT 10
    """
    out = run_output(sql)

    assert len(out.set_ops) == 1
    assert out.set_ops[0].op == "UNION ALL"
    assert out.limit == 10
    assert len(out.order_by) == 1
    assert out.order_by[0].expr == "1"

