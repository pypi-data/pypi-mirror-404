"""Unit tests for time column classification heuristics."""

from __future__ import annotations

from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    ColumnTimeContext,
    heuristic_classify_single_time_column,
    heuristic_time_classification,
)


class TestHeuristicClassifySingleTimeColumn:
    """Tests for heuristic_classify_single_time_column."""

    def test_created_at_is_time_column(self) -> None:
        """Column named 'created_at' should be classified as time."""
        col = ColumnTimeContext(
            alias="created_at",
            expr="created_at",
            in_group_by=False,
            source_aliases=["orders"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "attribute"

    def test_order_date_in_where_is_range_boundary(self) -> None:
        """Time column used in WHERE should be classified as range_boundary."""
        col = ColumnTimeContext(
            alias="order_date",
            expr="o.order_date",
            in_group_by=False,
            source_aliases=["o"],
        )
        result = heuristic_classify_single_time_column(
            col,
            where_predicates=["order_date >= '2024-01-01'"],
        )

        assert result.is_time_column is True
        assert result.time_role == "range_boundary"

    def test_month_in_group_by_is_bucket(self) -> None:
        """Time column in GROUP BY should be classified as bucket."""
        col = ColumnTimeContext(
            alias="month",
            expr="DATE_TRUNC('month', order_date)",
            in_group_by=True,
            source_aliases=["orders"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "bucket"
        assert result.grain == "month"

    def test_date_trunc_year_extracts_grain(self) -> None:
        """DATE_TRUNC with year should extract year grain."""
        col = ColumnTimeContext(
            alias="report_year",
            expr="DATE_TRUNC('year', created_at)",
            in_group_by=True,
            source_aliases=["events"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "year"

    def test_non_time_column_not_classified(self) -> None:
        """Column without time patterns should not be classified as time."""
        col = ColumnTimeContext(
            alias="customer_id",
            expr="c.customer_id",
            in_group_by=False,
            source_aliases=["c"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is False
        assert result.time_role is None
        assert result.grain is None

    def test_tpc_ds_d_year_is_time(self) -> None:
        """TPC-DS style d_year should be recognized as time."""
        col = ColumnTimeContext(
            alias="d_year",
            expr="d.d_year",
            in_group_by=True,
            source_aliases=["d"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "bucket"

    def test_day_of_week_is_attribute(self) -> None:
        """Day of week columns should be classified as attribute."""
        col = ColumnTimeContext(
            alias="d_dow",
            expr="d.d_dow",
            in_group_by=False,
            source_aliases=["d"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "attribute"

    def test_extract_hour_gets_hour_grain(self) -> None:
        """EXTRACT(hour FROM ...) should get hour grain."""
        col = ColumnTimeContext(
            alias="hour",
            expr="EXTRACT(hour FROM event_time)",
            in_group_by=True,
            source_aliases=["events"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "hour"

    # --- Business Calendar Patterns ---

    def test_fiscal_year_is_time_column(self) -> None:
        """Fiscal year columns should be recognized as time."""
        col = ColumnTimeContext(
            alias="fiscal_year",
            expr="f.fiscal_year",
            in_group_by=True,
            source_aliases=["f"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "bucket"
        assert result.grain == "year"

    def test_fiscal_quarter_is_time_column(self) -> None:
        """Fiscal quarter columns should be recognized as time."""
        col = ColumnTimeContext(
            alias="fiscal_quarter",
            expr="c.fiscal_quarter",
            in_group_by=True,
            source_aliases=["c"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "quarter"

    def test_reporting_period_is_time_column(self) -> None:
        """Reporting period columns should be recognized as time."""
        col = ColumnTimeContext(
            alias="reporting_period",
            expr="r.reporting_period",
            in_group_by=True,
            source_aliases=["r"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "bucket"

    def test_reporting_week_is_time_column(self) -> None:
        """Reporting week columns should be recognized as time."""
        col = ColumnTimeContext(
            alias="reporting_week",
            expr="DATE_TRUNC('week', event_date)",
            in_group_by=True,
            source_aliases=["e"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "week"

    # --- Timezone Suffix Patterns ---

    def test_created_at_utc_is_time_column(self) -> None:
        """Columns with _utc suffix should be recognized as time."""
        col = ColumnTimeContext(
            alias="created_at_utc",
            expr="e.created_at_utc",
            in_group_by=False,
            source_aliases=["e"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True

    def test_timestamp_pacific_is_time_column(self) -> None:
        """Columns with _pacific suffix should be recognized as time."""
        col = ColumnTimeContext(
            alias="event_time_pacific",
            expr="e.event_time_pacific",
            in_group_by=False,
            source_aliases=["e"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True


def test_heuristic_time_classification_respects_select_items() -> None:
    grouping_analysis = {
        "select": [
            {"alias": "created_at", "expr": "created_at", "source_aliases": ["t"]},
            {"alias": "customer_id", "expr": "t.customer_id", "source_aliases": ["t"]},
        ],
        "group_by": [],
    }
    filter_analysis = {"where": []}
    select_items = [
        {"alias": "created_at", "expr": "created_at", "source_aliases": ["t"]}
    ]

    result = heuristic_time_classification(
        grouping_analysis, filter_analysis, select_items=select_items
    )

    assert len(result.classifications) == 1
    assert result.classifications[0].column_alias == "created_at"

    # --- Calendar Table Patterns ---

    def test_week_of_year_is_time_attribute(self) -> None:
        """Week of year should be recognized as time attribute."""
        col = ColumnTimeContext(
            alias="week_of_year",
            expr="d.week_of_year",
            in_group_by=False,
            source_aliases=["d"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.time_role == "attribute"

    def test_iso_week_is_time_column(self) -> None:
        """ISO week columns should be recognized as time."""
        col = ColumnTimeContext(
            alias="iso_week",
            expr="d.iso_week",
            in_group_by=True,
            source_aliases=["d"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "week"

    # --- Time Function Patterns ---

    def test_year_function_extracts_year_grain(self) -> None:
        """YEAR(col) function should extract year grain."""
        col = ColumnTimeContext(
            alias="order_year",
            expr="YEAR(o.order_date)",
            in_group_by=True,
            source_aliases=["o"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "year"

    def test_month_function_extracts_month_grain(self) -> None:
        """MONTH(col) function should extract month grain."""
        col = ColumnTimeContext(
            alias="order_month",
            expr="MONTH(o.order_date)",
            in_group_by=True,
            source_aliases=["o"],
        )
        result = heuristic_classify_single_time_column(col, where_predicates=[])

        assert result.is_time_column is True
        assert result.grain == "month"


class TestHeuristicTimeClassification:
    """Tests for heuristic_time_classification (full pipeline)."""

    def test_empty_grouping_returns_empty_classifications(self) -> None:
        """Empty grouping analysis should return empty classifications."""
        result = heuristic_time_classification(
            grouping_analysis={},
            filter_analysis={},
        )

        assert result.classifications == []

    def test_multiple_columns_classified_independently(self) -> None:
        """Each column should be classified independently."""
        grouping_analysis = {
            "select": [
                {"alias": "order_date", "expr": "o.order_date", "source_aliases": ["o"]},
                {"alias": "customer_id", "expr": "o.customer_id", "source_aliases": ["o"]},
                {"alias": "total", "expr": "SUM(o.amount)", "source_aliases": ["o"]},
            ],
            "group_by": [],
        }
        filter_analysis = {"where": []}

        result = heuristic_time_classification(grouping_analysis, filter_analysis)

        assert len(result.classifications) == 3

        # order_date should be time
        order_date = next(c for c in result.classifications if c.column_alias == "order_date")
        assert order_date.is_time_column is True

        # customer_id should not be time
        customer_id = next(c for c in result.classifications if c.column_alias == "customer_id")
        assert customer_id.is_time_column is False

        # total (SUM) should not be time
        total = next(c for c in result.classifications if c.column_alias == "total")
        assert total.is_time_column is False

    def test_where_predicate_affects_role(self) -> None:
        """WHERE predicates should influence time role classification."""
        grouping_analysis = {
            "select": [
                {"alias": "created_at", "expr": "e.created_at", "source_aliases": ["e"]},
            ],
            "group_by": [],
        }
        filter_analysis = {
            "where": ["created_at >= '2024-01-01'"],
        }

        result = heuristic_time_classification(grouping_analysis, filter_analysis)

        assert len(result.classifications) == 1
        assert result.classifications[0].is_time_column is True
        assert result.classifications[0].time_role == "range_boundary"

    def test_group_by_affects_role(self) -> None:
        """GROUP BY membership should influence time role classification."""
        # Note: _extract_column_time_context checks if alias is in group_by list
        grouping_analysis = {
            "select": [
                {
                    "alias": "month",
                    "expr": "DATE_TRUNC('month', order_date)",
                    "source_aliases": ["orders"],
                    "kind": "group_key",
                },
            ],
            "group_by": ["month"],  # Must match alias, not expr
        }
        filter_analysis = {"where": []}

        result = heuristic_time_classification(grouping_analysis, filter_analysis)

        assert len(result.classifications) == 1
        assert result.classifications[0].is_time_column is True
        assert result.classifications[0].time_role == "bucket"
        assert result.classifications[0].grain == "month"


class TestHybridTimeConversion:
    """Tests for hybrid time_classification -> TimeAnalysis conversion."""

    def test_time_scope_extracted_when_alias_differs_from_base_column(self) -> None:
        """If the output alias is renamed, we should still match predicates via expr."""
        from lineage.ingest.static_loaders.semantic.pipeline.hybrid_executor import (
            HybridPipelineExecutor,
        )

        time_cls = {
            "classifications": [
                {
                    "column_alias": "ds",
                    "expr": "o.order_date",
                    "is_time_column": True,
                    "time_role": "range_boundary",
                    "grain": "day",
                },
                {
                    "column_alias": "month_bucket",
                    "expr": "DATE_TRUNC('month', o.order_date)",
                    "is_time_column": True,
                    "time_role": "bucket",
                    "grain": "month",
                },
            ]
        }

        filter_analysis = {
            "where": [
                "o.order_date >= '2024-01-01'",
                "o.order_date < '2024-02-01'",
            ]
        }

        # The conversion method does not depend on instance state; construct without __init__.
        executor = HybridPipelineExecutor.__new__(HybridPipelineExecutor)
        ta = executor._convert_time_classification_to_time_analysis(time_cls, filter_analysis)

        assert ta is not None
        assert ta.time_scope is not None
        assert ta.time_scope.column in ("o.order_date", "order_date")
        assert ta.time_scope.start == "'2024-01-01'"
        assert ta.time_scope.end == "'2024-02-01'"
        assert ta.time_scope.end_inclusive is False

        assert ta.normalized_time_scope is not None
        assert ta.normalized_time_scope.column == ta.time_scope.column
        assert ta.normalized_time_scope.end_exclusive is True

        # time_buckets should store expressions (preferred) rather than aliases.
        assert "DATE_TRUNC('month', o.order_date)" in ta.time_buckets
