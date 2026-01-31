"""FalkorDB memory adapter using Graphiti for temporal knowledge graphs.

This adapter implements the MemoryStorage protocol using Graphiti's temporal
knowledge graph framework with FalkorDB as the backend.

Key Features:
- Multi-tenant memory isolation (separate graphs per user/org)
- Temporal knowledge graphs with validity intervals
- Hybrid search (semantic + keyword + graph traversal)
- Automatic entity extraction and relationship building

Architecture:
- User Memory: Each user gets a separate graph (user_memory_{user_id})
- Org Memory: Each org gets a separate graph (org_memory_{org_id})
- Graphiti handles entity extraction, embeddings, and temporal indexing
- FalkorDB provides fast graph queries with sub-millisecond response times
"""

from __future__ import annotations

import logging
from typing import Any

from graphiti_core import Graphiti

from lineage.backends.memory.graphiti_adapter import GraphitiMemoryAdapter

logger = logging.getLogger(__name__)


class FalkorDBMemoryAdapter(GraphitiMemoryAdapter):
    """FalkorDB + Graphiti implementation of MemoryStorage protocol.

    This adapter uses Graphiti's temporal knowledge graph framework to store
    and retrieve agent memory in FalkorDB.

    Multi-Tenancy:
    - Each user gets their own graph: user_memory_{user_id}
    - Each org gets their own graph: org_memory_{org_id}
    - Graphs are completely isolated from each other

    Graphiti Features:
    - Automatic entity extraction from episode content
    - Semantic embeddings for similarity search
    - Temporal validity tracking (t_valid, t_invalid)
    - BM25 keyword matching
    - Graph distance reranking

    Example:
        ```python
        adapter = FalkorDBMemoryAdapter(
            host="localhost",
            port=6379,
            password="mypassword"
        )

        # Store user preference
        episode = Episode(
            name="chart_pref",
            content="User prefers bar charts for ARR",
            episode_type=EpisodeType.USER_PREFERENCE,
            source_description="Chat session"
        )
        await adapter.store_user_memory(user_id="alice", episode=episode)

        # Search
        results = await adapter.search_user_memory(user_id="alice", query="charts")
        ```
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        username: str = "",
        password: str = "",
        default_org_id: str = "default",
    ):
        """Initialize FalkorDB memory adapter.

        Args:
            host: FalkorDB host (default: localhost)
            port: FalkorDB port (default: 6379)
            username: FalkorDB username (optional)
            password: FalkorDB password (optional)
            default_org_id: Default organization ID (default: "default")

        Raises:
            ImportError: If graphiti-core is not installed
            ConnectionError: If cannot connect to FalkorDB
        """
        super().__init__()

        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.default_org_id = default_org_id

        logger.info(
            f"Initialized FalkorDB memory adapter: {host}:{port} "
            f"(default_org={default_org_id})"
        )

    def _create_driver(self, graph_name: str) -> Any:
        """Create FalkorDB driver for the given graph.

        Args:
            graph_name: Name of the graph (used as database name)

        Returns:
            FalkorDriver instance

        Raises:
            ImportError: If graphiti-core-falkordb is not installed
        """
        try:
            from graphiti_core.driver.falkordb_driver import FalkorDriver
        except ImportError:
            raise ImportError(
                "graphiti-core-falkordb is not installed. Install with: "
                "pip install graphiti-core-falkordb"
            )

        # Create FalkorDB driver
        driver = FalkorDriver(
            host=self.host,
            port=self.port,
            username=self.username if self.username else None,
            password=self.password if self.password else None,
            database=graph_name,
        )

        return driver

    async def _build_indices(self, graphiti: Graphiti) -> None:
        """Build indices and constraints for FalkorDB graph.

        This is idempotent - safe to call multiple times.

        Args:
            graphiti: Graphiti instance
        """
        try:
            await graphiti.build_indices_and_constraints()
        except Exception as e:
            logger.debug(f"Index creation skipped (may already exist): {e}")

    async def clear_user_memory(self, user_id: str) -> None:
        """Clear all memory for a specific user.

        WARNING: This permanently deletes the user's memory graph.

        Args:
            user_id: User identifier
        """
        graph_name = self._user_graph_name(user_id)

        # Remove from cache
        if graph_name in self._graphiti_cache:
            graphiti = self._graphiti_cache.pop(graph_name)
            # Close the connection
            graphiti.close()

        # Delete the graph in FalkorDB
        # Note: This requires direct FalkorDB connection
        try:
            from falkordb import FalkorDB

            client = FalkorDB(
                host=self.host,
                port=self.port,
                username=self.username if self.username else None,
                password=self.password if self.password else None,
            )
            # Delete graph
            client.delete_graph(graph_name)
            logger.info(f"Deleted user memory graph: {graph_name}")
        except Exception as e:
            logger.error(f"Failed to delete user memory: {e}")

    async def clear_org_memory(self, org_id: str) -> None:
        """Clear all organization memory.

        WARNING: This permanently deletes the organization's memory graph.

        Args:
            org_id: Organization identifier
        """
        graph_name = self._org_graph_name(org_id)

        # Remove from cache
        if graph_name in self._graphiti_cache:
            graphiti = self._graphiti_cache.pop(graph_name)
            graphiti.close()

        # Delete the graph in FalkorDB
        try:
            from falkordb import FalkorDB

            client = FalkorDB(
                host=self.host,
                port=self.port,
                username=self.username if self.username else None,
                password=self.password if self.password else None,
            )
            client.delete_graph(graph_name)
            logger.info(f"Deleted org memory graph: {graph_name}")
        except Exception as e:
            logger.error(f"Failed to delete org memory: {e}")


__all__ = ["FalkorDBMemoryAdapter"]
