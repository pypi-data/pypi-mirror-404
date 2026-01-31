"""Storage backend implementations for lineage metadata.

Available backends:
- KùzuDB (embedded graph database)
- PostgreSQL AGE (graph extension for PostgreSQL)
- Neo4j (native graph database)
- ArcadeDB (multi-model database)

Quick Start:
    from lineage.storage import create_storage

    # From environment
    storage = create_storage()

    # Specific backend
    storage = create_storage(backend="neo4j")

    # From config file
    storage = create_storage(config_path="default_configs/lineage/neo4j.yml")
"""

from lineage.backends.lineage.protocol import LineageStorage, JobNode, DatasetNode, RunNode, JoinEdge, ClusterInfo
from lineage.backends.lineage.base import BaseLineageStorage



from lineage.backends.lineage.factory import (
    create_storage,
    create_storage_for_cli,
)
from lineage.backends.types import LineageStorageType, DataBackendType

__all__ = [
    # Protocol
    "LineageStorage",
    "JobNode",
    "DatasetNode",
    "RunNode",
    "JoinEdge",
    "ClusterInfo",
    # Base
    "BaseLineageStorage",
    # Factory functions (use unified config)
    "create_storage",
    "create_storage_for_cli",
    # Type enums
    "LineageStorageType",
    "DataBackendType",
]
