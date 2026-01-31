"""Targeted LLM passes using deterministic analysis results.

These passes convert open-ended extraction tasks into focused classification tasks
by providing structured data from deterministic analysis as input.

Architecture:
- Input: Structured data from deterministic passes (columns, relations, etc.)
- Task: Simple classification (time column? fact or dimension? PII?)
- Model: Haiku (fast, cheap, sufficient for classification)
- Parallelization: Each model's classification runs independently

Benefits:
- 70%+ cheaper than full extraction (structured input, smaller model)
- Faster response times (less text to process)
- More consistent results (classification vs extraction)
- Easily parallelizable (all calls are independent)
"""

from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    ColumnClassification,
    ColumnClassificationResult,
    QueryMetadata,
    classify_columns,
    heuristic_column_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.filter_intent import (
    FilterIntentClassification,
    FilterIntentResult,
    classify_filter_intent,
    heuristic_filter_intent,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    IncrementalWatermarkClassification,
    IncrementalWatermarkResult,
    classify_incremental_watermark,
    heuristic_watermark_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    TimeClassificationResult,
    TimeColumnClassification,
    classify_time_columns,
    classify_time_columns_batch,
    heuristic_time_classification,
)

__all__ = [
    # Time classification
    "TimeColumnClassification",
    "TimeClassificationResult",
    "classify_time_columns",
    "classify_time_columns_batch",
    "heuristic_time_classification",
    # Column classification (merged semantic + column role)
    "ColumnClassification",
    "ColumnClassificationResult",
    "QueryMetadata",
    "classify_columns",
    "heuristic_column_classification",
    # Filter intent
    "FilterIntentClassification",
    "FilterIntentResult",
    "classify_filter_intent",
    "heuristic_filter_intent",
    # Incremental watermark
    "IncrementalWatermarkClassification",
    "IncrementalWatermarkResult",
    "classify_incremental_watermark",
    "heuristic_watermark_classification",
    # Note: PII detection is now part of column_classification (is_pii, pii_type, pii_confidence fields)
]
