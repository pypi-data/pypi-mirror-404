"""Backend-specific hints for agents to use correct SQL/Cypher dialects.

This module extracts hints directly from backend implementations using their
get_agent_hints() method. Backends are responsible for documenting their own
dialect-specific quirks and best practices.
"""


def get_backend_hints(data_backend=None, lineage_backend=None) -> str:
    """Get combined backend hints for both data and lineage backends.

    This function calls get_agent_hints() on backend objects if they implement it.
    Backends should provide comprehensive guides for AI agents in this method.

    Args:
        data_backend: Data warehouse backend (e.g., DuckDBBackend)
        lineage_backend: Graph/lineage backend (e.g., KuzuAdapter)

    Returns:
        Combined hints string to inject into system prompts
    """
    hints_parts = []

    # Add data backend hints
    if data_backend is not None and hasattr(data_backend, 'get_agent_hints'):
        try:
            hints = data_backend.get_agent_hints()
            if hints:
                hints_parts.append(hints)
        except Exception as e:
            # Log but don't fail if hints can't be retrieved
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to get hints from data backend: %s", e)

    # Add lineage backend hints
    if lineage_backend is not None and hasattr(lineage_backend, 'get_agent_hints'):
        try:
            hints = lineage_backend.get_agent_hints()
            if hints:
                hints_parts.append(hints)
        except Exception as e:
            # Log but don't fail if hints can't be retrieved
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Failed to get hints from lineage backend: %s", e)

    if not hints_parts:
        return ""

    return "\n\n---\n\n".join(hints_parts)
