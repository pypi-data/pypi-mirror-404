"""Change detection for incremental lineage loading.

Compares per-model fingerprints (derived from compiled SQL) against graph state to
identify added, modified, removed, and unchanged models.

Also supports test change detection with independent fingerprinting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

from lineage.ingest.progress import ProgressTracker, SyncPhase
from lineage.ingest.static_loaders.dbt.dbt_test_fingerprint import (
    compute_test_fingerprint,
    compute_unit_test_fingerprint,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    compute_model_fingerprint_result,
)

# Type alias for dialect resolver function: maps model unique_id -> sqlglot dialect
DialectResolver = Callable[[str], Optional[str]]

if TYPE_CHECKING:
    from lineage.backends.lineage.protocol import LineageStorage
    from lineage.ingest.static_loaders.dbt.dbt_loader import DbtArtifacts

logger = logging.getLogger(__name__)


def _is_empty_graph_error(error: Exception) -> bool:
    """Check if error indicates an empty/non-existent graph."""
    error_str = str(error).lower()
    return any(msg in error_str for msg in ["does not exist", "not found", "no such"])


@dataclass
class ModelChangeSet:
    """Results of comparing current vs. cached fingerprints."""

    added: list[str]  # New model unique_ids
    modified: list[str]  # Changed model unique_ids
    removed: list[str]  # Deleted model unique_ids
    unchanged: list[str]  # Same checksum

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.added or self.modified or self.removed)

    @property
    def models_to_process(self) -> list[str]:
        """Models needing re-analysis (added + modified)."""
        return self.added + self.modified


@dataclass
class TestChangeSet:
    """Results of comparing current vs. cached test fingerprints."""

    added: list[str]  # New test unique_ids
    modified: list[str]  # Changed test unique_ids
    removed: list[str]  # Deleted test unique_ids
    unchanged: list[str]  # Same fingerprint

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.added or self.modified or self.removed)

    @property
    def tests_to_process(self) -> list[str]:
        """Tests needing re-processing (added + modified)."""
        return self.added + self.modified


@dataclass
class UnitTestChangeSet:
    """Results of comparing current vs. cached unit test fingerprints."""

    added: list[str]  # New unit test unique_ids
    modified: list[str]  # Changed unit test unique_ids
    removed: list[str]  # Deleted unit test unique_ids
    unchanged: list[str]  # Same fingerprint

    @property
    def has_changes(self) -> bool:
        """Check if any changes were detected."""
        return bool(self.added or self.modified or self.removed)

    @property
    def tests_to_process(self) -> list[str]:
        """Unit tests needing re-processing (added + modified)."""
        return self.added + self.modified


class ChangeDetector:
    """Detects changes in dbt models by comparing fingerprints."""

    def detect_changes(
        self,
        artifacts: DbtArtifacts,
        storage: LineageStorage,
        dialect_resolver: Optional[DialectResolver] = None,
        tracker: Optional[ProgressTracker] = None,
    ) -> ModelChangeSet:
        """Detect changes by comparing manifest-derived fingerprints against graph state.

        Args:
            artifacts: DbtArtifacts from current manifest
            storage: LineageStorage to query for existing fingerprints
            dialect_resolver: Optional function mapping model unique_id -> sqlglot dialect
                to use for fingerprinting. If omitted, falls back to artifacts.adapter_type.
            tracker: Optional progress tracker for UI updates

        Returns:
            ModelChangeSet with added, modified, removed, and unchanged models
        """
        if tracker:
            tracker.phase_start(SyncPhase.CHANGE_DETECTION, artifacts.model_count, "Comparing fingerprints")

        # 1. Load current fingerprints and model IDs from graph (single query)
        current_fingerprints, existing_model_ids = self._load_graph_state(storage)

        if not existing_model_ids:
            logger.info("Graph is empty, treating all models as added")
            artifacts_model_ids = set(model.unique_id for model in artifacts.iter_models())
            if tracker:
                tracker.phase_complete(SyncPhase.CHANGE_DETECTION)
            return ModelChangeSet(
                added=list(artifacts_model_ids),
                modified=[],
                removed=[],
                unchanged=[],
            )

        # 2. Build manifest fingerprints dict (full scan over artifacts)
        manifest_fingerprints: dict[str, str] = {}
        manifest_model_ids: set[str] = set()
        # Get schema from artifacts for macro-aware fingerprinting (SELECT * expansion)
        # physically_agnostic=True inside compute_model_fingerprint_result handles stripping.
        sqlglot_schema = artifacts.sqlglot_schema()

        for idx, model in enumerate(artifacts.iter_models(), 1):
            manifest_model_ids.add(model.unique_id)

            try:
                # Use qualified_sql if available (already physically resolved), otherwise use compiled_sql.
                # Note: At change detection time, models from dbt-loader don't yet have qualified_sql.
                # compute_model_fingerprint_result handles qualification internally via the schema parameter.
                
                # Determine dialect for this model
                dialect = (
                    dialect_resolver(model.unique_id)
                    if dialect_resolver
                    else artifacts.adapter_type
                )

                # Compute fingerprint using shared helper (stores hash only, no prefix)
                checksum_value = model.checksum.checksum if model.checksum else None
                fp_result = compute_model_fingerprint_result(
                    resource_type=model.resource_type,
                    compiled_sql=model.compiled_sql,
                    checksum=checksum_value,
                    dialect=dialect,
                    schema=sqlglot_schema,
                    model_id=model.unique_id,
                )
                if fp_result:
                    manifest_fingerprints[model.unique_id] = fp_result.hash
                else:
                    # No fingerprint possible - treat conservatively
                    logger.warning(
                        f"Could not compute fingerprint for {model.unique_id}, "
                        f"treating as modified for safety"
                    )
            except Exception as e:
                # Log error but continue processing other models
                logger.error(
                    f"Error computing fingerprint for {model.unique_id}: {e}",
                    exc_info=True,
                )
                # Treat as modified to ensure it gets processed
                # (safer than treating as unchanged)
            
            if tracker and (idx % 10 == 0 or idx == artifacts.model_count):
                tracker.update(SyncPhase.CHANGE_DETECTION, idx, artifacts.model_count, details=f"Fingerprinted {idx} models")

        # 3. Compare and categorize
        added: list[str] = []
        modified: list[str] = []
        removed: list[str] = []
        unchanged: list[str] = []

        # Added / modified / unchanged based on fingerprint equality.
        #
        # Note: if a model doesn't have compiled_sql (or fingerprinting failed),
        # we treat it as modified (if it exists) to keep correctness.
        for model_id in manifest_model_ids:
            if model_id not in existing_model_ids:
                added.append(model_id)
                continue

            manifest_fp = manifest_fingerprints.get(model_id)
            if not manifest_fp:
                modified.append(model_id)
                continue

            current_fp = current_fingerprints.get(model_id)
            if current_fp != manifest_fp:
                modified.append(model_id)
            else:
                unchanged.append(model_id)

        # Removed models (in graph but not in manifest)
        for model_id in existing_model_ids:
            if model_id not in manifest_model_ids:
                removed.append(model_id)

        logger.info(
            f"Change detection: {len(added)} added, {len(modified)} modified, "
            f"{len(removed)} removed, {len(unchanged)} unchanged"
        )

        if tracker:
            tracker.phase_complete(SyncPhase.CHANGE_DETECTION)

        return ModelChangeSet(
            added=added,
            modified=modified,
            removed=removed,
            unchanged=unchanged,
        )

    def _load_graph_state(
        self, storage: LineageStorage
    ) -> tuple[dict[str, str], set[str]]:
        """Load fingerprints and model IDs from graph in a single query.

        This combines what was previously two separate queries to reduce
        database round-trips.

        Args:
            storage: LineageStorage to query

        Returns:
            Tuple of (fingerprints dict, model_ids set):
            - fingerprints: Dictionary mapping model_id -> model_fingerprint
              (only includes models that have a fingerprint)
            - model_ids: Set of all model unique_ids in the graph
              (includes models without fingerprints)
        """
        query = """
            MATCH (m:DbtModel)
            RETURN m.id AS id, m.model_fingerprint AS model_fingerprint
        """

        try:
            result = storage.execute_raw_query(query)
            fingerprints: dict[str, str] = {}
            model_ids: set[str] = set()

            for row in result.rows:
                model_id = row.get("id")
                if model_id:
                    model_ids.add(model_id)
                    fingerprint = row.get("model_fingerprint")
                    if fingerprint:
                        fingerprints[model_id] = fingerprint

            logger.debug(
                f"Loaded {len(model_ids)} models ({len(fingerprints)} with fingerprints) from graph"
            )
            return fingerprints, model_ids

        except Exception as e:
            # Connection/infrastructure errors should fail fast
            if isinstance(e, (ConnectionError, TimeoutError, OSError)):
                logger.error(f"Database connection failed while loading graph state: {e}")
                raise

            # Schema/table doesn't exist -> empty graph is expected
            if _is_empty_graph_error(e):
                logger.debug(f"Graph appears empty (no DbtModel table): {e}")
                return {}, set()
            # Unexpected errors - log with traceback but treat as empty to allow recovery
            logger.warning(f"Failed to load graph state: {e}", exc_info=True)
            return {}, set()

    def detect_test_changes(
        self,
        artifacts: DbtArtifacts,
        storage: LineageStorage,
    ) -> TestChangeSet:
        """Detect changes in dbt tests by comparing fingerprints.

        Args:
            artifacts: DbtArtifacts from current manifest
            storage: LineageStorage to query for existing fingerprints

        Returns:
            TestChangeSet with added, modified, removed, and unchanged tests
        """
        # 1. Load current fingerprints and test IDs from graph
        current_fingerprints, existing_test_ids = self._load_test_graph_state(storage)

        # 2. Build manifest fingerprints dict
        manifest_fingerprints: dict[str, str] = {}
        manifest_test_ids: set[str] = set()
        for test in artifacts.iter_tests():
            manifest_test_ids.add(test.unique_id)
            fp = compute_test_fingerprint(
                test_type=test.test_type,
                test_name=test.test_name,
                column_name=test.column_name,
                model_id=test.model_id,
                test_kwargs=test.test_kwargs,
                severity=test.severity,
                where_clause=test.where_clause,
                store_failures=test.store_failures,
            )
            manifest_fingerprints[test.unique_id] = fp

        # 3. Compare and categorize
        added: list[str] = []
        modified: list[str] = []
        removed: list[str] = []
        unchanged: list[str] = []

        for test_id in manifest_test_ids:
            if test_id not in existing_test_ids:
                added.append(test_id)
                continue

            manifest_fp = manifest_fingerprints.get(test_id)
            current_fp = current_fingerprints.get(test_id)
            if current_fp != manifest_fp:
                modified.append(test_id)
            else:
                unchanged.append(test_id)

        # Removed tests (in graph but not in manifest)
        for test_id in existing_test_ids:
            if test_id not in manifest_test_ids:
                removed.append(test_id)

        logger.info(
            f"Test change detection: {len(added)} added, {len(modified)} modified, "
            f"{len(removed)} removed, {len(unchanged)} unchanged"
        )

        return TestChangeSet(
            added=added,
            modified=modified,
            removed=removed,
            unchanged=unchanged,
        )

    def _load_test_graph_state(
        self, storage: LineageStorage
    ) -> tuple[dict[str, str], set[str]]:
        """Load test fingerprints and IDs from graph.

        Args:
            storage: LineageStorage to query

        Returns:
            Tuple of (fingerprints dict, test_ids set)
        """
        query = """
            MATCH (t:DbtTest)
            RETURN t.id AS id, t.test_fingerprint AS test_fingerprint
        """

        try:
            result = storage.execute_raw_query(query)
            fingerprints: dict[str, str] = {}
            test_ids: set[str] = set()

            for row in result.rows:
                test_id = row.get("id")
                if test_id:
                    test_ids.add(test_id)
                    fingerprint = row.get("test_fingerprint")
                    if fingerprint:
                        fingerprints[test_id] = fingerprint

            logger.debug(
                f"Loaded {len(test_ids)} tests ({len(fingerprints)} with fingerprints) from graph"
            )
            return fingerprints, test_ids

        except Exception as e:
            if isinstance(e, (ConnectionError, TimeoutError, OSError)):
                logger.error(f"Database connection failed while loading test state: {e}")
                raise

            if _is_empty_graph_error(e):
                logger.debug(f"Graph appears empty (no DbtTest table): {e}")
                return {}, set()

            logger.warning(f"Failed to load test graph state: {e}", exc_info=True)
            return {}, set()

    def detect_unit_test_changes(
        self,
        artifacts: DbtArtifacts,
        storage: LineageStorage,
    ) -> UnitTestChangeSet:
        """Detect changes in dbt unit tests by comparing fingerprints.

        Args:
            artifacts: DbtArtifacts from current manifest
            storage: LineageStorage to query for existing fingerprints

        Returns:
            UnitTestChangeSet with added, modified, removed, and unchanged unit tests
        """
        # 1. Load current fingerprints and unit test IDs from graph
        current_fingerprints, existing_test_ids = self._load_unit_test_graph_state(storage)

        # 2. Build manifest fingerprints dict
        manifest_fingerprints: dict[str, str] = {}
        manifest_test_ids: set[str] = set()
        for unit_test in artifacts.iter_unit_tests():
            manifest_test_ids.add(unit_test.unique_id)
            fp = compute_unit_test_fingerprint(
                model_id=unit_test.model_id,
                given=unit_test.given,
                expect=unit_test.expect,
                overrides=unit_test.overrides,
            )
            manifest_fingerprints[unit_test.unique_id] = fp

        # 3. Compare and categorize
        added: list[str] = []
        modified: list[str] = []
        removed: list[str] = []
        unchanged: list[str] = []

        for test_id in manifest_test_ids:
            if test_id not in existing_test_ids:
                added.append(test_id)
                continue

            manifest_fp = manifest_fingerprints.get(test_id)
            current_fp = current_fingerprints.get(test_id)
            if current_fp != manifest_fp:
                modified.append(test_id)
            else:
                unchanged.append(test_id)

        # Removed unit tests (in graph but not in manifest)
        for test_id in existing_test_ids:
            if test_id not in manifest_test_ids:
                removed.append(test_id)

        logger.info(
            f"Unit test change detection: {len(added)} added, {len(modified)} modified, "
            f"{len(removed)} removed, {len(unchanged)} unchanged"
        )

        return UnitTestChangeSet(
            added=added,
            modified=modified,
            removed=removed,
            unchanged=unchanged,
        )

    def _load_unit_test_graph_state(
        self, storage: LineageStorage
    ) -> tuple[dict[str, str], set[str]]:
        """Load unit test fingerprints and IDs from graph.

        Args:
            storage: LineageStorage to query

        Returns:
            Tuple of (fingerprints dict, test_ids set)
        """
        query = """
            MATCH (t:DbtUnitTest)
            RETURN t.id AS id, t.test_fingerprint AS test_fingerprint
        """

        try:
            result = storage.execute_raw_query(query)
            fingerprints: dict[str, str] = {}
            test_ids: set[str] = set()

            for row in result.rows:
                test_id = row.get("id")
                if test_id:
                    test_ids.add(test_id)
                    fingerprint = row.get("test_fingerprint")
                    if fingerprint:
                        fingerprints[test_id] = fingerprint

            logger.debug(
                f"Loaded {len(test_ids)} unit tests ({len(fingerprints)} with fingerprints) from graph"
            )
            return fingerprints, test_ids

        except Exception as e:
            if isinstance(e, (ConnectionError, TimeoutError, OSError)):
                logger.error(f"Database connection failed while loading unit test state: {e}")
                raise

            if _is_empty_graph_error(e):
                logger.debug(f"Graph appears empty (no DbtUnitTest table): {e}")
                return {}, set()

            logger.warning(f"Failed to load unit test graph state: {e}", exc_info=True)
            return {}, set()

