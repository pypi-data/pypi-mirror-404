"""Hybrid pipeline executor combining deterministic + targeted LLM analysis.

Architecture:
- Phase 1: Deterministic Analysis (Pure Python) - SQLGlot passes
- Phase 2: Batch LLM Classification (Fenic) - only for LLM calls
- Phase 3: Merge Results (Pure Python) - combine and build semantics
- Phase 4: LLM-Only Passes (Fenic) - grain, summary, domains

Key principle: Only use Fenic where we need LLM calls.
Complex dicts stay in Python; Fenic only sees simple types.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import fenic as fc
import polars as pl
from fenic.api.functions import udf
from fenic.api.functions.builtin import async_udf
from fenic.core.types import StringType
from sqlglot import exp
from sqlglot.optimizer import annotate_types

from lineage.backends.lineage.protocol import LineageStorage
from lineage.ingest.config import PipelineConfig
from lineage.ingest.static_loaders.semantic.deterministic.executor import (
    DeterministicExecutor,
    DeterministicResult,
)
from lineage.ingest.static_loaders.semantic.deterministic.graph_enrichment import (
    EnrichmentResult,
    GraphEnricher,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    classify_columns_batch,
    heuristic_column_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.filter_intent import (
    classify_filter_intent_batch,
    heuristic_filter_intent_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    heuristic_watermark_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    TimeClassificationResult,
    classify_time_columns_batch,
    heuristic_time_classification,
)
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    FilterAnalysis,
    GroupingAnalysis,
    JoinEdgeAnalysis,
    OutputShapeAnalysis,
    RelationAnalysis,
    WindowAnalysis,
)
from lineage.ingest.static_loaders.semantic.models.analytical import (
    NormalizedTimeScope,
    TimeAnalysis,
    TimeScope,
)
from lineage.ingest.static_loaders.semantic.models.business import (
    BusinessDimension,
    BusinessFact,
    BusinessMeasure,
    BusinessSemantics,
    BusinessTimeWindow,
    infer_domains_heuristic,
)
from lineage.ingest.static_loaders.semantic.pipeline.dag import SQLAnalysisDAG
from lineage.ingest.static_loaders.semantic.pipeline.executor import (
    PassProgressCallback,
)
from lineage.ingest.static_loaders.semantic.pipeline.schema import (
    build_hybrid_result_schema,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema

logger = logging.getLogger(__name__)

# Passes that run via LLM even in hybrid mode
LLM_ONLY_PASSES = {
    "audit_analysis",
    "grain_humanization",
    "analysis_summary",
    "model_domains",
}


# ---------------------------------------------------------------------------
# Time Analysis Helpers
# ---------------------------------------------------------------------------
# These functions support _convert_time_classification_to_time_analysis
# and are extracted for testability and clarity.


def _get_time_column_name(col: Dict[str, Any]) -> str:
    """Extract time column name from classification dict.

    Handles both new format (column_alias/expr) and legacy (qualified_name).
    """
    return (col.get("column_alias") or col.get("qualified_name") or "").strip()


def _get_time_column_expr(col: Dict[str, Any]) -> str:
    """Extract expression from time classification dict."""
    return (col.get("expr") or "").strip()


def _extract_primary_time_candidates(
    alias: str, expr_str: str
) -> List[Tuple[Optional[str], str]]:
    """Extract candidate (table, column) pairs from an expression.

    Prefers matching against the underlying column referenced by expr, not just
    the output alias. This handles cases like:
        SELECT o.order_date AS ds ... WHERE o.order_date >= ...

    Args:
        alias: Output column alias
        expr_str: Column expression SQL

    Returns:
        List of (table, column_name) tuples, deduplicated and in priority order.
        Table may be None for unqualified references.
    """
    candidates: List[Tuple[Optional[str], str]] = []
    alias = (alias or "").strip()
    expr_str = (expr_str or "").strip()

    if expr_str:
        # Try to parse the expression and extract the first column reference.
        try:
            parsed_expr = parse_sql_cached(f"SELECT {expr_str}")
            col = parsed_expr.find(exp.Column)
            if isinstance(col, exp.Column) and col.name:
                candidates.append(((col.table or None), col.name))
                # Also add unqualified fallback
                candidates.append((None, col.name))
        except Exception:
            # Best-effort fallback: attempt to split on dot
            if "." in expr_str:
                parts = [p for p in expr_str.split(".") if p]
                if len(parts) >= 2:
                    candidates.append((parts[-2].strip(), parts[-1].strip()))
                    candidates.append((None, parts[-1].strip()))

    # Put the output alias last; prefer matching against underlying column refs first.
    if alias:
        candidates.append((None, alias))

    # Deduplicate while preserving order
    seen: set[Tuple[Optional[str], str]] = set()
    out: List[Tuple[Optional[str], str]] = []
    for t, n in candidates:
        key = (t.lower() if isinstance(t, str) else t, n.lower())
        if key in seen or not n:
            continue
        seen.add(key)
        out.append((t, n))
    return out


def _strip_quotes(value: str) -> str:
    """Remove surrounding single or double quotes from a string."""
    v = value.strip()
    if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
        return v[1:-1]
    return v


def _is_quoted(value: str) -> bool:
    """Check if a string is surrounded by quotes."""
    v = value.strip()
    return (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"'))


def _quote_like(example: str, new_value: str) -> str:
    """Quote new_value in the same style as example (quoted or unquoted)."""
    if _is_quoted(example):
        return f"'{new_value}'"
    return new_value


def _parse_predicate_expr(predicate: str) -> Optional[exp.Expression]:
    """Parse a predicate into an Expression using SQLGlot.

    Wraps the predicate in SELECT ... WHERE to parse consistently.
    """
    try:
        parsed = parse_sql_cached(f"SELECT * WHERE {predicate}")
        where = parsed.find(exp.Where)
        return where.this if where else None
    except Exception:
        return None


def _binary_sides(
    node: exp.Expression,
) -> Tuple[Optional[exp.Expression], Optional[exp.Expression]]:
    """Extract left and right sides from a binary expression."""
    left = getattr(node, "left", None)
    right = getattr(node, "right", None)
    if left is None:
        left = node.args.get("this")
    if right is None:
        right = node.args.get("expression")
    return left, right


def _normalize_time_end_bound(
    end_value: str,
    end_inclusive: bool,
    grain: Optional[str],
) -> str:
    """Normalize an inclusive end bound to exclusive based on grain.

    Handles day, week, month, year, hour, minute, second grains.

    Args:
        end_value: Original end bound value (possibly quoted)
        end_inclusive: Whether the original bound was inclusive
        grain: Time grain (day, month, year, etc.)

    Returns:
        Normalized end value (exclusive), preserving quoting style
    """
    if not end_inclusive:
        return end_value

    if not grain:
        return end_value

    def _extract_cast_literal(
        value: str,
    ) -> Tuple[Optional[str], Optional[exp.Expression]]:
        try:
            from sqlglot import parse_one

            parsed = parse_one(value)
        except Exception:
            return None, None

        if isinstance(parsed, (exp.Cast, exp.TryCast)) or parsed.__class__.__name__ in {
            "SafeCast",
            "TryCast",
        }:
            inner = getattr(parsed, "this", None) or parsed.args.get("this")
            if isinstance(inner, exp.Literal) and inner.is_string:
                return inner.this, parsed
        return None, None

    cast_literal, cast_expr = _extract_cast_literal(end_value)
    raw = cast_literal if cast_literal is not None else _strip_quotes(end_value)
    try:
        from datetime import date, datetime, timedelta

        def _format_value(new_value: str) -> str:
            if cast_expr is not None and cast_literal is not None:
                new_cast = cast_expr.copy()
                new_cast.set("this", exp.Literal.string(new_value))
                return new_cast.sql(pretty=False)
            return _quote_like(end_value, new_value)

        if grain == "day":
            d = date.fromisoformat(raw)
            return _format_value((d + timedelta(days=1)).isoformat())
        elif grain == "year":
            y = int(raw)
            return _format_value(str(y + 1))
        elif grain == "month":
            if len(raw) == 7 and raw[4] == "-":
                y = int(raw[:4])
                m = int(raw[5:7])
                if m == 12:
                    y, m = y + 1, 1
                else:
                    m += 1
                return _format_value(f"{y:04d}-{m:02d}")
        elif grain == "week":
            d = date.fromisoformat(raw)
            return _format_value((d + timedelta(days=7)).isoformat())
        elif grain in ("hour", "minute", "second"):
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if grain == "hour":
                return _format_value((dt + timedelta(hours=1)).isoformat())
            elif grain == "minute":
                return _format_value((dt + timedelta(minutes=1)).isoformat())
            else:
                return _format_value((dt + timedelta(seconds=1)).isoformat())
    except Exception as e:
        logger.warning(f"Failed to normalize end bound {end_value}: {e}")
        pass

    return end_value


@dataclass
class TimeBounds:
    """Extracted time range bounds from filter predicates."""

    start_value: Optional[str] = None
    end_value: Optional[str] = None
    end_inclusive: bool = True


def _extract_time_bounds_from_filters(
    filter_analysis: Dict[str, Any],
    primary_candidates: List[Tuple[Optional[str], str]],
) -> TimeBounds:
    """Extract time range bounds from filter predicates.

    Parses WHERE predicates to find BETWEEN, >=, >, <=, <, = comparisons
    that match the primary time column candidates.

    Args:
        filter_analysis: FilterAnalysis dict with 'where' list of predicates
        primary_candidates: List of (table, column) candidates to match against

    Returns:
        TimeBounds with extracted start_value, end_value, and end_inclusive flag
    """
    bounds = TimeBounds()

    def matches_primary(col: exp.Column) -> bool:
        if not col.name:
            return False
        for target_table, target_col in primary_candidates:
            if not target_col:
                continue
            if target_table:
                if (
                    (col.table or "").lower() == target_table.lower()
                    and col.name.lower() == target_col.lower()
                ):
                    return True
            else:
                if col.name.lower() == target_col.lower():
                    return True
        return False

    for pred in filter_analysis.get("where", []):
        pred_str = pred.get("predicate", "") if isinstance(pred, dict) else str(pred)
        pred_expr = _parse_predicate_expr(pred_str)
        if not pred_expr:
            continue

        # Handle BETWEEN
        for between in pred_expr.find_all(exp.Between):
            this_expr = between.args.get("this")
            if isinstance(this_expr, exp.Column) and matches_primary(this_expr):
                low = between.args.get("low")
                high = between.args.get("high")
                if low is not None:
                    bounds.start_value = low.sql(pretty=False)
                if high is not None:
                    bounds.end_value = high.sql(pretty=False)
                    bounds.end_inclusive = True

        # Handle comparisons: >=, >, <=, <, =
        for node in pred_expr.walk():
            if not isinstance(node, (exp.GTE, exp.GT, exp.LTE, exp.LT, exp.EQ)):
                continue

            left, right = _binary_sides(node)
            if left is None or right is None:
                continue

            # Normalize to "col OP value"
            col_side: Optional[exp.Column] = None
            value_side: Optional[exp.Expression] = None
            operator_on_col: Optional[type] = None

            if isinstance(left, exp.Column) and matches_primary(left):
                col_side = left
                value_side = right
                operator_on_col = type(node)
            elif isinstance(right, exp.Column) and matches_primary(right):
                col_side = right
                value_side = left
                # Reverse operator when value OP col
                if isinstance(node, exp.GTE):
                    operator_on_col = exp.LTE
                elif isinstance(node, exp.GT):
                    operator_on_col = exp.LT
                elif isinstance(node, exp.LTE):
                    operator_on_col = exp.GTE
                elif isinstance(node, exp.LT):
                    operator_on_col = exp.GT
                else:  # EQ is symmetric
                    operator_on_col = exp.EQ

            if not col_side or value_side is None or operator_on_col is None:
                continue

            value_sql = value_side.sql(pretty=False)

            if operator_on_col in (exp.GTE, exp.GT):
                # Best-effort: store as inclusive start even for strict >
                bounds.start_value = value_sql
            elif operator_on_col in (exp.LTE, exp.LT):
                bounds.end_value = value_sql
                bounds.end_inclusive = operator_on_col is exp.LTE
            elif operator_on_col is exp.EQ:
                bounds.start_value = value_sql
                bounds.end_value = value_sql
                bounds.end_inclusive = True

    return bounds


@dataclass
class HybridModelResult:
    """Result of hybrid analysis for a single model."""

    model_id: str
    original_row: Dict[str, Any]

    # Deterministic results
    deterministic: Optional[DeterministicResult] = None
    parse_error: Optional[str] = None

    # Classification results (heuristic or LLM)
    time_classification: Optional[Dict] = None
    semantic_classification: Optional[Dict] = None

    # New targeted classification results
    filter_intent: Optional[Dict] = None  # LLM: business context for filters
    # Note: PII detection merged into semantic_classification (pii_columns, high_risk_pii_count)
    incremental_watermark: Optional[Dict] = None  # Heuristic: watermark vs business filter

    # Built business semantics
    business_semantics: Optional[BusinessSemantics] = None

    # Tracking
    passes_used: Dict[str, str] = field(default_factory=dict)


class HybridPipelineExecutor:
    """Execute hybrid deterministic + targeted LLM analysis pipeline.

    This executor uses Python dicts for intermediate results and only
    uses Fenic DataFrames where LLM calls are needed.
    """

    def __init__(
        self,
        session: fc.Session,
        pipeline_config: PipelineConfig,
        schema: Optional[Union[Dict, SqlglotSchema]] = None,
        classification_model_size: str = "micro",
        lineage_storage: Optional[LineageStorage] = None,
    ):
        """Initialize the hybrid executor.

        Args:
            session: Fenic session for LLM operations
            pipeline_config: Pipeline configuration
            schema: SQLGlot-compatible schema for column resolution (Dict or SqlglotSchema)
            classification_model_size: T-shirt size for classification LLM
            lineage_storage: Optional LineageStorage instance used for in-process graph enrichment
                when running deterministic analysis via Fenic UDFs. If not provided,
                enrichment is skipped.
        """
        self.session = session
        self.pipeline_config = pipeline_config
        # Convert SqlglotSchema to dict if needed - SQLGlot's qualify() expects dict
        if schema is not None and isinstance(schema, SqlglotSchema):
            self.schema = schema.to_dict()
        else:
            self.schema = schema
        self.classification_model_size = classification_model_size
        self.lineage_storage = lineage_storage

        # Create DAG for LLM-only passes
        self.dag = SQLAnalysisDAG(session, pipeline_config)
        self.execution_times: Dict[str, float] = {}

    def run(
        self,
        df: fc.DataFrame,
        session: Optional[fc.Session] = None,
        dbt_model_name: str = "batch_analysis",  # noqa: ARG002
        dialect: Optional[str] = None,
        progress_callback: Optional[PassProgressCallback] = None,
    ) -> fc.DataFrame:
        """Execute hybrid pipeline on input DataFrame.

        Args:
            df: Input DataFrame with SQL queries (must have 'sql' column)
            session: Fenic session for LLM operations. If provided, must match the
                session passed to __init__ (deprecated parameter for backwards
                compatibility). If None, uses the session from __init__.
            dbt_model_name: Name for logging
            dialect: SQL dialect for parsing
            progress_callback: Optional callback for progress updates

        Returns:
            DataFrame with all analysis results
        """
        # Use the session from __init__ if not provided, warn if different session passed
        if session is not None and session is not self.session:
            logger.warning(
                "Different session passed to run() than __init__(). "
                "This is deprecated and may cause race conditions. "
                "Using the session from run() for backwards compatibility."
            )
            self.session = session
        elif session is None and self.session is None:
            raise ValueError("No session provided. Pass session to __init__ or run().")

        # Calculate total passes for progress tracking
        llm_passes = [p for p in self.dag.get_execution_order() if p in LLM_ONLY_PASSES]
        total_passes = 3 + len(llm_passes)  # deterministic + classification + merge + llm passes
        pass_index = 0

        # Get input rows
        input_rows = df.to_pylist()

        # Phase 1: Deterministic Analysis (Pure Python)
        start_time = time.time()
        results = self._run_deterministic_analysis_fenic(input_rows, dialect)
        elapsed = time.time() - start_time
        self.execution_times["deterministic"] = elapsed
        logger.info(f"  ✅ deterministic analysis executed in {elapsed:.2f}s")

        pass_index += 1
        if progress_callback:
            progress_callback("deterministic", pass_index, total_passes)

        # Phase 1.5: LLM fallback for parse failures / incomplete deterministic passes (Fenic)
        # This populates missing technical analysis columns so targeted classification can proceed.
        start_time = time.time()
        results = self._run_llm_fallback_for_incomplete_results(results)
        elapsed = time.time() - start_time
        self.execution_times["llm_fallback"] = elapsed
        if elapsed > 0:
            logger.info(f"  ✅ LLM fallback executed in {elapsed:.2f}s")

        # Phase 2: Batch Heuristic Classification (Pure Python)
        start_time = time.time()
        results = self._run_batch_classification(results)
        elapsed = time.time() - start_time
        self.execution_times["classification"] = elapsed
        logger.info(f"  ✅ heuristic classification executed in {elapsed:.2f}s")

        pass_index += 1
        if progress_callback:
            progress_callback("classification", pass_index, total_passes)

        # Phase 2.5: LLM Filter Intent Classification (Fenic)
        # Filter intent requires business context, so always use LLM
        start_time = time.time()
        results = self._run_llm_filter_intent(results)
        elapsed = time.time() - start_time
        self.execution_times["filter_intent"] = elapsed
        if elapsed > 0:
            logger.info(f"  ✅ LLM filter intent executed in {elapsed:.2f}s")

        # Phase 3: Merge Results & Build Semantics (Pure Python)
        start_time = time.time()
        result_df = self._merge_and_build_dataframe(results)
        elapsed = time.time() - start_time
        self.execution_times["merge"] = elapsed
        logger.info(f"  ✅ merge and build executed in {elapsed:.2f}s")

        pass_index += 1
        if progress_callback:
            progress_callback("merge", pass_index, total_passes)

        # Phase 4: LLM-Only Passes (Fenic)
        # Now that we use explicit Polars schemas, struct columns work correctly
        for pass_name in llm_passes:
            if self._should_skip_pass(pass_name):
                logger.info(f"  ⏭️ {pass_name} skipped (disabled in config)")
                pass_index += 1
                if progress_callback:
                    progress_callback(pass_name, pass_index, total_passes)
                continue

            try:
                result_df, success = self._execute_llm_pass(pass_name, result_df)
                pass_index += 1
                if progress_callback:
                    progress_callback(pass_name, pass_index, total_passes)
            except Exception as e:
                logger.warning(f"  ⚠️ {pass_name} failed: {e}")
                pass_index += 1
                if progress_callback:
                    progress_callback(pass_name, pass_index, total_passes)

        return result_df

    def _run_deterministic_analysis_fenic(
        self,
        rows: List[Dict[str, Any]],
        dialect: Optional[str],
    ) -> Dict[str, HybridModelResult]:
        """Run deterministic analysis using a Fenic/Polars UDF (in-process).

        This avoids ProcessPoolExecutor overhead (schema pickling, process spin-up),
        and enables inserting Fenic async UDF stages (e.g. graph enrichment) between passes.

        Returns:
            Dict mapping model_id to HybridModelResult
        """
        results: Dict[str, HybridModelResult] = {}
        row_by_model_id: Dict[str, Dict[str, Any]] = {}
        model_ids: List[str] = []
        sqls: List[str] = []

        for row in rows:
            model_id = row.get("model_id", "unknown")
            row_by_model_id[model_id] = row
            # Prefer canonical_sql when available.
            sql = row.get("canonical_sql") or row.get("sql") or ""
            model_ids.append(model_id)
            sqls.append(sql)

        polars_df = pl.DataFrame(
            {"model_id": model_ids, "canonical_sql": sqls},
            schema={"model_id": pl.String, "canonical_sql": pl.String},
        )
        df = self.session.create_dataframe(polars_df)
        schema_dict = self.schema
        dialect_str = dialect or "snowflake"

        def _dump_deterministic(det: DeterministicResult) -> Dict[str, Any]:
            """Convert DeterministicResult into JSON-serializable dict."""
            def _dump_model(m: Any) -> Any:
                if m is None:
                    return None
                # Pydantic v2
                if hasattr(m, "model_dump"):
                    return m.model_dump()
                # dataclasses (e.g. CompletionResult)
                if dataclasses.is_dataclass(m):
                    return dataclasses.asdict(m)
                return m

            def _dump_dict(d: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
                if d is None:
                    return None
                return {k: _dump_model(v) for k, v in d.items()}

            return {
                "parse_error": det.parse_error,
                "analysis_errors": det.analysis_errors,
                "fallback_passes": det.fallback_passes,
                "completeness": {k: _dump_model(v) for k, v in (det.completeness or {}).items()},
                "quality_by_pass": {k: _dump_model(v) for k, v in (det.quality_by_pass or {}).items()},
                "relation_analysis": _dump_model(det.relation_analysis),
                "column_analysis": _dump_model(det.column_analysis),
                "join_analysis": _dump_model(det.join_analysis),
                "filter_analysis": _dump_model(det.filter_analysis),
                "grouping_by_scope": _dump_dict(det.grouping_by_scope),
                "window_by_scope": _dump_dict(det.window_by_scope),
                "output_by_scope": _dump_dict(det.output_by_scope),
                "enrichment": det.enrichment.model_dump() if det.enrichment else None,
            }

        @udf(return_type=StringType)
        def relations_json(model_id: str, canonical_sql: str) -> str:
            if not canonical_sql:
                return json.dumps({"parse_error": None, "analysis_error": None, "relation_analysis": None})
            executor = DeterministicExecutor(schema=schema_dict)
            relation_analysis, qualified_ast, parse_error, analysis_error = executor.run_pass_1_relations(
                canonical_sql, dialect=dialect_str
            )
            output_cols: list[str] = []
            if qualified_ast and qualified_ast.find(exp.Select):
                output_cols = [e.alias_or_name for e in qualified_ast.find(exp.Select).expressions]
            payload = {
                "parse_error": parse_error,
                "analysis_error": analysis_error,
                "relation_analysis": relation_analysis.model_dump() if relation_analysis else None,
                "output_columns": output_cols,
            }
            return json.dumps(payload)

        df2 = df.with_column(
            "relations_json",
            relations_json(fc.col("model_id"), fc.col("canonical_sql")),
        )

        # Optional: graph enrichment as async_udf (fail-open). This runs in-process,
        # so it can safely use the provided LineageStorage without pickling.
        if self.lineage_storage is not None:
            enricher = GraphEnricher(self.lineage_storage)

            @async_udf(return_type=StringType, max_concurrency=20, timeout_seconds=2, num_retries=0)
            async def enrichment_json(model_id: str, relations_json_str: str) -> str:
                try:
                    payload = json.loads(relations_json_str or "{}")
                except Exception as e:
                    logger.debug(f"Failed to parse relations JSON for {model_id}: {e}")
                    return "{}"

                # Extract relation bases from relation_analysis
                bases: set[str] = set()
                ra = payload.get("relation_analysis") or {}
                for rel in ra.get("relations") or []:
                    base = rel.get("base")
                    if base:
                        bases.add(base)

                out_cols = payload.get("output_columns") or []

                try:
                    enriched = await enricher.enrich_model(model_id, bases, out_cols)
                    return json.dumps(enriched.model_dump())
                except Exception as e:
                    logger.debug(f"Graph enrichment failed for {model_id}: {e}")
                    return "{}"

            df2 = df2.with_column(
                "enrichment_json",
                enrichment_json(fc.col("model_id"), fc.col("relations_json")),
            )
        else:
            df2 = df2.with_column("enrichment_json", fc.lit("{}"))

        @udf(return_type=StringType)
        def deterministic_json(
            model_id: str,
            canonical_sql: str,
            relations_json_str: str,
            enrichment_json_str: str,
        ) -> str:
            if not canonical_sql:
                return json.dumps({"parse_error": None, "fallback_passes": ["all"]})

            try:
                rel_payload = json.loads(relations_json_str or "{}")
            except Exception:
                rel_payload = {}

            parse_error = rel_payload.get("parse_error")
            if parse_error:
                return json.dumps({
                    "parse_error": parse_error,
                    "fallback_passes": [
                        "relation_analysis",
                        "column_analysis",
                        "join_analysis",
                        "filter_analysis",
                        "grouping_analysis",
                        "window_analysis",
                        "output_shape_analysis",
                    ],
                })

            analysis_error = rel_payload.get("analysis_error")
            executor = DeterministicExecutor(schema=schema_dict)
            relation_analysis = None
            if rel_payload.get("relation_analysis"):
                relation_analysis = RelationAnalysis.model_validate(rel_payload["relation_analysis"])

            enrichment: Optional[EnrichmentResult] = None
            try:
                enr_payload = json.loads(enrichment_json_str or "{}")
                if isinstance(enr_payload, dict) and enr_payload:
                    enrichment = EnrichmentResult.model_validate(enr_payload)
            except Exception:
                enrichment = None

            if relation_analysis is None:
                det = DeterministicResult()
                if analysis_error:
                    det.analysis_errors["relation_analysis"] = analysis_error
                    det.fallback_passes.append("relation_analysis")
                det.enrichment = enrichment
                det = executor.run_passes_2_to_8(
                    qualified_ast=None,
                    relation_analysis=None,
                    dialect=dialect_str,
                    result=det,
                )
                return json.dumps(_dump_deterministic(det))

            # Parse/annotate for downstream passes
            try:
                ast = parse_sql_cached(canonical_sql, dialect_str)
                try:
                    ast = annotate_types.annotate_types(ast, dialect=dialect_str)
                except Exception as e:
                    logger.warning(f"Failed to annotate types for {canonical_sql}: {e}")
                    pass
            except Exception as e:
                return json.dumps({
                    "parse_error": str(e),
                    "fallback_passes": [
                        "relation_analysis",
                        "column_analysis",
                        "join_analysis",
                        "filter_analysis",
                        "grouping_analysis",
                        "window_analysis",
                        "output_shape_analysis",
                    ],
                })

            det = DeterministicResult()
            if analysis_error:
                det.analysis_errors["relation_analysis"] = analysis_error
                det.fallback_passes.append("relation_analysis")
            det.enrichment = enrichment
            det = executor.run_passes_2_to_8(
                qualified_ast=ast,
                relation_analysis=relation_analysis,
                dialect=dialect_str,
                result=det,
            )
            return json.dumps(_dump_deterministic(det))

        df2 = df2.with_column(
            "deterministic_json",
            deterministic_json(
                fc.col("model_id"),
                fc.col("canonical_sql"),
                fc.col("relations_json"),
                fc.col("enrichment_json"),
            ),
        )

        out_rows = df2.to_pylist()

        for r in out_rows:
            model_id = r.get("model_id", "unknown")
            original_row = row_by_model_id.get(model_id, {})
            payload = {}
            try:
                payload = json.loads(r.get("deterministic_json") or "{}")
            except Exception:
                payload = {"parse_error": "failed_to_parse_deterministic_json"}

            det_result = DeterministicResult()
            det_result.parse_error = payload.get("parse_error")
            det_result.analysis_errors = payload.get("analysis_errors") or {}
            det_result.fallback_passes = payload.get("fallback_passes") or []

            # Rehydrate pydantic models
            if payload.get("relation_analysis"):
                det_result.relation_analysis = RelationAnalysis.model_validate(payload["relation_analysis"])
            if payload.get("column_analysis"):
                det_result.column_analysis = ColumnAnalysis.model_validate(payload["column_analysis"])
            if payload.get("join_analysis"):
                det_result.join_analysis = JoinEdgeAnalysis.model_validate(payload["join_analysis"])
            if payload.get("filter_analysis"):
                det_result.filter_analysis = FilterAnalysis.model_validate(payload["filter_analysis"])
            if payload.get("grouping_by_scope"):
                det_result.grouping_by_scope = {
                    k: GroupingAnalysis.model_validate(v) for k, v in payload["grouping_by_scope"].items()
                }
            if payload.get("window_by_scope"):
                det_result.window_by_scope = {
                    k: WindowAnalysis.model_validate(v) for k, v in payload["window_by_scope"].items()
                }
            if payload.get("output_by_scope"):
                det_result.output_by_scope = {
                    k: OutputShapeAnalysis.model_validate(v) for k, v in payload["output_by_scope"].items()
                }

            # Enrichment sidecar
            try:
                enr_payload = json.loads(r.get("enrichment_json") or "{}")
                if isinstance(enr_payload, dict) and enr_payload:
                    det_result.enrichment = EnrichmentResult.model_validate(enr_payload)
            except Exception as e:
                logger.warning(f"Failed to load enrichment for {model_id}: {e}")
                pass

            # completeness / quality_by_pass are already dicts of primitives; keep as-is
            result = HybridModelResult(
                model_id=model_id,
                original_row=original_row,
                deterministic=det_result,
                parse_error=det_result.parse_error,
                passes_used={"all": "deterministic_fenic"},
            )
            results[model_id] = result

        return results

    def _run_batch_classification(
        self,
        results: Dict[str, HybridModelResult],
    ) -> Dict[str, HybridModelResult]:
        """Run targeted classification passes with batched LLM calls.

        Architecture:
        - Column classification: Batched LLM across ALL models with heuristic fallback
        - Time classification: Batched LLM across identified columns from column classification with heuristic fallback
        - Watermark classification: Heuristics only (structural patterns)

        PII detection is merged into column classification for better per-column context.

        Only models with successful deterministic analysis are classified.
        """
        # Collect models eligible for LLM classification
        models_for_llm: List[Dict[str, Any]] = []
        model_analyses: Dict[str, Dict[str, Any]] = {}  # Store analyses for heuristics

        for model_id, result in results.items():
            if not result.deterministic or result.parse_error:
                continue

            # Get outer scope grouping
            outer_grouping: Dict[str, Any] = {}
            if result.deterministic.grouping_by_scope and "outer" in result.deterministic.grouping_by_scope:
                outer_grouping = result.deterministic.grouping_by_scope["outer"].model_dump()

            if not outer_grouping.get("select"):
                continue

            # Get filter and relation analysis
            filter_analysis: Dict[str, Any] = {}
            if result.deterministic.filter_analysis:
                filter_analysis = result.deterministic.filter_analysis.model_dump()

            relation_analysis: Dict[str, Any] = {}
            if result.deterministic.relation_analysis:
                relation_analysis = result.deterministic.relation_analysis.model_dump()

            # Store for heuristic passes
            column_features = None
            if result.deterministic.enrichment:
                column_features = {
                    k: v.model_dump()
                    for k, v in result.deterministic.enrichment.column_features.items()
                }
            model_analyses[model_id] = {
                "outer_grouping": outer_grouping,
                "filter_analysis": filter_analysis,
                "relation_analysis": relation_analysis,
                "column_features": column_features,
            }

            # Add to LLM batch
            models_for_llm.append({
                "model_id": model_id,
                "grouping_analysis": outer_grouping,
                "relation_analysis": relation_analysis,
            })

        total_models = len(models_for_llm)
        if total_models == 0:
            return results

        logger.info(f"  📊 Classifying {total_models} models (Column Analysis)...")

        # Run batched LLM classification for all columns across all models
        llm_success = 0
        heuristic_fallback = 0

        try:
            batch_results = classify_columns_batch(
                models_for_llm,
                self.session,
                model_size=self.classification_model_size,
                use_examples=True,
            )

            # Apply LLM results
            for model_id, semantic_result in batch_results.items():
                results[model_id].semantic_classification = semantic_result.model_dump()
                results[model_id].passes_used["semantic"] = "llm"
                llm_success += 1

            # Fall back to heuristics for models that didn't get LLM results
            for model_id in model_analyses:
                if model_id not in batch_results:
                    try:
                        analyses = model_analyses[model_id]
                        semantic_result = heuristic_column_classification(
                            analyses["outer_grouping"],
                            analyses["relation_analysis"],
                            analyses["column_features"],
                        )
                        results[model_id].semantic_classification = semantic_result.model_dump()
                        results[model_id].passes_used["semantic"] = "heuristic"
                        heuristic_fallback += 1
                    except Exception as he:
                        logger.warning(f"Heuristic classification failed for {model_id}: {he}")

        except Exception as e:
            logger.warning(f"Batched LLM classification failed: {e}, falling back to heuristics for all models")
            # Fall back to heuristics for all models
            for model_id, analyses in model_analyses.items():
                try:
                    semantic_result = heuristic_column_classification(
                        analyses["outer_grouping"],
                        analyses["relation_analysis"],
                        analyses["column_features"],
                    )
                    results[model_id].semantic_classification = semantic_result.model_dump()
                    results[model_id].passes_used["semantic"] = "heuristic"
                    heuristic_fallback += 1
                except Exception as he:
                    logger.warning(f"Heuristic classification also failed for {model_id}: {he}")

        # Run batch time classification (LLM) and watermark classification (heuristics)
        models_for_time_llm: List[Dict[str, Any]] = []
        time_inputs: Dict[str, Dict[str, Any]] = {}
        for model_id, analyses in model_analyses.items():
            outer_grouping = analyses["outer_grouping"]
            filter_analysis = analyses["filter_analysis"]

            semantic_classification = results[model_id].semantic_classification or {}
            time_related_aliases = {
                c.get("column_alias")
                for c in semantic_classification.get("classifications", [])
                if c.get("is_time_related")
            }
            select_items = outer_grouping.get("select", []) if outer_grouping else []
            filtered_select = [
                item for item in select_items if item.get("alias") in time_related_aliases
            ]

            if time_related_aliases:
                models_for_time_llm.append(
                    {
                        "model_id": model_id,
                        "grouping_analysis": outer_grouping,
                        "filter_analysis": filter_analysis,
                        "select_items": filtered_select,
                    }
                )
                time_inputs[model_id] = {
                    "grouping_analysis": outer_grouping,
                    "filter_analysis": filter_analysis,
                    "select_items": filtered_select,
                }
            else:
                logger.info(
                    "Skipping LLM time classification for %s: no time-related columns",
                    model_id,
                )
                results[model_id].time_classification = TimeClassificationResult(
                    classifications=[]
                ).model_dump()
                results[model_id].passes_used["time"] = "skipped"

        if models_for_time_llm:
            logger.info(
                f"  📊 Classifying {len(models_for_time_llm)} models (Time Analysis)..."
            )
            try:
                time_batch_results = classify_time_columns_batch(
                    models_for_time_llm,
                    self.session,
                    model_size=self.classification_model_size,
                )
                for model_id, time_result in time_batch_results.items():
                    results[model_id].time_classification = time_result.model_dump()
                    results[model_id].passes_used["time"] = "llm"

                missing = {
                    m["model_id"] for m in models_for_time_llm
                } - set(time_batch_results.keys())
                for model_id in missing:
                    inputs = time_inputs[model_id]
                    time_result = heuristic_time_classification(
                        inputs["grouping_analysis"],
                        inputs["filter_analysis"],
                        select_items=inputs["select_items"],
                    )
                    results[model_id].time_classification = time_result.model_dump()
                    results[model_id].passes_used["time"] = "heuristic"
            except Exception as te:
                logger.warning(
                    f"Batched LLM time classification failed: {te}; falling back to heuristics"
                )
                for model_id, inputs in time_inputs.items():
                    time_result = heuristic_time_classification(
                        inputs["grouping_analysis"],
                        inputs["filter_analysis"],
                        select_items=inputs["select_items"],
                    )
                    results[model_id].time_classification = time_result.model_dump()
                    results[model_id].passes_used["time"] = "heuristic"

        logger.info(f"  📊 Classifying {total_models} models (Watermark Analysis)...")
        for model_id, analyses in model_analyses.items():
            filter_analysis = analyses["filter_analysis"]
            watermark_result = heuristic_watermark_classification(filter_analysis)
            results[model_id].incremental_watermark = watermark_result.model_dump()
            results[model_id].passes_used["watermark"] = "heuristic"

        # Log classification summary
        logger.info(f"  📊 Column classification: {llm_success} LLM, {heuristic_fallback} heuristic fallback")

        return results

    def _run_llm_filter_intent(
        self,
        results: Dict[str, HybridModelResult],
    ) -> Dict[str, HybridModelResult]:
        """Run batched LLM-based filter intent classification.

        Filter intent is fundamentally about business context, so we use LLM
        for meaningful descriptions and intent classification. This method
        batches all models into a single Fenic call for efficiency.

        Args:
            results: Dict of model_id -> HybridModelResult with deterministic results

        Returns:
            Updated results with filter_intent populated
        """
        # Collect models that need filter intent classification
        models_for_llm: List[Dict[str, Any]] = []
        filter_analyses: Dict[str, Dict[str, Any]] = {}  # Store for heuristic fallback

        for model_id, result in results.items():
            if not result.deterministic or result.parse_error:
                continue

            filter_analysis: Dict[str, Any] = {}
            if result.deterministic.filter_analysis:
                filter_analysis = result.deterministic.filter_analysis.model_dump()

            # Only classify if there are actual predicates
            has_predicates = (
                filter_analysis.get("where")
                or filter_analysis.get("having")
                or filter_analysis.get("qualify")
            )
            if has_predicates:
                filter_analyses[model_id] = filter_analysis
                models_for_llm.append({
                    "model_id": model_id,
                    "filter_analysis": filter_analysis,
                })

        if not models_for_llm:
            return results

        logger.info(f"  📊 Classifying filter intent for {len(models_for_llm)} models (batched LLM)...")

        # Run batched LLM classification
        llm_success = 0
        heuristic_fallback = 0

        try:
            batch_results = classify_filter_intent_batch(
                models_for_llm,
                self.session,
                model_size=self.classification_model_size,
                use_examples=True,
            )

            # Apply LLM results
            for model_id, filter_intent_result in batch_results.items():
                results[model_id].filter_intent = filter_intent_result.model_dump()
                results[model_id].passes_used["filter_intent"] = "llm"
                llm_success += 1

            # Fall back to heuristics for models that didn't get LLM results
            for model_id in filter_analyses:
                if model_id not in batch_results:
                    try:
                        heuristic_result = heuristic_filter_intent_classification(
                            filter_analyses[model_id]
                        )
                        results[model_id].filter_intent = heuristic_result.model_dump()
                        results[model_id].passes_used["filter_intent"] = "heuristic"
                        heuristic_fallback += 1
                    except Exception as he:
                        logger.warning(f"Filter intent heuristic fallback failed for {model_id}: {he}")

        except Exception as e:
            logger.warning(f"Batched filter intent LLM failed: {e}, falling back to heuristics for all")
            # Fall back to heuristics for all models
            for model_id, filter_analysis in filter_analyses.items():
                try:
                    heuristic_result = heuristic_filter_intent_classification(filter_analysis)
                    results[model_id].filter_intent = heuristic_result.model_dump()
                    results[model_id].passes_used["filter_intent"] = "heuristic"
                    heuristic_fallback += 1
                except Exception as he:
                    logger.warning(f"Filter intent heuristic also failed for {model_id}: {he}")

        # Log filter intent summary
        logger.info(f"  📊 Filter intent: {llm_success} LLM, {heuristic_fallback} heuristic fallback")

        return results

    def _run_llm_fallback_for_incomplete_results(
        self,
        results: Dict[str, HybridModelResult],
    ) -> Dict[str, HybridModelResult]:
        """Run per-pass LLM fallback for models where deterministic analysis is incomplete.

        Deterministic analysis can fail in two ways:
        - **Parse failure**: SQLGlot cannot parse the dialect → run LLM technical passes to produce
          relation/column/join/filter/grouping/window/output analyses.
        - **Completeness failure**: deterministic returns fallback_passes based on thresholds →
          run only the corresponding LLM passes (plus dependencies) for those models.

        The goal is to unblock targeted classification + merge, while keeping deterministic analysis
        for models that are already complete.
        """
        # Identify models needing any fallback
        fallback_models: List[HybridModelResult] = []
        for r in results.values():
            det = r.deterministic
            if det is None:
                # deterministic crashed; treat as full technical fallback
                fallback_models.append(r)
                continue
            if r.parse_error or det.parse_error:
                fallback_models.append(r)
                continue
            if det.fallback_passes:
                fallback_models.append(r)

        if not fallback_models:
            return results

        # Group by the specific fallback passes needed, so we don't overwrite passes on unrelated models.
        # Key is the set of DAG pass names to run.
        from collections import defaultdict

        groups: Dict[Tuple[str, ...], List[HybridModelResult]] = defaultdict(list)
        for r in fallback_models:
            det = r.deterministic
            if det is None or r.parse_error or (det and det.parse_error):
                # Full technical fallback for parse failures
                wanted = {
                    "relation_analysis",
                    "column_analysis",
                    "join_analysis",
                    "filter_analysis",
                    "grouping_analysis",
                    "time_analysis",
                    "window_analysis",
                    "output_shape_analysis",
                }
            else:
                wanted = set()
                for p in det.fallback_passes:
                    # Names are normalized across deterministic and DAG passes.
                    if p in self.dag.passes:
                        wanted.add(p)
                # If windows/output need fallback, we need their dependencies too.
                if "window_analysis" in wanted:
                    wanted.add("time_analysis")
                if "output_shape_analysis" in wanted:
                    wanted.update({"window_analysis", "time_analysis"})

            key = tuple(sorted(wanted))
            groups[key].append(r)

        for wanted_passes, group_models in groups.items():
            if not wanted_passes:
                continue

            # Compute closure of dependencies
            closure = set(wanted_passes)
            # Expand required dependencies via DAG metadata
            changed = True
            while changed:
                changed = False
                for p in list(closure):
                    deps = self.dag.dependencies.get(p, [])
                    for d in deps:
                        if d in self.dag.passes and d not in closure:
                            closure.add(d)
                            changed = True

            execution_order = [
                p for p in self.dag.get_execution_order() if p in closure and p not in LLM_ONLY_PASSES
            ]

            # Build input rows for this group
            input_rows: List[Dict[str, Any]] = []
            for r in group_models:
                orig = r.original_row
                # Seed with required metadata columns. (DAG passes group_by on these.)
                row: Dict[str, Any] = {
                    "model_id": orig.get("model_id", r.model_id),
                    "model_name": orig.get("model_name", ""),
                    "path": orig.get("path", ""),
                    "filename": orig.get("filename", ""),
                    "sql": orig.get("sql", ""),
                    "canonical_sql": orig.get("canonical_sql", orig.get("sql", "")),
                }
                input_rows.append(row)

            df_fb = self.session.create_dataframe(input_rows)

            # Execute required technical passes in DAG order
            for pass_name in execution_order:
                if self._should_skip_pass(pass_name):
                    continue
                df_fb, _success = self._execute_llm_pass(pass_name, df_fb)

            fb_rows = df_fb.to_pylist()
            fb_by_id: Dict[str, Dict[str, Any]] = {r["model_id"]: r for r in fb_rows if "model_id" in r}

            # Merge fallback outputs back into HybridModelResult as DeterministicResult
            for r in group_models:
                row = fb_by_id.get(r.original_row.get("model_id", r.model_id))
                if not row:
                    logger.warning(f"No fallback row produced for {r.model_id}; leaving deterministic as-is")
                    continue

                # Ensure we have a DeterministicResult container
                det = r.deterministic or DeterministicResult(method="llm_fallback")
                det.method = "llm_fallback"
                det.parse_error = None

                # Convert technical pass outputs into our deterministic result types
                if row.get("relation_analysis"):
                    det.relation_analysis = RelationAnalysis.model_validate(row["relation_analysis"])
                    r.passes_used["relations"] = "llm_fallback"
                if row.get("column_analysis"):
                    det.column_analysis = ColumnAnalysis.model_validate(row["column_analysis"])
                    r.passes_used["columns"] = "llm_fallback"
                if row.get("join_analysis"):
                    det.join_analysis = JoinEdgeAnalysis.model_validate(row["join_analysis"])
                    r.passes_used["joins"] = "llm_fallback"
                if row.get("filter_analysis"):
                    det.filter_analysis = FilterAnalysis.model_validate(row["filter_analysis"])
                    r.passes_used["filters"] = "llm_fallback"

                # grouping_by_scope: [{scope, grouping_for_scope}]
                # Note: Fenic may return structs as dicts or as JSON strings
                grouping_by_scope = row.get("grouping_by_scope") or []
                if grouping_by_scope:
                    det.grouping_by_scope = {}
                    for item in grouping_by_scope:
                        # Handle case where item is a JSON string instead of dict
                        if isinstance(item, str):
                            try:
                                item = json.loads(item)
                            except Exception:
                                logger.warning(f"Could not parse grouping_by_scope item: {item[:100]}")
                                continue
                        if not isinstance(item, dict):
                            logger.warning(f"Unexpected grouping_by_scope item type: {type(item)}")
                            continue
                        scope = item.get("scope")
                        g = item.get("grouping_for_scope")
                        if scope and g:
                            det.grouping_by_scope[scope] = GroupingAnalysis.model_validate(g)
                    if det.grouping_by_scope:
                        r.passes_used["grouping"] = "llm_fallback"

                # window_by_scope: [{scope, window_analysis_json}]
                window_by_scope = row.get("window_by_scope") or []
                if window_by_scope:
                    det.window_by_scope = {}
                    for item in window_by_scope:
                        # Handle case where item is a JSON string instead of dict
                        if isinstance(item, str):
                            try:
                                item = json.loads(item)
                            except Exception:
                                logger.warning(f"Could not parse window_by_scope item: {item[:100]}")
                                continue
                        if not isinstance(item, dict):
                            logger.warning(f"Unexpected window_by_scope item type: {type(item)}")
                            continue
                        scope = item.get("scope")
                        wj = item.get("window_analysis_json")
                        if scope and wj:
                            try:
                                det.window_by_scope[scope] = WindowAnalysis.model_validate(json.loads(wj))
                            except Exception:
                                # If parsing fails, leave empty for this scope
                                det.window_by_scope[scope] = WindowAnalysis(windows=[])
                    if det.window_by_scope:
                        r.passes_used["windows"] = "llm_fallback"

                # output_by_scope: [{scope, output_for_scope}]
                output_by_scope = row.get("output_by_scope") or []
                if output_by_scope:
                    det.output_by_scope = {}
                    for item in output_by_scope:
                        # Handle case where item is a JSON string instead of dict
                        if isinstance(item, str):
                            try:
                                item = json.loads(item)
                            except Exception:
                                logger.warning(f"Could not parse output_by_scope item: {item[:100]}")
                                continue
                        if not isinstance(item, dict):
                            logger.warning(f"Unexpected output_by_scope item type: {type(item)}")
                            continue
                        scope = item.get("scope")
                        o = item.get("output_for_scope")
                        if scope and o:
                            det.output_by_scope[scope] = OutputShapeAnalysis.model_validate(o)
                    if det.output_by_scope:
                        r.passes_used["output"] = "llm_fallback"

                # Clear deterministic fallback flags now that we filled via LLM
                det.fallback_passes = []

                r.deterministic = det
                r.parse_error = None

        return results

    def _merge_and_build_dataframe(
        self,
        results: Dict[str, HybridModelResult],
    ) -> fc.DataFrame:
        """Merge all results and build final DataFrame for LLM-only passes.

        Uses explicit Polars schema from Fenic utilities to avoid type inference
        issues with complex nested structs and None values.
        """
        import json

        output_rows: List[Dict[str, Any]] = []

        for _model_id, result in results.items():
            # Skip models that failed parsing - they can't go through LLM passes
            if result.parse_error or not result.deterministic:
                logger.debug(f"Skipping {result.model_id}: no deterministic results")
                continue

            orig = result.original_row
            det = result.deterministic

            # Build row with proper struct types (model_dump for structs, None for missing)
            row: Dict[str, Any] = {
                # Simple scalar columns
                "model_id": orig.get("model_id", ""),
                "model_name": orig.get("model_name", ""),
                "path": orig.get("path", ""),
                "filename": orig.get("filename", ""),
                "sql": orig.get("sql", ""),
                "canonical_sql": orig.get("canonical_sql", ""),
                # Pass through dbt metadata for downstream passes
                "materialization": orig.get("materialization", ""),
                "model_description": orig.get("model_description", ""),
                # Struct columns (None if not present)
                "relation_analysis": det.relation_analysis.model_dump() if det.relation_analysis else None,
                "column_analysis": det.column_analysis.model_dump() if det.column_analysis else None,
                "join_analysis": det.join_analysis.model_dump() if det.join_analysis else None,
                "filter_analysis": det.filter_analysis.model_dump() if det.filter_analysis else None,
                # Scoped analysis - all are arrays for consistency
                "grouping_by_scope": [],
                "time_by_scope": [],
                "window_by_scope": [],
                "output_by_scope": [],
                # Business semantics
                "business_semantics": None,
                "grain_humanization": None,
                # Analysis summary (filled by LLM pass)
                "analysis_summary": None,
                # Targeted classification results
                "time_classification": result.time_classification,  # Heuristic: time column classification
                "semantic_classification": result.semantic_classification,  # LLM+heuristic: column classification (includes PII)
                "filter_intent": result.filter_intent,  # LLM: business context for filters
                # Note: PII now in semantic_classification (pii_columns, high_risk_pii_count fields)
                "incremental_watermark": result.incremental_watermark,  # Heuristic: watermark detection
            }

            # Build scoped analysis - all as arrays for consistency
            if det.grouping_by_scope:
                row["grouping_by_scope"] = [
                    {"scope": scope, "grouping_for_scope": g.model_dump()}
                    for scope, g in det.grouping_by_scope.items()
                ]

            # Time analysis from classification results - convert to TimeAnalysis format
            if result.time_classification:
                time_analysis = self._convert_time_classification_to_time_analysis(
                    result.time_classification,
                    det.filter_analysis.model_dump() if det.filter_analysis else {},
                )
                if time_analysis:
                    row["time_by_scope"] = [
                        {"scope": "outer", "time_for_scope": time_analysis.model_dump()}
                    ]

            # Window analysis - array of scopes
            if det.window_by_scope:
                row["window_by_scope"] = [
                    {"scope": scope, "window_analysis_json": json.dumps(w.model_dump())}
                    for scope, w in det.window_by_scope.items()
                ]

            # Output analysis - array of scopes
            if det.output_by_scope:
                row["output_by_scope"] = [
                    {"scope": scope, "output_for_scope": o.model_dump()}
                    for scope, o in det.output_by_scope.items()
                ]

            # Build business semantics from classification results
            grouping_dict = {}
            if det.grouping_by_scope and "outer" in det.grouping_by_scope:
                grouping_dict = det.grouping_by_scope["outer"].model_dump()

            if result.semantic_classification and result.time_classification:
                business_semantics = self._build_business_semantics(
                    grouping_dict,
                    result.semantic_classification,
                    result.time_classification,
                    det,  # Pass deterministic results for intent fallback
                )
                row["business_semantics"] = business_semantics.model_dump()
                result.business_semantics = business_semantics

            output_rows.append(row)

        if not output_rows:
            logger.warning("No models with successful analysis - returning empty DataFrame")
            # Return empty DataFrame with correct schema
            polars_schema = build_hybrid_result_schema()
            empty_pl_df = pl.DataFrame(schema=polars_schema)
            return self.session.create_dataframe(empty_pl_df)

        # Create Polars DataFrame with explicit schema to avoid type inference issues
        polars_schema = build_hybrid_result_schema()
        try:
            pl_df = pl.DataFrame(output_rows, schema=polars_schema)
        except Exception as e:
            logger.error(f"Failed to create DataFrame with explicit schema: {e}")
            # Fall back to creating without schema and letting Polars infer
            logger.warning("Falling back to schema inference - struct types may not match")
            pl_df = pl.DataFrame(output_rows)

        # Convert Polars DataFrame to Fenic DataFrame
        return self.session.create_dataframe(pl_df)

    def _convert_time_classification_to_time_analysis(
        self,
        time_cls: Dict,
        filter_analysis: Dict,
    ) -> Optional[TimeAnalysis]:
        """Convert TimeClassificationResult to TimeAnalysis format.

        The LLM classification identifies which columns are time-related and their roles.
        This method converts that to the TimeAnalysis format expected by the schema.

        Args:
            time_cls: TimeClassificationResult dict from LLM classification
            filter_analysis: FilterAnalysis dict for extracting time predicates

        Returns:
            TimeAnalysis object or None if no time columns found
        """
        classifications = time_cls.get("classifications", [])
        if not classifications:
            return None

        # Extract time columns (names) and buckets (expressions)
        time_columns = [
            _get_time_column_name(c)
            for c in classifications
            if c.get("is_time_column")
        ]
        time_buckets = [
            _get_time_column_expr(c) or _get_time_column_name(c)
            for c in classifications
            if c.get("is_time_column") and c.get("time_role") == "bucket"
        ]

        # Find range boundary column for time_scope
        range_cols = [
            c for c in classifications
            if c.get("time_role") == "range_boundary"
        ]

        time_scope = None
        normalized_time_scope = None

        if range_cols:
            first = range_cols[0]
            primary_alias = _get_time_column_name(first)
            primary_expr = _get_time_column_expr(first)
            grain = first.get("grain")

            # Extract candidate (table, column) pairs for matching filter predicates
            primary_candidates = _extract_primary_time_candidates(primary_alias, primary_expr)

            # Pick a best-effort "qualified-ish" column string for TimeScope.column
            primary_time_col = ""
            if primary_candidates:
                table, name = primary_candidates[0]
                primary_time_col = f"{table}.{name}" if table else name

            # Extract time bounds from filter predicates
            bounds = _extract_time_bounds_from_filters(filter_analysis, primary_candidates)

            # Normalize end bound based on grain (inclusive -> exclusive)
            normalized_end: Optional[str] = None
            if bounds.end_value:
                normalized_end = _normalize_time_end_bound(
                    bounds.end_value, bounds.end_inclusive, grain
                )

            if primary_time_col:
                # Only set a time_scope if we found at least one bound.
                if bounds.start_value or bounds.end_value:
                    time_scope = TimeScope(
                        column=primary_time_col,
                        start=bounds.start_value or "",
                        end=bounds.end_value or "",
                        end_inclusive=bounds.end_inclusive if bounds.end_value else True,
                    )
                    normalized_time_scope = NormalizedTimeScope(
                        column=primary_time_col,
                        start=bounds.start_value or "",
                        end=normalized_end or (bounds.end_value or ""),
                        end_exclusive=True,
                    )

        return TimeAnalysis(
            time_scope=time_scope,
            normalized_time_scope=normalized_time_scope,
            time_buckets=time_buckets,
            time_columns=time_columns,
        )

    def _build_business_semantics(
        self,
        grouping: Dict,
        semantic_cls: Dict,
        time_cls: Dict,
        det: Optional[DeterministicResult] = None,
    ) -> BusinessSemantics:
        """Build BusinessSemantics from classification results.

        Uses raw SQL column names (column_alias) for the name field, NOT display names.
        This enables agents to cross-reference SQL column references to semantic metadata.

        Maps new semantic roles to business semantics categories:
        - metric → BusinessMeasure (aggregated values)
        - attribute, timestamp, flag, bucket_label → BusinessDimension (descriptive)
        - foreign_key, natural_key, surrogate_key → BusinessFact (grain-defining)
        """
        measures: List[BusinessMeasure] = []
        dimensions: List[BusinessDimension] = []
        facts: List[BusinessFact] = []
        pii_columns: List[str] = []

        # Roles that map to measures (aggregated values)
        measure_roles = {"metric"}

        # Roles that map to dimensions (descriptive attributes)
        dimension_roles = {"attribute", "timestamp", "flag", "bucket_label"}

        # Roles that map to facts (grain-defining keys)
        fact_roles = {"foreign_key", "natural_key", "surrogate_key"}

        classifications = semantic_cls.get("classifications", [])
        for cls in classifications:
            role = cls.get("semantic_role", "")
            # Use column_alias (raw SQL column name) as name, NOT business_name
            raw_name = cls.get("column_alias", "") or cls.get("alias", "")
            expr = cls.get("expr", "")
            is_pii = cls.get("is_pii") or False

            if role in measure_roles:
                measures.append(BusinessMeasure(
                    name=raw_name,
                    expr=expr,
                    source_alias=raw_name,
                    default_agg=self._infer_agg_type(expr),
                ))
            elif role in dimension_roles:
                dimensions.append(BusinessDimension(
                    name=raw_name,
                    source=expr,
                    pii=is_pii,
                ))
                if is_pii:
                    pii_columns.append(raw_name)
            elif role in fact_roles:
                # Foreign keys and natural keys are grain-defining
                # Surrogate keys are technical (not grain-defining for business purposes)
                is_grain_defining = role in ("foreign_key", "natural_key")
                facts.append(BusinessFact(
                    name=raw_name,
                    source=expr,
                    is_grain_defining=is_grain_defining,
                ))

        # Build time window from time classification
        time_window = BusinessTimeWindow()
        time_classifications = time_cls.get("classifications", [])
        time_cols = [c for c in time_classifications if c.get("is_time_column")]
        if time_cols:
            # Use column_alias (new format) with fallback to qualified_name (old format)
            time_window.attributes = [
                c.get("column_alias", "") or c.get("qualified_name", "")
                for c in time_cols
            ]
            range_cols = [c for c in time_cols if c.get("time_role") == "range_boundary"]
            if range_cols:
                time_window.column = range_cols[0].get("column_alias", "") or range_cols[0].get("qualified_name", "")

        # Compute grain
        grain_keys = grouping.get("result_grain", [])
        grain_human = self._humanize_grain(grain_keys)

        # Infer intent from semantic classification or deterministic analysis
        intent = semantic_cls.get("intent", "unknown")
        if intent == "unknown":
            # Fallback: infer from deterministic analysis
            intent = self._infer_intent_from_deterministic(grouping, det)

        # Infer domains from table and column names
        table_names: List[str] = []
        column_names: List[str] = []
        if det and det.relation_analysis:
            table_names = [r.base for r in det.relation_analysis.relations if r.base]
        if det and det.column_analysis:
            for cba in det.column_analysis.columns_by_alias:
                column_names.extend(cba.columns)
        domains = infer_domains_heuristic(table_names, column_names)

        return BusinessSemantics(
            fact_alias=semantic_cls.get("fact_alias"),
            grain_human=grain_human,
            grain_keys=grain_keys,
            measures=measures,
            dimensions=dimensions,
            facts=facts,
            time=time_window,
            segments=[],
            intent=intent,
            ordering=[],
            limit=None,
            pii_columns=pii_columns,
            domains=domains,  # type: ignore[arg-type]
        )

    def _infer_intent_from_deterministic(
        self,
        grouping: Dict,
        det: Optional[DeterministicResult],
    ) -> str:
        """Infer intent from deterministic analysis as fallback.

        This is only used when the LLM doesn't provide intent.
        """
        is_aggregated = grouping.get("is_aggregated", False)

        # Check for window functions (ranking/deduplication patterns)
        if det and det.window_by_scope and "outer" in det.window_by_scope:
            window_analysis = det.window_by_scope["outer"]
            if window_analysis.windows:
                # Check for ROW_NUMBER pattern (often deduplication)
                for w in window_analysis.windows:
                    if "ROW_NUMBER" in w.func.upper():
                        return "ranking"  # Could be deduplication
                return "ranking"

        # Check for joins + aggregation (reporting pattern)
        if det and det.join_analysis and det.join_analysis.joins:
            if is_aggregated:
                return "aggregation"
            return "unknown"  # transformation

        if is_aggregated:
            return "aggregation"

        return "unknown"

    def _infer_agg_type(self, expr: str) -> str:
        """Infer aggregation type from expression."""
        expr_upper = expr.upper()
        if "SUM(" in expr_upper:
            return "SUM"
        elif "COUNT(DISTINCT" in expr_upper:
            return "COUNT_DISTINCT"
        elif "COUNT(" in expr_upper:
            return "COUNT"
        elif "AVG(" in expr_upper:
            return "AVG"
        elif "MIN(" in expr_upper:
            return "MIN"
        elif "MAX(" in expr_upper:
            return "MAX"
        return "OTHER"

    def _humanize_grain(self, grain_keys: List[str]) -> str:
        """Convert grain keys to human-readable format."""
        if not grain_keys:
            return "per row"

        humanized = []
        for key in grain_keys[:5]:
            if "." in key:
                key = key.split(".")[-1]
            for suffix in ["_id", "_sk", "_key", "_number"]:
                if key.lower().endswith(suffix):
                    key = key[:-len(suffix)]
                    break
            key = key.replace("_", " ").lower()
            humanized.append(key)

        return "per " + " × ".join(humanized)

    def _should_skip_pass(self, pass_name: str) -> bool:
        """Check if pass should be skipped based on settings."""
        if pass_name == "audit_analysis": #nosec: B105 -- not a password
            return not self.pipeline_config.enable_audit
        return False

    def _execute_llm_pass(
        self,
        pass_name: str,
        df: fc.DataFrame,
    ) -> tuple[fc.DataFrame, bool]:
        """Execute a single LLM-only pass."""
        pass_instance = self.dag.get_pass(pass_name)
        if not pass_instance:
            logger.warning(f"Pass {pass_name} not found in DAG")
            return df, False

        start_time = time.time()

        try:
            pass_instance.validate_inputs(df)
            df = pass_instance.execute(df).cache()
            row_count = df.count()

            elapsed = time.time() - start_time
            self.execution_times[pass_name] = elapsed

            model_str = f"{row_count} models" if row_count > 1 else "1 model"
            logger.info(f"  ✅ {pass_name} executed for {model_str} in {elapsed:.2f}s")

            return df, True

        except Exception as e:
            logger.error(f"✗ Error in {pass_name}: {e}")
            raise

    def get_execution_order(self) -> List[str]:
        """Get execution order for progress tracking."""
        llm_passes = [p for p in self.dag.get_execution_order() if p in LLM_ONLY_PASSES]
        return ["deterministic", "classification", "merge"] + llm_passes
