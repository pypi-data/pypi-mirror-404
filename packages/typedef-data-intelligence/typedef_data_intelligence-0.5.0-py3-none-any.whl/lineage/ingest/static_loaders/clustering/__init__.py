"""Join clustering module - portable clustering logic.

This module provides portable clustering functionality that works across
all graph backends (Kuzu, FalkorDB, Neo4j, PostgreSQL AGE).

Key components:
- algorithms: Pure Python clustering algorithms (Louvain, Greedy)
- enrichment: Model role classification and domain extraction
- summarizer: Cluster analysis and blueprint generation
- orchestrator: Main API coordinating the clustering pipeline

All Cypher queries are minimal (MATCH/RETURN only) to ensure compatibility.
Complex logic is implemented in Python for maximum portability.
"""

from lineage.ingest.static_loaders.clustering.orchestrator import ClusteringOrchestrator

__all__ = ["ClusteringOrchestrator"]
