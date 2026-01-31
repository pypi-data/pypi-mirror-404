"""Unit tests for column classification heuristics."""

from __future__ import annotations

from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    ColumnContext,
    GroupingContext,
    RelationContext,
    heuristic_classify_single_column,
    heuristic_column_classification,
)


class TestHeuristicClassifySingleColumn:
    """Tests for heuristic_classify_single_column."""

    def _make_column(
        self,
        alias: str,
        expr: str,
        source_aliases: list[str] | None = None,
    ) -> ColumnContext:
        return ColumnContext(
            alias=alias,
            expr=expr,
            source_aliases=source_aliases or [],
        )

    def _make_grouping(
        self,
        is_aggregated: bool = False,
        group_by: list[str] | None = None,
    ) -> GroupingContext:
        return GroupingContext(
            is_aggregated=is_aggregated,
            group_by=group_by or [],
        )

    def test_customer_id_from_fact_is_foreign_key(self) -> None:
        """ID column from fact table should be foreign_key."""
        col = self._make_column("customer_id", "o.customer_id", source_aliases=["o"])
        relations = [RelationContext(alias="o", base="fct_orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "foreign_key"
        assert result.table_type == "fact"
        assert result.derivation == "direct"

    def test_customer_id_from_dim_is_natural_key(self) -> None:
        """ID column from dimension table should be natural_key."""
        col = self._make_column("customer_id", "c.customer_id", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="dim_customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "natural_key"
        assert result.table_type == "dimension"

    def test_md5_hash_is_surrogate_key(self) -> None:
        """MD5 hash expression should be surrogate_key."""
        col = self._make_column(
            "dedup_key",
            "MD5(customer_id || order_date)",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "surrogate_key"
        # Note: derivation is "calculated" because || operator is detected
        assert result.derivation == "calculated"

    def test_is_active_flag_pattern(self) -> None:
        """is_* column should be classified as flag."""
        col = self._make_column("is_active", "c.is_active", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "flag"
        assert result.is_categorical is True
        assert result.cardinality_hint == "low"

    def test_has_subscription_flag_pattern(self) -> None:
        """has_* column should be classified as flag."""
        col = self._make_column("has_subscription", "u.has_subscription", source_aliases=["u"])
        relations = [RelationContext(alias="u", base="users", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "flag"

    def test_sum_aggregation_is_metric(self) -> None:
        """SUM aggregation should be metric with aggregated derivation."""
        col = self._make_column(
            "total_revenue",
            "SUM(o.amount)",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping(is_aggregated=True)

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "metric"
        assert result.derivation == "aggregated"

    def test_count_aggregation_is_metric(self) -> None:
        """COUNT aggregation should be metric."""
        col = self._make_column(
            "order_count",
            "COUNT(*)",
            source_aliases=[],
        )
        relations = []
        grouping = self._make_grouping(is_aggregated=True)

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "metric"
        assert result.derivation == "aggregated"

    def test_created_at_is_timestamp(self) -> None:
        """created_at column should be timestamp."""
        col = self._make_column("created_at", "o.created_at", source_aliases=["o"])
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "timestamp"

    def test_order_date_is_timestamp(self) -> None:
        """*_date column should be timestamp."""
        col = self._make_column("order_date", "o.order_date", source_aliases=["o"])
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "timestamp"

    def test_case_with_0_1_is_bucket_label(self) -> None:
        """CASE producing 0/1 should be bucket_label."""
        # Note: heuristic checks for " then 1 " with spaces (lowercase)
        # Use alias that doesn't match is_* pattern (which takes priority)
        col = self._make_column(
            "large_order_flag",
            "case when amount > 1000 then 1 else 0 end",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "bucket_label"
        assert result.derivation == "conditional"
        assert result.is_categorical is True

    def test_row_number_is_window_derivation(self) -> None:
        """ROW_NUMBER() should have window derivation."""
        col = self._make_column(
            "rn",
            "ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date)",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.derivation == "window"

    def test_cast_derivation(self) -> None:
        """CAST() expression should have cast derivation."""
        col = self._make_column(
            "amount_str",
            "CAST(amount AS VARCHAR)",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.derivation == "cast"

    def test_calculated_derivation(self) -> None:
        """Arithmetic expression should have calculated derivation."""
        col = self._make_column(
            "total_with_tax",
            "amount * 1.1",
            source_aliases=["o"],
        )
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.derivation == "calculated"

    def test_plain_attribute(self) -> None:
        """Plain column without special patterns should be attribute."""
        col = self._make_column("product_name", "p.name", source_aliases=["p"])
        relations = [RelationContext(alias="p", base="products", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.semantic_role == "attribute"
        assert result.derivation == "direct"

    def test_business_name_generation(self) -> None:
        """Business name should be humanized from alias."""
        col = self._make_column("customer_first_name", "c.first_name", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        # Should convert snake_case to human readable
        assert result.business_name == "Customer First Name"


class TestHeuristicColumnClassificationPII:
    """Tests for PII detection in column classification."""

    def _make_column(
        self,
        alias: str,
        expr: str,
        source_aliases: list[str] | None = None,
    ) -> ColumnContext:
        return ColumnContext(
            alias=alias,
            expr=expr,
            source_aliases=source_aliases or [],
        )

    def _make_grouping(self) -> GroupingContext:
        return GroupingContext()

    def test_email_is_high_confidence_pii(self) -> None:
        """Email column should be detected as high confidence PII."""
        col = self._make_column("email", "c.email", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is True
        assert result.pii_type == "email"
        assert result.pii_confidence == "high"

    def test_first_name_is_high_confidence_pii(self) -> None:
        """first_name column should be detected as name PII."""
        col = self._make_column("first_name", "c.first_name", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is True
        assert result.pii_type == "name"
        assert result.pii_confidence == "high"

    def test_phone_number_is_high_confidence_pii(self) -> None:
        """phone_number column should be detected as phone PII."""
        col = self._make_column("phone_number", "c.phone", source_aliases=["c"])
        relations = [RelationContext(alias="c", base="customers", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is True
        assert result.pii_type == "phone"
        assert result.pii_confidence == "high"

    def test_ssn_is_high_confidence_pii(self) -> None:
        """SSN column should be detected as high confidence PII."""
        col = self._make_column("ssn", "e.social_security", source_aliases=["e"])
        relations = [RelationContext(alias="e", base="employees", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is True
        assert result.pii_type == "ssn"
        assert result.pii_confidence == "high"

    def test_ip_address_is_medium_confidence_pii(self) -> None:
        """IP address column should be detected as medium confidence PII."""
        # Note: Use "client_ip" to avoid matching "address" pattern first
        col = self._make_column("client_ip", "e.client_ip", source_aliases=["e"])
        relations = [RelationContext(alias="e", base="events", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is True
        assert result.pii_type == "ip_address"
        assert result.pii_confidence == "medium"

    def test_order_id_is_not_pii(self) -> None:
        """order_id should not be detected as PII."""
        col = self._make_column("order_id", "o.order_id", source_aliases=["o"])
        relations = [RelationContext(alias="o", base="orders", kind="table")]
        grouping = self._make_grouping()

        result = heuristic_classify_single_column(col, relations, grouping)

        assert result.is_pii is False
        assert result.pii_type is None


class TestHeuristicColumnClassification:
    """Tests for heuristic_column_classification (full pipeline)."""

    def test_empty_grouping_returns_empty_classifications(self) -> None:
        """Empty grouping analysis should return empty classifications."""
        result = heuristic_column_classification(
            grouping_analysis={},
            relation_analysis={},
        )

        assert result.classifications == []

    def test_multiple_columns_classified(self) -> None:
        """Multiple columns should each be classified."""
        grouping_analysis = {
            "select": [
                {"alias": "customer_id", "expr": "o.customer_id", "kind": "dimension", "source_aliases": ["o"]},
                {"alias": "total_revenue", "expr": "SUM(o.amount)", "kind": "measure", "source_aliases": ["o"]},
                {"alias": "order_date", "expr": "o.order_date", "kind": "dimension", "source_aliases": ["o"]},
            ],
            "is_aggregated": True,
            "group_by": ["customer_id"],
        }
        relation_analysis = {
            "relations": [{"alias": "o", "base": "fct_orders", "kind": "table"}],
        }

        result = heuristic_column_classification(grouping_analysis, relation_analysis)

        assert len(result.classifications) == 3

        # customer_id should be foreign_key (from fact table)
        customer_id = next(c for c in result.classifications if c.column_alias == "customer_id")
        assert customer_id.semantic_role == "foreign_key"
        assert customer_id.table_type == "fact"

        # total_revenue should be metric
        total_revenue = next(c for c in result.classifications if c.column_alias == "total_revenue")
        assert total_revenue.semantic_role == "metric"
        assert total_revenue.derivation == "aggregated"

        # order_date should be timestamp
        order_date = next(c for c in result.classifications if c.column_alias == "order_date")
        assert order_date.semantic_role == "timestamp"

    def test_pii_columns_aggregated(self) -> None:
        """PII columns should be aggregated in result."""
        grouping_analysis = {
            "select": [
                {"alias": "customer_id", "expr": "c.id", "kind": "dimension", "source_aliases": ["c"]},
                {"alias": "email", "expr": "c.email", "kind": "dimension", "source_aliases": ["c"]},
                {"alias": "phone_number", "expr": "c.phone", "kind": "dimension", "source_aliases": ["c"]},
            ],
        }
        relation_analysis = {
            "relations": [{"alias": "c", "base": "customers", "kind": "table"}],
        }

        result = heuristic_column_classification(grouping_analysis, relation_analysis)

        # Should have 2 PII columns
        assert len(result.pii_columns) == 2
        assert "email" in result.pii_columns
        assert "phone_number" in result.pii_columns
        assert result.high_risk_pii_count == 2  # Both are high confidence

    def test_heuristic_classification_with_column_features(self) -> None:
        """Heuristic classification should accept optional column_features argument.

        This test ensures the function signature is stable and accepts the expected
        3 arguments (grouping_analysis, relation_analysis, column_features).
        """
        grouping_analysis = {
            "select": [
                {"alias": "revenue", "expr": "SUM(o.amount)", "kind": "measure", "source_aliases": ["o"]},
            ],
        }
        relation_analysis = {
            "relations": [{"alias": "o", "base": "orders", "kind": "table"}],
        }
        # column_features is optional - test with None and with a dict
        result_without_features = heuristic_column_classification(
            grouping_analysis, relation_analysis
        )
        result_with_features = heuristic_column_classification(
            grouping_analysis, relation_analysis, column_features={}
        )

        # Both should succeed and produce valid results
        assert len(result_without_features.classifications) == 1
        assert len(result_with_features.classifications) == 1
        assert result_without_features.classifications[0].column_alias == "revenue"
        assert result_with_features.classifications[0].column_alias == "revenue"
