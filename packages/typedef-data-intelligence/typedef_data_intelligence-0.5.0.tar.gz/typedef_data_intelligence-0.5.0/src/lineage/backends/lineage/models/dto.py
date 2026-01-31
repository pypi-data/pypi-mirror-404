"""Pydantic DTOs for lineage operations.

These models are data transfer objects used for queries and operations,
but are not stored in the graph as nodes.
"""

from pydantic import BaseModel


class JoinEdge(BaseModel):
    """Aggregated join relationship between two models.

    This DTO represents the aggregated join pattern between two models,
    computed by analyzing all JoinEdge nodes in semantic analysis.
    Used for clustering algorithms to determine which models frequently join.
    """

    source: str  # Source model ID
    target: str  # Target model ID
    count: int  # Number of times these models join together
    models: list[str]  # List of model IDs that contain this join
    join_types: list[str]  # Join types used (INNER, LEFT, etc.)
    equi_conditions: list[str]  # Equi-join conditions


__all__ = [
    "JoinEdge",
]
