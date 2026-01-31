"""Memory backend for persistent agent memory.

This module provides a protocol-based memory system for PydanticAI agents,
supporting both user-specific and organization-wide memory using temporal
knowledge graphs (via Graphiti + FalkorDB).

Key Components:
- MemoryStorage: Protocol defining the memory backend interface
- Episode: Represents a discrete memory unit (query, insight, pattern)
- MemoryResult: Search result with relevance and temporal context
- FalkorDBMemoryAdapter: Implementation using Graphiti + FalkorDB

Example Usage:
    ```python
    from lineage.backends.memory import create_memory_backend
    from lineage.backends.memory.models import Episode, EpisodeType

    # Create memory backend
    memory = create_memory_backend(config.memory)

    # Store user preference
    episode = Episode(
        name="chart_preference",
        content="User prefers bar charts for ARR visualizations",
        episode_type=EpisodeType.USER_PREFERENCE,
        source_description="Analyst chat session"
    )
    memory.store_user_memory(user_id="alice", episode=episode)

    # Search user memory
    results = memory.search_user_memory(user_id="alice", query="chart preferences")
    ```
"""

from lineage.backends.memory.protocol import MemoryStorage
from lineage.backends.memory.models import (
    Episode,
    EpisodeType,
    MemoryResult,
    UserPreference,
    DataPattern,
)

__all__ = [
    "MemoryStorage",
    "Episode",
    "EpisodeType",
    "MemoryResult",
    "UserPreference",
    "DataPattern",
]
