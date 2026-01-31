"""Clustering orchestration - coordinates the full clustering pipeline.

This module provides the main API for clustering. It coordinates:
1. Join graph extraction from semantic analysis
2. Optional model enrichment (role, domains, PII)
3. Clustering algorithm execution (Louvain or Greedy)
4. Cluster summarization and blueprint generation
5. Storage of results in graph database

The orchestrator is backend-agnostic and works with any LineageStorage implementation.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

import fenic as fc
import networkx as nx

from lineage.backends.lineage.protocol import LineageStorage
from lineage.ingest.static_loaders.clustering.algorithms import cluster_models
from lineage.ingest.static_loaders.clustering.enrichment import ModelEnricher
from lineage.ingest.static_loaders.clustering.summarizer import ClusterSummarizer

logger = logging.getLogger(__name__)


class ClusteringOrchestrator:
    """Orchestrates the complete clustering pipeline.

    This is the main entry point for clustering functionality. It coordinates
    all the steps from data extraction to storage, delegating to specialized
    components for each phase.

    Usage:
        session = create_session(default_model="google/gemini-2.5-flash-lite")
        orchestrator = ClusteringOrchestrator(storage)
        result = await orchestrator.cluster_and_analyze(
            session=session,
            min_weight=0.0,
            method="greedy",
            enrich_models=True,
        )
    """

    def __init__(self, storage: LineageStorage):
        """Initialize orchestrator with storage backend.

        Args:
            storage: LineageStorage instance for graph access
        """
        self.storage = storage

    async def cluster_and_analyze(
        self,
        session: fc.Session,
        min_weight: float = 0.0,
        method: str = "greedy",
        resolution: float = 1.0,
        enrich_models: bool = True,
    ) -> Dict[str, Any]:
        """Execute the complete clustering pipeline.

        This method orchestrates all phases of clustering:
        1. Extract join edges from graph
        2. Enrich models (if enabled)
        3. Build NetworkX graph
        4. Run clustering algorithm
        5. Generate summaries and blueprints
        6. Store results in graph

        Args:
            session: Fenic session for LLM operations (managed by integration layer)
            min_weight: Minimum edge weight to include in clustering
            method: Clustering algorithm - "greedy" or "louvain"
            resolution: Resolution parameter (placeholder for future Leiden support)
            enrich_models: Whether to run LLM enrichment for domains

        Returns:
            Dictionary with:
                - clusters: Dict[int, List[str]] - cluster assignments
                - summaries: List[ClusterSummaryDTO] - cluster analysis
                - blueprints: List[ClusterBlueprint] - schema design templates
                - enrichment: Dict[str, ModelEnrichmentData] - model metadata (if enabled)
        """
        logger.info("=" * 60)
        logger.info("Starting clustering pipeline")
        logger.info(f"  Method: {method}")
        logger.info(f"  Min weight: {min_weight}")
        logger.info(f"  Enrich models: {enrich_models}")
        logger.info("=" * 60)

        # Phase 1: Extract join edges from graph
        logger.info("\n[1/6] Extracting join edges...")
        join_edges = self.storage.get_join_edges()
        logger.info(f"  Found {len(join_edges)} total join edges")

        # Filter by minimum weight
        filtered = [e for e in join_edges if e["weight"] >= min_weight]
        logger.info(f"  Filtered to {len(filtered)} edges (min_weight={min_weight})")

        if not filtered:
            logger.warning("No join edges found after filtering - clustering may produce trivial results")

        # Phase 2: Get model list
        logger.info("\n[2/6] Loading models...")
        models = self.storage.get_all_models_with_analysis()
        model_ids = [m["model_id"] for m in models]
        logger.info(f"  Found {len(model_ids)} models with semantic analysis")

        if not model_ids:
            logger.error("No models found - cannot proceed with clustering")
            return {
                "clusters": {},
                "summaries": [],
                "blueprints": [],
                "enrichment": {},
            }

        # Phase 3: Build NetworkX graph
        logger.info("\n[3/6] Building graph...")
        G = nx.Graph()
        for model_id in model_ids:
            G.add_node(model_id)

        for edge in filtered:
            G.add_edge(edge["source"], edge["target"], weight=float(edge["weight"]))

        logger.info(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

        # Phase 4: Run clustering algorithm
        logger.info(f"\n[4/6] Running {method} clustering...")
        weighted_edges = [
            (edge["source"], edge["target"], float(edge["weight"])) for edge in filtered
        ]
        clusters = cluster_models(
            model_ids, weighted_edges, method=method, resolution=resolution
        )
        logger.info(f"  Found {len(clusters)} clusters")

        # Log cluster sizes
        cluster_sizes = sorted([len(members) for members in clusters.values()], reverse=True)
        if cluster_sizes:
            logger.info(f"  Cluster sizes: {cluster_sizes[:10]}{'...' if len(cluster_sizes) > 10 else ''}")

        # Phase 5: Enrich models (optional)
        enrichment = {}
        if enrich_models:
            logger.info("\n[5/6] Enriching models...")
            enricher = ModelEnricher(self.storage)
            enrichment = await enricher.enrich_all_models(session=session)

            # Add weighted degree to enrichment
            weighted_degree = dict(G.degree(weight="weight"))
            for model_id, data in enrichment.items():
                data.weighted_degree = weighted_degree.get(model_id, 0.0)

            logger.info(f"  Enriched {len(enrichment)} models")
        else:
            logger.info("\n[5/6] Skipping model enrichment (disabled)")

            # Create minimal enrichment data for summarization
            for model_id in model_ids:
                from lineage.backends.lineage.models.clustering import (
                    ModelEnrichmentData,
                )

                enrichment[model_id] = ModelEnrichmentData(
                    model_id=model_id,
                    role="unknown",
                    domains=[],
                    has_pii=False,
                    fact_count=0,
                    dimension_count=0,
                    weighted_degree=0.0,
                )

        # Phase 6: Generate summaries & blueprints
        logger.info("\n[6/6] Generating cluster analysis...")
        summarizer = ClusterSummarizer()
        summaries, blueprints = summarizer.generate_analysis(G, clusters, enrichment)
        logger.info(f"  Generated {len(summaries)} summaries and {len(blueprints)} blueprints")

        # Phase 7: Store in graph
        logger.info("\nStoring cluster analysis in graph...")
        try:
            self.storage.store_cluster_analysis(clusters, summaries, blueprints)
            logger.info("  ✅ Successfully stored cluster analysis")
        except NotImplementedError:
            logger.warning(
                "  ⚠️  store_cluster_analysis() not implemented in adapter - skipping storage"
            )
        except Exception as e:
            logger.error(f"  ❌ Failed to store cluster analysis: {e}")

        logger.info("\n" + "=" * 60)
        logger.info("Clustering pipeline complete!")
        logger.info("=" * 60)

        return {
            "clusters": clusters,
            "summaries": summaries,
            "blueprints": blueprints,
            "enrichment": enrichment,
        }


__all__ = ["ClusteringOrchestrator"]
