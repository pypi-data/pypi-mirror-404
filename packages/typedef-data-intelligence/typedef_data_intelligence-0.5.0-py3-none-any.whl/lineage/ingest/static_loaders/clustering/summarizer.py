"""Cluster summarization and blueprint generation.

This module analyzes clustered models to generate:
1. Cluster summaries: Role breakdown, domain analysis, PII detection, top edges
2. Cluster blueprints: Schema design templates with fact/dimension recommendations

The logic is ported from the reference implementation (reference/backend/cluster_join_graph.py)
but implemented using NetworkX for portability.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Tuple

import networkx as nx

from lineage.backends.lineage.models.clustering import (
    ClusterBlueprint,
    ClusterSummaryDTO,
    ModelEnrichmentData,
)

logger = logging.getLogger(__name__)


class ClusterSummarizer:
    """Generates cluster summaries and blueprints from clustering results.

    This class analyzes the graph structure and enrichment data to produce:
    - Detailed cluster summaries (size, roles, domains, PII, top edges)
    - Schema design blueprints (fact selection, dimension ordering, layering)
    """

    def generate_analysis(
        self,
        graph: nx.Graph,
        clusters: Dict[int, List[str]],
        enrichment: Dict[str, ModelEnrichmentData],
    ) -> Tuple[List[ClusterSummaryDTO], List[ClusterBlueprint]]:
        """Generate cluster summaries and blueprints.

        This is the main entry point. It analyzes each cluster to produce
        both a detailed summary and a schema design blueprint.

        Args:
            graph: NetworkX graph with models as nodes and join edges
            clusters: Dictionary mapping cluster_id -> list of model IDs
            enrichment: Dictionary mapping model_id -> enrichment data

        Returns:
            Tuple of (summaries, blueprints) lists, one per cluster
        """
        logger.info(f"Generating analysis for {len(clusters)} clusters...")

        summaries = []
        blueprints = []

        for cluster_id, members in sorted(clusters.items()):
            # Create subgraph for this cluster
            subgraph = graph.subgraph(members)

            # Generate summary
            summary = self._generate_summary(
                cluster_id, members, subgraph, enrichment
            )
            summaries.append(summary)

            # Generate blueprint
            blueprint = self._generate_blueprint(
                cluster_id, members, subgraph, enrichment, summary
            )
            blueprints.append(blueprint)

        logger.info(f"Generated {len(summaries)} summaries and {len(blueprints)} blueprints")
        return summaries, blueprints

    def _generate_summary(
        self,
        cluster_id: int,
        members: List[str],
        subgraph: nx.Graph,
        enrichment: Dict[str, ModelEnrichmentData],
    ) -> ClusterSummaryDTO:
        """Generate detailed summary for a single cluster.

        Analyzes role breakdown, domain aggregation, PII detection,
        and identifies top join edges by weight.

        Args:
            cluster_id: Cluster identifier
            members: List of model IDs in cluster
            subgraph: NetworkX subgraph for this cluster
            enrichment: Model enrichment data

        Returns:
            ClusterSummaryDTO with detailed cluster analysis
        """
        # Role breakdown
        facts = [m for m in members if enrichment[m].role == "fact"]
        dims = [m for m in members if enrichment[m].role == "dimension"]
        mixed = [m for m in members if enrichment[m].role == "mixed"]

        # Domain aggregation (collect all unique domains)
        all_domains = []
        for model_id in members:
            all_domains.extend(enrichment[model_id].domains)
        shared_domains = sorted(set(all_domains))

        # PII detection
        has_pii_tables = [m for m in members if enrichment[m].has_pii]

        # Top edges by weight
        edges_with_weight = [
            {
                "table_a": u,
                "table_b": v,
                "weight": data.get("weight", 0.0),
            }
            for u, v, data in subgraph.edges(data=True)
        ]
        top_edges = sorted(
            edges_with_weight,
            key=lambda e: e["weight"],
            reverse=True,
        )[:10]  # Top 10 edges

        # Total edge weight
        total_weight = subgraph.size(weight="weight")

        return ClusterSummaryDTO(
            cluster_id=cluster_id,
            size=len(members),
            tables=sorted(members),
            fact_tables=sorted(facts),
            dimension_tables=sorted(dims),
            mixed_tables=sorted(mixed),
            has_pii_tables=sorted(has_pii_tables),
            domains=shared_domains,
            total_edge_weight=total_weight,
            top_edges=top_edges,
        )

    def _generate_blueprint(
        self,
        cluster_id: int,
        members: List[str],
        subgraph: nx.Graph,
        enrichment: Dict[str, ModelEnrichmentData],
        summary: ClusterSummaryDTO,
    ) -> ClusterBlueprint:
        """Generate schema design blueprint for a cluster.

        Implements layering logic from reference implementation:
        1. Fact table selection: Highest weighted-degree fact
        2. Dimension ordering: Sorted by weighted degree (connectivity)
        3. Subject area naming: Primary domain or generic fallback

        Args:
            cluster_id: Cluster identifier
            members: List of model IDs in cluster
            subgraph: NetworkX subgraph for this cluster
            enrichment: Model enrichment data
            summary: Cluster summary (for role breakdown)

        Returns:
            ClusterBlueprint with schema design recommendations
        """
        # Calculate weighted degree for all nodes in cluster
        weighted_degree = dict(subgraph.degree(weight="weight"))

        # Fact table selection (highest weighted-degree fact)
        # Fallback: mixed tables, then any table
        fact_candidates = summary.fact_tables or summary.mixed_tables or members

        if fact_candidates:
            fact_table = max(
                fact_candidates,
                key=lambda n: weighted_degree.get(n, 0.0),
            )
        else:
            fact_table = None

        # Dimension ordering (exclude fact table, sort by weighted degree)
        dimension_candidates = [m for m in members if m != fact_table]
        dimension_order = sorted(
            dimension_candidates,
            key=lambda n: weighted_degree.get(n, 0.0),
            reverse=True,  # Most connected first
        )

        # Subject area naming
        if summary.domains:
            subject_area_name = summary.domains[0]  # Primary domain
        else:
            subject_area_name = f"cluster_{cluster_id}"  # Generic fallback

        # Generate notes
        notes = []

        # Note about fact table candidates
        if summary.fact_tables or summary.mixed_tables:
            candidates = summary.fact_tables or summary.mixed_tables
            notes.append(f"Fact candidates: {', '.join(candidates)}")
        else:
            notes.append("No explicit fact table detected")

        # Note about PII
        if summary.has_pii_tables:
            notes.append(f"Includes PII ({len(summary.has_pii_tables)} tables)")
        else:
            notes.append("PII-free")

        return ClusterBlueprint(
            cluster_id=cluster_id,
            subject_area_name=subject_area_name,
            fact_table=fact_table,
            dimension_tables=dimension_order,
            shared_domains=summary.domains,
            contains_pii=bool(summary.has_pii_tables),
            notes=notes,
        )


__all__ = ["ClusterSummarizer"]
