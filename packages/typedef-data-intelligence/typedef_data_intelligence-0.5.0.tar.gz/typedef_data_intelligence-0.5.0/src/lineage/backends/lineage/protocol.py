"""Protocol for lineage storage backends.

This module defines the LineageStorage protocol interface that all backend
implementations must follow. It uses a minimal, generic API based on two
core operations: upsert_node() and create_edge().
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)

from pydantic import BaseModel, Field, model_validator

from lineage.backends.lineage.models.base import BaseNode, GraphEdge, NodeIdentifier
from lineage.backends.lineage.models.clustering import (
    ClusterBlueprint,
    ClusterSummaryDTO,
)
from lineage.backends.lineage.models.dto import JoinEdge

# Type alias for graph schema format to ensure consistency across all implementations
# - "summary": Minimal schema for system prompt injection (~1,700 tokens). Core nodes only with key properties.
# - "compact": Complete schema in natural language (~3-4k tokens). All nodes with all properties and types.
# - "structured": Full JSON schema (~12k tokens). Use when you need programmatic access.
GraphSchemaFormat = Literal["summary", "compact", "structured"]

# ---- Data Classes for OpenLineage and Clustering ----

LineageDirection = Literal["upstream", "downstream", "both"]
@dataclass
class JobNode:
    """OpenLineage job node."""
    id: str
    name: str
    namespace: str
    job_type: str
    metadata: Dict[str, Any]


@dataclass
class DatasetNode:
    """OpenLineage dataset node."""
    id: str
    name: str
    namespace: str
    dataset_type: str
    metadata: Dict[str, Any]


@dataclass
class RunNode:
    """OpenLineage run node."""
    run_id: str
    job_id: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration_ms: Optional[int]
    error_info: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]


@dataclass
class LineageEdge:
    """Generic lineage edge."""
    edge_type: str
    from_node: str
    to_node: str
    properties: Dict[str, Any]


@dataclass
class ClusterInfo:
    """Join cluster information."""
    cluster_id: int
    member_count: int
    members: List[str]


# ---- Lightweight Lineage Result Types (Token-Efficient) ----


class SemanticSummary(BaseModel):
    """Brief semantic summary for lineage overview (token-efficient).

    Contains only the essential semantic information needed for at-a-glance
    understanding in lineage views. For full semantic details, use get_model_details.
    """

    grain_human: Optional[str] = None
    intent: Optional[str] = None
    analysis_summary: Optional[str] = None
    has_aggregations: bool = False
    has_window_functions: bool = False


class LineageOverviewNode(BaseModel):
    """Lightweight node for lineage overview (no SQL content).

    Contains only core identifiers and brief semantic summary.
    Use get_model_details() for full model information including SQL.
    """

    model_config = {"extra": "forbid"}  # Strict - no extra fields allowed

    type: str  # DbtModel, PhysicalTable, PhysicalView, etc.
    id: str
    name: str
    # Fully qualified name for physical nodes (database.schema.table). Optional for logical nodes.
    # Note: Keep as explicit field so TUI can display it; extra fields are forbidden.
    fqn: Optional[str] = None
    materialization: Optional[str] = None
    # Brief semantic summary (if InferredSemanticModel exists)
    semantic_summary: Optional[SemanticSummary] = None


class LineageRelationship(BaseModel):
    """Relationship between nodes in lineage graph."""

    from_id: str
    to_id: str
    edge_type: str  # DEPENDS_ON, BUILDS, etc.


class ModelMaterialization(BaseModel):
    """Details for a specific physical materialization of a logical model."""

    type: str  # PhysicalTable, PhysicalView, etc.
    fqn: str  # Fully qualified name (database.schema.table)
    database: Optional[str] = None
    schema_name: Optional[str] = None
    relation_name: str
    warehouse_type: Optional[str] = None  # snowflake, bigquery, duckdb, etc.
    environment: str  # prod, dev, staging, etc.
    materialization_strategy: Optional[str] = None
    updated_at: Optional[str] = None


class ModelMaterializationsResult(BaseModel):
    """Result from get_model_materializations tool."""

    tool_name: str = "get_model_materializations"
    model_id: str
    materializations: List[ModelMaterialization] = Field(default_factory=list)


class ModelDetailsResult(BaseModel):
    """Detailed model information with optional includes.

    Replaces get_model_semantics and provides granular control over detail level.
    Use after get_relation_lineage to deep-dive into specific models.
    """

    tool_name: str = "get_model_details"
    model_id: str
    model_name: str
    materialization: Optional[str] = None
    description: Optional[str] = None
    unique_id: Optional[str] = None
    original_path: Optional[str] = None

    # Optional: SQL content (include_sql=True)
    raw_sql: Optional[str] = None  # Original SQL from .sql file (with Jinja)
    # Compiled SQL is not included here because it is environment-specific.
    canonical_sql: Optional[str] = None  # Environment-agnostic SQL (replaces compiled_sql, which was environment-specific)

    # Optional: Full semantic analysis (include_semantics=True)
    grain: Optional[str] = None
    intent: Optional[str] = None
    analysis_summary: Optional[str] = None
    has_aggregations: Optional[bool] = None
    has_window_functions: Optional[bool] = None
    measures: Optional[List[Dict[str, Any]]] = None
    dimensions: Optional[List[Dict[str, Any]]] = None
    facts: Optional[List[Dict[str, Any]]] = None

    # Optional: Column information (include_columns=True)
    columns: Optional[List[Dict[str, Any]]] = None

    # Optional: Macro dependencies (include_macros=True)
    macros: Optional[List[Dict[str, Any]]] = None


# ---- LineageStorage Protocol ----


@runtime_checkable
class LineageStorage(Protocol):
    """Protocol for lineage graph storage backends.

    This protocol defines a minimal, generic API for storing and querying lineage graphs.
    All operations are based on two core methods:
    - upsert_node(): Create or update any node type
    - create_edge(): Create any relationship type

    Backends implement these two methods plus query/clustering utilities.
    """

    # ---- Core Generic Methods (required) ----

    def upsert_node(self, node: BaseNode) -> None:
        """Upsert a Pydantic BaseNode model into the graph.

        Extracts the node label, ID, and properties directly from the model:
        - node.node_label (class attribute) → NodeLabel
        - node.id (computed property) → unique ID
        - node.model_dump(exclude={'id'}) → all properties

        Args:
            node: Pydantic BaseNode with node_label and computed id

        Example:
            ```python
            # Create a native semantic model
            model = NativeSemanticModel(
                name="sv_arr_reporting",
                database="DEMO_DB",
                schema_name="MARTS",
                provider="snowflake",
                measures=[...],
                dimensions=[...]
            )

            # Upsert - no need to specify label or ID!
            storage.upsert_node(model)
            ```
        """
        ...

    def create_edge(
        self,
        from_node: Union[BaseNode, NodeIdentifier],
        to_node: Union[BaseNode, NodeIdentifier],
        edge: GraphEdge,
    ) -> None:
        """Create an edge between two nodes.

        Accepts either full BaseNode objects or lightweight NodeIdentifier objects.
        The edge object encodes its own edge_type and validates node type compatibility.

        Extracts IDs and labels from nodes/identifiers:
        - BaseNode: uses node.id and node.node_label
        - NodeIdentifier: uses identifier.id and identifier.node_label

        Edge properties are extracted from edge.model_dump().

        Args:
            from_node: Source node or identifier
            to_node: Target node or identifier
            edge: GraphEdge with type validation and properties

        Example:
            ```python
            from lineage.models import (
                DbtModel, NodeIdentifier, DependsOn,
                NativeSemanticModel, NativeMeasure, HasMeasure
            )

            # With full nodes (when you have them)
            model = NativeSemanticModel(name="sv_test", ...)
            measure = NativeMeasure(name="total_arr", ...)
            edge = HasMeasure()
            storage.create_edge(model, measure, edge)

            # With identifiers (when you only have IDs)
            from_id = NodeIdentifier(id="model.x", node_label=NodeLabel.DBT_MODEL)
            to_id = NodeIdentifier(id="model.y", node_label=NodeLabel.DBT_MODEL)
            edge = DependsOn(type="model", direct=True)
            storage.create_edge(from_id, to_id, edge)
            ```
        """
        ...

    def recreate_schema(self) -> None:
        """Drop and recreate the graph and all labels."""
        ...

    def ensure_schema(self) -> None:
        """Ensure schema exists (create indices if missing).

        Unlike recreate_schema(), this is idempotent and preserves existing data.
        Safe to call on every sync.
        """
        ...

    def bulk_load(
        self,
        nodes: List[BaseNode],
        edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> None:
        """Load nodes and edges into storage.

        Adapters can implement this either:
        - Optimized: Group by type, export to format (Parquet/CSV/etc), use backend's bulk loader
        - Simple: Loop over nodes/edges calling upsert_node() and create_edge()

        Args:
            nodes: All nodes to load (flat list of Pydantic BaseNode objects)
            edges: All edges to load (tuples of from_node, to_node, edge)
            progress_callback: Optional callback for progress updates.
                Signature: (current: int, total: int, message: str) -> None

        Example - Optimized (KùzuDB):
            ```python
            def bulk_load(self, nodes, edges):
                # Group nodes/edges by type
                # Export to Parquet
                # Use COPY FROM command
                pass
            ```

        Example - Simple (fallback):
            ```python
            def bulk_load(self, nodes, edges, progress_callback=None):
                total = len(nodes) + len(edges)
                for i, node in enumerate(nodes):
                    self.upsert_node(node)
                    if progress_callback and (i + 1) % 500 == 0:
                        progress_callback(i + 1, total, f"Loaded {i + 1}/{len(nodes)} nodes")
                for i, (from_node, to_node, edge) in enumerate(edges):
                    self.create_edge(from_node, to_node, edge)
                    if progress_callback and (i + 1) % 500 == 0:
                        progress_callback(len(nodes) + i + 1, total, f"Loaded {i + 1}/{len(edges)} edges")
            ```

        Note:
            All adapters MUST implement this method. There is no feature detection -
            adapters choose whether to optimize or use simple one-by-one inserts.
        """
        ...

    def delete_model_cascade(self, model_id: str, preserve_model: bool = False) -> int:
        """Delete a DbtModel and all associated child nodes in a cascade operation.

        This operation attempts to delete all nodes and relationships associated with
        a dbt model, including:
        - DbtModel node (unless preserve_model=True)
        - DbtColumn nodes (children via MATERIALIZES relationship)
        - PhysicalTable/View/Column nodes (via BUILDS relationship)
        - InferredSemanticModel and all semantic child nodes
        - TableProfile and ColumnProfile nodes
        - All edges involving these nodes

        Args:
            model_id: dbt unique_id of the resource to delete (e.g., "model.project.model_name").
                Must be a valid dbt unique_id format (model.*, source.*, seed.*, etc.).
            preserve_model: If True, delete all child nodes and edges but keep the DbtModel
                node itself. Useful for incremental updates where we want to clear children
                before re-loading them with updated data.

        Returns:
            Number of nodes deleted (useful for logging/metrics). Returns 0 if model
            doesn't exist.

        Raises:
            ValueError: If model_id is invalid or empty, or if storage is read-only.
            Exception: Backend-specific exceptions may be raised if deletion fails
                (e.g., database connection errors, query execution failures). These
                are not wrapped - callers should handle database-specific exceptions.

        Notes:
            - This operation should be atomic where supported by the backend.
            - Implementations should use DETACH DELETE to clean up relationships.
            - If the model doesn't exist, this should be a no-op (not an error).
            - Performance: For bulk deletions, consider calling this in parallel
              or implementing a backend-specific batch deletion method.

        Example:
            ```python
            # Full cascade delete (model removal)
            deleted_count = storage.delete_model_cascade("model.demo.orders")
            logger.info(f"Deleted {deleted_count} nodes")

            # Preserve model for incremental update (clear children only)
            deleted_count = storage.delete_model_cascade("model.demo.orders", preserve_model=True)
            logger.info(f"Cleared {deleted_count} child nodes, model preserved")
            ```
        """
        ...

    # ---- Query Methods (required) ----

    def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> RawLineageQueryResult:
        """Execute a raw backend Cypher query and return results.

        Args:
            query: Query string in the backend's native language
            params: Optional dictionary of parameters to bind to the query
        Returns:
            RawLineageQueryResult with untyped dict rows that can be converted
            to Pydantic models using convert()

        Example:
            # Execute query
            raw = storage.execute_raw_query("MATCH (m:DbtModel) RETURN m.name, m.schema")

            # Parameterized query (recommended for user input)
            raw = storage.execute_raw_query(
                "MATCH (m:DbtModel {id: $model_id}) RETURN m.name",
                params={"model_id": "model.demo_finance.fct_revenue"}
            )

            # Access raw dicts
            for row in raw.rows:
                print(row["name"])

            # Or convert to typed models
            result = convert(raw, ModelOverview)
            for model in result.nodes:
                print(model.name)  # Type-safe!
        """
        ...

    def set_active_graph(self, graph_name: str, ensure_schema: bool = True) -> None:
        """Switch to a different graph within the backend instance.

        Args:
            graph_name: Name of the graph to switch to
            ensure_schema: If True and not read_only, ensure indexes exist on the new graph
        """
        ...

    def list_graphs(self) -> list[str]:
        """List all graphs in the backend instance.

        Returns:
            List of graph names in the database
        """
        ...

    def close(self) -> None:
        """Close backend connections and cleanup resources."""
        ...

    def get_graph_schema(self, format: GraphSchemaFormat = "summary") -> str | Dict[str, Any]:
        """Get the lineage graph schema in the specified format.

        Args:
            format: Output format:
                - "summary" (default): Minimal natural language schema for system prompts (~1,700 tokens).
                  Shows core nodes with key properties, non-core nodes with descriptions only.
                - "compact": Complete natural language schema (~3-4k tokens). All nodes with all
                  properties and types. Use when you need exact property names for Cypher queries.
                - "structured": Full JSON schema (~12k tokens). Use for programmatic access.

        Returns:
            summary/compact: Markdown-formatted schema string
            structured: Dictionary with node_tables and relationship_tables

        Example:
            # Get minimal summary (default, for system prompts)
            summary = storage.get_graph_schema()

            # Get complete schema with all properties
            compact = storage.get_graph_schema(format="compact")

            # Get full JSON schema for programmatic access
            schema = storage.get_graph_schema(format="structured")
            print(schema["node_tables"]["DbtModel"]["columns"])
        """
        ...

    def get_agent_hints(self) -> str:
        """Get backend-specific Cypher query hints for AI agents.

        Returns:
            String containing dialect-specific guidance for writing Cypher queries,
            including limitations, best practices, and syntax variations.

        Example:
            hints = storage.get_agent_hints()
            # Returns Kùzu-specific hints: "NO GROUP BY clause supported..."
        """
        ...

    def get_relation_lineage(
        self,
        identifier: str,
        node_type: Literal["physical", "logical"],
        direction: LineageDirection = "both",
        depth: int = 3,
        include_physical: bool = True,
    ) -> RelationLineageResult:
        """Get lineage for a table/view/model (always crosses logical ↔ physical boundaries).

        For physical nodes: Finds DbtModel that builds it, traverses DEPENDS_ON, gets physical outputs
        For logical nodes: Traverses DEPENDS_ON, gets physical outputs via BUILDS

        Args:
            identifier: PhysicalTable FQN (e.g., 'db.schema.table') or DbtModel ID (e.g., 'model.project.name')
            node_type: "physical" (start at PhysicalTable) or "logical" (start at DbtModel)
            direction: Which direction to traverse - "upstream", "downstream", or "both"
            depth: Maximum traversal depth
            include_physical: Whether to include physical tables in results
            depth: Maximum traversal depth through DEPENDS_ON relationships

        Returns:
            RelationLineageResult with typed, flattened, deduplicated lineage nodes
        """
        ...

    def get_column_lineage(
        self,
        identifier: str,
        node_type: Literal["physical", "logical"],
        direction: str = "upstream",
        depth: int = 10,
    ) -> ColumnLineageResult:
        """Get lineage for a column (traces DERIVES_FROM relationships).

        Args:
            identifier: PhysicalColumn FQN (e.g., 'db.schema.table.column') or DbtColumn ID
            node_type: "physical" or "logical"
            direction: "upstream" (trace source) or "downstream" (trace usage)
            depth: Maximum traversal depth

        Returns:
            ColumnLineageResult with typed, flattened column lineage nodes
        """
        ...

    def get_model_details(
        self,
        model_id: str,
        include_sql: bool = False,
        include_semantics: bool = False,
        include_columns: bool = False,
        include_macros: bool = False,
    ) -> ModelDetailsResult:
        """Get detailed model information with optional includes.

        Use after get_relation_lineage to deep-dive into specific models.
        Only includes requested data to minimize token usage.

        Args:
            model_id: DbtModel ID (e.g., "model.project.model_name")
            include_sql: Include raw_sql and canonical_sql (token-heavy, use sparingly)
            include_semantics: Include full semantic analysis (grain, measures, dimensions, facts)
            include_columns: Include DbtColumn information via MATERIALIZES relationship
            include_macros: Include DbtMacro dependencies via USES_MACRO relationship

        Returns:
            ModelDetailsResult with requested detail level

        Example:
            # Basic info only (~200 tokens)
            details = storage.get_model_details("model.demo.orders")

            # With SQL for code review (~2k tokens)
            details = storage.get_model_details("model.demo.orders", include_sql=True)

            # Full semantic analysis (~1k tokens)
            details = storage.get_model_details("model.demo.orders", include_semantics=True)

            # Everything (~3k tokens)
            details = storage.get_model_details(
                "model.demo.orders",
                include_sql=True,
                include_semantics=True,
                include_columns=True,
                include_macros=True,
            )
        """
        ...

    def search_nodes(self, node_label: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search nodes using backend-native full-text index (or fallback).

        Args:
            node_label: Graph node label/type to search (e.g., "DbtModel")
            query: Search term (backend-specific syntax supported)
            limit: Maximum results to return

        Returns:
            List of rows with "node" and optional "score" fields.
        """
        ...

    def find_model_for_physical_table(self, relation_name: str) -> Optional[str]:
        """Find a model by its relation_name (fully qualified table name).

        This is more reliable than matching by database/schema/table components
        because relation_name is the actual table name used in the warehouse.

        Args:
            relation_name: Fully qualified relation name (e.g., "database.schema.table")

        Returns:
            Model ID if found, None otherwise

        Note:
            Should use case-insensitive matching for Snowflake compatibility.
        """
        ...

    def get_unique_database_schema_pairs(self) -> List[tuple[str, str]]:
        """Get unique (database, schema) pairs from loaded dbt models.

        This is used to discover all database/schema combinations present
        in the loaded dbt project, enabling iteration over all relevant
        schemas when loading semantic views or querying data.

        Returns:
            List of (database_name, schema_name) tuples from all DbtModel nodes,
            ordered by database then schema. Empty list if no models loaded.

        Example:
            pairs = storage.get_unique_database_schema_pairs()
            # [("DEMO_DB", "RAW"), ("DEMO_DB", "STAGING"), ("DEMO_DB", "MARTS")]

            for database, schema in pairs:
                load_semantic_views(database, schema)
        """
        ...

    # ---- Join Graph Clustering (required) ----

    def compute_join_graph(self) -> List[JoinEdge]:
        """Compute join graph from semantic analysis join edges.

        This method aggregates JoinEdge nodes from semantic analysis
        into a unified join graph showing which models commonly join together.

        Returns:
            List of JoinEdge objects with aggregated join information
        """
        ...

    def cluster_join_graph(self, min_count: int = 1) -> Dict[int, List[str]]:
        """Cluster the join graph using community detection.

        Uses the Louvain algorithm to find communities of models that
        frequently join together.

        Args:
            min_count: Minimum join count to include an edge (default: 1)

        Returns:
            Dict mapping cluster_id to list of model IDs in that cluster
        """
        ...

    def get_join_edges(
        self,
        min_confidence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch aggregated join edge records from JoinEdge nodes.

        Args:
            min_confidence: Optional confidence threshold ("low", "medium", "high")

        Returns:
            List of dictionaries with keys: source, target, weight, models,
            join_types, equi_conditions, scopes, confidences.
        """
        ...

    def store_clusters(self, clusters: Dict[int, List[str]]) -> None:
        """Store join clusters in the graph.

        Args:
            clusters: Dict mapping cluster_id to list of model IDs
        """
        ...

    def get_clusters(self) -> List[ClusterInfo]:
        """Get all join clusters.

        Returns:
            List of ClusterInfo objects with cluster metadata
        """
        ...

    # ---- Clustering Enrichment (required for enhanced clustering) ----

    def get_model_business_measure_count(self, model_id: str) -> int:
        """Count InferredMeasure nodes for a model.

        Args:
            model_id: Model identifier

        Returns:
            Number of InferredMeasure nodes linked to this model via InferredSemanticModel
        """
        ...

    def get_model_business_dimension_count(self, model_id: str) -> int:
        """Count InferredDimension nodes for a model.

        Args:
            model_id: Model identifier

        Returns:
            Number of InferredDimension nodes linked to this model via InferredSemanticModel
        """
        ...

    def model_has_pii(self, model_id: str) -> bool:
        """Check if any InferredDimension has is_pii=true.

        Args:
            model_id: Model identifier

        Returns:
            True if any dimension in this model has PII
        """
        ...

    def get_all_models_with_analysis(self) -> List[Dict[str, Any]]:
        """Get all models with semantic analysis for clustering.

        Returns list of dicts with model metadata needed for clustering:
        - model_id: Model identifier
        - relation_name: Database relation name
        - model_name: dbt model name
        - analysis_json: Full semantic analysis JSON (optional)
        - has_aggregations: Whether model has aggregations (boolean)
        - intent: Semantic analysis intent field (string)

        Returns:
            List of model metadata dictionaries
        """
        ...

    def store_cluster_analysis(
        self,
        clusters: Dict[int, List[str]],
        summaries: List["ClusterSummaryDTO"],
        blueprints: List["ClusterBlueprint"],
    ) -> None:
        """Store enhanced cluster analysis in the graph.

        This method replaces the old store_clusters() and stores richer
        cluster metadata including role breakdown, domains, PII flags,
        and blueprint recommendations.

        Args:
            clusters: Dict mapping cluster_id to list of model IDs
            summaries: List of ClusterSummaryDTO with detailed cluster analysis
            blueprints: List of ClusterBlueprint with schema design templates
        """
        ...

    # ---- Helper Methods (optional, for OpenLineage) ----

    def get_job(self, job_id: str) -> Optional[JobNode]:
        """Get job by ID (optional, for OpenLineage).

        Args:
            job_id: Job unique identifier

        Returns:
            JobNode if found, None otherwise
        """
        return None

    def get_dataset(self, dataset_id: str) -> Optional[DatasetNode]:
        """Get dataset by ID (optional, for OpenLineage).

        Args:
            dataset_id: Dataset unique identifier

        Returns:
            DatasetNode if found, None otherwise
        """
        return None

    def get_model_materializations(self, model_id: str) -> ModelMaterializationsResult:
        """Get all physical materializations (warehouse tables/views) for a dbt model.

        Args:
            model_id: DbtModel ID

        Returns:
            ModelMaterializationsResult with environment-specific details
        """
        ...

    def find_upstream(self, node_id: str, depth: int = 1) -> List[str]:
        """Find upstream dependencies (optional utility).

        Args:
            node_id: Starting node ID
            depth: How many levels to traverse

        Returns:
            List of upstream node IDs
        """
        return []

T = TypeVar('T', bound=BaseModel)


# ---- Typed Lineage Result Models ----


class LineageNode(BaseModel):
    """A node in a relation lineage graph.

    Represents DbtModel, PhysicalTable, PhysicalView, etc. with normalized type field.
    """

    model_config = {"extra": "allow"}  # Allow additional properties from graph

    type: str  # Node type: DbtModel, PhysicalTable, PhysicalView, etc.
    id: Optional[str] = None
    name: Optional[str] = None
    fqn: Optional[str] = None
    labels: Optional[List[str]] = None  # Original labels from graph
    # Common properties (optional, populated based on node type)
    database: Optional[str] = None
    schema_name: Optional[str] = None
    materialization: Optional[str] = None
    environment: Optional[str] = None
    warehouse_type: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def set_type_from_labels(cls, data: Any) -> Any:
        """Set type from labels list if type is missing."""
        if isinstance(data, dict):
            if "type" not in data and "labels" in data and data["labels"]:
                # Use the first label as the primary type
                data["type"] = data["labels"][0]
            elif "type" not in data:
                # Fallback if neither type nor labels exist
                data["type"] = "Unknown"
        return data


class ColumnLineageNode(BaseModel):
    """A node in a column lineage graph.

    Represents DbtColumn or PhysicalColumn with derivation info.
    """

    model_config = {"extra": "allow"}

    type: str  # DbtColumn, PhysicalColumn
    id: Optional[str] = None
    name: Optional[str] = None
    fqn: Optional[str] = None
    labels: Optional[List[str]] = None
    data_type: Optional[str] = None
    parent_model: Optional[str] = None
    parent_table: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def set_type_from_labels(cls, data: Any) -> Any:
        """Set type from labels list if type is missing."""
        if isinstance(data, dict):
            if "type" not in data and "labels" in data and data["labels"]:
                data["type"] = data["labels"][0]
            elif "type" not in data:
                data["type"] = "ColumnLineage"  # Default for column nodes
        return data


class ColumnLineageHop(BaseModel):
    """A single DERIVES_FROM hop with transformation metadata."""

    model_config = {"extra": "allow"}

    from_id: Optional[str] = None
    to_id: Optional[str] = None
    transformations: List[str] = []
    raw: Optional[Dict[str, Any]] = None


class RelationLineageResult(BaseModel):
    """Typed result from get_relation_lineage (token-efficient overview).

    Contains lightweight nodes with semantic summaries (no SQL) and edges.
    For detailed model information including SQL, use get_model_details().
    """

    nodes: List[LineageOverviewNode]
    edges: List[LineageRelationship] = []
    count: int
    query: str
    identifier: str
    node_type: Literal["physical", "logical"]
    direction: str
    depth: int
    query_description: str = ""  # Human-readable description of what this lineage trace is for


class ColumnLineageResult(BaseModel):
    """Typed result from get_column_lineage.

    Contains flattened, deduplicated column lineage nodes.
    """

    nodes: List[ColumnLineageNode]
    hops: List[ColumnLineageHop] = []
    count: int
    query: str
    identifier: str
    node_type: Literal["physical", "logical"]
    direction: str
    depth: int
    query_description: str = ""  # Human-readable description of what this column trace is for


class RawLineageQueryResult(BaseModel):
    """Raw result from executing a lineage query.

    Contains untyped dict rows that can be converted to Pydantic models
    using the convert() function.

    Example:
        raw = storage.execute_raw_query("MATCH (sm:NativeSemanticModel) RETURN sm.name ...")
        typed = convert(raw, NativeSemanticModelOverview)
    """
    rows: List[Dict[str, Any]]
    count: int
    query: str


class LineageQueryResult(BaseModel, Generic[T]):
    """Typed result from converting a raw lineage query.

    Args:
        nodes: List of validated Pydantic models
        count: Number of nodes returned
        query: The executed query
    """
    nodes: List[T]
    count: int
    query: str


def convert(
    raw_result: RawLineageQueryResult,
    model_class: type[T],
) -> LineageQueryResult[T]:
    """Convert raw query result to typed Pydantic models.

    This function deserializes raw dict rows into validated Pydantic models,
    enabling type-safe query results. Works with any Pydantic BaseModel,
    not just predefined node types.

    Args:
        raw_result: Raw query result with dict rows
        model_class: Pydantic model class to deserialize into

    Returns:
        Typed query result with validated Pydantic models

    Example:
        # With predefined models
        raw = storage.execute_raw_query(\"\"\"
            MATCH (sm:NativeSemanticModel)
            RETURN sm.name AS name, sm.database AS database, sm.schema_name AS schema,
                   sm.comment AS description, sm.provider AS provider,
                   sm.synonyms AS synonyms
        \"\"\")
        result = convert(raw, NativeSemanticModelOverview)
        for model in result.nodes:
            print(model.name)  # Full type safety!

        # With ad-hoc models for custom queries
        class ModelStats(BaseModel):
            model_name: str
            measure_count: int
            dimension_count: int

        raw = storage.execute_raw_query(\"\"\"
            MATCH (sm:NativeSemanticModel)
            OPTIONAL MATCH (sm)-[:HAS_MEASURE]->(m:NativeMeasure)
            OPTIONAL MATCH (sm)-[:HAS_DIMENSION]->(d:NativeDimension)
            RETURN sm.name AS model_name,
                   COUNT(DISTINCT m) AS measure_count,
                   COUNT(DISTINCT d) AS dimension_count
        \"\"\")
        stats = convert(raw, ViewStats)
        for stat in stats.nodes:
            print(f"{stat.view_name}: {stat.measure_count} measures")
    """
    nodes = [model_class(**row) for row in raw_result.rows]
    return LineageQueryResult(
        nodes=nodes,
        count=len(nodes),
        query=raw_result.query
    )


__all__ = [
    "LineageStorage",
    "JobNode",
    "DatasetNode",
    "RunNode",
    "LineageEdge",
    "JoinEdge",
    "ClusterInfo",
    "RawLineageQueryResult",
    "LineageQueryResult",
    "LineageNode",
    "ColumnLineageNode",
    "RelationLineageResult",
    "ColumnLineageResult",
    "convert",
    # Token-efficient lineage types
    "SemanticSummary",
    "LineageOverviewNode",
    "LineageRelationship",
    "ModelDetailsResult",
]
