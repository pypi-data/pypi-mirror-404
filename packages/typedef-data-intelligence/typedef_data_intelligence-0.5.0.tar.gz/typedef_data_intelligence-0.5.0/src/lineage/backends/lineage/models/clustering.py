"""Pydantic models for join clustering nodes and DTOs.

These models represent groups of models with similar join patterns:
- JoinCluster: Enhanced cluster node with business metadata (stored in graph)
- ModelEnrichmentData: Enrichment metadata for models (DTO, not stored)
- ClusterSummaryDTO: Cluster analysis results (DTO, not stored)
- ClusterBlueprint: Schema design template (DTO, not stored)
"""

from typing import Any, ClassVar, Optional

from pydantic import BaseModel, computed_field

from lineage.backends.lineage.models.base import BaseNode
from lineage.backends.types import NodeLabel


class JoinCluster(BaseNode):
    """Enhanced join cluster node with rich business metadata.

    Represents a group of models that frequently join together,
    discovered through join pattern analysis. Includes business metadata
    extracted from semantic analysis and clustering algorithm results.

    The ID is the cluster_id (typically an integer converted to string).
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.JOIN_CLUSTER

    # Core properties
    name: str  # Usually subject area name or "Cluster {cluster_id}"
    cluster_id: str  # Unique cluster identifier
    pattern: Optional[str] = None  # Description of the join pattern
    model_count: int = 0  # Number of models in this cluster

    # Business metadata (from semantic analysis)
    subject_area: Optional[str] = None  # Primary business domain name
    domains: list[str] = []  # All business domains in this cluster
    total_edge_weight: float = 0.0  # Sum of join edge weights

    # Role breakdown (from semantic analysis)
    fact_table_count: int = 0  # Number of fact tables (has aggregations)
    dimension_table_count: int = 0  # Number of dimension tables (no aggregations)
    mixed_table_count: int = 0  # Number of mixed tables (both fact and dimension characteristics)

    # PII & governance
    contains_pii: bool = False  # True if any table in cluster has PII
    pii_table_count: int = 0  # Number of tables with PII

    # Blueprint fields (schema design guidance)
    recommended_fact_table: Optional[str] = None  # Highest-degree fact table
    top_dimension_tables: list[str] = []  # Top dimensions ordered by connectivity

    @computed_field
    @property
    def id(self) -> str:
        """Cluster ID is the unique identifier."""
        return self.cluster_id


class ModelEnrichmentData(BaseModel):
    """Enrichment metadata for a single model (DTO - not stored in graph).

    This data is computed during clustering enrichment phase and used
    to generate cluster summaries and blueprints.
    """

    model_id: str
    role: str  # "fact", "dimension", or "mixed"
    domains: list[str] = []  # Business domain keywords extracted from intent
    has_pii: bool = False  # True if any column has PII
    fact_count: int = 0  # Number of BusinessMeasure nodes
    dimension_count: int = 0  # Number of BusinessDimension nodes
    weighted_degree: float = 0.0  # Weighted degree in join graph (computed during clustering)


class ClusterSummaryDTO(BaseModel):
    """Cluster analysis results (DTO - not stored in graph).

    Detailed analysis of a single cluster including role breakdown,
    domain analysis, PII detection, and top join edges.
    """

    cluster_id: int
    size: int  # Number of models in cluster
    tables: list[str]  # All model IDs in cluster
    fact_tables: list[str]  # Models with role='fact'
    dimension_tables: list[str]  # Models with role='dimension'
    mixed_tables: list[str]  # Models with role='mixed'
    has_pii_tables: list[str]  # Models with PII data
    domains: list[str]  # All unique business domains in cluster
    total_edge_weight: float  # Sum of edge weights in cluster subgraph
    top_edges: list[dict[str, Any]]  # Top 10 edges by weight


class ClusterBlueprint(BaseModel):
    """Schema design template for a cluster (DTO - not stored in graph).

    Provides recommendations for how to build a subject area or mart
    based on cluster analysis. Includes fact table selection and
    dimension ordering based on connectivity patterns.
    """

    cluster_id: int
    subject_area_name: str  # Primary domain or "cluster_{id}"
    fact_table: Optional[str] = None  # Recommended fact table (highest weighted-degree fact)
    dimension_tables: list[str] = []  # Ordered by weighted degree (most connected first)
    shared_domains: list[str] = []  # All business domains in cluster
    contains_pii: bool = False  # True if cluster contains PII
    notes: list[str] = []  # Auto-generated notes about cluster characteristics


__all__ = [
    "JoinCluster",
    "ModelEnrichmentData",
    "ClusterSummaryDTO",
    "ClusterBlueprint",
]
