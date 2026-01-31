"""Tests for cascade deletion functionality.

Tests cover:
- delete_model_cascade implementation for FalkorDBLite
- delete_model_cascade implementation for FalkorDB
- Error handling for cascade deletion
"""
import pytest
from lineage.backends.lineage.models.dbt import DbtColumn, DbtModel
from lineage.backends.lineage.models.edges import (
    DerivesFrom,
    HasDimension,
    HasInferredSemantics,
    HasJoinEdge,
    HasMeasure,
    JoinsRightModel,
)
from lineage.backends.lineage.models.semantic_analysis import (
    InferredDimension,
    InferredMeasure,
    InferredSemanticModel,
    JoinEdge,
)
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.types import Confidence

try:
    from lineage.backends.lineage.falkordblite_adapter import FalkorDBLiteAdapter
except ImportError:
    FalkorDBLiteAdapter = None  # type: ignore


@pytest.mark.integration
@pytest.mark.skipif(FalkorDBLiteAdapter is None, reason="FalkorDBLite not available")
class TestCascadeDeletion:
    """Tests for delete_model_cascade implementation."""

    def test_delete_model_cascade_falkordblite(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Delete model and verify all child nodes removed (FalkorDBLite)."""
        # Create a model with columns
        model = DbtModel(
            unique_id="model.test.test_model",
            name="test_model",
            materialization="table",
        )
        falkordblite_storage.upsert_node(model)
        
        # Create columns
        col1 = DbtColumn(
            name="col1",
            parent_id="model.test.test_model",
            parent_label="DbtModel",
            data_type="string",
        )
        col2 = DbtColumn(
            name="col2",
            parent_id="model.test.test_model",
            parent_label="DbtModel",
            data_type="integer",
        )
        falkordblite_storage.upsert_node(col1)
        falkordblite_storage.upsert_node(col2)
        
        # Verify model and columns exist
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.test_model'}) RETURN m"
        )
        assert result.count == 1
        
        result = falkordblite_storage.execute_raw_query(
            "MATCH (c:DbtColumn) WHERE c.parent_id = 'model.test.test_model' RETURN c"
        )
        assert result.count == 2
        
        # Delete model with cascade
        falkordblite_storage.delete_model_cascade("model.test.test_model")
        
        # Verify model deleted
        result = falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.test_model'}) RETURN m"
        )
        assert result.count == 0

    def test_preserve_model_does_not_break_downstream_column_lineage(
        self, falkordblite_storage: FalkorDBLiteAdapter
    ) -> None:
        """Regression: preserve_model=True must not delete DbtColumn nodes.

        If upstream DbtColumn nodes are deleted, downstream unchanged models can lose
        their DERIVES_FROM edges permanently (because lineage extraction only re-runs
        for changed models).
        """
        # Upstream model + column
        upstream_model = DbtModel(unique_id="model.test.upstream", name="upstream", materialization="table")
        falkordblite_storage.upsert_node(upstream_model)
        upstream_col = DbtColumn(
            name="up_col",
            parent_id=upstream_model.unique_id,
            parent_label="DbtModel",
            data_type="string",
        )
        falkordblite_storage.upsert_node(upstream_col)

        # Downstream unchanged model + column
        downstream_model = DbtModel(unique_id="model.test.downstream", name="downstream", materialization="table")
        falkordblite_storage.upsert_node(downstream_model)
        downstream_col = DbtColumn(
            name="down_col",
            parent_id=downstream_model.unique_id,
            parent_label="DbtModel",
            data_type="string",
        )
        falkordblite_storage.upsert_node(downstream_col)

        # Downstream -> upstream lineage edge (incoming to upstream column)
        falkordblite_storage.create_edge(downstream_col, upstream_col, DerivesFrom(confidence=Confidence.DIRECT))

        # Add an outgoing lineage edge from upstream column that should be cleared
        other_model = DbtModel(unique_id="model.test.other", name="other", materialization="table")
        falkordblite_storage.upsert_node(other_model)
        other_col = DbtColumn(
            name="other_col",
            parent_id=other_model.unique_id,
            parent_label="DbtModel",
            data_type="string",
        )
        falkordblite_storage.upsert_node(other_col)
        falkordblite_storage.create_edge(upstream_col, other_col, DerivesFrom(confidence=Confidence.DIRECT))

        # Sanity: both edges exist
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (d:DbtColumn {id: $d})-[r:DERIVES_FROM]->(u:DbtColumn {id: $u}) RETURN r",
                params={"d": downstream_col.id, "u": upstream_col.id},
            ).count
            == 1
        )
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (u:DbtColumn {id: $u})-[r:DERIVES_FROM]->(o:DbtColumn {id: $o}) RETURN r",
                params={"u": upstream_col.id, "o": other_col.id},
            ).count
            == 1
        )

        # Preserve-model cascade delete for the upstream model (incremental update behavior)
        falkordblite_storage.delete_model_cascade(upstream_model.unique_id, preserve_model=True)

        # Upstream model + column should still exist
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (m:DbtModel {id: $id}) RETURN m",
                params={"id": upstream_model.unique_id},
            ).count
            == 1
        )
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (c:DbtColumn {id: $id}) RETURN c",
                params={"id": upstream_col.id},
            ).count
            == 1
        )

        # Incoming lineage to upstream column should survive (downstream model unchanged)
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (d:DbtColumn {id: $d})-[r:DERIVES_FROM]->(u:DbtColumn {id: $u}) RETURN r",
                params={"d": downstream_col.id, "u": upstream_col.id},
            ).count
            == 1
        )

        # Outgoing lineage from upstream columns should be cleared (to avoid stale edges)
        assert (
            falkordblite_storage.execute_raw_query(
                "MATCH (u:DbtColumn {id: $u})-[r:DERIVES_FROM]->(o:DbtColumn {id: $o}) RETURN r",
                params={"u": upstream_col.id, "o": other_col.id},
            ).count
            == 0
        )

    def test_delete_model_cascade_falkordb(self, falkordb_storage: LineageStorage) -> None:
        """Delete model and verify all child nodes removed (FalkorDB)."""
        # Create a model with columns
        model = DbtModel(
            unique_id="model.test.test_model",
            name="test_model",
            materialization="table",
        )
        falkordb_storage.upsert_node(model)
        
        # Create columns
        col1 = DbtColumn(
            name="col1",
            parent_id="model.test.test_model",
            parent_label="DbtModel",
            data_type="string",
        )
        falkordb_storage.upsert_node(col1)
        
        # Delete model with cascade
        falkordb_storage.delete_model_cascade("model.test.test_model")
        
        # Verify model deleted
        result = falkordb_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.test_model'}) RETURN m"
        )
        assert result.count == 0

    def test_delete_nonexistent_model(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Handle deletion of non-existent model gracefully."""
        # Should not raise exception and should return 0
        deleted_count = falkordblite_storage.delete_model_cascade("model.test.nonexistent")
        assert deleted_count == 0, "Expected 0 nodes deleted for non-existent model"

    def test_delete_model_read_only(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Verify deletion fails in read-only mode."""
        # Create read-only storage
        read_only_storage = FalkorDBLiteAdapter(
            db_path=falkordblite_storage.db_path,
            graph_name="test_lineage",
            read_only=True
        )
        
        with pytest.raises(ValueError, match="Cannot delete in read-only mode"):
            read_only_storage.delete_model_cascade("model.test.test_model")

    def test_delete_model_with_semantic_metadata(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Verify cascade deletion removes semantic analysis nodes."""
        # Create a model
        model = DbtModel(
            unique_id="model.test.m1",
            name="m1",
            materialization="table",
        )
        falkordblite_storage.upsert_node(model)

        # Create semantic analysis
        semantic = InferredSemanticModel(
            model_id="model.test.m1",
            name="m1",
            analyzed_at="2024-01-01T00:00:00Z",
            analysis_version="1.0",
            has_aggregations=True,
            has_time_window=False,
            has_window_functions=False,
            grain_human="per customer",
            intent="customer metrics",
        )
        falkordblite_storage.upsert_node(semantic)
        falkordblite_storage.create_edge(model, semantic, HasInferredSemantics())

        # Create child semantic nodes (measure and dimension)
        measure = InferredMeasure(
            name="total_revenue",
            semantic_model_id=semantic.id,
            expr="revenue",
            agg_function="SUM",
        )
        dimension = InferredDimension(
            name="customer_id",
            semantic_model_id=semantic.id,
            source="customers.id",
            is_pii=False,
        )
        falkordblite_storage.upsert_node(measure)
        falkordblite_storage.upsert_node(dimension)
        falkordblite_storage.create_edge(semantic, measure, HasMeasure())
        falkordblite_storage.create_edge(semantic, dimension, HasDimension())

        # Verify all nodes exist
        assert falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.m1'}) RETURN m"
        ).count == 1
        assert falkordblite_storage.execute_raw_query(
            "MATCH (s:InferredSemanticModel {model_id: 'model.test.m1'}) RETURN s"
        ).count == 1
        assert falkordblite_storage.execute_raw_query(
            f"MATCH (meas:InferredMeasure {{id: '{measure.id}'}}) RETURN meas"
        ).count == 1
        assert falkordblite_storage.execute_raw_query(
            f"MATCH (dim:InferredDimension {{id: '{dimension.id}'}}) RETURN dim"
        ).count == 1

        # Delete model with cascade
        falkordblite_storage.delete_model_cascade("model.test.m1")

        # Verify model deleted
        assert falkordblite_storage.execute_raw_query(
            "MATCH (m:DbtModel {id: 'model.test.m1'}) RETURN m"
        ).count == 0

        # Verify semantic node deleted
        assert falkordblite_storage.execute_raw_query(
            "MATCH (s:InferredSemanticModel {model_id: 'model.test.m1'}) RETURN s"
        ).count == 0

        # Verify child semantic nodes deleted
        assert falkordblite_storage.execute_raw_query(
            f"MATCH (meas:InferredMeasure {{id: '{measure.id}'}}) RETURN meas"
        ).count == 0
        assert falkordblite_storage.execute_raw_query(
            f"MATCH (dim:InferredDimension {{id: '{dimension.id}'}}) RETURN dim"
        ).count == 0

    def test_semantic_cleanup_does_not_delete_other_models(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Regression test: verify semantic cleanup does not delete unrelated DbtModel nodes via JoinEdge links."""
        # 1. Setup: Create model_a (to be deleted) and model_b (should survive)
        model_a = DbtModel(unique_id="model.test.a", name="model_a", materialization="table")
        model_b = DbtModel(unique_id="model.test.b", name="model_b", materialization="table")
        falkordblite_storage.upsert_node(model_a)
        falkordblite_storage.upsert_node(model_b)
        
        # 2. Setup: Create semantic analysis for model_a
        sem_a = InferredSemanticModel(
            id="model.test.a.inferred_semantics",
            model_id="model.test.a",
            name="model_a",
            analyzed_at="2025-01-01T00:00:00Z",
            analysis_version="1.0",
            has_aggregations=False,
            has_time_window=False,
            has_window_functions=False,
            grain_human="per record",
            intent="test model"
        )
        falkordblite_storage.upsert_node(sem_a)
        falkordblite_storage.create_edge(model_a, sem_a, HasInferredSemantics())
        
        # 3. Setup: Create a JoinEdge owned by model_a that links to model_b
        join_edge = JoinEdge(
            id="model.test.a.inferred_semantics.join.a.b",
            semantic_model_id=sem_a.id,
            name="a_to_b",
            join_type="inner",
            left_alias="a",
            right_alias="b",
            equi_condition="a.id = b.id"
        )
        falkordblite_storage.upsert_node(join_edge)
        falkordblite_storage.create_edge(sem_a, join_edge, HasJoinEdge())
        falkordblite_storage.create_edge(join_edge, model_b, JoinsRightModel())
        
        # Verify setup
        assert falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.a'}) RETURN m").count == 1
        assert falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.b'}) RETURN m").count == 1
        assert falkordblite_storage.execute_raw_query("MATCH (s:InferredSemanticModel {id: 'model.test.a.inferred_semantics'}) RETURN s").count == 1
        
        # 4. Action: Delete model_a cascade
        falkordblite_storage.delete_model_cascade("model.test.a")
        
        # 5. Assert: model_a and its semantics are gone, but model_b SURVIVES
        assert falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.a'}) RETURN m").count == 0
        assert falkordblite_storage.execute_raw_query("MATCH (s:InferredSemanticModel {id: 'model.test.a.inferred_semantics'}) RETURN s").count == 0
        assert falkordblite_storage.execute_raw_query("MATCH (j:JoinEdge {id: 'model.test.a.inferred_semantics.join.a.b'}) RETURN j").count == 0
        
        # CRITICAL ASSERTION: model_b must still exist
        result_b = falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.b'}) RETURN m")
        assert result_b.count == 1, "model_b was accidentally deleted by cascade delete of model_a!"

    def test_integration_semantic_cleanup_does_not_delete_other_models(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """Regression test: verify the semantic cleanup query used in Integration does not delete unrelated models."""
        # 1. Setup: Create model_a (to be cleaned up) and model_b (should survive)
        model_a = DbtModel(unique_id="model.test.a", name="model_a", materialization="table")
        model_b = DbtModel(unique_id="model.test.b", name="model_b", materialization="table")
        falkordblite_storage.upsert_node(model_a)
        falkordblite_storage.upsert_node(model_b)
        
        # 2. Setup: Create semantic analysis for model_a
        sem_a = InferredSemanticModel(
            id="model.test.a.inferred_semantics",
            model_id="model.test.a",
            name="model_a",
            analyzed_at="2025-01-01T00:00:00Z",
            analysis_version="1.0",
            has_aggregations=False,
            has_time_window=False,
            has_window_functions=False,
            grain_human="per record",
            intent="test model"
        )
        falkordblite_storage.upsert_node(sem_a)
        falkordblite_storage.create_edge(model_a, sem_a, HasInferredSemantics())
        
        # 3. Setup: Create a JoinEdge owned by model_a that links to model_b
        join_edge = JoinEdge(
            id="model.test.a.inferred_semantics.join.a.b",
            semantic_model_id=sem_a.id,
            name="a_to_b",
            join_type="inner",
            left_alias="a",
            right_alias="b",
            equi_condition="a.id = b.id"
        )
        falkordblite_storage.upsert_node(join_edge)
        falkordblite_storage.create_edge(sem_a, join_edge, HasJoinEdge())
        falkordblite_storage.create_edge(join_edge, model_b, JoinsRightModel())
        
        # 4. Action: Run the specific query used in Integration._delete_semantic_analysis
        # We simulate the string replacement logic used in the actual method
        query = """
            MATCH (m:DbtModel {id: $model_id})-[:HAS_INFERRED_SEMANTICS]->(sem:InferredSemanticModel)
            OPTIONAL MATCH (child)
            WHERE child.semantic_model_id = sem.id AND NOT child:DbtModel
            DETACH DELETE child
            DETACH DELETE sem
        """
        falkordblite_storage.execute_raw_query(query.replace("$model_id", "'model.test.a'"))
        
        # 5. Assert: model_a semantics are gone, but model_b SURVIVES
        assert falkordblite_storage.execute_raw_query("MATCH (s:InferredSemanticModel {id: 'model.test.a.inferred_semantics'}) RETURN s").count == 0
        assert falkordblite_storage.execute_raw_query("MATCH (j:JoinEdge {id: 'model.test.a.inferred_semantics.join.a.b'}) RETURN j").count == 0
        
        # model_a itself should still exist (this query only deletes semantics)
        assert falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.a'}) RETURN m").count == 1
        
        # CRITICAL ASSERTION: model_b must still exist
        result_b = falkordblite_storage.execute_raw_query("MATCH (m:DbtModel {id: 'model.test.b'}) RETURN m")
        assert result_b.count == 1, "model_b was accidentally deleted by semantic cleanup of model_a!"



