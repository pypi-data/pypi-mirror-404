"""Tests for change detection functionality.

Tests cover:
- ModelChangeSet dataclass properties
- ChangeDetector change detection logic
- TestChangeSet dataclass properties
- UnitTestChangeSet dataclass properties
- ChangeDetector test change detection logic
"""
from unittest.mock import Mock

from lineage.backends.lineage.protocol import RawLineageQueryResult
from lineage.ingest.static_loaders.change_detection import (
    ChangeDetector,
    ModelChangeSet,
    TestChangeSet,
    UnitTestChangeSet,
)
from lineage.ingest.static_loaders.dbt.dbt_test_fingerprint import (
    compute_test_fingerprint,
    compute_unit_test_fingerprint,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    compute_model_fingerprint_result,
    compute_source_fingerprint,
)
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema, TableEntry

from tests.test_helpers import (
    create_mock_artifacts,
    create_mock_model,
    create_mock_test,
    create_mock_unit_test,
)


def get_fingerprint_hash(model_id: str, sql: str, dialect: str = "duckdb") -> str:
    """Get the hash-only fingerprint for a model's SQL.

    Uses compute_model_fingerprint_result and extracts just the hash,
    matching how ChangeDetector and the graph store fingerprints.
    """
    result = compute_model_fingerprint_result(
        resource_type="model",
        compiled_sql=sql,
        checksum=None,
        dialect=dialect,
        model_id=model_id,
    )
    assert result is not None, f"Failed to compute fingerprint for {model_id}"
    return result.hash


def setup_mock_storage_for_changes(
    mock_storage: Mock, fingerprint_rows: list[dict]
) -> None:
    """Helper to setup mock storage for change detection tests.

    Sets up the combined fingerprint + model ID query to return results.
    The query returns both id and model_fingerprint, with fingerprint being
    None for models that don't have one yet.
    """
    def mock_query(query: str):  # type: ignore[no-untyped-def]
        if "RETURN m.id AS id, m.model_fingerprint AS model_fingerprint" in query:
            # Combined query returns both id and fingerprint
            return RawLineageQueryResult(
                rows=fingerprint_rows,
                count=len(fingerprint_rows),
                query=query
            )
        return RawLineageQueryResult(rows=[], count=0, query=query)

    mock_storage.execute_raw_query.side_effect = mock_query


# ============================================================================
# Test ModelChangeSet (Unit Tests)
# ============================================================================


class TestModelChangeSet:
    """Tests for ModelChangeSet dataclass properties and methods."""

    def test_has_changes_true_when_added(self) -> None:
        """Verify has_changes returns True when models added."""
        change_set = ModelChangeSet(
            added=["model.test.new_model"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_modified(self) -> None:
        """Verify has_changes returns True when models modified."""
        change_set = ModelChangeSet(
            added=[],
            modified=["model.test.modified_model"],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_removed(self) -> None:
        """Verify has_changes returns True when models removed."""
        change_set = ModelChangeSet(
            added=[],
            modified=[],
            removed=["model.test.removed_model"],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_false_when_unchanged(self) -> None:
        """Verify has_changes returns False when all unchanged."""
        change_set = ModelChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=["model.test.existing_model"],
        )
        assert change_set.has_changes is False

    def test_models_to_process(self) -> None:
        """Verify models_to_process returns added + modified models."""
        change_set = ModelChangeSet(
            added=["model.test.new1", "model.test.new2"],
            modified=["model.test.modified1"],
            removed=["model.test.removed1"],
            unchanged=["model.test.unchanged1"],
        )
        result = change_set.models_to_process
        assert len(result) == 3
        assert "model.test.new1" in result
        assert "model.test.new2" in result
        assert "model.test.modified1" in result
        assert "model.test.removed1" not in result
        assert "model.test.unchanged1" not in result

    def test_empty_changeset(self) -> None:
        """Verify empty changeset properties."""
        change_set = ModelChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is False
        assert len(change_set.models_to_process) == 0


# ============================================================================
# Fingerprint helper (Unit Tests)
# ============================================================================


class TestModelFingerprint:
    """Tests for stable compiled-SQL fingerprinting."""

    def test_model_fingerprint_canonicalization_is_stable(self) -> None:
        """Whitespace/casing differences should canonicalize to the same fingerprint."""
        fp1 = get_fingerprint_hash("test.model.1", "select  1", dialect="duckdb")
        fp2 = get_fingerprint_hash("test.model.1", "SELECT 1", dialect="duckdb")
        assert fp1 == fp2


# ============================================================================
# Test ChangeDetector (Unit Tests)
# ============================================================================


class TestChangeDetector:
    """Tests for change detection logic with mock storage."""

    def test_detect_changes_added(self, mock_storage: Mock) -> None:
        """Detect new models not in graph."""
        # Graph is empty
        setup_mock_storage_for_changes(mock_storage, [])
        
        # Manifest has 2 new models
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
            create_mock_model("model.test.model2", compiled_sql="select 2"),
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 2
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert change_set.has_changes is True

    def test_detect_changes_modified(self, mock_storage: Mock) -> None:
        """Detect models with different fingerprints."""
        # Graph has model1 with old fingerprint (hash-only)
        old_fp = get_fingerprint_hash("model.test.model1", "select 1", dialect="duckdb")
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": old_fp},
        ])
        
        # Manifest has model1 with new fingerprint
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 2"),
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "model.test.model1" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_changes_removed(self, mock_storage: Mock) -> None:
        """Detect models in graph but not in manifest."""
        # Graph has model1
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": "deadbeef"},
        ])
        
        # Manifest is empty
        artifacts = create_mock_artifacts([])
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 1
        assert "model.test.model1" in change_set.removed

    def test_detect_changes_unchanged(self, mock_storage: Mock) -> None:
        """Detect models with same fingerprint."""
        fp = get_fingerprint_hash("model.test.model1", "select 1", dialect="duckdb")
        # Graph has model1 with fingerprint (hash-only)
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": fp},
        ])
        
        # Manifest has model1 with same fingerprint (after canonicalization)
        models = [
            create_mock_model("model.test.model1", compiled_sql="SELECT 1"),
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert len(change_set.unchanged) == 1
        assert "model.test.model1" in change_set.unchanged

    def test_detect_changes_mixed(self, mock_storage: Mock) -> None:
        """Detect combination of added/modified/removed/unchanged."""
        fp1 = get_fingerprint_hash("model.test.model1", "select 1", dialect="duckdb")
        # Graph has model1 (unchanged) and model2 (will be removed)
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": fp1},
            {"id": "model.test.model2", "model_fingerprint": "deadbeef"},
        ])
        
        # Manifest has model1 (unchanged), model3 (new), model4 (new)
        models = [
            create_mock_model("model.test.model1", compiled_sql="SELECT 1"),  # unchanged
            create_mock_model("model.test.model3", compiled_sql="select 3"),  # new
            create_mock_model("model.test.model4", compiled_sql="select 4"),  # new
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 2  # model3 and model4
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 1  # model2
        assert len(change_set.unchanged) == 1  # model1

    def test_detect_changes_no_checksum_in_graph(self, mock_storage: Mock) -> None:
        """Handle models in graph without fingerprint.

        When a model exists in the graph but has no fingerprint (e.g., from
        a previous load before fingerprinting was implemented), it should
        be treated as modified to ensure it gets reprocessed.
        """
        # Model exists in graph but has no fingerprint (None)
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": None},
        ])

        # Manifest has model1 with compiled SQL
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)

        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)

        # Model without fingerprint in graph should be treated as modified
        assert len(change_set.modified) == 1

    def test_detect_changes_no_checksum_in_manifest(self, mock_storage: Mock) -> None:
        """Handle models in manifest without compiled SQL fingerprint.

        Models without compiled_sql (empty string or None) cannot produce a
        fingerprint. This happens for:
        - Seeds (CSV data, no SQL)
        - Analyses that haven't been compiled
        - Models that failed dbt compilation

        These models are treated conservatively:
        - If not in graph: treated as "added" (processed as new)
        - If in graph: treated as "modified" (reprocessed for safety)

        This ensures correctness over efficiency - we'd rather reprocess
        a model unnecessarily than miss a change.
        """
        # Graph is empty
        setup_mock_storage_for_changes(mock_storage, [])

        # Manifest has model1 without compiled SQL (no fingerprint possible)
        models = [
            create_mock_model("model.test.model1", compiled_sql=""),
        ]
        artifacts = create_mock_artifacts(models)

        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)

        # Model without fingerprint should be treated as added (graph empty)
        assert len(change_set.added) == 1

    def test_detect_changes_no_checksum_in_manifest_existing_model(self, mock_storage: Mock) -> None:
        """Models without compiled_sql that exist in graph are treated as modified.

        See test_detect_changes_no_checksum_in_manifest for background on why
        models without compiled_sql cannot produce fingerprints.
        """
        # Graph has the model with a fingerprint from a previous load
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": "previous_fingerprint"},
        ])

        # Manifest has model1 but without compiled SQL (e.g., compilation failed this time)
        models = [
            create_mock_model("model.test.model1", compiled_sql=""),
        ]
        artifacts = create_mock_artifacts(models)

        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)

        # Model without fingerprint in manifest but exists in graph -> modified (safe)
        assert len(change_set.modified) == 1
        assert "model.test.model1" in change_set.modified

    def test_detect_changes_empty_graph(self, mock_storage: Mock) -> None:
        """First load (empty graph)."""
        # Graph is empty
        setup_mock_storage_for_changes(mock_storage, [])
        
        # Manifest has models
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
            create_mock_model("model.test.model2", compiled_sql="select 2"),
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 2
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0

    def test_detect_changes_query_failure(self, mock_storage: Mock) -> None:
        """Handle storage query failures gracefully."""
        # Storage query fails
        mock_storage.execute_raw_query.side_effect = Exception("Query failed")

        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)

        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)

        # Should treat all models as new when query fails
        assert len(change_set.added) == 1

    def test_detect_changes_with_custom_dialect_resolver(self, mock_storage: Mock) -> None:
        """Custom dialect_resolver overrides artifacts.adapter_type for fingerprinting.

        This is useful when:
        - Different models use different SQL dialects
        - The manifest adapter_type doesn't match the actual SQL dialect
        - Testing with a specific dialect regardless of manifest metadata
        """
        # Graph has an unrelated model - this ensures the fingerprinting loop runs
        # (empty graph triggers early return optimization that skips fingerprinting)
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.unrelated_model", "model_fingerprint": "abc123"}
        ])

        # Create models - the SQL is dialect-agnostic for this test
        models = [
            create_mock_model("model.test.snowflake_model", compiled_sql="select 1"),
            create_mock_model("model.test.duckdb_model", compiled_sql="select 2"),
        ]
        artifacts = create_mock_artifacts(models)

        # Track which dialects were requested for each model
        dialect_calls: dict[str, str] = {}

        def custom_dialect_resolver(model_id: str) -> str:
            """Return different dialects based on model naming convention."""
            if "snowflake" in model_id:
                dialect = "snowflake"
            else:
                dialect = "duckdb"
            dialect_calls[model_id] = dialect
            return dialect

        detector = ChangeDetector()
        change_set = detector.detect_changes(
            artifacts, mock_storage, dialect_resolver=custom_dialect_resolver
        )

        # Verify the resolver was called for each model
        assert len(dialect_calls) == 2
        assert dialect_calls["model.test.snowflake_model"] == "snowflake"
        assert dialect_calls["model.test.duckdb_model"] == "duckdb"

        # Both models should be detected as added (empty graph)
        assert len(change_set.added) == 2

    def test_detect_changes_dialect_resolver_affects_fingerprint(self, mock_storage: Mock) -> None:
        """Dialect affects fingerprint canonicalization, so resolver choice matters.

        Different dialects may canonicalize SQL differently, leading to different
        fingerprints for the same SQL string. This test verifies that using a
        consistent dialect_resolver produces consistent fingerprints.
        """
        # Compute fingerprint with duckdb dialect for the graph state
        fp_duckdb = get_fingerprint_hash("model.test.m1", "select 1", dialect="duckdb")

        # Graph has the model with a duckdb-computed fingerprint
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.m1", "model_fingerprint": fp_duckdb},
        ])

        models = [
            create_mock_model("model.test.m1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)

        detector = ChangeDetector()

        # Using duckdb dialect should show unchanged (same fingerprint)
        change_set_duckdb = detector.detect_changes(
            artifacts, mock_storage, dialect_resolver=lambda _: "duckdb"
        )
        assert len(change_set_duckdb.unchanged) == 1
        assert len(change_set_duckdb.modified) == 0

        # Using snowflake dialect may show modified if fingerprints differ
        # (This depends on whether sqlglot produces different canonical forms)
        change_set_snowflake = detector.detect_changes(
            artifacts, mock_storage, dialect_resolver=lambda _: "snowflake"
        )
        # The model is either unchanged (same canonical form) or modified (different)
        # We just verify the resolver was used by checking the model was categorized
        assert (
            len(change_set_snowflake.unchanged) == 1 or len(change_set_snowflake.modified) == 1
        )


# ============================================================================
# Fingerprint with schema tests (D4)
# ============================================================================


class TestFingerprintWithSchema:
    """Tests for schema-aware fingerprint computation."""

    def test_fingerprint_with_schema_expands_star(self) -> None:
        """Adding a column to the schema should change the fingerprint for SELECT *."""
        entry_2col = TableEntry(
            database="my_db",
            schema="my_schema",
            table="my_table",
            columns=(("id", "INT"), ("name", "VARCHAR")),
        )
        schema_2col = SqlglotSchema(_entries=(entry_2col,))

        entry_3col = TableEntry(
            database="my_db",
            schema="my_schema",
            table="my_table",
            columns=(("id", "INT"), ("name", "VARCHAR"), ("email", "VARCHAR")),
        )
        schema_3col = SqlglotSchema(_entries=(entry_3col,))

        sql = "SELECT * FROM my_db.my_schema.my_table"

        fp_2col = compute_model_fingerprint_result(
            resource_type="model",
            compiled_sql=sql,
            checksum=None,
            dialect="duckdb",
            schema=schema_2col,
            model_id="model.test.my_model",
        )
        fp_3col = compute_model_fingerprint_result(
            resource_type="model",
            compiled_sql=sql,
            checksum=None,
            dialect="duckdb",
            schema=schema_3col,
            model_id="model.test.my_model",
        )

        assert fp_2col is not None
        assert fp_3col is not None
        # Different column sets should produce different hashes
        assert fp_2col.hash != fp_3col.hash


# ============================================================================
# Source fingerprint database exclusion tests (D5)
# ============================================================================


class TestSourceFingerprintDatabaseExclusion:
    """Tests for source fingerprint excluding database from hash."""

    def test_source_fingerprint_excludes_database(self) -> None:
        """Same schema+table with different databases should produce identical hashes."""
        fp1 = compute_source_fingerprint(
            database="prod_db",
            schema="raw",
            identifier="orders",
            columns={"id": "INT", "amount": "DECIMAL"},
        )
        fp2 = compute_source_fingerprint(
            database="dev_db",
            schema="raw",
            identifier="orders",
            columns={"id": "INT", "amount": "DECIMAL"},
        )
        assert fp1.hash == fp2.hash

    def test_source_fingerprint_differs_by_schema(self) -> None:
        """Different schemas should produce different hashes."""
        fp1 = compute_source_fingerprint(
            database="my_db",
            schema="raw",
            identifier="orders",
            columns={"id": "INT"},
        )
        fp2 = compute_source_fingerprint(
            database="my_db",
            schema="staging",
            identifier="orders",
            columns={"id": "INT"},
        )
        assert fp1.hash != fp2.hash


# ============================================================================
# Test TestChangeSet (Unit Tests)
# ============================================================================


class TestTestChangeSet:
    """Tests for TestChangeSet dataclass properties and methods."""

    def test_has_changes_true_when_added(self) -> None:
        """Verify has_changes returns True when tests added."""
        change_set = TestChangeSet(
            added=["test.project.unique_orders_id"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_modified(self) -> None:
        """Verify has_changes returns True when tests modified."""
        change_set = TestChangeSet(
            added=[],
            modified=["test.project.unique_orders_id"],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_removed(self) -> None:
        """Verify has_changes returns True when tests removed."""
        change_set = TestChangeSet(
            added=[],
            modified=[],
            removed=["test.project.unique_orders_id"],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_false_when_unchanged(self) -> None:
        """Verify has_changes returns False when all unchanged."""
        change_set = TestChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=["test.project.unique_orders_id"],
        )
        assert change_set.has_changes is False

    def test_tests_to_process_returns_added_and_modified(self) -> None:
        """Verify tests_to_process returns added + modified tests."""
        change_set = TestChangeSet(
            added=["test.project.new1", "test.project.new2"],
            modified=["test.project.modified1"],
            removed=["test.project.removed1"],
            unchanged=["test.project.unchanged1"],
        )
        result = change_set.tests_to_process
        assert len(result) == 3
        assert "test.project.new1" in result
        assert "test.project.new2" in result
        assert "test.project.modified1" in result
        assert "test.project.removed1" not in result
        assert "test.project.unchanged1" not in result

    def test_empty_changeset(self) -> None:
        """Verify empty changeset properties."""
        change_set = TestChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is False
        assert len(change_set.tests_to_process) == 0


# ============================================================================
# Test UnitTestChangeSet (Unit Tests)
# ============================================================================


class TestUnitTestChangeSet:
    """Tests for UnitTestChangeSet dataclass properties and methods."""

    def test_has_changes_true_when_added(self) -> None:
        """Verify has_changes returns True when unit tests added."""
        change_set = UnitTestChangeSet(
            added=["unit_test.project.test_orders_logic"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_modified(self) -> None:
        """Verify has_changes returns True when unit tests modified."""
        change_set = UnitTestChangeSet(
            added=[],
            modified=["unit_test.project.test_orders_logic"],
            removed=[],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_true_when_removed(self) -> None:
        """Verify has_changes returns True when unit tests removed."""
        change_set = UnitTestChangeSet(
            added=[],
            modified=[],
            removed=["unit_test.project.test_orders_logic"],
            unchanged=[],
        )
        assert change_set.has_changes is True

    def test_has_changes_false_when_unchanged(self) -> None:
        """Verify has_changes returns False when all unchanged."""
        change_set = UnitTestChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=["unit_test.project.test_orders_logic"],
        )
        assert change_set.has_changes is False

    def test_tests_to_process_returns_added_and_modified(self) -> None:
        """Verify tests_to_process returns added + modified unit tests."""
        change_set = UnitTestChangeSet(
            added=["unit_test.project.new1"],
            modified=["unit_test.project.modified1"],
            removed=["unit_test.project.removed1"],
            unchanged=["unit_test.project.unchanged1"],
        )
        result = change_set.tests_to_process
        assert len(result) == 2
        assert "unit_test.project.new1" in result
        assert "unit_test.project.modified1" in result
        assert "unit_test.project.removed1" not in result
        assert "unit_test.project.unchanged1" not in result


# ============================================================================
# Helper for Test Change Detection
# ============================================================================


def setup_mock_storage_for_test_changes(
    mock_storage: Mock, fingerprint_rows: list[dict]
) -> None:
    """Helper to setup mock storage for test change detection tests.

    Sets up the test fingerprint query to return results.
    """
    def mock_query(query: str):  # type: ignore[no-untyped-def]
        if "RETURN t.id AS id, t.test_fingerprint AS test_fingerprint" in query:
            return RawLineageQueryResult(
                rows=fingerprint_rows,
                count=len(fingerprint_rows),
                query=query
            )
        return RawLineageQueryResult(rows=[], count=0, query=query)

    mock_storage.execute_raw_query.side_effect = mock_query


def setup_mock_storage_for_unit_test_changes(
    mock_storage: Mock, fingerprint_rows: list[dict]
) -> None:
    """Helper to setup mock storage for unit test change detection tests.

    Sets up the unit test fingerprint query to return results.
    """
    def mock_query(query: str):  # type: ignore[no-untyped-def]
        if "MATCH (t:DbtUnitTest)" in query:
            return RawLineageQueryResult(
                rows=fingerprint_rows,
                count=len(fingerprint_rows),
                query=query
            )
        return RawLineageQueryResult(rows=[], count=0, query=query)

    mock_storage.execute_raw_query.side_effect = mock_query


# ============================================================================
# Test ChangeDetector.detect_test_changes (Unit Tests)
# ============================================================================


class TestDetectTestChanges:
    """Tests for ChangeDetector.detect_test_changes()."""

    def test_detect_test_changes_added(self, mock_storage: Mock) -> None:
        """Empty graph + manifest with tests -> all added."""
        setup_mock_storage_for_test_changes(mock_storage, [])

        models = [create_mock_model("model.test.orders")]
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
            create_mock_test(
                "test.project.not_null_orders_id",
                test_type="generic",
                test_name="not_null",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 2
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert change_set.has_changes is True

    def test_detect_test_changes_modified(self, mock_storage: Mock) -> None:
        """Graph has test with old fingerprint -> modified."""
        # Compute old fingerprint with different severity
        old_fp = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs=None,
            severity="warn",  # Old severity
            where_clause=None,
            store_failures=False,
        )
        setup_mock_storage_for_test_changes(mock_storage, [
            {"id": "test.project.unique_orders_id", "test_fingerprint": old_fp},
        ])

        models = [create_mock_model("model.test.orders")]
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="error",  # New severity (changed)
            ),
        ]
        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "test.project.unique_orders_id" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_test_changes_removed(self, mock_storage: Mock) -> None:
        """Graph has test not in manifest -> removed."""
        setup_mock_storage_for_test_changes(mock_storage, [
            {"id": "test.project.old_test", "test_fingerprint": "deadbeef"},
        ])

        models = [create_mock_model("model.test.orders")]
        # Manifest is empty - no tests
        artifacts = create_mock_artifacts(models, tests=[])

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 1
        assert "test.project.old_test" in change_set.removed

    def test_detect_test_changes_unchanged(self, mock_storage: Mock) -> None:
        """Graph has test with same fingerprint -> unchanged."""
        # Compute fingerprint that matches manifest
        # Note: test_kwargs={} because the manifest flow converts None to {}
        fp = compute_test_fingerprint(
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs={},  # Empty dict to match manifest parsing
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        setup_mock_storage_for_test_changes(mock_storage, [
            {"id": "test.project.unique_orders_id", "test_fingerprint": fp},
        ])

        models = [create_mock_model("model.test.orders")]
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="error",
            ),
        ]
        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert len(change_set.unchanged) == 1
        assert "test.project.unique_orders_id" in change_set.unchanged

    def test_detect_test_changes_mixed(self, mock_storage: Mock) -> None:
        """Combination of added/modified/removed/unchanged."""
        # unchanged test fingerprint
        # Note: test_kwargs={} because the manifest flow converts None to {}
        fp_unchanged = compute_test_fingerprint(
            test_type="generic",
            test_name="not_null",
            column_name="id",
            model_id="model.test.orders",
            test_kwargs={},  # Empty dict to match manifest parsing
            severity="error",
            where_clause=None,
            store_failures=False,
        )
        setup_mock_storage_for_test_changes(mock_storage, [
            {"id": "test.project.unchanged_test", "test_fingerprint": fp_unchanged},
            {"id": "test.project.removed_test", "test_fingerprint": "old_fp"},
        ])

        models = [create_mock_model("model.test.orders")]
        tests = [
            # Unchanged
            create_mock_test(
                "test.project.unchanged_test",
                test_type="generic",
                test_name="not_null",
                column_name="id",
                model_id="model.test.orders",
            ),
            # Added (new)
            create_mock_test(
                "test.project.new_test",
                test_type="generic",
                test_name="unique",
                column_name="name",
                model_id="model.test.orders",
            ),
        ]
        # removed_test is not in manifest

        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 1
        assert "test.project.new_test" in change_set.added
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 1
        assert "test.project.removed_test" in change_set.removed
        assert len(change_set.unchanged) == 1
        assert "test.project.unchanged_test" in change_set.unchanged

    def test_detect_test_changes_empty_graph(self, mock_storage: Mock) -> None:
        """First load scenario (empty graph)."""
        setup_mock_storage_for_test_changes(mock_storage, [])

        models = [create_mock_model("model.test.orders")]
        tests = [
            create_mock_test(
                "test.project.test1",
                model_id="model.test.orders",
            ),
            create_mock_test(
                "test.project.test2",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 2
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0

    def test_detect_test_changes_query_failure_returns_empty(self, mock_storage: Mock) -> None:
        """Graceful handling of query errors."""
        mock_storage.execute_raw_query.side_effect = Exception("Query failed")

        models = [create_mock_model("model.test.orders")]
        tests = [
            create_mock_test(
                "test.project.test1",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts(models, tests=tests)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, mock_storage)

        # Should treat all tests as new when query fails
        assert len(change_set.added) == 1


# ============================================================================
# Test ChangeDetector.detect_unit_test_changes (Unit Tests)
# ============================================================================


class TestDetectUnitTestChanges:
    """Tests for ChangeDetector.detect_unit_test_changes()."""

    def test_detect_unit_test_changes_added(self, mock_storage: Mock) -> None:
        """Empty graph + manifest with unit tests -> all added."""
        setup_mock_storage_for_unit_test_changes(mock_storage, [])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 1
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert change_set.has_changes is True

    def test_detect_unit_test_changes_modified(self, mock_storage: Mock) -> None:
        """Graph has unit test with old fingerprint -> modified."""
        # Old fingerprint with different expect
        old_fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1, "total": 100}]},  # Old expect
            overrides=None,
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_orders_logic", "test_fingerprint": old_fp},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1, "total": 200}]},  # New expect (changed)
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "unit_test.project.test_orders_logic" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_unit_test_changes_removed(self, mock_storage: Mock) -> None:
        """Graph has unit test not in manifest -> removed."""
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.old_test", "test_fingerprint": "deadbeef"},
        ])

        models = [create_mock_model("model.test.orders")]
        # Manifest has no unit tests
        artifacts = create_mock_artifacts(models, unit_tests=[])

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 1
        assert "unit_test.project.old_test" in change_set.removed

    def test_detect_unit_test_changes_unchanged(self, mock_storage: Mock) -> None:
        """Graph has unit test with same fingerprint -> unchanged."""
        fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_orders_logic", "test_fingerprint": fp},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert len(change_set.removed) == 0
        assert len(change_set.unchanged) == 1
        assert "unit_test.project.test_orders_logic" in change_set.unchanged

    def test_detect_unit_test_changes_modified_given(self, mock_storage: Mock) -> None:
        """Changed given data -> detected as modified."""
        # Old fingerprint with original given data
        old_fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],  # Original given
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_orders_logic", "test_fingerprint": old_fp},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 2}]}],  # Changed given
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "unit_test.project.test_orders_logic" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_unit_test_changes_modified_expect(self, mock_storage: Mock) -> None:
        """Changed expect data -> detected as modified."""
        # Old fingerprint with original expect data
        old_fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1, "total": 100}]},  # Original expect
            overrides=None,
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_orders_logic", "test_fingerprint": old_fp},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1, "total": 200}]},  # Changed expect
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "unit_test.project.test_orders_logic" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_unit_test_changes_modified_overrides(self, mock_storage: Mock) -> None:
        """Changed overrides -> detected as modified."""
        # Old fingerprint with original overrides
        old_fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides={"vars": {"date": "2024-01-01"}},  # Original overrides
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_orders_logic", "test_fingerprint": old_fp},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
                overrides={"vars": {"date": "2024-06-01"}},  # Changed overrides
            ),
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 0
        assert len(change_set.modified) == 1
        assert "unit_test.project.test_orders_logic" in change_set.modified
        assert len(change_set.removed) == 0

    def test_detect_unit_test_changes_mixed(self, mock_storage: Mock) -> None:
        """Combination of added/modified/removed/unchanged unit tests."""
        # Set up graph with 3 unit tests
        unchanged_fp = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
            expect={"rows": [{"id": 1}]},
            overrides=None,
        )
        old_fp_modified = compute_unit_test_fingerprint(
            model_id="model.test.orders",
            given=[{"input": "ref('raw')", "rows": [{"id": 2}]}],
            expect={"rows": [{"id": 2}]},
            overrides=None,
        )
        setup_mock_storage_for_unit_test_changes(mock_storage, [
            {"id": "unit_test.project.test_unchanged", "test_fingerprint": unchanged_fp},
            {"id": "unit_test.project.test_modified", "test_fingerprint": old_fp_modified},
            {"id": "unit_test.project.test_removed", "test_fingerprint": "deadbeef"},
        ])

        models = [create_mock_model("model.test.orders")]
        unit_tests = [
            # Unchanged
            create_mock_unit_test(
                "unit_test.project.test_unchanged",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
            # Modified (changed expect)
            create_mock_unit_test(
                "unit_test.project.test_modified",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 2}]}],
                expect={"rows": [{"id": 2, "extra": "field"}]},  # Changed
            ),
            # Added (new)
            create_mock_unit_test(
                "unit_test.project.test_new",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 3}]}],
                expect={"rows": [{"id": 3}]},
            ),
            # test_removed is not in manifest (will be in removed)
        ]
        artifacts = create_mock_artifacts(models, unit_tests=unit_tests)

        detector = ChangeDetector()
        change_set = detector.detect_unit_test_changes(artifacts, mock_storage)

        assert len(change_set.added) == 1
        assert "unit_test.project.test_new" in change_set.added
        assert len(change_set.modified) == 1
        assert "unit_test.project.test_modified" in change_set.modified
        assert len(change_set.removed) == 1
        assert "unit_test.project.test_removed" in change_set.removed
        assert len(change_set.unchanged) == 1
        assert "unit_test.project.test_unchanged" in change_set.unchanged

