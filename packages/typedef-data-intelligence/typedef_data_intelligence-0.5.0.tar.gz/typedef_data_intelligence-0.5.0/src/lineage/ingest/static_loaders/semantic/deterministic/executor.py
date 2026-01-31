"""Hybrid executor for deterministic + LLM analysis.

Orchestrates all deterministic passes with shared parsed AST,
checks completeness, and determines which passes need LLM fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.optimizer import annotate_types

from lineage.ingest.static_loaders.semantic.deterministic.columns import analyze_columns
from lineage.ingest.static_loaders.semantic.deterministic.completeness import (
    CompletionResult,
    check_completeness,
    needs_fallback,
)
from lineage.ingest.static_loaders.semantic.deterministic.filters import analyze_filters
from lineage.ingest.static_loaders.semantic.deterministic.graph_enrichment import (
    EnrichmentResult,
    GraphEnricher,
)
from lineage.ingest.static_loaders.semantic.deterministic.grouping import (
    analyze_grouping,
)
from lineage.ingest.static_loaders.semantic.deterministic.joins import analyze_joins
from lineage.ingest.static_loaders.semantic.deterministic.null_killing import (
    detect_null_killing,
)
from lineage.ingest.static_loaders.semantic.deterministic.output import analyze_output
from lineage.ingest.static_loaders.semantic.deterministic.quality import (
    PassQuality,
    build_alias_to_schema_columns,
    filter_ambiguity_quality,
    find_unqualified_ambiguities_in_scope,
    grouping_ambiguity_quality,
    join_partial_quality,
)
from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    AnalysisError,
    analyze_relations,
)
from lineage.ingest.static_loaders.semantic.deterministic.windows import analyze_windows
from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    FilterAnalysis,
    GroupingAnalysis,
    JoinEdgeAnalysis,
    OutputShapeAnalysis,
    RelationAnalysis,
    WindowAnalysis,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached

logger = logging.getLogger(__name__)


@dataclass
class DeterministicResult:
    """Result of deterministic analysis for a single model."""

    # Analysis results (None if analysis failed)
    relation_analysis: Optional[RelationAnalysis] = None
    column_analysis: Optional[ColumnAnalysis] = None
    join_analysis: Optional[JoinEdgeAnalysis] = None
    filter_analysis: Optional[FilterAnalysis] = None
    grouping_by_scope: Optional[Dict[str, GroupingAnalysis]] = None
    window_by_scope: Optional[Dict[str, WindowAnalysis]] = None
    output_by_scope: Optional[Dict[str, OutputShapeAnalysis]] = None

    # Graph enrichment sidecar
    enrichment: Optional[EnrichmentResult] = None

    # Metadata
    parse_error: Optional[str] = None
    analysis_errors: Dict[str, str] = field(default_factory=dict)
    completeness: Dict[str, CompletionResult] = field(default_factory=dict)
    fallback_passes: List[str] = field(default_factory=list)
    quality_by_pass: Dict[str, PassQuality] = field(default_factory=dict)

    # Provenance tracking
    method: str = "deterministic"  # or "llm_fallback"

    @property
    def needs_any_fallback(self) -> bool:
        """Check if any pass needs LLM fallback."""
        return bool(self.parse_error) or bool(self.fallback_passes)

    @property
    def all_results(self) -> Dict[str, Any]:
        """Get all results as a dict."""
        return {
            "relation_analysis": self.relation_analysis,
            "column_analysis": self.column_analysis,
            "join_analysis": self.join_analysis,
            "filter_analysis": self.filter_analysis,
            "grouping_by_scope": self.grouping_by_scope,
            "window_by_scope": self.window_by_scope,
            "output_by_scope": self.output_by_scope,
        }


class DeterministicExecutor:
    """Execute all deterministic passes with shared AST and LLM fallback support."""

    def __init__(
        self,
        schema: Optional[Dict] = None,
        unresolved_threshold: float = 0.10,
        ambiguity_threshold: float = 0.05,
        enricher: Optional[GraphEnricher] = None,
    ):
        """Initialize the executor.

        Args:
            schema: Optional SQLGlot-compatible schema for column resolution
                   Format: {catalog: {schema: {table: {col: type}}}}
            unresolved_threshold: Maximum ratio of unresolved items before fallback
            ambiguity_threshold: Maximum allowed ambiguity/partial ratio before fallback
            enricher: Optional GraphEnricher for lineage-based insights
        """
        self.schema = schema
        self.unresolved_threshold = unresolved_threshold
        self.ambiguity_threshold = ambiguity_threshold
        self.enricher = enricher

    def run_all_passes(
        self,
        sql: str,
        dialect: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> DeterministicResult:
        """Run all deterministic passes on a SQL query.

        Expects pre-qualified canonical_sql from dbt ingest. Parses and annotates
        types for richer analysis.

        Args:
            sql: The SQL query string (should be canonical_sql, already qualified)
            dialect: SQL dialect (e.g., 'snowflake', 'duckdb', 'hive')
            model_id: Unique identifier for the model (used for graph enrichment)

        Returns:
            DeterministicResult with all analysis outputs
        """
        result = DeterministicResult()

        relation_analysis, qualified_ast, parse_error, analysis_error = self.run_pass_1_relations(
            sql, dialect
        )
        if parse_error:
            result.parse_error = parse_error
            result.fallback_passes = [
                "relation_analysis",
                "column_analysis",
                "join_analysis",
                "filter_analysis",
                "grouping_analysis",
                "window_analysis",
                "output_shape_analysis",
            ]
            logger.warning(f"Parse failed, falling back to LLM for all passes: {parse_error}")
            return result

        if analysis_error:
            result.analysis_errors["relation_analysis"] = analysis_error
            result.fallback_passes.append("relation_analysis")

        result.relation_analysis = relation_analysis

        # Graph Enrichment (between Pass 1 and Pass 2)
        if self.enricher and result.relation_analysis:
            relation_bases = {r.base for r in result.relation_analysis.relations if r.base}
            output_cols = []
            if qualified_ast and qualified_ast.find(exp.Select):
                output_cols = [e.alias_or_name for e in qualified_ast.find(exp.Select).expressions]

            # Since DeterministicExecutor is sync, we use the sync helper directly if needed,
            # but usually it's used via HybridPipelineExecutor's async UDF.
            # We'll use the sync helper here for the unit tests and standalone usage.
            try:
                result.enrichment = self.enricher._fetch_enrichment_sync(
                    model_id or "", relation_bases, output_cols
                )
            except Exception as e:
                logger.debug(f"Sync graph enrichment failed: {e}")

        # Passes 2-8
        return self.run_passes_2_to_8(
            qualified_ast=qualified_ast,
            relation_analysis=result.relation_analysis,
            dialect=dialect,
            result=result,
        )

    def run_pass_1_relations(
        self,
        sql: str,
        dialect: Optional[str] = None,
    ) -> Tuple[Optional[RelationAnalysis], Optional[exp.Expression], Optional[str], Optional[str]]:
        """Run only Pass 1 (relations) and return the annotated AST."""
        # Parse and annotate
        try:
            ast = parse_sql_cached(sql, dialect)
        except SqlglotError as e:
            return None, None, str(e), None

        qualified_ast = ast
        try:
            qualified_ast = annotate_types.annotate_types(ast, dialect=dialect)
        except SqlglotError:
            qualified_ast = ast

        # Relations
        try:
            relations = analyze_relations(qualified_ast, dialect)
            return relations, qualified_ast, None, None
        except AnalysisError as e:
            return None, qualified_ast, None, str(e)

    def run_passes_2_to_8(
        self,
        qualified_ast: Optional[exp.Expression],
        relation_analysis: Optional[RelationAnalysis],
        dialect: Optional[str],
        result: Optional[DeterministicResult] = None,
    ) -> DeterministicResult:
        """Run Passes 2–8 given a pre-parsed AST and relation analysis."""
        if result is None:
            result = DeterministicResult()
        result.relation_analysis = relation_analysis

        if qualified_ast is None or relation_analysis is None:
            result.fallback_passes.append("relation_analysis")
            return result

        # Pass 2: Columns
        try:
            result.column_analysis = analyze_columns(
                qualified_ast,
                relation_analysis,
                self.schema,
                dialect,
                relation_hints=(
                    result.enrichment.relation_hints if result.enrichment else None
                ),
            )
        except AnalysisError as e:
            result.analysis_errors["column_analysis"] = str(e)
            result.fallback_passes.append("column_analysis")

        # Pass 3: Joins
        if result.column_analysis:
            try:
                result.join_analysis = analyze_joins(
                    qualified_ast,
                    relation_analysis,
                    result.column_analysis,
                    dialect,
                )
            except AnalysisError as e:
                result.analysis_errors["join_analysis"] = str(e)
                result.fallback_passes.append("join_analysis")

        # Pass 4: Filters
        if result.column_analysis:
            try:
                result.filter_analysis = analyze_filters(
                    qualified_ast,
                    relation_analysis,
                    result.column_analysis,
                    result.join_analysis,
                    dialect,
                )
            except AnalysisError as e:
                result.analysis_errors["filter_analysis"] = str(e)
                result.fallback_passes.append("filter_analysis")

        # Apply null-killing detection to join analysis
        if result.join_analysis and result.filter_analysis:
            try:
                result.join_analysis = detect_null_killing(
                    result.join_analysis,
                    result.filter_analysis,
                )
            except AnalysisError as e:
                logger.warning(f"Null-killing detection failed: {e}")

        # Determine scopes for per-scope passes
        scopes = self._extract_scopes(result.relation_analysis)

        # Pass 5: Grouping (per scope)
        if result.column_analysis:
            result.grouping_by_scope = {}
            for scope in scopes:
                try:
                    result.grouping_by_scope[scope] = analyze_grouping(
                        qualified_ast,
                        relation_analysis,
                        result.column_analysis,
                        scope,
                        dialect,
                    )
                except AnalysisError as e:
                    result.analysis_errors[f"grouping_analysis:{scope}"] = str(e)
                    if "grouping_analysis" not in result.fallback_passes:
                        result.fallback_passes.append("grouping_analysis")

        # Pass 7: Windows (per scope)
        result.window_by_scope = {}
        for scope in scopes:
            try:
                result.window_by_scope[scope] = analyze_windows(
                    qualified_ast,
                    scope,
                    dialect,
                )
            except AnalysisError as e:
                result.analysis_errors[f"window_analysis:{scope}"] = str(e)
                if "window_analysis" not in result.fallback_passes:
                    result.fallback_passes.append("window_analysis")

        # Pass 8: Output (per scope)
        result.output_by_scope = {}
        for scope in scopes:
            try:
                result.output_by_scope[scope] = analyze_output(
                    qualified_ast,
                    scope,
                    dialect,
                )
            except AnalysisError as e:
                result.analysis_errors[f"output_shape_analysis:{scope}"] = str(e)
                if "output_shape_analysis" not in result.fallback_passes:
                    result.fallback_passes.append("output_shape_analysis")

        # Step 4: Check completeness and determine additional fallbacks
        completeness_input = {
            "relation_analysis": result.relation_analysis,
            "column_analysis": result.column_analysis,
            "join_analysis": result.join_analysis,
            "filter_analysis": result.filter_analysis,
        }

        # Add first scope's grouping for completeness check
        if result.grouping_by_scope and "outer" in result.grouping_by_scope:
            completeness_input["grouping_analysis"] = result.grouping_by_scope["outer"]

        if result.window_by_scope and "outer" in result.window_by_scope:
            completeness_input["window_analysis"] = result.window_by_scope["outer"]

        if result.output_by_scope and "outer" in result.output_by_scope:
            completeness_input["output_shape_analysis"] = result.output_by_scope["outer"]

        result.completeness = check_completeness(
            completeness_input,
            self.unresolved_threshold,
        )

        # Add completeness-based fallbacks
        for pass_name in needs_fallback(result.completeness):
            if pass_name not in result.fallback_passes:
                result.fallback_passes.append(pass_name)

        # Step 5: Compute quality sidecar (ambiguity + partialness) and add ambiguity-based fallbacks
        try:
            # Build schema columns per alias for ambiguity detection
            alias_to_cols = {}
            if result.relation_analysis:
                alias_to_cols = build_alias_to_schema_columns(
                    self.schema,
                    result.relation_analysis,
                    relation_hints=(
                        result.enrichment.relation_hints if result.enrichment else None
                    ),
                )

            # Column ambiguity in outer scope (unqualified columns matching 2+ aliases)
            if result.relation_analysis:
                valid_outer_aliases = {r.alias for r in result.relation_analysis.relations if r.scope == "outer"}
            else:
                valid_outer_aliases = set()

            ambiguous_cols, col_examples = find_unqualified_ambiguities_in_scope(
                qualified_ast,
                scope="outer",
                valid_aliases=valid_outer_aliases,
                alias_to_schema_columns=alias_to_cols,
            )

            # Column pass quality
            if result.column_analysis:
                total_refs = len(result.column_analysis.column_refs) + len(result.column_analysis.unresolved_unqualified)
            else:
                total_refs = 0
            col_total = total_refs or 0
            col_ambiguity_score = (ambiguous_cols / col_total) if col_total else 0.0
            result.quality_by_pass["column_analysis"] = PassQuality( # nosec: B106
                pass_name="column_analysis",
                completeness_score=result.completeness.get("column_analysis").completeness_score if "column_analysis" in result.completeness else None,
                unresolved_count=len(result.column_analysis.unresolved_unqualified) if result.column_analysis else 0,
                total_count=col_total,
                ambiguous_count=ambiguous_cols,
                ambiguity_score=col_ambiguity_score,
                examples=col_examples,
            )

            # Grouping ambiguity (outer scope)
            if result.grouping_by_scope and "outer" in result.grouping_by_scope and result.relation_analysis:
                result.quality_by_pass["grouping_analysis"] = grouping_ambiguity_quality(
                    qualified_ast,
                    result.grouping_by_scope["outer"],
                    result.relation_analysis,
                    self.schema,
                    scope="outer",
                    relation_hints=(
                        result.enrichment.relation_hints if result.enrichment else None
                    ),
                )

            # Filter ambiguity (outer scope)
            if result.filter_analysis and result.relation_analysis:
                result.quality_by_pass["filter_analysis"] = filter_ambiguity_quality(
                    qualified_ast,
                    result.filter_analysis,
                    result.relation_analysis,
                    self.schema,
                    scope="outer",
                    relation_hints=(
                        result.enrichment.relation_hints if result.enrichment else None
                    ),
                )

            # Join partialness
            if result.join_analysis:
                result.quality_by_pass["join_analysis"] = join_partial_quality(result.join_analysis)

            # Apply ambiguity thresholds to fallback passes
            for pn, pq in result.quality_by_pass.items():
                if pq.should_fallback(self.ambiguity_threshold) and pn not in result.fallback_passes:
                    result.fallback_passes.append(pn)

        except Exception as e:
            logger.debug(f"Quality sidecar computation failed: {e}")

        return result

    def _extract_scopes(
        self,
        relation_analysis: Optional[RelationAnalysis],
    ) -> List[str]:
        """Extract unique scopes from relation analysis.

        Args:
            relation_analysis: RelationAnalysis with scope info

        Returns:
            List of unique scope labels, starting with 'outer'
        """
        scopes: Set[str] = {"outer"}

        if relation_analysis:
            for rel in relation_analysis.relations:
                scopes.add(rel.scope)

            # Add CTE scopes
            for cte_name in relation_analysis.cte_defs:
                scopes.add(f"cte:{cte_name}")

            # Add subquery scopes
            for sq_alias in relation_analysis.subqueries:
                scopes.add(f"subquery:{sq_alias}")

        return sorted(list(scopes))


def analyze_sql_deterministically(
    sql: str,
    dialect: Optional[str] = None,
    schema: Optional[Dict] = None,
) -> DeterministicResult:
    """Convenience function for deterministic SQL analysis.

    Args:
        sql: The SQL query string
        dialect: SQL dialect
        schema: Optional schema for column resolution

    Returns:
        DeterministicResult with all analysis outputs
    """
    executor = DeterministicExecutor(schema=schema)
    return executor.run_all_passes(sql, dialect)
