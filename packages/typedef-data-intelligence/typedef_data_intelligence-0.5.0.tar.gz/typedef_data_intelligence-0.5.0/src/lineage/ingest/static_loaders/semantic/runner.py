"""Semantic analysis runner - bridges analyzer pipeline and loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from lineage.ingest.config import PipelineConfig
from lineage.ingest.static_loaders.semantic.pipeline.executor import (
    PipelineExecutor,
)
from lineage.ingest.static_loaders.semantic.utils.data_loaders import load_sql_files
from lineage.ingest.static_loaders.semantic.utils.sql_operations import (
    canonicalize_sql_udf,
)

# Import from the migrated analyzer
try:
    import fenic as fc

    FENIC_AVAILABLE = True
except ImportError:
    FENIC_AVAILABLE = False


def analyze_model_sql(
    compiled_sql: str,
    session: fc.Session,
    dbt_model_name: str,
    pipeline_config: PipelineConfig,
    dialect: str = "duckdb",
    verbose: bool = False,
    canonical_sql: Optional[str] = None,
) -> Dict[str, Any]:
    """Run semantic analysis on a single SQL query.

    Args:
        compiled_sql: The compiled SQL to analyze
        session: Fenic session to reuse
        dbt_model_name: Name for this model (used in temp file)
        pipeline_config: Pipeline configuration with model assignments
        dialect: SQL dialect (duckdb, snowflake, etc.)
        verbose: Enable verbose output
        canonical_sql: Pre-computed canonical SQL. When provided, skips the
            expensive canonicalize_sql UDF. The builder already persists this
            on the DbtModel node, so callers should pass it when available.

    Returns:
        Dictionary with analysis results from all passes

    Raises:
        ImportError: If Fenic is not available
        RuntimeError: If analysis fails
    """
    # Create a temporary directory with the SQL file
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())
    sql_file = temp_dir / f"{dbt_model_name}.sql"
    sql_file.write_text(compiled_sql)

    try:

        # Load SQL file as DataFrame
        df = load_sql_files(str(sql_file), session)

        # Use pre-computed canonical SQL if provided, otherwise compute via UDF
        if canonical_sql:
            df = df.with_column("canonical_sql", fc.lit(canonical_sql))
        else:
            df = df.with_column("canonical_sql", canonicalize_sql_udf(fc.col("sql"), fc.lit(dialect)))

        # Create and execute pipeline
        executor = PipelineExecutor(session, pipeline_config)
        result_df = executor.run(df, session, dbt_model_name=dbt_model_name)

        # Extract results from DataFrame
        # The result DataFrame should have one row with all analysis columns
        results = _extract_results_from_df(result_df)
        return results

    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def _extract_results_from_df(df: fc.DataFrame) -> Dict[str, Any]:
    """Extract analysis results from Fenic DataFrame.

    The DataFrame has columns for each analysis pass:
    - relation_analysis
    - column_analysis
    - join_analysis
    - filter_analysis
    - grouping_analysis
    - time_analysis
    - window_analysis
    - output_shape_analysis
    - audit_analysis
    - business_semantics
    - grain_humanization
    """
    # Collect the DataFrame (evaluates lazy operations)
    collected: fc.QueryResult = df.to_pylist()
    if len(collected) == 0:
        raise RuntimeError("Analysis returned no results")

    row = collected[0]

    # Build results dictionary
    results = {}

    # Map DataFrame column names to result keys
    pass_columns = [
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

    for col in pass_columns:
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


def create_placeholder_analysis(model_name: str) -> Dict[str, Any]:
    """Create placeholder analysis results when Fenic is not available.

    This allows the system to work without semantic analysis.
    """
    return {
        "relation_analysis": {"relations": [], "tables": []},
        "column_analysis": {"columns_by_alias": [], "column_refs": []},
        "join_analysis": {"joins": []},
        "filter_analysis": {"where": [], "having": [], "qualify": []},
        "grouping_analysis": {"select": [], "group_by": [], "is_aggregated": False, "result_grain": []},
        "time_analysis": {"time_scope": None, "normalized_time_scope": None, "time_buckets": [], "time_columns": []},
        "window_analysis": {"windows": []},
        "output_shape_analysis": {"order_by": [], "limit": None, "select_distinct": False},
        "audit_analysis": {"findings": []},
        "business_semantics": {
            "grain_human": "unknown",
            "measures": [],
            "dimensions": [],
            "segments": [],
            "intent": "unknown",
        },
        "grain_humanization": {"grain_human": "unknown", "tokens": []},
    }
