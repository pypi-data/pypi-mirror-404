"""Semantic SQL analysis models - migrated from de-agentic-demo/sql_analyzer."""

# Base models
# Analytical models (Passes 5-8)
from .analytical import (
    GroupingAnalysis,
    NormalizedTimeScope,
    # Pass 8: Output Shape Analysis
    OrderByItem,
    OutputShapeAnalysis,
    # Pass 5: Grouping Analysis
    SelectItem,
    SetOperation,
    TimeAnalysis,
    # Pass 6: Time Analysis
    TimeScope,
    WindowAnalysis,
    # Pass 7: Window Analysis
    WindowSpec,
)
from .base import Evidence, Ptr

# Business models (Passes 10-10a)
from .business import (
    BusinessDimension,
    BusinessFact,
    # Pass 10: Business Semantics
    BusinessMeasure,
    BusinessSemantics,
    BusinessTimeWindow,
    GrainHumanization,
    # Pass 10a: Grain Humanization
    GrainToken,
    SegmentRule,
)

# Technical models (Passes 1-4)
from .technical import (
    AliasMapping,
    ColumnAnalysis,
    # Pass 2: Column Analysis
    ColumnRef,
    ColumnsByAlias,
    # Pass 4: Filter Analysis
    FilterAnalysis,
    # Pass 3: Join Edge Analysis
    JoinClause,
    JoinEdgeAnalysis,
    RelationAnalysis,
    # Pass 1: Relation Analysis
    RelationUse,
    SelfJoinGroup,
)

# Validation models (Pass 9)
from .validation import (
    AuditAnalysis,
    AuditFinding,
    FindingContext,
    PatchOp,
    PatchValue,
)

__all__ = [
    # Base
    "Evidence",
    "Ptr",
    # Technical
    "RelationUse",
    "AliasMapping",
    "SelfJoinGroup",
    "RelationAnalysis",
    "ColumnRef",
    "ColumnsByAlias",
    "ColumnAnalysis",
    "JoinClause",
    "JoinEdgeAnalysis",
    "FilterAnalysis",
    # Analytical
    "SelectItem",
    "GroupingAnalysis",
    "TimeScope",
    "NormalizedTimeScope",
    "TimeAnalysis",
    "WindowSpec",
    "WindowAnalysis",
    "OrderByItem",
    "SetOperation",
    "OutputShapeAnalysis",
    # Validation
    "FindingContext",
    "AuditFinding",
    "PatchValue",
    "PatchOp",
    "AuditAnalysis",
    # Business
    "BusinessMeasure",
    "BusinessDimension",
    "BusinessFact",
    "SegmentRule",
    "BusinessTimeWindow",
    "BusinessSemantics",
    "GrainToken",
    "GrainHumanization",
]
