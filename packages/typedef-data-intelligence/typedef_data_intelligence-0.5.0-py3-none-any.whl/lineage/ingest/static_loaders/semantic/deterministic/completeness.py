"""Completeness checking for deterministic analysis.

Determines whether deterministic analysis is complete enough or should
fall back to LLM. Uses configurable thresholds.

Fallback Triggers:
- Parse failure: SQLGlot cannot parse the SQL dialect
- Completeness threshold: >10% unresolved columns (default)
- Validation failure: Output doesn't match expected schema
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from lineage.ingest.static_loaders.semantic.models import (
    ColumnAnalysis,
    FilterAnalysis,
    GroupingAnalysis,
    JoinEdgeAnalysis,
    OutputShapeAnalysis,
    RelationAnalysis,
    WindowAnalysis,
)

logger = logging.getLogger(__name__)


@dataclass
class CompletionResult:
    """Result of completeness checking for a single pass."""

    pass_name: str
    is_complete: bool
    completeness_score: float  # 0.0 to 1.0
    reason: Optional[str] = None
    unresolved_count: int = 0
    total_count: int = 0


# Default threshold for unresolved columns (10%)
DEFAULT_UNRESOLVED_THRESHOLD = 0.10


def check_relation_completeness(
    result: RelationAnalysis,
) -> CompletionResult:
    """Check if relation analysis is complete.

    Relation analysis is fully deterministic - only fails on parse error.
    This function checks for empty results which might indicate issues.

    Args:
        result: RelationAnalysis output

    Returns:
        CompletionResult
    """
    # Relations is complete if we have at least one relation
    # (empty is valid for simple literals-only queries)
    has_relations = len(result.relations) > 0
    has_tables = len(result.tables) > 0 or len(result.cte_defs) > 0

    if has_relations or has_tables:
        return CompletionResult( #nosec: B106
            pass_name="relation_analysis",
            is_complete=True,
            completeness_score=1.0,
        )
    else:
        # Empty result - might be valid, might indicate parse issue
        return CompletionResult( #nosec: B106
            pass_name="relation_analysis",
            is_complete=True,  # Still complete, just empty
            completeness_score=1.0,
            reason="No relations found (may be valid for literals-only queries)",
        )


def check_column_completeness(
    result: ColumnAnalysis,
    threshold: float = DEFAULT_UNRESOLVED_THRESHOLD,
) -> CompletionResult:
    """Check if column analysis is complete.

    Column analysis may have unresolved unqualified columns if schema
    is not available. Falls back to LLM if too many are unresolved.

    Args:
        result: ColumnAnalysis output
        threshold: Maximum allowed ratio of unresolved columns (default 10%)

    Returns:
        CompletionResult
    """
    total_refs = len(result.column_refs)
    unresolved = len(result.unresolved_unqualified)

    if total_refs == 0 and unresolved == 0:
        # No columns found - might be valid
        return CompletionResult( #nosec: B106
            pass_name="column_analysis",
            is_complete=True,
            completeness_score=1.0,
        )

    # Calculate completeness ratio
    total = total_refs + unresolved
    resolved = total_refs
    completeness = resolved / total if total > 0 else 1.0

    is_complete = completeness >= (1.0 - threshold)

    return CompletionResult( #nosec: B106
        pass_name="column_analysis",
        is_complete=is_complete,
        completeness_score=completeness,
        reason=f"{unresolved} unresolved columns" if not is_complete else None,
        unresolved_count=unresolved,
        total_count=total,
    )


def check_join_completeness(
    result: JoinEdgeAnalysis,
) -> CompletionResult:
    """Check if join analysis is complete.

    Join analysis is mostly deterministic - checks for reasonable output.

    Args:
        result: JoinEdgeAnalysis output

    Returns:
        CompletionResult
    """
    # Joins is complete - empty is valid (no joins in query)
    return CompletionResult( #nosec: B106
        pass_name="join_analysis",
        is_complete=True,
        completeness_score=1.0,
    )


def check_filter_completeness(
    result: FilterAnalysis,
    threshold: float = DEFAULT_UNRESOLVED_THRESHOLD,
) -> CompletionResult:
    """Check if filter analysis is complete.

    Filter analysis may have unresolved predicates if columns can't be resolved.

    Args:
        result: FilterAnalysis output
        threshold: Maximum allowed ratio of unresolved predicates

    Returns:
        CompletionResult
    """
    total_predicates = (
        len(result.where) + len(result.having) + len(result.qualify)
    )
    unresolved = len(result.unresolved_predicates)

    total = total_predicates + unresolved
    if total == 0:
        return CompletionResult( #nosec: B106
            pass_name="filter_analysis",
            is_complete=True,
            completeness_score=1.0,
        )

    completeness = total_predicates / total
    is_complete = completeness >= (1.0 - threshold)

    return CompletionResult( #nosec: B106
        pass_name="filter_analysis",
        is_complete=is_complete,
        completeness_score=completeness,
        reason=f"{unresolved} unresolved predicates" if not is_complete else None,
        unresolved_count=unresolved,
        total_count=total,
    )


def check_grouping_completeness(
    result: GroupingAnalysis,
) -> CompletionResult:
    """Check if grouping analysis is complete.

    Grouping analysis may fail source_alias resolution without schema.
    Note: Literal values (NULL, strings, numbers) legitimately have no
    source_aliases - we use the is_literal field to identify them.

    Args:
        result: GroupingAnalysis output

    Returns:
        CompletionResult
    """
    # Check if source_aliases are resolved for all select items
    # (excluding literal values which don't have source aliases)
    unresolved = 0
    total_non_literal = 0

    for item in result.select:
        # Skip literal values - they correctly have no source_aliases
        if item.is_literal:
            continue

        total_non_literal += 1
        if not item.source_aliases:
            unresolved += 1

    if total_non_literal == 0:
        # All items are literals - that's complete
        return CompletionResult(  # nosec: B106
            pass_name="grouping_analysis",
            is_complete=True,
            completeness_score=1.0,
        )

    completeness = (total_non_literal - unresolved) / total_non_literal
    is_complete = completeness >= (1.0 - DEFAULT_UNRESOLVED_THRESHOLD)

    return CompletionResult(  # nosec: B106
        pass_name="grouping_analysis",
        is_complete=is_complete,
        completeness_score=completeness,
        reason=f"{unresolved} items without source_aliases" if not is_complete else None,
        unresolved_count=unresolved,
        total_count=total_non_literal,
    )


def check_window_completeness(
    result: WindowAnalysis,
) -> CompletionResult:
    """Check if window analysis is complete.

    Window analysis is fully deterministic.

    Args:
        result: WindowAnalysis output

    Returns:
        CompletionResult
    """
    return CompletionResult( #nosec: B106
        pass_name="window_analysis",
        is_complete=True,
        completeness_score=1.0,
    )


def check_output_completeness(
    result: OutputShapeAnalysis,
) -> CompletionResult:
    """Check if output analysis is complete.

    Output analysis is fully deterministic.

    Args:
        result: OutputShapeAnalysis output

    Returns:
        CompletionResult
    """
    return CompletionResult( #nosec: B106
        pass_name="output_shape_analysis",
        is_complete=True,
        completeness_score=1.0,
    )


def check_completeness(
    results: Dict[str, object],
    threshold: float = DEFAULT_UNRESOLVED_THRESHOLD,
) -> Dict[str, CompletionResult]:
    """Check completeness for all deterministic analysis results.

    Args:
        results: Dict of pass_name → result object
        threshold: Unresolved ratio threshold for fallback

    Returns:
        Dict of pass_name → CompletionResult
    """
    completeness: Dict[str, CompletionResult] = {}

    if "relation_analysis" in results and results["relation_analysis"]:
        completeness["relation_analysis"] = check_relation_completeness(
            results["relation_analysis"]
        )

    if "column_analysis" in results and results["column_analysis"]:
        completeness["column_analysis"] = check_column_completeness(
            results["column_analysis"], threshold
        )

    if "join_analysis" in results and results["join_analysis"]:
        completeness["join_analysis"] = check_join_completeness(
            results["join_analysis"]
        )

    if "filter_analysis" in results and results["filter_analysis"]:
        completeness["filter_analysis"] = check_filter_completeness(
            results["filter_analysis"], threshold
        )

    if "grouping_analysis" in results and results["grouping_analysis"]:
        completeness["grouping_analysis"] = check_grouping_completeness(
            results["grouping_analysis"]
        )

    if "window_analysis" in results and results["window_analysis"]:
        completeness["window_analysis"] = check_window_completeness(
            results["window_analysis"]
        )

    if "output_shape_analysis" in results and results["output_shape_analysis"]:
        completeness["output_shape_analysis"] = check_output_completeness(
            results["output_shape_analysis"]
        )

    return completeness


def needs_fallback(
    completeness_results: Dict[str, CompletionResult],
) -> List[str]:
    """Determine which passes need LLM fallback.

    Args:
        completeness_results: Results from check_completeness()

    Returns:
        List of pass names that need LLM fallback
    """
    fallback_passes: List[str] = []

    for pass_name, result in completeness_results.items():
        if not result.is_complete:
            fallback_passes.append(pass_name)
            logger.info(
                f"Pass {pass_name} needs LLM fallback: {result.reason} "
                f"(completeness: {result.completeness_score:.1%})"
            )

    return fallback_passes
