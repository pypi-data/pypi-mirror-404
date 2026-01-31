"""Tests for incremental graph loading functionality.

Tests cover:
- LineageBuilder.write_incremental method
- Column lineage incremental updates
"""
# ruff: noqa: I001

import json
from pathlib import Path

import pytest

from lineage.backends.lineage.models import DerivesFrom
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.types import NodeLabel
from lineage.ingest.progress import ProgressTracker
from lineage.ingest.static_loaders.change_detection import (
    ChangeDetector,
    ModelChangeSet,
    TestChangeSet,
    UnitTestChangeSet,
)
from lineage.ingest.static_loaders.dbt.builder import LineageBuilder
from lineage.backends.lineage.models import DbtColumn as GraphDbtColumn
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtColumn, FilteredDbtArtifacts

from tests.test_helpers import (
    create_mock_artifacts,
    create_mock_macro,
    create_mock_model,
    create_mock_source,
    create_mock_test,
    create_mock_unit_test,
)


@pytest.mark.integration
class TestIncrementalGraphLoading:
    """Tests for LineageBuilder.write_incremental."""

    def test_sqlglot_schema_returns_defensive_copy(self) -> None:
        """Mutating a returned SQLGlot schema dict should not corrupt cached state."""
        columns = {"id": DbtColumn(name="id", description="", data_type="int")}
        model = create_mock_model("model.test.model1", checksum="abc123", columns=columns)
        artifacts = create_mock_artifacts([model])

        # Raw artifacts schema.to_dict() should return a fresh copy safe to mutate.
        raw_schema = artifacts.sqlglot_schema().to_dict()
        raw_schema["test_db"]["test_schema"]["model1"]["id"] = "text"
        assert artifacts.sqlglot_schema().to_dict()["test_db"]["test_schema"]["model1"]["id"] == "int"

        # Filtered view schema should be safe to mutate as well.
        filtered = FilteredDbtArtifacts(artifacts, model_ids={"model.test.model1"})
        filtered_schema = filtered.sqlglot_schema().to_dict()
        filtered_schema["test_db"]["test_schema"]["model1"]["id"] = "text"
        assert filtered.sqlglot_schema().to_dict()["test_db"]["test_schema"]["model1"]["id"] == "int"

    def test_write_incremental_added_models(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Load only new models."""
        # Initial load: model1
        models_v1 = [
            create_mock_model("model.test.model1", checksum="abc123"),
        ]
        artifacts_v1 = create_mock_artifacts(models_v1)
        
        # Create artifacts directory structure with proper manifest
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        manifest_v1 = artifacts_v1.manifest
        (artifacts_dir / "manifest.json").write_text(json.dumps(manifest_v1))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)
        
        # Incremental load: add model2
        change_set = ModelChangeSet(
            added=["model.test.model2"],
            modified=[],
            removed=[],
            unchanged=["model.test.model1"],
        )
        
        models_v2 = [
            create_mock_model("model.test.model1", checksum="abc123"),
            create_mock_model("model.test.model2", checksum="def456"),
        ]
        artifacts_v2 = create_mock_artifacts(models_v2)
        
        # Update builder's artifacts directly
        builder._artifacts = artifacts_v2
        
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify both models exist
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel) RETURN m.id AS id ORDER BY m.id"
        )
        assert result.count == 2
        ids = [row["id"] for row in result.rows]
        assert "model.test.model1" in ids
        assert "model.test.model2" in ids

    def test_write_incremental_removed_models(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Delete removed models with cascade."""
        # Initial load: model1 and model2
        models_v1 = [
            create_mock_model("model.test.model1", checksum="abc123"),
            create_mock_model("model.test.model2", checksum="def456"),
        ]
        artifacts_v1 = create_mock_artifacts(models_v1)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)
        
        # Incremental load: remove model2
        change_set = ModelChangeSet(
            added=[],
            modified=[],
            removed=["model.test.model2"],
            unchanged=["model.test.model1"],
        )
        
        models_v2 = [
            create_mock_model("model.test.model1", checksum="abc123"),
        ]
        artifacts_v2 = create_mock_artifacts(models_v2)
        builder.loader._artifacts = artifacts_v2
        
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify only model1 exists
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel) RETURN m.id AS id"
        )
        assert result.count == 1
        assert result.rows[0]["id"] == "model.test.model1"

    def test_write_incremental_no_changes(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Skip processing when no changes."""
        # Initial load
        models = [
            create_mock_model("model.test.model1", checksum="abc123"),
        ]
        artifacts = create_mock_artifacts(models)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)
        
        # Incremental load with no changes
        change_set = ModelChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=["model.test.model1"],
        )
        
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify model still exists (no errors)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel) RETURN m.id AS id"
        )
        assert result.count == 1

    def test_write_incremental_clears_stale_dependency_edges(
        self,
        falkordblite_storage: LineageStorage,
        tmp_path: Path,
    ) -> None:
        """Incremental updates must not leave stale DEPENDS_ON / USES_MACRO edges.

        Regression:
        - v1: model.a depends on model.b and uses macro.m1
        - v2: model.a depends on model.c and uses macro.m2
        If we preserve the DbtModel node during incremental updates, we must still
        clear outgoing dependency edges for model.a or the graph will accumulate
        incorrect/stale relationships.
        """
        macros = [
            create_mock_macro("macro.test.m1"),
            create_mock_macro("macro.test.m2"),
        ]

        # Initial load: a -> b, a -> m1
        models_v1 = [
            create_mock_model(
                "model.test.a",
                checksum="a_v1",
                depends_on_nodes=["model.test.b"],
                depends_on_macros=["macro.test.m1"],
            ),
            create_mock_model("model.test.b", checksum="b_v1"),
            create_mock_model("model.test.c", checksum="c_v1"),
        ]
        artifacts_v1 = create_mock_artifacts(models_v1, macros=macros)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:DEPENDS_ON]->(:DbtModel {id: 'model.test.b'}) RETURN 1"
            ).count
            == 1
        )
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:USES_MACRO]->(:DbtMacro {id: 'macro.test.m1'}) RETURN 1"
            ).count
            == 1
        )

        # Incremental update: a -> c, a -> m2
        models_v2 = [
            create_mock_model(
                "model.test.a",
                checksum="a_v2",
                depends_on_nodes=["model.test.c"],
                depends_on_macros=["macro.test.m2"],
            ),
            create_mock_model("model.test.b", checksum="b_v1"),  # unchanged
            create_mock_model("model.test.c", checksum="c_v1"),  # unchanged
        ]
        artifacts_v2 = create_mock_artifacts(models_v2, macros=macros)

        change_set = ModelChangeSet(
            added=[],
            modified=["model.test.a"],
            removed=[],
            unchanged=["model.test.b", "model.test.c"],
        )

        builder._artifacts = artifacts_v2
        builder.write_incremental(falkordblite_storage, change_set)

        # Old edges must be gone
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:DEPENDS_ON]->(:DbtModel {id: 'model.test.b'}) RETURN 1"
            ).count
            == 0
        )
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:USES_MACRO]->(:DbtMacro {id: 'macro.test.m1'}) RETURN 1"
            ).count
            == 0
        )

        # New edges must exist
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:DEPENDS_ON]->(:DbtModel {id: 'model.test.c'}) RETURN 1"
            ).count
            == 1
        )
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (:DbtModel {id: 'model.test.a'})-[:USES_MACRO]->(:DbtMacro {id: 'macro.test.m2'}) RETURN 1"
            ).count
            == 1
        )

    def test_physical_columns_exist_without_macros(self) -> None:
        """Physical columns should be created even when no macros are present."""
        cols = {
            "derived": DbtColumn(name="derived", description="", data_type="int")
        }
        model = create_mock_model(
            "model.test.model1",
            checksum="abc123",
            columns=cols,
        )
        artifacts = create_mock_artifacts([model])

        builder = LineageBuilder()
        tracker = ProgressTracker()
        nodes, _ = builder._collect_nodes_and_edges(
            artifacts,
            create_physical_nodes=True,
            tracker=tracker,
        )

        physical_columns = [
            node for node in nodes if node.node_label == NodeLabel.PHYSICAL_COLUMN
        ]
        assert len(physical_columns) == len(cols)

    def test_incremental_column_lineage_resolves_upstream(self) -> None:
        """Incremental lineage keeps upstream model lookup even when filtered."""
        upstream_columns = {
            "upstream_col": DbtColumn(name="upstream_col", description="", data_type="int")
        }
        upstream = create_mock_model(
            "model.test.upstream",
            checksum="abc123",
            columns=upstream_columns,
        )
        derived_columns = {
            "derived": DbtColumn(name="derived", description="", data_type="int")
        }
        changed = create_mock_model(
            "model.test.changed",
            checksum="def456",
            compiled_sql="SELECT upstream_col AS derived FROM test_schema.upstream",
            columns=derived_columns,
        )

        artifacts = create_mock_artifacts([upstream, changed])
        filtered_artifacts = FilteredDbtArtifacts(
            artifacts,
            model_ids={"model.test.changed"},
        )

        builder = LineageBuilder()
        tracker = ProgressTracker()
        _, edges = builder._collect_nodes_and_edges(
            filtered_artifacts,
            create_physical_nodes=False,
            tracker=tracker,
        )

        target_column_id = GraphDbtColumn.identifier("model.test.changed", "derived").id
        source_column_id = GraphDbtColumn.identifier("model.test.upstream", "upstream_col").id

        derivations = [
            (from_node, to_node, edge)
            for from_node, to_node, edge in edges
            if isinstance(edge, DerivesFrom)
            and from_node.id == target_column_id
            and to_node.id == source_column_id
        ]

        assert derivations

    def test_change_detector_agrees_with_builder_fingerprint(
        self,
        falkordblite_storage: LineageStorage,
        tmp_path: Path,
    ) -> None:
        """ChangeDetector should see no changes when builder fingerprint matches."""
        columns = {
            "derived": DbtColumn(name="derived", description="", data_type="int")
        }
        model = create_mock_model(
            "model.test.model1",
            checksum="abc123",
            columns=columns,
        )
        artifacts = create_mock_artifacts([model])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        def dialect_resolver(model_id: str) -> str | None:
            return builder.config.sqlglot.per_model_dialects.get(
                model_id, builder.config.sqlglot.default_dialect
            )
        detector = ChangeDetector()
        change_set = detector.detect_changes(
            artifacts,
            falkordblite_storage,
            dialect_resolver=dialect_resolver,
        )

        assert change_set.has_changes is False
        assert change_set.unchanged == ["model.test.model1"]
    def test_write_incremental_checksum_preserved(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Verify checksums stored correctly."""
        models = [
            create_mock_model("model.test.model1", checksum="abc123"),
        ]
        artifacts = create_mock_artifacts(models)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        
        change_set = ModelChangeSet(
            added=["model.test.model1"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify checksum stored
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.model1'}) RETURN m.checksum AS checksum"
        )
        assert result.count == 1
        assert result.rows[0]["checksum"] == "abc123"


@pytest.mark.integration
class TestColumnLineageIncremental:
    """Tests for column lineage extraction for changed models only."""

    def test_column_lineage_only_changed_models(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Extract lineage only for changed models."""
        # This test would require models with actual SQL that has column dependencies
        # For now, we test that the filtering mechanism exists
        models = [
            create_mock_model("model.test.model1", checksum="abc123", compiled_sql="SELECT col1 FROM source1"),
        ]
        artifacts = create_mock_artifacts(models)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        
        change_set = ModelChangeSet(
            added=["model.test.model1"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        
        # This should work - column lineage extraction will be called with filtered models
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify model was loaded
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel) RETURN m.id AS id"
        )
        assert result.count == 1

    def test_column_lineage_cleanup_before_extraction(self, falkordblite_storage: LineageStorage) -> None:
        """Verify old child nodes deleted for modified models via delete_model_cascade."""
        # This test verifies that delete_model_cascade with preserve_model=True works correctly.
        # The method is now called on the storage adapter, not on the builder.
        # For empty case, it should be a no-op
        result = falkordblite_storage.delete_model_cascade("model.test.nonexistent", preserve_model=True)
        assert result == 0  # No nodes deleted for non-existent model


    def test_write_incremental_modified_model_column_removed(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Verify old columns are deleted when model is modified to remove a column."""
        # Initial load: model with columns A, B, C
        cols_v1 = {
            "col_a": DbtColumn(name="col_a", description="", data_type="string"),
            "col_b": DbtColumn(name="col_b", description="", data_type="int"),
            "col_c": DbtColumn(name="col_c", description="", data_type="bool"),
        }
        model_v1 = create_mock_model(
            "model.test.model1",
            checksum="v1_checksum",
            compiled_sql="SELECT a AS col_a, b AS col_b, c AS col_c FROM source",
            columns=cols_v1,
        )
        artifacts_v1 = create_mock_artifacts([model_v1])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify all 3 columns exist
        result = falkordblite_storage.execute_raw_query(
            "MATCH (c:DbtColumn) WHERE c.parent_id = 'model.test.model1' RETURN c.name AS name ORDER BY c.name"
        )
        assert result.count == 3
        names_v1 = [row["name"] for row in result.rows]
        assert names_v1 == ["col_a", "col_b", "col_c"]

        # Modify model: remove col_c, keep A and B
        cols_v2 = {
            "col_a": DbtColumn(name="col_a", description="", data_type="string"),
            "col_b": DbtColumn(name="col_b", description="", data_type="int"),
        }
        model_v2 = create_mock_model(
            "model.test.model1",
            checksum="v2_checksum",
            compiled_sql="SELECT a AS col_a, b AS col_b FROM source",
            columns=cols_v2,
        )
        artifacts_v2 = create_mock_artifacts([model_v2])

        # Incremental load with model marked as modified
        change_set = ModelChangeSet(
            added=[],
            modified=["model.test.model1"],
            removed=[],
            unchanged=[],
        )

        builder._artifacts = artifacts_v2
        builder.write_incremental(falkordblite_storage, change_set)

        # Verify only 2 columns exist (col_c should be deleted)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (c:DbtColumn) WHERE c.parent_id = 'model.test.model1' RETURN c.name AS name ORDER BY c.name"
        )
        assert result.count == 2
        names_v2 = [row["name"] for row in result.rows]
        assert names_v2 == ["col_a", "col_b"]
        assert "col_c" not in names_v2


@pytest.mark.integration
class TestSourceFingerprinting:
    """Tests for source fingerprint computation."""

    def test_source_fingerprint_computed_on_load(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Verify source fingerprints are computed and stored during load."""
        from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
            FingerprintType,
        )

        # Create a source with columns
        model = create_mock_model("model.test.model1", checksum="abc123")
        artifacts = create_mock_artifacts([model])

        # Add a source to the manifest
        artifacts.manifest["sources"] = {
            "source.test.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "source_name": "raw",
                "source_description": "",
                "database": "analytics",
                "schema": "raw",
                "identifier": "orders_table",
                "loader": "fivetran",
                "columns": {
                    "id": {"description": "Primary key"},
                    "amount": {"description": "Order amount"},
                },
            }
        }
        artifacts.catalog["sources"] = {
            "source.test.raw.orders": {
                "columns": {
                    "id": {"type": "integer"},
                    "amount": {"type": "decimal"},
                }
            }
        }

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify source exists with fingerprint
        result = falkordblite_storage.execute_raw_query(
            "MATCH (s:DbtSource {id: 'source.test.raw.orders'}) "
            "RETURN s.source_fingerprint AS fp, s.fingerprint_type AS fp_type"
        )
        assert result.count == 1
        row = result.rows[0]
        assert row["fp"] is not None
        # Fingerprint is hash-only (no prefix); type is stored separately
        assert row["fp_type"] == FingerprintType.SOURCE

    def test_source_fingerprint_deterministic(self) -> None:
        """Verify source fingerprint is deterministic for same inputs."""
        from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
            compute_source_fingerprint,
        )

        fp1 = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "integer", "amount": "decimal"},
        )
        fp2 = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "integer", "amount": "decimal"},
        )
        assert fp1.hash == fp2.hash

    def test_source_fingerprint_detects_column_changes(self) -> None:
        """Verify source fingerprint changes when columns change."""
        from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
            compute_source_fingerprint,
        )

        fp_original = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "integer", "amount": "decimal"},
        )

        # Add a column
        fp_added = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "integer", "amount": "decimal", "status": "string"},
        )
        assert fp_original.hash != fp_added.hash

        # Change a type
        fp_changed_type = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "bigint", "amount": "decimal"},  # id changed from integer
        )
        assert fp_original.hash != fp_changed_type.hash

    def test_source_fingerprint_detects_schema_changes(self) -> None:
        """Verify source fingerprint changes when schema location changes."""
        from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
            compute_source_fingerprint,
        )

        fp_original = compute_source_fingerprint(
            database="analytics",
            schema="raw",
            identifier="orders",
            columns={"id": "integer"},
        )

        # Different schema
        fp_different_schema = compute_source_fingerprint(
            database="analytics",
            schema="staging",  # Changed
            identifier="orders",
            columns={"id": "integer"},
        )
        assert fp_original.hash != fp_different_schema.hash


@pytest.mark.integration
class TestMacroIngest:
    """Tests for dbt macro ingest and macro dependency edges."""

    def test_model_uses_macro_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Ingest macro nodes and create `USES_MACRO` edges from models."""
        macro = create_mock_macro("macro.test.generate_columns")
        model = create_mock_model(
            "model.test.model1",
            checksum="abc123",
            compiled_sql="select 1",
            depends_on_macros=[macro.unique_id],
        )
        artifacts = create_mock_artifacts([model], macros=[macro])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Macro node exists
        res = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtMacro {id: 'macro.test.generate_columns'}) RETURN m.id AS id"
        )
        assert res.count == 1

        # Edge exists: model -> macro
        res = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel {id: 'model.test.model1'})-[:USES_MACRO]->(:DbtMacro {id: 'macro.test.generate_columns'}) RETURN 1 AS ok"
        )
        assert res.count == 1


@pytest.mark.integration
class TestTestIngest:
    """Integration tests for dbt test loading."""

    def test_tests_loaded_on_write_typed(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """write_typed() creates DbtTest nodes."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            compiled_sql="select id, customer_id from raw_orders",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
                "customer_id": DbtColumn(name="customer_id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                compiled_sql="""
SELECT id
FROM test_schema.orders
GROUP BY id
HAVING count(*) > 1
""",
            ),
            create_mock_test(
                "test.project.not_null_orders_id",
                test_type="generic",
                test_name="not_null",
                column_name="id",
                model_id="model.test.orders",
                compiled_sql="""
SELECT *
FROM test_schema.orders
WHERE id IS NULL
""",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify test nodes created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 2

    def test_has_test_edges_created(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """HAS_TEST edges link models to tests."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                compiled_sql="""
SELECT id
FROM test_schema.orders
GROUP BY id
HAVING count(*) > 1
""",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify HAS_TEST edge created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.orders'})-[:HAS_TEST]->(t:DbtTest) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_tests_column_edges_created(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """TESTS_COLUMN edges link tests to columns."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify TESTS_COLUMN edge created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TESTS_COLUMN]->(c:DbtColumn) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_test_references_edges_created(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """TEST_REFERENCES edges for relationship tests."""

        orders = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
                "customer_id": DbtColumn(name="customer_id", description="", data_type="int"),
            },
        )
        customers = create_mock_model(
            "model.test.customers",
            checksum="def456",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.relationships_orders_customer",
                test_type="generic",
                test_name="relationships",
                column_name="customer_id",
                model_id="model.test.orders",
                referenced_model_id="model.test.customers",
                test_kwargs={"to": "ref('customers')", "field": "id"},
                compiled_sql="""
SELECT o.customer_id
FROM test_schema.orders o
LEFT JOIN test_schema.customers c ON o.customer_id = c.id
WHERE c.id IS NULL
""",
            ),
        ]
        artifacts = create_mock_artifacts([orders, customers], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify TEST_REFERENCES edge created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TEST_REFERENCES]->(m:DbtModel {id: 'model.test.customers'}) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_test_fingerprints_stored(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """test_fingerprint property set on DbtTest nodes."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify fingerprint stored
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) WHERE t.test_fingerprint IS NOT NULL RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_unit_tests_loaded_on_write_typed(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """write_typed() creates DbtUnitTest nodes."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
        )
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts([model], unit_tests=unit_tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify unit test nodes created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtUnitTest) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_has_unit_test_edges_created(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """HAS_UNIT_TEST edges link models to unit tests."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
        )
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts([model], unit_tests=unit_tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify HAS_UNIT_TEST edge created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.orders'})-[:HAS_UNIT_TEST]->(t:DbtUnitTest) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1


@pytest.mark.integration
class TestTestIncrementalLoading:
    """Integration tests for incremental test loading."""

    def test_incremental_test_detection_no_changes(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Second load with same tests -> 0 changes detected."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load
        builder.write_typed(falkordblite_storage)

        # Second detection
        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts, falkordblite_storage)

        assert change_set.has_changes is False
        assert len(change_set.unchanged) == 1

    def test_incremental_test_added(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """New test in manifest -> detected as added."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts_v1 = create_mock_artifacts([model], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load
        builder.write_typed(falkordblite_storage)

        # Add new test
        tests_v2 = [
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
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts_v2, falkordblite_storage)

        assert len(change_set.added) == 1
        assert "test.project.not_null_orders_id" in change_set.added
        assert len(change_set.unchanged) == 1

    def test_incremental_test_modified(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Changed test config (e.g., severity) -> detected as modified."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="error",
            ),
        ]
        artifacts_v1 = create_mock_artifacts([model], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load
        builder.write_typed(falkordblite_storage)

        # Modify test severity
        tests_v2 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="warn",  # Changed
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts_v2, falkordblite_storage)

        assert len(change_set.modified) == 1
        assert "test.project.unique_orders_id" in change_set.modified

    def test_incremental_test_removed(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Test removed from manifest -> detected as removed."""

        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests_v1 = [
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
        artifacts_v1 = create_mock_artifacts([model], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load
        builder.write_typed(falkordblite_storage)

        # Remove one test
        tests_v2 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)

        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts_v2, falkordblite_storage)

        assert len(change_set.removed) == 1
        assert "test.project.not_null_orders_id" in change_set.removed
        assert len(change_set.unchanged) == 1

    def test_write_incremental_tests_adds_new(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """write_incremental_tests() creates new test nodes."""


        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load models only (no tests)
        change_set = ModelChangeSet(
            added=["model.test.orders"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        builder.write_incremental(falkordblite_storage, change_set)

        # Now add tests incrementally
        test_changes = TestChangeSet(
            added=["test.project.unique_orders_id"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=[],
        )

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify test was created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_write_incremental_tests_removes_deleted(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """write_incremental_tests() deletes removed test nodes."""


        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
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
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # First load all tests
        builder.write_typed(falkordblite_storage)

        # Verify both tests exist
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 2

        # Now remove one test
        tests_v2 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=[],
            removed=["test.project.not_null_orders_id"],
            unchanged=["test.project.unique_orders_id"],
        )
        unit_test_changes = UnitTestChangeSet(
            added=[],
            modified=[],
            removed=[],
            unchanged=[],
        )

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify only one test remains
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1


@pytest.mark.integration
class TestSourceTestIngest:
    """Integration tests for tests on DbtSource nodes."""

    def test_source_test_creates_has_test_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """HAS_TEST edge created from DbtSource -> DbtTest."""
        source = create_mock_source(
            "source.test.raw.orders",
            columns={
                "id": DbtColumn(name="id", description="Order ID", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.source_unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="source.test.raw.orders",
                compiled_sql="""
SELECT id
FROM raw.orders
GROUP BY id
HAVING count(*) > 1
""",
            ),
        ]
        artifacts = create_mock_artifacts([], tests=tests, sources=[source])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify HAS_TEST edge from source to test
        result = falkordblite_storage.execute_raw_query(
            "MATCH (s:DbtSource {id: 'source.test.raw.orders'})-[:HAS_TEST]->(t:DbtTest) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_source_test_with_column_creates_tests_column_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Column-scoped test on source creates TESTS_COLUMN edge."""
        source = create_mock_source(
            "source.test.raw.customers",
            columns={
                "email": DbtColumn(name="email", description="Customer email", data_type="varchar"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.source_not_null_email",
                test_type="generic",
                test_name="not_null",
                column_name="email",
                model_id="source.test.raw.customers",
                compiled_sql="""
SELECT *
FROM raw.customers
WHERE email IS NULL
""",
            ),
        ]
        artifacts = create_mock_artifacts([], tests=tests, sources=[source])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify TESTS_COLUMN edge from test to source column
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TESTS_COLUMN]->(c:DbtColumn) "
            "WHERE c.parent_id = 'source.test.raw.customers' RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_relationship_test_references_source(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Relationship test with source as target creates TEST_REFERENCES edge."""
        source = create_mock_source(
            "source.test.raw.customers",
            columns={
                "id": DbtColumn(name="id", description="Customer ID", data_type="int"),
            },
        )
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "customer_id": DbtColumn(name="customer_id", description="FK to customers", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.relationships_orders_to_source_customers",
                test_type="generic",
                test_name="relationships",
                column_name="customer_id",
                model_id="model.test.orders",
                referenced_model_id="source.test.raw.customers",
                test_kwargs={"to": "source('raw', 'customers')", "field": "id"},
                compiled_sql="""
SELECT o.customer_id
FROM orders o
LEFT JOIN raw.customers c ON o.customer_id = c.id
WHERE c.id IS NULL
""",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests, sources=[source])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify TEST_REFERENCES edge from test to source
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TEST_REFERENCES]->(s:DbtSource {id: 'source.test.raw.customers'}) "
            "RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_source_test_fingerprint_stored(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Source tests have fingerprints computed and stored."""
        source = create_mock_source(
            "source.test.raw.orders",
            columns={
                "id": DbtColumn(name="id", description="Order ID", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.source_unique_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="source.test.raw.orders",
            ),
        ]
        artifacts = create_mock_artifacts([], tests=tests, sources=[source])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify fingerprint stored
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) WHERE t.test_fingerprint IS NOT NULL RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

    def test_source_test_incremental_detection(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Source tests detected as added/modified/removed correctly."""
        source = create_mock_source(
            "source.test.raw.orders",
            columns={
                "id": DbtColumn(name="id", description="Order ID", data_type="int"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.source_unique_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="source.test.raw.orders",
                severity="error",
            ),
        ]
        artifacts_v1 = create_mock_artifacts([], tests=tests_v1, sources=[source])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Modify test severity
        tests_v2 = [
            create_mock_test(
                "test.project.source_unique_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="source.test.raw.orders",
                severity="warn",  # Changed
            ),
        ]
        artifacts_v2 = create_mock_artifacts([], tests=tests_v2, sources=[source])

        # Detect changes
        detector = ChangeDetector()
        change_set = detector.detect_test_changes(artifacts_v2, falkordblite_storage)

        assert len(change_set.modified) == 1
        assert "test.project.source_unique_id" in change_set.modified


@pytest.mark.integration
class TestModifiedTestHandling:
    """Integration tests for modified test updates."""

    def test_write_incremental_tests_updates_modified_fingerprint(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Modified test -> old node deleted, new node with new fingerprint."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="error",
            ),
        ]
        artifacts_v1 = create_mock_artifacts([model], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Get original fingerprint
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) "
            "RETURN t.test_fingerprint AS fp, t.severity AS severity"
        )
        original_fp = result.rows[0]["fp"]
        assert result.rows[0]["severity"] == "error"

        # Modify test
        tests_v2 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
                severity="warn",  # Changed
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=["test.project.unique_orders_id"],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify fingerprint changed and severity updated
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) "
            "RETURN t.test_fingerprint AS fp, t.severity AS severity"
        )
        assert result.rows[0]["fp"] != original_fp
        assert result.rows[0]["severity"] == "warn"

    def test_write_incremental_tests_recreates_edges_on_modify(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Modified test -> all edges (HAS_TEST, TESTS_COLUMN) recreated."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Count edges before
        has_test_count = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        ).rows[0]["count"]
        tests_column_count = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        ).rows[0]["count"]

        # Modify test (same test, treat as modified)
        test_changes = TestChangeSet(
            added=[],
            modified=["test.project.unique_orders_id"],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Count edges after - should be same
        has_test_after = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        ).rows[0]["count"]
        tests_column_after = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        ).rows[0]["count"]

        assert has_test_after == has_test_count
        assert tests_column_after == tests_column_count

    def test_modified_unit_test_updates_fingerprint(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Modified unit test -> fingerprint updated."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
        )
        unit_tests_v1 = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1, "total": 100}]},  # Original expect
            ),
        ]
        artifacts_v1 = create_mock_artifacts([model], unit_tests=unit_tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Get original fingerprint
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtUnitTest {id: 'unit_test.project.test_orders_logic'}) "
            "RETURN t.test_fingerprint AS fp"
        )
        original_fp = result.rows[0]["fp"]

        # Modify unit test expect
        unit_tests_v2 = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1, "total": 200}]},  # Changed expect
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], unit_tests=unit_tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(added=[], modified=[], removed=[], unchanged=[])
        unit_test_changes = UnitTestChangeSet(
            added=[],
            modified=["unit_test.project.test_orders_logic"],
            removed=[],
            unchanged=[],
        )

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify fingerprint changed
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtUnitTest {id: 'unit_test.project.test_orders_logic'}) "
            "RETURN t.test_fingerprint AS fp"
        )
        assert result.rows[0]["fp"] != original_fp

    def test_modified_relationship_test_updates_referenced_model(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Relationship test to= changed -> TEST_REFERENCES edge updated."""
        orders = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "customer_id": DbtColumn(name="customer_id", description="", data_type="int"),
            },
        )
        customers = create_mock_model(
            "model.test.customers",
            checksum="def456",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        accounts = create_mock_model(
            "model.test.accounts",
            checksum="ghi789",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.relationships_orders_fk",
                test_type="generic",
                test_name="relationships",
                column_name="customer_id",
                model_id="model.test.orders",
                referenced_model_id="model.test.customers",  # Original reference
                test_kwargs={"to": "ref('customers')", "field": "id"},
            ),
        ]
        artifacts_v1 = create_mock_artifacts([orders, customers, accounts], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify original reference
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TEST_REFERENCES]->(m:DbtModel) RETURN m.id AS ref_id"
        )
        assert result.rows[0]["ref_id"] == "model.test.customers"

        # Change reference to accounts
        tests_v2 = [
            create_mock_test(
                "test.project.relationships_orders_fk",
                test_type="generic",
                test_name="relationships",
                column_name="customer_id",
                model_id="model.test.orders",
                referenced_model_id="model.test.accounts",  # Changed reference
                test_kwargs={"to": "ref('accounts')", "field": "id"},
            ),
        ]
        artifacts_v2 = create_mock_artifacts([orders, customers, accounts], tests=tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=["test.project.relationships_orders_fk"],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify reference updated
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest)-[:TEST_REFERENCES]->(m:DbtModel) RETURN m.id AS ref_id"
        )
        assert result.rows[0]["ref_id"] == "model.test.accounts"


@pytest.mark.integration
class TestEdgeCleanup:
    """Integration tests for edge cleanup during test operations."""

    def test_removed_test_cleans_up_has_test_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Removed test -> HAS_TEST edge deleted."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify edge exists
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 1

        # Remove test
        artifacts_v2 = create_mock_artifacts([model], tests=[])
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=[],
            removed=["test.project.unique_orders_id"],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify edge deleted
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_removed_test_cleans_up_tests_column_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Removed test -> TESTS_COLUMN edge deleted."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify edge exists
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 1

        # Remove test
        artifacts_v2 = create_mock_artifacts([model], tests=[])
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=[],
            removed=["test.project.unique_orders_id"],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify edge deleted
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_removed_test_cleans_up_test_references_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Removed relationship test -> TEST_REFERENCES edge deleted."""
        orders = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "customer_id": DbtColumn(name="customer_id", description="", data_type="int"),
            },
        )
        customers = create_mock_model(
            "model.test.customers",
            checksum="def456",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.relationships_orders_customer",
                test_type="generic",
                test_name="relationships",
                column_name="customer_id",
                model_id="model.test.orders",
                referenced_model_id="model.test.customers",
                test_kwargs={"to": "ref('customers')", "field": "id"},
            ),
        ]
        artifacts = create_mock_artifacts([orders, customers], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify edge exists
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TEST_REFERENCES]->(:DbtModel) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 1

        # Remove test
        artifacts_v2 = create_mock_artifacts([orders, customers], tests=[])
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=[],
            modified=[],
            removed=["test.project.relationships_orders_customer"],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify edge deleted
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TEST_REFERENCES]->(:DbtModel) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_removed_unit_test_cleans_up_has_unit_test_edge(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Removed unit test -> HAS_UNIT_TEST edge deleted."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
        )
        unit_tests = [
            create_mock_unit_test(
                "unit_test.project.test_orders_logic",
                model_id="model.test.orders",
                given=[{"input": "ref('raw')", "rows": [{"id": 1}]}],
                expect={"rows": [{"id": 1}]},
            ),
        ]
        artifacts = create_mock_artifacts([model], unit_tests=unit_tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify edge exists
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_UNIT_TEST]->(:DbtUnitTest) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 1

        # Remove unit test
        artifacts_v2 = create_mock_artifacts([model], unit_tests=[])
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(added=[], modified=[], removed=[], unchanged=[])
        unit_test_changes = UnitTestChangeSet(
            added=[],
            modified=[],
            removed=["unit_test.project.test_orders_logic"],
            unchanged=[],
        )

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify edge deleted
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_UNIT_TEST]->(:DbtUnitTest) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_no_orphan_edges_after_mixed_operations(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """After add/modify/remove mix, no orphan edges remain."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
                "amount": DbtColumn(name="amount", description="", data_type="decimal"),
            },
        )
        tests_v1 = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
            create_mock_test(
                "test.project.not_null_amount",
                test_type="generic",
                test_name="not_null",
                column_name="amount",
                model_id="model.test.orders",
            ),
        ]
        artifacts_v1 = create_mock_artifacts([model], tests=tests_v1)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Mixed operations: remove unique, modify not_null, add new test
        tests_v2 = [
            create_mock_test(
                "test.project.not_null_amount",
                test_type="generic",
                test_name="not_null",
                column_name="amount",
                model_id="model.test.orders",
                severity="warn",  # Modified
            ),
            create_mock_test(
                "test.project.positive_amount",
                test_type="singular",
                model_id="model.test.orders",
                compiled_sql="SELECT * FROM orders WHERE amount < 0",
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=["test.project.positive_amount"],
            modified=["test.project.not_null_amount"],
            removed=["test.project.unique_orders_id"],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Verify: 2 tests (removed unique, added positive_amount)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 2

        # Verify: no orphan HAS_TEST edges (all edges point to existing tests)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel)-[:HAS_TEST]->(t:DbtTest) "
            "WHERE t.id IN ['test.project.not_null_amount', 'test.project.positive_amount'] "
            "RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 2

        # Verify: no edge to removed test
        result = falkordblite_storage.execute_raw_query(
            "MATCH ()-[e]->(:DbtTest {id: 'test.project.unique_orders_id'}) RETURN count(e) AS count"
        )
        assert result.rows[0]["count"] == 0


@pytest.mark.integration
class TestIncrementalTestFailures:
    """Integration tests for failure scenarios."""

    def test_write_incremental_tests_missing_parent_model(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Test references deleted model -> test created but no HAS_TEST edge."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_orders_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Delete the model
        falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.orders'}) DETACH DELETE m"
        )

        # Now try to add a new test referencing the deleted model
        tests_v2 = [
            create_mock_test(
                "test.project.not_null_id",
                test_type="generic",
                test_name="not_null",
                column_name="id",
                model_id="model.test.orders",  # Model no longer exists
            ),
        ]
        artifacts_v2 = create_mock_artifacts([], tests=tests_v2)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=["test.project.not_null_id"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        # Should not crash
        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Test node created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.not_null_id'}) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

        # But no HAS_TEST edge (parent doesn't exist)
        result = falkordblite_storage.execute_raw_query(
            "MATCH ()-[:HAS_TEST]->(t:DbtTest {id: 'test.project.not_null_id'}) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_write_incremental_tests_missing_parent_column(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Test references deleted column -> no TESTS_COLUMN edge."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        artifacts = create_mock_artifacts([model])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Delete the column
        falkordblite_storage.execute_raw_query(
            "MATCH (c:DbtColumn) WHERE c.parent_id = 'model.test.orders' DETACH DELETE c"
        )

        # Add test referencing the deleted column
        tests = [
            create_mock_test(
                "test.project.unique_id",
                test_type="generic",
                test_name="unique",
                column_name="id",  # Column no longer exists
                model_id="model.test.orders",
            ),
        ]
        artifacts_v2 = create_mock_artifacts([model], tests=tests)
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=["test.project.unique_id"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        # Should not crash
        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Test node created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_id'}) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1

        # HAS_TEST edge exists (model exists)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[:HAS_TEST]->(t:DbtTest {id: 'test.project.unique_id'}) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 1

        # But no TESTS_COLUMN edge (column doesn't exist)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_id'})-[:TESTS_COLUMN]->(:DbtColumn) RETURN count(*) AS count"
        )
        assert result.rows[0]["count"] == 0

    def test_concurrent_add_and_remove_same_test_id(self, falkordblite_storage: LineageStorage, tmp_path: Path) -> None:
        """Edge case: test_id in both added and removed lists."""
        model = create_mock_model(
            "model.test.orders",
            checksum="abc123",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_id",
                test_type="generic",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Edge case: same test in both added and removed
        # This shouldn't happen normally but tests robustness
        test_changes = TestChangeSet(
            added=["test.project.unique_id"],  # Also in removed
            modified=[],
            removed=["test.project.unique_id"],  # Also in added
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        # Should not crash - behavior may vary (add wins, remove wins, or error)
        # The key is that it handles the edge case gracefully
        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Test should exist after operation (add typically processed after remove)
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_id'}) RETURN count(t) AS count"
        )
        # Either 0 or 1 is acceptable, just not a crash
        assert result.rows[0]["count"] in [0, 1]


@pytest.mark.integration
class TestIncrementalModelLoadingDoesNotAffectTests:
    """Prove that incremental MODEL loading does not corrupt test data.

    This addresses a code review concern that `write_incremental()` might
    reprocess all tests during model-only changes. These tests prove that
    test nodes and edges remain intact when only models are modified.
    """

    def test_incremental_model_change_preserves_test_nodes(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Modifying a model via write_incremental() does not affect test nodes."""
        # Setup: model with a test
        model_v1 = create_mock_model(
            "model.test.orders",
            checksum="v1_checksum",
            compiled_sql="SELECT id FROM raw_orders",
            columns={
                "id": DbtColumn(name="id", description="Order ID", data_type="int"),
            },
        )
        test = create_mock_test(
            "test.project.unique_orders_id",
            test_type="generic",
            test_name="unique",
            column_name="id",
            model_id="model.test.orders",
            compiled_sql="SELECT id FROM orders GROUP BY id HAVING count(*) > 1",
        )
        artifacts_v1 = create_mock_artifacts([model_v1], tests=[test])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        # Full load
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Capture test state BEFORE incremental model update
        result_before = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) "
            "RETURN t.test_fingerprint AS fingerprint, t.compiled_sql AS sql"
        )
        assert len(result_before.rows) == 1
        fingerprint_before = result_before.rows[0]["fingerprint"]
        sql_before = result_before.rows[0]["sql"]

        # Count HAS_TEST edges before
        edge_count_before = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        ).rows[0]["count"]
        assert edge_count_before == 1

        # Modify the MODEL only (different checksum/SQL)
        model_v2 = create_mock_model(
            "model.test.orders",
            checksum="v2_checksum_changed",
            compiled_sql="SELECT id, status FROM raw_orders WHERE active = true",
            columns={
                "id": DbtColumn(name="id", description="Order ID", data_type="int"),
                "status": DbtColumn(name="status", description="Status", data_type="varchar"),
            },
        )
        # Test remains UNCHANGED
        artifacts_v2 = create_mock_artifacts([model_v2], tests=[test])
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v2.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v2.catalog))

        # Reload builder and do INCREMENTAL model update
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        change_set = ModelChangeSet(
            added=[],
            modified=["model.test.orders"],  # Only model changed
            removed=[],
            unchanged=[],
        )
        builder.write_incremental(falkordblite_storage, change_set)

        # Verify test state AFTER incremental model update
        result_after = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.unique_orders_id'}) "
            "RETURN t.test_fingerprint AS fingerprint, t.compiled_sql AS sql"
        )
        assert len(result_after.rows) == 1
        fingerprint_after = result_after.rows[0]["fingerprint"]
        sql_after = result_after.rows[0]["sql"]

        # Test fingerprint and SQL should be UNCHANGED
        assert fingerprint_after == fingerprint_before, "Test fingerprint was corrupted by model update"
        assert sql_after == sql_before, "Test SQL was corrupted by model update"

        # HAS_TEST edge should still exist
        edge_count_after = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtModel)-[e:HAS_TEST]->(:DbtTest) RETURN count(e) AS count"
        ).rows[0]["count"]
        assert edge_count_after == edge_count_before, "HAS_TEST edge was deleted by model update"

    def test_incremental_model_change_preserves_tests_column_edges(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Modifying a model via write_incremental() preserves TESTS_COLUMN edges."""
        model = create_mock_model(
            "model.test.orders",
            checksum="v1",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
                "amount": DbtColumn(name="amount", description="", data_type="decimal"),
            },
        )
        tests = [
            create_mock_test(
                "test.project.unique_id",
                test_name="unique",
                column_name="id",
                model_id="model.test.orders",
            ),
            create_mock_test(
                "test.project.not_null_amount",
                test_name="not_null",
                column_name="amount",
                model_id="model.test.orders",
            ),
        ]
        artifacts = create_mock_artifacts([model], tests=tests)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Count TESTS_COLUMN edges before
        tests_col_before = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        ).rows[0]["count"]
        assert tests_col_before == 2, "Expected 2 TESTS_COLUMN edges"

        # Modify model (change SQL but keep same columns)
        model_v2 = create_mock_model(
            "model.test.orders",
            checksum="v2_changed",
            compiled_sql="SELECT id, amount FROM raw_orders WHERE status = 'active'",
            columns={
                "id": DbtColumn(name="id", description="", data_type="int"),
                "amount": DbtColumn(name="amount", description="", data_type="decimal"),
            },
        )
        artifacts_v2 = create_mock_artifacts([model_v2], tests=tests)
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v2.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v2.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        change_set = ModelChangeSet(
            added=[],
            modified=["model.test.orders"],
            removed=[],
            unchanged=[],
        )
        builder.write_incremental(falkordblite_storage, change_set)

        # TESTS_COLUMN edges should still exist
        tests_col_after = falkordblite_storage.execute_raw_query(
            "MATCH (:DbtTest)-[e:TESTS_COLUMN]->(:DbtColumn) RETURN count(e) AS count"
        ).rows[0]["count"]
        assert tests_col_after == tests_col_before, "TESTS_COLUMN edges were deleted by model update"

    def test_incremental_model_add_does_not_duplicate_tests(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Adding a new model via write_incremental() does not duplicate existing tests."""
        model1 = create_mock_model("model.test.orders", checksum="abc")
        test1 = create_mock_test(
            "test.project.unique_orders",
            model_id="model.test.orders",
        )
        artifacts_v1 = create_mock_artifacts([model1], tests=[test1])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Count tests before
        test_count_before = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        ).rows[0]["count"]
        assert test_count_before == 1

        # Add a NEW model (test stays the same)
        model2 = create_mock_model("model.test.customers", checksum="def")
        artifacts_v2 = create_mock_artifacts([model1, model2], tests=[test1])
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v2.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v2.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        change_set = ModelChangeSet(
            added=["model.test.customers"],  # Only new model
            modified=[],
            removed=[],
            unchanged=["model.test.orders"],
        )
        builder.write_incremental(falkordblite_storage, change_set)

        # Test count should be UNCHANGED (no duplicates created)
        test_count_after = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest) RETURN count(t) AS count"
        ).rows[0]["count"]
        assert test_count_after == test_count_before, (
            f"Test count changed from {test_count_before} to {test_count_after} - "
            "incremental model loading should not affect test count"
        )


@pytest.mark.integration
class TestMalformedTestKwargsInBuilder:
    """Tests for builder handling of malformed test_kwargs.

    These tests specifically address the reviewer's concern that calling
    test_kwargs.get("field") would crash if test_kwargs is not a dict.
    """

    def test_relationship_test_with_non_dict_kwargs_full_load(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Relationship test with kwargs as string -> should not crash builder.

        This tests the reviewer's specific concern: test_kwargs.get("field")
        would raise AttributeError if kwargs is not a dict.
        """
        model = create_mock_model(
            "model.test.orders",
            checksum="abc",
            columns={"customer_id": DbtColumn(name="customer_id", description="", data_type="int")},
        )
        customer_model = create_mock_model(
            "model.test.customers",
            checksum="def",
            columns={"id": DbtColumn(name="id", description="", data_type="int")},
        )

        # Create a relationship test with MALFORMED kwargs (string instead of dict)
        test = create_mock_test(
            "test.project.relationships_orders_customers",
            test_type="generic",
            test_name="relationships",
            column_name="customer_id",
            model_id="model.test.orders",
            referenced_model_id="model.test.customers",
            test_kwargs="malformed_string",  # Should be dict like {"to": "ref('customers')", "field": "id"}
        )

        artifacts = create_mock_artifacts([model, customer_model], tests=[test])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)

        # This should NOT crash - it should handle malformed kwargs gracefully
        builder.write_typed(falkordblite_storage)

        # Test node should exist
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.relationships_orders_customers'}) "
            "RETURN t.test_name AS name"
        )
        assert len(result.rows) == 1
        assert result.rows[0]["name"] == "relationships"

    def test_relationship_test_with_list_kwargs_incremental(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Relationship test with kwargs as list -> should not crash incremental writer."""
        model = create_mock_model("model.test.orders", checksum="abc")
        customer_model = create_mock_model("model.test.customers", checksum="def")

        # First do a full load without the malformed test
        artifacts_v1 = create_mock_artifacts([model, customer_model])

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))

        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Now add a malformed test via incremental
        test = create_mock_test(
            "test.project.bad_relationship",
            test_type="generic",
            test_name="relationships",
            model_id="model.test.orders",
            referenced_model_id="model.test.customers",
            test_kwargs=["field", "id"],  # Malformed: list instead of dict
        )
        artifacts_v2 = create_mock_artifacts([model, customer_model], tests=[test])
        builder._artifacts = artifacts_v2

        test_changes = TestChangeSet(
            added=["test.project.bad_relationship"],
            modified=[],
            removed=[],
            unchanged=[],
        )
        unit_test_changes = UnitTestChangeSet(added=[], modified=[], removed=[], unchanged=[])

        # This should NOT crash
        builder.write_incremental_tests(falkordblite_storage, test_changes, unit_test_changes)

        # Test should be created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (t:DbtTest {id: 'test.project.bad_relationship'}) RETURN count(t) AS count"
        )
        assert result.rows[0]["count"] == 1
