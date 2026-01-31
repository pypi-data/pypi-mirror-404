"""Targeted Time Column Classification.

Classifies which SELECT columns are time-related and determines their role.
Processes columns one-by-one from the SELECT items in grouping analysis.

Architecture:
- Each SELECT column is classified INDIVIDUALLY
- Uses context (GROUP BY, WHERE predicates) to determine time role
- Fenic parallelizes LLM calls automatically for batch processing

Provides both heuristic (fast, no LLM) and LLM-based (more accurate) classification.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Literal, Optional, Set

import fenic
import polars as pl
from pydantic import BaseModel, Field


class TimeColumnClassification(BaseModel):
    """Classification result for a single column."""

    column_alias: str = Field(
        description="The output column alias from SELECT"
    )
    expr: str = Field(
        description="The column expression SQL"
    )
    is_time_column: bool = Field(
        description="True if this column represents time/date"
    )
    time_role: Optional[Literal["range_boundary", "bucket", "attribute"]] = Field(
        default=None,
        description="Role: range_boundary (filtering), bucket (aggregation), or attribute (descriptive)"
    )
    grain: Optional[Literal["year", "quarter", "month", "week", "day", "hour", "minute", "second"]] = Field(
        default=None,
        description="Time grain if determinable"
    )


class TimeClassificationResult(BaseModel):
    """Result of time column classification."""

    classifications: List[TimeColumnClassification] = Field(
        default_factory=list,
        description="Classification for each SELECT column"
    )


# Common time-related column name patterns
TIME_PATTERNS: Set[str] = {
    # Common date/time column names
    "date", "dt", "day", "month", "year", "quarter", "week",
    "timestamp", "time", "datetime", "created", "updated", "modified",
    # Common suffixes
    "created_at", "updated_at", "modified_at", "deleted_at",
    "start_date", "end_date", "order_date", "ship_date", "due_date",
    # TPC-DS style
    "d_year", "d_month", "d_day", "d_date", "d_dow", "d_moy", "d_dom",
    # Business calendar patterns
    "fiscal", "accounting", "reporting", "marketing",
    "fiscal_year", "fiscal_quarter", "fiscal_month", "fiscal_week",
    "reporting_period", "reporting_week", "reporting_month",
    "period", "period_id", "period_start", "period_end",
    # Calendar table patterns
    "week_of_year", "day_of_year", "iso_week", "calendar_week",
    "week_num", "day_num", "month_num", "year_num",
    # Timezone-suffixed columns (match with _utc, _gmt, etc.)
    "_utc", "_gmt", "_pacific", "_eastern", "_local", "_tz",
}

# Patterns that indicate time attributes (not range boundaries or buckets)
ATTRIBUTE_PATTERNS: Set[str] = {
    "d_dow", "d_moy", "d_dom", "day_of_week", "month_of_year", "day_of_month",
    "is_holiday", "is_weekend",
    # Week/day numbers within larger periods
    "week_of_year", "day_of_year", "week_num", "day_num",
    # ISO week (often used as attribute for week-over-week comparisons)
    "iso_week", "calendar_week",
}

# Time functions that indicate time processing
TIME_FUNCS: Set[str] = {
    "date_trunc", "datetrunc", "trunc", "extract",
    "year", "month", "day", "hour", "minute", "second",
    "datediff", "dateadd", "date_add", "date_sub",
    "to_date", "to_timestamp", "date", "timestamp",
}


# LLM prompt for single column time classification
SINGLE_TIME_COLUMN_PROMPT = """Classify if this column is time-related.

## Column to Classify
- Alias: {{ column.alias }}
- Expression: {{ column.expr }}
- In GROUP BY: {{ column.in_group_by }}
- Source tables: {{ column.source_aliases }}

## Query Context
### WHERE predicates (for reference)
{% for pred in where_predicates %}
- {{ pred }}
{% endfor %}

### GROUP BY columns
{% for col in group_by_columns %}
- {{ col }}
{% endfor %}

## Classification Rules

### is_time_column
True if the column represents a time/date concept:
- Date/datetime columns: created_at, updated_at, order_date, timestamp
- Year/month/day columns: d_year, year, month, day, quarter, week
- Time functions: DATE_TRUNC, EXTRACT, TO_DATE
- Time-related attributes: day_of_week, is_weekend

### time_role (if is_time_column is true)
- **"range_boundary"**: Used to define a time range (WHERE date BETWEEN x AND y)
  - If this column or its base column appears in WHERE with comparison operators
- **"bucket"**: Used for time aggregation (GROUP BY year, DATE_TRUNC(month, date))
  - If this column appears in GROUP BY
- **"attribute"**: Other time-related attributes
  - Day of week, month of year, holiday flags, etc.

### grain (if range_boundary or bucket)
What time grain does this represent?
- "year", "quarter", "month", "week", "day", "hour", "minute", "second"
- Look at column name and expression (DATE_TRUNC('month', ...) -> month)

Return JSON classification for this column.
"""


class ColumnTimeContext(BaseModel):
    """Context about a column for time classification."""

    alias: str = Field(description="Output column alias")
    expr: str = Field(description="Column expression SQL")
    in_group_by: bool = Field(default=False, description="True if in GROUP BY")
    source_aliases: List[str] = Field(default_factory=list)


def _extract_column_time_context(
    grouping_analysis: Dict[str, Any],
    filter_analysis: Dict[str, Any],
    select_items: Optional[List[Dict[str, Any]]] = None,
) -> tuple[List[ColumnTimeContext], List[str], List[str]]:
    """Extract column context and query info for time classification.

    Args:
        grouping_analysis: Output from deterministic grouping pass
        filter_analysis: Output from deterministic filter pass
        select_items: Optional list of SELECT items to classify

    Returns:
        Tuple of (columns, where_predicates, group_by_columns)
    """
    group_by_cols = set(grouping_analysis.get("group_by", []))

    columns: List[ColumnTimeContext] = []
    select_items = select_items if select_items is not None else grouping_analysis.get("select", [])
    if not isinstance(select_items, list):
        select_items = []
    for item in select_items:
        if not isinstance(item, dict):
            continue
        alias = item.get("alias", "")
        columns.append(ColumnTimeContext(
            alias=alias,
            expr=item.get("expr", ""),
            in_group_by=alias in group_by_cols,
            source_aliases=item.get("source_aliases", []),
        ))

    # Extract WHERE predicates as strings
    where_predicates: List[str] = []
    for pred in filter_analysis.get("where", []):
        if isinstance(pred, dict):
            where_predicates.append(pred.get("predicate", str(pred)))
        else:
            where_predicates.append(str(pred))

    return columns, where_predicates, list(group_by_cols)


def _infer_grain(expr: str, alias: str) -> Optional[str]:
    """Infer time grain from expression or column name.

    Handles:
    - DATE_TRUNC('month', col) → month
    - YEAR(col), EXTRACT(year FROM col) → year
    - Column names: fiscal_year, d_month, report_week → year, month, week
    """
    text = (expr + " " + alias).lower()

    # Check for explicit DATE_TRUNC grain
    trunc_match = re.search(r"date_trunc\s*\(\s*['\"](\w+)['\"]", text)
    if trunc_match:
        grain = trunc_match.group(1).lower()
        if grain in ("year", "quarter", "month", "week", "day", "hour", "minute", "second"):
            return grain

    # Check for EXTRACT function: EXTRACT(year FROM col)
    extract_match = re.search(r"extract\s*\(\s*(\w+)\s+from", text)
    if extract_match:
        part = extract_match.group(1).lower()
        if part in ("year", "quarter", "month", "week", "day", "hour", "minute", "second"):
            return part

    # Check for standalone time functions: YEAR(col), MONTH(col), DAY(col), etc.
    func_match = re.search(r"\b(year|quarter|month|week|day|hour|minute|second)\s*\(", text)
    if func_match:
        return func_match.group(1).lower()

    # Infer from column name patterns (order matters - more specific first)
    if "fiscal_year" in text or "fy" in text:
        return "year"
    if "fiscal_quarter" in text or "fq" in text:
        return "quarter"
    if "fiscal_month" in text or "fm" in text:
        return "month"
    if "fiscal_week" in text or "fw" in text:
        return "week"
    if "year" in text:
        return "year"
    if "quarter" in text:
        return "quarter"
    if "month" in text or "moy" in text:
        return "month"
    if "week" in text or "iso_week" in text:
        return "week"
    if "day" in text or "date" in text or "dom" in text:
        return "day"
    if "hour" in text:
        return "hour"
    if "minute" in text:
        return "minute"
    if "second" in text:
        return "second"

    return None


def _is_time_column(alias: str, expr: str) -> bool:
    """Check if column is time-related based on name/expression patterns."""
    text = (alias + " " + expr).lower()

    # Check for time-related column name patterns
    if any(pattern in text for pattern in TIME_PATTERNS):
        return True

    # Check for time functions in expression
    if any(func in text for func in TIME_FUNCS):
        return True

    return False


def _column_in_where_predicates(alias: str, expr: str, where_predicates: List[str]) -> bool:
    """Check if column or its expression appears in WHERE predicates."""
    alias_lower = alias.lower()
    expr_lower = expr.lower()

    for pred in where_predicates:
        pred_lower = pred.lower()
        # Check if alias or base column appears in predicate
        if alias_lower in pred_lower:
            return True
        # Check for base column references (e.g., "order_date" from "t.order_date")
        if "." in expr_lower:
            base_col = expr_lower.split(".")[-1].strip()
            if base_col in pred_lower:
                return True

    return False


def heuristic_classify_single_time_column(
    column: ColumnTimeContext,
    where_predicates: List[str],
) -> TimeColumnClassification:
    """Classify a single column for time-relatedness using heuristics.

    Args:
        column: The column to classify
        where_predicates: WHERE predicates for context

    Returns:
        TimeColumnClassification for this column
    """
    is_time = _is_time_column(column.alias, column.expr)

    time_role = None
    grain = None

    if is_time:
        # Determine role based on usage
        in_where = _column_in_where_predicates(column.alias, column.expr, where_predicates)

        if in_where:
            time_role = "range_boundary"
        elif column.in_group_by:
            time_role = "bucket"
        elif any(p in column.alias.lower() for p in ATTRIBUTE_PATTERNS):
            time_role = "attribute"
        else:
            time_role = "attribute"

        # Determine grain
        grain = _infer_grain(column.expr, column.alias)

    return TimeColumnClassification(
        column_alias=column.alias,
        expr=column.expr,
        is_time_column=is_time,
        time_role=time_role,
        grain=grain,
    )


def heuristic_time_classification(
    grouping_analysis: Dict[str, Any],
    filter_analysis: Dict[str, Any],
    select_items: Optional[List[Dict[str, Any]]] = None,
) -> TimeClassificationResult:
    """Classify time columns using heuristics (no LLM).

    Processes each SELECT column individually and determines:
    - Whether it's time-related
    - Its role (range_boundary, bucket, attribute)
    - Its time grain

    Args:
        grouping_analysis: Output from deterministic grouping pass
        filter_analysis: Output from deterministic filter pass
        select_items: Optional list of SELECT items to classify

    Returns:
        TimeClassificationResult with classifications for each SELECT column
    """
    columns, where_predicates, _ = _extract_column_time_context(
        grouping_analysis, filter_analysis, select_items=select_items
    )

    classifications: List[TimeColumnClassification] = []
    for col in columns:
        classification = heuristic_classify_single_time_column(col, where_predicates)
        classifications.append(classification)

    return TimeClassificationResult(classifications=classifications)


def classify_time_columns(
    grouping_analysis: Dict[str, Any],
    filter_analysis: Dict[str, Any],
    session: "fenic.Session",
    model_size: str = "micro",
    select_items: Optional[List[Dict[str, Any]]] = None,
) -> TimeClassificationResult:
    """Classify time columns using LLM (single query).

    More accurate than heuristics for edge cases like:
    - Custom date column names (fiscal_period, reporting_week)
    - Ambiguous names (period, interval, range)
    - Complex expressions with time functions

    For batch processing of multiple queries, use classify_time_columns_batch().

    Args:
        grouping_analysis: Output from deterministic grouping pass
        filter_analysis: Output from deterministic filter pass
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro is sufficient for classification)
        select_items: Optional list of SELECT items to classify

    Returns:
        TimeClassificationResult with classifications for each SELECT column
    """
    columns, where_predicates, group_by_cols = _extract_column_time_context(
        grouping_analysis, filter_analysis, select_items=select_items
    )

    if not columns:
        return TimeClassificationResult(classifications=[])

    # Build input rows - one per column for parallel processing
    input_rows = []
    for col in columns:
        where_preds = list(where_predicates or [])
        group_by_cols = list(group_by_cols or [])
        input_rows.append({
            "column": col.model_dump(),
            "where_predicates": where_preds,
            "group_by_columns": group_by_cols,
        })

    schema = pl.Schema({
        "column": pl.Struct({
            "alias": pl.String,
            "expr": pl.String,
            "in_group_by": pl.Boolean,
            "source_aliases": pl.List(pl.String),
        }),
        "where_predicates": pl.List(pl.String),
        "group_by_columns": pl.List(pl.String),
    })
    polars_df = pl.DataFrame(input_rows, schema=schema)
    df = session.create_dataframe(polars_df)

    # Run LLM classification (Fenic parallelizes automatically)
    df = df.with_column(
        "classification",
        fenic.semantic.map(
            SINGLE_TIME_COLUMN_PROMPT,
            response_format=TimeColumnClassification,
            column=fenic.col("column"),
            where_predicates=fenic.col("where_predicates"),
            group_by_columns=fenic.col("group_by_columns"),
            model_alias=model_size,
            max_output_tokens=512,
        )
    )

    # Collect results
    results = df.to_pylist()
    classifications = []
    for row in results:
        cls_dict = row.get("classification")
        if isinstance(cls_dict, dict):
            classifications.append(TimeColumnClassification.model_validate(cls_dict))

    return TimeClassificationResult(classifications=classifications)


def classify_time_columns_batch(
    models_data: List[Dict[str, Any]],
    session: "fenic.Session",
    model_size: str = "micro",
) -> Dict[str, TimeClassificationResult]:
    """Classify time columns for multiple models in a single batched LLM call.

    Args:
        models_data: List of dicts with keys:
            - model_id: str
            - grouping_analysis: Dict from deterministic grouping pass
            - filter_analysis: Dict from deterministic filter pass
            - select_items: Optional list of SELECT items to classify
        session: Fenic session for LLM calls
        model_size: T-shirt size (micro is sufficient for classification)

    Returns:
        Dict mapping model_id -> TimeClassificationResult
    """
    if not models_data:
        return {}

    rows: List[Dict[str, Any]] = []
    for model_data in models_data:
        model_id = model_data["model_id"]
        grouping_analysis = model_data["grouping_analysis"]
        filter_analysis = model_data["filter_analysis"]
        select_items = model_data.get("select_items")

        columns, where_predicates, group_by_cols = _extract_column_time_context(
            grouping_analysis, filter_analysis, select_items=select_items
        )
        if not columns:
            continue

        for col in columns:
            rows.append(
                {
                    "model_id": model_id,
                    "column": col.model_dump(),
                    "where_predicates": list(where_predicates or []),
                    "group_by_columns": list(group_by_cols or []),
                }
            )

    if not rows:
        return {}

    schema = pl.Schema({
        "model_id": pl.String,
        "column": pl.Struct({
            "alias": pl.String,
            "expr": pl.String,
            "in_group_by": pl.Boolean,
            "source_aliases": pl.List(pl.String),
        }),
        "where_predicates": pl.List(pl.String),
        "group_by_columns": pl.List(pl.String),
    })
    polars_df = pl.DataFrame(rows, schema=schema)
    df = session.create_dataframe(polars_df)

    df = df.with_column(
        "classification",
        fenic.semantic.map(
            SINGLE_TIME_COLUMN_PROMPT,
            response_format=TimeColumnClassification,
            column=fenic.col("column"),
            where_predicates=fenic.col("where_predicates"),
            group_by_columns=fenic.col("group_by_columns"),
            model_alias=model_size,
            max_output_tokens=512,
        ),
    )

    results = df.to_pylist()
    by_model: Dict[str, List[TimeColumnClassification]] = {}
    for row in results:
        model_id = row.get("model_id")
        cls_dict = row.get("classification")
        if not model_id:
            continue
        if isinstance(cls_dict, dict):
            by_model.setdefault(model_id, []).append(
                TimeColumnClassification.model_validate(cls_dict)
            )

    return {
        model_id: TimeClassificationResult(classifications=classifications)
        for model_id, classifications in by_model.items()
    }
