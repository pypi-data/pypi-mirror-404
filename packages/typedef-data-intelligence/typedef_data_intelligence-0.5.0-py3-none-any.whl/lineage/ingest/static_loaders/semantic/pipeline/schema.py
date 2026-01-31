"""Explicit schema builder for hybrid analysis results.

Uses Fenic's schema utilities to convert Pydantic models to Polars schemas,
avoiding type inference issues with Null values and inconsistent struct schemas.

SCHEMA ARCHITECTURE
-------------------
The semantic analysis pipeline has two categories of Polars schemas:

1. **Final Output Schema** (this module):
   - `build_hybrid_result_schema()` - defines the DataFrame schema for pipeline results
   - Uses Fenic utilities to auto-generate struct types from Pydantic models
   - Used by HybridPipelineExecutor._merge_and_build_dataframe()

2. **Internal Batch Schemas** (in targeted classification modules):
   - `_build_classification_input_schema()` in column_classification.py
   - `_build_filter_intent_batch_schema()` in filter_intent.py
   - These are LOCAL helpers for structuring input/output of Fenic batch LLM calls
   - They're intentionally co-located with their consumers to keep context together

The separation is intentional: final output schemas belong here (centralized),
while batch processing schemas stay with their specific pass implementations.
"""

from typing import Optional

import polars as pl
from fenic.core._utils.schema import (
    convert_custom_dtype_to_polars,
    convert_custom_schema_to_polars_schema,
    convert_pydantic_type_to_custom_struct_type,
)
from fenic.core.types.datatypes import (
    ArrayType,
    StringType,
    StructField,
    StructType,
)
from fenic.core.types.schema import ColumnField, Schema

from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    ColumnClassificationResult,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.filter_intent import (
    FilterIntentResult,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    IncrementalWatermarkResult,
)

# Note: PIIDetectionResult removed - PII fields merged into ColumnClassificationResult
from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    TimeClassificationResult,
)
from lineage.ingest.static_loaders.semantic.models.analytical import (
    GroupingAnalysis,
    OutputShapeAnalysis,
    TimeAnalysis,
)
from lineage.ingest.static_loaders.semantic.models.business import (
    BusinessSemantics,
    GrainHumanization,
)
from lineage.ingest.static_loaders.semantic.models.technical import (
    ColumnAnalysis,
    FilterAnalysis,
    JoinEdgeAnalysis,
    RelationAnalysis,
)

# Cache the schema since it's expensive to build
_CACHED_SCHEMA: Optional[pl.Schema] = None


def _build_grouping_by_scope_type() -> StructType:
    """Build the grouping_by_scope struct type.

    Structure: {scope: str, grouping_for_scope: GroupingAnalysis}
    """
    return StructType([
        StructField("scope", StringType),
        StructField(
            "grouping_for_scope",
            convert_pydantic_type_to_custom_struct_type(GroupingAnalysis)
        ),
    ])


def _build_time_by_scope_type() -> StructType:
    """Build the time_by_scope struct type.

    Structure: {scope: str, time_for_scope: TimeAnalysis}
    """
    return StructType([
        StructField("scope", StringType),
        StructField(
            "time_for_scope",
            convert_pydantic_type_to_custom_struct_type(TimeAnalysis)
        ),
    ])


def _build_window_by_scope_type() -> StructType:
    """Build the window_by_scope struct type.

    Structure: {scope: str, window_analysis_json: str}
    Note: window_analysis is stored as JSON string in the legacy schema.
    """
    return StructType([
        StructField("scope", StringType),
        StructField("window_analysis_json", StringType),
    ])


def _build_output_by_scope_type() -> StructType:
    """Build the output_by_scope struct type.

    Structure: {scope: str, output_for_scope: OutputShapeAnalysis}
    """
    return StructType([
        StructField("scope", StringType),
        StructField(
            "output_for_scope",
            convert_pydantic_type_to_custom_struct_type(OutputShapeAnalysis)
        ),
    ])


def build_hybrid_result_schema() -> pl.Schema:
    """Build explicit Polars schema for hybrid analysis results.

    This schema matches the existing table schema used by the LLM pipeline,
    allowing hybrid results to append to existing tables.

    Returns:
        Polars schema with explicit types for all columns
    """
    global _CACHED_SCHEMA
    if _CACHED_SCHEMA is not None:
        return _CACHED_SCHEMA

    column_fields = [
        # Simple string columns
        ColumnField(name="model_id", data_type=StringType),
        ColumnField(name="model_name", data_type=StringType),
        ColumnField(name="path", data_type=StringType),
        ColumnField(name="filename", data_type=StringType),
        ColumnField(name="sql", data_type=StringType),
        ColumnField(name="canonical_sql", data_type=StringType),
        # dbt metadata for downstream passes
        ColumnField(name="materialization", data_type=StringType),
        ColumnField(name="model_description", data_type=StringType),

        # Technical analysis structs (Passes 1-4)
        ColumnField(
            name="relation_analysis",
            data_type=convert_pydantic_type_to_custom_struct_type(RelationAnalysis)
        ),
        ColumnField(
            name="column_analysis",
            data_type=convert_pydantic_type_to_custom_struct_type(ColumnAnalysis)
        ),
        ColumnField(
            name="join_analysis",
            data_type=convert_pydantic_type_to_custom_struct_type(JoinEdgeAnalysis)
        ),
        ColumnField(
            name="filter_analysis",
            data_type=convert_pydantic_type_to_custom_struct_type(FilterAnalysis)
        ),

        # Analytical scoped arrays (Passes 5-8)
        # All *_by_scope columns are arrays for consistency
        # Each element: {scope: str, <analysis>_for_scope: <AnalysisType>}
        ColumnField(
            name="grouping_by_scope",
            data_type=ArrayType(_build_grouping_by_scope_type())
        ),
        ColumnField(
            name="time_by_scope",
            data_type=ArrayType(_build_time_by_scope_type())
        ),
        ColumnField(
            name="window_by_scope",
            data_type=ArrayType(_build_window_by_scope_type())
        ),
        ColumnField(
            name="output_by_scope",
            data_type=ArrayType(_build_output_by_scope_type())
        ),

        # Business semantics (Pass 10)
        ColumnField(
            name="business_semantics",
            data_type=convert_pydantic_type_to_custom_struct_type(BusinessSemantics)
        ),

        # Grain humanization (Pass 10a)
        ColumnField(
            name="grain_humanization",
            data_type=convert_pydantic_type_to_custom_struct_type(GrainHumanization)
        ),

        # Analysis summary (Pass 11)
        ColumnField(name="analysis_summary", data_type=StringType),

        # Targeted classification results (heuristic-based)
        ColumnField(
            name="time_classification",
            data_type=convert_pydantic_type_to_custom_struct_type(TimeClassificationResult)
        ),
        ColumnField(
            name="semantic_classification",
            data_type=convert_pydantic_type_to_custom_struct_type(ColumnClassificationResult)
        ),
        ColumnField(
            name="filter_intent",
            data_type=convert_pydantic_type_to_custom_struct_type(FilterIntentResult)
        ),
        # Note: pii_detection removed - PII fields (pii_columns, high_risk_pii_count) now in semantic_classification
        ColumnField(
            name="incremental_watermark",
            data_type=convert_pydantic_type_to_custom_struct_type(IncrementalWatermarkResult)
        ),
    ]

    fenic_schema = Schema(column_fields=column_fields)
    _CACHED_SCHEMA = convert_custom_schema_to_polars_schema(fenic_schema)
    return _CACHED_SCHEMA


def get_polars_dtype_for_model(model_class: type) -> pl.DataType:
    """Get the Polars dtype for a Pydantic model class.

    Args:
        model_class: A Pydantic BaseModel subclass

    Returns:
        Corresponding Polars struct type
    """
    fenic_type = convert_pydantic_type_to_custom_struct_type(model_class)
    return convert_custom_dtype_to_polars(fenic_type)
