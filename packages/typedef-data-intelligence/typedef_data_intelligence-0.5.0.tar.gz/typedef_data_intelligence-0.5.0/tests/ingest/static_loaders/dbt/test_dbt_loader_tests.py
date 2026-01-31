"""Tests for dbt test parsing from manifest.

Tests cover:
- DbtTestNode parsing from manifest
- DbtUnitTestNode parsing from manifest
- iter_tests() and iter_unit_tests() methods
- get_test() lookup
- Test/unit test count properties
"""
import json
from pathlib import Path

from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
from lineage.ingest.static_loaders.dbt.dbt_loader import RawDbtArtifacts


def create_manifest_with_tests(tests: dict, unit_tests: dict | None = None) -> dict:
    """Create a minimal manifest with test nodes.

    Args:
        tests: Dictionary of test unique_id -> test node dict
        unit_tests: Optional dictionary of unit test unique_id -> unit test node dict

    Returns:
        Manifest dict suitable for RawDbtArtifacts
    """
    nodes = {}

    # Add a minimal model for tests to reference
    nodes["model.project.orders"] = {
        "resource_type": "model",
        "name": "orders",
        "original_file_path": "models/orders.sql",
        "compiled_sql": "SELECT * FROM raw_orders",
        "database": "test_db",
        "schema": "test_schema",
        "alias": "orders",
        "relation_name": "test_schema.orders",
        "columns": {
            "id": {"description": "Order ID"},
            "customer_id": {"description": "Customer FK"},
            "status": {"description": "Order status"},
        },
        "config": {"materialized": "table"},
        "depends_on": {"nodes": [], "sources": [], "macros": []},
        "checksum": {"name": "sha256", "checksum": "abc123"},
    }

    # Add another model for relationship tests
    nodes["model.project.customers"] = {
        "resource_type": "model",
        "name": "customers",
        "original_file_path": "models/customers.sql",
        "compiled_sql": "SELECT * FROM raw_customers",
        "database": "test_db",
        "schema": "test_schema",
        "alias": "customers",
        "relation_name": "test_schema.customers",
        "columns": {
            "id": {"description": "Customer ID"},
        },
        "config": {"materialized": "table"},
        "depends_on": {"nodes": [], "sources": [], "macros": []},
        "checksum": {"name": "sha256", "checksum": "def456"},
    }

    # Add test nodes
    nodes.update(tests)

    # Add unit test nodes
    if unit_tests:
        nodes.update(unit_tests)

    return {
        "metadata": {
            "project_name": "test_project",
            "adapter_type": "duckdb",
            "target_name": "dev",
        },
        "nodes": nodes,
        "sources": {},
        "macros": {},
    }


def create_artifacts_from_manifest(manifest: dict, tmp_path: Path) -> RawDbtArtifacts:
    """Create RawDbtArtifacts from a manifest dict."""
    target_dir = tmp_path / "target"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "manifest.json").write_text(json.dumps(manifest))
    (target_dir / "catalog.json").write_text(json.dumps({"nodes": {}, "sources": {}}))

    config = DbtArtifactsConfig()
    config.target_path = target_dir

    return RawDbtArtifacts(
        config=config,
        manifest=manifest,
        catalog={"nodes": {}, "sources": {}},
        run_results={},
    )


class TestDbtTestNodeParsing:
    """Tests for _load_tests() parsing from manifest."""

    def test_generic_test_parsed_correctly(self, tmp_path: Path) -> None:
        """Generic tests (unique, not_null) have test_metadata extracted."""
        tests = {
            "test.project.unique_orders_id": {
                "resource_type": "test",
                "name": "unique_orders_id",
                "description": "Ensure order IDs are unique",
                "tags": ["data_quality"],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT id FROM orders GROUP BY 1 HAVING count(*) > 1",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {"column_name": "id"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.unique_orders_id")
        assert test is not None
        assert test.unique_id == "test.project.unique_orders_id"
        assert test.name == "unique_orders_id"
        assert test.test_type == "generic"
        assert test.test_name == "unique"
        assert test.column_name == "id"
        assert test.model_id == "model.project.orders"
        assert test.severity == "error"

    def test_singular_test_parsed_correctly(self, tmp_path: Path) -> None:
        """Singular tests (custom SQL) have test_type='singular'."""
        tests = {
            "test.project.assert_valid_orders": {
                "resource_type": "test",
                "name": "assert_valid_orders",
                "description": "Custom validation for orders",
                "tags": [],
                "meta": {},
                "original_file_path": "tests/assert_valid_orders.sql",
                "compiled_sql": "SELECT * FROM orders WHERE amount < 0",
                "column_name": None,
                # No test_metadata means singular test
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.assert_valid_orders")
        assert test is not None
        assert test.test_type == "singular"
        assert test.test_name is None
        assert test.original_path == "tests/assert_valid_orders.sql"

    def test_relationship_test_extracts_referenced_model(self, tmp_path: Path) -> None:
        """Relationship tests extract referenced_model_id from depends_on."""
        tests = {
            "test.project.relationships_orders_customer": {
                "resource_type": "test",
                "name": "relationships_orders_customer",
                "description": "FK constraint",
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT o.customer_id FROM orders o LEFT JOIN customers c ON o.customer_id = c.id WHERE c.id IS NULL",
                "column_name": "customer_id",
                "test_metadata": {
                    "name": "relationships",
                    "kwargs": {"to": "ref('customers')", "field": "id"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders", "model.project.customers"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.relationships_orders_customer")
        assert test is not None
        assert test.test_name == "relationships"
        assert test.model_id == "model.project.orders"
        assert test.referenced_model_id == "model.project.customers"

    def test_test_kwargs_extracted(self, tmp_path: Path) -> None:
        """test_kwargs includes values like accepted_values list."""
        tests = {
            "test.project.accepted_values_orders_status": {
                "resource_type": "test",
                "name": "accepted_values_orders_status",
                "description": "Status validation",
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT * FROM orders WHERE status NOT IN ('pending', 'shipped', 'delivered')",
                "column_name": "status",
                "test_metadata": {
                    "name": "accepted_values",
                    "kwargs": {
                        "column_name": "status",
                        "values": ["pending", "shipped", "delivered"],
                    },
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.accepted_values_orders_status")
        assert test is not None
        assert test.test_kwargs is not None
        assert test.test_kwargs.get("values") == ["pending", "shipped", "delivered"]

    def test_test_config_extracted(self, tmp_path: Path) -> None:
        """severity, where, store_failures extracted from config."""
        tests = {
            "test.project.unique_orders_id": {
                "resource_type": "test",
                "name": "unique_orders_id",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT id FROM orders GROUP BY 1 HAVING count(*) > 1",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {},
                },
                "config": {
                    "severity": "warn",
                    "where": "status != 'cancelled'",
                    "store_failures": True,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.unique_orders_id")
        assert test is not None
        assert test.severity == "warn"
        assert test.where_clause == "status != 'cancelled'"
        assert test.store_failures is True

    def test_column_name_extracted(self, tmp_path: Path) -> None:
        """column_name extracted for column-scoped tests."""
        tests = {
            "test.project.not_null_orders_amount": {
                "resource_type": "test",
                "name": "not_null_orders_amount",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT * FROM orders WHERE amount IS NULL",
                "column_name": "amount",
                "test_metadata": {
                    "name": "not_null",
                    "kwargs": {"column_name": "amount"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.not_null_orders_amount")
        assert test is not None
        assert test.column_name == "amount"

    def test_model_id_from_depends_on(self, tmp_path: Path) -> None:
        """model_id extracted from depends_on.nodes[0]."""
        tests = {
            "test.project.unique_orders_id": {
                "resource_type": "test",
                "name": "unique_orders_id",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.unique_orders_id")
        assert test is not None
        assert test.model_id == "model.project.orders"

    def test_iter_tests_returns_all_tests(self, tmp_path: Path) -> None:
        """iter_tests() iterates over all loaded tests."""
        tests = {
            "test.project.test1": {
                "resource_type": "test",
                "name": "test1",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "test_metadata": {"name": "unique", "kwargs": {}},
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": ["model.project.orders"]},
            },
            "test.project.test2": {
                "resource_type": "test",
                "name": "test2",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "test_metadata": {"name": "not_null", "kwargs": {}},
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": ["model.project.orders"]},
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test_list = list(artifacts.iter_tests())
        assert len(test_list) == 2
        test_ids = {t.unique_id for t in test_list}
        assert "test.project.test1" in test_ids
        assert "test.project.test2" in test_ids

    def test_get_test_returns_correct_test(self, tmp_path: Path) -> None:
        """get_test(unique_id) returns the right test."""
        tests = {
            "test.project.test1": {
                "resource_type": "test",
                "name": "test1",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "test_metadata": {"name": "unique", "kwargs": {}},
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": []},
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.test1")
        assert test is not None
        assert test.unique_id == "test.project.test1"

        # Non-existent test returns None
        assert artifacts.get_test("test.project.nonexistent") is None

    def test_test_count_property(self, tmp_path: Path) -> None:
        """test_count matches number of loaded tests."""
        tests = {
            "test.project.test1": {
                "resource_type": "test",
                "name": "test1",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "test_metadata": {"name": "unique", "kwargs": {}},
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": []},
            },
            "test.project.test2": {
                "resource_type": "test",
                "name": "test2",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "test_metadata": {"name": "not_null", "kwargs": {}},
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": []},
            },
            "test.project.test3": {
                "resource_type": "test",
                "name": "test3",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": None,
                "config": {"severity": "error", "where": None, "store_failures": False},
                "depends_on": {"nodes": []},
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        assert artifacts.test_count == 3


class TestDbtUnitTestNodeParsing:
    """Tests for _load_unit_tests() parsing from manifest."""

    def test_unit_test_parsed_correctly(self, tmp_path: Path) -> None:
        """Unit tests with given/expect/overrides parsed."""
        unit_tests = {
            "unit_test.project.test_orders_calculation": {
                "resource_type": "unit_test",
                "name": "test_orders_calculation",
                "description": "Test order total calculation",
                "tags": ["unit"],
                "meta": {},
                "given": [
                    {
                        "input": "ref('raw_orders')",
                        "rows": [{"id": 1, "amount": 100, "tax": 10}],
                    },
                ],
                "expect": {
                    "rows": [{"id": 1, "total": 110}],
                },
                "overrides": {
                    "vars": {"calculation_date": "2024-01-01"},
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test = list(artifacts.iter_unit_tests())[0]
        assert unit_test.unique_id == "unit_test.project.test_orders_calculation"
        assert unit_test.name == "test_orders_calculation"
        assert unit_test.description == "Test order total calculation"
        assert unit_test.given is not None
        assert len(unit_test.given) == 1
        assert unit_test.given[0]["input"] == "ref('raw_orders')"
        assert unit_test.expect is not None
        assert unit_test.expect["rows"] == [{"id": 1, "total": 110}]
        assert unit_test.overrides is not None
        assert unit_test.overrides["vars"]["calculation_date"] == "2024-01-01"

    def test_unit_test_model_id_extracted(self, tmp_path: Path) -> None:
        """model_id extracted from depends_on."""
        unit_tests = {
            "unit_test.project.test_orders_logic": {
                "resource_type": "unit_test",
                "name": "test_orders_logic",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [{"input": "ref('raw')", "rows": []}],
                "expect": {"rows": []},
                "overrides": None,
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test = list(artifacts.iter_unit_tests())[0]
        assert unit_test.model_id == "model.project.orders"

    def test_iter_unit_tests_returns_all(self, tmp_path: Path) -> None:
        """iter_unit_tests() iterates over all loaded unit tests."""
        unit_tests = {
            "unit_test.project.test1": {
                "resource_type": "unit_test",
                "name": "test1",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [],
                "expect": {},
                "overrides": None,
                "depends_on": {"nodes": []},
            },
            "unit_test.project.test2": {
                "resource_type": "unit_test",
                "name": "test2",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [],
                "expect": {},
                "overrides": None,
                "depends_on": {"nodes": []},
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test_list = list(artifacts.iter_unit_tests())
        assert len(unit_test_list) == 2
        ids = {ut.unique_id for ut in unit_test_list}
        assert "unit_test.project.test1" in ids
        assert "unit_test.project.test2" in ids

    def test_unit_test_count_property(self, tmp_path: Path) -> None:
        """unit_test_count matches number of loaded unit tests."""
        unit_tests = {
            "unit_test.project.test1": {
                "resource_type": "unit_test",
                "name": "test1",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [],
                "expect": {},
                "overrides": None,
                "depends_on": {"nodes": []},
            },
            "unit_test.project.test2": {
                "resource_type": "unit_test",
                "name": "test2",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [],
                "expect": {},
                "overrides": None,
                "depends_on": {"nodes": []},
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        assert artifacts.unit_test_count == 2

    def test_unit_test_with_multiple_given_inputs(self, tmp_path: Path) -> None:
        """Unit test with multiple given inputs parsed correctly."""
        unit_tests = {
            "unit_test.project.test_join_logic": {
                "resource_type": "unit_test",
                "name": "test_join_logic",
                "description": "Test join between orders and customers",
                "tags": [],
                "meta": {},
                "given": [
                    {"input": "ref('orders')", "rows": [{"id": 1, "customer_id": 10}]},
                    {"input": "ref('customers')", "rows": [{"id": 10, "name": "Alice"}]},
                ],
                "expect": {
                    "rows": [{"order_id": 1, "customer_name": "Alice"}],
                },
                "overrides": None,
                "depends_on": {"nodes": ["model.project.orders"]},
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test = list(artifacts.iter_unit_tests())[0]
        assert len(unit_test.given) == 2
        assert unit_test.given[0]["input"] == "ref('orders')"
        assert unit_test.given[1]["input"] == "ref('customers')"


class TestMalformedManifestHandling:
    """Tests for graceful handling of malformed manifest data."""

    def test_test_with_missing_depends_on(self, tmp_path: Path) -> None:
        """Test with no depends_on field -> model_id=None, no crash."""
        tests = {
            "test.project.orphan_test": {
                "resource_type": "test",
                "name": "orphan_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": """
SELECT id
FROM orders
GROUP BY id
HAVING count(*) > 1
""",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {"column_name": "id"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                # Missing depends_on entirely
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.orphan_test")
        assert test is not None
        assert test.model_id is None
        assert test.depends_on_nodes == []

    def test_test_with_empty_depends_on_nodes(self, tmp_path: Path) -> None:
        """Test with depends_on.nodes=[] -> model_id=None."""
        tests = {
            "test.project.empty_deps_test": {
                "resource_type": "test",
                "name": "empty_deps_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": """
SELECT *
FROM orders
WHERE id IS NULL
""",
                "column_name": "id",
                "test_metadata": {
                    "name": "not_null",
                    "kwargs": {"column_name": "id"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": [],  # Empty nodes list
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.empty_deps_test")
        assert test is not None
        assert test.model_id is None
        assert test.referenced_model_id is None

    def test_test_with_missing_config(self, tmp_path: Path) -> None:
        """Test with no config -> defaults: severity=error, store_failures=False."""
        tests = {
            "test.project.no_config_test": {
                "resource_type": "test",
                "name": "no_config_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": """
SELECT id
FROM orders
GROUP BY id
HAVING count(*) > 1
""",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": {},
                },
                # Missing config entirely
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.no_config_test")
        assert test is not None
        # Default severity
        assert test.severity == "error"
        # Default store_failures
        assert test.store_failures is False
        assert test.where_clause is None

    def test_test_with_missing_test_metadata(self, tmp_path: Path) -> None:
        """Generic test without test_metadata -> treated as singular."""
        tests = {
            "test.project.no_metadata_test": {
                "resource_type": "test",
                "name": "no_metadata_test",
                "description": "Custom validation",
                "tags": [],
                "meta": {},
                "original_file_path": "tests/custom_test.sql",
                "compiled_sql": "SELECT * FROM orders WHERE amount < 0",
                "column_name": None,
                # No test_metadata
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.no_metadata_test")
        assert test is not None
        # Without test_metadata, it's a singular test
        assert test.test_type == "singular"
        assert test.test_name is None

    def test_test_with_non_dict_test_kwargs(self, tmp_path: Path) -> None:
        """test_kwargs as non-dict -> handled gracefully."""
        tests = {
            "test.project.bad_kwargs_test": {
                "resource_type": "test",
                "name": "bad_kwargs_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": "id",
                "test_metadata": {
                    "name": "unique",
                    "kwargs": "invalid_string",  # Should be dict
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.bad_kwargs_test")
        assert test is not None
        # The kwargs might be stored as-is or converted
        # Key is that it doesn't crash

    def test_unit_test_with_missing_given(self, tmp_path: Path) -> None:
        """Unit test without given field -> given=None or empty."""
        unit_tests = {
            "unit_test.project.no_given_test": {
                "resource_type": "unit_test",
                "name": "no_given_test",
                "description": None,
                "tags": [],
                "meta": {},
                # Missing given
                "expect": {"rows": [{"id": 1}]},
                "overrides": None,
                "depends_on": {"nodes": ["model.project.orders"]},
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test = list(artifacts.iter_unit_tests())[0]
        assert unit_test is not None
        assert unit_test.given is None

    def test_unit_test_with_missing_expect(self, tmp_path: Path) -> None:
        """Unit test without expect field -> expect=None or empty."""
        unit_tests = {
            "unit_test.project.no_expect_test": {
                "resource_type": "unit_test",
                "name": "no_expect_test",
                "description": None,
                "tags": [],
                "meta": {},
                "given": [{"input": "ref('raw')", "rows": [{"id": 1}]}],
                # Missing expect
                "overrides": None,
                "depends_on": {"nodes": ["model.project.orders"]},
            },
        }

        manifest = create_manifest_with_tests({}, unit_tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        unit_test = list(artifacts.iter_unit_tests())[0]
        assert unit_test is not None
        assert unit_test.expect is None

    def test_relationship_test_with_single_dependency(self, tmp_path: Path) -> None:
        """Relationship test with only one depends_on node -> referenced_model_id=None."""
        tests = {
            "test.project.relationships_incomplete": {
                "resource_type": "test",
                "name": "relationships_incomplete",
                "description": "Incomplete relationship test",
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": """
SELECT o.customer_id
FROM orders o
LEFT JOIN customers c ON o.customer_id = c.id
WHERE c.id IS NULL
""",
                "column_name": "customer_id",
                "test_metadata": {
                    "name": "relationships",
                    "kwargs": {"to": "ref('customers')", "field": "id"},
                },
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    # Only one node, relationships expects two
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.relationships_incomplete")
        assert test is not None
        assert test.test_name == "relationships"
        assert test.model_id == "model.project.orders"
        # With only one dependency, referenced_model_id should be None
        assert test.referenced_model_id is None

    def test_test_metadata_as_string(self, tmp_path: Path) -> None:
        """test_metadata as string (not dict) -> should not crash.

        This tests the reviewer's concern about calling .get() on non-dict.
        """
        tests = {
            "test.project.string_metadata_test": {
                "resource_type": "test",
                "name": "string_metadata_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": "tests/custom.sql",
                "compiled_sql": "SELECT 1 WHERE 1=0",
                "column_name": None,
                "test_metadata": "this_is_a_string_not_dict",  # Malformed!
                "config": {
                    "severity": "error",
                    "where": None,
                    "store_failures": False,
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        # Should not crash - should be treated as singular test
        test = artifacts.get_test("test.project.string_metadata_test")
        assert test is not None
        # With non-dict test_metadata, test_name should be None
        assert test.test_name is None
        # Should be treated as singular since test_metadata is not a valid dict
        assert test.test_type == "singular"

    def test_test_metadata_as_list(self, tmp_path: Path) -> None:
        """test_metadata as list (not dict) -> should not crash."""
        tests = {
            "test.project.list_metadata_test": {
                "resource_type": "test",
                "name": "list_metadata_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": "tests/custom.sql",
                "compiled_sql": "SELECT 1 WHERE 1=0",
                "column_name": None,
                "test_metadata": ["unique", "not_null"],  # Malformed! Should be dict
                "config": {
                    "severity": "error",
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.list_metadata_test")
        assert test is not None
        assert test.test_type == "singular"  # Treated as singular due to invalid metadata

    def test_test_kwargs_as_list(self, tmp_path: Path) -> None:
        """test_kwargs as list (not dict) -> should not crash."""
        tests = {
            "test.project.list_kwargs_test": {
                "resource_type": "test",
                "name": "list_kwargs_test",
                "description": None,
                "tags": [],
                "meta": {},
                "original_file_path": None,
                "compiled_sql": "SELECT 1",
                "column_name": "id",
                "test_metadata": {
                    "name": "accepted_values",
                    "kwargs": ["value1", "value2"],  # Should be dict like {"values": [...]}
                },
                "config": {
                    "severity": "error",
                },
                "depends_on": {
                    "nodes": ["model.project.orders"],
                },
            },
        }

        manifest = create_manifest_with_tests(tests)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        test = artifacts.get_test("test.project.list_kwargs_test")
        assert test is not None
        # Non-dict kwargs are converted to None for safety
        assert test.test_kwargs is None
