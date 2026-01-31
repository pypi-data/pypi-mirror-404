"""Pydantic data models for lineage system.

This package contains the canonical Pydantic models that serve as both:
1. Data transfer objects (validation, serialization)
2. Graph schema definitions (structure, relationships)

Models replace manual dict construction and provide:
- Type safety with Pydantic validation
- Computed IDs (auto-generated from component fields)
- Self-documenting structure
- IDE autocomplete support

## Base Classes
- BaseNode: Base class for all graph nodes with computed IDs
- GraphEdge: Base class for all edges with pair-based validation

## Node Models (by category)
- dbt (logical): DbtModel, DbtSource, DbtColumn
- physical: PhysicalRelation, PhysicalTable, PhysicalView, PhysicalColumn, etc.
- OpenLineage: Job, Dataset, Run, Error
- Inferred Semantic: InferredSemanticModel, InferredMeasure, InferredDimension, InferredFact, etc.
- Native Semantic: NativeSemanticModel, NativeMeasure, NativeDimension, NativeFact, etc.
- Profiling: TableProfile, ColumnProfile
- Clustering: JoinCluster
- Tickets: DataRequestTicket

## Edge Models (by category)
- dbt: DependsOn, Materializes, DerivesFrom
- physical: Builds, HasColumn
- OpenLineage: Reads, Writes, InstanceOf, SameAs, HasError, Executes
- Inferred Semantic: HasInferredSemantics, HasMeasure, HasDimension, HasFact, etc.
- Native Semantic: DrawsFrom, HasSemanticTable
- Profiling: HasProfile, HasColumnProfile
- Clustering: JoinsWith, InJoinCluster
"""
# ruff: noqa: I001
from __future__ import annotations

# Base classes
from lineage.backends.lineage.models.base import BaseNode, GraphEdge, NodeIdentifier

# Clustering nodes
from lineage.backends.lineage.models.clustering import JoinCluster

# dbt nodes (logical)
from lineage.backends.lineage.models.dbt import (
    DbtColumn,
    DbtMacro,
    DbtModel,
    DbtSource,
    DbtTest,
    DbtUnitTest,
)

# All edge types
from lineage.backends.lineage.models.edges import (
    # Physical edges
    Builds,
    # Logical dbt edges
    DependsOn,
    # Data lineage
    DerivesFrom,
    # Native semantic edges
    DrawsFrom,
    Executes,
    HasColumn,
    HasColumnProfile,
    HasDimension,
    HasError,
    HasFact,
    # Inferred semantic edges
    HasInferredSemantics,
    HasJoinEdge,
    HasMeasure,
    # Profiling edges
    HasProfile,
    HasSegment,
    HasSemanticTable,
    # dbt test edges
    HasTest,
    HasUnitTest,
    HasTimeAttribute,
    HasTimeWindow,
    HasWindowFunction,
    InJoinCluster,
    InstanceOf,
    # Clustering edges
    JoinsWith,
    CallsMacro,
    Materializes,
    # OpenLineage edges
    Reads,
    SameAs,
    # Test edges
    TestReferences,
    TestsColumn,
    UsesMacro,
    Writes,
)

# OpenLineage nodes
from lineage.backends.lineage.models.openlineage import Dataset, Error, Job, Run

# Physical nodes
from lineage.backends.lineage.models.physical import (
    PhysicalColumn,
    PhysicalEphemeral,
    PhysicalIncrementalModel,
    PhysicalMaterializedView,
    PhysicalRelation,
    PhysicalTable,
    PhysicalView,
)

# Profiling nodes
from lineage.backends.lineage.models.profiling import ColumnProfile, TableProfile

# Inferred semantic nodes (LLM-derived)
from lineage.backends.lineage.models.semantic_analysis import (
    InferredDimension,
    InferredFact,
    InferredMeasure,
    InferredSegment,
    InferredSemanticModel,
    TimeAttribute,
    TimeWindow,
    WindowFunction,
)
from lineage.backends.lineage.models.semantic_analysis import (
    JoinEdge as JoinEdgeNode,
)

# Native semantic nodes (warehouse-declared)
from lineage.backends.lineage.models.semantic_views import (
    NativeBaseTable,
    NativeDimension,
    NativeFact,
    NativeMeasure,
    NativeSemanticModel,
    NativeSemanticModelData,
    NativeSemanticModelOverview,
)

# Ticket nodes
from lineage.backends.lineage.models.tickets import DataRequestTicket

__all__ = [
    # Base classes
    "NodeIdentifier",
    "BaseNode",
    "GraphEdge",
    # dbt nodes (logical)
    "DbtModel",
    "DbtSource",
    "DbtColumn",
    "DbtMacro",
    "DbtTest",
    "DbtUnitTest",
    # Physical nodes
    "PhysicalRelation",
    "PhysicalTable",
    "PhysicalView",
    "PhysicalMaterializedView",
    "PhysicalIncrementalModel",
    "PhysicalEphemeral",
    "PhysicalColumn",
    # OpenLineage nodes
    "Job",
    "Dataset",
    "Run",
    "Error",
    # Inferred semantic nodes
    "InferredSemanticModel",
    "InferredMeasure",
    "InferredDimension",
    "InferredFact",
    "InferredSegment",
    "TimeWindow",
    "TimeAttribute",
    "JoinEdgeNode",
    "WindowFunction",
    # Native semantic nodes
    "NativeSemanticModel",
    "NativeMeasure",
    "NativeDimension",
    "NativeFact",
    "NativeBaseTable",
    "NativeSemanticModelData",
    "NativeSemanticModelOverview",
    # Profiling nodes
    "TableProfile",
    "ColumnProfile",
    # Clustering nodes
    "JoinCluster",
    # Ticket nodes
    "DataRequestTicket",
    # Logical dbt edges
    "DependsOn",
    "Materializes",
    "UsesMacro",
    "CallsMacro",
    # dbt test edges
    "HasTest",
    "HasUnitTest",
    "TestsColumn",
    "TestReferences",
    # Physical edges
    "Builds",
    "HasColumn",
    # Data lineage
    "DerivesFrom",
    # OpenLineage edges
    "Reads",
    "Writes",
    "InstanceOf",
    "SameAs",
    "HasError",
    "Executes",
    # Inferred semantic edges
    "HasInferredSemantics",
    "HasMeasure",
    "HasDimension",
    "HasFact",
    "HasSegment",
    "HasTimeWindow",
    "HasTimeAttribute",
    "HasJoinEdge",
    "HasWindowFunction",
    # Native semantic edges
    "DrawsFrom",
    "HasSemanticTable",
    # Profiling edges
    "HasProfile",
    "HasColumnProfile",
    # Clustering edges
    "JoinsWith",
    "InJoinCluster",
]
