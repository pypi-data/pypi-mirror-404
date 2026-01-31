from __future__ import annotations

from .helpers import run_grouping


def test_pass_05_grouping_windowed_sum_is_not_an_aggregate() -> None:
    sql = """
    SELECT SUM(x) OVER (PARTITION BY y) AS s
    FROM t
    """
    _, _, grouping = run_grouping(sql)

    assert grouping.is_aggregated is False
    assert grouping.measures == []
    assert grouping.select
    # Window functions are not aggregates, so this should be in result_grain
    assert "SUM(x) OVER (PARTITION BY y)" in grouping.result_grain


def test_pass_05_grouping_group_by_is_aggregated_and_extracts_measures() -> None:
    sql = """
    SELECT a, COUNT(*) AS cnt
    FROM t
    GROUP BY a
    """
    _, _, grouping = run_grouping(sql)

    assert grouping.is_aggregated is True
    assert "COUNT(*)" in grouping.measures
    assert "a" in grouping.group_by


def test_pass_05_grouping_parenthesized_union_has_outer_select() -> None:
    """UNION ALL with parenthesized SELECT branches should still yield outer SELECT items."""
    sql = "(SELECT 1 AS x) UNION ALL (SELECT 2 AS x)"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    assert len(grouping.select) > 0


def test_pass_05_grouping_parenthesized_single_select_has_outer_scope() -> None:
    """A top-level parenthesized SELECT should be treated as outer scope."""
    sql = "(SELECT 1 AS x)"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    assert len(grouping.select) > 0


# --- is_literal tests ---


def test_pass_05_grouping_string_literal_is_literal() -> None:
    """String literals like 'Stripe' should be marked as is_literal=True."""
    sql = "SELECT 'Stripe' AS source, a FROM t"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    source_item = next((s for s in grouping.select if s.alias == "source"), None)
    assert source_item is not None
    assert source_item.is_literal is True
    assert source_item.source_aliases == []  # Literals have no source aliases


def test_pass_05_grouping_numeric_literal_is_literal() -> None:
    """Numeric literals like 42 should be marked as is_literal=True."""
    sql = "SELECT 42 AS answer, a FROM t"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    answer_item = next((s for s in grouping.select if s.alias == "answer"), None)
    assert answer_item is not None
    assert answer_item.is_literal is True


def test_pass_05_grouping_null_is_literal() -> None:
    """NULL should be marked as is_literal=True."""
    sql = "SELECT NULL AS empty_val, a FROM t"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    null_item = next((s for s in grouping.select if s.alias == "empty_val"), None)
    assert null_item is not None
    assert null_item.is_literal is True


def test_pass_05_grouping_boolean_literal_is_literal() -> None:
    """Boolean literals like TRUE should be marked as is_literal=True."""
    sql = "SELECT TRUE AS is_active, a FROM t"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    bool_item = next((s for s in grouping.select if s.alias == "is_active"), None)
    assert bool_item is not None
    assert bool_item.is_literal is True


def test_pass_05_grouping_column_ref_is_not_literal() -> None:
    """Column references should NOT be marked as is_literal."""
    sql = "SELECT a, b FROM t"
    _, _, grouping = run_grouping(sql)

    assert grouping.select is not None
    for item in grouping.select:
        assert item.is_literal is False

