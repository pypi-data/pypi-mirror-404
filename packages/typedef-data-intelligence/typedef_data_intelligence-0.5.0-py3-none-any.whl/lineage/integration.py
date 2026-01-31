"""Integration module - combines dbt lineage with semantic analysis."""
# ruff: noqa: I001

from __future__ import annotations

import asyncio
import logging
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from lineage.backends.data_query.protocol import DataQueryBackend
from lineage.backends.lineage.protocol import LineageStorage
from lineage.ingest.config import (
    ClusteringConfig,
    ProfilingConfig,
    SemanticAnalysisConfig,
    SemanticViewLoaderConfig,
)
from lineage.ingest.progress import PASS_DESCRIPTIONS, ProgressTracker, SyncPhase
from lineage.ingest.static_loaders.change_detection import (
    ChangeDetector,
    ModelChangeSet,
)
from lineage.ingest.static_loaders.clustering import ClusteringOrchestrator
from lineage.ingest.static_loaders.dbt.builder import LineageBuilder
from lineage.ingest.static_loaders.dbt.dbt_loader import DbtArtifacts, DbtModelNode
from lineage.ingest.static_loaders.profiling.loader import ProfilingLoader
from lineage.ingest.static_loaders.semantic.loader import SemanticLoader
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    compute_model_fingerprint_result,
)
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema
from lineage.ingest.static_loaders.semantic.pipeline.executor import PipelineExecutor
from lineage.ingest.static_loaders.semantic.pipeline.hybrid_executor import (
    HybridPipelineExecutor,
)
from lineage.ingest.static_loaders.semantic.runner import (
    FENIC_AVAILABLE,
    create_placeholder_analysis,
)
from lineage.ingest.static_loaders.semantic_views.loader import SemanticViewLoader

if FENIC_AVAILABLE:
    import fenic as fc

    from lineage.ingest.static_loaders.semantic.config.session import create_session


logger = logging.getLogger(__name__)

# Default project name used when project_name is None from dbt artifacts
DEFAULT_PROJECT_NAME = "default_project"


def _calculate_batch_count(total_items: int, batch_size: int) -> int:
    """Calculate number of batches needed for given items and batch size.

    Args:
        total_items: Total number of items to process
        batch_size: Maximum items per batch

    Returns:
        Number of batches needed (0 if total_items <= 0)
    """
    if total_items <= 0:
        return 0
    return (total_items + batch_size - 1) // batch_size


@dataclass
class SemanticDeletionResult:
    """Result of attempting to delete semantic analysis for a model."""

    model_id: str
    success: bool
    error: Optional[str] = None


class SemanticCleanupTracker:
    """Tracks which models have been cleaned up to prevent redundant deletions.

    Used during incremental semantic analysis to ensure each modified model's
    old semantic analysis is deleted exactly once, and to skip insertion for
    models where deletion failed (fail-fast behavior).
    """

    def __init__(self):
        """Initialize the SemanticCleanupTracker."""
        self._cleaned_models: set[str] = set()
        self._failed_models: dict[str, str] = {}  # model_id -> error message

    def is_cleaned(self, model_id: str) -> bool:
        """Check if model has already been cleaned up."""
        return model_id in self._cleaned_models

    def mark_cleaned(self, model_id: str) -> None:
        """Mark model as successfully cleaned up."""
        self._cleaned_models.add(model_id)

    def mark_failed(self, model_id: str, error: str) -> None:
        """Mark model as failed to clean up."""
        self._failed_models[model_id] = error

    def is_failed(self, model_id: str) -> bool:
        """Check if model cleanup failed."""
        return model_id in self._failed_models

    def get_failed_models(self) -> dict[str, str]:
        """Get all models that failed cleanup with their error messages."""
        return self._failed_models.copy()

    def reset(self) -> None:
        """Reset the tracker for a new run."""
        self._cleaned_models.clear()
        self._failed_models.clear()


@dataclass(frozen=True)
class SyncPlan:
    """Encapsulates all decisions made during the planning phase."""

    project_name: Optional[str]
    run_dbt_write: bool
    incremental: bool
    change_set: Optional[ModelChangeSet]
    models_to_analyze: list[DbtModelNode]
    models_to_profile: list[DbtModelNode]
    run_semantic_views: bool
    run_clustering: bool
    is_semantic_recovery: bool
    allow_cache_read: bool
    skip_all_derived: bool


class SyncPlanner:
    """Stateless class that determines what work needs to be done for a sync."""

    def __init__(
        self,
        storage: LineageStorage,
        enable_semantic: bool,
        enable_profiling: bool,
        enable_clustering: bool,
        enable_semantic_views: bool,
        semantic_config: SemanticAnalysisConfig,
    ):
        """Initialize the SyncPlanner with current enablement states and config.

        Args:
            storage: LineageStorage instance
            enable_semantic: Whether semantic analysis is enabled
            enable_profiling: Whether profiling is enabled
            enable_clustering: Whether clustering is enabled
            enable_semantic_views: Whether semantic view loading is enabled
            semantic_config: Semantic analysis configuration
        """
        self.storage = storage
        self.enable_semantic = enable_semantic
        self.enable_profiling = enable_profiling
        self.enable_clustering = enable_clustering
        self.enable_semantic_views = enable_semantic_views
        self.semantic_config = semantic_config

    def create_plan(
        self,
        artifacts: DbtArtifacts,
        models_list: list[DbtModelNode],
        graph_was_empty: bool,
        incremental: bool = False,
        model_filter: Optional[str] = None,
        builder: Optional[LineageBuilder] = None,
        tracker: Optional[ProgressTracker] = None,
    ) -> SyncPlan:
        """Create a execution plan based on current state and artifacts."""
        # 1. Detect changes
        change_set = None
        if incremental and builder:
            change_set = self._detect_incremental_changes(artifacts, builder, tracker)

        # 2. Determine dbt write
        run_dbt_write = True
        if incremental and change_set and not change_set.has_changes:
            run_dbt_write = False

        # 3. Check for semantic recovery
        # Even if fingerprints haven't changed, we might be missing semantic metadata
        # (e.g. if a previous run crashed).
        skip_all_derived = bool(incremental and change_set and not change_set.has_changes)
        semantic_recovery = False
        effective_change_set = change_set

        if skip_all_derived and self.enable_semantic:
            missing_ids = self._find_missing_semantics(models_list, model_filter)
            if missing_ids:
                semantic_recovery = True
                skip_all_derived = False
                # Show preview of models needing recovery (max 5)
                preview_ids = sorted(missing_ids)[:5]
                preview = ", ".join(preview_ids)
                suffix = f" (and {len(missing_ids) - 5} more)" if len(missing_ids) > 5 else ""
                logger.warning(
                    f"Semantic analysis missing for {len(missing_ids)} model(s); "
                    f"running recovery for: {preview}{suffix}"
                )
                # Create synthetic change_set so existing "analyze change_set.models_to_process" logic works
                effective_change_set = ModelChangeSet(
                    added=sorted(missing_ids),
                    modified=[],
                    removed=[],
                    unchanged=[],
                )

        # 4. Build worklists
        models_to_profile, models_to_analyze = self._build_worklists(
            models_list, model_filter, effective_change_set, skip_all_derived
        )

        return SyncPlan(
            project_name=artifacts.project_name,
            run_dbt_write=run_dbt_write,
            incremental=incremental,
            change_set=effective_change_set,
            models_to_analyze=models_to_analyze,
            models_to_profile=models_to_profile,
            run_semantic_views=self.enable_semantic_views and not skip_all_derived,
            run_clustering=self.enable_clustering and not skip_all_derived,
            is_semantic_recovery=semantic_recovery,
            allow_cache_read=(not incremental) or graph_was_empty or semantic_recovery,
            skip_all_derived=skip_all_derived,
        )

    def _detect_incremental_changes(
        self, artifacts: DbtArtifacts, builder: LineageBuilder, tracker: Optional[ProgressTracker] = None
    ) -> ModelChangeSet:
        logger.info("Detecting changes for incremental load...")
        detector = ChangeDetector()

        def dialect_resolver(model_id: str) -> Optional[str]:
            return builder.config.sqlglot.per_model_dialects.get(
                model_id, builder.config.sqlglot.default_dialect
            )

        return detector.detect_changes(
            artifacts, self.storage, dialect_resolver=dialect_resolver, tracker=tracker
        )

    def _find_missing_semantics(
        self, models_list: list[DbtModelNode], model_filter: Optional[str]
    ) -> set[str]:
        eligible_models = _filter_models_for_semantic_analysis(
            models_list, model_filter=model_filter
        )
        eligible_ids = [m.unique_id for m in eligible_models]
        if not eligible_ids:
            return set()

        # Use parameterized query to prevent injection attacks
        # Retry logic is handled at the adapter level via max_retries
        query = """
            MATCH (m:DbtModel)
            WHERE m.id IN $eligible_ids
              AND NOT (m)-[:HAS_INFERRED_SEMANTICS]->(:InferredSemanticModel)
            RETURN m.id AS id
        """
        result = self.storage.execute_raw_query(query, params={"eligible_ids": eligible_ids})
        return {row["id"] for row in result.rows if row.get("id")}

    def _build_worklists(
        self,
        models_list: list[DbtModelNode],
        model_filter: Optional[str],
        change_set: Optional[ModelChangeSet],
        skip_all_derived: bool,
    ) -> tuple[list[DbtModelNode], list[DbtModelNode]]:
        if skip_all_derived:
            return [], []

        models_to_profile = []
        if self.enable_profiling:
            models_to_profile = [
                m
                for m in models_list
                if m.materialization in ["table", "view", "incremental"]
                and (not model_filter or model_filter in m.unique_id)
            ]

        models_to_analyze = []
        if self.enable_semantic:
            models_to_analyze = _filter_models_for_semantic_analysis(
                models_list, model_filter=model_filter, change_set=change_set
            )

        return models_to_profile, models_to_analyze


class LineageIntegration:
    """Orchestrates dbt lineage loading with optional semantic analysis and profiling."""

    def __init__(
        self,
        storage: LineageStorage,
        semantic_config: SemanticAnalysisConfig,
        profiling_config: ProfilingConfig,
        clustering_config: ClusteringConfig,
        semantic_view_config: SemanticViewLoaderConfig,
        data_backend: Optional[DataQueryBackend] = None,
        fenic_db_path: Optional[Path] = None,
    ):
        """Initialize the LineageIntegration.

        Args:
            storage: LineageStorage instance
            semantic_config: Semantic analysis configuration
            profiling_config: Profiling configuration
            clustering_config: Clustering configuration
            semantic_view_config: Semantic view loader configuration
            data_backend: Optional data query backend
            fenic_db_path: Optional path for fenic database files (DuckDB, LLM cache)
        """
        self.storage = storage
        self.semantic_config = semantic_config
        self.profiling_config = profiling_config
        self.clustering_config = clustering_config
        self.semantic_view_config = semantic_view_config
        self.data_backend: DataQueryBackend = data_backend
        self.fenic_db_path = fenic_db_path

        # SQLGlot schema for SQL canonicalization (set during load)
        self._sqlglot_schema: Optional[SqlglotSchema] = None

        # Determine actual enablement based on config and availability
        self.enable_semantic = semantic_config.enabled and FENIC_AVAILABLE
        self.enable_clustering = clustering_config.enabled
        self.enable_profiling = profiling_config.enabled and data_backend is not None
        self.enable_semantic_views = (
            semantic_view_config.enabled and data_backend is not None
        )

        if semantic_config.enabled and not FENIC_AVAILABLE:
            logger.warning("Fenic not available - semantic analysis disabled")
        if profiling_config.enabled and data_backend is None:
            logger.warning("Data backend not provided - profiling disabled")
        if semantic_view_config.enabled and data_backend is None:
            logger.warning("Data backend not provided - semantic views disabled")

    def _is_valid_analysis(self, row: dict) -> bool:
        """Check if analysis row has valid results."""
        required_columns = [
            "relation_analysis",
            "column_analysis",
            "business_semantics",
        ]
        for col in required_columns:
            if col not in row or row[col] is None:
                return False
        return True

    def _extract_analysis_from_row(self, row: dict) -> dict:
        """Extract analysis results from DataFrame row."""
        results = {}
        analysis_columns = [
            "relation_analysis",
            "column_analysis",
            "join_analysis",
            "filter_analysis",
            "grouping_analysis",
            "time_analysis",
            "window_analysis",
            "output_shape_analysis",
            "audit_analysis",
            "business_semantics",
            "grain_humanization",
            "analysis_summary",
        ]

        for col in analysis_columns:
            if col in row:
                value = row[col]
                # Convert Pydantic models to dict if needed
                if hasattr(value, "model_dump"):
                    results[col] = value.model_dump()
                elif hasattr(value, "dict"):
                    results[col] = value.dict()
                else:
                    results[col] = value

        return results

    def _get_project_cache_dir(self, project_name: Optional[str]) -> Path:
        """Get cache directory for a specific project.

        Args:
            project_name: Name of the dbt project (None if not available)

        Returns:
            Path to project-specific cache directory
        """
        # Use default name if project_name is None
        safe_name = project_name or DEFAULT_PROJECT_NAME
        return self.semantic_config.cache_dir / safe_name

    def _graph_has_any_dbt_models(self) -> bool:
        """Return True if the graph already contains any DbtModel nodes."""
        try:
            result = self.storage.execute_raw_query(
                "MATCH (m:DbtModel) RETURN COUNT(m) AS count"
            )
            if not result.rows:
                return False
            count = result.rows[0].get("count", 0)
            return bool(count)
        except Exception:
            # Conservative: assume non-empty to avoid cache reads in incremental.
            return True

    def _create_fenic_session_if_needed(
        self, skip_remaining_steps: bool
    ) -> Optional[fc.Session]:
        """Create Fenic session if needed for semantic analysis or clustering."""
        if skip_remaining_steps or not FENIC_AVAILABLE:
            return None
        if not (self.enable_semantic or self.enable_clustering):
            return None

        session = create_session(
            analysis_models=self.semantic_config.models,
            db_path=self.fenic_db_path,
        )
        fc.configure_logging(log_level=logging.WARNING)
        return session

    def _execute_dbt_write(
        self,
        builder: LineageBuilder,
        change_set: Optional[ModelChangeSet],
        tracker: ProgressTracker,
        incremental: bool,
    ) -> None:
        if incremental and change_set and change_set.has_changes:
            logger.info("Writing incremental dbt graph...")
            builder.write_incremental(self.storage, change_set, tracker)
        elif not incremental:
            builder.write_typed(self.storage, tracker)

        # After model write, handle tests incrementally if in incremental mode.
        # Always run detection (even when counts are 0) so that removals are caught.
        if incremental:
            artifacts = builder.get_artifacts()
            from lineage.ingest.static_loaders.change_detection import ChangeDetector
            detector = ChangeDetector()
            test_changes = detector.detect_test_changes(artifacts, self.storage)
            unit_test_changes = detector.detect_unit_test_changes(artifacts, self.storage)
            if test_changes.has_changes or unit_test_changes.has_changes:
                builder.write_incremental_tests(
                    self.storage, test_changes, unit_test_changes, tracker
                )

    def _execute_semantic_views(self, verbose: bool, tracker: ProgressTracker) -> None:
        logger.debug(f"Loading semantic views from {self.data_backend.get_backend_type().value}...")
        loader = SemanticViewLoader(self.storage)
        db_schema_pairs = self.storage.get_unique_database_schema_pairs()

        if not db_schema_pairs:
            logger.warning("No database/schema pairs found - skipping semantic views")
            return

        tracker.phase_start(SyncPhase.SEMANTIC_VIEWS, len(db_schema_pairs), f"{len(db_schema_pairs)} schemas")
        total_views = 0
        for idx, (database, schema) in enumerate(db_schema_pairs, 1):
            tracker.update(SyncPhase.SEMANTIC_VIEWS, idx, len(db_schema_pairs), details=f"{database}.{schema}")
            total_views += loader.load_semantic_views(self.data_backend, database=database, schema=schema, verbose=verbose)
        tracker.phase_complete(SyncPhase.SEMANTIC_VIEWS)
        logger.debug(f"Total: {total_views} semantic views across {len(db_schema_pairs)} schemas")

    def _execute_derived_work(
        self,
        plan: SyncPlan,
        session: Optional[fc.Session],
        verbose: bool,
        tracker: ProgressTracker,
    ) -> None:
        """Execute profiling and semantic analysis based on the plan sequentially."""
        # 1. Profiling (Sequential)
        if plan.models_to_profile:
            tracker.phase_start(
                SyncPhase.PROFILING,
                len(plan.models_to_profile),
                f"{len(plan.models_to_profile)} tables",
            )
            profiling_loader = ProfilingLoader(self.storage)
            asyncio.run(
                profiling_loader.profile_models_parallel(
                    plan.models_to_profile,
                    self.data_backend,
                    max_workers=self.profiling_config.max_workers,
                    sample_size=self.profiling_config.sample_size,
                    verbose=verbose,
                )
            )
            tracker.phase_complete(SyncPhase.PROFILING)

        # 2. Semantic Analysis (Sequential)
        if plan.models_to_analyze:
            # Note: _run_semantic_analysis_only handles phase start/complete internally
            self._run_semantic_analysis_only(
                plan.models_to_analyze,
                session,
                plan.project_name,
                None,  # model_filter already applied by planner
                plan.change_set,
                plan.allow_cache_read,
                verbose,
                progress_tracker=tracker,
            )

    def load_dbt_with_semantics(
        self,
        artifacts_dir: Path,
        model_filter: Optional[str] = None,
        export_cache_override: Optional[bool] = None,
        incremental: bool = False,
        verbose: bool = False,
        progress_tracker: Optional[ProgressTracker] = None,
    ) -> None:
        """Load dbt artifacts with optional semantic analysis.

        Args:
            artifacts_dir: Path to dbt target/ directory
            model_filter: Optional substring to filter models (e.g., "fct_" for facts only)
            export_cache_override: Override export_cache config setting (default: None, use config)
            incremental: If True, only load changed models (default: False)
            verbose: Enable verbose output
            progress_tracker: Optional progress tracker for UI updates
        """
        tracker = progress_tracker or ProgressTracker()

        # Store original export_cache setting and apply override
        original_export_cache = self.semantic_config.export_cache
        if export_cache_override is not None:
            self.semantic_config.export_cache = export_cache_override
            logger.info(f"   Export cache override: {export_cache_override}")

        try:
            # 1. Gather Metadata (Artifacts + Graph State)
            builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
            artifacts = builder.loader.load()
            models_list = list(artifacts.iter_models())
            sources_list = list(artifacts.iter_sources())
            logger.info(f"Loaded {len(models_list)} models, {len(sources_list)} sources")

            # Cache SQLGlot schema for SQL canonicalization
            self._sqlglot_schema = artifacts.sqlglot_schema()

            graph_was_empty = not self._graph_has_any_dbt_models()

            # 2. Planning (Pure Logic)
            planner = SyncPlanner(
                storage=self.storage,
                enable_semantic=self.enable_semantic,
                enable_profiling=self.enable_profiling,
                enable_clustering=self.enable_clustering,
                enable_semantic_views=self.enable_semantic_views,
                semantic_config=self.semantic_config,
            )
            plan = planner.create_plan(
                artifacts=artifacts,
                models_list=models_list,
                graph_was_empty=graph_was_empty,
                incremental=incremental,
                model_filter=model_filter,
                builder=builder,
                tracker=tracker,
            )

            # 3. Execution Phase: dbt Graph Write
            if plan.run_dbt_write:
                self._execute_dbt_write(builder, plan.change_set, tracker, plan.incremental)
            else:
                logger.info("No changes detected - not updating knowledge graph.")

            if plan.skip_all_derived:
                logger.info("No changes detected (model_fingerprint unchanged) - skipping derived work.")
                tracker.update(SyncPhase.COMPLETE, 1, 1)
                return

            # 4. Execution Phase: Semantic Views
            if plan.run_semantic_views:
                self._execute_semantic_views(verbose, tracker)

            # 5. Execution Phase: Derived Work (Profiling + Semantic Analysis)
            session = self._create_fenic_session_if_needed(plan.skip_all_derived)
            try:
                self._execute_derived_work(plan, session, verbose, tracker)

                # 6. Execution Phase: Clustering
                if plan.run_clustering:
                    tracker.phase_start(SyncPhase.CLUSTERING, 1, "Clustering models")
                    self._run_clustering(session, verbose)
                    tracker.phase_complete(SyncPhase.CLUSTERING)

            finally:
                if session:
                    session.stop()

            tracker.update(SyncPhase.COMPLETE, 1, 1)

        finally:
            self.semantic_config.export_cache = original_export_cache

    def _partition_models_by_cache(
        self, session: fc.Session, models: list[DbtModelNode], cache_dir: Path
    ) -> tuple[list[DbtModelNode], list[DbtModelNode]]:
        """Partition models into cache hits and misses based on fingerprints stored in parquet.

        Fingerprints are stored directly in analysis_results.parquet as a column,
        eliminating the need for a separate checksums.json file.

        Args:
            session: Fenic session to read cache file
            models: List of current dbt models to check
            cache_dir: Project cache directory

        Returns:
            Tuple of (hit_models, miss_models)
        """
        hit_models: list[DbtModelNode] = []
        miss_models: list[DbtModelNode] = []

        # If cache doesn't exist, everything is a miss
        if not cache_dir.exists():
            return [], models

        parquet_file = cache_dir / "analysis_results.parquet"
        if not parquet_file.exists():
            return [], models

        # Load cached fingerprints directly from parquet (fast columnar access)
        cached_fingerprints: dict[str, str] = {}
        try:
            results_df = self._load_cached_analysis(session, cache_dir).select(
                "model_id", "fingerprint"
            )
            cached_fingerprints = {
                row["model_id"]: row["fingerprint"]
                for row in results_df.to_pylist()
                if row.get("fingerprint")  # Skip rows without fingerprint
            }
        except Exception as e:
            logger.warning(f"Failed to read fingerprints from analysis_results.parquet: {e}")
            return [], models

        if not cached_fingerprints:
            return [], models

        dialect = (
            self.data_backend.get_backend_type().value
            if self.data_backend
            else None
        )

        for model in models:
            # Missing SQL is always a miss (cannot fingerprint)
            if not model.compiled_sql:
                miss_models.append(model)
                continue

            # Compute current fingerprint using new structured result
            checksum_value = model.checksum.checksum if model.checksum else None
            try:
                current_result = compute_model_fingerprint_result(
                    resource_type=model.resource_type,
                    compiled_sql=model.compiled_sql,
                    checksum=checksum_value,
                    dialect=dialect,
                    model_id=model.unique_id,
                )
                if not current_result:
                    miss_models.append(model)
                    continue
            except Exception as e:
                logger.debug(f"Failed to compute fingerprint for {model.unique_id}: {e}")
                miss_models.append(model)
                continue

            # Check if fingerprint hash matches cached value
            cached_fingerprint = cached_fingerprints.get(model.unique_id)
            if cached_fingerprint and cached_fingerprint == current_result.hash:
                hit_models.append(model)
            else:
                miss_models.append(model)

        return hit_models, miss_models

    def _get_invalid_cached_models(
        self, models: list[DbtModelNode], cache_dir: Path, change_set: Optional[ModelChangeSet] = None
    ) -> list[str]:
        """Get list of model IDs with invalid cache (per-model granularity).

        Reads fingerprints directly from analysis_results.parquet.

        Args:
            models: List of current dbt models
            cache_dir: Project cache directory
            change_set: Optional ModelChangeSet to use for filtering

        Returns:
            List of model unique_ids that need re-analysis
        """
        invalid_models: list[str] = []

        # If change_set provided, use it to determine which models need analysis
        if change_set:
            # All added and modified models need analysis
            invalid_models.extend(change_set.models_to_process)
            return invalid_models

        # Otherwise, check cache for all models
        if not cache_dir.exists():
            # No cache - all models need analysis
            return [m.unique_id for m in models if m.compiled_sql]

        parquet_file = cache_dir / "analysis_results.parquet"
        if not parquet_file.exists():
            # No cache file - all models need analysis
            return [m.unique_id for m in models if m.compiled_sql]

        # Load cached fingerprints directly from parquet using PyArrow (no Fenic session needed)
        import pyarrow.parquet as pq

        cached_fingerprints: dict[str, str] = {}
        try:
            table = pq.read_table(parquet_file, columns=["model_id", "fingerprint"])
            for model_id, fingerprint in zip(
                table.column("model_id").to_pylist(),
                table.column("fingerprint").to_pylist(),
                strict=True,
            ):
                if fingerprint:
                    cached_fingerprints[model_id] = fingerprint
        except Exception as e:
            logger.warning(f"Failed to read fingerprints from {parquet_file}: {e}")
            # No cached fingerprints - all models need analysis
            return [m.unique_id for m in models if m.compiled_sql]

        if not cached_fingerprints:
            # No cached fingerprints - all models need analysis
            return [m.unique_id for m in models if m.compiled_sql]

        # Check each model individually
        dialect = (
            self.data_backend.get_backend_type().value
            if self.data_backend
            else None
        )
        for model in models:
            if not model.compiled_sql:
                # No compiled SQL - cannot fingerprint reliably
                invalid_models.append(model.unique_id)
                continue

            # Compute current fingerprint using new structured result
            checksum_value = model.checksum.checksum if model.checksum else None
            try:
                current_result = compute_model_fingerprint_result(
                    resource_type=model.resource_type,
                    compiled_sql=model.compiled_sql,
                    checksum=checksum_value,
                    dialect=dialect,
                    model_id=model.unique_id,
                )
                if not current_result:
                    invalid_models.append(model.unique_id)
                    continue
            except Exception:
                invalid_models.append(model.unique_id)
                continue

            # Compare fingerprint hash
            cached_fingerprint = cached_fingerprints.get(model.unique_id)
            if not cached_fingerprint or cached_fingerprint != current_result.hash:
                invalid_models.append(model.unique_id)

        return invalid_models

    def _load_cached_analysis(
        self, session: fc.Session, cache_dir: Path
    ) -> fc.DataFrame:
        """Load analysis results from Parquet cache.

        Args:
            session: Fenic session
            cache_dir: Project cache directory

        Returns:
            Fenic DataFrame with cached analysis results
        """
        parquet_file = cache_dir / "analysis_results.parquet"
        logger.debug(f"Loading cached analysis from {parquet_file}")
        return session.read.parquet(str(parquet_file))

    def _export_cache(
        self,
        result_df: fc.DataFrame,
        cache_dir: Path,
        models: list[DbtModelNode]
    ) -> None:
        """Export analysis results to Parquet cache with fingerprints.

        Fingerprints are stored directly in the parquet file, eliminating the
        need for a separate checksums.json file.

        Args:
            result_df: Fenic DataFrame with analysis results
            cache_dir: Project cache directory
            models: List of dbt models
        """
        import polars as pl

        cache_dir.mkdir(parents=True, exist_ok=True)

        # Build fingerprint lookup for models
        dialect = (
            self.data_backend.get_backend_type().value if self.data_backend else None
        )
        fingerprints: dict[str, dict] = {}
        for model in models:
            checksum_value = model.checksum.checksum if model.checksum else None
            try:
                result = compute_model_fingerprint_result(
                    resource_type=model.resource_type,
                    compiled_sql=model.compiled_sql,
                    checksum=checksum_value,
                    dialect=dialect,
                    model_id=model.unique_id,
                )
                if result:
                    fingerprints[model.unique_id] = {
                        "fingerprint": result.hash,
                        "fingerprint_type": result.type,
                        "fingerprint_dialect": result.dialect,
                    }
            except Exception as e:
                logger.debug(
                    f"Failed to compute fingerprint for cache ({model.unique_id}): {e}"
                )

        # Deduplicate by model_id before export (keep last occurrence for each model)
        # This prevents duplicate accumulation from multiple runs or session table appends
        result_df_deduped = result_df.group_by("model_id").last()
        deduped_count = result_df_deduped.count()
        original_count = result_df.count()
        if deduped_count != original_count:
            logger.debug(
                f"Deduplicated cache: {original_count} -> {deduped_count} rows "
                f"(removed {original_count - deduped_count} duplicates)"
            )

        # Get model_ids from deduplicated DataFrame to build fingerprint columns
        model_ids = [row["model_id"] for row in result_df_deduped.select("model_id").to_pylist()]

        # Build fingerprint Series aligned with model_id order
        fp_hashes = [fingerprints.get(mid, {}).get("fingerprint") for mid in model_ids]
        fp_types = [fingerprints.get(mid, {}).get("fingerprint_type") for mid in model_ids]
        fp_dialects = [fingerprints.get(mid, {}).get("fingerprint_dialect") for mid in model_ids]

        # Add fingerprint columns using Fenic's with_columns (efficient, no temp file)
        result_with_fp = result_df_deduped.with_columns({
            "fingerprint": pl.Series(fp_hashes),
            "fingerprint_type": pl.Series(fp_types),
            "fingerprint_dialect": pl.Series(fp_dialects),
        })

        # Write to parquet
        parquet_file = cache_dir / "analysis_results.parquet"
        result_with_fp.write.parquet(str(parquet_file), mode="overwrite")

        logger.debug(f"Exported analysis cache to {cache_dir}")

    def _export_cache_from_batches(
        self,
        batch_dfs: list[fc.DataFrame],
        cache_dir: Path,
        models: list[DbtModelNode],
        miss_model_ids: set[str],
    ) -> None:
        """Export analysis results to Parquet cache using Polars concatenation.

        This method avoids DuckDB session table schema issues by:
        1. Loading preserved cache entries directly with Polars
        2. Converting batch DataFrames to Polars
        3. Concatenating everything with Polars (schema-flexible)
        4. Writing the combined result to parquet

        Args:
            batch_dfs: List of Fenic DataFrames from batch analysis
            cache_dir: Project cache directory
            models: List of dbt models (for fingerprint computation)
            miss_model_ids: Set of model IDs that were re-analyzed (to filter from preserved cache)
        """
        import polars as pl

        cache_dir.mkdir(parents=True, exist_ok=True)
        parquet_file = cache_dir / "analysis_results.parquet"

        # Build fingerprint lookup for models
        dialect = (
            self.data_backend.get_backend_type().value if self.data_backend else None
        )
        fingerprints: dict[str, dict] = {}
        for model in models:
            checksum_value = model.checksum.checksum if model.checksum else None
            try:
                result = compute_model_fingerprint_result(
                    resource_type=model.resource_type,
                    compiled_sql=model.compiled_sql,
                    checksum=checksum_value,
                    dialect=dialect,
                    model_id=model.unique_id,
                )
                if result:
                    fingerprints[model.unique_id] = {
                        "fingerprint": result.hash,
                        "fingerprint_type": result.type,
                        "fingerprint_dialect": result.dialect,
                    }
            except Exception as e:
                logger.debug(
                    f"Failed to compute fingerprint for cache ({model.unique_id}): {e}"
                )

        # Collect all Polars DataFrames to concatenate
        polars_dfs: list[pl.DataFrame] = []

        # 1. Load preserved cache entries (models not re-analyzed)
        if parquet_file.exists():
            try:
                existing_df = pl.read_parquet(parquet_file)
                # Filter out models that were re-analyzed
                if miss_model_ids:
                    preserved_df = existing_df.filter(~pl.col("model_id").is_in(list(miss_model_ids)))
                else:
                    preserved_df = existing_df
                if len(preserved_df) > 0:
                    # Drop fingerprint columns (will be recomputed)
                    cols_to_drop = [c for c in ["fingerprint", "fingerprint_type", "fingerprint_dialect"] if c in preserved_df.columns]
                    if cols_to_drop:
                        preserved_df = preserved_df.drop(cols_to_drop)
                    polars_dfs.append(preserved_df)
                    logger.debug(f"Preserved {len(preserved_df)} cached entries")
            except Exception as e:
                logger.warning(f"Failed to load existing cache for preservation: {e}")

        # 2. Convert batch DataFrames to Polars
        for batch_df in batch_dfs:
            try:
                # Convert Fenic DataFrame to Polars via Arrow
                polars_df = pl.from_arrow(batch_df.to_arrow())
                # Drop fingerprint columns if present (will be recomputed)
                cols_to_drop = [c for c in ["fingerprint", "fingerprint_type", "fingerprint_dialect"] if c in polars_df.columns]
                if cols_to_drop:
                    polars_df = polars_df.drop(cols_to_drop)
                polars_dfs.append(polars_df)
            except Exception as e:
                logger.warning(f"Failed to convert batch DataFrame: {e}")

        # 3. Concatenate all DataFrames
        if not polars_dfs:
            logger.warning("No data to export to cache")
            return

        # Use diagonal concat to handle potential schema differences
        combined_df = pl.concat(polars_dfs, how="diagonal_relaxed")

        # Deduplicate by model_id (keep last occurrence = newest)
        combined_df = combined_df.group_by("model_id").last()

        # 4. Add fingerprint columns
        model_ids = combined_df["model_id"].to_list()
        fp_hashes = [fingerprints.get(mid, {}).get("fingerprint") for mid in model_ids]
        fp_types = [fingerprints.get(mid, {}).get("fingerprint_type") for mid in model_ids]
        fp_dialects = [fingerprints.get(mid, {}).get("fingerprint_dialect") for mid in model_ids]

        combined_df = combined_df.with_columns([
            pl.Series("fingerprint", fp_hashes),
            pl.Series("fingerprint_type", fp_types),
            pl.Series("fingerprint_dialect", fp_dialects),
        ])

        # 5. Write to parquet
        combined_df.write_parquet(parquet_file)
        logger.debug(f"Exported {len(combined_df)} analysis results to {parquet_file}")

    def _run_semantic_analysis_only(
        self,
        models_list: list[DbtModelNode],
        session: fc.Session,
        project_name: Optional[str],
        model_filter: Optional[str] = None,
        change_set: Optional[ModelChangeSet] = None,
        allow_cache_read: bool = True,
        verbose: bool = False,
        progress_tracker: Optional[ProgressTracker] = None,
    ) -> tuple[int, int]:
        """Run semantic analysis on models.

        Args:
            models_list: List of all dbt models
            session: Fenic session
            project_name: Name of the dbt project (for cache key, None if not available)
            model_filter: Optional substring to filter models
            change_set: Optional ModelChangeSet for incremental analysis
            allow_cache_read: Whether reading the file-backed semantic cache is allowed for this run
            verbose: Enable verbose output
            progress_tracker: Optional progress tracker for UI updates

        Returns:
            Tuple of (analyzed_count, skipped_count)
        """
        logger.debug("Running semantic analysis...")
        semantic_loader = SemanticLoader(self.storage)
        models_to_analyze = _filter_models_for_semantic_analysis(
            models_list, model_filter=model_filter, change_set=change_set
        )

        if not models_to_analyze:
            logger.warning("No valid models to analyze")
            return 0, 0

        # Get dialect from data backend
        if self.data_backend is None:
            raise ValueError(
                "Semantic analysis requires a data backend to determine SQL dialect. "
                "Provide a data_backend when initializing DbtModelSyncer."
            )
        dialect = self.data_backend.get_backend_type().value

        # Run batch processing
        analyzed_count, skipped_count = self._analyze_models_batch(
            models_to_analyze,
            semantic_loader,
            session,
            dialect,
            project_name,
            change_set,
            allow_cache_read,
            verbose,
            progress_tracker,
            all_manifest_models=models_list,  # Full manifest for cache pruning
        )

        logger.debug(f"Analyzed {analyzed_count} models ({skipped_count} skipped)")
        return analyzed_count, skipped_count

    def _run_clustering(
        self,
        session: fc.Session,
        verbose: bool = False,
    ) -> None:
        """Run join graph clustering with enrichment.

        Args:
            session: Fenic session for LLM operations
            verbose: Enable verbose output
        """
        logger.info("Clustering join graph with enrichment...")
        try:
            orchestrator = ClusteringOrchestrator(self.storage)
            result = asyncio.run(
                orchestrator.cluster_and_analyze(
                    session,
                    min_weight=0.0,
                    method="greedy",
                    resolution=1.0,
                    enrich_models=True,
                )
            )

            logger.info(f"✓ Found {len(result['clusters'])} clusters")

            if verbose:
                for summary in result["summaries"]:
                    subject_area = (
                        summary.domains[0]
                        if summary.domains
                        else f"cluster_{summary.cluster_id}"
                    )
                    logger.info(
                        f"   Cluster {summary.cluster_id} - {subject_area}:"
                    )
                    logger.info(f"      Size: {summary.size} models")
                    logger.info(
                        f"      Roles: {len(summary.fact_tables)} facts, "
                        f"{len(summary.dimension_tables)} dims, "
                        f"{len(summary.mixed_tables)} mixed"
                    )
                    if summary.domains:
                        logger.info(f"      Domains: {', '.join(summary.domains)}")
                    if summary.has_pii_tables:
                        logger.info(
                            f"      Contains PII: {len(summary.has_pii_tables)} tables"
                        )

                    # Show blueprint info
                    blueprint = result["blueprints"][summary.cluster_id]
                    if blueprint.fact_table:
                        logger.info(f"      Fact table: {blueprint.fact_table}")
                    if blueprint.dimension_tables[:3]:
                        logger.info(
                            f"      Top dimensions: {', '.join(blueprint.dimension_tables[:3])}"
                        )

        except Exception as e:
            logger.error(f"Clustering failed: {e}")
            if verbose:
                traceback.print_exc()

    def _fetch_canonical_sql_from_graph(self, model_ids: list[str]) -> dict[str, str]:
        """Fetch canonical_sql for models from the graph.

        Args:
            model_ids: List of model unique_ids to fetch

        Returns:
            Dict mapping model_id -> canonical_sql (only for models that have it)
        """
        if not model_ids:
            return {}

        try:
            # Batch query for all model canonical_sql values
            result = self.storage.execute_raw_query(
                """
                MATCH (m:DbtModel)
                WHERE m.id IN $model_ids
                RETURN m.id AS id, m.canonical_sql AS canonical_sql
                """,
                params={"model_ids": model_ids},
            )
            return {
                row["id"]: row["canonical_sql"]
                for row in result.rows
                if row.get("canonical_sql")
            }
        except Exception as e:
            logger.debug(f"Failed to fetch canonical_sql from graph: {e}")
            return {}

    def _create_batch_dataframe(
        self,
        models: list[DbtModelNode],
        session: fc.Session,
        dialect: str
    ) -> fc.DataFrame:
        """Create DataFrame with all models to analyze.

        Fetches pre-computed canonical_sql from the graph (stored during dbt ingest).
        Falls back to on-the-fly canonicalization for models not in graph.
        """
        from lineage.ingest.static_loaders.semantic.utils.sql_operations import (
            _canonicalize_sql,
        )

        # Query canonical_sql for all models from graph (batch query)
        model_ids = [m.unique_id for m in models]
        canonical_sql_map = self._fetch_canonical_sql_from_graph(model_ids)

        data = []
        fallback_count = 0
        for model in models:
            source_path = model.source_path or model.compiled_path or model.original_path
            file_name = None
            if source_path:
                file_name = Path(source_path).name

            # Use canonical_sql from graph, or compute on-the-fly as fallback
            canonical_sql = canonical_sql_map.get(model.unique_id)
            if not canonical_sql and model.compiled_sql:
                # Fallback: compute canonical_sql (for models not yet in graph)
                try:
                    canonical_sql = _canonicalize_sql(
                        model.compiled_sql,
                        dialect=dialect,
                        schema=self._sqlglot_schema,
                    )
                    fallback_count += 1  # Only count successful canonicalizations
                except Exception:
                    canonical_sql = model.compiled_sql
                    # Don't increment: canonicalization failed, using compiled_sql as fallback

            data.append({
                "model_id": model.unique_id,
                "model_name": model.name or model.unique_id.split(".")[-1],
                "path": source_path,
                "filename": file_name,
                "sql": model.compiled_sql,
                "canonical_sql": canonical_sql or model.compiled_sql or "",
            })

        if fallback_count > 0:
            logger.debug(f"Computed canonical_sql for {fallback_count} models not in graph")

        return session.create_dataframe(data)

    def _analyze_models_batch_helper(
        self,
        models: list[DbtModelNode],
        loader: SemanticLoader,
        session: fc.Session,
        dialect: str,
        modified_models: Optional[list[str]] = None,
        cleanup_tracker: Optional[SemanticCleanupTracker] = None,
        verbose: bool = False,
        pass_progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> tuple[int, int, list, list, fc.DataFrame]:
        """Analyze all models in a single batch operation.

        Args:
            models: List of models to analyze in this batch
            loader: SemanticLoader instance
            session: Fenic session
            dialect: SQL dialect
            modified_models: Optional list of modified model IDs for cleanup
            cleanup_tracker: Optional tracker to prevent redundant deletions
            verbose: Enable verbose output
            pass_progress_callback: Optional progress callback for pipeline execution.

        Returns:
            Tuple of (analyzed_count, skipped_count, nodes, edges, result_df)
            The result_df is returned for later concatenation (no session table used).
        """
        if verbose:
            logger.info(f"Batch processing {len(models)} models...")

        # Create batch DataFrame
        df = self._create_batch_dataframe(models, session, dialect)

        # Choose executor based on hybrid mode setting
        if self.semantic_config.use_hybrid:
            # Hybrid mode: deterministic SQLGlot + targeted LLM classification
            executor = HybridPipelineExecutor(
                session,
                self.semantic_config.pipeline,
                schema=self._sqlglot_schema,
                classification_model_size="micro",  # Classification is simple
                lineage_storage=self.storage,
            )
            result_df = executor.run(
                df,
                session,
                dbt_model_name="batch_analysis",
                dialect=dialect,
                progress_callback=pass_progress_callback,
            )
        else:
            # Standard mode: all LLM passes
            executor = PipelineExecutor(session, self.semantic_config.pipeline)
            result_df = executor.run(
                df,
                session,
                dbt_model_name="batch_analysis",
                progress_callback=pass_progress_callback,
            )

        # Collect graph nodes/edges from results
        analyzed, skipped, nodes, edges = self._collect_batch_analysis_results(
            loader,
            result_df,
            allowed_model_ids=None,
            modified_models=modified_models,
            cleanup_tracker=cleanup_tracker,
            verbose=verbose,
        )
        # Return the DataFrame for later concatenation (avoid session table schema issues)
        return analyzed, skipped, nodes, edges, result_df

    def _delete_semantic_analysis(self, model_id: str) -> SemanticDeletionResult:
        """Delete old semantic analysis nodes for a model before re-analysis.

        Args:
            model_id: dbt unique_id of the model (must be non-empty string)

        Returns:
            SemanticDeletionResult with success status and optional error message
        """
        # Input validation
        if not model_id or not isinstance(model_id, str):
            return SemanticDeletionResult(
                model_id=model_id or "",
                success=False,
                error="Invalid model_id: must be a non-empty string",
            )

        # Optimized to use semantic_model_id ownership key instead of variable-length traversal
        # which can accidentally delete other DbtModel nodes if they are reachable.
        query = """
            MATCH (m:DbtModel {id: $model_id})-[:HAS_INFERRED_SEMANTICS]->(sem:InferredSemanticModel)
            OPTIONAL MATCH (child)
            WHERE child.semantic_model_id = sem.id AND NOT child:DbtModel
            DETACH DELETE child
            DETACH DELETE sem
        """
        try:
            # Use parameterized query to prevent injection attacks
            self.storage.execute_raw_query(query, params={"model_id": model_id})
            logger.debug(f"Deleted old semantic analysis for {model_id}")
            return SemanticDeletionResult(model_id=model_id, success=True)
        except Exception as e:
            error_msg = f"Failed to delete semantic analysis for {model_id}: {e}"
            logger.warning(error_msg)
            return SemanticDeletionResult(model_id=model_id, success=False, error=error_msg)

    def _collect_batch_analysis_results(
        self,
        loader: SemanticLoader,
        result_df: fc.DataFrame,
        allowed_model_ids: Optional[set[str]] = None,
        modified_models: Optional[list[str]] = None,
        cleanup_tracker: Optional[SemanticCleanupTracker] = None,
        verbose: bool = False,
    ) -> tuple[int, int, list, list]:
        """Collect nodes and edges from batch analysis results.

        Parses the analysis DataFrame and converts results to graph nodes/edges.
        Does NOT write to graph - caller is responsible for bulk_load().

        Optimized to collect all nodes/edges first, then call bulk_load() once
        instead of once per model.

        Args:
            loader: SemanticLoader instance
            result_df: Fenic DataFrame with analysis results
            allowed_model_ids: Optional set of model IDs to include (filters cached results to a subset)
            modified_models: Optional list of model IDs that were modified (need cleanup)
            cleanup_tracker: Optional tracker to prevent redundant deletions and enable fail-fast
            verbose: Enable verbose output

        Returns:
            Tuple of (analyzed_count, skipped_count, all_nodes, all_edges)
        """
        try:
            results = result_df.to_pylist()

            analyzed_count = 0
            skipped_count = 0

            # Track which models need cleanup (modified models)
            models_to_cleanup = set(modified_models or [])

            # Delete stale semantic analysis upfront for modified models (only once per model)
            for model_id in models_to_cleanup:
                # Skip if already attempted (cleaned or failed)
                if cleanup_tracker is not None:
                    if cleanup_tracker.is_cleaned(model_id) or cleanup_tracker.is_failed(model_id):
                        continue

                result = self._delete_semantic_analysis(model_id)

                if cleanup_tracker is not None:
                    if result.success:
                        cleanup_tracker.mark_cleaned(model_id)
                    else:
                        cleanup_tracker.mark_failed(model_id, result.error or "Unknown error")
                        logger.error(f"Deletion failed for {model_id}, will skip insertion")

            # Collect all nodes and edges
            all_nodes = []
            all_edges = []

            for row in results:
                model_id = row["model_id"]
                model_name = row["model_name"]

                if allowed_model_ids is not None and model_id not in allowed_model_ids:
                    continue

                # Fail-fast: skip insertion for models where deletion failed
                if cleanup_tracker is not None and cleanup_tracker.is_failed(model_id):
                    logger.warning(f"Skipping insertion for {model_id}: deletion failed")
                    skipped_count += 1
                    continue

                if self._is_valid_analysis(row):
                    # Extract analysis results
                    analysis_results = self._extract_analysis_from_row(row)

                    # Collect nodes and edges
                    nodes, edges = loader._collect_nodes_and_edges(model_id, analysis_results)
                    all_nodes.extend(nodes)
                    all_edges.extend(edges)

                    analyzed_count += 1

                    if verbose:
                        logger.debug(f"✓ {model_name}: analysis collected")
                else:
                    # Create placeholder for failed analysis
                    placeholder = create_placeholder_analysis(model_name)

                    # Collect placeholder nodes and edges
                    nodes, edges = loader._collect_nodes_and_edges(model_id, placeholder)
                    all_nodes.extend(nodes)
                    all_edges.extend(edges)

                    skipped_count += 1

                    if verbose:
                        logger.warning(f"✗ {model_name}: analysis failed, using placeholder")

            return analyzed_count, skipped_count, all_nodes, all_edges
        except Exception as e:
            logger.error(f"Error collecting batch analysis results: {e}")
            raise e

    def _get_num_semantic_passes(self, session: fc.Session) -> int:
        """Get the number of semantic analysis passes from the pipeline configuration.

        Args:
            session: Fenic session (required to create PipelineExecutor)

        Returns:
            Number of passes in the execution order
        """
        if self.semantic_config.use_hybrid:
            # Hybrid mode: 1 deterministic phase + LLM-only passes
            temp_executor = HybridPipelineExecutor(
                session,
                self.semantic_config.pipeline,
                lineage_storage=self.storage,
            )
            return len(temp_executor.get_execution_order())
        else:
            temp_executor = PipelineExecutor(session, self.semantic_config.pipeline)
            execution_order = temp_executor.dag.get_execution_order()
            return len(execution_order)

    def _analyze_models_batch(
        self,
        models: list[DbtModelNode],
        loader: SemanticLoader,
        session: fc.Session,
        dialect: str,
        project_name: Optional[str],
        change_set: Optional[ModelChangeSet] = None,
        allow_cache_read: bool = True,
        verbose: bool = False,
        progress_tracker: Optional[ProgressTracker] = None,
        all_manifest_models: Optional[list[DbtModelNode]] = None,
    ) -> tuple[int, int]:
        """Batch analysis with incremental filesystem caching and fallback.

        Args:
            models: List of models to analyze
            loader: SemanticLoader instance
            session: Fenic session
            dialect: SQL dialect
            project_name: Project name for cache key (None if not available)
            change_set: Optional ModelChangeSet for incremental mode
            allow_cache_read: Whether reading the file-backed semantic cache is allowed for this run
            verbose: Enable verbose output
            progress_tracker: Callback for progress tracking
            all_manifest_models: Full list of models from manifest (for cache pruning)

        Returns:
            Tuple of (analyzed_count, skipped_count)
        """
        batch_size = self.semantic_config.batch_size
        tracker = progress_tracker or ProgressTracker()
        cache_dir = self._get_project_cache_dir(project_name)
        
        # Calculate total steps for progress tracking (based on all models, before partitioning)
        # This ensures accurate progress even when cache hits exist
        temp_executor = PipelineExecutor(session, self.semantic_config.pipeline)
        execution_order = temp_executor.dag.get_execution_order()
        num_passes = len(execution_order)
        total_batches_all = _calculate_batch_count(len(models), batch_size)
        total_steps_all = total_batches_all * num_passes

        # Start phase once with correct total (includes both hits and misses)
        tracker.phase_start(SyncPhase.SEMANTIC_ANALYSIS, total_steps_all, f"{len(models)} models")
        completed_steps = 0

        # 1. Partition models into cache hits and misses
        hit_models: list[DbtModelNode] = []
        miss_models: list[DbtModelNode] = models
        
        if self.semantic_config.use_cache and allow_cache_read:
            hit_models, miss_models = self._partition_models_by_cache(session, models, cache_dir)
            if hit_models:
                logger.info(f"Incremental cache: {len(hit_models)} hits, {len(miss_models)} misses")
            else:
                logger.debug("No incremental cache hits found")

        # Track results for graph write
        analyzed_total = 0
        skipped_total = 0
        all_nodes: list = []
        all_edges: list = []
        modified_models = change_set.modified if change_set else None

        # Create cleanup tracker to prevent redundant deletions across cache hits and batches
        cleanup_tracker = SemanticCleanupTracker()

        # 2. Process hits (load from cache)
        if hit_models:
            try:
                result_df = self._load_cached_analysis(session, cache_dir)
                allowed_ids = {m.unique_id for m in hit_models}
                analyzed, skipped, nodes, edges = self._collect_batch_analysis_results(
                    loader,
                    result_df,
                    allowed_model_ids=allowed_ids,
                    modified_models=modified_models,
                    cleanup_tracker=cleanup_tracker,
                    verbose=verbose,
                )
                analyzed_total += analyzed
                skipped_total += skipped
                all_nodes.extend(nodes)
                all_edges.extend(edges)
                logger.debug(f"Loaded {analyzed} results from incremental cache")
                # Update progress for cache hits (count as completed steps)
                # Progress is tracked as batches * passes, so count hit batches
                hit_batches = _calculate_batch_count(len(hit_models), batch_size)
                completed_steps += hit_batches * num_passes
                tracker.update(
                    SyncPhase.SEMANTIC_ANALYSIS,
                    completed_steps,
                    total_steps_all,
                    details=f"Loaded {len(hit_models)} from cache",
                )
            except Exception as e:
                logger.warning(f"Failed to load hits from cache: {e}, adding to misses")
                miss_models.extend(hit_models)
                # Deduplicate miss_models
                seen_miss_ids = set()
                miss_models = [m for m in miss_models if not (m.unique_id in seen_miss_ids or seen_miss_ids.add(m.unique_id))]

        # 3. Handle misses (fresh analysis)
        # Deduplicate miss_models (defensive programming)
        seen_ids: set[str] = set()
        original_count = len(miss_models)
        miss_models = [
            m for m in miss_models
            if m.unique_id not in seen_ids and not seen_ids.add(m.unique_id)
        ]
        if len(miss_models) < original_count:
            logger.warning(
                f"Removed {original_count - len(miss_models)} duplicate models from miss list"
            )

        # Collect batch result DataFrames for later concatenation
        # This avoids DuckDB session table schema mismatch issues
        batch_result_dfs: list[fc.DataFrame] = []

        if not miss_models:
            # Complete semantic analysis phase early if no misses
            tracker.phase_complete(SyncPhase.SEMANTIC_ANALYSIS)
        else:
            # Process misses in batches
            total_batches = _calculate_batch_count(len(miss_models), batch_size)

            for i in range(0, len(miss_models), batch_size):
                batch = miss_models[i : i + batch_size]
                batch_num = (i // batch_size) + 1

                def on_pass_complete(_pass_name: str, completed_count: int, total_passes: int, batch_num=batch_num):
                    nonlocal completed_steps
                    completed_steps += 1
                    if completed_count < total_passes:
                        next_pass_name = execution_order[completed_count]
                        description = PASS_DESCRIPTIONS.get(next_pass_name, next_pass_name)
                    else:
                        description = "Collecting results..."
                    tracker.update(
                        SyncPhase.SEMANTIC_ANALYSIS, completed_steps, total_steps_all,
                        details=f"Batch {batch_num}/{total_batches}: {description}",
                    )

                try:
                    # Batch processing with pass-level progress
                    analyzed, skipped, nodes, edges, result_df = self._analyze_models_batch_helper(
                        batch, loader, session, dialect, modified_models,
                        cleanup_tracker=cleanup_tracker,
                        verbose=verbose,
                        pass_progress_callback=on_pass_complete,
                    )
                    analyzed_total += analyzed
                    skipped_total += skipped
                    all_nodes.extend(nodes)
                    all_edges.extend(edges)
                    batch_result_dfs.append(result_df)

                except Exception as e:
                    logger.error(
                        f"Batch {batch_num}/{total_batches} failed: {e.__class__.__name__}: {e}"
                    )
                    raise

            # Finalize phase for misses
            tracker.phase_complete(SyncPhase.SEMANTIC_ANALYSIS)

        # 4. Finalize results: Export Cache & Write to Graph
        if self.semantic_config.export_cache:
            try:
                # Export cache using Polars concatenation (avoids DuckDB schema issues)
                checksum_models = all_manifest_models if all_manifest_models else models
                miss_model_ids = {m.unique_id for m in miss_models} if miss_models else set()
                self._export_cache_from_batches(
                    batch_result_dfs,
                    cache_dir,
                    checksum_models,
                    miss_model_ids=miss_model_ids,
                )
                logger.info(f"✓ Exported analysis cache to {cache_dir}")
            except Exception as e:
                logger.warning(f"Failed to export cache: {e}")

        # Log summary of failed deletions (if any)
        failed_models = cleanup_tracker.get_failed_models()
        if failed_models:
            logger.warning(
                f"Semantic cleanup failed for {len(failed_models)} model(s): "
                f"{list(failed_models.keys())}"
            )

        # Write all collected nodes/edges to graph in separate phase
        self._write_semantic_graph(tracker, all_nodes, all_edges)

        return analyzed_total, skipped_total

    def _write_semantic_graph(
        self,
        tracker: ProgressTracker,
        nodes: list,
        edges: list,
    ) -> None:
        """Write semantic analysis results to graph in a separate phase.

        Args:
            tracker: Progress tracker for phase updates
            nodes: All collected nodes to write
            edges: All collected edges to write
        """
        if not nodes and not edges:
            return

        total_items = len(nodes) + len(edges)
        tracker.phase_start(
            SyncPhase.SEMANTIC_GRAPH_WRITE,
            total_items,
            f"{len(nodes)} nodes, {len(edges)} edges",
        )

        # Create progress callback that updates the tracker
        def on_bulk_load_progress(current: int, total: int, message: str) -> None:
            tracker.update(
                SyncPhase.SEMANTIC_GRAPH_WRITE,
                current,
                total,
                details=message,
            )

        logger.debug(f"Bulk loading semantic results: {len(nodes)} nodes, {len(edges)} edges...")
        self.storage.bulk_load(nodes, edges, progress_callback=on_bulk_load_progress)
        logger.debug("✓ Semantic graph write complete")

        tracker.phase_complete(SyncPhase.SEMANTIC_GRAPH_WRITE)

    def load_dbt_only(self, artifacts_dir: Path) -> None:
        """Load dbt artifacts without semantic analysis."""
        logger.info(f"Loading dbt artifacts from {artifacts_dir}...")
        start_time = time.time()
        builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
        builder_time = time.time() - start_time
        logger.info(f"Builder time: {builder_time:.2f} seconds")
        start_time = time.time()
        builder.write_typed(self.storage)
        write_time = time.time() - start_time
        logger.info(f"Write time: {write_time:.2f} seconds")

    def reanalyze_semantics_only(
        self,
        artifacts_dir: Path,
        model_filter: Optional[str] = None,
        skip_clustering: bool = False,
        export_cache_override: Optional[bool] = None,
        verbose: bool = False,
    ) -> None:
        """Re-run semantic analysis without reloading dbt graph data."""
        # Store original export_cache setting and apply override
        original_export_cache = self.semantic_config.export_cache
        if export_cache_override is not None:
            self.semantic_config.export_cache = export_cache_override
            logger.info(f"   Export cache override: {export_cache_override}")

        try:
            # 1. Gather Metadata
            builder = LineageBuilder.from_dbt_artifacts(artifacts_dir)
            artifacts = builder.loader.load()
            models_list = list(artifacts.iter_models())
            logger.info(f"Found {len(models_list)} models")

            # Cache SQLGlot schema for SQL canonicalization.
            #
            # NOTE: `_create_batch_dataframe()` uses schema-aware canonicalization to enable
            # SELECT * expansion and column qualification. If we don't refresh this schema
            # in the reanalyze-only path, canonicalization will silently run without schema
            # context (or, worse, reuse a stale schema from a prior load).
            self._sqlglot_schema = artifacts.sqlglot_schema()

            # 2. Planning (Simplified for reanalyze mode)
            # We assume dbt data is already there, so we just want a plan for derived work.
            planner = SyncPlanner(
                storage=self.storage,
                enable_semantic=self.enable_semantic,
                enable_profiling=False,  # Reanalyze only does semantics/clustering
                enable_clustering=not skip_clustering and self.enable_clustering,
                enable_semantic_views=False,
                semantic_config=self.semantic_config,
            )
            plan = planner.create_plan(
                artifacts=artifacts,
                models_list=models_list,
                graph_was_empty=False,  # Assumed non-empty
                incremental=False,
                model_filter=model_filter,
                tracker=ProgressTracker(),
            )

            # 3. Execution
            session = self._create_fenic_session_if_needed(False)
            try:
                self._execute_derived_work(plan, session, verbose, ProgressTracker())

                if plan.run_clustering:
                    self._run_clustering(session, verbose)
            finally:
                if session:
                    session.stop()

        finally:
            self.semantic_config.export_cache = original_export_cache

    def run_clustering_only(self, verbose: bool = False) -> None:
        """Run join graph clustering only."""
        if not self.enable_clustering:
            logger.error("Clustering is disabled in configuration")
            return

        logger.info("Running join graph clustering...")
        session = self._create_fenic_session_if_needed(False)
        try:
            self._run_clustering(session, verbose)
        finally:
            if session:
                session.stop()


def load_full_lineage(
    artifacts_dir: Path,
    storage: LineageStorage,
    semantic_config: SemanticAnalysisConfig,
    profiling_config: ProfilingConfig,
    clustering_config: ClusteringConfig,
    semantic_view_config: SemanticViewLoaderConfig,
    data_backend: Optional[DataQueryBackend] = None,
    model_filter: Optional[str] = None,
    export_cache_override: Optional[bool] = None,
    incremental: bool = False,
    verbose: bool = False,
    graph_name: Optional[str] = None,
    progress_tracker: Optional[ProgressTracker] = None,
    fenic_db_path: Optional[Path] = None,
) -> None:
    """Convenience function to load dbt lineage with semantic analysis, profiling, and clustering."""
    if graph_name and hasattr(storage, 'set_active_graph'):
        storage.set_active_graph(graph_name)

    integration = LineageIntegration(
        storage,
        semantic_config=semantic_config,
        profiling_config=profiling_config,
        clustering_config=clustering_config,
        semantic_view_config=semantic_view_config,
        data_backend=data_backend,
        fenic_db_path=fenic_db_path,
    )
    integration.load_dbt_with_semantics(
        artifacts_dir,
        model_filter=model_filter,
        export_cache_override=export_cache_override,
        incremental=incremental,
        verbose=verbose,
        progress_tracker=progress_tracker,
    )

def _filter_models_for_semantic_analysis(
    models_list: list[DbtModelNode],
    model_filter: Optional[str] = None,
    change_set: Optional[ModelChangeSet] = None,
) -> list[DbtModelNode]:
    """Filter models eligible for semantic analysis.

    A model is eligible if it:
    - Has compiled SQL (seeds don't have SQL to analyze)
    - Is not a seed (seeds are raw data, not transformations)
    - Is not a semantic view (Snowflake semantic views use declarative YAML/DDL
      syntax rather than SQL queries, so SQLGlot-based analysis doesn't apply)
    - Matches the optional model_filter substring
    - Is in the change_set (if provided for incremental mode)

    Args:
        models_list: List of dbt models to filter
        model_filter: Optional substring filter for model IDs
        change_set: Optional change set for incremental mode

    Returns:
        Filtered list of models eligible for semantic analysis
    """
    # Count exclusions by reason
    no_sql_count = 0
    seed_count = 0
    semantic_view_count = 0
    filter_mismatch_count = 0
    not_in_changeset_count = 0

    eligible: list[DbtModelNode] = []

    for m in models_list:
        if not m.compiled_sql:
            no_sql_count += 1
            continue
        if m.resource_type == "seed":
            seed_count += 1
            continue
        if m.materialization == "semantic_view":
            semantic_view_count += 1
            continue
        if model_filter and model_filter not in m.unique_id:
            filter_mismatch_count += 1
            continue
        if change_set is not None and m.unique_id not in change_set.models_to_process:
            not_in_changeset_count += 1
            continue
        eligible.append(m)

    # Log exclusion summary
    total_excluded = no_sql_count + seed_count + semantic_view_count + filter_mismatch_count + not_in_changeset_count
    if total_excluded > 0:
        exclusion_parts = []
        if no_sql_count > 0:
            exclusion_parts.append(f"{no_sql_count} no SQL")
        if seed_count > 0:
            exclusion_parts.append(f"{seed_count} seeds")
        if semantic_view_count > 0:
            exclusion_parts.append(f"{semantic_view_count} semantic views")
        if filter_mismatch_count > 0:
            exclusion_parts.append(f"{filter_mismatch_count} filter mismatch")
        if not_in_changeset_count > 0:
            exclusion_parts.append(f"{not_in_changeset_count} not in changeset")

        logger.info(
            f"Semantic analysis: {len(eligible)} models eligible, "
            f"{total_excluded} excluded ({', '.join(exclusion_parts)})"
        )

    return eligible