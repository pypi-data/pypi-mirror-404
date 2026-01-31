"""Targeted Filter Intent Classification.

Instead of passing raw SQL and asking "what filters are applied",
this pass provides structured filter predicates from deterministic analysis and asks
the LLM to classify each predicate's business intent.

The deterministic analysis already knows:
- WHERE predicates
- HAVING predicates
- QUALIFY predicates
- Which predicates are null-killing on outer joins

This pass adds business semantics:
- Is this a date range filter?
- Is this a status filter (active/inactive)?
- Is this a deduplication pattern?
- Is this a tenant isolation filter?

Batch Processing:
This module supports batch classification via Fenic's semantic.map() which
processes all models in parallel, leveraging Fenic's columnar execution.

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
import polars as pl
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Prompt for filter intent classification
FILTER_INTENT_PROMPT = """
Classify the business intent of each filter predicate.

## Filter Predicates to Classify
{% for pred in predicates %}
{{ loop.index }}. {{ pred.predicate }}
   - Clause: {{ pred.clause }}
{% endfor %}

## Classification Rules

For each predicate, determine the business intent:

### Intent Categories
- **"date_range"**: Time-based filtering (BETWEEN dates, >= start_date, date comparisons)
  - Examples: `order_date >= '2024-01-01'`, `created_at BETWEEN ... AND ...`

- **"status_filter"**: Filtering by status/state columns
  - Examples: `status = 'active'`, `is_deleted = false`, `state != 'cancelled'`

- **"geography_filter"**: Region, country, state, location filtering
  - Examples: `country = 'US'`, `region IN ('EMEA', 'APAC')`, `state_code = 'CA'`

- **"segment_filter"**: Customer/product/business segments
  - Examples: `customer_tier = 'enterprise'`, `product_category IN (...)`, `segment = 'SMB'`

- **"exclusion"**: Explicitly excluding data (NOT IN, !=, NOT LIKE patterns)
  - Examples: `customer_id NOT IN (...)`, `type != 'test'`, `email NOT LIKE '%@test.com'`

- **"threshold"**: Numeric comparisons for business thresholds
  - Examples: `amount > 1000`, `quantity >= 10`, `revenue < 0`

- **"null_handling"**: IS NULL / IS NOT NULL checks
  - Examples: `email IS NOT NULL`, `deleted_at IS NULL`

- **"deduplication"**: ROW_NUMBER = 1 or similar patterns for deduplication
  - Examples: `row_num = 1`, `rn = 1`, `ROW_NUMBER() = 1`

- **"tenant_filter"**: Multi-tenant isolation
  - Examples: `tenant_id = ...`, `org_id = ...`, `workspace_id = ...`

- **"data_quality"**: Filtering out invalid/bad data
  - Examples: `email LIKE '%@%'`, `amount > 0`, `LENGTH(name) > 0`

- **"other"**: Cannot classify into above categories

Return JSON with a classification for EACH input predicate.
"""


class FilterIntentClassification(BaseModel):
    """Classification result for a single filter predicate."""

    predicate: str = Field(description="The original predicate SQL")
    clause: Literal["where", "having", "qualify"] = Field(
        description="Which clause the predicate is from"
    )
    intent: Literal[
        "date_range",
        "status_filter",
        "geography_filter",
        "segment_filter",
        "exclusion",
        "threshold",
        "null_handling",
        "deduplication",
        "tenant_filter",
        "data_quality",
        "other",
    ] = Field(description="The business intent of this filter")
    description: Optional[str] = Field(
        default=None, description="Human-readable explanation of the filter's purpose"
    )


class FilterIntentResult(BaseModel):
    """Result of filter intent classification for all predicates."""

    classifications: List[FilterIntentClassification] = Field(
        default_factory=list, description="Classification for each predicate"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Summary of overall filtering strategy (e.g., 'filters by date range and active status')",
    )


class PredicateContext(BaseModel):
    """Context about a predicate for classification."""

    predicate: str = Field(description="The predicate SQL")
    clause: Literal["where", "having", "qualify"] = Field(
        description="Which clause the predicate is from"
    )


def build_filter_intent_examples() -> Any:
    """Build few-shot examples for filter intent classification.

    Uses Fenic's native MapExampleCollection to provide consistent
    classification guidance to the LLM.

    Returns:
        MapExampleCollection with filter intent examples
    """
    from fenic.core.types.semantic_examples import MapExample, MapExampleCollection

    examples = MapExampleCollection()

    # Date range examples
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "order_date >= '2024-01-01'", "clause": "where"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="order_date >= '2024-01-01'",
                        clause="where",
                        intent="date_range",
                        description="Filters orders from start of 2024",
                    )
                ]
            ),
        )
    )

    # Status filter example
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "status = 'active'", "clause": "where"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="status = 'active'",
                        clause="where",
                        intent="status_filter",
                        description="Includes only active records",
                    )
                ]
            ),
        )
    )

    # Deduplication example
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "row_number = 1", "clause": "qualify"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="row_number = 1",
                        clause="qualify",
                        intent="deduplication",
                        description="Keeps only first row per partition for deduplication",
                    )
                ]
            ),
        )
    )

    # Null handling example
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "email IS NOT NULL", "clause": "where"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="email IS NOT NULL",
                        clause="where",
                        intent="null_handling",
                        description="Excludes records without email",
                    )
                ]
            ),
        )
    )

    # Tenant filter example
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "tenant_id = '12345'", "clause": "where"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="tenant_id = '12345'",
                        clause="where",
                        intent="tenant_filter",
                        description="Multi-tenant isolation filter",
                    )
                ]
            ),
        )
    )

    # Threshold example
    examples.create_example(
        MapExample(
            input={"predicates": [{"predicate": "amount > 1000", "clause": "having"}]},
            output=FilterIntentResult(
                classifications=[
                    FilterIntentClassification(
                        predicate="amount > 1000",
                        clause="having",
                        intent="threshold",
                        description="Filters to high-value transactions over $1000",
                    )
                ]
            ),
        )
    )

    return examples


@functools.lru_cache(maxsize=1)
def get_filter_intent_examples() -> Any:
    """Get cached filter intent examples collection."""
    return build_filter_intent_examples()


def extract_predicate_context(
    filter_analysis: Dict[str, Any],
) -> List[PredicateContext]:
    """Extract predicate context from deterministic filter analysis.

    Args:
        filter_analysis: Output from deterministic filter pass

    Returns:
        List of PredicateContext for classification
    """
    predicates: List[PredicateContext] = []

    # Extract WHERE predicates
    for pred in filter_analysis.get("where", []):
        pred_str = pred if isinstance(pred, str) else pred.get("predicate", str(pred))
        predicates.append(PredicateContext(predicate=pred_str, clause="where"))

    # Extract HAVING predicates
    for pred in filter_analysis.get("having", []):
        pred_str = pred if isinstance(pred, str) else pred.get("predicate", str(pred))
        predicates.append(PredicateContext(predicate=pred_str, clause="having"))

    # Extract QUALIFY predicates
    for pred in filter_analysis.get("qualify", []):
        pred_str = pred if isinstance(pred, str) else pred.get("predicate", str(pred))
        predicates.append(PredicateContext(predicate=pred_str, clause="qualify"))

    return predicates


def heuristic_filter_intent(
    predicate: str,
    clause: str,
) -> FilterIntentClassification:
    """Classify a single predicate using heuristics (no LLM).

    Args:
        predicate: The predicate SQL string
        clause: Which clause (where, having, qualify)

    Returns:
        FilterIntentClassification based on heuristics
    """
    pred_lower = predicate.lower()

    # Deduplication patterns (highest priority - very specific)
    if re.search(r"\brow_num(ber)?\s*=\s*1\b", pred_lower) or re.search(
        r"\brn\s*=\s*1\b", pred_lower
    ):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="deduplication",
            description="Row number filter for deduplication",
        )

    # Null handling
    if " is null" in pred_lower or " is not null" in pred_lower:
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="null_handling",
            description="NULL check filter",
        )

    # Date range patterns
    date_patterns = [
        r"\bdate\b",
        r"\b_at\b",
        r"\bcreated\b",
        r"\bupdated\b",
        r"\bmodified\b",
        r"\btimestamp\b",
        r"\btime\b",
        r"\bday\b",
        r"\bmonth\b",
        r"\byear\b",
    ]
    if any(re.search(p, pred_lower) for p in date_patterns):
        if " between " in pred_lower or ">=" in predicate or "<=" in predicate:
            return FilterIntentClassification(
                predicate=predicate,
                clause=clause,
                intent="date_range",
                description="Date/time range filter",
            )

    # Status filter patterns
    status_patterns = [
        r"\bstatus\b",
        r"\bstate\b",
        r"\bis_active\b",
        r"\bis_deleted\b",
        r"\bactive\b",
        r"\binactive\b",
        r"\bdeleted\b",
        r"\bcancelled\b",
        r"\bcanceled\b",
        r"\benabled\b",
        r"\bdisabled\b",
    ]
    if any(re.search(p, pred_lower) for p in status_patterns):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="status_filter",
            description="Status/state filter",
        )

    # Tenant/org filter patterns
    tenant_patterns = [
        r"\btenant_id\b",
        r"\borg_id\b",
        r"\borganization_id\b",
        r"\bworkspace_id\b",
        r"\baccount_id\b",
        r"\bcompany_id\b",
    ]
    if any(re.search(p, pred_lower) for p in tenant_patterns):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="tenant_filter",
            description="Multi-tenant isolation filter",
        )

    # Geography patterns
    geo_patterns = [
        r"\bcountry\b",
        r"\bregion\b",
        r"\bstate\b",
        r"\bcity\b",
        r"\bzip\b",
        r"\bpostal\b",
        r"\blocation\b",
        r"\bgeo\b",
    ]
    if any(re.search(p, pred_lower) for p in geo_patterns):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="geography_filter",
            description="Geographic location filter",
        )

    # Segment patterns
    segment_patterns = [
        r"\bsegment\b",
        r"\btier\b",
        r"\bcategory\b",
        r"\btype\b",
        r"\bclass\b",
        r"\bgroup\b",
    ]
    if any(re.search(p, pred_lower) for p in segment_patterns):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="segment_filter",
            description="Business segment filter",
        )

    # Exclusion patterns
    if " not in " in pred_lower or " != " in predicate or " <> " in predicate:
        if "not like" in pred_lower:
            return FilterIntentClassification(
                predicate=predicate,
                clause=clause,
                intent="exclusion",
                description="Exclusion filter",
            )
        # Check if it's excluding specific values (not a comparison)
        if re.search(r"!=\s*['\"]", predicate) or " not in " in pred_lower:
            return FilterIntentClassification(
                predicate=predicate,
                clause=clause,
                intent="exclusion",
                description="Exclusion filter",
            )

    # Threshold patterns (numeric comparisons)
    if re.search(r"[<>=]\s*\d+", predicate):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="threshold",
            description="Numeric threshold filter",
        )

    # Data quality patterns
    quality_patterns = [r"\blength\s*\(", r"\blike\s*'%@%'", r">\s*0\s*$"]
    if any(re.search(p, pred_lower) for p in quality_patterns):
        return FilterIntentClassification(
            predicate=predicate,
            clause=clause,
            intent="data_quality",
            description="Data quality filter",
        )

    # Default to other
    return FilterIntentClassification(
        predicate=predicate,
        clause=clause,
        intent="other",
        description=None,
    )


def heuristic_filter_intent_classification(
    filter_analysis: Dict[str, Any],
) -> FilterIntentResult:
    """Classify all filter predicates using heuristics (no LLM).

    This is a fallback when LLM is not available or for testing.

    Args:
        filter_analysis: Output from deterministic filter pass

    Returns:
        FilterIntentResult based on heuristics
    """
    predicates = extract_predicate_context(filter_analysis)
    classifications: List[FilterIntentClassification] = []

    for pred in predicates:
        classification = heuristic_filter_intent(pred.predicate, pred.clause)
        classifications.append(classification)

    # Generate summary
    intent_counts: Dict[str, int] = {}
    for c in classifications:
        intent_counts[c.intent] = intent_counts.get(c.intent, 0) + 1

    summary_parts = []
    if intent_counts.get("date_range"):
        summary_parts.append("date range filtering")
    if intent_counts.get("status_filter"):
        summary_parts.append("status filtering")
    if intent_counts.get("deduplication"):
        summary_parts.append("deduplication")
    if intent_counts.get("tenant_filter"):
        summary_parts.append("tenant isolation")

    summary = (
        f"Filters include: {', '.join(summary_parts)}" if summary_parts else None
    )

    return FilterIntentResult(
        classifications=classifications,
        summary=summary,
    )


def add_filter_intent_column(
    df: "fenic.DataFrame",
    model_size: str = "micro",
    use_examples: bool = True,
) -> "fenic.DataFrame":
    """Add filter intent classification column to DataFrame using batch LLM processing.

    This function leverages Fenic's columnar execution to process all rows
    in parallel via semantic.map().

    Args:
        df: DataFrame with '_filter_predicates' column (list of predicate contexts)
        model_size: T-shirt size for LLM (micro, small, etc.)
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        DataFrame with 'filter_intent' column added
    """
    # Get examples if enabled
    examples = get_filter_intent_examples() if use_examples else None

    return df.with_column(
        "filter_intent",
        fenic.semantic.map(
            FILTER_INTENT_PROMPT,
            response_format=FilterIntentResult,
            predicates=fenic.col("_filter_predicates"),
            model_alias=model_size,
            max_output_tokens=4096,
            request_timeout=300,
            strict=False,
            examples=examples,
        ),
    )


def _build_filter_intent_batch_schema() -> pl.Schema:
    """Build explicit Polars schema for batched filter intent classification.

    Includes model_id for tracking results back to their models.
    """
    predicate_struct = pl.Struct({
        "predicate": pl.String,
        "clause": pl.String,
    })

    return pl.Schema({
        "model_id": pl.String,
        "predicates": pl.List(predicate_struct),
    })


def classify_filter_intent(
    filter_analysis: Dict[str, Any],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> FilterIntentResult:
    """Classify filter intent using LLM (single model).

    This is a targeted classification task that leverages deterministic
    analysis results instead of processing raw SQL.

    Note: For batch processing, use classify_filter_intent_batch() instead.

    Args:
        filter_analysis: Output from deterministic filter pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro, small, etc.) - micro is sufficient for classification
        use_examples: Whether to use few-shot examples (default True)

    Returns:
        FilterIntentResult with classifications for each predicate
    """
    predicates = extract_predicate_context(filter_analysis)

    if not predicates:
        return FilterIntentResult(classifications=[])

    # Create a single-row DataFrame with the context
    df = session.create_dataframe(
        [{"predicates": [p.model_dump() for p in predicates]}]
    )

    # Get examples if enabled
    examples = get_filter_intent_examples() if use_examples else None

    # Run classification
    df = df.with_column(
        "result",
        fenic.semantic.map(
            FILTER_INTENT_PROMPT,
            response_format=FilterIntentResult,
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
        if result_dict is None:
            # LLM returned None, fall back to heuristics
            logger.warning("LLM returned None for filter intent, using heuristics")
            return heuristic_filter_intent_classification(filter_analysis)
        if isinstance(result_dict, dict):
            try:
                return FilterIntentResult(**result_dict)
            except Exception as e:
                logger.warning(f"Failed to parse LLM result as FilterIntentResult: {e}")
                return heuristic_filter_intent_classification(filter_analysis)

    return heuristic_filter_intent_classification(filter_analysis)


def classify_filter_intent_batch(
    models_data: List[Dict[str, Any]],
    session: "fenic.Session",
    model_size: str = "micro",
    use_examples: bool = True,
) -> Dict[str, FilterIntentResult]:
    """Classify filter intent for multiple models in a single batched LLM call.

    This is more efficient than classify_filter_intent() when processing many models,
    as it consolidates all filter predicates from all models into a single Fenic batch.

    Architecture:
    1. Collect ALL predicates from ALL models into one DataFrame
    2. Run one semantic.map() call (Fenic batches LLM requests)
    3. Map results back by model_id

    Args:
        models_data: List of dicts with keys:
            - model_id: str
            - filter_analysis: Dict from deterministic filter pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro recommended)
        use_examples: Whether to use few-shot examples

    Returns:
        Dict mapping model_id -> FilterIntentResult
    """
    if not models_data:
        return {}

    # Step 1: Build rows for all models (one row per model with its predicates)
    rows: List[Dict[str, Any]] = []
    models_with_predicates: List[str] = []

    for model_data in models_data:
        model_id = model_data["model_id"]
        filter_analysis = model_data["filter_analysis"]

        predicates = extract_predicate_context(filter_analysis)

        if not predicates:
            continue

        models_with_predicates.append(model_id)
        rows.append({
            "model_id": model_id,
            "predicates": [p.model_dump() for p in predicates],
        })

    if not rows:
        return {}

    # Step 2: Create single Polars DataFrame with explicit schema
    schema = _build_filter_intent_batch_schema()
    polars_df = pl.DataFrame(rows, schema=schema)

    # Step 3: Convert to Fenic DataFrame and run classification (single batch)
    df = session.create_dataframe(polars_df)

    examples = get_filter_intent_examples() if use_examples else None

    df = df.with_column(
        "filter_intent",
        fenic.semantic.map(
            FILTER_INTENT_PROMPT,
            response_format=FilterIntentResult,
            predicates=fenic.col("predicates"),
            model_alias=model_size,
            max_output_tokens=2048,
            request_timeout=300,
            strict=False,
            examples=examples,
        ),
    )

    # Step 4: Collect results and map back to model_ids
    results = df.to_pylist()
    intent_by_model: Dict[str, FilterIntentResult] = {}

    for row in results:
        model_id = row.get("model_id")
        result_dict = row.get("filter_intent")

        if model_id and isinstance(result_dict, dict):
            try:
                intent_by_model[model_id] = FilterIntentResult(**result_dict)
            except Exception as e:
                logger.warning(f"Failed to parse filter intent for {model_id}: {e}")
                # Find original filter_analysis for heuristic fallback
                for md in models_data:
                    if md["model_id"] == model_id:
                        intent_by_model[model_id] = heuristic_filter_intent_classification(
                            md["filter_analysis"]
                        )
                        break
        elif model_id:
            # LLM returned None, fall back to heuristics
            for md in models_data:
                if md["model_id"] == model_id:
                    intent_by_model[model_id] = heuristic_filter_intent_classification(
                        md["filter_analysis"]
                    )
                    break

    return intent_by_model
