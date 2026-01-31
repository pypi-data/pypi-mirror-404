"""FalkorDB adapter implementing LineageStorage protocol.

FalkorDB is a Redis-based graph database with Cypher query support.
Key characteristics:
- Redis protocol (default port 6379)
- Cypher query language (with some limitations)
- Manual index creation required
- No regex support, no temporal arithmetic
"""
from __future__ import annotations

import logging

from lineage.backends.lineage._base_falkordb_adapter import _BaseFalkorDBAdapter

logger = logging.getLogger(__name__)

try:
    from falkordb import FalkorDB
except ImportError as exc:
    raise ImportError(
        "falkordb is required for FalkorDB backend. Install with: pip install falkordb"
    ) from exc


class FalkorDBAdapter(_BaseFalkorDBAdapter):
    """FalkorDB adapter implementing LineageStorage protocol.

    This adapter connects to FalkorDB (Redis-based graph database) and implements
    the minimal LineageStorage interface: upsert_node(), create_edge(), execute_raw_query().

    All specific node/edge operations are inherited from _BaseFalkorDBAdapter.

    FalkorDB-specific notes:
    - Uses Redis protocol (default port 6379)
    - Supports most Cypher syntax except regex and temporal functions
    - Requires manual index creation (no automatic indexing)
    - Properties are deleted with SET prop = NULL (not REMOVE)
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        username: str = "td-data-intelligence",
        password: str = "",
        graph_name: str = "lineage",
        read_only: bool = False,
    ):
        """Initialize FalkorDB adapter.

        Args:
            host: FalkorDB/Redis host
            port: FalkorDB/Redis port (default: 6379)
            username: Authentication username (default: "td-data-intelligence")
            password: Authentication password (empty string for no auth)
            graph_name: Name of the graph to use
            read_only: If True, prevent write operations
        """
        super().__init__(graph_name=graph_name, read_only=read_only)

        self.host = host
        self.port = port
        self.username = username
        self.password = password

        # Create client
        # Note: FalkorDB client may have different connection parameters
        # Check the actual FalkorDB Python client API
        if username and password:
            self.client = FalkorDB(host=host, port=port, username=username, password=password)
        else:
            self.client = FalkorDB(host=host, port=port)

        # Select graph
        self.graph = self.client.select_graph(graph_name)

        logger.info(
            f"Connected to FalkorDB at {host}:{port}, graph={graph_name} (read_only={read_only})"
        )

    def copy_graph(
        self,
        source_graph: str,
        dest_graph: str,
    ) -> None:
        """Copy a graph using GRAPH.COPY command.

        Creates an exact copy of the source graph with a new name.
        This is useful for creating isolated task-specific graphs from a base graph.

        Args:
            source_graph: Name of the source graph to copy
            dest_graph: Name for the new copied graph
        """
        # GRAPH.COPY is a Redis command, execute via the connection
        self.client.connection.execute_command("GRAPH.COPY", source_graph, dest_graph)
        logger.info(f"Copied graph '{source_graph}' to '{dest_graph}'")

    def delete_graph(self, graph_name: str) -> None:
        """Delete a graph by name.

        Args:
            graph_name: Name of the graph to delete
        """
        # Use GRAPH.DELETE Redis command
        self.client.connection.execute_command("GRAPH.DELETE", graph_name)
        logger.info(f"Deleted graph '{graph_name}'")
