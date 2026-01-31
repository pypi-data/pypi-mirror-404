"""Tests for physical node registration with None value handling.

Tests verify that register_physical_node correctly handles:
- None database values
- None schema values
- None materialization values
- Proper FQN construction when components are missing
"""

import json
from pathlib import Path

import pytest
from lineage.backends.lineage.protocol import LineageStorage
from lineage.ingest.static_loaders.dbt.builder import LineageBuilder

from tests.test_helpers import create_mock_artifacts, create_mock_model


@pytest.mark.integration
class TestPhysicalNodeRegistration:
    """Tests for register_physical_node with None value handling."""

    def test_register_physical_node_with_none_database_and_schema(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should handle None database and schema by defaulting to empty strings."""
        # Create model with None database and schema
        model = create_mock_model(
            "model.test.my_model",
            checksum="abc123",
            database=None,  # Explicitly None
            schema=None,  # Explicitly None
            relation_name="my_table",
            materialization="table",
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify PhysicalTable node was created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalTable) RETURN p.database AS database, "
            "p.schema_name AS schema_name, p.fqn AS fqn, p.relation_name AS relation_name"
        )
        assert result.count == 1
        row = result.rows[0]

        # database and schema should be empty strings (not None)
        assert row["database"] == ""
        assert row["schema_name"] == ""
        # FQN should just be the relation_name when db/schema are missing
        assert row["fqn"] == "my_table"
        assert row["relation_name"] == "my_table"

    def test_register_physical_node_with_partial_fqn(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should use FQN from relation_name when only schema is present (no database)."""
        # Create model with None database but valid schema
        # relation_name is the FQN as it appears in dbt manifests
        model = create_mock_model(
            "model.test.my_model",
            checksum="abc123",
            database=None,  # Explicitly None
            schema="my_schema",
            relation_name="my_schema.my_table",  # FQN as dbt provides it
            materialization="view",
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify PhysicalView node was created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalView) RETURN p.database AS database, "
            "p.schema_name AS schema_name, p.fqn AS fqn"
        )
        assert result.count == 1
        row = result.rows[0]

        assert row["database"] == ""
        assert row["schema_name"] == "my_schema"
        # FQN should be schema.table when database is missing
        assert row["fqn"] == "my_schema.my_table"

    def test_register_physical_node_with_none_materialization_skips(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should skip physical node creation when materialization is None."""
        # Create model with None materialization
        model = create_mock_model(
            "model.test.my_model",
            checksum="abc123",
            database="my_db",
            schema="my_schema",
            relation_name="my_table",
            materialization=None,  # Explicitly None
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify NO PhysicalTable nodes were created (should have been skipped)
        result = falkordblite_storage.execute_raw_query("MATCH (p:PhysicalTable) RETURN COUNT(p) AS count")
        assert result.count == 1
        assert result.rows[0]["count"] == 0

        # Verify DbtModel was still created
        result = falkordblite_storage.execute_raw_query("MATCH (m:DbtModel) RETURN m.id AS id")
        assert result.count == 1
        assert result.rows[0]["id"] == "model.test.my_model"

    def test_register_physical_node_with_none_relation_name_skips(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should skip physical node creation when relation_name is None."""
        # Create model with None relation_name
        model = create_mock_model(
            "model.test.my_model",
            checksum="abc123",
            database="my_db",
            schema="my_schema",
            relation_name=None,  # Explicitly None
            materialization="table",
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify NO PhysicalTable nodes were created
        result = falkordblite_storage.execute_raw_query("MATCH (p:PhysicalTable) RETURN COUNT(p) AS count")
        assert result.count == 1
        assert result.rows[0]["count"] == 0

    def test_register_physical_node_with_full_fqn(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should use FQN from relation_name when all components are present."""
        # Create model with all components
        # relation_name is the FQN as it appears in dbt manifests
        model = create_mock_model(
            "model.test.my_model",
            checksum="abc123",
            database="my_db",
            schema="my_schema",
            relation_name="my_db.my_schema.my_table",  # FQN as dbt provides it
            materialization="table",  # Changed from "incremental" to "table"
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify PhysicalTable node was created with full FQN
        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalTable) RETURN p.database AS database, "
            "p.schema_name AS schema_name, p.fqn AS fqn"
        )
        assert result.count == 1
        row = result.rows[0]

        assert row["database"] == "my_db"
        assert row["schema_name"] == "my_schema"
        assert row["fqn"] == "my_db.my_schema.my_table"

    def test_register_physical_node_with_different_materialization_types(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should create correct physical node types for different materializations."""
        models = [
            create_mock_model(
                "model.test.table_model",
                checksum="abc1",
                database="db",
                schema="sch",
                relation_name="tbl",
                materialization="table",
            ),
            create_mock_model(
                "model.test.view_model",
                checksum="abc2",
                database="db",
                schema="sch",
                relation_name="vw",
                materialization="view",
            ),
            create_mock_model(
                "model.test.matview_model",
                checksum="abc3",
                database="db",
                schema="sch",
                relation_name="mvw",
                materialization="materialized_view",
            ),
            create_mock_model(
                "model.test.ephemeral_model",
                checksum="abc4",
                database="db",
                schema="sch",
                relation_name="eph",
                materialization="ephemeral",
            ),
        ]
        artifacts = create_mock_artifacts(models)

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and write
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Verify correct node types were created
        result = falkordblite_storage.execute_raw_query("MATCH (p:PhysicalTable) RETURN COUNT(p) AS count")
        assert result.rows[0]["count"] == 1

        result = falkordblite_storage.execute_raw_query("MATCH (p:PhysicalView) RETURN COUNT(p) AS count")
        assert result.rows[0]["count"] == 1

        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalMaterializedView) RETURN COUNT(p) AS count"
        )
        assert result.rows[0]["count"] == 1

        # Ephemeral models should NOT create physical nodes
        result = falkordblite_storage.execute_raw_query("MATCH (p:PhysicalEphemeral) RETURN COUNT(p) AS count")
        assert result.rows[0]["count"] == 0

    def test_register_physical_node_direct_ephemeral_skips(
        self, falkordblite_storage: LineageStorage, tmp_path: Path
    ) -> None:
        """Should skip physical node creation for ephemeral models even when called directly."""
        # Create model with ephemeral materialization
        model = create_mock_model(
            "model.test.eph_model",
            checksum="abc123",
            database="db",
            schema="sch",
            relation_name="eph_table",
            materialization="ephemeral",
        )
        artifacts = create_mock_artifacts([model])

        # Create artifacts directory
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Build and call register_physical_node directly
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        # Should not raise exception and should not create physical node
        builder.register_physical_node(falkordblite_storage, "model.test.eph_model")

        # Verify NO PhysicalEphemeral nodes were created
        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalEphemeral) RETURN COUNT(p) AS count"
        )
        assert result.rows[0]["count"] == 0
        # Also no PhysicalTable fallback
        result = falkordblite_storage.execute_raw_query(
            "MATCH (p:PhysicalTable) RETURN COUNT(p) AS count"
        )
        assert result.rows[0]["count"] == 0
