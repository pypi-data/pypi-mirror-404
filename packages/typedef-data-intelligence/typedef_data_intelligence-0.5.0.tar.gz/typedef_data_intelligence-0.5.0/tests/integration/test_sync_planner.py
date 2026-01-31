"""Tests for the SyncPlanner class."""
from unittest.mock import Mock

import pytest
from lineage.backends.lineage.protocol import LineageStorage, RawLineageQueryResult
from lineage.ingest.config import SemanticAnalysisConfig
from lineage.ingest.static_loaders.change_detection import ModelChangeSet
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtModelNode
from lineage.integration import SyncPlanner


@pytest.fixture
def mock_storage() -> Mock:
    """Mock the lineage storage."""
    return Mock(spec=LineageStorage)

@pytest.fixture
def mock_semantic_config() -> SemanticAnalysisConfig:
    """Mock the semantic analysis config."""
    config = SemanticAnalysisConfig()
    config.enabled = True
    return config

@pytest.fixture
def planner(mock_storage: Mock, mock_semantic_config: SemanticAnalysisConfig) -> SyncPlanner:
    """Mock the planner."""
    return SyncPlanner(
        storage=mock_storage,
        enable_semantic=True,
        enable_profiling=True,
        enable_clustering=True,
        enable_semantic_views=True,
        semantic_config=mock_semantic_config,
    )

def create_mock_model(unique_id: str, compiled_sql: str = "select 1", resource_type: str = "model", materialization: str = "table") -> DbtModelNode:
    """Create a mock model."""
    return DbtModelNode(
        unique_id=unique_id,
        name=unique_id.split(".")[-1],
        resource_type=resource_type,
        materialization=materialization,
        compiled_sql=compiled_sql,
        description="",
        tags=[],
        meta={},
        database="db",
        schema="schema",
        alias="alias",
        relation_name="rel",
        depends_on_nodes=[],
        depends_on_sources=[],
        depends_on_macros=[],
        raw_sql="select 1",
        columns={},
        original_path="path",
        source_path="path",
        compiled_path="path",
        checksum=None,
    )

def test_planner_full_load(planner: SyncPlanner, mock_storage: Mock) -> None:
    """Test the planner full load."""
    # Setup
    models = [create_mock_model("model.a"), create_mock_model("model.b")]
    artifacts = Mock()
    artifacts.project_name = "test_project"
    
    # Execute
    plan = planner.create_plan(
        artifacts=artifacts,
        models_list=models,
        graph_was_empty=True,
        incremental=False,
    )
    
    # Assert
    assert plan.run_dbt_write is True
    assert plan.skip_all_derived is False
    assert len(plan.models_to_analyze) == 2
    assert len(plan.models_to_profile) == 2
    assert plan.allow_cache_read is True

def test_planner_incremental_no_changes_early_exit(planner: SyncPlanner, mock_storage: Mock) -> None:
    """Test the planner incremental no changes early exit."""
    # Setup
    models = [create_mock_model("model.a")]
    artifacts = Mock()
    artifacts.project_name = "test_project"
    
    # Mock detector to return no changes
    detector_mock = Mock()
    detector_mock.detect_changes.return_value = ModelChangeSet([], [], [], ["model.a"])
    
    # We need to mock the detector instantiation inside SyncPlanner._detect_incremental_changes
    # or just mock the _detect_incremental_changes method itself for this unit test.
    planner._detect_incremental_changes = Mock(return_value=ModelChangeSet([], [], [], ["model.a"]))
    
    # Mock graph to say all semantics exist (no recovery)
    mock_storage.execute_raw_query.return_value = RawLineageQueryResult(rows=[], count=0, query="")
    
    # Execute
    plan = planner.create_plan(
        artifacts=artifacts,
        models_list=models,
        graph_was_empty=False,
        incremental=True,
        builder=Mock(),
    )
    
    # Assert
    assert plan.run_dbt_write is False
    assert plan.skip_all_derived is True
    assert len(plan.models_to_analyze) == 0
    assert plan.is_semantic_recovery is False

def test_planner_semantic_recovery(planner: SyncPlanner, mock_storage: Mock) -> None:
    """Test the planner semantic recovery."""
    # Setup
    models = [create_mock_model("model.a")]
    artifacts = Mock()
    artifacts.project_name = "test_project"
    
    # No fingerprint changes
    planner._detect_incremental_changes = Mock(return_value=ModelChangeSet([], [], [], ["model.a"]))
    
    # BUT model.a is missing semantics in the graph
    mock_storage.execute_raw_query.return_value = RawLineageQueryResult(rows=[{"id": "model.a"}], count=1, query="")
    
    # Execute
    plan = planner.create_plan(
        artifacts=artifacts,
        models_list=models,
        graph_was_empty=False,
        incremental=True,
        builder=Mock(),
    )
    
    # Assert
    assert plan.run_dbt_write is False  # dbt doesn't need to write
    assert plan.skip_all_derived is False  # Derived work should NOT be skipped
    assert plan.is_semantic_recovery is True
    assert len(plan.models_to_analyze) == 1
    assert plan.models_to_analyze[0].unique_id == "model.a"
    assert plan.allow_cache_read is True  # Allowed in recovery

