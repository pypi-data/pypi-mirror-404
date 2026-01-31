"""Shared fixtures for incremental loading tests."""
import uuid
from pathlib import Path
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

# KuzuAdapter import removed - using FalkorDBLite instead
from lineage.backends.lineage.protocol import LineageStorage, RawLineageQueryResult
from lineage.ingest.static_loaders.dbt.dbt_loader import (
    ChecksumInfo,
    DbtModelNode,
    RawDbtArtifacts,
)

# Load .env from monorepo root (one level above package root)
package_root = Path(__file__).parent.parent.parent
repo_root = package_root.parent
for candidate in [repo_root / ".env", repo_root / ".local.env", repo_root / ".test.env"]:
    if candidate.exists():
        load_dotenv(candidate)


@pytest.fixture
def temp_db_path(tmp_path):
    """Temporary database path for tests."""
    return tmp_path / "test_lineage.db"


# Session-scoped FalkorDBLite connection - reuses a single redislite server
# for the entire test session, significantly speeding up tests
@pytest.fixture(scope="session")
def _falkordblite_session_db(tmp_path_factory):
    """Session-scoped FalkorDBLite database (internal fixture)."""
    try:
        from lineage.backends.lineage.falkordblite_adapter import FalkorDBLiteAdapter
        db_path = tmp_path_factory.mktemp("data") / "test_lineage.db"
        # Create adapter with a placeholder graph - each test gets its own graph
        adapter = FalkorDBLiteAdapter(
            db_path=str(db_path),
            graph_name="session_init",  # Will be switched per test
        )
        yield adapter
        adapter.close()
    except ImportError:
        pytest.skip("FalkorDBLite not available (redislite and falkordb required)")


@pytest.fixture
def falkordblite_storage(_falkordblite_session_db):
    """FalkorDBLiteAdapter instance with unique graph per test.

    Uses a session-scoped database connection but creates a unique graph
    for each test, avoiding the overhead of starting redislite multiple times.
    """
    adapter = _falkordblite_session_db
    # Use a unique graph name for each test to ensure isolation
    graph_name = f"test_{uuid.uuid4().hex[:8]}"

    # Switch to the new graph and recreate schema
    adapter.graph_name = graph_name
    adapter.graph = adapter.client.select_graph(graph_name)
    adapter.recreate_schema()

    yield adapter

    # Cleanup: delete the test graph to save memory
    try:
        adapter.graph.delete()
    except Exception:
        pass  # Ignore cleanup errors


@pytest.fixture
def falkordb_storage():
    """FalkorDBAdapter instance (skip if not available)."""
    try:
        from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter
        storage = FalkorDBAdapter(
            host="localhost",
            port=6379,
            graph_name="test_lineage",
        )
        storage.recreate_schema()
        yield storage
        # Cleanup: delete test graph
        try:
            storage.delete_graph("test_lineage")
        except Exception:
            pass
        storage.close()
    except ImportError:
        pytest.skip("FalkorDB not available")


@pytest.fixture
def mock_storage():
    """Mock LineageStorage for unit tests."""
    storage = Mock(spec=LineageStorage)
    storage.execute_raw_query = Mock(return_value=RawLineageQueryResult(
        rows=[],
        count=0,
        query=""
    ))
    return storage


def create_mock_model(
    unique_id: str,
    checksum: str = "abc123",
    name: str = None,
    compiled_sql: str = "SELECT 1",
    materialization: str = "table",
) -> DbtModelNode:
    """Create a mock DbtModelNode for testing."""
    if name is None:
        name = unique_id.split(".")[-1]
    
    return DbtModelNode(
        unique_id=unique_id,
        name=name,
        resource_type="model",
        description=None,
        tags=[],
        meta={},
        database="test_db",
        schema="test_schema",
        alias=name,
        relation_name=f"test_schema.{name}",
        materialization=materialization,
        depends_on_nodes=[],
        depends_on_sources=[],
        compiled_sql=compiled_sql,
        columns={},
        checksum=ChecksumInfo(name="sha256", checksum=checksum) if checksum else None,
    )


def create_mock_artifacts(models: list[DbtModelNode]) -> RawDbtArtifacts:
    """Create mock DbtArtifacts from a list of models."""
    # Create minimal manifest structure
    manifest = {
        "metadata": {
            "project_name": "test_project",
            "adapter_type": "duckdb",
            "target_name": "dev",
        },
        "nodes": {
            model.unique_id: {
                "resource_type": "model",
                "name": model.name,
                "original_file_path": f"models/{model.name}.sql",
                "compiled_sql": model.compiled_sql,
                "checksum": {
                    "name": model.checksum.name if model.checksum else "sha256",
                    "checksum": model.checksum.checksum if model.checksum else "",
                } if model.checksum else None,
            }
            for model in models
        },
    }
    
    catalog = {
        "nodes": {
            model.unique_id: {}
            for model in models
        }
    }
    
    # Create minimal config
    from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
    config = DbtArtifactsConfig()
    config.target_path = Path("/tmp/test_target")
    
    return RawDbtArtifacts(
        config=config,
        manifest=manifest,
        catalog=catalog,
        run_results={},
    )


@pytest.fixture
def sample_manifest():
    """Sample dbt manifest.json structure."""
    return {
        "metadata": {
            "project_name": "test_project",
            "adapter_type": "duckdb",
            "target_name": "dev",
        },
        "nodes": {
            "model.test.fct_orders": {
                "resource_type": "model",
                "name": "fct_orders",
                "original_file_path": "models/fct_orders.sql",
                "compiled_sql": "SELECT * FROM orders",
                "checksum": {
                    "name": "sha256",
                    "checksum": "abc123",
                },
            },
            "model.test.dim_customers": {
                "resource_type": "model",
                "name": "dim_customers",
                "original_file_path": "models/dim_customers.sql",
                "compiled_sql": "SELECT * FROM customers",
                "checksum": {
                    "name": "sha256",
                    "checksum": "def456",
                },
            },
        },
    }

