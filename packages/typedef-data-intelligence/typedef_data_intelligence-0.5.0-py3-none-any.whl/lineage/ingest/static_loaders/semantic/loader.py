"""Semantic analysis loader - integrates analysis pipeline with lineage storage."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Tuple

from lineage.backends.lineage.models.base import BaseNode, GraphEdge, NodeIdentifier
from lineage.backends.lineage.models.edges import (
    HasAuditFinding,
    HasAuditPatch,
    HasDimension,
    HasFact,
    HasFilter,
    HasGrainToken,
    HasGroupingScope,
    HasInferredSemantics,
    HasJoinEdge,
    HasMeasure,
    HasOutputShape,
    HasRelation,
    HasSegment,
    HasSelectItem,
    HasTimeAttribute,
    HasTimeScope,
    HasTimeWindow,
    HasWindowFunction,
    HasWindowScope,
    InferredJoinsWith,
    JoinsLeftModel,
    JoinsRightModel,
    ResolvesToModel,
)
from lineage.backends.lineage.models.semantic_analysis import (
    InferredAuditFinding,
    InferredAuditPatch,
    InferredDimension,
    InferredFact,
    InferredFilter,
    InferredGrainToken,
    InferredGroupingScope,
    InferredMeasure,
    InferredOutputShape,
    InferredRelation,
    InferredSegment,
    InferredSelectItem,
    InferredSemanticModel,
    InferredTimeScope,
    InferredWindowScope,
    TimeAttribute,
    TimeWindow,
    WindowFunction,
)
from lineage.backends.lineage.models.semantic_analysis import (
    JoinEdge as JoinEdgeNode,
)
from lineage.backends.types import NodeLabel

logger = logging.getLogger(__name__)

_PHYSICAL_RELATION_LABELS: tuple[str, ...] = (
    NodeLabel.PHYSICAL_TABLE.value,
    NodeLabel.PHYSICAL_VIEW.value,
    NodeLabel.PHYSICAL_MATERIALIZED_VIEW.value,
    NodeLabel.PHYSICAL_INCREMENTAL_MODEL.value,
    NodeLabel.PHYSICAL_EPHEMERAL.value,
)

if TYPE_CHECKING:
    from lineage.backends.lineage.protocol import LineageStorage


class SemanticLoader:
    """Loads semantic analysis results into the typed graph."""

    def __init__(self, storage: LineageStorage, analysis_version: str = "1.0.0"):
        """Initialize the SemanticLoader.

        Args:
            storage: Lineage storage backend
            analysis_version: Version of the analysis
        """
        self.storage = storage
        self.analysis_version = analysis_version

    def _as_dict(self, value: object, model_id: str, field_name: str) -> dict:
        if isinstance(value, dict):
            return value
        if value is None:
            return {}
        logger.warning(
            "Skipping %s for %s: expected dict, got %s",
            field_name,
            model_id,
            type(value).__name__,
        )
        return {}

    def _as_list(self, value: object, model_id: str, field_name: str) -> list:
        if isinstance(value, list):
            return value
        if value is None:
            return []
        logger.warning(
            "Skipping %s for %s: expected list, got %s",
            field_name,
            model_id,
            type(value).__name__,
        )
        return []

    def load_analysis_results(
        self,
        model_id: str,
        analysis_results: dict,
    ) -> None:
        """Load semantic analysis results into storage for a single model.

        Collects all nodes and edges in memory, then passes to storage.bulk_load()
        for optimized batch loading.

        Args:
            model_id: dbt unique_id of the model (e.g., "model.demo_finance.fct_arr_reporting_monthly")
            analysis_results: Dictionary with analysis pass results
        """
        # Collect all nodes and edges in memory
        nodes, edges = self._collect_nodes_and_edges(model_id, analysis_results)

        # Pass to storage for bulk loading
        self.storage.bulk_load(nodes, edges)

    def _collect_nodes_and_edges(
        self,
        model_id: str,
        analysis_results: dict,
    ) -> Tuple[List[BaseNode], List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]]]:
        """Collect all nodes and edges for a model's semantic analysis.

        This method orchestrates the collection of all semantic analysis nodes and edges
        without writing to storage. All nodes/edges are collected in memory and returned
        for bulk loading.

        Args:
            model_id: dbt unique_id of the model
            analysis_results: Dictionary with analysis pass results

        Returns:
            Tuple of (all_nodes, all_edges) where:
            - all_nodes: List of all Pydantic node objects
            - all_edges: List of (from_node, to_node, edge) tuples
        """
        all_nodes: List[BaseNode] = []
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]] = []

        # Build model resolution lookup for join edges and relations
        # This pre-fetches data needed for alias resolution
        model_lookup, collisions, id_to_label = self._build_model_resolution_lookup()

        # Get upstream deps for disambiguation when collisions exist
        upstream_deps: set[str] = set()
        if collisions:
            upstream_deps = set(self.storage.find_upstream(model_id, depth=1))

        # 1. Container node first (InferredSemanticModel)
        semantic_model = self._collect_semantic_analysis(model_id, analysis_results, all_nodes, all_edges)

        # 2. Formalized semantic nodes (Passes 1-9)
        self._collect_relations(model_id, analysis_results, semantic_model.id, model_lookup, collisions, id_to_label, upstream_deps, all_nodes, all_edges)
        # Note: Column refs removed - they're internal tracking data, not useful for lineage queries
        self._collect_join_edges(model_id, analysis_results, semantic_model.id, model_lookup, collisions, id_to_label, upstream_deps, all_nodes, all_edges)
        self._collect_filters(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_grouping_scopes(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_time_scopes(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_window_scopes(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_output_shapes(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_audit_findings(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)

        # 3. Business semantics (Pass 10)
        self._collect_business_semantics(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_business_facts(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_business_segments(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)

        # 4. Grain tokens (Pass 10a)
        self._collect_grain_tokens(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)

        # 5. Legacy nodes (for backward compatibility)
        self._collect_time_window(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_time_attributes(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)
        self._collect_window_functions(model_id, analysis_results, semantic_model.id, all_nodes, all_edges)

        return all_nodes, all_edges

    def _build_model_resolution_lookup(self) -> tuple[dict[str, tuple[str, NodeLabel]], dict[str, set[str]]]:
        """Pre-build a lookup dictionary for resolving relation names to model IDs.

        This queries the graph once to get DbtModel names and their PhysicalRelation
        data (via BUILDS edges), then builds a lookup dictionary. This avoids executing
        individual queries during collection for each relation/join.

        Returns:
            Tuple of (lookup, collisions) where:
            - lookup: Dictionary mapping relation names (various formats) to (model_id, label)
            - collisions: Dictionary mapping keys to sets of all model IDs when >1 model maps to the same key
        """
        query = """
            MATCH (m:DbtModel)-[:BUILDS]->(p)
            RETURN m.id AS id,
                   m.name AS name,
                   p.relation_name AS relation_name,
                   p.database AS database,
                   p.schema_name AS schema_name
        """

        result = self.storage.execute_raw_query(query)

        lookup: dict[str, tuple[str, NodeLabel]] = {}
        collisions: dict[str, set[str]] = {}
        id_to_label: dict[str, NodeLabel] = {}  # Reverse lookup for collision resolution

        def _insert(key: str, model_id: str, label: NodeLabel) -> None:
            existing = lookup.get(key)
            if existing and existing[0] != model_id:
                collisions.setdefault(key, {existing[0]}).add(model_id)
            lookup[key] = (model_id, label)
            id_to_label[model_id] = label  # Track label for each model_id

        for row in result.rows:
            model_id = row.get("id")
            name = self._normalize_identifier(row.get("name"))
            relation_name = self._normalize_identifier(row.get("relation_name"))
            database = self._normalize_identifier(row.get("database"))
            schema_name = self._normalize_identifier(row.get("schema_name"))

            if model_id:
                # Map by model name
                if name:
                    _insert(name.lower(), model_id, NodeLabel.DBT_MODEL)

                # Map by relation_name (base table name)
                if relation_name:
                    _insert(relation_name.lower(), model_id, NodeLabel.DBT_MODEL)

                # Build FQN variations for lookup
                if relation_name:
                    # database.schema.table
                    if database and schema_name:
                        fqn = f"{database}.{schema_name}.{relation_name}".lower()
                        _insert(fqn, model_id, NodeLabel.DBT_MODEL)

                    # schema.table
                    if schema_name:
                        schema_qualified = f"{schema_name}.{relation_name}".lower()
                        _insert(schema_qualified, model_id, NodeLabel.DBT_MODEL)

        # Add sources by name (logical sources don't carry schema/database here)
        source_query = """
            MATCH (s:DbtSource)
            RETURN s.id AS id, s.name AS name
        """
        try:
            source_result = self.storage.execute_raw_query(source_query)
            for row in source_result.rows:
                source_id = row.get("id")
                source_name = self._normalize_identifier(row.get("name"))
                if source_id and source_name:
                    _insert(source_name.lower(), source_id, NodeLabel.DBT_SOURCE)
        except Exception:
            logger.debug("Source lookup query failed; continuing without source mappings", exc_info=True)

        return lookup, collisions, id_to_label

    def _collect_semantic_analysis(
        self,
        model_id: str,
        results: dict,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> InferredSemanticModel:
        """Collect InferredSemanticModel container and link to DbtModel.

        Returns:
            The created InferredSemanticModel node (needed by other collection methods)
        """
        # Extract summary flags from results
        business_sem = self._as_dict(
            results.get("business_semantics"), model_id, "business_semantics"
        )
        time_analysis = self._as_dict(
            results.get("time_analysis"), model_id, "time_analysis"
        )
        grouping = self._as_dict(
            results.get("grouping_analysis"), model_id, "grouping_analysis"
        )
        windows = self._as_dict(
            results.get("window_analysis"), model_id, "window_analysis"
        )

        # Extract analysis summary (if available)
        analysis_summary = results.get("analysis_summary")

        # Create InferredSemanticModel container using Pydantic model
        semantic_model = InferredSemanticModel(
            name=model_id.split(".")[-1],  # Extract model name from unique_id
            model_id=model_id,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            analysis_version=self.analysis_version,
            has_aggregations=grouping.get("is_aggregated", False),
            has_time_window=time_analysis.get("time_scope") is not None,
            has_window_functions=len(windows.get("windows", [])) > 0,
            grain_human=business_sem.get("grain_human", ""),
            intent=business_sem.get("intent", "unknown"),
            analysis_summary=analysis_summary,
        )

        # Add to collection
        all_nodes.append(semantic_model)

        # Link DbtModel → InferredSemanticModel using typed edge
        model_identifier = NodeIdentifier(id=model_id, node_label=NodeLabel.DBT_MODEL)
        all_edges.append((
            model_identifier,
            semantic_model,
            HasInferredSemantics(),
        ))

        return semantic_model

    def _collect_business_semantics(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredMeasure and InferredDimension nodes attached to InferredSemanticModel."""
        business_sem = self._as_dict(
            results.get("business_semantics"), model_id, "business_semantics"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        # Collect measures
        for measure in business_sem.get("measures", []):
            measure_node = InferredMeasure(
                name=measure.get("name", ""),
                semantic_model_id=semantic_model_id,
                expr=measure.get("expr", ""),
                agg_function=measure.get("default_agg", "OTHER"),
                source_alias=measure.get("source_alias", ""),
            )

            all_nodes.append(measure_node)
            all_edges.append((
                semantic_model_identifier,
                measure_node,
                HasMeasure(output_alias=measure.get("name", "")),
            ))

        # Collect dimensions
        for dimension in business_sem.get("dimensions", []):
            dimension_node = InferredDimension(
                name=dimension.get("name", ""),
                semantic_model_id=semantic_model_id,
                source=dimension.get("source", ""),
                is_pii=dimension.get("pii", False) or False,
            )

            all_nodes.append(dimension_node)
            all_edges.append((
                semantic_model_identifier,
                dimension_node,
                HasDimension(output_alias=dimension.get("name", "")),
            ))

    def _collect_business_facts(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredFact nodes for fact table attributes."""
        business_sem = self._as_dict(
            results.get("business_semantics"), model_id, "business_semantics"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        # Collect facts
        for fact in business_sem.get("facts", []):
            fact_node = InferredFact(
                name=fact.get("name", ""),
                semantic_model_id=semantic_model_id,
                source=fact.get("source", ""),
                description=f"Grain-defining: {fact.get('is_grain_defining', True)}",
            )

            all_nodes.append(fact_node)
            all_edges.append((
                semantic_model_identifier,
                fact_node,
                HasFact(),
            ))

    def _collect_business_segments(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredSegment nodes for filter rules."""
        business_sem = self._as_dict(
            results.get("business_semantics"), model_id, "business_semantics"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for segment in business_sem.get("segments", []):
            segment_node = InferredSegment(
                name=segment.get("name", ""),
                semantic_model_id=semantic_model_id,
                rule=segment.get("rule", ""),
                clause="WHERE",
            )

            all_nodes.append(segment_node)
            all_edges.append((
                semantic_model_identifier,
                segment_node,
                HasSegment(),
            ))

    def _collect_join_edges(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        model_lookup: dict[str, tuple[str, NodeLabel]],
        collisions: dict[str, set[str]],
        id_to_label: dict[str, NodeLabel],
        upstream_deps: set[str],
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect JoinEdge nodes for each join in the model and resolve to models."""
        join_analysis = self._as_dict(
            results.get("join_analysis"), model_id, "join_analysis"
        )
        relation_analysis = self._as_dict(
            results.get("relation_analysis"), model_id, "relation_analysis"
        )

        # Build alias -> relation mapping for resolution
        alias_to_relation = {}
        for rel in relation_analysis.get("relations", []):
            alias = rel.get("alias")
            if alias:
                alias_to_relation[alias] = rel
        cte_resolution, subquery_resolution = self._build_cte_and_subquery_resolution(
            relation_analysis.get("relations", [])
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        joins = self._as_list(join_analysis.get("joins"), model_id, "join_analysis.joins")
        logger.debug(f"Processing {len(joins)} joins for {model_id}")

        resolved_count = 0
        partial_count = 0
        unresolved_count = 0
        unresolved_samples: list[str] = []

        for join in joins:
            if not isinstance(join, dict):
                logger.warning(
                    "Skipping join for %s: expected dict, got %s",
                    model_id,
                    type(join).__name__,
                )
                continue
            left_alias = join.get("left", "")
            right_alias = join.get("right", "")

            # Determine scope from relation analysis
            scope = "outer"  # Default
            left_rel = alias_to_relation.get(left_alias, {})
            if left_rel:
                scope = left_rel.get("scope", "outer")

            # Try to resolve aliases to models using pre-built lookup
            left_resolution = self._resolve_alias_via_lookup(
                left_alias,
                alias_to_relation,
                model_lookup,
                cte_resolution=cte_resolution,
                subquery_resolution=subquery_resolution,
                collisions=collisions,
                id_to_label=id_to_label,
                upstream_deps=upstream_deps,
            )
            right_resolution = self._resolve_alias_via_lookup(
                right_alias,
                alias_to_relation,
                model_lookup,
                cte_resolution=cte_resolution,
                subquery_resolution=subquery_resolution,
                collisions=collisions,
                id_to_label=id_to_label,
                upstream_deps=upstream_deps,
            )

            left_model_id = left_resolution[0] if left_resolution else None
            right_model_id = right_resolution[0] if right_resolution else None
            left_label = left_resolution[1] if left_resolution else None
            right_label = right_resolution[1] if right_resolution else None

            # Track resolution statistics
            if left_model_id and right_model_id:
                resolved_count += 1
                logger.debug(f"  ✓ Resolved join: {left_alias} -> {right_alias}")
            elif left_model_id or right_model_id:
                partial_count += 1
                logger.debug(f"  ⚠ Partial join: {left_alias} ({left_model_id or 'UNRESOLVED'}) -> {right_alias} ({right_model_id or 'UNRESOLVED'})")
            else:
                unresolved_count += 1
                logger.debug(f"  ✗ Unresolved join: {left_alias} -> {right_alias}")
                if len(unresolved_samples) < 5:
                    left_rel = alias_to_relation.get(left_alias, {}) if left_alias else {}
                    right_rel = alias_to_relation.get(right_alias, {}) if right_alias else {}
                    unresolved_samples.append(
                        (
                            f"{left_alias or '?'}({left_rel.get('base') or left_rel.get('name') or 'unknown'})"
                            f" -> {right_alias or '?'}({right_rel.get('base') or right_rel.get('name') or 'unknown'})"
                        )
                    )

            # Create join node with resolved IDs
            join_node = JoinEdgeNode(
                name=f"{left_alias}_{right_alias}",
                semantic_model_id=semantic_model_id,
                join_type=join.get("type", "INNER"),
                left_alias=left_alias,
                right_alias=right_alias,
                equi_condition=join.get("equi_condition", ""),
                effective_type=join.get("effective_type", join.get("type", "INNER")),
                normalized_equi_condition=join.get(
                    "normalized_equi_condition", join.get("equi_condition", "")
                ),
                scope=scope,
                left_model_id=left_model_id,
                right_model_id=right_model_id,
                confidence="high" if (left_model_id and right_model_id) else ("medium" if (left_model_id or right_model_id) else "low"),
            )

            all_nodes.append(join_node)

            # Link InferredSemanticModel -> JoinEdge
            all_edges.append((
                semantic_model_identifier,
                join_node,
                HasJoinEdge(),
            ))

            # Create edges to resolved models
            if left_model_id or right_model_id:
                join_edge_identifier = NodeIdentifier(id=join_node.id, node_label=NodeLabel.JOIN_EDGE)

                if left_model_id:
                    left_model_identifier = NodeIdentifier(
                        id=left_model_id,
                        node_label=left_label or NodeLabel.DBT_MODEL,
                    )
                    all_edges.append((
                        left_model_identifier,
                        join_edge_identifier,
                        InferredJoinsWith(confidence=join_node.confidence),
                    ))
                    all_edges.append((
                        join_edge_identifier,
                        left_model_identifier,
                        JoinsLeftModel(),
                    ))

                if right_model_id:
                    right_model_identifier = NodeIdentifier(
                        id=right_model_id,
                        node_label=right_label or NodeLabel.DBT_MODEL,
                    )
                    all_edges.append((
                        right_model_identifier,
                        join_edge_identifier,
                        InferredJoinsWith(confidence=join_node.confidence),
                    ))
                    all_edges.append((
                        join_edge_identifier,
                        right_model_identifier,
                        JoinsRightModel(),
                    ))

        # Log resolution summary
        if joins:
            logger.info(f"Join resolution for {model_id}: {resolved_count} fully resolved, {partial_count} partial, {unresolved_count} unresolved ({len(joins)} total)")
            if unresolved_samples:
                logger.debug(
                    "Join resolution unresolved samples for %s: %s",
                    model_id,
                    ", ".join(unresolved_samples),
                )

    def _normalize_identifier(self, value: str | None) -> str:
        """Normalize identifiers by stripping common quoting and whitespace."""
        if value is None:
            return ""
        text = str(value).strip()
        if not text:
            return ""
        if (text.startswith('"') and text.endswith('"')) or (
            text.startswith("`") and text.endswith("`")
        ):
            return text[1:-1]
        if text.startswith("[") and text.endswith("]"):
            return text[1:-1]
        return text

    def _build_cte_and_subquery_resolution(
        self,
        relations: list[dict],
    ) -> tuple[
        dict[str, tuple[str, str | None, str | None]],
        dict[str, tuple[str, str | None, str | None]],
    ]:
        """Build CTE/subquery alias resolution from relation analysis.

        We only resolve when a scope maps to a single underlying base relation.
        """
        # TODO: add optional heuristics for multi-base CTE/subquery resolution (dominant table,
        # join predicate scoring, or explicit source hints) once we have feedback on accuracy.
        cte_candidates: dict[str, set[tuple[str, str | None, str | None]]] = {}
        subquery_candidates: dict[str, set[tuple[str, str | None, str | None]]] = {}

        for rel in relations:
            kind = rel.get("kind")
            if kind not in ("table", "view"):
                continue
            scope = rel.get("scope") or ""
            if not scope.startswith("cte:") and not scope.startswith("subquery:"):
                continue

            base = self._normalize_identifier(rel.get("base") or rel.get("name"))
            schema_name = self._normalize_identifier(rel.get("schema_name") or rel.get("schema")) or None
            catalog = self._normalize_identifier(rel.get("catalog") or rel.get("database")) or None
            if not base:
                continue

            resolved = (base, schema_name, catalog)
            if scope.startswith("cte:"):
                cte_name = self._normalize_identifier(scope.split(":", 1)[1]).lower()
                cte_candidates.setdefault(cte_name, set()).add(resolved)
            else:
                subquery_alias = self._normalize_identifier(scope.split(":", 1)[1]).lower()
                subquery_candidates.setdefault(subquery_alias, set()).add(resolved)

        cte_resolution = {
            key: next(iter(values))
            for key, values in cte_candidates.items()
            if len(values) == 1
        }
        subquery_resolution = {
            key: next(iter(values))
            for key, values in subquery_candidates.items()
            if len(values) == 1
        }
        return cte_resolution, subquery_resolution

    def _resolve_alias_via_lookup(
        self,
        alias: str,
        alias_to_relation: dict,
        model_lookup: dict[str, tuple[str, NodeLabel]],
        *,
        cte_resolution: dict[str, tuple[str, str | None, str | None]] | None = None,
        subquery_resolution: dict[str, tuple[str, str | None, str | None]] | None = None,
        collisions: dict[str, set[str]] | None = None,
        id_to_label: dict[str, NodeLabel] | None = None,
        upstream_deps: set[str] | None = None,
    ) -> tuple[str, NodeLabel] | None:
        """Resolve join alias to DbtModel ID using logic-only lookup.

        This ensures that join resolution is physically agnostic and consistent
        with Pass 1: Relation Analysis. When multiple models map to the same key
        (collisions), upstream DEPENDS_ON edges are used to disambiguate.
        """
        rel = alias_to_relation.get(alias, {})
        if not rel or rel.get("kind") not in ("table", "view", "cte", "subquery"):
            return None

        # Build name components
        base = self._normalize_identifier(rel.get("base") or rel.get("name"))
        schema_name = self._normalize_identifier(rel.get("schema_name") or rel.get("schema"))

        if rel.get("kind") == "cte" and cte_resolution:
            resolved = cte_resolution.get(base.lower())
            if resolved:
                base, schema_name, _catalog = resolved
        if rel.get("kind") == "subquery" and subquery_resolution:
            resolved = subquery_resolution.get(alias.lower())
            if resolved:
                base, schema_name, _catalog = resolved

        if not base:
            return None

        # Build lookup keys - try schema-qualified first, then base-only (consistent with _collect_relations)
        lookup_keys = []
        if schema_name and base:
            lookup_keys.append(f"{schema_name}.{base}".lower())
        if base:
            lookup_keys.append(base.lower())

        # Try each key in order of specificity, disambiguating via upstream deps when collisions exist
        for key in lookup_keys:
            if key in model_lookup:
                result = model_lookup[key]
                if collisions and key in collisions:
                    candidate_id = result[0]
                    if upstream_deps:
                        # Have upstream deps to use for disambiguation
                        if candidate_id not in upstream_deps:
                            # Current match isn't a dep — check if any collision candidate is
                            for alt_id in collisions[key]:
                                if alt_id in upstream_deps:
                                    # Get the correct label for alt_id from id_to_label
                                    alt_label = id_to_label.get(alt_id, result[1]) if id_to_label else result[1]
                                    return (alt_id, alt_label)
                            # No dep match found; log and fall through to current match
                            logger.warning(
                                "Ambiguous resolution for '%s': candidates %s, "
                                "none in upstream deps for model",
                                key,
                                collisions[key] | {candidate_id},
                            )
                    else:
                        # No upstream deps to disambiguate with; log warning
                        logger.warning(
                            "Ambiguous resolution for '%s': candidates %s, "
                            "no upstream deps available for disambiguation (using first match)",
                            key,
                            collisions[key] | {candidate_id},
                        )
                return result

        return None

    def _collect_time_window(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect TimeWindow node if model has time constraints (legacy)."""
        time_analysis = self._as_dict(
            results.get("time_analysis"), model_id, "time_analysis"
        )
        time_scope = time_analysis.get("normalized_time_scope")
        if time_scope is not None and not isinstance(time_scope, dict):
            logger.warning(
                "Skipping time window for %s: normalized_time_scope is not a dict",
                model_id,
            )
            return

        if time_scope:
            semantic_model_identifier = NodeIdentifier(
                id=semantic_model_id,
                node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
            )

            column_qualified = time_scope.get("column", "")
            time_window_node = TimeWindow(
                name=column_qualified,  # Use column name
                semantic_model_id=semantic_model_id,
                column_qualified=column_qualified,
                start_value=time_scope.get("start", ""),
                end_value=time_scope.get("end", ""),
                end_exclusive=time_scope.get("end_exclusive", True),
                granularity=self._infer_granularity(column_qualified),
            )

            all_nodes.append(time_window_node)
            all_edges.append((
                semantic_model_identifier,
                time_window_node,
                HasTimeWindow(),
            ))

    def _collect_time_attributes(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect TimeAttribute nodes for time-related filters (legacy)."""
        time_analysis = self._as_dict(
            results.get("time_analysis"), model_id, "time_analysis"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for _idx, time_column in enumerate(
            self._as_list(time_analysis.get("time_columns"), model_id, "time_analysis.time_columns")
        ):
            time_attr_node = TimeAttribute(
                name=time_column,  # Use column name
                semantic_model_id=semantic_model_id,
                column_qualified=time_column,
                filter_expr="",
            )

            all_nodes.append(time_attr_node)
            all_edges.append((
                semantic_model_identifier,
                time_attr_node,
                HasTimeAttribute(),
            ))

    def _collect_window_functions(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect WindowFunction nodes (legacy)."""
        window_analysis = self._as_dict(
            results.get("window_analysis"), model_id, "window_analysis"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for _idx, window in enumerate(
            self._as_list(window_analysis.get("windows"), model_id, "window_analysis.windows")
        ):
            if not isinstance(window, dict):
                logger.warning(
                    "Skipping window function for %s: expected dict, got %s",
                    model_id,
                    type(window).__name__,
                )
                continue
            window_func = window.get("func", "")
            window_node = WindowFunction(
                name=window_func,  # Use function name
                semantic_model_id=semantic_model_id,
                func=window_func,
                partition_by=",".join(window.get("partition_by", [])),
                order_by=",".join(window.get("order_by", [])),
                frame=window.get("frame", ""),
            )

            all_nodes.append(window_node)
            all_edges.append((
                semantic_model_identifier,
                window_node,
                HasWindowFunction(),
            ))

    def _collect_relations(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        model_lookup: dict[str, tuple[str, NodeLabel]],
        collisions: dict[str, set[str]],
        id_to_label: dict[str, NodeLabel],
        upstream_deps: set[str],
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredRelation nodes for Pass 1: Relation Analysis."""
        relation_analysis = self._as_dict(
            results.get("relation_analysis"), model_id, "relation_analysis"
        )
        relations = self._as_list(
            relation_analysis.get("relations"), model_id, "relation_analysis.relations"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for rel in relations:
            if not isinstance(rel, dict):
                logger.warning(
                    "Skipping relation for %s: expected dict, got %s",
                    model_id,
                    type(rel).__name__,
                )
                continue
            # Try to resolve relation to DbtModel using lookup
            resolved_model_id = None
            resolved_model_label = None
            if rel.get("kind") in ("table", "view"):
                # Build lookup keys - prefer logic-only names for agnosticism
                base = self._normalize_identifier(rel.get("base") or rel.get("name"))
                schema_name = self._normalize_identifier(rel.get("schema_name") or rel.get("schema"))

                lookup_keys = []
                if schema_name and base:
                    lookup_keys.append(f"{schema_name}.{base}".lower())
                if base:
                    lookup_keys.append(base.lower())

                # Try each key, disambiguating via upstream deps when collisions exist
                for key in lookup_keys:
                    if key in model_lookup:
                        candidate_id, candidate_label = model_lookup[key]
                        if collisions and key in collisions:
                            if upstream_deps:
                                # Have upstream deps to use for disambiguation
                                if candidate_id not in upstream_deps:
                                    # Current match isn't a dep — check collision candidates
                                    for alt_id in collisions[key]:
                                        if alt_id in upstream_deps:
                                            resolved_model_id = alt_id
                                            # Get the correct label for alt_id from id_to_label
                                            resolved_model_label = id_to_label.get(alt_id, candidate_label)
                                            break
                                    else:
                                        # No dep match; use current candidate anyway
                                        resolved_model_id = candidate_id
                                        resolved_model_label = candidate_label
                                        logger.warning(
                                            "Ambiguous resolution for '%s' in %s: candidates %s, "
                                            "none in upstream deps",
                                            key,
                                            model_id,
                                            collisions[key] | {candidate_id},
                                        )
                                else:
                                    resolved_model_id = candidate_id
                                    resolved_model_label = candidate_label
                            else:
                                # No upstream deps to disambiguate with; log warning
                                resolved_model_id = candidate_id
                                resolved_model_label = candidate_label
                                logger.warning(
                                    "Ambiguous resolution for '%s' in %s: candidates %s, "
                                    "no upstream deps available for disambiguation (using first match)",
                                    key,
                                    model_id,
                                    collisions[key] | {candidate_id},
                                )
                        else:
                            resolved_model_id = candidate_id
                            resolved_model_label = candidate_label
                        break

            relation_node = InferredRelation(
                name=rel.get("alias", ""),
                semantic_model_id=semantic_model_id,
                alias=rel.get("alias", ""),
                base=rel.get("base", ""),
                kind=rel.get("kind", "table"),
                scope=rel.get("scope", "outer"),
                is_temp=rel.get("is_temp", False),
                confidence="high" if resolved_model_id else "low",
            )

            all_nodes.append(relation_node)
            all_edges.append((
                semantic_model_identifier,
                relation_node,
                HasRelation(),
            ))

            # If resolved, create edge to DbtModel
            if resolved_model_id:
                model_identifier = NodeIdentifier(
                    id=resolved_model_id,
                    node_label=resolved_model_label or NodeLabel.DBT_MODEL,
                )
                relation_identifier = NodeIdentifier(
                    id=relation_node.id,
                    node_label=NodeLabel.INFERRED_RELATION
                )
                all_edges.append((
                    relation_identifier,
                    model_identifier,
                    ResolvesToModel(confidence="high"),
                ))

    def _collect_filters(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredFilter nodes for Pass 4: Filter Analysis."""
        filter_analysis = self._as_dict(
            results.get("filter_analysis"), model_id, "filter_analysis"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        # Collect WHERE filters
        for predicate in self._as_list(
            filter_analysis.get("where"), model_id, "filter_analysis.where"
        ):
            filter_node = InferredFilter(
                name=predicate[:50] + "..." if len(predicate) > 50 else predicate,
                semantic_model_id=semantic_model_id,
                predicate=predicate,
                clause="WHERE",
                scope="outer",  # WHERE is typically outer scope
            )

            all_nodes.append(filter_node)
            all_edges.append((
                semantic_model_identifier,
                filter_node,
                HasFilter(),
            ))

        # Collect HAVING filters
        for predicate in self._as_list(
            filter_analysis.get("having"), model_id, "filter_analysis.having"
        ):
            filter_node = InferredFilter(
                name=predicate[:50] + "..." if len(predicate) > 50 else predicate,
                semantic_model_id=semantic_model_id,
                predicate=predicate,
                clause="HAVING",
                scope="outer",
            )

            all_nodes.append(filter_node)
            all_edges.append((
                semantic_model_identifier,
                filter_node,
                HasFilter(),
            ))

        # Collect QUALIFY filters
        for predicate in self._as_list(
            filter_analysis.get("qualify"), model_id, "filter_analysis.qualify"
        ):
            filter_node = InferredFilter(
                name=predicate[:50] + "..." if len(predicate) > 50 else predicate,
                semantic_model_id=semantic_model_id,
                predicate=predicate,
                clause="QUALIFY",
                scope="outer",
            )

            all_nodes.append(filter_node)
            all_edges.append((
                semantic_model_identifier,
                filter_node,
                HasFilter(),
            ))

    def _collect_grouping_scopes(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredGroupingScope and InferredSelectItem nodes for Pass 5: Grouping Analysis."""
        grouping_by_scope = self._as_list(
            results.get("grouping_by_scope"), model_id, "grouping_by_scope"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for scope_data in grouping_by_scope:
            if not isinstance(scope_data, dict):
                logger.warning(
                    "Skipping grouping scope for %s: expected dict, got %s",
                    model_id,
                    type(scope_data).__name__,
                )
                continue
            scope = scope_data.get("scope", "outer")
            grouping_data = scope_data.get("grouping_for_scope") or scope_data.get("analysis", {})
            if not isinstance(grouping_data, dict):
                logger.warning(
                    "Skipping grouping data for %s: expected dict, got %s",
                    model_id,
                    type(grouping_data).__name__,
                )
                continue

            grouping_scope_node = InferredGroupingScope(
                name=scope,
                semantic_model_id=semantic_model_id,
                scope=scope,
                is_aggregated=grouping_data.get("is_aggregated", False),
                group_by=json.dumps(grouping_data.get("group_by", [])),
                result_grain=json.dumps(grouping_data.get("result_grain", [])),
                measures=json.dumps(grouping_data.get("measures", [])),
            )

            all_nodes.append(grouping_scope_node)
            all_edges.append((
                semantic_model_identifier,
                grouping_scope_node,
                HasGroupingScope(),
            ))

            # Collect SELECT items
            for select_item in self._as_list(
                grouping_data.get("select"), model_id, "grouping_by_scope.select"
            ):
                if not isinstance(select_item, dict):
                    logger.warning(
                        "Skipping select item for %s: expected dict, got %s",
                        model_id,
                        type(select_item).__name__,
                    )
                    continue
                select_node = InferredSelectItem(
                    name=select_item.get("alias", ""),
                    semantic_model_id=semantic_model_id,
                    scope=scope,
                    expr=select_item.get("expr", ""),
                    alias=select_item.get("alias", ""),
                    kind=select_item.get("kind", "dimension"),
                    source_aliases=json.dumps(select_item.get("source_aliases", [])),
                )

                all_nodes.append(select_node)
                grouping_scope_identifier = NodeIdentifier(
                    id=grouping_scope_node.id,
                    node_label=NodeLabel.INFERRED_GROUPING_SCOPE
                )
                all_edges.append((
                    grouping_scope_identifier,
                    select_node,
                    HasSelectItem(),
                ))

    def _collect_time_scopes(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredTimeScope nodes for Pass 6: Time Analysis."""
        time_by_scope = self._as_list(
            results.get("time_by_scope"), model_id, "time_by_scope"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for scope_data in time_by_scope:
            if not isinstance(scope_data, dict):
                logger.warning(
                    "Skipping time scope for %s: expected dict, got %s",
                    model_id,
                    type(scope_data).__name__,
                )
                continue
            scope = scope_data.get("scope", "outer")
            time_data = scope_data.get("time_for_scope") or {}
            if not isinstance(time_data, dict):
                logger.warning(
                    "Skipping time data for %s: expected dict, got %s",
                    model_id,
                    type(time_data).__name__,
                )
                continue

            time_scope_node = InferredTimeScope(
                name=scope,
                semantic_model_id=semantic_model_id,
                scope=scope,
                time_scope=json.dumps(time_data.get("time_scope")) if time_data.get("time_scope") else None,
                normalized_time_scope=json.dumps(time_data.get("normalized_time_scope")) if time_data.get("normalized_time_scope") else None,
                time_buckets=json.dumps(time_data.get("time_buckets", [])),
                time_columns=json.dumps(time_data.get("time_columns", [])),
            )

            all_nodes.append(time_scope_node)
            all_edges.append((
                semantic_model_identifier,
                time_scope_node,
                HasTimeScope(),
            ))

    def _collect_window_scopes(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredWindowScope nodes for Pass 7: Window Analysis."""
        window_by_scope = self._as_list(
            results.get("window_by_scope"), model_id, "window_by_scope"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for scope_data in window_by_scope:
            if not isinstance(scope_data, dict):
                logger.warning(
                    "Skipping window scope for %s: expected dict, got %s",
                    model_id,
                    type(scope_data).__name__,
                )
                continue
            scope = scope_data.get("scope", "outer")
            window_json = scope_data.get("window_analysis_json") or scope_data.get("windows", "[]")

            # Parse if string, otherwise use as-is
            if isinstance(window_json, str):
                try:
                    windows = json.loads(window_json)
                except json.JSONDecodeError:
                    windows = []
            else:
                windows = window_json

            window_scope_node = InferredWindowScope(
                name=scope,
                semantic_model_id=semantic_model_id,
                scope=scope,
                windows=json.dumps(windows),
            )

            all_nodes.append(window_scope_node)
            all_edges.append((
                semantic_model_identifier,
                window_scope_node,
                HasWindowScope(),
            ))

    def _collect_output_shapes(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredOutputShape nodes for Pass 8: Output Shape Analysis."""
        output_by_scope = self._as_list(
            results.get("output_by_scope"), model_id, "output_by_scope"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for scope_data in output_by_scope:
            if not isinstance(scope_data, dict):
                logger.warning(
                    "Skipping output scope for %s: expected dict, got %s",
                    model_id,
                    type(scope_data).__name__,
                )
                continue
            scope = scope_data.get("scope", "outer")
            output_data = scope_data.get("output_for_scope") or {}
            if not isinstance(output_data, dict):
                logger.warning(
                    "Skipping output data for %s: expected dict, got %s",
                    model_id,
                    type(output_data).__name__,
                )
                continue

            output_shape_node = InferredOutputShape(
                name=scope,
                semantic_model_id=semantic_model_id,
                scope=scope,
                order_by=json.dumps(output_data.get("order_by", [])),
                limit=output_data.get("limit"),
                offset=output_data.get("offset"),
                select_distinct=output_data.get("select_distinct", False),
                set_ops=json.dumps(output_data.get("set_ops", [])),
            )

            all_nodes.append(output_shape_node)
            all_edges.append((
                semantic_model_identifier,
                output_shape_node,
                HasOutputShape(),
            ))

    def _collect_audit_findings(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredAuditFinding and InferredAuditPatch nodes for Pass 9: Audit Analysis."""
        audit_analysis = self._as_dict(
            results.get("audit_analysis"), model_id, "audit_analysis"
        )
        if not audit_analysis:
            return

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        # Collect findings
        for finding in self._as_list(
            audit_analysis.get("findings"), model_id, "audit_analysis.findings"
        ):
            where_ptr = finding.get("where")
            where_str = json.dumps(where_ptr) if where_ptr else None
            context = finding.get("context")
            context_str = json.dumps(context) if context else None

            finding_node = InferredAuditFinding(
                name=f"{finding.get('code', '')}: {finding.get('message', '')[:50]}",
                semantic_model_id=semantic_model_id,
                code=finding.get("code", ""),
                severity=finding.get("severity", "info"),
                message=finding.get("message", ""),
                where=where_str,
                context=context_str,
            )

            all_nodes.append(finding_node)
            all_edges.append((
                semantic_model_identifier,
                finding_node,
                HasAuditFinding(),
            ))

        # Collect patches
        for patch in self._as_list(
            audit_analysis.get("suggested_patches"),
            model_id,
            "audit_analysis.suggested_patches",
        ):
            patch_value = patch.get("value")
            value_str = json.dumps(patch_value.get("value")) if patch_value else None

            patch_node = InferredAuditPatch(
                name=f"{patch.get('op', '')} {patch.get('path', '')}",
                semantic_model_id=semantic_model_id,
                op=patch.get("op", ""),
                path=patch.get("path", ""),
                value=value_str,
                rationale=patch.get("rationale", ""),
            )

            all_nodes.append(patch_node)
            all_edges.append((
                semantic_model_identifier,
                patch_node,
                HasAuditPatch(),
            ))

    def _collect_grain_tokens(
        self,
        model_id: str,
        results: dict,
        semantic_model_id: str,
        all_nodes: List[BaseNode],
        all_edges: List[Tuple[BaseNode | NodeIdentifier, BaseNode | NodeIdentifier, GraphEdge]],
    ) -> None:
        """Collect InferredGrainToken nodes for Pass 10a: Grain Humanization."""
        grain_humanization = self._as_dict(
            results.get("grain_humanization"), model_id, "grain_humanization"
        )
        tokens = self._as_list(
            grain_humanization.get("tokens"), model_id, "grain_humanization.tokens"
        )

        semantic_model_identifier = NodeIdentifier(
            id=semantic_model_id,
            node_label=NodeLabel.INFERRED_SEMANTIC_MODEL
        )

        for token in tokens:
            token_node = InferredGrainToken(
                name=token.get("normalized_term", ""),
                semantic_model_id=semantic_model_id,
                input_expr=token.get("input_expr", ""),
                normalized_term=token.get("normalized_term", ""),
                is_measure=token.get("is_measure", False),
                dropped=token.get("dropped", False),
            )

            all_nodes.append(token_node)
            all_edges.append((
                semantic_model_identifier,
                token_node,
                HasGrainToken(),
            ))

    def _infer_granularity(self, column: str) -> str:
        """Infer time granularity from column name."""
        column_lower = column.lower()
        if "year" in column_lower:
            return "year"
        elif "month" in column_lower:
            return "month"
        elif "day" in column_lower or "date" in column_lower:
            return "day"
        elif "hour" in column_lower:
            return "hour"
        return "unknown"
