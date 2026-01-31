"""Pipeline executor for running SQL analysis passes with checkpoint support."""

import logging
import time
import traceback
from typing import Callable, Optional

import fenic as fc

from lineage.ingest.config import PipelineConfig
from lineage.ingest.static_loaders.semantic.pipeline.dag import SQLAnalysisDAG

# Type alias for pass progress callback: (pass_name, current_pass_index, total_passes)
PassProgressCallback = Callable[[str, int, int], None]

logger = logging.getLogger(__name__)
# Better table names - descriptive and queryable
TABLE_NAME_MAP = {
    "relation_analysis": "relations",
    "column_analysis": "columns",
    "join_analysis": "joins",
    "filter_analysis": "filters",
    "grouping_by_scope": "grouping",
    "time_by_scope": "time_scope",
    "window_by_scope": "windows",
    "output_by_scope": "output_shape",
    "audit_analysis": "audit",
    "business_semantics": "business",
    "grain_humanization": "grain",
    "analysis_summary": "summary",
}


class PipelineExecutor:
    """Executes the SQL analysis pipeline with checkpoint support."""

    def __init__(self, session: fc.Session, pipeline_config: PipelineConfig):
        """Initialize the executor.

        Args:
            session: Fenic session for DataFrame operations
            pipeline_config: Pipeline configuration with model assignments and settings
        """
        self.session = session
        self.pipeline_config = pipeline_config
        self.dag = SQLAnalysisDAG(session, pipeline_config)
        self.execution_times = {}

    def run(
        self,
        df: fc.DataFrame,
        session: fc.Session,
        dbt_model_name: str,
        up_to_pass: str = None,
        from_pass: str = None,
        progress_callback: Optional[PassProgressCallback] = None,
    ) -> fc.DataFrame:
        """Execute the pipeline on the input DataFrame.

        Args:
            df: Input DataFrame with SQL queries
            session: Fenic session for table operations
            dbt_model_name: Name of the dbt model being analyzed
            up_to_pass: Stop execution after this pass (inclusive)
            from_pass: Start execution from this pass (load previous from checkpoint)
            progress_callback: Optional callback for progress updates.
                Called after each pass with (pass_name, current_index, total_passes).

        Returns:
            DataFrame with all analysis results
        """
        self.session = session
        df = self._ensure_base_columns(df)

        # Validate DAG first
        self.dag.validate_dag()

        # Get execution order
        execution_order = self.dag.get_execution_order()

        # Filter passes based on up_to/from parameters
        if up_to_pass:
            try:
                up_to_idx = execution_order.index(up_to_pass) + 1
                execution_order = execution_order[:up_to_idx]
            except ValueError as e:
                raise ValueError(f"Pass '{up_to_pass}' not found in execution order") from e

        if from_pass:
            try:
                from_idx = execution_order.index(from_pass)
                execution_order = execution_order[from_idx:]

                # Load checkpoint for starting point
                if from_idx > 0:
                    # Check if the from_pass itself has a checkpoint
                    if self._checkpoint_exists(session, from_pass):
                        # Just load it directly - no need to re-execute
                        df = self._load_checkpoint(session, from_pass)
                        print(
                            f"  ↻ Resuming from checkpoint: {self._get_table_name(from_pass)}"
                        )
                        # Skip the first pass in execution_order since we already loaded it
                        execution_order = execution_order[1:]
                    else:
                        # Load from nearest earlier checkpoint and execute up to (but not including) from_pass
                        df = self._load_from_nearest_checkpoint(session, from_pass, df)
            except ValueError as e:
                raise ValueError(f"Pass '{from_pass}' not found in execution order") from e

        # Debug output removed (can add back if needed)

        # Execute passes in order
        total_passes = len(execution_order)
        for pass_index, pass_name in enumerate(execution_order):
            if self._should_skip_pass(pass_name):
                # Add stub column for skipped pass so downstream passes can reference it
                df = self._add_stub_column_for_skipped_pass(df, pass_name)
                # Still count skipped passes for progress
                if progress_callback:
                    progress_callback(pass_name, pass_index + 1, total_passes)
                continue

            # Execute the pass
            df, success = self._execute_pass(pass_name, df, dbt_model_name)

            # Fire progress callback after pass completes
            if progress_callback:
                progress_callback(pass_name, pass_index + 1, total_passes)

        return df

    def _ensure_base_columns(self, df: fc.DataFrame) -> fc.DataFrame:
        """Ensure base metadata columns required by downstream passes exist."""
        required_columns = {
            "path": None,
            "filename": None,
        }
        for column_name, default_value in required_columns.items():
            if column_name not in df.columns:
                df = df.with_column(column_name, fc.lit(default_value))
        return df

    def _execute_pass(
        self, pass_name: str, df: fc.DataFrame, dbt_model_name: str
    ) -> tuple[fc.DataFrame, bool]:
        """Execute a single pass.

        Returns:
            Tuple of (DataFrame, success_bool)
        """
        pass_instance = self.dag.get_pass(pass_name)

        start_time = time.time()

        try:
            # Validate inputs
            pass_instance.validate_inputs(df)

            # Execute pass
            df = pass_instance.execute(df).cache()
            # force evaluation here, so if an exception is raised, the error is not hidden by the lazy evaluation
            row_count = df.count()
            elapsed = time.time() - start_time
            self.execution_times[pass_name] = elapsed

            # Format log message based on batch vs single-model context
            if dbt_model_name == "batch_analysis":
                # Batch processing mode - row count indicates number of models
                model_str = f"{row_count} models" if row_count > 1 else "1 model"
                logger.info(f"  ✅ {pass_name} executed successfully for batch ({model_str}) in {elapsed:.2f}s")
            else:
                # Per-model processing mode
                logger.info(f"  ✅ {pass_name} executed successfully for {dbt_model_name} in {elapsed:.2f}s")

            return df, True

        except Exception as e:
            error_type = type(e).__name__

            # Format error message based on batch vs single-model context
            if dbt_model_name == "batch_analysis":
                logger.error(f"✗ Error in {pass_name} for batch ({error_type}) {traceback.format_exc()}")
            else:
                logger.error(f"✗ Error in {pass_name} for model {dbt_model_name} ({error_type}) {traceback.format_exc()}")

            raise

    def _should_skip_pass(self, pass_name: str) -> bool:
        """Check if pass should be skipped based on settings."""
        # All passes are now enabled by default
        # Audit is controlled by pipeline_config.enable_audit
        if pass_name == "audit_analysis": #nosec: B105 -- not a password
            return not self.pipeline_config.enable_audit
        return False

    def _add_stub_column_for_skipped_pass(
        self, df: fc.DataFrame, pass_name: str
    ) -> fc.DataFrame:
        """Add stub column when a pass is skipped so downstream passes can reference it.

        Creates an empty array column using fc.empty() with ArrayType.
        """
        # trunk-ignore(bandit/B105): not a password
        if pass_name == "time_analysis":
            # Add empty time_by_scope column (empty array)
            df = df.with_column(
                "time_by_scope",
                fc.empty(fc.ArrayType(fc.StringType))
            )
        # trunk-ignore(bandit/B105): not a password
        elif pass_name == "window_analysis":
            # Add empty window_by_scope column (empty array)
            df = df.with_column(
                "window_by_scope",
                fc.empty(fc.ArrayType(fc.StringType))
            )

        return df

    def _should_checkpoint(self, pass_name: str) -> bool:
        """Determine if a pass should be checkpointed."""
        # Checkpointing disabled for simplified config
        return False

    def _get_table_name(self, pass_name: str) -> str:
        """Get the table name for a checkpoint."""
        short_name = TABLE_NAME_MAP.get(pass_name, pass_name)
        return f"sql_analyzer_{short_name}"

    def _save_checkpoint(
        self, df: fc.DataFrame, session: fc.Session, pass_name: str
    ) -> tuple[fc.DataFrame, bool]:
        """Save DataFrame checkpoint as a table.

        Returns:
            Tuple of (DataFrame, success_bool)
        """
        table_name = self._get_table_name(pass_name)

        try:
            # Cache in memory first to avoid re-evaluation
            df = df.persist()

            # Save as table (overwrites if exists)
            df.write.save_as_table(table_name, mode="overwrite")

            return df, True

        except Exception as e:
            print(f"  ⚠️  Warning: Failed to save checkpoint for {pass_name}: {e}")
            return df, False

    def _load_checkpoint(self, session: fc.Session, pass_name: str) -> fc.DataFrame:
        """Load DataFrame from checkpoint table."""
        table_name = self._get_table_name(pass_name)

        try:
            return session.table(table_name)
        except Exception:
            return None

    def _checkpoint_exists(self, session: fc.Session, pass_name: str) -> bool:
        """Check if a checkpoint table exists."""
        table_name = self._get_table_name(pass_name)

        try:
            # Try to get table schema - if it works, table exists
            tables = session.catalog.list_tables()
            return table_name in tables
        except Exception:
            return False

    def _load_from_nearest_checkpoint(
        self, session: fc.Session, target_pass: str, fallback_df: fc.DataFrame
    ) -> fc.DataFrame:
        """Load from the nearest checkpoint before the target pass."""
        execution_order = self.dag.get_execution_order()
        target_idx = execution_order.index(target_pass)

        # Search backwards for nearest checkpoint
        for i in range(target_idx - 1, -1, -1):
            pass_name = execution_order[i]
            if self._checkpoint_exists(session, pass_name):
                df = self._load_checkpoint(session, pass_name)
                if df is not None:
                    print(
                        f"  ↻ Resuming from checkpoint: {self._get_table_name(pass_name)}"
                    )

                    # Execute passes between checkpoint and target
                    for j in range(i + 1, target_idx):
                        intermediate_pass = execution_order[j]
                        if not self._should_skip_pass(intermediate_pass):
                            df, _ = self._execute_pass(intermediate_pass, df)

                    return df

        # No checkpoint found, use fallback
        logger.info("No checkpoint found, starting from beginning")

        # Execute all passes up to target
        for i in range(0, target_idx):
            pass_name = execution_order[i]
            if not self._should_skip_pass(pass_name):
                fallback_df, _ = self._execute_pass(pass_name, fallback_df)

        return fallback_df

    def list_checkpoints(self, session: fc.Session) -> list[str]:
        """List all available checkpoint tables."""
        try:
            tables = session.catalog.list_tables()
            prefix = "sql_analyzer_"
            return [t for t in tables if t.startswith(prefix)]
        except Exception as e:
            print(f"Error listing checkpoints: {e}")
            return []

    def clear_checkpoints(self, session: fc.Session):
        """Clear all checkpoint tables."""
        checkpoints = self.list_checkpoints(session)
        for table in checkpoints:
            try:
                session.catalog.drop_table(table)
                print(f"  🗑️  Dropped checkpoint: {table}")
            except Exception as e:
                print(f"  ⚠️  Failed to drop {table}: {e}")
