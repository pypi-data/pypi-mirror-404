"""Shared base class for FalkorDB and FalkorDBLite adapters.

This module contains all shared logic between the network-based FalkorDB adapter
and the file-backed FalkorDBLite adapter. The only differences between the two
implementations are in connection initialization.

Both adapters use the same graph API after initialization, so all operations
(upsert_node, create_edge, execute_raw_query, etc.) are identical.
"""
from __future__ import annotations

import json
import logging
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

from falkordb.falkordb import FalkorDB
from falkordb.graph import Graph
from redis.exceptions import ResponseError
from redislite.falkordb_client import FalkorDB as FalkorDBLite
from redislite.falkordb_client import Graph as GraphLite

from lineage.backends.lineage.base import BaseLineageStorage
from lineage.backends.lineage.models.base import BaseNode, GraphEdge, NodeIdentifier
from lineage.backends.lineage.protocol import (
    DatasetNode,
    JobNode,
    RawLineageQueryResult,
)
from lineage.backends.lineage.schema_loader import load_schema

logger = logging.getLogger(__name__)


class _BaseFalkorDBAdapter(BaseLineageStorage):
    """Shared base class for FalkorDB and FalkorDBLite adapters.

    This base class contains all shared logic. Subclasses only need to
    implement __init__() to set up the client and graph connections.

    FalkorDB-specific notes:
    - Supports most Cypher syntax except regex and temporal functions
    - Requires manual index creation (no automatic indexing)
    - Properties are deleted with SET prop = NULL (not REMOVE)
    """

    def __init__(self, graph_name: str, read_only: bool, max_retries: int = 2):
        """Initialize base FalkorDB adapter.

        Subclasses should call super().__init__() then set self.client and self.graph.

        Args:
            graph_name: Name of the graph to use
            read_only: If True, prevent write operations
            max_retries: Maximum retries for transient query failures (default: 2).
                Must be at least 1 to ensure at least one attempt is made.

        Raises:
            ValueError: If max_retries is less than 1
        """
        if max_retries < 1:
            raise ValueError(f"max_retries must be at least 1, got {max_retries}")
        self.graph_name = graph_name
        self.read_only = read_only
        self.max_retries = max_retries
        # Subclasses must set these:
        self.client: FalkorDB | FalkorDBLite = None
        self.graph: Graph | GraphLite = None

    def close(self):
        """Close the FalkorDB client connection."""
        if hasattr(self, "client") and self.client:
            # FalkorDB client connection cleanup
            # The client uses Redis connection underneath
            logger.info("FalkorDB connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    # ------------------------------------------------------------------
    # Schema Management
    # ------------------------------------------------------------------

    def ensure_schema(self) -> None:
        """Create indexes on commonly queried properties.

        FalkorDB requires manual index creation (no automatic indexing).
        Unlike Neo4j, FalkorDB may not support unique constraints, so we
        create regular indexes on ID properties.
        """
        if self.read_only:
            logger.warning("Cannot ensure schema in read-only mode")
            return

        indexes = [
            # Logical dbt node indexes
            "CREATE INDEX FOR (n:DbtModel) ON (n.id)",
            "CREATE INDEX FOR (n:DbtSource) ON (n.id)",
            "CREATE INDEX FOR (n:DbtColumn) ON (n.id)",
            # Physical warehouse node indexes
            "CREATE INDEX FOR (n:PhysicalTable) ON (n.id)",
            "CREATE INDEX FOR (n:PhysicalView) ON (n.id)",
            "CREATE INDEX FOR (n:PhysicalMaterializedView) ON (n.id)",
            "CREATE INDEX FOR (n:PhysicalColumn) ON (n.id)",
            # OpenLineage node indexes
            "CREATE INDEX FOR (n:Job) ON (n.id)",
            "CREATE INDEX FOR (n:Dataset) ON (n.id)",
            "CREATE INDEX FOR (n:Run) ON (n.id)",
            "CREATE INDEX FOR (n:Error) ON (n.id)",
            # Inferred semantic node indexes (LLM-derived)
            "CREATE INDEX FOR (n:InferredSemanticModel) ON (n.id)",
            "CREATE INDEX FOR (n:InferredMeasure) ON (n.id)",
            "CREATE INDEX FOR (n:InferredDimension) ON (n.id)",
            "CREATE INDEX FOR (n:InferredFact) ON (n.id)",
            "CREATE INDEX FOR (n:InferredSegment) ON (n.id)",
            "CREATE INDEX FOR (n:TimeWindow) ON (n.id)",
            "CREATE INDEX FOR (n:TimeAttribute) ON (n.id)",
            "CREATE INDEX FOR (n:JoinEdge) ON (n.id)",
            "CREATE INDEX FOR (n:WindowFunction) ON (n.id)",
            # Native semantic node indexes (warehouse-declared)
            "CREATE INDEX FOR (n:NativeSemanticModel) ON (n.id)",
            "CREATE INDEX FOR (n:NativeMeasure) ON (n.id)",
            "CREATE INDEX FOR (n:NativeDimension) ON (n.id)",
            "CREATE INDEX FOR (n:NativeFact) ON (n.id)",
            "CREATE INDEX FOR (n:NativeBaseTable) ON (n.id)",
            # Clustering and profiling node indexes
            "CREATE INDEX FOR (n:JoinCluster) ON (n.cluster_id)",
            "CREATE INDEX FOR (n:TableProfile) ON (n.id)",
            "CREATE INDEX FOR (n:ColumnProfile) ON (n.id)",
            # Other node indexes
            "CREATE INDEX FOR (n:DataRequestTicket) ON (n.id)",
            # Additional indexes for commonly queried properties
            "CREATE INDEX FOR (n:DbtModel) ON (n.name)",
            "CREATE INDEX FOR (n:DbtSource) ON (n.name)",
            "CREATE INDEX FOR (n:PhysicalTable) ON (n.name)",
            "CREATE INDEX FOR (n:PhysicalView) ON (n.name)",
            "CREATE INDEX FOR (n:Job) ON (n.name)",
            "CREATE INDEX FOR (n:Run) ON (n.status)",
        ]

        for index in indexes:
            try:
                self.graph.query(index)
                logger.debug(f"Created index: {index[:60]}...")
            except Exception as e:
                # Index may already exist
                logger.debug(f"Index creation skipped (may exist): {e}")

        # Full-text indexes from schema.yaml
        self._ensure_fulltext_indexes()

        logger.info("Schema ensured: indexes created")

    def _ensure_fulltext_indexes(self) -> None:
        """Create full-text indexes from schema.yaml definitions.

        Fulltext indexes enable semantic search over node properties like
        name, description, compiled_sql, etc.
        """
        try:
            schema = load_schema()
        except Exception as e:
            logger.error(f"Failed to load schema for fulltext indexes: {e}")
            return

        # Get existing fulltext indexes
        existing_ft_labels = set()
        try:
            result = self.graph.query("CALL db.indexes()")
            for row in result.result_set:
                # row[0] is label, row[2] is field types dict where FULLTEXT indicates fulltext
                if row and len(row) > 2:
                    label = row[0]
                    field_types = row[2]  # OrderedDict like {'name': ['FULLTEXT'], ...}
                    # Check if any field has FULLTEXT type
                    has_fulltext = any(
                        'FULLTEXT' in types
                        for types in field_types.values()
                        if isinstance(types, list)
                    )
                    if has_fulltext:
                        existing_ft_labels.add(label)
        except Exception as e:
            logger.warning(f"Could not check existing indexes: {e}")

        created_count = 0
        skipped_count = 0

        for node_name, node_def in schema.get("nodes", {}).items():
            ft_cfg = node_def.get("fulltext_index")
            if not ft_cfg:
                continue

            fields = ft_cfg.get("fields") or []
            if not fields:
                continue

            # Skip if fulltext index already exists for this label
            if node_name in existing_ft_labels:
                logger.debug(f"Fulltext index already exists for {node_name}")
                skipped_count += 1
                continue

            # Build the query with proper quoting
            fields_str = ", ".join(repr(f) for f in fields)
            ft_query = f"CALL db.idx.fulltext.createNodeIndex('{node_name}', {fields_str})"

            try:
                self.graph.query(ft_query)
                created_count += 1
                logger.info(f"Created fulltext index for {node_name} on fields: {fields}")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exist" in error_msg or "duplicate" in error_msg:
                    logger.debug(f"Fulltext index already exists for {node_name}")
                    skipped_count += 1
                else:
                    logger.error(f"Failed to create fulltext index for {node_name}: {e}")

        logger.info(
            f"Fulltext indexes: {created_count} created, {skipped_count} already existed"
        )

    def list_fulltext_indexes(self) -> list[dict]:
        """List all fulltext indexes in the graph.

        Returns:
            List of dicts with 'label' and 'fields' keys
        """
        indexes = []
        try:
            result = self.graph.query("CALL db.indexes()")
            for row in result.result_set:
                if row and len(row) > 2:
                    label = row[0]
                    fields = row[1] if len(row) > 1 else []
                    field_types = row[2] if len(row) > 2 else {}

                    # Check if this is a fulltext index
                    has_fulltext = any(
                        'FULLTEXT' in types
                        for types in field_types.values()
                        if isinstance(types, list)
                    )
                    if has_fulltext:
                        indexes.append({
                            "label": label,
                            "fields": fields,
                        })
        except Exception as e:
            logger.error(f"Failed to list fulltext indexes: {e}")

        return indexes

    def recreate_schema(self) -> None:
        """Drop all data and recreate indexes.

        WARNING: This destroys all data in the graph!
        """
        if self.read_only:
            raise ValueError("Cannot recreate schema in read-only mode")

        # Delete all nodes and relationships (if graph exists)
        logger.warning("Deleting all nodes and relationships...")
        try:
            self.graph.delete()
        except ResponseError as e:
            # FalkorDB returns "Invalid graph operation on empty key" when the graph
            # does not yet exist. For test setups, we want recreate_schema() to be
            # idempotent and treat that as a no-op.
            if "Invalid graph operation on empty key" not in str(e):
                raise
            logger.debug("Graph doesn't exist yet, will create fresh")

        # Re-initialize graph object after deletion to ensure it references
        # a fresh graph instance (FalkorDB auto-creates graphs on first query,
        # but we need to re-select it to avoid stale state)
        self.graph = self.client.select_graph(self.graph_name)

        # Recreate indexes
        self.ensure_schema()
        logger.info("Schema recreated successfully")

    def set_active_graph(self, graph_name: str, ensure_schema: bool = True) -> None:
        """Switch to a different graph within the same FalkorDB instance.

        Args:
            graph_name: Name of the graph to switch to
            ensure_schema: If True and not read_only, ensure indexes exist on the new graph.
                FalkorDB indexes are per-graph, so switching graphs without ensuring schema
                will result in missing fulltext indexes and slower queries.
        """
        self.graph_name = graph_name
        self.graph = self.client.select_graph(graph_name)
        logger.info(f"Switched to graph: {graph_name}")

        # Ensure schema (indexes) exist on the new graph
        if ensure_schema and not self.read_only:
            self.ensure_schema()

    def list_graphs(self) -> list[str]:
        """List all graphs in the FalkorDB instance.

        Returns:
            List of graph names in the database
        """
        # FalkorDB stores graph names in a Redis key pattern
        # We can use KEYS command to list them
        try:
            # FalkorDB graph names are stored with prefix "graph:"
            return self.client.list_graphs()
        except Exception as e:
            logger.warning(f"Could not list graphs: {e}")
            return []

    # ========================================================================
    # CORE GENERIC METHODS
    # ========================================================================

    def upsert_node(
        self,
        node: BaseNode,
    ) -> None:
        """Generic node upsert - works for ALL node types.

        Args:
            node: Pydantic BaseNode with node_label and computed id
        """
        if self.read_only:
            raise ValueError("Cannot write in read-only mode")
        # Extract label, id, and properties from the node
        label = node.node_label.value
        id = node.id
        # Use mode='json' to serialize datetime objects to ISO strings
        properties = node.model_dump(mode='json')

        # Filter out None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Build Cypher MERGE query
        # FalkorDB uses SET prop = NULL instead of REMOVE for property deletion
        params = {"id": id}
        set_clauses = []

        for key, value in properties.items():
            param_key = f"prop_{key}"
            params[param_key] = self._normalize_value(value)
            set_clauses.append(f"n.{key} = ${param_key}")

        set_clause = ", ".join(set_clauses) if set_clauses else ""

        if set_clause:
            query = f"""
            MERGE (n:{label} {{id: $id}})
            ON CREATE SET {set_clause}
            ON MATCH SET {set_clause}
            """
        else:
            query = f"""
            MERGE (n:{label} {{id: $id}})
            """

        self._execute_query(query, params)

    def create_edge(
        self,
        from_node: Union[BaseNode, NodeIdentifier],
        to_node: Union[BaseNode, NodeIdentifier],
        edge: GraphEdge,
    ) -> None:
        """Generic edge creation - works for ALL edge types.

        Args:
            from_node: Source node (BaseNode or NodeIdentifier)
            to_node: Target node (BaseNode or NodeIdentifier)
            edge: GraphEdge with edge_type and properties
        """
        if self.read_only:
            raise ValueError("Cannot write in read-only mode")

        # Extract IDs and labels from nodes/identifiers
        if isinstance(from_node, BaseNode):
            from_id = from_node.id
            from_label = from_node.node_label
        else:
            from_id = from_node.id
            from_label = from_node.node_label

        if isinstance(to_node, BaseNode):
            to_id = to_node.id
            to_label = to_node.node_label
        else:
            to_id = to_node.id
            to_label = to_node.node_label

        # Extract edge type and properties
        edge_type = edge.edge_type.value
        # Use mode='json' to serialize datetime objects to ISO strings
        properties = edge.model_dump(mode='json')

        # Filter None values
        properties = {k: v for k, v in properties.items() if v is not None}

        # Build Cypher query
        params = {"from_id": from_id, "to_id": to_id}

        # Use MERGE to avoid duplicate relationships
        query = f"""
        MATCH (a:{from_label.value} {{id: $from_id}}), (b:{to_label.value} {{id: $to_id}})
        MERGE (a)-[r:{edge_type}]->(b)
        """

        # Add properties if they exist
        if properties:
            set_clauses = []
            for key, value in properties.items():
                param_key = f"prop_{key}"
                params[param_key] = self._normalize_value(value)
                set_clauses.append(f"r.{key} = ${param_key}")
            set_clause = ", ".join(set_clauses)
            query += f"\nON CREATE SET {set_clause}\nON MATCH SET {set_clause}"

        self._execute_query(query, params)

    def bulk_load(
        self,
        nodes: List[BaseNode],
        edges: List[tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> None:
        """Load nodes and edges into storage using one-by-one inserts.

        This is a simple implementation that loops over nodes and edges calling
        upsert_node() and create_edge() for each. For better performance, consider
        using the falkordb-bulk-loader CLI tool with CSV export.

        Args:
            nodes: List of all node Pydantic objects
            edges: List of (from_node, to_node, edge) tuples
            progress_callback: Optional callback for progress updates.
                Signature: (current: int, total: int, message: str) -> None
        """
        if self.read_only:
            raise ValueError("Cannot bulk load in read-only mode")

        total_items = len(nodes) + len(edges)
        logger.debug(f"Bulk loading {len(nodes)} nodes and {len(edges)} edges...")

        # Insert all nodes first
        for i, node in enumerate(nodes):
            self.upsert_node(node)
            if (i + 1) % 1000 == 0:
                if progress_callback:
                    progress_callback(i + 1, total_items, f"{i + 1}/{len(nodes)} nodes")
                else:
                    logger.debug(f"Loaded {i + 1}/{len(nodes)} nodes...")

        logger.debug(f"Completed loading {len(nodes)} nodes")

        # Insert all edges
        for i, (from_node, to_node, edge) in enumerate(edges):
            self.create_edge(from_node, to_node, edge)
            if (i + 1) % 1000 == 0:
                if progress_callback:
                    progress_callback(
                        len(nodes) + i + 1,
                        total_items,
                        f"{i + 1}/{len(edges)} edges",
                    )
                else:
                    logger.debug(f"Loaded {i + 1}/{len(edges)} edges...")

        logger.debug(f"Completed loading {len(edges)} edges")
        logger.debug("Bulk load completed successfully")

    def delete_model_cascade(self, model_id: str, preserve_model: bool = False) -> int:
        """Delete a DbtModel and all associated child nodes in a single atomic operation.

        Deletes:
        - DbtModel node (unless preserve_model=True)
        - DbtColumn nodes (children)
        - PhysicalTable/View/Column nodes (via BUILDS)
        - InferredSemanticModel and all semantic child nodes
        - TableProfile and ColumnProfile nodes
        - All edges involving these nodes

        Args:
            model_id: dbt unique_id of the model to delete
            preserve_model: If True, delete all children but keep the DbtModel node itself.
                Useful for incremental updates where we want to clear children before
                re-loading them.

        Returns:
            Number of nodes deleted
        """
        if self.read_only:
            raise ValueError("Cannot delete in read-only mode")

        # Validate model_id format
        if not model_id or not isinstance(model_id, str):
            raise ValueError(f"Invalid model_id: must be non-empty string, got {model_id!r}")

        # dbt resource IDs should start with known prefixes
        valid_prefixes = ("model.", "source.", "seed.", "snapshot.", "test.")
        if not model_id.startswith(valid_prefixes):
            logger.warning(
                f"model_id {model_id!r} does not match expected dbt format "
                f"(expected prefix: {', '.join(valid_prefixes)})"
            )

        # If preserving the model, we still need to clear outgoing edges even when the
        # model has no "child" nodes to delete. So we only early-exit if the model
        # node itself does not exist.
        if preserve_model:
            try:
                exists_result = self._execute_query(
                    "MATCH (m:DbtModel {id: $model_id}) RETURN COUNT(m) AS c",
                    {"model_id": model_id},
                )
                if not exists_result.result_set or int(exists_result.result_set[0][0]) == 0:
                    return 0
            except Exception:
                # Existence check is best-effort; proceed to deletion attempt.
                logger.warning(f"Failed to check if model {model_id} exists: {traceback.format_exc()}")

        # Single query for both count and delete - matches all related nodes
        # Uses semantic_model_id ownership key to avoid accidentally deleting other DbtModels
        #
        # IMPORTANT (incremental updates):
        # When preserve_model=True we intentionally DO NOT delete logical DbtColumn nodes.
        # Downstream models' column lineage edges (DERIVES_FROM) can point to these nodes,
        # and deleting them would permanently break lineage for unchanged downstream models.
        #
        # We still clear outgoing edges FROM the preserved model and its columns so the
        # modified model can be reloaded accurately.
        if preserve_model:
            base_query = """
                MATCH (m:DbtModel {id: $model_id})
                OPTIONAL MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(sem:InferredSemanticModel)
                OPTIONAL MATCH (sem_child)
                WHERE sem_child.semantic_model_id = sem.id AND NOT sem_child:DbtModel
                OPTIONAL MATCH (m)-[:BUILDS]->(phys)
                OPTIONAL MATCH (phys)-[:HAS_COLUMN]->(phys_col:PhysicalColumn)
                OPTIONAL MATCH (m)-[:HAS_PROFILE]->(prof:TableProfile)
                OPTIONAL MATCH (prof)-[:HAS_COLUMN_PROFILE]->(col_prof:ColumnProfile)
            """
        else:
            base_query = """
                MATCH (m:DbtModel {id: $model_id})
                OPTIONAL MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(sem:InferredSemanticModel)
                OPTIONAL MATCH (sem_child)
                WHERE sem_child.semantic_model_id = sem.id AND NOT sem_child:DbtModel
                OPTIONAL MATCH (m)-[:BUILDS]->(phys)
                OPTIONAL MATCH (phys)-[:HAS_COLUMN]->(phys_col:PhysicalColumn)
                OPTIONAL MATCH (m)-[:HAS_PROFILE]->(prof:TableProfile)
                OPTIONAL MATCH (prof)-[:HAS_COLUMN_PROFILE]->(col_prof:ColumnProfile)
                OPTIONAL MATCH (col:DbtColumn {parent_id: $model_id})
            """

        # Count first for metrics (exclude model from count if preserving)
        if preserve_model:
            count_query = base_query + """
                RETURN COUNT(DISTINCT sem) + COUNT(DISTINCT sem_child) +
                       COUNT(DISTINCT phys) + COUNT(DISTINCT phys_col) +
                       COUNT(DISTINCT prof) + COUNT(DISTINCT col_prof) AS total
            """
        else:
            count_query = base_query + """
                RETURN COUNT(DISTINCT m) + COUNT(DISTINCT sem) + COUNT(DISTINCT sem_child) +
                       COUNT(DISTINCT phys) + COUNT(DISTINCT phys_col) +
                       COUNT(DISTINCT prof) + COUNT(DISTINCT col_prof) + COUNT(DISTINCT col) AS total
            """
        count_succeeded = False
        deleted_count = 0
        try:
            result = self._execute_query(count_query, {"model_id": model_id})
            deleted_count = int(result.result_set[0][0]) if result.result_set else 0
            count_succeeded = True
        except Exception as e:
            # Count is only for metrics - log warning but still attempt deletion
            logger.warning(
                f"Failed to count nodes for model {model_id} before deletion: {e}. "
                "Proceeding with deletion attempt anyway."
            )
            # Don't return early - attempt deletion even if count failed

        # Only skip deletion if count succeeded AND found 0 nodes
        # If count failed, we can't know if model exists, so attempt deletion anyway
        if (not preserve_model) and count_succeeded and deleted_count == 0:
            return 0  # Model doesn't exist or no children, no-op

        # IMPORTANT (incremental updates):
        # When preserve_model=True we keep the DbtModel node, but we MUST clear its
        # outgoing dependency edges so they can be re-created accurately. Otherwise,
        # incremental updates can accumulate stale DEPENDS_ON / USES_MACRO edges.
        #
        # Additionally, we clear outgoing edges from its DbtColumns (DERIVES_FROM)
        # and model->column edges (MATERIALIZES). We intentionally DO NOT delete
        # DbtColumn nodes to preserve incoming lineage from downstream models.
        #
        # We do this as separate queries to avoid cartesian-product row explosion
        # from the multi-OPTIONAL-MATCH cascade query below.
        if preserve_model:
            try:
                self._execute_query(
                    "MATCH (m:DbtModel {id: $model_id})-[r:DEPENDS_ON]->() DELETE r",
                    {"model_id": model_id},
                )
                self._execute_query(
                    "MATCH (m:DbtModel {id: $model_id})-[r:USES_MACRO]->() DELETE r",
                    {"model_id": model_id},
                )
                self._execute_query(
                    "MATCH (m:DbtModel {id: $model_id})-[r:MATERIALIZES]->() DELETE r",
                    {"model_id": model_id},
                )
                self._execute_query(
                    "MATCH (c:DbtColumn {parent_id: $model_id})-[r:DERIVES_FROM]->() DELETE r",
                    {"model_id": model_id},
                )
            except Exception as e:
                # Edge cleanup is best-effort; cascade deletion below will still proceed.
                logger.warning(
                    f"Failed to clear outgoing dependency edges for preserved model {model_id}: {e}. "
                    "Proceeding with child-node cascade delete."
                )

        # Single atomic delete query - exclude model if preserving
        if preserve_model:
            delete_query = base_query + """
                DETACH DELETE sem, sem_child, phys, phys_col, prof, col_prof
            """
        else:
            delete_query = base_query + """
                DETACH DELETE m, sem, sem_child, phys, phys_col, prof, col_prof, col
            """

        try:
            self._execute_query(delete_query, {"model_id": model_id})
            if count_succeeded:
                if preserve_model:
                    logger.debug(f"Cleared {deleted_count} child nodes for model {model_id} (model preserved)")
                else:
                    logger.debug(f"Deleted model {model_id} and {deleted_count} associated nodes")
            else:
                # Count failed but deletion succeeded - log generic success
                if preserve_model:
                    logger.debug(f"Cleared child nodes for model {model_id} (model preserved, count unavailable)")
                else:
                    logger.debug(f"Deleted model {model_id} and associated nodes (count unavailable)")
        except Exception as e:
            # If single query fails, try step-by-step deletion as fallback
            logger.warning(f"Single-query cascade delete failed, trying step-by-step: {e}")
            # Clear outgoing dependency edges when preserving the model node
            if preserve_model:
                try:
                    self._execute_query(
                        "MATCH (m:DbtModel {id: $model_id})-[r:DEPENDS_ON]->() DELETE r",
                        {"model_id": model_id},
                    )
                    self._execute_query(
                        "MATCH (m:DbtModel {id: $model_id})-[r:USES_MACRO]->() DELETE r",
                        {"model_id": model_id},
                    )
                    self._execute_query(
                        "MATCH (m:DbtModel {id: $model_id})-[r:MATERIALIZES]->() DELETE r",
                        {"model_id": model_id},
                    )
                    self._execute_query(
                        "MATCH (c:DbtColumn {parent_id: $model_id})-[r:DERIVES_FROM]->() DELETE r",
                        {"model_id": model_id},
                    )
                except Exception as edge_e:
                    logger.warning(
                        f"Failed to clear outgoing dependency edges for preserved model {model_id} "
                        f"during fallback deletion: {edge_e}"
                    )
            self._execute_query(
                "MATCH (m:DbtModel {id: $model_id})-[:HAS_INFERRED_SEMANTICS]->(sem:InferredSemanticModel) "
                "OPTIONAL MATCH (child) WHERE child.semantic_model_id = sem.id AND NOT child:DbtModel "
                "DETACH DELETE sem, child",
                {"model_id": model_id}
            )
            self._execute_query(
                "MATCH (m:DbtModel {id: $model_id})-[:BUILDS]->(phys) "
                "OPTIONAL MATCH (phys)-[:HAS_COLUMN]->(phys_col:PhysicalColumn) "
                "DETACH DELETE phys, phys_col",
                {"model_id": model_id}
            )
            self._execute_query(
                "MATCH (m:DbtModel {id: $model_id})-[:HAS_PROFILE]->(prof:TableProfile) "
                "OPTIONAL MATCH (prof)-[:HAS_COLUMN_PROFILE]->(col_prof:ColumnProfile) "
                "DETACH DELETE prof, col_prof",
                {"model_id": model_id}
            )
            if not preserve_model:
                self._execute_query(
                    "MATCH (col:DbtColumn {parent_id: $model_id}) DETACH DELETE col",
                    {"model_id": model_id}
                )
            # Only delete the model node if not preserving
            if not preserve_model:
                self._execute_query(
                    "MATCH (m:DbtModel {id: $model_id}) DETACH DELETE m",
                    {"model_id": model_id}
                )
            if preserve_model:
                logger.debug(f"Cleared child nodes for {model_id} using step-by-step approach ({deleted_count} nodes)")
            else:
                logger.debug(f"Deleted model {model_id} using step-by-step approach ({deleted_count} nodes)")

        return deleted_count

    # ------------------------------------------------------------------
    # Override specific methods for performance (optional)
    # ------------------------------------------------------------------

    def get_job(self, job_id: str) -> Optional[JobNode]:
        """Get a Job node by ID (override for performance)."""
        result = self.graph.query(
            "MATCH (j:Job {id: $id}) RETURN j.name AS name, j.namespace AS namespace, j.job_type AS job_type",
            {"id": job_id},
        )

        if not result.result_set:
            return None

        record = result.result_set[0]
        return JobNode(
            id=job_id,
            name=record[0] if len(record) > 0 else "",
            namespace=record[1] if len(record) > 1 else "",
            job_type=record[2] if len(record) > 2 else "",
            metadata={},
        )

    def get_dataset(self, dataset_id: str) -> Optional[DatasetNode]:
        """Get a Dataset node by ID (override for performance)."""
        result = self.graph.query(
            "MATCH (d:Dataset {id: $id}) RETURN d.name AS name, d.namespace AS namespace, d.dataset_type AS dtype",
            {"id": dataset_id},
        )

        if not result.result_set:
            return None

        record = result.result_set[0]
        return DatasetNode(
            id=dataset_id,
            name=record[0] if len(record) > 0 else "",
            namespace=record[1] if len(record) > 1 else "",
            dataset_type=record[2] if len(record) > 2 else "",
            metadata={},
        )

    # ------------------------------------------------------------------
    # Query Methods (required by protocol)
    # ------------------------------------------------------------------

    def _convert_value(self, value):
        """Convert FalkorDB objects to JSON-serializable formats."""
        from falkordb import Edge, Node, Path

        if isinstance(value, Node):
            # Convert Node to dict with properties
            return {
                "id": value.id if hasattr(value, "id") else None,
                "labels": list(value.labels) if hasattr(value, "labels") else [],
                **value.properties
            }
        elif isinstance(value, Edge):
            # Convert Edge to dict
            return {
                "id": value.id if hasattr(value, "id") else None,
                "relation": value.relation if hasattr(value, "relation") else None,
                "src_node": value.src_node if hasattr(value, "src_node") else None,
                "dest_node": value.dest_node if hasattr(value, "dest_node") else None,
                **value.properties
            }
        elif isinstance(value, Path):
            # Convert Path to list of nodes and edges
            return {
                "nodes": [self._convert_value(n) for n in value.nodes()],
                "edges": [self._convert_value(e) for e in value.edges()],
            }
        elif isinstance(value, list):
            return [self._convert_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: self._convert_value(v) for k, v in value.items()}
        else:
            # Primitive types (str, int, float, bool, None)
            return value

    def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> RawLineageQueryResult:
        """Execute a raw Cypher query and return results in a consistent format.

        Automatically retries on transient failures up to max_retries times.

        Args:
            query: Cypher query string
            params: Optional dictionary of parameters to bind to the query
        Returns:
            Dictionary with rows (list of dicts), row_count, and query
        """
        last_error: Optional[Exception] = None

        # Ensure at least one attempt is made (defensive against invalid max_retries)
        attempts = max(1, self.max_retries)
        for attempt in range(attempts):
            try:
                result = self._execute_query(query, params)
                # Convert result to list of dicts
                rows = []
                column_names = [item[1] for item in result.header]
                # Convert the raw result into a list of dictionaries

                for row in result.result_set:
                    # Use zip() to pair the column names with the values in the current row
                    # Convert any FalkorDB objects to JSON-serializable formats
                    converted_row = [self._convert_value(value) for value in row]
                    new_dict = dict(zip(column_names, converted_row, strict=True))
                    rows.append(new_dict)

                return RawLineageQueryResult(rows=rows, count=len(rows), query=query)

            except Exception as e:
                last_error = e
                if attempt < attempts - 1:
                    logger.debug(
                        f"Query failed (attempt {attempt + 1}/{attempts}), retrying: "
                        f"{e.__class__.__name__}: {e}"
                    )

        # All attempts failed
        if last_error is None:
            # This should never happen due to validation, but defensive programming
            raise RuntimeError(
                f"Query failed after {attempts} attempts but no error was captured. "
                f"This indicates a bug in the retry logic."
            )
        logger.error(
            f"Query failed after {attempts} attempts: "
            f"{last_error.__class__.__name__}: {last_error}"
        )
        raise last_error

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search_nodes(self, node_label: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Use FalkorDB full-text index for search, with CONTAINS fallback.

        FalkorDB fulltext search supports:
        - Simple terms: "revenue" - matches any field containing "revenue"
        - Prefix matching: "rev*" - matches "revenue", "review", etc.
        - Fuzzy matching: "%revnue%1" - matches "revenue" with 1 edit distance
        - Boolean AND: "revenue monthly" - both terms required
        - Boolean OR: "revenue|income" - either term matches
        - Boolean NOT: "revenue -monthly" - excludes "monthly"

        Args:
            node_label: The node type to search (e.g., "DbtModel", "PhysicalTable")
            query: Search query with optional FalkorDB fulltext operators
            limit: Maximum results to return

        Returns:
            List of dicts with 'node' and 'score' keys, sorted by relevance
        """
        safe_label = self._validate_cypher_node_label(node_label)
        escaped_query = self._escape_cypher_string_literal(query)

        # Check if fulltext index exists for this label
        ft_indexes = self.list_fulltext_indexes()
        has_ft_index = any(idx["label"] == safe_label for idx in ft_indexes)

        if not has_ft_index:
            logger.info(f"No fulltext index for {safe_label}, using CONTAINS fallback")
        else:
            # Try full-text search
            ft_cypher = f"""
                CALL db.idx.fulltext.queryNodes('{safe_label}', '{escaped_query}')
                YIELD node, score
                RETURN node, score
                LIMIT {limit}
            """
            try:
                ft_result = self.execute_raw_query(ft_cypher)
                if ft_result.rows:
                    # Verify score is present in results
                    if "score" in ft_result.rows[0]:
                        logger.info(
                            f"Fulltext search for '{query}' on {node_label}: "
                            f"{len(ft_result.rows)} results"
                        )
                        return ft_result.rows
                    else:
                        logger.warning(
                            f"Fulltext search for {node_label} returned results without scores"
                        )
                else:
                    logger.info(
                        f"Fulltext search for '{query}' on {node_label}: 0 results, "
                        f"trying CONTAINS fallback"
                    )
            except Exception as e:
                error_msg = str(e).lower()
                if "index" in error_msg and ("not found" in error_msg or "does not exist" in error_msg):
                    logger.warning(f"Fulltext index for {safe_label} not ready: {e}")
                else:
                    logger.error(f"Fulltext search failed for {safe_label}: {e}")

        # Fallback: case-insensitive CONTAINS on common fields
        # Use CASE to compute approximate relevance score:
        # - Exact name match: 1.0
        # - Name contains: 0.8
        # - FQN contains: 0.6
        # - Description contains: 0.4
        fallback_cypher = f"""
            MATCH (n:`{safe_label}`)
            WHERE (exists(n.name) AND toLower(n.name) CONTAINS toLower('{escaped_query}'))
               OR (exists(n.description) AND toLower(n.description) CONTAINS toLower('{escaped_query}'))
               OR (exists(n.fqn) AND toLower(n.fqn) CONTAINS toLower('{escaped_query}'))
            RETURN n AS node,
                CASE
                    WHEN exists(n.name) AND toLower(n.name) = toLower('{escaped_query}') THEN 1.0
                    WHEN exists(n.name) AND toLower(n.name) CONTAINS toLower('{escaped_query}') THEN 0.8
                    WHEN exists(n.fqn) AND toLower(n.fqn) CONTAINS toLower('{escaped_query}') THEN 0.6
                    WHEN exists(n.description) AND toLower(n.description) CONTAINS toLower('{escaped_query}') THEN 0.4
                    ELSE 0.2
                END AS score
            ORDER BY score DESC
            LIMIT {limit}
        """
        fb_result = self.execute_raw_query(fallback_cypher)
        return fb_result.rows

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Execute a query with optional parameters.

        This method can be overridden by subclasses to handle parameterization differently.
        Default implementation uses standard parameterized queries.

        Args:
            query: Cypher query string (may contain $ parameters)
            params: Optional dictionary of parameter values
        """
        if self.read_only:
            return self.graph.ro_query(query, params)
        else:
            return self.graph.query(query, params)

    @staticmethod
    def _is_primitive(value) -> bool:
        return isinstance(value, (str, int, float, bool)) or value is None

    def _normalize_value(self, value):
        """Ensure property values comply with FalkorDB (primitives or arrays)."""
        if self._is_primitive(value):
            return value

        if isinstance(value, (list, tuple, set)):
            normalized_items = []
            for item in value:
                normalized_item = self._normalize_value(item)
                if not self._is_primitive(normalized_item):
                    return json.dumps(value, default=str)
                normalized_items.append(normalized_item)
            return normalized_items

        # Dicts or other complex types -> JSON string
        try:
            return json.dumps(value, default=str)
        except TypeError:
            return str(value)

    # get_graph_schema() inherited from BaseLineageStorage - uses schema.yaml

    def store_cluster_analysis(
        self,
        clusters: Dict[int, List[str]],
        summaries: List[Any],
        blueprints: List[Any],
    ) -> None:
        """Store enhanced cluster analysis in FalkorDB (schemaless approach).

        FalkorDB implementation:
        1. Delete existing JoinCluster nodes
        2. Create new JoinCluster nodes with enriched metadata
        3. Create IN_JOIN_CLUSTER relationships from models to clusters

        Args:
            clusters: Dict mapping cluster_id -> list of model IDs
            summaries: List of ClusterSummaryDTO with cluster analysis
            blueprints: List of ClusterBlueprint with schema design templates
        """
        from lineage.backends.lineage.models.clustering import JoinCluster

        # Step 1: Delete existing cluster nodes and relationships
        self.graph.query("MATCH (c:JoinCluster) DELETE c")

        # Step 2: Create cluster nodes with enriched metadata
        for summary, blueprint in zip(summaries, blueprints, strict=True):
            # Build JoinCluster node with all metadata
            cluster_node = JoinCluster(
                name=blueprint.subject_area_name,
                cluster_id=str(summary.cluster_id),
                subject_area=blueprint.subject_area_name,
                domains=summary.domains,
                total_edge_weight=summary.total_edge_weight,
                fact_table_count=len(summary.fact_tables),
                dimension_table_count=len(summary.dimension_tables),
                mixed_table_count=len(summary.mixed_tables),
                contains_pii=blueprint.contains_pii,
                pii_table_count=len(summary.has_pii_tables),
                recommended_fact_table=blueprint.fact_table,
                top_dimension_tables=blueprint.dimension_tables[:5],
                model_count=summary.size,
            )

            # Use upsert_node to store (leverages BaseLineageStorage logic)
            self.upsert_node(cluster_node)

        # Step 3: Create relationships from models to clusters
        for cluster_id, members in clusters.items():
            for model_id in members:
                # Use FalkorDB query to create relationship
                # Note: FalkorDB doesn't support regex, so we use exact match
                self.graph.query(
                    """
                    MATCH (m:DbtModel {id: $mid}), (c:JoinCluster {cluster_id: $cid})
                    CREATE (m)-[:IN_JOIN_CLUSTER]->(c)
                    """,
                    {"mid": model_id, "cid": str(cluster_id)},
                )

    def get_agent_hints(self) -> str:
        """Get FalkorDB-specific hints for AI agents writing Cypher queries."""
        return """
## FalkorDB Cypher Dialect Hints

You are querying a **FalkorDB** (RedisGraph) backend. Standard Cypher works, but keep these dialect rules in mind.

### Key Dialect Constraints
- **No regex** (`=~`) → use `CONTAINS`, `STARTS WITH`, `ENDS WITH`, `toLower()`.
- **No temporal arithmetic** → store timestamps as strings/ints and compare directly.
- **Property deletion** → `SET n.prop = NULL` (FalkorDB ignores `REMOVE`).
- **Relationship uniqueness quirks** → when de-duping, bind the relationship alias and (if necessary) add `WHERE ID(r) >= 0`.

```cypher
// Case-insensitive search without regex
MATCH (m:DbtModel)
WHERE toLower(m.name) CONTAINS toLower($needle)
RETURN m.id, m.name
```

### Supported Features
- Standard clauses: `MATCH`, `OPTIONAL MATCH`, `WITH`, `UNWIND`, aggregation.
- String helpers: `toLower`, `split`, `substring`, `trim`, etc.
- Collections: `COLLECT`, `apoc.coll.*` is **not** available—stick to native Cypher.

---

## Cypher Patterns That Map to Schema v2

**Logical ↔ Physical linkage (env aware)**
```cypher
MATCH (m:DbtModel {name: $model})
MATCH (m)-[b:BUILDS]->(p)
WHERE b.environment = $env
RETURN m.name, labels(p) AS physical_type, p.fqn, b.materialization_strategy
```

**Column-level lineage across layers**
```cypher
MATCH (target:DbtColumn {id: $child_id})
MATCH (source)<-[:DERIVES_FROM]-(target)
RETURN labels(source) AS node_type, source.id, source.name, source.confidence
```

**Semantic metadata summary for a model**
```cypher
MATCH (m:DbtModel {name: $model})
MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(s)
OPTIONAL MATCH (s)-[:HAS_MEASURE]->(meas)
OPTIONAL MATCH (s)-[:HAS_DIMENSION]->(dim)
RETURN m.name,
       s.grain_human,
       COLLECT(DISTINCT meas.name) AS measures,
       COLLECT(DISTINCT dim.name) AS dimensions
```

**Join insights and clustering**
```cypher
MATCH (m:DbtModel {name: $model})
OPTIONAL MATCH (m)-[:HAS_JOIN_EDGE]->(edge:JoinEdge)
OPTIONAL MATCH (m)-[:IN_JOIN_CLUSTER]->(cluster:JoinCluster)
RETURN COLLECT(DISTINCT edge.equi_condition) AS join_conditions,
       cluster.cluster_id AS cluster,
       cluster.pattern AS subject_area
```

**Runtime diagnostics via OpenLineage**
```cypher
MATCH (m:DbtModel {name: $model})
MATCH (j:Job)-[:EXECUTES]->(m)
MATCH (r:Run)-[:INSTANCE_OF]->(j)
OPTIONAL MATCH (r)-[:HAS_ERROR]->(err:Error)
RETURN r.id, r.status, r.start_time, err.error_type, err.message
ORDER BY r.start_time DESC
LIMIT 20
```

**Mapping datasets back to the warehouse**
```cypher
MATCH (ds:Dataset {namespace: $ns})
MATCH (ds)-[rel:SAME_AS]->(p:PhysicalTable)
RETURN ds.name, p.fqn, rel.confidence, rel.match_method
```

---

## Performance & Safety Tips
- Start exploratory queries with `LIMIT`, then remove once confident.
- Avoid Cartesian products: always connect matches or use `WHERE` equality.
- Use indexes by filtering on `id`, `name`, `cluster_id`, etc. (see `ensure_schema`).
- Always parameterize literals (`$param`) to prevent injection.
- Remember FalkorDB string functions are 1-based when supplying indices.
- Store and compare timestamps as ISO strings or epoch integers—no `datetime()` helpers exist.

---

## Common Gotchas Recap
- Regex/temporal functions are unsupported.
- `SET prop = NULL` instead of `REMOVE`.
- Relationship type and property names are case-sensitive.
- Use `COLLECT(DISTINCT ...)` if you see duplicates from multi-hop traversals.

Use these hints plus `schema.yaml` as the authoritative reference when crafting Cypher.
""".strip()
