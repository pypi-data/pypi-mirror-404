"""Graph-based enrichment for deterministic analysis.

Provides a cached, fail-open client for querying column lineage features
and relation resolution hints from FalkorDB during analysis.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Optional, Set

from pydantic import BaseModel, Field

from lineage.backends.lineage.protocol import LineageStorage

logger = logging.getLogger(__name__)


class ColumnLineageFeatures(BaseModel):
    """Lineage-derived confidence features for a single column."""

    fan_in: int = 0
    max_depth: int = 0
    has_transformation: bool = False
    min_edge_confidence: str = "direct"
    upstream_parent_spread: int = 0
    leaf_columns: List[str] = Field(default_factory=list)


class RelationHint(BaseModel):
    """Canonical identity hint for a relation base/alias."""

    model_id: Optional[str] = None
    physical_fqn: Optional[str] = None
    is_source: bool = False


class EnrichmentResult(BaseModel):
    """Container for all graph-derived metadata for a single model analysis."""

    # Features for output columns, keyed by column_alias
    column_features: Dict[str, ColumnLineageFeatures] = Field(default_factory=dict)

    # Resolution hints for relations found in SQL, keyed by base/alias
    relation_hints: Dict[str, RelationHint] = Field(default_factory=dict)


class GraphEnricher:
    """Utility for fetching lineage features from the graph with fail-open behavior."""

    def __init__(
        self,
        storage: LineageStorage,
        timeout_seconds: float = 2.0,
        max_depth: int = 5,
    ):
        """Initialize the enricher.

        Args:
            storage: LineageStorage protocol instance (must support execute_raw_query)
            timeout_seconds: Max time to wait for a graph query before falling back
            max_depth: Max traversal depth for lineage features
        """
        self.storage = storage
        self.timeout_seconds = timeout_seconds
        self.max_depth = max_depth
        self._cache: Dict[str, EnrichmentResult] = {}

    async def enrich_model(
        self,
        model_id: str,
        relation_bases: Set[str],
        output_column_aliases: List[str],
    ) -> EnrichmentResult:
        """Fetch lineage features and relation hints for a model.

        This is the main entry point for the Fenic async UDF.

        Args:
            model_id: The unique_id of the model being analyzed
            relation_bases: Set of table names/aliases used in the model
            output_column_aliases: List of projected column names

        Returns:
            EnrichmentResult (empty on failure or timeout)
        """
        if model_id in self._cache:
            return self._cache[model_id]

        try:
            # Run in thread pool to avoid blocking the event loop
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self._fetch_enrichment_sync,
                    model_id,
                    relation_bases,
                    output_column_aliases,
                ),
                timeout=self.timeout_seconds,
            )
            self._cache[model_id] = result
            return result
        except asyncio.TimeoutError:
            logger.warning(f"Graph enrichment timed out for {model_id}")
            return EnrichmentResult()
        except Exception as e:
            logger.warning(f"Graph enrichment failed for {model_id}: {e}")
            return EnrichmentResult()

    def _fetch_enrichment_sync(
        self,
        model_id: str,
        relation_bases: Set[str],
        output_column_aliases: List[str],
    ) -> EnrichmentResult:
        """Synchronous implementation of enrichment fetching."""
        result = EnrichmentResult()

        # 1. Relation Hints
        if relation_bases:
            result.relation_hints = self._fetch_relation_hints(relation_bases)

        # 2. Column Features (for projected output columns)
        if model_id and output_column_aliases:
            result.column_features = self._fetch_column_features(
                model_id, output_column_aliases
            )

        return result

    def _fetch_relation_hints(self, bases: Set[str]) -> Dict[str, RelationHint]:
        """Fetch hints for relation bases."""
        hints: Dict[str, RelationHint] = {}
        if not bases:
            return hints

        # Search for models or sources by name or ID
        query = """
            UNWIND $bases AS base
            OPTIONAL MATCH (m:DbtModel) WHERE m.name = base OR m.id = base
            OPTIONAL MATCH (s:DbtSource) WHERE s.name = base OR s.id = base
            OPTIONAL MATCH (p) WHERE (p:PhysicalTable OR p:PhysicalView) AND p.fqn = base
            RETURN base, 
                   m.id AS model_id, 
                   s.id AS source_id, 
                   p.fqn AS physical_fqn
        """
        try:
            result = self.storage.execute_raw_query(query, params={"bases": list(bases)})
            for row in result.rows:
                base = row["base"]
                model_id = row.get("model_id")
                source_id = row.get("source_id")
                physical_fqn = row.get("physical_fqn")

                if model_id or source_id or physical_fqn:
                    hints[base] = RelationHint(
                        model_id=model_id or source_id,
                        physical_fqn=physical_fqn,
                        is_source=bool(source_id),
                    )
        except Exception as e:
            logger.debug(f"Relation hint query failed: {e}")

        return hints

    def _fetch_column_features(
        self, model_id: str, aliases: List[str]
    ) -> Dict[str, ColumnLineageFeatures]:
        """Fetch lineage features for columns."""
        features: Dict[str, ColumnLineageFeatures] = {}
        if not model_id or not aliases:
            return features

        # Query for multi-hop lineage
        # We use a single query with UNWIND to fetch all column features at once
        # DERIVES_FROM is from target to source in our schema
        query = f"""
            UNWIND $aliases AS alias
            MATCH (c:DbtColumn {{parent_id: $model_id, name: alias}})
            OPTIONAL MATCH p=(c)-[:DERIVES_FROM*1..{self.max_depth}]->(leaf:DbtColumn)
            WHERE NOT (leaf)-[:DERIVES_FROM]->()
            RETURN alias, 
                   COLLECT(nodes(p)) AS paths_nodes,
                   COLLECT(relationships(p)) AS paths_edges
        """
        try:
            result = self.storage.execute_raw_query(
                query, params={"model_id": model_id, "aliases": aliases}
            )
            for row in result.rows:
                alias = row["alias"]
                paths_nodes = row.get("paths_nodes", [])
                paths_edges = row.get("paths_edges", [])

                # If no paths found, skip (defaults will be used)
                if not paths_nodes:
                    continue

                feat = ColumnLineageFeatures()
                leaf_cols = set()
                parent_ids = set()
                max_depth = 0
                has_trans = False
                min_conf = "direct"

                # Process all paths for this column
                for path_nodes in paths_nodes:
                    if not path_nodes:
                        continue
                    
                    # Leaf is the last node in the path
                    leaf = path_nodes[-1]
                    leaf_cols.add(leaf.get("id", "unknown"))
                    if "parent_id" in leaf:
                        parent_ids.add(leaf["parent_id"])
                    
                    # Depth is number of edges (nodes - 1)
                    depth = len(path_nodes) - 1
                    max_depth = max(max_depth, depth)

                for path_edges in paths_edges:
                    for edge in path_edges:
                        if edge.get("transformation"):
                            has_trans = True
                        conf = edge.get("confidence", "direct").lower()
                        if conf == "inferred" or (conf == "direct" and min_conf == "direct"):
                            # Simple min logic: inferred < direct
                            if conf == "inferred":
                                min_conf = "inferred"

                feat.fan_in = len(leaf_cols)
                feat.max_depth = max_depth
                feat.has_transformation = has_trans
                feat.min_edge_confidence = min_conf
                feat.upstream_parent_spread = len(parent_ids)
                feat.leaf_columns = sorted(list(leaf_cols))
                
                features[alias] = feat

        except Exception as e:
            logger.debug(f"Column features query failed: {e}")

        return features
