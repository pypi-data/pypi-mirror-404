"""Abstract base class for Graphiti-based memory adapters.

This module provides common functionality for memory storage backends using
Graphiti's temporal knowledge graph framework. Concrete implementations must
provide driver-specific logic for graph creation and deletion.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from lineage.backends.memory.models import Episode, MemoryResult
from lineage.backends.memory.protocol import MemoryStorage

logger = logging.getLogger(__name__)

try:
    from graphiti_core import Graphiti
    from graphiti_core.edges import EntityEdge

    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    logger.warning(
        "graphiti-core not installed. Memory backend will not be available. "
        "Install with: pip install graphiti-core"
    )


class GraphitiMemoryAdapter(ABC, MemoryStorage):
    """Abstract base class for Graphiti-based memory storage.

    This class provides common functionality for all Graphiti backends:
    - Multi-tenant graph naming (user/org isolation)
    - Graphiti instance caching
    - Episode storage and hybrid search
    - Result conversion and ranking

    Concrete implementations must provide:
    - Driver creation: _create_driver(graph_name) -> Driver
    - Optional index building: _build_indices(graphiti) -> None
    - Graph deletion: clear_user_memory(), clear_org_memory()
    """

    def __init__(self):
        """Initialize base adapter."""
        if not GRAPHITI_AVAILABLE:
            raise ImportError(
                "graphiti-core is not installed. Install with: pip install graphiti-core"
            )

        # Cache Graphiti instances by graph name
        # Format: {graph_name: Graphiti instance}
        self._graphiti_cache: dict[str, Graphiti] = {}

    def _user_graph_name(self, user_id: str) -> str:
        """Generate graph name for user memory using SHA256 hash.

        Args:
            user_id: User identifier

        Returns:
            Graph name like "user_memory_abc12345def67890"
        """
        hash_digest = hashlib.sha256(user_id.encode("utf-8")).hexdigest()
        suffix = f"{hash_digest[:8]}{hash_digest[-8:]}"
        return f"user_memory_{suffix}"

    def _org_graph_name(self, org_id: str) -> str:
        """Generate graph name for organization memory using SHA256 hash.

        Args:
            org_id: Organization identifier

        Returns:
            Graph name like "org_memory_xyz98765ghi43210"
        """
        hash_digest = hashlib.sha256(org_id.encode("utf-8")).hexdigest()
        suffix = f"{hash_digest[:8]}{hash_digest[-8:]}"
        return f"org_memory_{suffix}"

    @abstractmethod
    def _create_driver(self, graph_name: str) -> Any:
        """Create a driver instance for the given graph.

        Concrete implementations must create the appropriate driver
        (FalkorDriver, KuzuDriver, etc.) with backend-specific configuration.

        Args:
            graph_name: Name of the graph to connect to

        Returns:
            Driver instance (FalkorDriver, KuzuDriver, etc.)
        """
        pass

    async def _build_indices(self, graphiti: Graphiti) -> None:
        """Build indices and constraints for the graph.

        Override this method if the backend requires index creation.
        Default implementation does nothing (suitable for embedded DBs).

        Args:
            graphiti: Graphiti instance
        """
        pass

    async def _get_or_create_graphiti(self, graph_name: str) -> Graphiti:
        """Get or create a Graphiti instance for the given graph name.

        Graphiti instances are cached to avoid repeated initialization.

        Args:
            graph_name: Name of the graph (e.g., "user_memory_abc12345")

        Returns:
            Graphiti instance connected to the specified graph
        """
        if graph_name in self._graphiti_cache:
            return self._graphiti_cache[graph_name]

        # Create driver using backend-specific implementation
        driver = self._create_driver(graph_name)

        # Create Graphiti instance
        graphiti = Graphiti(graph_driver=driver)

        # Build indices if needed (backend-specific)
        try:
            await self._build_indices(graphiti)
        except Exception as e:
            logger.debug(f"Index creation skipped for {graph_name}: {e}")

        # Cache it
        self._graphiti_cache[graph_name] = graphiti

        logger.info(f"Created Graphiti instance for graph: {graph_name}")
        return graphiti

    def _convert_search_results_to_memory_results(
        self, search_results: list[EntityEdge], scope: str = "org"
    ) -> List[MemoryResult]:
        """Convert Graphiti EntityEdge results to MemoryResult objects.

        Args:
            search_results: List of EntityEdge objects from Graphiti search
            scope: Either "user" or "org" to indicate the source of results

        Returns:
            List of MemoryResult objects with proper rank and scope
        """
        memory_results = []
        for rank, result in enumerate(search_results, start=1):
            memory_results.append(
                MemoryResult(
                    name=result.name,
                    fact=result.fact,
                    source_episodes=result.episodes,
                    rank=rank,
                    scope=scope,
                    additional_context={
                        "attributes": result.attributes if hasattr(result, "attributes") else {},
                        "expired_at": result.expired_at if hasattr(result, "expired_at") else None,
                        "valid_at": result.valid_at if hasattr(result, "valid_at") else None,
                        "invalid_at": result.invalid_at if hasattr(result, "invalid_at") else None,
                    },
                )
            )
        return memory_results

    # ========================================================================
    # User Memory Methods
    # ========================================================================

    async def store_user_memory(self, user_id: str, episode: Episode) -> None:
        """Store an episode in user-specific memory.

        Creates a new episode node in the user's temporal knowledge graph.
        Graphiti will automatically extract entities and create relationships.

        Args:
            user_id: User identifier
            episode: Episode to store
        """
        graph_name = self._user_graph_name(user_id)
        graphiti = await self._get_or_create_graphiti(graph_name)

        try:
            # Add episode to Graphiti
            # Graphiti will extract entities and create a temporal graph
            # Note: add_episode may be sync or async - we handle both cases
            result = graphiti.add_episode(
                name=episode.name,
                episode_body=episode.content,
                source_description=episode.source_description,
                reference_time=episode.timestamp,
            )
            # If it's a coroutine, await it; otherwise it's sync and already done
            if asyncio.iscoroutine(result):
                await result

            logger.debug(
                f"Stored user memory: user={user_id}, episode={episode.name}, "
                f"type={episode.episode_type.value}"
            )
        except Exception as e:
            logger.error(
                f"Failed to store user memory: user={user_id}, episode={episode.name}: {e}",
                exc_info=True,
            )
            # Don't raise - memory storage failures shouldn't break the request

    async def search_user_memory(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search user-specific memory using hybrid search.

        Args:
            user_id: User identifier
            query: Search query (natural language)
            limit: Maximum number of results

        Returns:
            List of MemoryResult objects ranked by relevance
        """
        graph_name = self._user_graph_name(user_id)
        graphiti = await self._get_or_create_graphiti(graph_name)

        # Search using Graphiti's hybrid search
        # This combines semantic embeddings, BM25, and graph traversal
        search_results: list[EntityEdge] = await graphiti.search(
            query=query,
            num_results=limit,
        )

        # Convert to MemoryResult objects with scope="user"
        memory_results = self._convert_search_results_to_memory_results(
            search_results, scope="user"
        )

        logger.debug(
            f"User memory search: user={user_id}, query='{query}', "
            f"results={len(memory_results)}"
        )
        return memory_results

    @abstractmethod
    async def clear_user_memory(self, user_id: str) -> None:
        """Clear all memory for a specific user.

        WARNING: This permanently deletes the user's memory graph.

        Concrete implementations must provide backend-specific deletion logic.

        Args:
            user_id: User identifier
        """
        pass

    # ========================================================================
    # Organization Memory Methods
    # ========================================================================

    async def store_org_memory(self, org_id: str, episode: Episode) -> None:
        """Store an episode in organization-wide memory.

        Creates a new episode node in the organization's temporal knowledge graph,
        accessible by all users in that organization.

        Args:
            org_id: Organization identifier
            episode: Episode to store
        """
        graph_name = self._org_graph_name(org_id)
        graphiti = await self._get_or_create_graphiti(graph_name)

        # Prepare episode body with metadata so Graphiti can retain structured context
        metadata_payload = {"episode_type": episode.episode_type.value}
        if episode.metadata:
            metadata_payload.update(episode.metadata)

        episode_body = episode.content
        if metadata_payload:
            metadata_str = json.dumps(metadata_payload, indent=2, default=str)
            episode_body = f"{episode_body}\n\nMetadata:\n{metadata_str}"

        # Graphiti only accepts limited source enums ("message", "text", "json")
        # so we treat all episodes as textual messages and embed the true type in metadata.
        try:
            result = graphiti.add_episode(
                name=episode.name,
                episode_body=episode_body,
                source="message",
                source_description=episode.source_description,
                reference_time=episode.timestamp,
                update_communities=True,
            )
            # If it's a coroutine, await it; otherwise it's sync and already done
            if asyncio.iscoroutine(result):
                await result

            logger.debug(
                f"Stored org memory: org={org_id}, episode={episode.name}, "
                f"type={episode.episode_type.value}"
            )
        except Exception as e:
            logger.error(
                f"Failed to store org memory: org={org_id}, episode={episode.name}: {e}",
                exc_info=True,
            )
            # Don't raise - memory storage failures shouldn't break the request

    async def search_org_memory(
        self, org_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search organization-wide memory using hybrid search.

        Args:
            org_id: Organization identifier
            query: Search query (natural language)
            limit: Maximum number of results

        Returns:
            List of MemoryResult objects ranked by relevance
        """
        graph_name = self._org_graph_name(org_id)
        graphiti = await self._get_or_create_graphiti(graph_name)

        # Search using Graphiti's hybrid search
        search_results = await graphiti.search(
            query=query,
            num_results=limit,
        )

        # Convert to MemoryResult objects with scope="org"
        memory_results = self._convert_search_results_to_memory_results(
            search_results, scope="org"
        )

        return memory_results

    @abstractmethod
    async def clear_org_memory(self, org_id: str) -> None:
        """Clear all organization memory.

        WARNING: This permanently deletes the organization's memory graph.

        Concrete implementations must provide backend-specific deletion logic.

        Args:
            org_id: Organization identifier
        """
        pass

    # ========================================================================
    # Hybrid Search Methods
    # ========================================================================

    async def search_all(
        self, user_id: str, org_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search both user and organization memory simultaneously.

        Performs hybrid search across both graphs and merges results.

        Args:
            user_id: User identifier
            org_id: Organization identifier
            query: Search query (natural language)
            limit: Maximum total results to return

        Returns:
            Merged list of MemoryResult objects ranked by relevance
        """
        # Search both user and org memory
        user_results_task = asyncio.create_task(
            self.search_user_memory(user_id, query, limit=limit)
        )
        org_results_task = asyncio.create_task(self.search_org_memory(org_id, query, limit=limit))
        user_results, org_results = await asyncio.gather(user_results_task, org_results_task)

        # Merge and re-rank results
        # Combine results and sort by rank
        all_results = user_results + org_results
        all_results.sort(key=lambda r: r.rank, reverse=True)

        # Limit to requested number
        merged_results = all_results[:limit]

        # Update ranks
        for rank, result in enumerate(merged_results, start=1):
            result.rank = rank

        logger.debug(
            f"Hybrid search: user={user_id}, org={org_id}, query='{query}', "
            f"user_results={len(user_results)}, org_results={len(org_results)}, "
            f"merged={len(merged_results)}"
        )
        return merged_results

    # ========================================================================
    # Utility Methods
    # ========================================================================

    async def get_stats(
        self, user_id: Optional[str] = None, org_id: Optional[str] = None
    ) -> dict:
        """Get statistics about memory usage.

        Args:
            user_id: Optional user ID for user-specific stats
            org_id: Optional org ID for org-specific stats

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_graphs": len(self._graphiti_cache),
            "user_graphs": [],
            "org_graphs": [],
        }

        # Get stats for specific user or org
        if user_id:
            graph_name = self._user_graph_name(user_id)
            if graph_name in self._graphiti_cache:
                stats["user_memory"] = {
                    "graph_name": graph_name,
                    "exists": True,
                }
            else:
                stats["user_memory"] = {"exists": False}

        if org_id:
            graph_name = self._org_graph_name(org_id)
            if graph_name in self._graphiti_cache:
                stats["org_memory"] = {
                    "graph_name": graph_name,
                    "exists": True,
                }
            else:
                stats["org_memory"] = {"exists": False}

        return stats

    async def close(self) -> None:
        """Close all Graphiti connections and cleanup resources."""
        logger.info(f"Closing {len(self._graphiti_cache)} Graphiti connections...")

        for graph_name, graphiti in self._graphiti_cache.items():
            try:
                graphiti.close()
                logger.debug(f"Closed Graphiti connection: {graph_name}")
            except Exception as e:
                logger.error(f"Error closing Graphiti connection {graph_name}: {e}")

        self._graphiti_cache.clear()
        logger.info("Graphiti memory adapter closed")


__all__ = ["GraphitiMemoryAdapter"]
