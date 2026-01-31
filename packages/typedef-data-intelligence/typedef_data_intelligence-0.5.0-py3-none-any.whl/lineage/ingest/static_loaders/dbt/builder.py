"""High-level lineage builder facade."""
# ruff: noqa: I001

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, TypedDict
import warnings

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

from lineage.backends.lineage.models import (
    BaseNode,
    Builds,
    CallsMacro,
    DbtColumn,
    DbtMacro,
    DbtModel,
    DbtSource,
    DbtTest,
    DbtUnitTest,
    DependsOn,
    DerivesFrom,
    GraphEdge,
    HasColumn,
    HasTest,
    HasUnitTest,
    Materializes,
    NodeIdentifier,
    PhysicalColumn,
    PhysicalIncrementalModel,
    PhysicalMaterializedView,
    PhysicalTable,
    PhysicalView,
    TestReferences,
    TestsColumn,
    UsesMacro,
)
from lineage.backends.lineage.protocol import LineageStorage
from lineage.backends.types import Confidence, NodeLabel
from lineage.ingest.static_loaders.change_detection import ModelChangeSet, TestChangeSet, UnitTestChangeSet
from lineage.ingest.static_loaders.dbt.dbt_test_fingerprint import (
    compute_test_fingerprint,
    compute_unit_test_fingerprint,
)
from lineage.ingest.progress import ProgressTracker, SyncPhase
from lineage.ingest.static_loaders.dbt.config import LineageBuildConfig
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtArtifacts, DbtLoader, FilteredDbtArtifacts
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtModelNode
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    parse_sql_cached,
    compute_model_fingerprint_result,
    compute_source_fingerprint,
    extract_column_lineage,
    normalize_sql_pair,
)
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema

logger = logging.getLogger(__name__)


def _init_worker():
    """Initialize worker process with warning filters."""
    warnings.simplefilter("ignore", DeprecationWarning)
    warnings.simplefilter("ignore", UserWarning)
    warnings.filterwarnings("ignore", message=".*class-based.*config.*is deprecated.*")
    warnings.filterwarnings("ignore", message=".*PydanticDeprecatedSince20.*")
    warnings.filterwarnings("ignore", message="Field name .* shadows an attribute")
    warnings.filterwarnings("ignore", message=".*swigvarlink.*")
    warnings.filterwarnings("ignore", message=".*lance is not fork-safe.*")
    warnings.filterwarnings("ignore", message=".*multi-threaded.*use of fork.*")
    warnings.filterwarnings("ignore", message=".*default datetime adapter is deprecated.*")


def _clean_properties(properties: Dict[str, object]) -> Dict[str, object]:
    return {k: v for k, v in properties.items() if v is not None}


def _snapshot_identifier() -> str:
    return f"snapshot::{datetime.now(timezone.utc).isoformat()}"


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


def _build_alias_lookup(
    sql: Optional[str] = None, dialect: Optional[str] = None, expression: Optional[exp.Expression] = None
) -> Dict[str, str]:
    """Build a lookup mapping table aliases to table names.

    Args:
        sql: SQL string (only used if expression is not provided)
        dialect: SQL dialect (only used if expression is not provided)
        expression: Pre-parsed SQL expression (takes precedence over sql parameter)

    Returns:
        Dictionary mapping alias to table name
    """
    if expression is None:
        if sql is None:
            return {}
        try:
            expression = sqlglot.parse_one(sql, read=dialect)
        except SqlglotError:
            return {}

    lookup: Dict[str, str] = {}
    for table in expression.find_all(exp.Table):
        alias = table.alias_or_name
        table_sql = table.sql()
        if alias:
            lookup[alias.lower()] = table_sql
        else:
            lookup[table_sql.lower()] = table_sql
    return lookup


def _map_table_to_unique_id(
    table_name: str,
    relation_lookup: Dict[str, str],
    alias_lookup: Dict[str, str],
    artifacts: DbtArtifacts,
) -> Optional[str]:
    """Map a table reference to a dbt unique_id.

    Args:
        table_name: Table reference from SQL
        relation_lookup: Mapping of normalized relation names to unique_ids
        alias_lookup: Mapping of SQL aliases to table names
        artifacts: DbtArtifacts instance for normalization

    Returns:
        dbt unique_id or None if not found
    """
    if not table_name:
        return None
    normalized = artifacts.normalize_relation(table_name)
    candidate = relation_lookup.get(normalized)
    if candidate:
        return candidate
    alias_target = alias_lookup.get(table_name.lower())
    if alias_target:
        normalized_alias = artifacts.normalize_relation(alias_target)
        return relation_lookup.get(normalized_alias)
    return None


class _ColumnLineageEdgeDict(TypedDict):
    from_id: str
    to_id: str
    from_node_type: str
    to_node_type: str
    confidence: str
    transformation: Optional[str]


def _extract_column_lineage_for_model(
    artifacts: DbtArtifacts,
    model: DbtModelNode,
    dialect: Optional[str],
    relation_lookup: Dict[str, str],
    schema: Optional[SqlglotSchema] = None,
    qualified_sql: Optional[str] = None,
) -> List[_ColumnLineageEdgeDict]:
    """Extract column lineage for a single model (parallelizable).

    Parses SQL within the worker process. This is more efficient than
    pre-parsing in the main process because:
    1. Avoids expensive pickle serialization of sqlglot AST objects
    2. SQL strings are much smaller than serialized Expression trees
    3. Parsing is CPU-bound anyway, so workers can parse in parallel

    Args:
        artifacts: DbtArtifacts instance
        model: DbtModelNode instance (must have compiled_sql)
        dialect: SQL dialect
        relation_lookup: Mapping of relation names to unique_ids
        schema: SqlglotSchema instance for SELECT * resolution
        qualified_sql: Pre-qualified SQL string. If provided, skips qualify() call.
    """
    edges: List[_ColumnLineageEdgeDict] = []

    # Use qualified_sql if available (already physically resolved), otherwise use compiled_sql
    sql_to_parse = qualified_sql if qualified_sql else model.compiled_sql
    is_pre_qualified = qualified_sql is not None

    # Parse SQL in worker process
    expression = parse_sql_cached(sql_to_parse, dialect)

    # Build alias lookup from parsed expression
    alias_lookup = _build_alias_lookup(expression=expression)

    column_lineage = extract_column_lineage(
        expression, dialect=dialect, schema=schema, is_pre_qualified=is_pre_qualified
    )
    for column_name, lineage_info in column_lineage.items():
        from_node = DbtColumn.identifier(model.unique_id, column_name)
        for src in lineage_info.sources:
            src_uid = _map_table_to_unique_id(
                src.table, relation_lookup, alias_lookup, artifacts
            )
            if not src_uid:
                continue
            to_node = DbtColumn.identifier(src_uid, src.column)
            edges.append(
                {
                "from_id": from_node.id,
                "to_id": to_node.id,
                "from_node_type": "DbtColumn",
                "to_node_type": "DbtColumn",
                "confidence": lineage_info.confidence.value,
                "transformation": lineage_info.expression,
                }
            )
    return edges


class LineageBuilder:
    """Facade for constructing lineage snapshots from dbt artifacts."""

    def __init__(
        self,
        config: Optional[LineageBuildConfig] = None,
    ) -> None:
        """Create a lineage builder for a dbt artifacts directory.

        Args:
            config: Optional build configuration. If omitted, defaults are used.
        """
        self.config = config or LineageBuildConfig()
        self.loader = DbtLoader(self.config.artifacts)
        self._artifacts = None  # Cache loaded artifacts

    @classmethod
    def from_dbt_artifacts(
        cls, artifacts_path: str | Path, config: Optional[LineageBuildConfig] = None
    ) -> "LineageBuilder":
        """Construct a `LineageBuilder` from a dbt `target/` directory path.

        Args:
            artifacts_path: Path to dbt artifacts directory (usually `target/`).
            config: Optional build configuration.
        """
        cfg = config or LineageBuildConfig()
        cfg.with_artifacts_path(artifacts_path)
        return cls(cfg)

    def _get_artifacts(self):
        """Get cached artifacts or load them."""
        if self._artifacts is None:
            self._artifacts = self.loader.load()
        return self._artifacts

    def get_artifacts(self):
        """Get cached artifacts or load them.

        Public API for accessing the loaded dbt artifacts. This is useful
        for change detection between different manifest versions.

        Returns:
            DbtArtifacts containing manifest, catalog, and run_results
        """
        return self._get_artifacts()

    # ------------------------------------------------------------------
    # Typed write path: write directly via LineageStorage interface
    # ------------------------------------------------------------------
    def write_typed(
        self,
        storage: LineageStorage,
        tracker: Optional[ProgressTracker] = None,
        create_physical_nodes: bool = True,
    ) -> None:
        """Write dbt artifacts with unified parallel column lineage extraction.

        Creates logical dbt nodes (DbtModel, DbtSource, DbtColumn) and optionally
        physical warehouse nodes (PhysicalTable, PhysicalView, PhysicalColumn) with
        BUILDS edges linking them.

        Environment and warehouse type are automatically inferred from the dbt manifest:
        - environment: manifest.metadata.target_name (dev, prod, staging, etc.)
        - warehouse_type: manifest.metadata.adapter_type (duckdb, snowflake, bigquery, etc.)

        This method ALWAYS runs parallel column lineage extraction for performance,
        then passes collected nodes/edges to the storage adapter. The adapter handles
        bulk loading optimization (Parquet for Kùzu, CSV for FalkorDB, or simple loops).

        Args:
            storage: LineageStorage backend to write to
            tracker: Progress tracker for progress updates. If None, creates a no-op
                tracker that discards all progress updates (useful for batch operations
                where progress tracking is not needed).
            create_physical_nodes: If True, creates physical nodes for all models/sources.
                If False, only creates logical dbt nodes. Set to False if ingesting a
                manifest where models haven't been built yet.
        """
        # Create no-op tracker if none provided
        tracker = tracker or ProgressTracker()
        tracker.phase_start(SyncPhase.MANIFEST_PARSING, 1, str(self.config.artifacts.manifest_path()))
        artifacts = self._get_artifacts()
        tracker.update(SyncPhase.MANIFEST_PARSING, 1, 1, details="Manifest loaded")
        tracker.phase_complete(SyncPhase.MANIFEST_PARSING)

        logger.info("Collecting nodes and edges from dbt artifacts...")
        nodes, edges = self._collect_nodes_and_edges(artifacts, create_physical_nodes, tracker)

        logger.info(f"Collected {len(nodes)} nodes and {len(edges)} edges")
        logger.info("Passing to storage adapter for loading...")

        # Signal start of graph write phase with actual counts
        tracker.phase_start(SyncPhase.GRAPH_WRITE, len(nodes) + len(edges), f"{len(nodes)} nodes, {len(edges)} edges")
        storage.bulk_load(nodes, edges, lambda current, total, message: tracker.update(SyncPhase.GRAPH_WRITE, current, total, details=message))
        tracker.phase_complete(SyncPhase.GRAPH_WRITE)
        logger.info("Loading complete")

    def write_incremental(
        self,
        storage: LineageStorage,
        change_set: ModelChangeSet,
        tracker: Optional[ProgressTracker] = None,
        create_physical_nodes: bool = True,
    ) -> None:
        """Write dbt artifacts incrementally based on change detection.

        Only processes models that have been added or modified, and deletes
        models that have been removed. Currently, this can lead to a race condition where the graph is
        in an inconsistent state if the bulk_load operation fails after deleting the existing edges.

        TODO: add a mechanism to backup the state of the graph before and after the write operation, and roll back to the original state if the write operation fails.

        Args:
            storage: LineageStorage backend
            change_set: ModelChangeSet from ChangeDetector
            tracker: Progress tracker for progress updates. If None, creates a no-op
                tracker that discards all progress updates (useful for batch operations
                where progress tracking is not needed).
            create_physical_nodes: Whether to create physical nodes
        """
        tracker = tracker or ProgressTracker()
        tracker.phase_start(SyncPhase.MANIFEST_PARSING, 1, str(self.config.artifacts.manifest_path()))
        artifacts = self._get_artifacts()
        tracker.update(SyncPhase.MANIFEST_PARSING, 1, 1, details="Manifest loaded")
        tracker.phase_complete(SyncPhase.MANIFEST_PARSING)

        # 1. Delete removed models (cascade)
        if change_set.removed:
            logger.info(f"Deleting {len(change_set.removed)} removed models...")
            tracker.phase_start(SyncPhase.PRUNING_KNOWLEDGE_GRAPH, len(change_set.removed))
            total_deleted_nodes = 0
            for model_idx, model_id in enumerate(change_set.removed, 1):
                try:
                    deleted_count = storage.delete_model_cascade(model_id)
                    total_deleted_nodes += deleted_count
                    tracker.update(SyncPhase.PRUNING_KNOWLEDGE_GRAPH, model_idx, len(change_set.removed), details=f"Pruned model {model_id}")
                    logger.debug(f"Deleted model {model_id} ({deleted_count} nodes)")
                except Exception as e:
                    logger.warning(f"Failed to delete model {model_id}: {e}")
            logger.info(f"Pruned {len(change_set.removed)} models ({total_deleted_nodes} total nodes)")
            tracker.phase_complete(SyncPhase.PRUNING_KNOWLEDGE_GRAPH)

        # 2. Collect nodes/edges for added/modified only
        if not change_set.models_to_process:
            if change_set.removed:
                logger.info(
                    f"No models to add or modify (deleted {len(change_set.removed)} models, "
                    f"{len(change_set.unchanged)} unchanged)"
                )
            else:
                logger.info("No models to process (all unchanged)")
            return

        logger.info(
            f"Processing {len(change_set.models_to_process)} changed models "
            f"({len(change_set.added)} added, {len(change_set.modified)} modified)"
        )

        # Filter artifacts to only include changed models
        models_to_process = set(change_set.models_to_process)
        filtered_artifacts = FilteredDbtArtifacts(artifacts, models_to_process)

        # 3. Collect nodes and edges for changed models (includes column lineage extraction)
        # We collect BEFORE deleting old edges to avoid race conditions: if collection fails,
        # the graph remains unchanged. Only after successful collection do we delete+write.
        nodes, edges = self._collect_nodes_and_edges(
            filtered_artifacts,
            create_physical_nodes,
            tracker,
        )

        logger.info(f"Collected {len(nodes)} nodes and {len(edges)} edges for incremental load")

        # 4. Clear derived child nodes for modified models, then bulk load new data.
        # This uses delete_model_cascade(preserve_model=True) to delete:
        # - PhysicalColumn nodes and their edges (HAS_COLUMN, DERIVES_FROM)
        # - Physical relation nodes (PhysicalTable, PhysicalView, etc.)
        # - Semantic metadata (InferredSemanticModel and children)
        # - Profiles (TableProfile, ColumnProfile)
        # It DOES NOT delete DbtColumn nodes: those are preserved to avoid breaking
        # downstream column lineage edges (DERIVES_FROM) from unchanged models.
        # The DbtModel node itself is preserved since we're updating it, not removing it.
        #
        # This ordering ensures atomicity: either both delete and load succeed, or if
        # collection failed above, we never reach this point and the graph stays consistent.
        try:
            if change_set.modified:
                logger.info(f"Clearing child nodes for {len(change_set.modified)} modified models...")
                total_cleared = 0
                for model_id in change_set.modified:
                    cleared = storage.delete_model_cascade(model_id, preserve_model=True)
                    total_cleared += cleared
                    # Prune removed columns only (keep existing column nodes so downstream lineage stays intact)
                    model_node = artifacts.get_model(model_id)
                    if model_node is None:
                        logger.warning(f"Could not find model {model_id} in artifacts to prune removed columns")
                        continue

                    desired_cols = sorted({c.name for c in model_node.columns.values()})
                    if desired_cols:
                        storage.execute_raw_query(
                            "MATCH (c:DbtColumn {parent_id: $model_id}) "
                            "WHERE NOT c.name IN $desired_cols "
                            "DETACH DELETE c",
                            params={"model_id": model_id, "desired_cols": desired_cols},
                        )
                    else:
                        # Model has no columns; remove all columns so graph reflects reality.
                        storage.execute_raw_query(
                            "MATCH (c:DbtColumn {parent_id: $model_id}) DETACH DELETE c",
                            params={"model_id": model_id},
                        )
                logger.info(f"Cleared {total_cleared} child nodes for modified models")

            logger.info("Passing to storage adapter for loading...")
            # Signal start of graph write phase with actual counts
            tracker.phase_start(SyncPhase.GRAPH_WRITE, len(nodes) + len(edges), f"{len(nodes)} nodes, {len(edges)} edges")
            storage.bulk_load(nodes, edges, lambda current, total, message: tracker.update(SyncPhase.GRAPH_WRITE, current, total, details=message))
            tracker.phase_complete(SyncPhase.GRAPH_WRITE)

            # 5. Always sync physical nodes for unchanged models to ensure they exist in the current environment
            # TODO: Consider batching physical node registration for large projects
            # (e.g. database clones for benchmarks). This is the "best of both worlds": logic is cached,
            # but physical registration is always current.
            if change_set.unchanged and create_physical_nodes:
                logger.info(f"Registering physical nodes for {len(change_set.unchanged)} unchanged models...")
                tracker.phase_start(SyncPhase.PHYSICAL_NODE_SYNC, len(change_set.unchanged))
                for idx, model_id in enumerate(change_set.unchanged, 1):
                    try:
                        self.register_physical_node(storage, model_id)
                        if idx % 10 == 0 or idx == len(change_set.unchanged):
                            tracker.update(SyncPhase.PHYSICAL_NODE_SYNC, idx, len(change_set.unchanged), details=f"Synced physical: {model_id}")
                    except Exception as e:
                        logger.warning(f"Failed to register physical node for unchanged model {model_id}: {e}")
                tracker.phase_complete(SyncPhase.PHYSICAL_NODE_SYNC)

            logger.info("Incremental loading complete")
        except Exception as e:
            # Note: If we deleted child nodes but bulk_load failed, the graph may be in an
            # inconsistent state (children deleted but new data not loaded).
            # Graph databases don't support cross-operation transactions, so we document
            # this limitation rather than attempting a rollback.
            logger.error(f"Failed during incremental load: {e}")
            raise

    def write_incremental_tests(
        self,
        storage: LineageStorage,
        test_changes: TestChangeSet,
        unit_test_changes: UnitTestChangeSet,
        tracker: Optional[ProgressTracker] = None,
    ) -> None:
        """Write tests incrementally based on change detection.

        Only processes tests that have been added or modified, and deletes
        tests that have been removed.

        Args:
            storage: LineageStorage backend
            test_changes: TestChangeSet from ChangeDetector
            unit_test_changes: UnitTestChangeSet from ChangeDetector
            tracker: Progress tracker for progress updates
        """
        tracker = tracker or ProgressTracker()
        artifacts = self._get_artifacts()

        # Calculate total deletions for progress tracking
        total_deletions = (
            len(test_changes.removed) + len(unit_test_changes.removed) +
            len(test_changes.modified) + len(unit_test_changes.modified)
        )
        deletion_count = 0

        # 1. Delete removed data tests
        if test_changes.removed:
            logger.info(f"Deleting {len(test_changes.removed)} removed data tests...")
            for test_id in test_changes.removed:
                try:
                    storage.execute_raw_query(
                        "MATCH (t:DbtTest {id: $test_id}) DETACH DELETE t",
                        params={"test_id": test_id},
                    )
                    deletion_count += 1
                    tracker.update(SyncPhase.GRAPH_WRITE, deletion_count, total_deletions, details=f"Deleted test {test_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete test {test_id}: {e}")

        # 2. Delete removed unit tests
        if unit_test_changes.removed:
            logger.info(f"Deleting {len(unit_test_changes.removed)} removed unit tests...")
            for test_id in unit_test_changes.removed:
                try:
                    storage.execute_raw_query(
                        "MATCH (t:DbtUnitTest {id: $test_id}) DETACH DELETE t",
                        params={"test_id": test_id},
                    )
                    deletion_count += 1
                    tracker.update(SyncPhase.GRAPH_WRITE, deletion_count, total_deletions, details=f"Deleted unit test {test_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete unit test {test_id}: {e}")

        # 3. Delete modified tests (will be re-created)
        if test_changes.modified:
            logger.info(f"Deleting {len(test_changes.modified)} modified data tests for re-creation...")
            for test_id in test_changes.modified:
                try:
                    storage.execute_raw_query(
                        "MATCH (t:DbtTest {id: $test_id}) DETACH DELETE t",
                        params={"test_id": test_id},
                    )
                    deletion_count += 1
                    tracker.update(SyncPhase.GRAPH_WRITE, deletion_count, total_deletions, details=f"Deleted modified test {test_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete modified test {test_id}: {e}")

        if unit_test_changes.modified:
            logger.info(f"Deleting {len(unit_test_changes.modified)} modified unit tests for re-creation...")
            for test_id in unit_test_changes.modified:
                try:
                    storage.execute_raw_query(
                        "MATCH (t:DbtUnitTest {id: $test_id}) DETACH DELETE t",
                        params={"test_id": test_id},
                    )
                    deletion_count += 1
                    tracker.update(SyncPhase.GRAPH_WRITE, deletion_count, total_deletions, details=f"Deleted modified unit test {test_id}")
                except Exception as e:
                    logger.warning(f"Failed to delete modified unit test {test_id}: {e}")

        # 4. Collect and write new/modified tests
        tests_to_write = set(test_changes.tests_to_process)
        unit_tests_to_write = set(unit_test_changes.tests_to_process)

        if not tests_to_write and not unit_tests_to_write:
            logger.info("No tests to add or modify")
            return

        logger.info(
            f"Processing {len(tests_to_write)} data tests and "
            f"{len(unit_tests_to_write)} unit tests"
        )

        nodes, edges = self._collect_test_nodes_and_edges(
            artifacts, storage, tests_to_write, unit_tests_to_write
        )

        if nodes:
            logger.info(f"Writing {len(nodes)} test nodes and {len(edges)} edges...")
            tracker.phase_start(SyncPhase.GRAPH_WRITE, len(nodes) + len(edges), f"{len(nodes)} test nodes, {len(edges)} edges")
            storage.bulk_load(nodes, edges)
            tracker.phase_complete(SyncPhase.GRAPH_WRITE)
            logger.info("Incremental test loading complete")

    def _collect_test_nodes_and_edges(
        self,
        artifacts: DbtArtifacts,
        storage: LineageStorage,
        test_ids: Set[str],
        unit_test_ids: Set[str],
    ) -> Tuple[List[BaseNode], List[Tuple[NodeIdentifier, NodeIdentifier, GraphEdge]]]:
        """Collect test nodes and edges for specified test IDs.

        Args:
            artifacts: DbtArtifacts instance
            storage: LineageStorage backend for querying existing nodes
            test_ids: Set of data test unique_ids to collect
            unit_test_ids: Set of unit test unique_ids to collect

        Returns:
            Tuple of (nodes, edges) for the specified tests
        """
        all_nodes: List[BaseNode] = []
        all_edges: List[Tuple[NodeIdentifier, NodeIdentifier, GraphEdge]] = []

        # First pass: collect candidate IDs we need to check for edge creation
        # This avoids scanning the entire graph for large deployments
        candidate_ids: Set[str] = set()
        for test in artifacts.iter_tests():
            if test.unique_id not in test_ids:
                continue
            if test.model_id:
                candidate_ids.add(test.model_id)
            if test.referenced_model_id:
                candidate_ids.add(test.referenced_model_id)
            if test.column_name and test.model_id:
                col_id = DbtColumn.identifier(test.model_id, test.column_name).id
                candidate_ids.add(col_id)

        for unit_test in artifacts.iter_unit_tests():
            if unit_test.unique_id not in unit_test_ids:
                continue
            if unit_test.model_id:
                candidate_ids.add(unit_test.model_id)

        # Query only the candidate IDs to check which exist
        existing_ids: Set[str] = set()
        if candidate_ids:
            try:
                result = storage.execute_raw_query(
                    """
                    UNWIND $ids AS id
                    MATCH (n)
                    WHERE (n:DbtModel OR n:DbtSource OR n:DbtColumn) AND n.id = id
                    RETURN DISTINCT n.id AS id
                    """,
                    params={"ids": list(candidate_ids)},
                )
                existing_ids = {row.get("id") for row in result.rows if row.get("id")}
            except Exception:
                logger.exception(
                    "Failed to check existence of candidate IDs for test edges; "
                    "falling back to treating all candidate IDs as existing."
                )
                existing_ids = set(candidate_ids)

        # Collect data tests
        for test in artifacts.iter_tests():
            if test.unique_id not in test_ids:
                continue

            # Compute test fingerprint
            test_fp = compute_test_fingerprint(
                test_type=test.test_type,
                test_name=test.test_name,
                column_name=test.column_name,
                model_id=test.model_id,
                test_kwargs=test.test_kwargs,
                severity=test.severity,
                where_clause=test.where_clause,
                store_failures=test.store_failures,
            )

            dbt_test = DbtTest(
                name=test.name,
                unique_id=test.unique_id,
                description=test.description,
                test_type=test.test_type,
                test_name=test.test_name,
                column_name=test.column_name,
                model_id=test.model_id,
                referenced_model_id=test.referenced_model_id,
                severity=test.severity,
                tags=test.tags,
                where_clause=test.where_clause,
                store_failures=test.store_failures,
                test_kwargs=test.test_kwargs,
                original_path=test.original_path,
                compiled_sql=test.compiled_sql,
                test_fingerprint=test_fp,
                fingerprint_type="test_config",
            )

            all_nodes.append(dbt_test)

            # HAS_TEST edge
            if test.model_id and test.model_id in existing_ids:
                if test.model_id.startswith("source."):
                    from_label = NodeLabel.DBT_SOURCE
                else:
                    from_label = NodeLabel.DBT_MODEL

                from_node = NodeIdentifier(id=test.model_id, node_label=from_label)
                to_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                all_edges.append((from_node, to_node, HasTest()))

            # TESTS_COLUMN edge
            if test.column_name and test.model_id:
                col_id = DbtColumn.identifier(test.model_id, test.column_name).id
                if col_id in existing_ids:
                    from_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                    to_node = NodeIdentifier(id=col_id, node_label=NodeLabel.DBT_COLUMN)
                    all_edges.append((from_node, to_node, TestsColumn()))

            # TEST_REFERENCES edge
            if test.referenced_model_id and test.referenced_model_id in existing_ids:
                if test.referenced_model_id.startswith("source."):
                    to_label = NodeLabel.DBT_SOURCE
                else:
                    to_label = NodeLabel.DBT_MODEL

                referenced_field = None
                if test.test_kwargs:
                    referenced_field = test.test_kwargs.get("field")

                from_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                to_node = NodeIdentifier(id=test.referenced_model_id, node_label=to_label)
                all_edges.append((from_node, to_node, TestReferences(referenced_field=referenced_field)))

        # Collect unit tests
        for unit_test in artifacts.iter_unit_tests():
            if unit_test.unique_id not in unit_test_ids:
                continue

            unit_test_fp = compute_unit_test_fingerprint(
                model_id=unit_test.model_id,
                given=unit_test.given,
                expect=unit_test.expect,
                overrides=unit_test.overrides,
            )

            dbt_unit_test = DbtUnitTest(
                name=unit_test.name,
                unique_id=unit_test.unique_id,
                description=unit_test.description,
                model_id=unit_test.model_id,
                given=unit_test.given,
                expect=unit_test.expect,
                overrides=unit_test.overrides,
                tags=unit_test.tags,
                test_fingerprint=unit_test_fp,
            )

            all_nodes.append(dbt_unit_test)

            # HAS_UNIT_TEST edge
            if unit_test.model_id and unit_test.model_id in existing_ids:
                from_node = NodeIdentifier(id=unit_test.model_id, node_label=NodeLabel.DBT_MODEL)
                to_node = NodeIdentifier(id=dbt_unit_test.id, node_label=NodeLabel.DBT_UNIT_TEST)
                all_edges.append((from_node, to_node, HasUnitTest()))

        return all_nodes, all_edges

    def _collect_nodes_and_edges(
        self,
        artifacts: DbtArtifacts,
        create_physical_nodes: bool,
        tracker: ProgressTracker,
    ) -> Tuple[List[BaseNode], List[Tuple[NodeIdentifier, NodeIdentifier, GraphEdge]]]:
        """Collect all nodes and edges from dbt artifacts.

        This method:
        1. Collects logical nodes (sources, models, columns)
        2. Collects physical nodes (if enabled)
        3. Collects dependency edges
        4. Extracts column lineage in parallel (always)
        5. Returns flat lists ready for adapter to load

        Returns:
            Tuple of (all_nodes, all_edges) where:
            - all_nodes: List of all Pydantic node objects
            - all_edges: List of (from_node, to_node, edge) tuples
        """
        environment = artifacts.target_name
        warehouse_type = artifacts.adapter_type

        # Track all nodes in both list (for returning) and dict (for validation)
        all_nodes: List[BaseNode] = []
        node_ids: Set[str] = set()

        # Track edges as tuples
        all_edges: List[Tuple[NodeIdentifier, NodeIdentifier, GraphEdge]] = []

        # Counters for logging
        duplicate_source_count = 0
        duplicate_model_count = 0
        duplicate_column_count = 0

        # ========================================================================
        # PHASE 1: Collect Sources and their columns
        # ========================================================================
        total_sources = artifacts.source_count
        total_models = artifacts.model_count
        total_macros = artifacts.macro_count
        total_items = total_sources + total_models + total_macros

        tracker.phase_start(SyncPhase.MODEL_LINEAGE, total_items, f"{total_sources} sources, {total_models} models")
        logger.info("Collecting sources...")
        for source_idx, source in enumerate(artifacts.iter_sources(), 1):
            # Compute source fingerprint based on schema location and columns
            source_columns = {
                col.name: col.data_type
                for col in source.columns.values()
            } if source.columns else None

            source_fp_result = compute_source_fingerprint(
                database=source.database,
                schema=source.schema,
                identifier=source.identifier,
                columns=source_columns,
            )

            dbt_source = DbtSource(
                name=source.name,
                loader=source.loader or "",
                unique_id=source.unique_id,
                description=source.description,
                source_fingerprint=source_fp_result.hash,
                fingerprint_type=source_fp_result.type,
            )

            if dbt_source.id in node_ids:
                duplicate_source_count += 1
                continue

            all_nodes.append(dbt_source)
            node_ids.add(dbt_source.id)

            # Source columns
            for col in source.columns.values():
                dbt_col = DbtColumn(
                    name=col.name,
                    data_type=col.data_type or "unknown",
                    description=col.description or "",
                    parent_id=source.unique_id,
                    parent_label="DbtSource",
                )

                if dbt_col.id in node_ids:
                    duplicate_column_count += 1
                    continue

                all_nodes.append(dbt_col)
                node_ids.add(dbt_col.id)

                # MATERIALIZES edge
                from_node = NodeIdentifier(id=dbt_source.id, node_label=NodeLabel.DBT_SOURCE)
                to_node = NodeIdentifier(id=dbt_col.id, node_label=NodeLabel.DBT_COLUMN)
                all_edges.append((from_node, to_node, Materializes()))

            # Batched progress update (every 10 sources or at the end)
            if source_idx % 10 == 0 or source_idx == total_sources:
                tracker.update(SyncPhase.MODEL_LINEAGE, source_idx, total_items,
                               details=f"Sources: {source_idx}/{total_sources}")

        # ========================================================================
        # PHASE 2: Collect Macros (logical)
        # ========================================================================
        if total_macros:
            logger.info("Collecting macros...")
            # Pass 1: Add all macro nodes to node_ids first
            for macro in artifacts.iter_macros():
                dbt_macro = DbtMacro(
                    name=macro.name,
                    unique_id=macro.unique_id,
                    description=macro.description,
                    package_name=macro.package_name,
                    original_path=macro.original_path,
                    source_path=macro.source_path,
                    macro_sql=macro.macro_sql,
                )

                if dbt_macro.id in node_ids:
                    continue

                all_nodes.append(dbt_macro)
                node_ids.add(dbt_macro.id)

            # Pass 2: Create CALLS_MACRO dependency edges
            for macro in artifacts.iter_macros():
                # Macro -> Macro dependencies
                for dep_macro_id in macro.depends_on_macros or []:
                    # Only create edge if target macro exists in node_ids
                    # (external macros like built-in dbt macros may not be in manifest)
                    if dep_macro_id in node_ids:
                        from_node = NodeIdentifier(id=macro.unique_id, node_label=NodeLabel.DBT_MACRO)
                        to_node = NodeIdentifier(id=dep_macro_id, node_label=NodeLabel.DBT_MACRO)
                        all_edges.append((from_node, to_node, CallsMacro()))
                    else:
                        logger.warning(f"Skipped macro dependency edge to non-existent macro: {dep_macro_id}")

            # Update progress after macros (coarse-grained)
            tracker.update(
                SyncPhase.MODEL_LINEAGE,
                total_sources + total_macros,
                total_items,
                details=f"Macros: {total_macros}/{total_macros}",
            )

        # ========================================================================
        # PHASE 3: Collect Models, their columns, and physical nodes
        # ========================================================================
        logger.info("Collecting models...")
        # Get schema for canonical_sql computation (reused later for column lineage)
        sqlglot_schema = artifacts.sqlglot_schema()
        # Map model unique_id -> qualified_sql for column lineage (avoids redundant qualify)
        qualified_sql_map: Dict[str, str] = {}
        # Map model unique_id -> canonical_sql for stable fingerprints
        canonical_sql_map: Dict[str, str] = {}

        # Start SQL canonicalization phase (happens during model collection)
        tracker.phase_start(SyncPhase.SQL_CANONICALIZATION, total_models, f"Canonicalizing {total_models} models")

        for model_idx, model in enumerate(artifacts.iter_models(), 1):
            # Create logical DbtModel node with only logical properties
            # Physical properties (database, schema, relation_name) live on PhysicalRelation
            # Extract checksum from DbtModelNode
            checksum_value = None
            if model.checksum and model.checksum.checksum:
                checksum_value = model.checksum.checksum

            # Determine dialect for this model
            dialect = self.config.sqlglot.per_model_dialects.get(
                model.unique_id, self.config.sqlglot.default_dialect
            )

            # Compute canonical SQL versions once via a single normalization pass.
            # This avoids the expensive qualify() + annotate_types() running twice.
            canonical_sql = None  # Agnostic (stripped)
            qualified_sql = None  # Fully resolved (physical)
            if model.compiled_sql:
                try:
                    pair = normalize_sql_pair(
                        model.compiled_sql,
                        dialect=dialect,
                        schema=sqlglot_schema,
                    )
                    qualified_sql = pair.qualified
                    canonical_sql = pair.canonical
                except Exception as e:
                    logger.debug(f"SQL normalization failed for {model.unique_id}: {e}")
                    qualified_sql = None
                    canonical_sql = None

                if qualified_sql:
                    qualified_sql_map[model.unique_id] = qualified_sql
                if canonical_sql:
                    canonical_sql_map[model.unique_id] = canonical_sql

            # Compute macro-aware agnostic model fingerprint
            # We use model.compiled_sql + schema to expand SELECT * before hashing,
            # but strip physical names to stay agnostic across DB clones.
            fingerprint_result = compute_model_fingerprint_result(
                resource_type=model.resource_type,
                compiled_sql=model.compiled_sql,
                checksum=checksum_value,
                dialect=dialect,
                schema=sqlglot_schema,
                model_id=model.unique_id,
            )

            model_fingerprint = fingerprint_result.hash if fingerprint_result else None
            fingerprint_type = fingerprint_result.type if fingerprint_result else None
            fingerprint_dialect = fingerprint_result.dialect if fingerprint_result else None

            dbt_model = DbtModel(
                name=model.name,
                unique_id=model.unique_id,
                materialization=model.materialization or "view",
                original_path=model.original_path,
                source_path=model.source_path,
                compiled_path=model.compiled_path,
                description=model.description or "",
                raw_sql=model.raw_sql,
                compiled_sql=model.compiled_sql,
                canonical_sql=canonical_sql,
                qualified_sql=qualified_sql,
                checksum=checksum_value,
                model_fingerprint=model_fingerprint,
                fingerprint_type=fingerprint_type,
                fingerprint_dialect=fingerprint_dialect,
            )

            if dbt_model.id in node_ids:
                duplicate_model_count += 1
                continue

            all_nodes.append(dbt_model)
            node_ids.add(dbt_model.id)

            # Model columns (logical definitions only)
            for col in model.columns.values():
                dbt_col = DbtColumn(
                    name=col.name,
                    data_type=col.data_type or "unknown",
                    description=col.description or "",
                    parent_id=model.unique_id,
                    parent_label="DbtModel",
                )

                if dbt_col.id in node_ids:
                    duplicate_column_count += 1
                    continue

                all_nodes.append(dbt_col)
                node_ids.add(dbt_col.id)

                # MATERIALIZES edge (logical model -> logical column)
                from_node = NodeIdentifier(id=dbt_model.id, node_label=NodeLabel.DBT_MODEL)
                to_node = NodeIdentifier(id=dbt_col.id, node_label=NodeLabel.DBT_COLUMN)
                edge = Materializes()
                all_edges.append((from_node, to_node, edge))

            # Create physical node if enabled
            if create_physical_nodes and model.materialization and model.materialization != "ephemeral":
                # Skip if relation_name is None (model not yet compiled/built)
                if not model.relation_name:
                    logger.warning(
                        f"Skipping physical node for {model.unique_id} - "
                        f"relation_name is None (model may not be compiled/built yet)"
                    )
                else:
                    # Default database/schema to empty string if None (PhysicalRelation fields are non-optional)
                    database = model.database or ""
                    schema = model.schema or ""

                    # model.relation_name is already the fully qualified relation name from dbt
                    # (e.g., "ANALYTICS_BRANDON".mart_common.dim_date)
                    # Strip quotes for consistent matching (Snowflake uses quotes for case-sensitive identifiers)
                    fqn = model.relation_name.replace('"', '') if model.relation_name else ""

                    # Extract table name using sqlglot to handle quoted identifiers with dots
                    table_name = _extract_table_name_from_fqn(
                        model.relation_name, fallback=model.alias or model.name
                    )

                    # Determine physical node type
                    if model.materialization == "table":
                        physical_node = PhysicalTable(
                            fqn=fqn,
                            database=database,
                            schema_name=schema,
                            relation_name=table_name,
                            name=table_name,
                            warehouse_type=warehouse_type,
                            environment=environment,
                        )
                    elif model.materialization == "view":
                        physical_node = PhysicalView(
                            fqn=fqn,
                            database=database,
                            schema_name=schema,
                            relation_name=table_name,
                            name=table_name,
                            warehouse_type=warehouse_type,
                            environment=environment,
                        )
                    elif model.materialization == "incremental":
                        physical_node = PhysicalIncrementalModel(
                            fqn=fqn,
                            database=database,
                            schema_name=schema,
                            relation_name=table_name,
                            name=table_name,
                            warehouse_type=warehouse_type,
                            environment=environment,
                        )
                    elif model.materialization == "materialized_view":
                        physical_node = PhysicalMaterializedView(
                            fqn=fqn,
                            database=database,
                            schema_name=schema,
                            relation_name=table_name,
                            name=table_name,
                            warehouse_type=warehouse_type,
                            environment=environment,
                        )
                    else:
                        # Fallback to table for unknown materializations (including snapshot)
                        physical_node = PhysicalTable(
                            fqn=fqn,
                            database=database,
                            schema_name=schema,
                            relation_name=table_name,
                            name=table_name,
                            warehouse_type=warehouse_type,
                            environment=environment,
                        )

                    all_nodes.append(physical_node)
                    node_ids.add(physical_node.id)

                    # BUILDS edge
                    from_node = NodeIdentifier(id=dbt_model.id, node_label=NodeLabel.DBT_MODEL)
                    to_node = NodeIdentifier(id=physical_node.id, node_label=physical_node.node_label)
                    edge = Builds(environment=environment)
                    all_edges.append((from_node, to_node, edge))

                    # Physical columns (logical -> physical mapping)
                    for col in model.columns.values():
                        # Column FQN is the table FQN + column name
                        col_fqn = f"{fqn}.{col.name}" if fqn else col.name

                        phys_col = PhysicalColumn(
                            fqn=col_fqn,
                            parent_id=physical_node.id,
                            name=col.name,
                            data_type=col.data_type or "unknown",
                        )

                        all_nodes.append(phys_col)
                        node_ids.add(phys_col.id)

                        # HAS_COLUMN edge (physical table -> physical column)
                        from_node = NodeIdentifier(id=physical_node.id, node_label=physical_node.node_label)
                        to_node = NodeIdentifier(id=phys_col.id, node_label=NodeLabel.PHYSICAL_COLUMN)
                        edge = HasColumn()
                        all_edges.append((from_node, to_node, edge))

                        # DERIVES_FROM edge (physical column -> dbt column)
                        dbt_col_id = DbtColumn.identifier(model.unique_id, col.name).id
                        if dbt_col_id in node_ids:
                            from_node = NodeIdentifier(id=phys_col.id, node_label=NodeLabel.PHYSICAL_COLUMN)
                            to_node = NodeIdentifier(id=dbt_col_id, node_label=NodeLabel.DBT_COLUMN)
                            edge = DerivesFrom(confidence=Confidence.DIRECT)
                            all_edges.append((from_node, to_node, edge))

            # Model -> Macro dependencies (if present in manifest)
            for dep_macro_id in model.depends_on_macros or []:
                # Only create edge if target macro exists in node_ids
                # (external macros like built-in dbt macros may not be in manifest)
                if dep_macro_id in node_ids:
                    from_node = NodeIdentifier(id=dbt_model.id, node_label=NodeLabel.DBT_MODEL)
                    to_node = NodeIdentifier(id=dep_macro_id, node_label=NodeLabel.DBT_MACRO)
                    all_edges.append((from_node, to_node, UsesMacro()))
                else:
                    logger.warning(f"Skipped macro dependency edge to non-existent macro: {dep_macro_id}")

            # Batched progress update (every 10 models or at the end)
            if model_idx % 10 == 0 or model_idx == total_models:
                # Update SQL canonicalization progress
                tracker.update(SyncPhase.SQL_CANONICALIZATION, model_idx, total_models,
                               details=f"Canonicalizing: {model_idx}/{total_models}")
                # Update MODEL_LINEAGE progress
                progress = total_sources + total_macros + model_idx
                tracker.update(SyncPhase.MODEL_LINEAGE, progress, total_items,
                               details=f"Models: {model_idx}/{total_models}")

        # Complete SQL canonicalization phase
        tracker.phase_complete(
            SyncPhase.SQL_CANONICALIZATION,
            f"Canonicalized {len(canonical_sql_map)} models (logic) and {len(qualified_sql_map)} models (physical)"
        )

        # Log duplicate stats
        if duplicate_source_count > 0:
            logger.warning(f"Skipped {duplicate_source_count} duplicate sources")
        if duplicate_model_count > 0:
            logger.warning(f"Skipped {duplicate_model_count} duplicate models")
        if duplicate_column_count > 0:
            logger.warning(f"Skipped {duplicate_column_count} duplicate columns")

        # ========================================================================
        # PHASE 3: Collect dependency edges
        # ========================================================================
        logger.info("Collecting dependency edges...")
        dependency_edge_count = 0
        for model in artifacts.iter_models():
            # Combine model and source dependencies
            all_deps = (model.depends_on_nodes or []) + (model.depends_on_sources or [])
            for dep_id in all_deps:
                # Determine dependency type
                if dep_id.startswith("model."):
                    dep_type = "model"
                    to_label = NodeLabel.DBT_MODEL
                elif dep_id.startswith("source."):
                    dep_type = "source"
                    to_label = NodeLabel.DBT_SOURCE
                else:
                    dep_type = "other"
                    to_label = NodeLabel.DBT_MODEL  # Fallback

                from_node = NodeIdentifier(id=model.unique_id, node_label=NodeLabel.DBT_MODEL)
                to_node = NodeIdentifier(id=dep_id, node_label=to_label)
                edge = DependsOn(type=dep_type, direct=True)
                all_edges.append((from_node, to_node, edge))
                dependency_edge_count += 1

        # ========================================================================
        # PHASE 3b: Extract implicit source dependencies from compiled SQL
        # ========================================================================
        # dbt models using dynamic SQL generation (e.g., dbt_utils.get_relations_by_pattern(),
        # dbt_utils.union_relations()) bypass dbt's {{ source() }} macro. This means the
        # manifest's depends_on_sources is empty or incomplete. We parse compiled SQL to
        # extract table references and create DEPENDS_ON edges for sources not explicitly
        # declared.
        logger.info("Extracting implicit source dependencies...")
        from lineage.ingest.static_loaders.dbt.implicit_deps import (
            build_source_lookup,
            extract_implicit_source_deps,
        )

        source_lookup = build_source_lookup(artifacts)
        implicit_dep_count = 0

        for model in artifacts.iter_models():
            # Get dialect for this model
            dialect = self.config.sqlglot.per_model_dialects.get(
                model.unique_id, self.config.sqlglot.default_dialect
            )

            for dep in extract_implicit_source_deps(model, source_lookup, dialect):
                # Verify the source exists in our node set
                if dep.source_id not in node_ids:
                    logger.debug(
                        f"Skipping implicit dep to non-existent source: {dep.source_id}"
                    )
                    continue

                from_node = NodeIdentifier(id=model.unique_id, node_label=NodeLabel.DBT_MODEL)
                to_node = NodeIdentifier(id=dep.source_id, node_label=NodeLabel.DBT_SOURCE)
                edge = DependsOn(type="source", direct=True, inferred=True)
                all_edges.append((from_node, to_node, edge))
                implicit_dep_count += 1

        if implicit_dep_count > 0:
            logger.info(f"Added {implicit_dep_count} implicit source dependency edges")
        else:
            logger.debug("No implicit source dependencies found")

        # Signal completion of MODEL_LINEAGE phase
        tracker.update(SyncPhase.MODEL_LINEAGE, total_items, total_items,
                       details=f"Complete: {dependency_edge_count} explicit + {implicit_dep_count} implicit dependency edges")

        # ========================================================================
        # PHASE 4: Extract column lineage in PARALLEL (always)
        # ========================================================================
        logger.info("Extracting column lineage in parallel...")
        # Note: model_ids filter not used here - this is for full write_typed()
        # Incremental mode uses write_incremental() which handles filtering separately
        column_edges = self._extract_column_lineage_parallel(
            artifacts, node_ids, tracker=tracker, model_ids=None, qualified_sql_map=qualified_sql_map
        )
        all_edges.extend(column_edges)

        # ========================================================================
        # PHASE 5: Collect Tests (data tests and unit tests)
        # ========================================================================
        total_tests = artifacts.test_count
        total_unit_tests = artifacts.unit_test_count
        if total_tests > 0 or total_unit_tests > 0:
            logger.info(f"Collecting {total_tests} data tests and {total_unit_tests} unit tests...")
            test_edge_count = 0

            # Collect data tests
            for test in artifacts.iter_tests():
                # Compute test fingerprint
                test_fp = compute_test_fingerprint(
                    test_type=test.test_type,
                    test_name=test.test_name,
                    column_name=test.column_name,
                    model_id=test.model_id,
                    test_kwargs=test.test_kwargs,
                    severity=test.severity,
                    where_clause=test.where_clause,
                    store_failures=test.store_failures,
                )

                dbt_test = DbtTest(
                    name=test.name,
                    unique_id=test.unique_id,
                    description=test.description,
                    test_type=test.test_type,
                    test_name=test.test_name,
                    column_name=test.column_name,
                    model_id=test.model_id,
                    referenced_model_id=test.referenced_model_id,
                    severity=test.severity,
                    tags=test.tags,
                    where_clause=test.where_clause,
                    store_failures=test.store_failures,
                    test_kwargs=test.test_kwargs,
                    original_path=test.original_path,
                    compiled_sql=test.compiled_sql,
                    test_fingerprint=test_fp,
                    fingerprint_type="test_config",
                )

                if dbt_test.id in node_ids:
                    continue

                all_nodes.append(dbt_test)
                node_ids.add(dbt_test.id)

                # HAS_TEST edge: Model/Source -> DbtTest
                if test.model_id and test.model_id in node_ids:
                    # Determine if parent is model or source
                    if test.model_id.startswith("source."):
                        from_label = NodeLabel.DBT_SOURCE
                    else:
                        from_label = NodeLabel.DBT_MODEL

                    from_node = NodeIdentifier(id=test.model_id, node_label=from_label)
                    to_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                    all_edges.append((from_node, to_node, HasTest()))
                    test_edge_count += 1

                # TESTS_COLUMN edge: DbtTest -> DbtColumn
                if test.column_name and test.model_id:
                    col_id = DbtColumn.identifier(test.model_id, test.column_name).id
                    if col_id in node_ids:
                        from_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                        to_node = NodeIdentifier(id=col_id, node_label=NodeLabel.DBT_COLUMN)
                        all_edges.append((from_node, to_node, TestsColumn()))
                        test_edge_count += 1

                # TEST_REFERENCES edge: DbtTest -> Model/Source (for relationship tests)
                if test.referenced_model_id and test.referenced_model_id in node_ids:
                    if test.referenced_model_id.startswith("source."):
                        to_label = NodeLabel.DBT_SOURCE
                    else:
                        to_label = NodeLabel.DBT_MODEL

                    # Extract referenced field from test_kwargs if available
                    referenced_field = None
                    if test.test_kwargs:
                        referenced_field = test.test_kwargs.get("field")

                    from_node = NodeIdentifier(id=dbt_test.id, node_label=NodeLabel.DBT_TEST)
                    to_node = NodeIdentifier(id=test.referenced_model_id, node_label=to_label)
                    all_edges.append((from_node, to_node, TestReferences(referenced_field=referenced_field)))
                    test_edge_count += 1

            # Collect unit tests
            for unit_test in artifacts.iter_unit_tests():
                # Compute unit test fingerprint
                unit_test_fp = compute_unit_test_fingerprint(
                    model_id=unit_test.model_id,
                    given=unit_test.given,
                    expect=unit_test.expect,
                    overrides=unit_test.overrides,
                )

                dbt_unit_test = DbtUnitTest(
                    name=unit_test.name,
                    unique_id=unit_test.unique_id,
                    description=unit_test.description,
                    model_id=unit_test.model_id,
                    given=unit_test.given,
                    expect=unit_test.expect,
                    overrides=unit_test.overrides,
                    tags=unit_test.tags,
                    test_fingerprint=unit_test_fp,
                )

                if dbt_unit_test.id in node_ids:
                    continue

                all_nodes.append(dbt_unit_test)
                node_ids.add(dbt_unit_test.id)

                # HAS_UNIT_TEST edge: Model -> DbtUnitTest
                if unit_test.model_id and unit_test.model_id in node_ids:
                    from_node = NodeIdentifier(id=unit_test.model_id, node_label=NodeLabel.DBT_MODEL)
                    to_node = NodeIdentifier(id=dbt_unit_test.id, node_label=NodeLabel.DBT_UNIT_TEST)
                    all_edges.append((from_node, to_node, HasUnitTest()))
                    test_edge_count += 1

            logger.info(f"Collected {total_tests} data tests, {total_unit_tests} unit tests with {test_edge_count} edges")

        logger.info(
            f"Collection summary: {len(all_nodes)} nodes, {len(all_edges)} edges "
            f"({len(column_edges)} from column lineage)"
        )

        return all_nodes, all_edges

    def _extract_column_lineage_parallel(
        self,
        artifacts: DbtArtifacts,
        node_ids: Set[str],
        tracker: ProgressTracker,
        model_ids: Optional[Set[str]] = None,
        qualified_sql_map: Optional[Dict[str, str]] = None,
    ) -> List[Tuple[NodeIdentifier, NodeIdentifier, DerivesFrom]]:
        """Extract column lineage edges in parallel with validation.

        Args:
            artifacts: DbtArtifacts instance
            node_ids: Set of all node IDs for validation
            tracker: Progress tracker for progress updates
            model_ids: Optional set of model unique_ids to process (for incremental mode)
            qualified_sql_map: Pre-computed qualified SQL for each model (model_id -> qualified_sql).
                If provided, workers skip qualify() for matched models.

        Returns:
            List of validated (from_node, to_node, edge) tuples
        """
        from lineage.backends.lineage.models.base import NodeIdentifier
        from lineage.backends.lineage.models.edges import DerivesFrom
        from lineage.backends.types import NodeLabel

        # Handle model_ids filtering with explicit semantics:
        # - None: process all models
        # - Empty set: process no models (early return)
        # - Non-empty set: process only specified models
        if model_ids is not None and len(model_ids) == 0:
            logger.info("Empty model_ids set provided, skipping column lineage extraction")
            return []

        # Build normalized relation lookup for parallel workers
        relation_lookup = artifacts.relation_lookup()
        normalized_relation_lookup = {}
        for relation_name, unique_id in relation_lookup.items():
            normalized_relation_lookup[relation_name.lower()] = unique_id

        # Get schema for SELECT * resolution (already cached in artifacts)
        schema = artifacts.sqlglot_schema()

        # Count models by exclusion reason for logging
        no_sql_count = 0
        seed_count = 0
        semantic_view_count = 0

        # Prepare models for parallel processing with explicit filtering
        # Exclude seeds (raw data) and semantic views (non-SQL syntax) which cannot be parsed
        all_models_with_dialects = []
        for model in artifacts.iter_models():
            if not model.compiled_sql:
                no_sql_count += 1
                continue
            if model.resource_type == "seed":
                seed_count += 1
                continue
            if model.materialization == "semantic_view":
                semantic_view_count += 1
                continue
            dialect = self.config.sqlglot.per_model_dialects.get(
                model.unique_id, self.config.sqlglot.default_dialect
            )
            all_models_with_dialects.append((model, dialect))

        # Log exclusion summary
        total_excluded = no_sql_count + seed_count + semantic_view_count
        if total_excluded > 0:
            exclusion_parts = []
            if no_sql_count > 0:
                exclusion_parts.append(f"{no_sql_count} no SQL")
            if seed_count > 0:
                exclusion_parts.append(f"{seed_count} seeds")
            if semantic_view_count > 0:
                exclusion_parts.append(f"{semantic_view_count} semantic views")

            logger.info(
                f"Column lineage: {len(all_models_with_dialects)} models eligible, "
                f"{total_excluded} excluded ({', '.join(exclusion_parts)})"
            )

        if model_ids is None:
            # None means "process all models"
            models_with_dialects = all_models_with_dialects
        else:
            # Non-empty set means "process only these models"
            models_with_dialects = [
                (model, dialect)
                for model, dialect in all_models_with_dialects
                if model.unique_id in model_ids
            ]

        if not models_with_dialects:
            logger.info("No models with compiled SQL found for column lineage extraction")
            return []

        total_models = len(models_with_dialects)
        tracker.phase_start(SyncPhase.COLUMN_LINEAGE, total_models, f"{total_models} models")

        validated_edges: List[Tuple[NodeIdentifier, NodeIdentifier, DerivesFrom]] = []
        allow_missing_source_columns = isinstance(artifacts, FilteredDbtArtifacts)
        completed = 0
        skipped_edges = 0

        def _validate_and_collect_edges(edge_dicts: List[Dict]) -> None:
            """Validate edge dicts and add to validated_edges list."""
            nonlocal skipped_edges
            for edge_dict in edge_dicts:
                from_id = edge_dict["from_id"]
                to_id = edge_dict["to_id"]

                # `from_id` is the *target* column (in the model being analyzed) and
                # `to_id` is the upstream *source* column.
                #
                # Validate the target column exists in this batch; source columns may
                # already exist in the graph (incremental runs) even if not part of this
                # batch.
                if from_id in node_ids and (
                    allow_missing_source_columns or to_id in node_ids
                ):
                    from_node = NodeIdentifier(
                        id=from_id,
                        node_label=NodeLabel.DBT_COLUMN,
                    )
                    to_node = NodeIdentifier(
                        id=to_id,
                        node_label=NodeLabel.DBT_COLUMN,
                    )
                    edge = DerivesFrom(
                        confidence=Confidence(edge_dict["confidence"]),
                        transformation=edge_dict.get("transformation"),
                    )
                    validated_edges.append((from_node, to_node, edge))
                else:
                    skipped_edges += 1
                    logger.debug(
                        f"Skipping DERIVES_FROM edge - missing column: "
                        f"{from_id} or {to_id}"
                    )

        # Check if single-process mode is enabled
        use_single_process = self.config.single_process

        # Prepare qualified_sql_map for lookup
        qualified_sql_map = qualified_sql_map or {}

        if use_single_process:
            # Single-process mode: process models sequentially
            # Useful when running inside another process pool or for debugging
            logger.info(f"Processing {total_models} models in single-process mode...")

            for model, dialect in models_with_dialects:
                model_id = model.unique_id
                try:
                    edge_dicts = _extract_column_lineage_for_model(
                        artifacts,
                        model,
                        dialect,
                        normalized_relation_lookup,
                        schema,
                        qualified_sql=qualified_sql_map.get(model_id),
                    )
                    _validate_and_collect_edges(edge_dicts)

                    completed += 1
                    # Batched progress update (every 10 models or at the end)
                    if completed % 10 == 0 or completed == total_models:
                        tracker.update(SyncPhase.COLUMN_LINEAGE, completed, total_models,
                                       details=f"Extracting: {completed}/{total_models}")

                except Exception as e:
                    completed += 1  # Count failed models too
                    logger.warning(f"Failed to extract column lineage for {model_id}: {e}")
                    # Update progress even on failure
                    if completed % 10 == 0 or completed == total_models:
                        tracker.update(SyncPhase.COLUMN_LINEAGE, completed, total_models,
                                       details=f"Extracting: {completed}/{total_models}")
        else:
            # Multi-process mode: process models in parallel using ProcessPoolExecutor
            # SQL parsing happens in workers - avoids expensive AST serialization
            max_workers = min(os.cpu_count() or 1, total_models)
            logger.info(f"Processing {total_models} models with {max_workers} workers...")

            with ProcessPoolExecutor(max_workers=max_workers, initializer=_init_worker) as executor:
                # Submit all tasks - workers parse SQL themselves
                future_to_model = {
                    executor.submit(
                        _extract_column_lineage_for_model,
                        artifacts,
                        model,
                        dialect,
                        normalized_relation_lookup,
                        schema,
                        qualified_sql_map.get(model.unique_id),
                    ): model.unique_id
                    for model, dialect in models_with_dialects
                }

                # Collect results as they complete
                for future in as_completed(future_to_model):
                    model_id = future_to_model[future]
                    try:
                        edge_dicts = future.result()
                        _validate_and_collect_edges(edge_dicts)

                        completed += 1
                        # Batched progress update (every 10 models or at the end)
                        if completed % 10 == 0 or completed == total_models:
                            tracker.update(SyncPhase.COLUMN_LINEAGE, completed, total_models,
                                           details=f"Extracting: {completed}/{total_models}")

                    except Exception as e:
                        completed += 1  # Count failed models too
                        logger.warning(f"Failed to extract column lineage for {model_id}: {e}")
                        # Update progress even on failure
                        if completed % 10 == 0 or completed == total_models:
                            tracker.update(SyncPhase.COLUMN_LINEAGE, completed, total_models,
                                           details=f"Extracting: {completed}/{total_models}")

        # Log skip rate to detect data quality issues
        total_edges = len(validated_edges) + skipped_edges
        if total_edges > 0 and skipped_edges > total_edges * 0.1:
            skip_rate = skipped_edges * 100 / total_edges
            logger.warning(
                f"High edge skip rate: {skipped_edges}/{total_edges} "
                f"({skip_rate:.1f}%) edges skipped due to missing columns"
            )
        elif skipped_edges > 0:
            logger.debug(f"Skipped {skipped_edges} edges due to missing columns")
        logger.info(
            f"Column lineage extraction complete: {len(validated_edges)} edges validated"
        )

        tracker.phase_complete(SyncPhase.COLUMN_LINEAGE)

        return validated_edges

    def register_physical_node(
        self,
        storage: LineageStorage,
        model_unique_id: str,
    ) -> None:
        """Register a physical node for a specific dbt model.

        Use this after write_typed(create_physical_nodes=False) to register
        physical nodes for models that have been successfully built.

        Environment and warehouse type are automatically inferred from the dbt manifest.

        Args:
            storage: LineageStorage backend
            model_unique_id: dbt unique_id (e.g., "model.demo.customers")

        Example:
            >>> builder = LineageBuilder.from_dbt_artifacts("target/")
            >>> # Load logical only
            >>> builder.write_typed(storage, create_physical_nodes=False)
            >>> # Build specific model
            >>> run_dbt_model("customers")
            >>> # Register physical node
            >>> builder.register_physical_node(storage, "model.demo.customers")
        """
        artifacts = self._get_artifacts()

        # Infer environment and warehouse type from manifest metadata
        environment = artifacts.target_name
        warehouse_type = artifacts.adapter_type

        # Find the model
        model = artifacts.get_model(model_unique_id)

        if model is None:
            raise ValueError(f"Model not found: {model_unique_id}")

        if not model.relation_name:
            logger.warning(
                f"Cannot register physical node for {model_unique_id} - "
                f"relation_name is None (model may not be compiled/built yet)"
            )
            return

        # Check materialization is present
        if not model.materialization:
            logger.warning(
                f"Cannot register physical node for {model_unique_id} - "
                f"materialization is None"
            )
            return

        mat_type = model.materialization.lower()
        if mat_type == "ephemeral":
            logger.debug(f"Skipping physical node for ephemeral model {model_unique_id}")
            return

        # Default database/schema to empty string if None (PhysicalRelation fields are non-optional)
        database = model.database or ""
        schema = model.schema or ""

        # model.relation_name is already the fully qualified relation name from dbt
        # (e.g., "ANALYTICS_BRANDON".mart_common.dim_date)
        # Strip quotes for consistent matching (Snowflake uses quotes for case-sensitive identifiers)
        fqn = model.relation_name.replace('"', '') if model.relation_name else ""

        # Extract table name using sqlglot to handle quoted identifiers with dots
        table_name = _extract_table_name_from_fqn(
            model.relation_name, fallback=model.alias or model.name
        )

        if mat_type in ("table", "incremental", "snapshot"):
            physical_node = PhysicalTable(
                name=table_name,
                fqn=fqn,
                database=database,
                schema_name=schema,
                relation_name=table_name,
                warehouse_type=warehouse_type,
                environment=environment,
                created_at=datetime.now(timezone.utc),
            )
        elif mat_type == "view":
            physical_node = PhysicalView(
                name=table_name,
                fqn=fqn,
                database=database,
                schema_name=schema,
                relation_name=table_name,
                warehouse_type=warehouse_type,
                environment=environment,
                created_at=datetime.now(timezone.utc),
            )
        elif mat_type == "materialized_view":
            physical_node = PhysicalMaterializedView(
                name=table_name,
                fqn=fqn,
                database=database,
                schema_name=schema,
                relation_name=table_name,
                warehouse_type=warehouse_type,
                environment=environment,
                created_at=datetime.now(timezone.utc),
            )
        else:
            physical_node = PhysicalTable(
                name=table_name,
                fqn=fqn,
                database=database,
                schema_name=schema,
                relation_name=table_name,
                warehouse_type=warehouse_type,
                environment=environment,
                created_at=datetime.now(timezone.utc),
            )

        storage.upsert_node(physical_node)

        # Create BUILDS edge
        dbt_model_identifier = DbtModel.identifier(model_unique_id)
        storage.create_edge(
            dbt_model_identifier,
            physical_node.get_node_identifier(),
            Builds(
                environment=environment,
                materialization_strategy=mat_type,
                deployed_at=datetime.now(timezone.utc),
            )
        )

        # Create PhysicalColumn nodes
        for col in model.columns.values():
            physical_col = PhysicalColumn(
                name=col.name,
                parent_id=physical_node.id,
                data_type=col.data_type,
            )
            storage.upsert_node(physical_col)

            storage.create_edge(
                physical_node.get_node_identifier(),
                physical_col.get_node_identifier(),
                HasColumn()
            )

            storage.create_edge(
                physical_col.get_node_identifier(),
                DbtColumn.identifier(model_unique_id, col.name),
                DerivesFrom(confidence=Confidence.DIRECT)
            )


