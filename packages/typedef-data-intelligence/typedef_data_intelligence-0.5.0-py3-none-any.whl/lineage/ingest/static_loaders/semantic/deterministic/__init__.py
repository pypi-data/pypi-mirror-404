"""Deterministic + Targeted LLM SQL analysis.

This module provides a hybrid approach to semantic analysis:
1. Deterministic extraction using SQLGlot AST (FREE, instant)
2. Targeted LLM classification using Haiku (CHEAP, parallelizable)
3. Full LLM fallback only on parse failure

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                    Hybrid Analysis Flow                      │
├─────────────────────────────────────────────────────────────┤
│  SQL Query                                                   │
│      │                                                       │
│      ▼                                                       │
│  ┌─────────────────────────────────────┐                    │
│  │    Deterministic Passes (SQLGlot)   │ ◀── FREE, instant  │
│  │    - Relations, Columns, Joins      │                    │
│  │    - Filters, Grouping              │                    │
│  │    - Windows, Output                │                    │
│  └─────────────────────────────────────┘                    │
│      │                                                       │
│      ▼                                                       │
│  ┌─────────────────────────────────────┐                    │
│  │   Targeted LLM Classification       │ ◀── Cheap, parallel│
│  │   - Time columns                    │     (Haiku)        │
│  │   - Fact/Dimension/Measure roles    │                    │
│  │   - PII detection                   │                    │
│  └─────────────────────────────────────┘                    │
│      │                                                       │
│      ▼                                                       │
│  BusinessSemantics                                           │
└─────────────────────────────────────────────────────────────┘

Fallback Triggers:
- Parse failure: SQLGlot cannot parse the SQL dialect → full LLM
- Completeness threshold: >10% unresolved columns → full LLM for that pass
"""

from lineage.ingest.static_loaders.semantic.deterministic.columns import (
    analyze_columns,
)
from lineage.ingest.static_loaders.semantic.deterministic.completeness import (
    CompletionResult,
    check_completeness,
)
from lineage.ingest.static_loaders.semantic.deterministic.executor import (
    DeterministicExecutor,
    DeterministicResult,
)
from lineage.ingest.static_loaders.semantic.deterministic.filters import (
    analyze_filters,
)
from lineage.ingest.static_loaders.semantic.deterministic.grouping import (
    analyze_grouping,
)
from lineage.ingest.static_loaders.semantic.deterministic.joins import (
    analyze_joins,
)
from lineage.ingest.static_loaders.semantic.deterministic.null_killing import (
    detect_null_killing,
)
from lineage.ingest.static_loaders.semantic.deterministic.output import (
    analyze_output,
)
from lineage.ingest.static_loaders.semantic.deterministic.relations import (
    analyze_relations,
)
from lineage.ingest.static_loaders.semantic.deterministic.windows import (
    analyze_windows,
)

__all__ = [
    # Pass analysis functions
    "analyze_relations",
    "analyze_columns",
    "analyze_joins",
    "detect_null_killing",
    "analyze_filters",
    "analyze_grouping",
    "analyze_windows",
    "analyze_output",
    # Completeness checking
    "check_completeness",
    "CompletionResult",
    # Executor
    "DeterministicExecutor",
    "DeterministicResult",
]
