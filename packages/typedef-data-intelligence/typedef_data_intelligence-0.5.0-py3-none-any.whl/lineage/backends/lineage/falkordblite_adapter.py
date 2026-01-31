"""FalkorDBLite adapter implementing LineageStorage protocol.

FalkorDBLite is an embedded Redis-based graph database with Cypher query support.
Key characteristics:
- File-backed (no network connection required)
- Cypher query language (with some limitations)
- Manual index creation required
- No regex support, no temporal arithmetic
- Self-contained Redis server with FalkorDB module
"""
from __future__ import annotations

import logging
import os

from lineage.backends.lineage._base_falkordb_adapter import _BaseFalkorDBAdapter

logger = logging.getLogger(__name__)

try:
    from redislite.falkordb_client import FalkorDB
except ImportError as exc:
    raise ImportError(
        "redislite and falkordb are required for FalkorDBLite backend. "
        "Install with: pip install redislite falkordb"
    ) from exc


class FalkorDBLiteAdapter(_BaseFalkorDBAdapter):
    """FalkorDBLite adapter implementing LineageStorage protocol.

    This adapter connects to FalkorDBLite (embedded file-backed graph database)
    and implements the minimal LineageStorage interface: upsert_node(),
    create_edge(), execute_raw_query().

    All specific node/edge operations are inherited from _BaseFalkorDBAdapter.

    FalkorDBLite-specific notes:
    - Uses file-backed storage (no network connection required)
    - Supports most Cypher syntax except regex and temporal functions
    - Requires manual index creation (no automatic indexing)
    - Properties are deleted with SET prop = NULL (not REMOVE)
    - Ideal for development, testing, prototyping, and educational purposes
    """

    def __init__(
        self,
        db_path: str = "lineage_store/falkordb.db",
        graph_name: str = "lineage",
        read_only: bool = False,
    ):
        """Initialize FalkorDBLite adapter.

        Args:
            db_path: Path to FalkorDBLite database file (will be created if doesn't exist)
            graph_name: Name of the graph to use
            read_only: If True, prevent write operations
        """
        super().__init__(graph_name=graph_name, read_only=read_only)

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path

        # Create file-backed FalkorDBLite client
        self.client = FalkorDB(db_path)

        # Select graph
        self.graph = self.client.select_graph(graph_name)

        logger.info(
            f"Connected to FalkorDBLite at {db_path}, graph={graph_name} (read_only={read_only})"
        )

    def close(self):
        """Close the FalkorDBLite client and shut down embedded Redis."""
        if self.client:
            try:
                # redislite.falkordb_client.FalkorDB wraps a redislite.Redis instance.
                # Calling shutdown() stops the embedded redis-server process immediately.
                self.client.close()
            except Exception as e:
                logger.warning(f"Failed to shut down FalkorDBLite embedded Redis: {e}")

        super().close()
