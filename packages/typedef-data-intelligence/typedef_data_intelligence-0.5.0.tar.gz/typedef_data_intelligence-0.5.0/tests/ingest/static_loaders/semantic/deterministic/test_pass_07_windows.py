from __future__ import annotations

from .helpers import run_windows


def test_pass_07_windows_row_number_partition_and_order() -> None:
    sql = """
    SELECT ROW_NUMBER() OVER (PARTITION BY a ORDER BY b) AS rn
    FROM t
    """
    win = run_windows(sql)

    assert len(win.windows) == 1
    w = win.windows[0]
    assert w.func == "ROW_NUMBER()"
    assert w.partition_by == ["a"]
    # SQLGlot may append default NULLS LAST/FIRST depending on dialect.
    assert len(w.order_by) == 1
    assert w.order_by[0].startswith("b")

