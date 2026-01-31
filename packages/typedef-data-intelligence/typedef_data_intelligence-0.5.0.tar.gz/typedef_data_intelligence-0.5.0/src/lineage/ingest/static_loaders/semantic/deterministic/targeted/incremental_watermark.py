"""Targeted Incremental Watermark Detection.

Identifies incremental load patterns vs business filters in WHERE predicates.
This is particularly important for dbt incremental models where predicates like:
  received_at >= (SELECT MAX(received_at_date) FROM target)
are load window controls, not business constraints.

The deterministic analysis already knows:
- Filter predicates from WHERE/HAVING/QUALIFY
- Subquery references in predicates
- Column names and patterns

This pass adds semantic classification:
- Is this predicate a watermark/incremental filter?
- What type of watermark (max_timestamp, date_partition, id_range)?
- What column defines the watermark?

Examples:
Uses Fenic's native MapExampleCollection to provide few-shot examples that
guide the LLM toward consistent classification.
"""

from __future__ import annotations

import functools
import logging
import re
from typing import Any, Dict, List, Literal, Optional

import fenic
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Prompt for incremental watermark classification
INCREMENTAL_WATERMARK_PROMPT = """
Classify whether each filter predicate is an incremental load watermark or a business filter.

## Filter Predicates to Classify
{% for pred in predicates %}
{{ loop.index }}. {{ pred.predicate }}
{% endfor %}

## Classification Rules

### Watermark Types (incremental load controls)
- **"max_timestamp"**: Compares to MAX/MIN of a timestamp column from target table
  - Examples: `received_at >= (SELECT MAX(received_at) FROM target)`
  - Examples: `updated_at > (SELECT COALESCE(MAX(updated_at), '1900-01-01') FROM self)`

- **"date_partition"**: Uses Jinja/templated date variables for partition pruning
  - Examples: `date >= '{{ ds }}'`, `partition_date = '{{ var("start_date") }}'`
  - Examples: `created_at >= {{ this.updated_at }}`

- **"id_range"**: Compares to MAX/MIN of an ID column for incremental ID-based loading
  - Examples: `id > (SELECT MAX(id) FROM target)`
  - Examples: `batch_id >= (SELECT COALESCE(MAX(batch_id), 0) FROM self)`

- **"modified_since"**: Compares to a fixed or parameterized "last run" timestamp
  - Examples: `modified_at > :last_run_timestamp`
  - Examples: `updated_at >= DATEADD(day, -3, CURRENT_DATE())`

### Not a Watermark (business filters)
- Date range filters for business logic: `order_date BETWEEN '2024-01-01' AND '2024-12-31'`
- Status filters: `status = 'active'`
- Any filter that doesn't reference a subquery against the target/self table

Return JSON with a classification for EACH input predicate.
"""


class IncrementalWatermarkClassification(BaseModel):
    """Classification result for a single predicate."""

    predicate: str = Field(description="The original predicate SQL")
    is_watermark: bool = Field(
        description="True if this is an incremental load watermark, False if business filter"
    )
    watermark_type: Optional[
        Literal["max_timestamp", "date_partition", "id_range", "modified_since"]
    ] = Field(default=None, description="Type of watermark if is_watermark is True")
    watermark_column: Optional[str] = Field(
        default=None, description="Column used as the watermark (e.g., received_at, id)"
    )
    description: Optional[str] = Field(
        default=None, description="Human-readable explanation"
    )


class IncrementalWatermarkResult(BaseModel):
    """Result of incremental watermark classification for all predicates."""

    classifications: List[IncrementalWatermarkClassification] = Field(
        default_factory=list, description="Classification for each predicate"
    )
    has_watermark: bool = Field(
        default=False, description="True if any predicate is a watermark"
    )
    watermark_summary: Optional[str] = Field(
        default=None,
        description="Summary of watermark strategy (e.g., 'incremental by received_at timestamp')",
    )


class WatermarkPredicateContext(BaseModel):
    """Context about a predicate for watermark classification."""

    predicate: str = Field(description="The predicate SQL")
    has_subquery: bool = Field(
        default=False, description="Whether predicate contains a subquery"
    )
    has_jinja: bool = Field(
        default=False, description="Whether predicate contains Jinja templating"
    )


def extract_watermark_context(
    filter_analysis: Dict[str, Any],
) -> List[WatermarkPredicateContext]:
    """Extract predicate context for watermark classification.

    Args:
        filter_analysis: Output from deterministic filter pass

    Returns:
        List of WatermarkPredicateContext for classification
    """
    predicates: List[WatermarkPredicateContext] = []

    # Extract WHERE predicates (most likely location for watermarks)
    for pred in filter_analysis.get("where", []):
        pred_str = pred if isinstance(pred, str) else pred.get("predicate", str(pred))

        # Detect subquery patterns
        has_subquery = bool(
            re.search(r"\(\s*SELECT\s+", pred_str, re.IGNORECASE)
        )

        # Detect Jinja patterns
        has_jinja = bool(re.search(r"\{\{.*\}\}", pred_str))

        predicates.append(
            WatermarkPredicateContext(
                predicate=pred_str,
                has_subquery=has_subquery,
                has_jinja=has_jinja,
            )
        )

    return predicates


def build_watermark_examples() -> Any:
    """Build few-shot examples for watermark classification.

    Returns:
        MapExampleCollection with watermark examples
    """
    from fenic.core.types.semantic_examples import MapExample, MapExampleCollection

    examples = MapExampleCollection()

    # Max timestamp watermark example
    examples.create_example(
        MapExample(
            input={
                "predicates": [
                    {
                        "predicate": "received_at >= (SELECT MAX(received_at_date) FROM analytics.int_user_active_days)",
                        "has_subquery": True,
                        "has_jinja": False,
                    }
                ]
            },
            output=IncrementalWatermarkResult(
                classifications=[
                    IncrementalWatermarkClassification(
                        predicate="received_at >= (SELECT MAX(received_at_date) FROM analytics.int_user_active_days)",
                        is_watermark=True,
                        watermark_type="max_timestamp",
                        watermark_column="received_at",
                        description="Incremental load using max timestamp from target table",
                    )
                ],
                has_watermark=True,
                watermark_summary="Incremental by received_at timestamp",
            ),
        )
    )

    # Date partition watermark example
    examples.create_example(
        MapExample(
            input={
                "predicates": [
                    {
                        "predicate": "date >= '{{ var(\"start_date\") }}'",
                        "has_subquery": False,
                        "has_jinja": True,
                    }
                ]
            },
            output=IncrementalWatermarkResult(
                classifications=[
                    IncrementalWatermarkClassification(
                        predicate="date >= '{{ var(\"start_date\") }}'",
                        is_watermark=True,
                        watermark_type="date_partition",
                        watermark_column="date",
                        description="Partition-based incremental using dbt variable",
                    )
                ],
                has_watermark=True,
                watermark_summary="Partition pruning by date variable",
            ),
        )
    )

    # NOT a watermark - business date range
    examples.create_example(
        MapExample(
            input={
                "predicates": [
                    {
                        "predicate": "order_date >= '2024-01-01'",
                        "has_subquery": False,
                        "has_jinja": False,
                    }
                ]
            },
            output=IncrementalWatermarkResult(
                classifications=[
                    IncrementalWatermarkClassification(
                        predicate="order_date >= '2024-01-01'",
                        is_watermark=False,
                        watermark_type=None,
                        watermark_column=None,
                        description="Business filter for orders from 2024",
                    )
                ],
                has_watermark=False,
                watermark_summary=None,
            ),
        )
    )

    # ID range watermark example
    examples.create_example(
        MapExample(
            input={
                "predicates": [
                    {
                        "predicate": "id > (SELECT COALESCE(MAX(id), 0) FROM {{ this }})",
                        "has_subquery": True,
                        "has_jinja": True,
                    }
                ]
            },
            output=IncrementalWatermarkResult(
                classifications=[
                    IncrementalWatermarkClassification(
                        predicate="id > (SELECT COALESCE(MAX(id), 0) FROM {{ this }})",
                        is_watermark=True,
                        watermark_type="id_range",
                        watermark_column="id",
                        description="Incremental load by ID from self-reference",
                    )
                ],
                has_watermark=True,
                watermark_summary="Incremental by ID range",
            ),
        )
    )

    return examples


@functools.lru_cache(maxsize=1)
def get_watermark_examples() -> Any:
    """Get cached watermark examples collection."""
    return build_watermark_examples()


def heuristic_watermark_classification(
    filter_analysis: Dict[str, Any],
) -> IncrementalWatermarkResult:
    """Classify watermarks using heuristics (no LLM).

    This is a fallback when LLM is not available or for testing.

    Args:
        filter_analysis: Output from deterministic filter pass

    Returns:
        IncrementalWatermarkResult based on heuristics
    """
    predicates = extract_watermark_context(filter_analysis)
    classifications: List[IncrementalWatermarkClassification] = []
    has_any_watermark = False

    # Patterns for watermark detection
    MAX_SUBQUERY_PATTERN = re.compile(
        r">=?\s*\(\s*SELECT\s+(COALESCE\s*\(\s*)?(MAX|MIN)\s*\(",
        re.IGNORECASE,
    )
    JINJA_VAR_PATTERN = re.compile(r"\{\{\s*(var|this|ds|execution_date)", re.IGNORECASE)
    TIMESTAMP_COLS = {
        "received_at",
        "updated_at",
        "created_at",
        "modified_at",
        "timestamp",
        "loaded_at",
        "ingested_at",
    }
    ID_COLS = {"id", "batch_id", "event_id", "record_id"}

    for pred in predicates:
        is_watermark = False
        watermark_type = None
        watermark_column = None
        description = None

        pred_lower = pred.predicate.lower()

        # Check for MAX/MIN subquery pattern
        if pred.has_subquery and MAX_SUBQUERY_PATTERN.search(pred.predicate):
            is_watermark = True

            # Determine if timestamp or ID based
            for col in TIMESTAMP_COLS:
                if col in pred_lower:
                    watermark_type = "max_timestamp"
                    watermark_column = col
                    description = f"Incremental load using MAX({col})"
                    break

            if watermark_type is None:
                for col in ID_COLS:
                    if col in pred_lower:
                        watermark_type = "id_range"
                        watermark_column = col
                        description = f"Incremental load using MAX({col})"
                        break

            if watermark_type is None:
                watermark_type = "max_timestamp"
                description = "Incremental load using MAX subquery"

        # Check for Jinja variable patterns
        elif pred.has_jinja and JINJA_VAR_PATTERN.search(pred.predicate):
            is_watermark = True
            watermark_type = "date_partition"

            # Try to extract column name
            match = re.search(r"(\w+)\s*>=?\s*['\"]?\{\{", pred.predicate)
            if match:
                watermark_column = match.group(1)

            description = "Partition-based incremental using dbt variable"

        # Check for DATEADD lookback patterns
        elif re.search(r"DATEADD\s*\([^)]+,\s*-\d+", pred.predicate, re.IGNORECASE):
            is_watermark = True
            watermark_type = "modified_since"
            description = "Rolling window incremental load"

        if is_watermark:
            has_any_watermark = True

        classifications.append(
            IncrementalWatermarkClassification(
                predicate=pred.predicate,
                is_watermark=is_watermark,
                watermark_type=watermark_type,
                watermark_column=watermark_column,
                description=description,
            )
        )

    # Generate summary
    watermark_summary = None
    if has_any_watermark:
        watermark_cols = [c.watermark_column for c in classifications if c.watermark_column]
        if watermark_cols:
            watermark_summary = f"Incremental by {', '.join(watermark_cols)}"
        else:
            watermark_summary = "Incremental load detected"

    return IncrementalWatermarkResult(
        classifications=classifications,
        has_watermark=has_any_watermark,
        watermark_summary=watermark_summary,
    )


def add_watermark_column(
    df: "fenic.DataFrame",
    model_size: str = "micro",
    use_examples: bool = True,
) -> "fenic.DataFrame":
    """Add watermark classification column to DataFrame using batch LLM processing.

    Args:
        df: DataFrame with '_watermark_predicates' column (list of predicate contexts)
        model_size: T-shirt size for LLM (micro, small, etc.)
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        DataFrame with 'watermark_classification' column added
    """
    examples = get_watermark_examples() if use_examples else None

    return df.with_column(
        "watermark_classification",
        fenic.semantic.map(
            INCREMENTAL_WATERMARK_PROMPT,
            response_format=IncrementalWatermarkResult,
            predicates=fenic.col("_watermark_predicates"),
            model_alias=model_size,
            max_output_tokens=2048,
            request_timeout=300,
            strict=False,
            examples=examples,
        ),
    )


def classify_incremental_watermark(
    filter_analysis: Dict[str, Any],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> IncrementalWatermarkResult:
    """Classify incremental watermarks using LLM (single model).

    Args:
        filter_analysis: Output from deterministic filter pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro, small, etc.)
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        IncrementalWatermarkResult with classifications for each predicate
    """
    predicates = extract_watermark_context(filter_analysis)

    if not predicates:
        return IncrementalWatermarkResult(classifications=[], has_watermark=False)

    # Create a single-row DataFrame with the context
    df = session.create_dataframe(
        [{"predicates": [p.model_dump() for p in predicates]}]
    )

    # Get examples if enabled
    examples = get_watermark_examples() if use_examples else None

    # Run classification
    df = df.with_column(
        "result",
        fenic.semantic.map(
            INCREMENTAL_WATERMARK_PROMPT,
            response_format=IncrementalWatermarkResult,
            predicates=fenic.col("predicates"),
            model_alias=model_size,
            max_output_tokens=2048,
            request_timeout=300,
            strict=False,
            examples=examples,
        ),
    )

    # Collect result
    results = df.to_pylist()
    if results:
        result_dict = results[0].get("result")
        if isinstance(result_dict, dict):
            return IncrementalWatermarkResult(**result_dict)

    return IncrementalWatermarkResult(classifications=[], has_watermark=False)
