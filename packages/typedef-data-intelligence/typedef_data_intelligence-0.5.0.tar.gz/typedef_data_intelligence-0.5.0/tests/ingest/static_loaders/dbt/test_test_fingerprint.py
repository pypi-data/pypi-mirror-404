"""Tests for dbt test fingerprinting functions.

Tests cover:
- compute_test_fingerprint() determinism and sensitivity
- compute_unit_test_fingerprint() determinism and sensitivity
"""
import re

from lineage.ingest.static_loaders.dbt.dbt_test_fingerprint import (
    compute_test_fingerprint,
    compute_unit_test_fingerprint,
)


class TestComputeTestFingerprint:
    """Tests for compute_test_fingerprint()."""

    def test_same_inputs_produce_same_fingerprint(self) -> None:
        """Verify deterministic fingerprinting."""
        fp1 = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs={"column_name": "id"},
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp2 = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs={"column_name": "id"},
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp1 == fp2

    def test_different_test_type_produces_different_fingerprint(self) -> None:
        """test_type change -> different fingerprint."""
        fp_generic = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_singular = compute_test_fingerprint(
            test_type="singular",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp_generic != fp_singular

    def test_different_test_name_produces_different_fingerprint(self) -> None:
        """test_name change -> different fingerprint."""
        fp_unique = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_not_null = compute_test_fingerprint(
            test_type="generic",
            test_name="not_null",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp_unique != fp_not_null

    def test_different_column_produces_different_fingerprint(self) -> None:
        """column_name change -> different fingerprint."""
        fp_id = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_status = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="status",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp_id != fp_status

    def test_different_model_produces_different_fingerprint(self) -> None:
        """model_id change -> different fingerprint."""
        fp_orders = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_customers = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.customers",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp_orders != fp_customers

    def test_different_kwargs_produces_different_fingerprint(self) -> None:
        """test_kwargs change (e.g., accepted_values list) -> different fingerprint."""
        fp_values_1 = compute_test_fingerprint(
            test_type="generic",
            test_name="accepted_values",
            column_name="status",
            model_id="model.test.orders",
            test_kwargs={"values": ["pending", "shipped", "delivered"]},
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_values_2 = compute_test_fingerprint(
            test_type="generic",
            test_name="accepted_values",
            column_name="status",
            model_id="model.test.orders",
            test_kwargs={"values": ["pending", "shipped", "delivered", "cancelled"]},
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp_values_1 != fp_values_2

    def test_different_severity_produces_different_fingerprint(self) -> None:
        """severity change -> different fingerprint."""
        fp_error = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_warn = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="warn",
            where_clause=None,
            store_failures=False,
        )
        assert fp_error != fp_warn

    def test_different_where_clause_produces_different_fingerprint(self) -> None:
        """where_clause change -> different fingerprint."""
        fp_no_where = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_with_where = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause="status != 'cancelled'",
            store_failures=False,
        )
        assert fp_no_where != fp_with_where

    def test_different_store_failures_produces_different_fingerprint(self) -> None:
        """store_failures change -> different fingerprint."""
        fp_no_store = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        fp_store = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=True,
        )
        assert fp_no_store != fp_store

    def test_none_values_handled_correctly(self) -> None:
        """None values don't cause errors and produce valid fingerprints."""
        fp = compute_test_fingerprint(
            test_type="singular",
            test_name=None,
            column_name=None,
            model_id=None,
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert fp is not None
        assert len(fp) == 64  # SHA-256 hex

    def test_fingerprint_is_valid_sha256(self) -> None:
        """Fingerprint is a 64-char hex string (SHA-256)."""
        fp = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert len(fp) == 64
        assert re.match(r"^[0-9a-f]{64}$", fp)

    def test_relationship_test_fingerprint(self) -> None:
        """Relationship test with kwargs produces valid fingerprint."""
        fp = compute_test_fingerprint(
            test_type="generic",
            test_name="relationships",
            column_name="customer_id",
            model_id="model.test.orders",
            test_kwargs={"to": "ref('customers')", "field": "id"},
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        assert len(fp) == 64
        assert re.match(r"^[0-9a-f]{64}$", fp)


class TestComputeUnitTestFingerprint:
    """Tests for compute_unit_test_fingerprint()."""

    def test_same_inputs_produce_same_fingerprint(self) -> None:
        """Verify deterministic fingerprinting."""
        fp1 = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1, "amount": 100}]}],
            expect={"rows": [{"id": 1, "total": 100}]},
            overrides=None,
        )
        fp2 = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1, "amount": 100}]}],
            expect={"rows": [{"id": 1, "total": 100}]},
            overrides=None,
        )
        assert fp1 == fp2

    def test_different_model_produces_different_fingerprint(self) -> None:
        """model_id change -> different fingerprint."""
        fp_orders = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        fp_customers = compute_unit_test_fingerprint(
            model_id="model.test.customers",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        assert fp_orders != fp_customers

    def test_different_given_produces_different_fingerprint(self) -> None:
        """given (mock data) change -> different fingerprint."""
        fp_one_row = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        fp_two_rows = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}, {"id": 2}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        assert fp_one_row != fp_two_rows

    def test_different_expect_produces_different_fingerprint(self) -> None:
        """expect change -> different fingerprint."""
        fp_expect_1 = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1, "total": 100}]},
            overrides=None,
        )
        fp_expect_2 = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1, "total": 200}]},
            overrides=None,
        )
        assert fp_expect_1 != fp_expect_2

    def test_different_overrides_produces_different_fingerprint(self) -> None:
        """overrides change -> different fingerprint."""
        fp_no_override = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        fp_with_override = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides={"vars": {"date_override": "2024-01-01"}},
        )
        assert fp_no_override != fp_with_override

    def test_none_values_handled_correctly(self) -> None:
        """None values produce valid fingerprints."""
        fp = compute_unit_test_fingerprint(
            model_id=None,
            given=None,
            expect=None,
            overrides=None,
        )
        assert fp is not None
        assert len(fp) == 64  # SHA-256 hex

    def test_fingerprint_is_valid_sha256(self) -> None:
        """Fingerprint is a 64-char hex string (SHA-256)."""
        fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw_orders')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        assert len(fp) == 64
        assert re.match(r"^[0-9a-f]{64}$", fp)

    def test_complex_given_with_multiple_inputs(self) -> None:
        """Unit test with multiple given inputs produces valid fingerprint."""
        fp = compute_unit_test_fingerprint(
            model_id="model.test.order_summary",
            given=[
                {"input": "ref('orders')", "rows": [{"id": 1, "customer_id": 10}]},
                {"input": "ref('customers')", "rows": [{"id": 10, "name": "Alice"}]},
            ],
            expect={"rows": [{"order_id": 1, "customer_name": "Alice"}]},
            overrides=None,
        )
        assert len(fp) == 64
        assert re.match(r"^[0-9a-f]{64}$", fp)
