"""Base class for LineageStorage implementations.

This module provides BaseLineageStorage which defines the core abstract methods
that all backends must implement. The API is intentionally minimal, with just
two core operations: upsert_node() and create_edge().

All specific operations (creating models, edges, etc.) use these generic methods
with explicit NodeLabel and EdgeType enums.
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Literal, Optional, Union

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.backends.lineage import LineageStorage
from lineage.backends.lineage.models.base import BaseNode, GraphEdge, NodeIdentifier
from lineage.backends.lineage.models.dto import JoinEdge
from lineage.backends.lineage.protocol import (
    ClusterInfo,
    ColumnLineageHop,
    ColumnLineageNode,
    ColumnLineageResult,
    DatasetNode,
    GraphSchemaFormat,
    JobNode,
    LineageDirection,
    LineageOverviewNode,
    LineageRelationship,
    ModelDetailsResult,
    ModelMaterialization,
    ModelMaterializationsResult,
    RawLineageQueryResult,
    RelationLineageResult,
    SemanticSummary,
)
from lineage.backends.types import NodeLabel

logger = logging.getLogger(__name__)


def _extract_table_name_from_fqn(fqn: str, fallback: str = "") -> str:
    """Extract the table name from a fully qualified relation name using sqlglot.

    This handles quoted identifiers that may contain dots, e.g.:
    - '"db.with.dots"."schema"."table.name"' -> 'table.name'
    - 'database.schema.table' -> 'table'
    - '"DATABASE"."SCHEMA"."TABLE"' -> 'TABLE'

    Args:
        fqn: Fully qualified relation name (may include quotes)
        fallback: Value to return if parsing fails

    Returns:
        The extracted table name, or fallback if parsing fails
    """
    if not fqn:
        return fallback

    try:
        # Parse as a SELECT statement to extract the table reference
        parsed = sqlglot.parse_one(f"SELECT * FROM {fqn}") # nosec: B608 sql is never executed
        table_expr = parsed.find(exp.Table)
        if table_expr and table_expr.name:
            return table_expr.name
    except SqlglotError:
        logger.debug(f"Failed to parse FQN with sqlglot: {fqn}; falling back to string split")

    # Fallback: strip quotes and split by dot (original behavior)
    stripped = fqn.replace('"', '')
    return stripped.split('.')[-1] if stripped else fallback


class BaseLineageStorage(ABC, LineageStorage):
    """Base implementation of LineageStorage protocol.

    Provides abstract methods for the core operations. Backends inherit from
    this class and implement the abstract methods.

    The API uses explicit enums for node labels and edge types, making it:
    - Type-safe (no string typos)
    - Self-documenting (labels/edges clear at call site)
    - Easy to maintain (no fragile pattern matching)
    """

    # ---- Core Generic Methods (MUST be implemented by subclasses) ----

    @abstractmethod
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
            view = NativeSemanticModel(name="sv_test", database="DB", schema_name="SCHEMA", provider="snowflake")
            self.upsert_node(view)  # No need to specify label or ID!
            ```
        """
        ...

    @abstractmethod
    def create_edge(
        self,
        from_node: Union[BaseNode, NodeIdentifier],
        to_node: Union[BaseNode, NodeIdentifier],
        edge: GraphEdge,
    ) -> None:
        """Generic edge creation - works for ALL edge types.

        Accepts either full BaseNode objects or lightweight NodeIdentifier objects.
        The edge object encodes its own edge_type and validates node type compatibility.

        Args:
            from_node: Source node or identifier
            to_node: Target node or identifier
            edge: GraphEdge with type validation and properties

        Example:
            ```python
            from lineage.models import DbtModel, NodeIdentifier, DependsOn, NodeLabel

            # With full nodes (when you have them)
            model1 = DbtModel(name="orders", database="db", schema="schema", ...)
            model2 = DbtModel(name="customers", database="db", schema="schema", ...)
            edge = DependsOn(type="model", direct=True)
            self.create_edge(model1, model2, edge)

            # With identifiers (when you only have IDs)
            from_id = NodeIdentifier(id="model.x", node_label=NodeLabel.DBT_MODEL)
            to_id = NodeIdentifier(id="model.y", node_label=NodeLabel.DBT_MODEL)
            edge = DependsOn(type="model", direct=True)
            self.create_edge(from_id, to_id, edge)
            ```
        """
        ...

    # ---- Query Methods (MUST be implemented by subclasses) ----

    @abstractmethod
    def execute_raw_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> RawLineageQueryResult:
        """Execute raw query in the backend's native language.

        Args:
            query: Query string (Cypher for KùzuDB/AGE/Neo4j, AQL for ArangoDB, etc.)
            params: Optional dict of query parameters for parameterized queries.

        Returns:
            RawLineageQueryResult with untyped dict rows that can be converted
            to Pydantic models using convert()
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Close backend connections and cleanup resources."""
        ...

    def get_graph_schema(self, format: GraphSchemaFormat = "summary") -> str | Dict[str, Any]:
        """Get the lineage graph schema in the specified format.

        Default implementation loads schema from schema.yaml.
        Backends with native introspection (KùzuDB) can override this.

        Args:
            format: Output format:
                - "summary" (default): Minimal natural language schema (~1,700 tokens).
                - "compact": Complete natural language schema with all properties (~3-4k tokens).
                - "structured": Full JSON with all node/relationship properties (~12k tokens).

        Returns:
            summary/compact: Markdown-formatted schema string
            structured: Dictionary with node_tables and relationship_tables
        """
        from lineage.backends.lineage.schema_loader import (
            generate_schema_compact,
            generate_schema_summary,
            load_schema,
            schema_to_get_graph_schema_format,
        )

        if format == "summary":
            return generate_schema_summary()
        elif format == "compact":
            return generate_schema_compact()
        else:
            schema = load_schema()
            return schema_to_get_graph_schema_format(schema)

    # ---- Helper Methods (default implementations) ----

    @staticmethod
    def _escape_cypher_string_literal(value: Optional[str]) -> str:
        r"""Escape a value for safe interpolation into a single-quoted Cypher string literal.

        Cypher supports escaping single quotes with backslashes (e.g. `\'`).
        If the input contains a trailing backslash (e.g. `test\`), failing to
        escape backslashes can cause the backslash to escape the closing quote,
        breaking the query and potentially enabling injection.

        We escape backslashes first, then single quotes.
        """
        if value is None:
            return ""
        s = str(value)
        return s.replace("\\", "\\\\").replace("'", "\\'")

    def _validate_cypher_node_label(self, node_label: str) -> str:
        """Validate a Cypher node label (cannot be safely parameterized).

        Cypher labels are identifiers, not string literals. Escaping is not a
        robust defense here; we must **strictly validate/whitelist** to prevent
        injection (e.g. `DbtModel) RETURN ...`).
        """
        candidate = (node_label or "").strip()
        if not candidate:
            raise ValueError("node_label must be non-empty")

        # Enforce identifier-safe characters only (no quotes, spaces, colons, parens, etc.)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", candidate):
            raise ValueError(f"Invalid node_label: {node_label!r}")

        # Whitelist against known labels (enum + schema.yaml) to avoid querying
        # arbitrary labels and to further reduce attack surface.
        allowed: set[str] | None = getattr(self, "_cached_allowed_node_labels", None)
        if allowed is None:
            allowed = {nl.value for nl in NodeLabel}
            try:
                schema = self.get_graph_schema()
                node_tables = schema.get("node_tables", {}) if isinstance(schema, dict) else {}
                if isinstance(node_tables, dict):
                    allowed |= set(node_tables.keys())
            except Exception:
                # If schema loading fails, fall back to enum-only allowlist.
                logger.warning("Failed to load graph schema; using enum-only allowlist.")
            self._cached_allowed_node_labels = allowed  # type: ignore[attr-defined]

        if candidate not in allowed:
            raise ValueError(f"Unknown node_label: {node_label!r}")

        return candidate

    def find_model_for_physical_table(self, relation_name: str) -> Optional[str]:
        """Find the corresponding dbt model or source for a given physical relation.

        Search order:
        1. Physical nodes (PhysicalTable/View/etc.) via BUILDS edge
        2. DbtModel by name (fallback if physical nodes don't exist)
        3. DbtSource by name (for source tables)

        Args:
            relation_name: Fully qualified relation name (e.g., "database.schema.table")

        Returns:
            Model or Source ID if found, None otherwise

        Note:
            Uses case-insensitive matching for Snowflake compatibility.
        """
        # Extract table name from FQN for fallback searches using sqlglot
        # This handles quoted identifiers that may contain dots
        table_name = _extract_table_name_from_fqn(relation_name) if relation_name else ""

        # Strategy 1: Match via physical nodes (most reliable when physical nodes exist)
        query_physical = """
            MATCH (p)
            WHERE (p:PhysicalTable OR p:PhysicalView OR p:PhysicalMaterializedView OR p:PhysicalIncrementalModel)
              AND toLower(p.fqn) = toLower($relation_name)
            MATCH (current_model:DbtModel)-[:BUILDS]->(p)
            RETURN current_model.id as model_id
        """
        try:
            result = self.execute_raw_query(query_physical, params={"relation_name": relation_name})
            if result.rows:
                return result.rows[0].get("model_id")
        except Exception as e:
            logger.debug(f"Physical node lookup failed for '{relation_name}': {e}")

        # Strategy 2: Fall back to DbtModel by name (for models without physical nodes)
        if table_name:
            query_model = """
                MATCH (m:DbtModel)
                WHERE toLower(m.name) = toLower($table_name)
                RETURN m.id as model_id
            """
            try:
                result = self.execute_raw_query(query_model, params={"table_name": table_name})
                if result.rows:
                    return result.rows[0].get("model_id")
            except Exception as e:
                logger.debug(f"DbtModel name lookup failed for '{table_name}': {e}")

            # Strategy 3: Fall back to DbtSource by name (for source tables)
            query_source = """
                MATCH (s:DbtSource)
                WHERE toLower(s.name) = toLower($table_name)
                RETURN s.id as model_id
            """
            try:
                result = self.execute_raw_query(query_source, params={"table_name": table_name})
                if result.rows:
                    return result.rows[0].get("model_id")
            except Exception as e:
                logger.debug(f"DbtSource name lookup failed for '{table_name}': {e}")

        return None

    # ---- Search (fallback) ----

    def search_nodes(self, node_label: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fallback CONTAINS-based search for backends without native full-text."""
        safe_label = self._validate_cypher_node_label(node_label)
        escaped = self._escape_cypher_string_literal(query)
        cypher = f"""
            MATCH (n:`{safe_label}`)
            WHERE (exists(n.name) AND toLower(n.name) CONTAINS toLower('{escaped}'))
               OR (exists(n.description) AND toLower(n.description) CONTAINS toLower('{escaped}'))
               OR (exists(n.fqn) AND toLower(n.fqn) CONTAINS toLower('{escaped}'))
            RETURN n AS node, 50 AS score
            LIMIT {limit}
        """
        result = self.execute_raw_query(cypher)
        return result.rows



    def get_unique_database_schema_pairs(self) -> List[tuple[str, str]]:
        """Get unique (database, schema) pairs from loaded dbt models.

        Default Cypher implementation for KùzuDB, Neo4j, FalkorDB, and PostgreSQL AGE.
        Backends using other query languages should override.

        Returns:
            List of (database_name, schema_name) tuples, ordered by database then schema.
            Empty list if no models loaded or query fails.
        """
        query = """
            MATCH (m:PhysicalTable)
            WHERE m.database IS NOT NULL AND m.schema_name IS NOT NULL
            RETURN DISTINCT m.database AS database, m.schema_name AS schema
            ORDER BY database, schema
        """

        try:
            result = self.execute_raw_query(query)
            pairs = []

            for row in result.rows:
                # Handle different result formats (list/tuple vs dict)
                if isinstance(row, (list, tuple)):
                    database, schema = row[0], row[1]
                elif isinstance(row, dict):
                    database = row.get("database")
                    schema = row.get("schema")
                else:
                    continue

                if database and schema:
                    pairs.append((database, schema))

            return pairs

        except Exception as e:
            logger.debug(f"Error getting database/schema pairs: {e}")
            return []

    def get_relation_lineage(
        self,
        identifier: str,
        node_type: Literal["physical", "logical"],
        direction: LineageDirection = "both",
        depth: int = 3,
        include_physical: bool = True,
    ) -> RelationLineageResult:
        """Get relation lineage crossing logical/physical boundaries (token-efficient overview).

        Returns lightweight nodes with semantic summaries (no SQL) and edges.
        Use get_model_details() for full model information including SQL.

        Args:
            identifier: Model ID, name, or FQN to start from
            node_type: Whether identifier refers to a "logical" (DbtModel) or "physical" table
            direction: Which direction to traverse - "upstream", "downstream", or "both"
            depth: Maximum traversal depth (default 3, use 1-2 for token efficiency)
            include_physical: Whether to include physical tables in results (default True)

        Returns:
            RelationLineageResult with lightweight nodes, edges, count, and query metadata
        """
        escaped_id = self._escape_cypher_string_literal(identifier)

        # Build direction-specific query parts
        include_upstream = direction in ("upstream", "both")
        include_downstream = direction in ("downstream", "both")

        # Query 1: Get lightweight node data with semantic summaries
        if node_type == "logical":
            # Start with the target model
            match_clause = f"""
                MATCH (m:DbtModel)
                WHERE toLower(m.id) = toLower('{escaped_id}') OR toLower(m.name) = toLower('{escaped_id}')
            """

            # Build optional matches based on direction
            optional_matches = []
            if include_physical:
                optional_matches.append("OPTIONAL MATCH (m)-[:BUILDS]->(physical)")

            if include_upstream:
                optional_matches.append(
                    f"OPTIONAL MATCH (m)-[:DEPENDS_ON*1..{depth}]->(upstream:DbtModel)"
                )
                if include_physical:
                    optional_matches.append(
                        "OPTIONAL MATCH (upstream)-[:BUILDS]->(up_physical)"
                    )

            if include_downstream:
                optional_matches.append(
                    f"OPTIONAL MATCH (downstream:DbtModel)-[:DEPENDS_ON*1..{depth}]->(m)"
                )
                if include_physical:
                    optional_matches.append(
                        "OPTIONAL MATCH (downstream)-[:BUILDS]->(down_physical)"
                    )

            # Build collection based on what we're gathering
            model_parts = ["m"]
            if include_upstream:
                model_parts.append("upstream")
            if include_downstream:
                model_parts.append("downstream")

            physical_parts = []
            if include_physical:
                physical_parts.append("physical")
                if include_upstream:
                    physical_parts.append("up_physical")
                if include_downstream:
                    physical_parts.append("down_physical")

            model_collect = " + ".join(
                f"COLLECT(DISTINCT {p})" for p in model_parts
            )
            if physical_parts:
                physical_collect = " + ".join(
                    f"COLLECT(DISTINCT {p})" for p in physical_parts
                )
                with_clause = f"""
                    WITH {model_collect} AS models,
                         {physical_collect} AS physicals
                    UNWIND models + physicals AS node
                """
            else:
                with_clause = f"""
                    WITH {model_collect} AS models
                    UNWIND models AS node
                """

            # Return only lightweight fields (no SQL!)
            # Filter nulls via WITH clause (FalkorDB doesn't support WHERE after UNWIND)
            cypher = f"""
                {match_clause}
                {chr(10).join(optional_matches)}
                {with_clause}
                WITH node WHERE node.id IS NOT NULL OR node.fqn IS NOT NULL
                OPTIONAL MATCH (node)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)
                RETURN DISTINCT
                    labels(node)[0] AS type,
                    node.id AS id,
                    node.name AS name,
                    node.materialization AS materialization,
                    node.fqn AS fqn,
                    ism.grain_human AS grain_human,
                    ism.intent AS intent,
                    ism.analysis_summary AS analysis_summary,
                    ism.has_aggregations AS has_aggregations,
                    ism.has_window_functions AS has_window_functions
                LIMIT 100
            """

        else:  # physical
            # Start at physical, find logical, traverse
            match_clause = f"""
                MATCH (pt:PhysicalTable)
                WHERE toLower(pt.fqn) = toLower('{escaped_id}') OR toLower(pt.id) = toLower('{escaped_id}')
            """

            optional_matches = ["OPTIONAL MATCH (m:DbtModel)-[:BUILDS]->(pt)"]

            if include_upstream:
                optional_matches.append(
                    f"OPTIONAL MATCH (m)-[:DEPENDS_ON*1..{depth}]->(upstream:DbtModel)"
                )
                if include_physical:
                    optional_matches.append(
                        "OPTIONAL MATCH (upstream)-[:BUILDS]->(up_physical)"
                    )

            if include_downstream:
                optional_matches.append(
                    f"OPTIONAL MATCH (downstream:DbtModel)-[:DEPENDS_ON*1..{depth}]->(m)"
                )
                if include_physical:
                    optional_matches.append(
                        "OPTIONAL MATCH (downstream)-[:BUILDS]->(down_physical)"
                    )

            # Build collection
            model_parts = ["pt", "m"]
            if include_upstream:
                model_parts.append("upstream")
            if include_downstream:
                model_parts.append("downstream")

            physical_parts = []
            if include_physical:
                if include_upstream:
                    physical_parts.append("up_physical")
                if include_downstream:
                    physical_parts.append("down_physical")

            model_collect = " + ".join(
                f"COLLECT(DISTINCT {p})" for p in model_parts
            )
            if physical_parts:
                physical_collect = " + ".join(
                    f"COLLECT(DISTINCT {p})" for p in physical_parts
                )
                with_clause = f"""
                    WITH {model_collect} AS models,
                         {physical_collect} AS physicals
                    UNWIND models + physicals AS node
                """
            else:
                with_clause = f"""
                    WITH {model_collect} AS models
                    UNWIND models AS node
                """

            # Return only lightweight fields (no SQL!)
            # Filter nulls via WITH clause (FalkorDB doesn't support WHERE after UNWIND)
            cypher = f"""
                {match_clause}
                {chr(10).join(optional_matches)}
                {with_clause}
                WITH node WHERE node.id IS NOT NULL OR node.fqn IS NOT NULL
                OPTIONAL MATCH (node)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)
                RETURN DISTINCT
                    labels(node)[0] AS type,
                    node.id AS id,
                    node.name AS name,
                    node.materialization AS materialization,
                    node.fqn AS fqn,
                    ism.grain_human AS grain_human,
                    ism.intent AS intent,
                    ism.analysis_summary AS analysis_summary,
                    ism.has_aggregations AS has_aggregations,
                    ism.has_window_functions AS has_window_functions
                LIMIT 100
            """

        raw_result = self.execute_raw_query(cypher)

        # Build lightweight nodes with semantic summaries
        nodes = []
        seen_ids = set()
        node_ids = set()  # Track all node IDs for edge filtering
        for row in raw_result.rows:
            node_id = row.get("id") or row.get("fqn")
            if not node_id or node_id in seen_ids:
                continue
            seen_ids.add(node_id)
            node_ids.add(node_id)

            # Build semantic summary if any semantic fields present
            # Check both text fields and boolean flags (boolean fields can be True/False/None)
            semantic_summary = None
            has_text_fields = any(row.get(f) is not None for f in ["grain_human", "intent", "analysis_summary"])
            has_boolean_flags = (
                row.get("has_aggregations") is True or row.get("has_window_functions") is True
            )
            if has_text_fields or has_boolean_flags:
                semantic_summary = SemanticSummary(
                    grain_human=row.get("grain_human"),
                    intent=row.get("intent"),
                    analysis_summary=row.get("analysis_summary"),
                    # FalkorDB can return NULL for these booleans; coerce to False to avoid
                    # Pydantic ValidationError (which would wipe the whole lineage result).
                    has_aggregations=row.get("has_aggregations") is True,
                    has_window_functions=row.get("has_window_functions") is True,
                )

            nodes.append(LineageOverviewNode(
                type=row.get("type", "Unknown"),
                id=node_id,
                name=row.get("name", ""),
                fqn=row.get("fqn"),
                materialization=row.get("materialization"),
                semantic_summary=semantic_summary,
            ))

        # Query 2: Get edges between discovered nodes
        edges = []
        # Only query edges when there are at least two distinct nodes. While a single node
        # could theoretically have self-referential edges, lineage here is concerned with
        # relationships between different nodes, so we skip the edge query for len == 1
        if len(node_ids) > 1:
            edges = self._get_lineage_edges(node_ids, include_physical)

        return RelationLineageResult(
            nodes=nodes,
            edges=edges,
            count=len(nodes),
            query=cypher,
            identifier=identifier,
            node_type=node_type,
            direction=direction,
            depth=depth,
        )

    def _get_lineage_edges(
        self, node_ids: set, include_physical: bool = True
    ) -> List[LineageRelationship]:
        """Get edges between a set of nodes for lineage results.

        Args:
            node_ids: Set of node IDs to find edges between
            include_physical: Whether to include BUILDS edges to physical tables

        Returns:
            List of LineageRelationship objects
        """
        # Build a list of IDs for the IN clause
        id_list = ", ".join(f"'{self._escape_cypher_string_literal(nid)}'" for nid in node_ids)

        # Query for DEPENDS_ON edges between DbtModels
        edge_queries = [f"""
            MATCH (a:DbtModel)-[r:DEPENDS_ON]->(b:DbtModel)
            WHERE a.id IN [{id_list}] AND b.id IN [{id_list}]
            RETURN a.id AS from_id, b.id AS to_id, 'DEPENDS_ON' AS edge_type
        """]

        if include_physical:
            # Also get BUILDS edges
            edge_queries.append(f"""
                MATCH (m:DbtModel)-[r:BUILDS]->(p)
                WHERE m.id IN [{id_list}] AND (p.id IN [{id_list}] OR p.fqn IN [{id_list}])
                RETURN m.id AS from_id, COALESCE(p.id, p.fqn) AS to_id, 'BUILDS' AS edge_type
            """)

        edges = []
        seen_edges = set()
        for query in edge_queries:
            try:
                result = self.execute_raw_query(query)
                for row in result.rows:
                    from_id = row.get("from_id")
                    to_id = row.get("to_id")
                    edge_type = row.get("edge_type")
                    if from_id and to_id:
                        edge_key = (from_id, to_id, edge_type)
                        if edge_key not in seen_edges:
                            seen_edges.add(edge_key)
                            edges.append(LineageRelationship(
                                from_id=from_id,
                                to_id=to_id,
                                edge_type=edge_type,
                            ))
            except Exception as e:
                logger.debug(f"Error getting lineage edges: {e}")

        return edges

    def get_column_lineage(
        self,
        identifier: str,
        node_type: Literal["physical", "logical"],
        direction: str = "upstream",
        depth: int = 10,
    ) -> ColumnLineageResult:
        """Get column lineage via DERIVES_FROM.

        Returns fully flattened path including nodes and edges (hops).
        """
        escaped_id = self._escape_cypher_string_literal(identifier)

        if node_type == "physical":
            node_label = "PhysicalColumn"
            id_field = "fqn"
            default_type = "PhysicalColumn"
        else:
            node_label = "DbtColumn"
            id_field = "id"
            default_type = "DbtColumn"

        # Return the full path object + starting column
        if direction == "downstream":
            cypher = f"""
                MATCH (col:{node_label})
                WHERE toLower(col.{id_field}) = toLower('{escaped_id}')
                OPTIONAL MATCH path = (col)<-[:DERIVES_FROM*1..{depth}]-(downstream)
                RETURN col, path
                LIMIT 100
            """
        else:  # upstream
            cypher = f"""
                MATCH (col:{node_label})
                WHERE toLower(col.{id_field}) = toLower('{escaped_id}')
                OPTIONAL MATCH path = (col)-[:DERIVES_FROM*1..{depth}]->(upstream)
                RETURN col, path
                LIMIT 100
            """

        raw_result = self.execute_raw_query(cypher)

        # Parse paths into unique nodes and hops
        unique_nodes: Dict[str, ColumnLineageNode] = {}
        hops: List[ColumnLineageHop] = []

        for row in raw_result.rows:
            # Always include the starting column
            col_data = row.get("col")
            if col_data and isinstance(col_data, dict):
                col_id_val = col_data.get("id") or col_data.get("fqn")
                if col_id_val and col_id_val not in unique_nodes:
                    if "type" not in col_data:
                        labels = col_data.get("labels", [])
                        col_data["type"] = labels[0] if labels else default_type
                    unique_nodes[col_id_val] = ColumnLineageNode(**col_data)

            # Process path if it exists
            path_data = row.get("path")
            if not path_data or not isinstance(path_data, dict):
                continue

            # Extract nodes from path and build ID mapping
            nodes_list = path_data.get("nodes", [])
            node_id_by_index = []  # Store semantic IDs in order

            for node_data in nodes_list:
                semantic_id = node_data.get("id") or node_data.get("fqn")
                node_id_by_index.append(semantic_id)

                if semantic_id and semantic_id not in unique_nodes:
                    # Ensure type is set
                    if "type" not in node_data:
                        labels = node_data.get("labels", [])
                        node_data["type"] = labels[0] if labels else default_type
                    unique_nodes[semantic_id] = ColumnLineageNode(**node_data)

            # Extract edges from path
            # For a path of N nodes, there are N-1 edges
            # Edge[i] connects Node[i] → Node[i+1]
            edges_list = path_data.get("edges", [])
            for edge_idx, edge_data in enumerate(edges_list):
                # Only care about DERIVES_FROM for column lineage
                rel_type = edge_data.get("relation") or edge_data.get("type")
                if rel_type != "DERIVES_FROM":
                    continue

                # Extract transformations from edge properties
                transformations = []
                # Check common property names for transformations
                for key in ["transformation", "transformation_types", "expression", "operation"]:
                    val = edge_data.get(key)
                    if val:
                        if isinstance(val, list):
                            transformations.extend([str(v) for v in val])
                        else:
                            transformations.append(str(val))

                # Map edge to nodes by index
                # Edge[i] connects Node[i] → Node[i+1]
                from_id = node_id_by_index[edge_idx] if edge_idx < len(node_id_by_index) else None
                to_id = node_id_by_index[edge_idx + 1] if edge_idx + 1 < len(node_id_by_index) else None

                hops.append(
                    ColumnLineageHop(
                        from_id=from_id,
                        to_id=to_id,
                        transformations=transformations,
                        raw=edge_data,
                    )
                )

        return ColumnLineageResult(
            nodes=list(unique_nodes.values()),
            hops=hops,
            count=len(unique_nodes),
            query=cypher,
            identifier=identifier,
            node_type=node_type,
            direction=direction,
            depth=depth,
        )

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
            include_sql: Include raw_sql and canonical_sql
            include_semantics: Include full semantic analysis (grain, measures, dimensions, facts)
            include_columns: Include DbtColumn information via MATERIALIZES relationship
            include_macros: Include DbtMacro dependencies via USES_MACRO relationship

        Returns:
            ModelDetailsResult with requested detail level
        """
        # Build the query based on what we need
        # Always get basic model info
        base_fields = [
            "m.id AS model_id",
            "m.name AS model_name",
            "m.materialization AS materialization",
            "m.description AS description",
            "m.unique_id AS unique_id",
            "m.original_path AS original_path",
        ]

        if include_sql:
            base_fields.extend([
                "m.raw_sql AS raw_sql",
                "m.canonical_sql AS canonical_sql",
            ])

        # Base query - use case-insensitive matching for consistency with get_relation_lineage
        escaped_id = self._escape_cypher_string_literal(model_id)
        cypher = f"""
            MATCH (m:DbtModel)
            WHERE toLower(m.id) = toLower('{escaped_id}')
            RETURN {', '.join(base_fields)}
            LIMIT 1
        """

        raw_result = self.execute_raw_query(cypher)

        if not raw_result.rows:
            # Model not found - return empty result
            return ModelDetailsResult(
                model_id=model_id,
                model_name="",
            )

        row = raw_result.rows[0]

        # Use the actual ID from the database (normalized casing) for all subsequent queries
        normalized_model_id = row.get("model_id", model_id)

        # Build result with basic info
        result = ModelDetailsResult(
            model_id=normalized_model_id,
            model_name=row.get("model_name", ""),
            materialization=row.get("materialization"),
            description=row.get("description"),
            unique_id=row.get("unique_id"),
            original_path=row.get("original_path"),
        )

        # Add SQL if requested
        if include_sql:
            result.raw_sql = row.get("raw_sql")
            result.canonical_sql = row.get("canonical_sql")

        # Add semantics if requested
        if include_semantics:
            self._add_semantics_to_details(normalized_model_id, result)

        # Add columns if requested
        if include_columns:
            self._add_columns_to_details(normalized_model_id, result)

        # Add macros if requested
        if include_macros:
            self._add_macros_to_details(normalized_model_id, result)

        return result

    def _add_semantics_to_details(self, model_id: str, result: ModelDetailsResult) -> None:
        """Add semantic analysis data to model details result."""
        # Get InferredSemanticModel - use case-insensitive matching for API consistency
        sem_query = """
            MATCH (m:DbtModel)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                ism.grain_human AS grain,
                ism.intent AS intent,
                ism.analysis_summary AS analysis_summary,
                ism.has_aggregations AS has_aggregations,
                ism.has_window_functions AS has_window_functions
            LIMIT 1
        """
        sem_result = self.execute_raw_query(sem_query, params={"model_id": model_id})

        if sem_result.rows:
            sem_row = sem_result.rows[0]
            result.grain = sem_row.get("grain")
            result.intent = sem_row.get("intent")
            result.analysis_summary = sem_row.get("analysis_summary")
            result.has_aggregations = sem_row.get("has_aggregations")
            result.has_window_functions = sem_row.get("has_window_functions")

        # Get measures - use case-insensitive matching for API consistency
        measures_query = """
            MATCH (m:DbtModel)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)-[:HAS_MEASURE]->(measure:InferredMeasure)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                measure.name AS name,
                measure.expr AS expr,
                measure.agg_function AS agg_function,
                measure.description AS description
        """
        measures_result = self.execute_raw_query(measures_query, params={"model_id": model_id})
        result.measures = [
            {
                "name": r.get("name"),
                "expr": r.get("expr"),
                "agg_function": r.get("agg_function"),
                "description": r.get("description"),
            }
            for r in measures_result.rows
        ]

        # Get dimensions - use case-insensitive matching for API consistency
        dimensions_query = """
            MATCH (m:DbtModel)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)-[:HAS_DIMENSION]->(dim:InferredDimension)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                dim.name AS name,
                dim.source AS source,
                dim.is_pii AS is_pii,
                dim.description AS description
        """
        dimensions_result = self.execute_raw_query(dimensions_query, params={"model_id": model_id})
        result.dimensions = [
            {
                "name": r.get("name"),
                "source": r.get("source"),
                "is_pii": r.get("is_pii"),
                "description": r.get("description"),
            }
            for r in dimensions_result.rows
        ]

        # Get facts - use case-insensitive matching for API consistency
        facts_query = """
            MATCH (m:DbtModel)-[:HAS_INFERRED_SEMANTICS]->(ism:InferredSemanticModel)-[:HAS_FACT]->(fact:InferredFact)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                fact.name AS name,
                fact.source AS source,
                fact.description AS description
        """
        facts_result = self.execute_raw_query(facts_query, params={"model_id": model_id})
        result.facts = [
            {
                "name": r.get("name"),
                "source": r.get("source"),
                "description": r.get("description"),
            }
            for r in facts_result.rows
        ]

    def _add_columns_to_details(self, model_id: str, result: ModelDetailsResult) -> None:
        """Add column information to model details result."""
        # Use case-insensitive matching for API consistency
        columns_query = """
            MATCH (m:DbtModel)-[:MATERIALIZES]->(col:DbtColumn)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                col.name AS name,
                col.data_type AS data_type,
                col.description AS description
        """
        columns_result = self.execute_raw_query(columns_query, params={"model_id": model_id})
        result.columns = [
            {
                "name": r.get("name"),
                "data_type": r.get("data_type"),
                "description": r.get("description"),
            }
            for r in columns_result.rows
        ]

    def _add_macros_to_details(self, model_id: str, result: ModelDetailsResult) -> None:
        """Add macro dependencies to model details result."""
        # Use case-insensitive matching for API consistency
        macros_query = """
            MATCH (m:DbtModel)-[:USES_MACRO]->(macro:DbtMacro)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                macro.name AS name,
                macro.unique_id AS unique_id,
                macro.package_name AS package_name,
                macro.description AS description
        """
        macros_result = self.execute_raw_query(macros_query, params={"model_id": model_id})
        result.macros = [
            {
                "name": r.get("name"),
                "unique_id": r.get("unique_id"),
                "package_name": r.get("package_name"),
                "description": r.get("description"),
            }
            for r in macros_result.rows
        ]

    # ---- Join Graph Clustering (default implementations) ----

    _CONFIDENCE_ORDER = {"low": 0, "medium": 1, "high": 2}

    def _confidence_rank(self, value: Optional[str]) -> int:
        if not value:
            return 0
        return self._CONFIDENCE_ORDER.get(value.lower(), 0)

    def compute_join_graph(self) -> List[JoinEdge]:
        """Extract join relationships from formalized graph nodes and aggregate into edges.

        This method:
        1. Queries all JoinEdge nodes that have been resolved to models (left_model_id/right_model_id)
        2. Aggregates joins between the same two models
        3. Returns a list of JoinEdge DTOs for clustering

        Uses the new formalized graph structure instead of parsing JSON.

        Returns:
            List of JoinEdge DTOs with aggregated join counts
        """
        logger.info("Computing join graph from formalized semantic nodes...")

        edge_records = self.get_join_edges()
        logger.info(f"Found {len(edge_records)} unique join edges")

        edges: List[JoinEdge] = []
        for record in edge_records:
            edges.append(
                JoinEdge(
                    source=record["source"],
                    target=record["target"],
                    count=int(record["weight"]),
                    models=record["models"],
                    join_types=record["join_types"],
                    equi_conditions=record["equi_conditions"],
                )
            )

        return edges
    def cluster_join_graph(self, min_count: int = 1) -> Dict[int, List[str]]:
        """Cluster join graph (default returns empty)."""
        return {}

    def store_clusters(self, clusters: Dict[int, List[str]]) -> None:
        """Legacy cluster storage hook (deprecated)."""
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement store_cluster_analysis(); "
            "store_clusters() is deprecated."
        )

    def get_join_edges(
        self,
        min_confidence: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch aggregated join edges from JoinEdge nodes using relationship edges.

        Uses JOINS_LEFT_MODEL and JOINS_RIGHT_MODEL edges to find connected models,
        rather than relying on left_model_id/right_model_id properties.
        """
        threshold = 0
        if min_confidence:
            min_conf = min_confidence.lower()
            if min_conf not in self._CONFIDENCE_ORDER:
                valid = ", ".join(self._CONFIDENCE_ORDER.keys())
                raise ValueError(
                    f"Invalid confidence '{min_confidence}'. Valid options: {valid}"
                )
            threshold = self._confidence_rank(min_conf)

        query = """
            MATCH (je:JoinEdge)-[:JOINS_LEFT_MODEL]->(m1:DbtModel)
            MATCH (je)-[:JOINS_RIGHT_MODEL]->(m2:DbtModel)
            WHERE m1.id < m2.id
            WITH m1.id AS source, m2.id AS target, je
            RETURN
                source,
                target,
                COUNT(je) AS weight,
                COLLECT(DISTINCT je.semantic_model_id) AS models,
                COLLECT(DISTINCT COALESCE(je.effective_type, je.join_type)) AS join_types,
                COLLECT(DISTINCT COALESCE(je.normalized_equi_condition, je.equi_condition)) AS equi_conditions,
                COLLECT(DISTINCT COALESCE(je.scope, 'unknown')) AS scopes,
                COLLECT(DISTINCT COALESCE(je.confidence, 'low')) AS confidences
        """
        result = self.execute_raw_query(query)

        edges: List[Dict[str, Any]] = []
        for row in result.rows:
            source = row.get("source")
            target = row.get("target")
            if not source or not target:
                continue

            models_raw = [m for m in (row.get("models") or []) if m]
            contributing_models = sorted(
                {
                    model_id.replace(".inferred_semantics", "")
                    for model_id in models_raw
                }
            )

            join_types = sorted(
                {jt for jt in row.get("join_types") or [] if jt}
            )
            equi_conditions = sorted(
                {cond for cond in row.get("equi_conditions") or [] if cond}
            )
            scopes = sorted(
                {scope for scope in row.get("scopes") or [] if scope}
            )

            confidences_raw = [
                (conf or "low").lower() for conf in (row.get("confidences") or [])
            ]
            confidences = sorted({conf for conf in confidences_raw})
            if not confidences:
                confidences = ["low"]

            max_rank = max(self._confidence_rank(conf) for conf in confidences)
            if max_rank < threshold:
                continue

            weight = int(row.get("weight") or 0)
            if weight <= 0:
                continue

            edges.append(
                {
                    "source": source,
                    "target": target,
                    "weight": weight,
                    "models": contributing_models,
                    "join_types": join_types,
                    "equi_conditions": equi_conditions,
                    "scopes": scopes,
                    "confidences": confidences,
                }
            )

        return edges

    def get_clusters(self) -> List[ClusterInfo]:
        """Get clusters (default returns empty)."""
        return []

    # ---- Clustering Enrichment (universal Cypher implementations) ----

    def get_model_business_measure_count(self, model_id: str) -> int:
        """Count InferredMeasure nodes for a model (universal Cypher).

        Uses simple MATCH/COUNT query that works on all backends.
        Note: InferredMeasure nodes are connected via InferredSemanticModel.
        """
        safe_id = self._escape_cypher_string_literal(model_id)
        query = f"""
            MATCH (m:DbtModel {{id: '{safe_id}'}})-[:HAS_INFERRED_SEMANTICS]->(s:InferredSemanticModel)-[:HAS_MEASURE]->(bm:InferredMeasure)
            RETURN COUNT(bm) AS cnt
        """
        result = self.execute_raw_query(query)
        if result.rows:
            return int(result.rows[0].get("cnt", 0))
        return 0

    def get_model_business_dimension_count(self, model_id: str) -> int:
        """Count InferredDimension nodes for a model (universal Cypher).

        Uses simple MATCH/COUNT query that works on all backends.
        Note: InferredDimension nodes are connected via InferredSemanticModel.
        """
        safe_id = self._escape_cypher_string_literal(model_id)
        query = f"""
            MATCH (m:DbtModel {{id: '{safe_id}'}})-[:HAS_INFERRED_SEMANTICS]->(s:InferredSemanticModel)-[:HAS_DIMENSION]->(bd:InferredDimension)
            RETURN COUNT(bd) AS cnt
        """
        result = self.execute_raw_query(query)
        if result.rows:
            return int(result.rows[0].get("cnt", 0))
        return 0

    def model_has_pii(self, model_id: str) -> bool:
        """Check if any InferredDimension has is_pii=true (universal Cypher).

        Uses COLLECT to aggregate is_pii flags, then checks in Python.
        Note: InferredDimension nodes are connected via InferredSemanticModel.
        """
        safe_id = self._escape_cypher_string_literal(model_id)
        query = f"""
            MATCH (m:DbtModel {{id: '{safe_id}'}})-[:HAS_INFERRED_SEMANTICS]->(s:InferredSemanticModel)-[:HAS_DIMENSION]->(bd:InferredDimension)
            RETURN COLLECT(bd.is_pii) AS pii_flags
        """
        result = self.execute_raw_query(query)
        if result.rows:
            pii_flags = result.rows[0].get("pii_flags", [])
            # Check if any flag is true (handle various representations)
            return any(
                flag in (True, "true", "True", 1, "1")
                for flag in pii_flags
                if flag is not None
            )
        return False

    def get_all_models_with_analysis(self) -> List[Dict[str, Any]]:
        """Get all models with semantic analysis (universal Cypher).

        Uses simple MATCH/OPTIONAL MATCH/RETURN - works on all backends.
        """
        query = """
            MATCH (m:DbtModel)
            OPTIONAL MATCH (m)-[:HAS_INFERRED_SEMANTICS]->(s:InferredSemanticModel)
            RETURN m.id AS model_id,
                   m.relation_name AS relation_name,
                   m.name AS model_name,
                   s.has_aggregations AS has_aggregations,
                   s.intent AS intent
        """
        result = self.execute_raw_query(query)
        return result.rows

    def store_cluster_analysis(
        self,
        clusters: Dict[int, List[str]],
        summaries: List[Any],  # ClusterSummaryDTO
        blueprints: List[Any],  # ClusterBlueprint
    ) -> None:
        """Store enhanced cluster analysis (adapter-specific implementation required).

        Default implementation raises NotImplementedError. Each adapter should
        implement this method according to its schema management approach:
        - KuzuDB: DROP TABLE IF EXISTS + CREATE NODE TABLE
        - FalkorDB: DELETE + CREATE with schemaless approach
        - Neo4j: MERGE with constraints
        - PostgreSQL AGE: Custom _cypher() wrapper

        Args:
            clusters: Dict mapping cluster_id -> list of model IDs
            summaries: List of ClusterSummaryDTO with cluster analysis
            blueprints: List of ClusterBlueprint with schema design templates

        Raises:
            NotImplementedError: Adapters must override this method
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement store_cluster_analysis()"
        )

    # ---- OpenLineage Helpers (default implementations) ----

    def get_job(self, job_id: str) -> Optional[JobNode]:
        """Get job by ID (default implementation returns None)."""
        return None

    def get_dataset(self, dataset_id: str) -> Optional[DatasetNode]:
        """Get dataset by ID (default implementation returns None)."""
        return None

    def get_model_materializations(self, model_id: str) -> ModelMaterializationsResult:
        """Get all physical materializations (warehouse tables/views) for a dbt model.

        Returns details for each environment where this model is built.

        Args:
            model_id: DbtModel ID (e.g., "model.project.model_name")

        Returns:
            ModelMaterializationsResult with environment-specific details
        """
        # Use case-insensitive matching for consistency with get_relation_lineage
        query = """
            MATCH (m:DbtModel)-[r:BUILDS]->(p)
            WHERE toLower(m.id) = toLower($model_id)
            RETURN
                labels(p)[0] AS type,
                p.fqn AS fqn,
                p.database AS database,
                p.schema_name AS schema_name,
                p.relation_name AS relation_name,
                p.warehouse_type AS warehouse_type,
                p.environment AS environment,
                p.materialization_strategy AS materialization_strategy,
                p.updated_at AS updated_at
            ORDER BY p.environment
        """
        result = self.execute_raw_query(query, params={"model_id": model_id})

        materializations = [ModelMaterialization(**row) for row in result.rows]

        return ModelMaterializationsResult(
            model_id=model_id,
            materializations=materializations
        )

    def find_upstream(self, node_id: str, depth: int = 1) -> List[str]:
        """Find upstream dependencies via DEPENDS_ON edges.

        Args:
            node_id: DbtModel ID to find upstream dependencies for
            depth: Maximum number of hops to traverse (default: 1, max: 10)

        Returns:
            List of upstream DbtModel and DbtSource IDs

        Raises:
            ValueError: If depth is less than 1 or greater than 10
        """
        # Validate depth to prevent invalid queries or performance issues.
        # Max depth of 10 is chosen because:
        # 1. Most real-world DAGs rarely exceed 10 levels of dependencies
        # 2. Cypher variable-length paths grow exponentially in cost
        # 3. Beyond 10 hops, results become less meaningful for disambiguation
        if depth < 1:
            raise ValueError(f"depth must be at least 1, got {depth}")
        if depth > 10:
            raise ValueError(f"depth must be at most 10, got {depth}")

        query = f"""
            MATCH (m:DbtModel)-[:DEPENDS_ON*1..{depth}]->(upstream)
            WHERE toLower(m.id) = toLower($node_id)
              AND (upstream:DbtModel OR upstream:DbtSource)
            RETURN DISTINCT upstream.id AS upstream_id
        """
        try:
            result = self.execute_raw_query(query, params={"node_id": node_id})
            return [row.get("upstream_id") for row in result.rows if row.get("upstream_id")]
        except Exception as e:
            logger.error(f"Error finding upstream dependencies for '{node_id}': {e}")
            return []
