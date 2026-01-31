"""FalkorDBLite memory backend (embedded, no Docker required).

This adapter implements the MemoryStorage protocol using Graphiti's temporal
knowledge graph framework with FalkorDBLite (embedded) as the backend.

Key Features:
- No Docker required (file-backed embedded database)
- Multi-tenant memory isolation (separate graphs per user/org)
- Temporal knowledge graphs with validity intervals
- Hybrid search (semantic + keyword + graph traversal)
- Automatic entity extraction and relationship building

Architecture:
- User Memory: Each user gets a separate graph (user_memory_{user_id})
- Org Memory: Each org gets a separate graph (org_memory_{org_id})
- FalkorDBLite provides embedded storage in local file
"""

from __future__ import annotations

import logging

from graphiti_core import Graphiti

from lineage.backends.memory.graphiti_adapter import GraphitiMemoryAdapter

logger = logging.getLogger(__name__)


class FalkorDBLiteMemoryBackend(GraphitiMemoryAdapter):
    """FalkorDBLite + Graphiti implementation of MemoryStorage protocol.

    This adapter uses Graphiti's temporal knowledge graph framework to store
    and retrieve agent memory in FalkorDBLite (embedded, file-backed).

    Multi-Tenancy:
    - Each user gets their own graph: user_memory_{user_id}
    - Each org gets their own graph: org_memory_{org_id}
    - Graphs are completely isolated from each other

    Example:
        ```python
        adapter = FalkorDBLiteMemoryBackend(
            db_path=".lineage_workspace/falkordb_memory.db"
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
        db_path: str = ".lineage_workspace/falkordb_memory.db",
        default_org_id: str = "default-org",
        default_user_id: str = "default-user",
    ):
        """Initialize FalkorDBLite memory backend.

        Args:
            db_path: Path to FalkorDBLite database file
            default_org_id: Default organization ID
            default_user_id: Default user ID

        Raises:
            ImportError: If redislite is not installed
        """
        super().__init__()

        self.db_path = db_path
        self.default_org_id = default_org_id
        self.default_user_id = default_user_id

        logger.info(
            f"Initializing FalkorDBLite memory backend at {db_path} "
            f"(org={default_org_id}, user={default_user_id})"
        )

    def _create_graphiti_client(self, graph_name: str) -> Graphiti:
        """Create Graphiti client for FalkorDBLite.

        Args:
            graph_name: Name of the graph to create/use

        Returns:
            Initialized Graphiti instance

        Raises:
            ImportError: If redislite or graphiti-core not installed
        """
        try:
            from redislite.falkordb_client import FalkorDB  # noqa: F401
        except ImportError as exc:
            raise ImportError(
                "redislite is required for FalkorDBLite. "
                "Install with: pip install redislite"
            ) from exc

        # Initialize Graphiti with FalkorDBLite
        # Note: Graphiti expects a file URI for embedded databases
        graphiti = Graphiti(
            uri=f"file://{self.db_path}",
            graph_name=graph_name,
            # FalkorDBLite doesn't need credentials
        )

        logger.debug(f"Created Graphiti client for graph: {graph_name}")
        return graphiti

