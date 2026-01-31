"""Tests for find_upstream functionality.

Tests cover:
- find_upstream returns direct dependencies (depth=1)
- find_upstream returns transitive dependencies (depth>1)
- find_upstream returns empty list for leaf nodes
- find_upstream handles case-insensitive model IDs
"""
import pytest
from lineage.backends.lineage.models.dbt import DbtModel
from lineage.backends.lineage.models.edges import DependsOn

try:
    from lineage.backends.lineage.falkordblite_adapter import FalkorDBLiteAdapter
except ImportError:
    FalkorDBLiteAdapter = None  # type: ignore


@pytest.mark.integration
@pytest.mark.skipif(FalkorDBLiteAdapter is None, reason="FalkorDBLite not available")
class TestFindUpstream:
    """Tests for find_upstream implementation."""

    def test_find_upstream_direct_dependencies(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream returns direct upstream dependencies (depth=1)."""
        # Create a dependency chain: base -> intermediate -> final
        base = DbtModel(
            unique_id="model.test.base",
            name="base",
            materialization="table",
        )
        intermediate = DbtModel(
            unique_id="model.test.intermediate",
            name="intermediate",
            materialization="table",
        )
        final = DbtModel(
            unique_id="model.test.final",
            name="final",
            materialization="table",
        )
        
        falkordblite_storage.upsert_node(base)
        falkordblite_storage.upsert_node(intermediate)
        falkordblite_storage.upsert_node(final)
        
        # Create dependencies: final -> intermediate -> base
        falkordblite_storage.create_edge(
            final,
            intermediate,
            DependsOn(type="model", direct=True),
        )
        falkordblite_storage.create_edge(
            intermediate,
            base,
            DependsOn(type="model", direct=True),
        )
        
        # Find direct upstream (depth=1) from final
        upstream = falkordblite_storage.find_upstream("model.test.final", depth=1)
        assert len(upstream) == 1
        assert "model.test.intermediate" in upstream
        
    def test_find_upstream_transitive_dependencies(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream returns transitive dependencies with depth>1."""
        # Create a dependency chain: base -> intermediate -> final
        base = DbtModel(
            unique_id="model.test.base",
            name="base",
            materialization="table",
        )
        intermediate = DbtModel(
            unique_id="model.test.intermediate",
            name="intermediate",
            materialization="table",
        )
        final = DbtModel(
            unique_id="model.test.final",
            name="final",
            materialization="table",
        )
        
        falkordblite_storage.upsert_node(base)
        falkordblite_storage.upsert_node(intermediate)
        falkordblite_storage.upsert_node(final)
        
        # Create dependencies: final -> intermediate -> base
        falkordblite_storage.create_edge(
            final,
            intermediate,
            DependsOn(type="model", direct=True),
        )
        falkordblite_storage.create_edge(
            intermediate,
            base,
            DependsOn(type="model", direct=True),
        )
        
        # Find transitive upstream (depth=2) from final
        upstream = falkordblite_storage.find_upstream("model.test.final", depth=2)
        assert len(upstream) == 2
        assert "model.test.intermediate" in upstream
        assert "model.test.base" in upstream
        
    def test_find_upstream_multiple_direct_dependencies(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream returns all direct upstream dependencies."""
        # Create a diamond dependency:
        #   left -> final
        #   right -> final
        left = DbtModel(
            unique_id="model.test.left",
            name="left",
            materialization="table",
        )
        right = DbtModel(
            unique_id="model.test.right",
            name="right",
            materialization="table",
        )
        final = DbtModel(
            unique_id="model.test.final",
            name="final",
            materialization="table",
        )
        
        falkordblite_storage.upsert_node(left)
        falkordblite_storage.upsert_node(right)
        falkordblite_storage.upsert_node(final)
        
        # Create dependencies: final -> left, final -> right
        falkordblite_storage.create_edge(
            final,
            left,
            DependsOn(type="model", direct=True),
        )
        falkordblite_storage.create_edge(
            final,
            right,
            DependsOn(type="model", direct=True),
        )
        
        # Find direct upstream from final
        upstream = falkordblite_storage.find_upstream("model.test.final", depth=1)
        assert len(upstream) == 2
        assert "model.test.left" in upstream
        assert "model.test.right" in upstream
        
    def test_find_upstream_leaf_node_returns_empty(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream returns empty list for leaf nodes with no dependencies."""
        base = DbtModel(
            unique_id="model.test.base",
            name="base",
            materialization="table",
        )
        
        falkordblite_storage.upsert_node(base)
        
        # Find upstream from leaf node
        upstream = falkordblite_storage.find_upstream("model.test.base", depth=1)
        assert len(upstream) == 0
        
    def test_find_upstream_case_insensitive(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream handles case-insensitive model IDs."""
        base = DbtModel(
            unique_id="model.test.BASE",
            name="BASE",
            materialization="table",
        )
        final = DbtModel(
            unique_id="model.test.FINAL",
            name="FINAL",
            materialization="table",
        )
        
        falkordblite_storage.upsert_node(base)
        falkordblite_storage.upsert_node(final)
        
        # Create dependency: final -> base
        falkordblite_storage.create_edge(
            final,
            base,
            DependsOn(type="model", direct=True),
        )
        
        # Find upstream with lowercase query (should match FINAL)
        upstream = falkordblite_storage.find_upstream("model.test.final", depth=1)
        assert len(upstream) == 1
        assert upstream[0].lower() == "model.test.base".lower()
        
    def test_find_upstream_nonexistent_node_returns_empty(self, falkordblite_storage: FalkorDBLiteAdapter) -> None:
        """find_upstream returns empty list for nonexistent node."""
        upstream = falkordblite_storage.find_upstream("model.test.nonexistent", depth=1)
        assert len(upstream) == 0
