"""Integration tests for incremental lineage loading.

Tests cover:
- Full change detection workflow
- Semantic analysis filtering
- Edge cases and error handling
"""
# ruff: noqa: I001
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

try:
    from lineage.backends.lineage.falkordblite_adapter import FalkorDBLiteAdapter
except ImportError:
    FalkorDBLiteAdapter = None  # type: ignore

from lineage.backends.lineage.models.dbt import DbtModel
from lineage.backends.lineage.models.semantic_analysis import InferredSemanticModel
from lineage.backends.lineage.models.edges import HasInferredSemantics
from lineage.backends.lineage.protocol import RawLineageQueryResult
from lineage.backends.lineage.models.base import NodeIdentifier
from lineage.backends.types import NodeLabel
from lineage.ingest.config import (
    ClusteringConfig,
    ProfilingConfig,
    SemanticAnalysisConfig,
    SemanticViewLoaderConfig,
)
from lineage.ingest.static_loaders.change_detection import ChangeDetector
from lineage.ingest.static_loaders.dbt.builder import LineageBuilder
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    compute_model_fingerprint_result,
)
from lineage.integration import LineageIntegration

from tests.ingest.static_loaders.change_detection.test_change_detection import (
    setup_mock_storage_for_changes,
)
from tests.test_helpers import create_mock_artifacts, create_mock_model


@pytest.mark.integration
@pytest.mark.skipif(FalkorDBLiteAdapter is None, reason="FalkorDBLite not available")
class TestChangeDetectionIntegration:
    """Tests for full change detection workflow."""

    def test_full_load_then_incremental(self, falkordblite_storage: FalkorDBLiteAdapter, tmp_path: Path) -> None:
        """Full load, then incremental with 1 model changed."""
        # Full load: 2 models
        models_v1 = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
            create_mock_model("model.test.model2", compiled_sql="select 2"),
        ]
        artifacts_v1 = create_mock_artifacts(models_v1)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts_v1.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts_v1.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)
        
        # Incremental load: model2 changed
        models_v2 = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),  # unchanged
            create_mock_model("model.test.model2", compiled_sql="select 3"),  # modified
        ]
        artifacts_v2 = create_mock_artifacts(models_v2)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts_v2, falkordblite_storage)
        
        assert len(change_set.modified) == 1
        assert "model.test.model2" in change_set.modified
        assert len(change_set.unchanged) == 1
        assert "model.test.model1" in change_set.unchanged
        
        builder._artifacts = artifacts_v2
        builder.write_incremental(falkordblite_storage, change_set)

        # Verify model fingerprint updated (hash-only, no prefix)
        fp_result = compute_model_fingerprint_result(
            resource_type="model",
            compiled_sql="select 3",
            checksum=None,
            dialect="duckdb",
            model_id="model.test.model2",
        )
        assert fp_result is not None
        expected_fp = fp_result.hash
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.model2'}) RETURN m.model_fingerprint AS model_fingerprint"
        )
        assert result.count == 1
        assert result.rows[0]["model_fingerprint"] == expected_fp

    def test_incremental_no_changes_skips_graph_write_and_derived_work(
        self, falkordblite_storage: FalkorDBLiteAdapter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """If no model_fingerprint changes, incremental run should skip writes + derived work."""
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Initial load writes fingerprint to graph
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # Add semantics so recovery doesn't trigger
        semantic = InferredSemanticModel(
            name="model1",
            model_id="model.test.model1",
            analyzed_at="2024-01-01T00:00:00Z",
            analysis_version="1.0.0",
            has_aggregations=False,
            has_time_window=False,
            has_window_functions=False,
            grain_human="",
            intent="unknown",
        )
        falkordblite_storage.upsert_node(semantic)
        edge = HasInferredSemantics()
        model_identifier = NodeIdentifier(id="model.test.model1", node_label=NodeLabel.DBT_MODEL)
        falkordblite_storage.create_edge(model_identifier, semantic, edge)

        # If the integration tries to write again during a no-change incremental run, fail the test.
        def _fail(*args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("Unexpected graph write during no-change incremental run")

        monkeypatch.setattr(LineageBuilder, "write_incremental", _fail)
        monkeypatch.setattr(LineageBuilder, "write_typed", _fail)

        integration = LineageIntegration(
            storage=falkordblite_storage,
            semantic_config=SemanticAnalysisConfig(),
            profiling_config=ProfilingConfig(),
            clustering_config=ClusteringConfig(),
            semantic_view_config=SemanticViewLoaderConfig(),
        )

        # Should not raise (no changes -> skip)
        integration.load_dbt_with_semantics(Path(artifacts_dir), incremental=True)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(FalkorDBLiteAdapter is None, reason="FalkorDBLite not available")
class TestSemanticAnalysisFiltering:
    """Tests for semantic analysis respecting change_set.
    
    Note: These tests require Fenic session setup and are marked as slow.
    """

    def test_semantic_analysis_only_changed_models(self) -> None:
        """Only analyze added/modified models."""
        # This would require Fenic session and actual semantic analysis
        # Placeholder for now - can be implemented when semantic analysis tests are added
        pytest.skip("Requires Fenic session setup")

    def test_semantic_analysis_skips_unchanged(self) -> None:
        """Skip unchanged models."""
        pytest.skip("Requires Fenic session setup")

    def test_semantic_analysis_deletes_old_nodes(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Delete old semantic nodes before re-analysis."""
        # Test that _delete_semantic_analysis works
        
        # Create a model
        model = DbtModel(
            unique_id="model.test.test_model",
            name="test_model",
            materialization="table",
        )
        falkordblite_storage.upsert_node(model)
        
        # Integration class has the delete method
        # This is a basic test that the method exists and can be called
        # Full test would require semantic nodes to be created first
        integration = LineageIntegration(
            storage=falkordblite_storage,
            semantic_config=SemanticAnalysisConfig(),
            profiling_config=ProfilingConfig(),
            clustering_config=ClusteringConfig(),
            semantic_view_config=SemanticViewLoaderConfig(),
        )
        # Should not raise error even if no semantic nodes exist
        integration._delete_semantic_analysis("model.test.test_model")


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_manifest(self, mock_storage: Mock) -> None:
        """Handle empty manifest gracefully."""
        artifacts = create_mock_artifacts([])
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.added) == 0
        assert len(change_set.modified) == 0
        assert change_set.has_changes is False

    def test_all_models_removed(self, mock_storage: Mock) -> None:
        """Handle case where all models removed."""
        # Graph has models - setup mock to handle both queries
        setup_mock_storage_for_changes(mock_storage, [
            {"id": "model.test.model1", "model_fingerprint": "deadbeef"},
            {"id": "model.test.model2", "model_fingerprint": "feedface"},
        ])
        
        # Manifest is empty
        artifacts = create_mock_artifacts([])
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        assert len(change_set.removed) == 2
        assert change_set.has_changes is True

    def test_missing_compiled_sql(self, mock_storage: Mock) -> None:
        """Handle models without compiled SQL (no fingerprint possible)."""
        # Graph is empty
        mock_storage.execute_raw_query.return_value = RawLineageQueryResult(
            rows=[],
            count=0,
            query=""
        )
        
        # Manifest has model without compiled SQL
        models = [
            create_mock_model("model.test.model1", compiled_sql=""),
        ]
        artifacts = create_mock_artifacts(models)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, mock_storage)
        
        # Should treat as added (graph empty)
        assert len(change_set.added) == 1

    def test_incremental_without_initial_load(self, falkordblite_storage: FalkorDBLiteAdapter, tmp_path: Path) -> None:
        """Handle incremental mode without prior load."""
        # Try incremental load on empty graph
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)
        
        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))
        
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        
        detector = ChangeDetector()
        change_set = detector.detect_changes(artifacts, falkordblite_storage)
        
        # Should detect all as added
        assert len(change_set.added) == 1
        
        # Should be able to write incrementally
        builder.write_incremental(falkordblite_storage, change_set)
        
        # Verify model loaded
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel) RETURN m.id AS id"
        )
        assert result.count == 1


@pytest.mark.integration
@pytest.mark.skipif(FalkorDBLiteAdapter is None, reason="FalkorDBLite not available")
class TestSemanticRecoveryIntegration:
    """End-to-end tests for semantic recovery."""

    def test_recovery_triggers_when_semantics_missing(
        self, falkordblite_storage: FalkorDBLiteAdapter, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Integration test: Recovery triggers when fingerprints unchanged but semantics missing."""
        models = [
            create_mock_model("model.test.model1", compiled_sql="select 1"),
        ]
        artifacts = create_mock_artifacts(models)

        artifacts_dir = tmp_path / "target"
        artifacts_dir.mkdir()
        (artifacts_dir / "manifest.json").write_text(json.dumps(artifacts.manifest))
        (artifacts_dir / "catalog.json").write_text(json.dumps(artifacts.catalog))

        # Initial load
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder.write_typed(falkordblite_storage)

        # No semantics added yet

        # Track semantic analysis calls
        semantic_called = False
        def _mock_semantic(*args, **kwargs):  # type: ignore[no-untyped-def]
            nonlocal semantic_called
            semantic_called = True
            return 0, 0

        monkeypatch.setattr(LineageIntegration, "_run_semantic_analysis_only", _mock_semantic)
        monkeypatch.setattr(LineageIntegration, "_create_fenic_session_if_needed", lambda *a, **k: Mock())

        profiling_config = ProfilingConfig()
        profiling_config.enabled = False

        integration = LineageIntegration(
            storage=falkordblite_storage,
            semantic_config=SemanticAnalysisConfig(),
            profiling_config=profiling_config,
            clustering_config=ClusteringConfig(),
            semantic_view_config=SemanticViewLoaderConfig(),
        )

        # Should trigger recovery (no fingerprint changes, but model missing semantics)
        integration.load_dbt_with_semantics(Path(artifacts_dir), incremental=True)

        assert semantic_called is True

