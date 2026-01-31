"""Protocol for memory storage backends.

This module defines the MemoryStorage protocol that all memory backend
implementations must follow. It provides a unified interface for storing
and retrieving both user-specific and organization-wide memory.

The protocol supports:
- User-specific memory (preferences, queries, context)
- Organization-wide memory (data patterns, common joins, metrics)
- Hybrid search combining semantic similarity and graph traversal
- Temporal querying (future enhancement)

Implementations:
- FalkorDBMemoryAdapter: Uses Graphiti + FalkorDB for temporal knowledge graphs
- (Future) Neo4jMemoryAdapter, KuzuMemoryAdapter, etc.
"""

from __future__ import annotations

from typing import List, Optional, Protocol, runtime_checkable

from lineage.backends.memory.models import Episode, MemoryResult


@runtime_checkable
class MemoryStorage(Protocol):
    """Protocol for memory storage backends.

    This protocol defines the interface for storing and retrieving agent memory
    using temporal knowledge graphs. All implementations must support:
    - Multi-tenant user memory (isolated per user)
    - Shared organization memory (across all users in an org)
    - Hybrid search (semantic + graph + keyword)
    - Episode-based storage with temporal context

    Memory Isolation:
    - User memory is isolated per user_id (user_memory_{user_id} graph)
    - Organization memory is shared across users in the same org_id (org_memory_{org_id} graph)
    - Hybrid search can query both user and org memory simultaneously

    Example Usage:
        ```python
        # Store user preference
        episode = Episode(
            name="chart_preference",
            content="User prefers bar charts",
            episode_type=EpisodeType.USER_PREFERENCE,
            source_description="Chat session"
        )
        memory.store_user_memory(user_id="alice", episode=episode)

        # Search across user + org memory
        results = memory.search_all(
            user_id="alice",
            org_id="acme_corp",
            query="ARR metric definitions"
        )
        ```
    """

    # ---- User Memory Methods ----

    async def store_user_memory(self, user_id: str, episode: Episode) -> None:
        """Store an episode in user-specific memory.

        Creates or updates a temporal knowledge graph for the given user,
        adding the episode as a new node with temporal context.

        Args:
            user_id: Unique user identifier (e.g., "alice", "user_123")
            episode: Episode to store

        Example:
            ```python
            from lineage.backends.memory.models import Episode, EpisodeType

            episode = Episode(
                name="prefers_line_charts",
                content="User alice prefers line charts for time series",
                episode_type=EpisodeType.USER_PREFERENCE,
                source_description="Analyst chat on 2025-01-24"
            )
            memory.store_user_memory(user_id="alice", episode=episode)
            ```

        Note:
            - User memory is isolated per user_id
            - Each user has their own temporal knowledge graph
            - Episodes are timestamped for temporal reasoning
        """
        ...

    async def search_user_memory(
        self, user_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search user-specific memory using hybrid search.

        Performs semantic search + keyword matching + graph traversal
        to find relevant episodes in the user's memory.

        Args:
            user_id: User identifier
            query: Search query (natural language)
            limit: Maximum number of results to return

        Returns:
            List of MemoryResult objects, ranked by relevance

        Example:
            ```python
            results = memory.search_user_memory(
                user_id="alice",
                query="What are my chart preferences?"
            )
            for result in results:
                print(f"{result.rank}. {result.episode.name} (score: {result.score})")
                print(f"   Content: {result.episode.content}")
            ```

        Note:
            - Returns empty list if user has no memory
            - Results are ranked by relevance score (1.0 = perfect match)
            - Combines semantic embeddings, BM25 keyword matching, and graph distance
        """
        ...

    async def clear_user_memory(self, user_id: str) -> None:
        """Clear all memory for a specific user.

        WARNING: This permanently deletes all episodes in the user's memory graph.

        Args:
            user_id: User identifier

        Example:
            ```python
            # User requests to delete their memory
            memory.clear_user_memory(user_id="alice")
            ```

        Note:
            - This is a destructive operation and cannot be undone
            - Used for GDPR compliance / user privacy requests
            - Organization memory is not affected
        """
        ...

    # ---- Organization Memory Methods ----

    async def store_org_memory(self, org_id: str, episode: Episode) -> None:
        """Store an episode in organization-wide memory.

        Creates or updates a shared knowledge graph for the organization,
        accessible by all users in that org.

        Args:
            org_id: Organization identifier (e.g., "acme_corp", "org_456")
            episode: Episode to store

        Example:
            ```python
            from lineage.backends.memory.models import DataPattern, EpisodeType

            pattern = DataPattern(
                pattern_type="common_join",
                pattern_name="arr_to_customers",
                description="ARR fact commonly joined to customers dim on customer_id",
                models_involved=["fct_arr", "dim_customers"],
                discovered_by="analyst_agent"
            )
            memory.store_org_memory(
                org_id="acme_corp",
                episode=pattern.to_episode()
            )
            ```

        Note:
            - Organization memory is shared across all users in the org
            - Used for discovered data patterns, common joins, metric definitions
            - Episodes persist across user sessions
        """
        ...

    async def search_org_memory(
        self, org_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search organization-wide memory using hybrid search.

        Args:
            org_id: Organization identifier
            query: Search query (natural language)
            limit: Maximum number of results to return

        Returns:
            List of MemoryResult objects, ranked by relevance

        Example:
            ```python
            results = memory.search_org_memory(
                org_id="acme_corp",
                query="common joins between fact and dimension tables"
            )
            for result in results:
                print(f"{result.rank}. {result.episode.name}")
                print(f"   Models: {result.episode.metadata.get('models_involved')}")
            ```

        Note:
            - Returns patterns discovered by any user/agent in the organization
            - Useful for learning from collective agent experience
        """
        ...

    async def clear_org_memory(self, org_id: str) -> None:
        """Clear all organization memory.

        WARNING: This permanently deletes all episodes in the organization's memory graph.

        Args:
            org_id: Organization identifier

        Example:
            ```python
            # Reset organization memory (e.g., after major schema changes)
            memory.clear_org_memory(org_id="acme_corp")
            ```

        Note:
            - This affects all users in the organization
            - User-specific memory is not affected
            - Use with caution in production
        """
        ...

    # ---- Hybrid Search Methods ----

    async def search_all(
        self, user_id: str, org_id: str, query: str, limit: int = 10
    ) -> List[MemoryResult]:
        """Search both user and organization memory simultaneously.

        Performs hybrid search across both user-specific and organization-wide
        memory graphs, merging and ranking results by relevance.

        Args:
            user_id: User identifier
            org_id: Organization identifier
            query: Search query (natural language)
            limit: Maximum total results to return

        Returns:
            Merged list of MemoryResult objects from both user and org memory,
            ranked by relevance

        Example:
            ```python
            # Search everything the agent knows about ARR metrics
            results = memory.search_all(
                user_id="alice",
                org_id="acme_corp",
                query="ARR metric calculation and common dimensions"
            )

            # Results include:
            # - User preferences for ARR visualizations
            # - Organization patterns for ARR calculations
            # - Common joins involving ARR fact tables
            ```

        Note:
            - Results are merged and re-ranked by relevance
            - User memory results may be weighted higher for personalization
            - This is the recommended method for agent memory retrieval
        """
        ...

    # ---- Utility Methods ----

    async def get_stats(self, user_id: Optional[str] = None, org_id: Optional[str] = None) -> dict:
        """Get statistics about memory usage.

        Args:
            user_id: Optional user ID to get user-specific stats
            org_id: Optional org ID to get org-specific stats

        Returns:
            Dictionary with statistics:
            - episode_count: Total number of episodes
            - entity_count: Total number of entities (nodes)
            - relationship_count: Total number of relationships (edges)
            - last_update: Timestamp of last update

        Example:
            ```python
            # Get user stats
            user_stats = memory.get_stats(user_id="alice")
            print(f"Alice has {user_stats['episode_count']} memories")

            # Get org stats
            org_stats = memory.get_stats(org_id="acme_corp")
            print(f"Org has {org_stats['entity_count']} entities")
            ```
        """
        ...

    async def close(self) -> None:
        """Close connections and cleanup resources.

        Called on shutdown to properly close database connections
        and release resources.

        Example:
            ```python
            memory.close()
            ```
        """
        ...


__all__ = ["MemoryStorage"]
