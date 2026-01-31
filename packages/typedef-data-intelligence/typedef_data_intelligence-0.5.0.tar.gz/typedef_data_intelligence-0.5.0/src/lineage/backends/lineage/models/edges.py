"""Pydantic models for all graph edge types with pair-based validation.

This module defines strongly-typed edge classes for all relationship types in the lineage graph.
Each edge class:
1. Encodes its edge_type as a ClassVar
2. Specifies allowed_pairs as tuples of (from_node_type, to_node_type)
3. Validates node pair compatibility at runtime
4. Defines edge-specific properties

ALL edges now use pair-based validation to prevent cartesian product issues.

Edges are organized by category:
- Logical dbt edges (dependencies, materialization)
- Physical edges (builds, has_column)
- Data lineage edges (derives_from)
- OpenLineage edges (reads, writes, executions, errors)
- Inferred semantic edges (LLM-derived metadata)
- Native semantic edges (warehouse-declared metadata)
- Profiling edges (table/column profiles)
- Clustering edges (join patterns)
"""

from datetime import datetime
from typing import ClassVar, Optional

from lineage.backends.lineage.models.base import GraphEdge
from lineage.backends.lineage.models.clustering import JoinCluster

# Import ALL node types for type validation
from lineage.backends.lineage.models.dbt import (
    DbtColumn,
    DbtMacro,
    DbtModel,
    DbtSource,
    DbtTest,
    DbtUnitTest,
)
from lineage.backends.lineage.models.openlineage import Dataset, Error, Job, Run
from lineage.backends.lineage.models.physical import (
    PhysicalColumn,
    PhysicalEphemeral,
    PhysicalIncrementalModel,
    PhysicalMaterializedView,
    PhysicalTable,
    PhysicalView,
)
from lineage.backends.lineage.models.profiling import ColumnProfile, TableProfile
from lineage.backends.lineage.models.semantic_analysis import (
    InferredAuditFinding,
    InferredAuditPatch,
    InferredDimension,
    InferredFact,
    InferredFilter,
    InferredGrainToken,
    InferredGroupingScope,
    InferredMeasure,
    InferredOutputShape,
    InferredRelation,
    InferredSegment,
    InferredSelectItem,
    InferredSemanticModel,
    InferredTimeScope,
    InferredWindowScope,
    TimeAttribute,
    TimeWindow,
    WindowFunction,
)
from lineage.backends.lineage.models.semantic_analysis import (
    JoinEdge as JoinEdgeNode,
)
from lineage.backends.lineage.models.semantic_views import (
    NativeBaseTable,
    NativeDimension,
    NativeFact,
    NativeMeasure,
    NativeSemanticModel,
)
from lineage.backends.types import Confidence, EdgeType

# ==============================================================================
# LOGICAL dbt EDGES
# ==============================================================================


class DependsOn(GraphEdge):
    """Model depends on another model or source.

    Represents dbt model-to-model or model-to-source dependencies in the DAG.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.DEPENDS_ON
    allowed_pairs: ClassVar = [
        (DbtModel, DbtModel),
        (DbtModel, DbtSource),
    ]

    type: str  # "model", "source", "seed"
    direct: bool  # Whether this is a direct dependency
    inferred: bool = False  # True if extracted from compiled_sql (implicit dependency)


class Materializes(GraphEdge):
    """Logical model/source owns logical columns.

    Represents the relationship between a logical dbt model/source and its
    logical column definitions. This is separate from physical materialization.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.MATERIALIZES
    allowed_pairs: ClassVar = [
        (DbtModel, DbtColumn),
        (DbtSource, DbtColumn),
    ]

    # No additional properties for logical ownership


# ==============================================================================
# PHYSICAL EDGES
# ==============================================================================


class Builds(GraphEdge):
    """Logical dbt entity builds physical warehouse relation.

    Links logical dbt models/sources to their physical warehouse materializations.
    One logical entity can build multiple physical relations (dev, staging, prod).
    """

    edge_type: ClassVar[EdgeType] = EdgeType.BUILDS
    allowed_pairs: ClassVar = [
        (DbtModel, PhysicalTable),
        (DbtModel, PhysicalView),
        (DbtModel, PhysicalMaterializedView),
        (DbtModel, PhysicalIncrementalModel),
        (DbtModel, PhysicalEphemeral),
        (DbtSource, PhysicalTable),
        (DbtSource, PhysicalView),
    ]

    environment: str  # "dev", "staging", "prod", etc.
    materialization_strategy: Optional[str] = None  # "full-refresh", "incremental", etc.
    deployed_at: Optional[datetime] = None  # When this materialization was created


class HasColumn(GraphEdge):
    """Physical relation has physical columns.

    Links physical warehouse tables/views to their actual columns.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_COLUMN
    allowed_pairs: ClassVar = [
        (PhysicalTable, PhysicalColumn),
        (PhysicalView, PhysicalColumn),
        (PhysicalMaterializedView, PhysicalColumn),
        (PhysicalIncrementalModel, PhysicalColumn),
    ]

    # No additional properties


# ==============================================================================
# DATA LINEAGE EDGES
# ==============================================================================


class DerivesFrom(GraphEdge):
    """Entity derives from source data (DATA LINEAGE).

    Consolidated edge for all data lineage relationships. Tracks how data
    flows from source columns to derived columns/measures/dimensions/facts.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.DERIVES_FROM
    allowed_pairs: ClassVar = [
        # Logical column lineage
        (DbtColumn, DbtColumn),

        # Physical column from logical column
        (PhysicalColumn, DbtColumn),

        # Inferred semantic components from logical columns
        (InferredMeasure, DbtColumn),
        (InferredDimension, DbtColumn),
        (InferredFact, DbtColumn),

        # Native semantic components from logical columns
        (NativeMeasure, DbtColumn),
        (NativeDimension, DbtColumn),
        (NativeFact, DbtColumn),
    ]

    confidence: Optional[Confidence] = None
    transformation: Optional[str] = None  # Description of transformation
    expr: Optional[str] = None  # Expression (e.g., "SUM(revenue)")


# ==============================================================================
# MACRO EDGES (dbt)
# ==============================================================================


class UsesMacro(GraphEdge):
    """Model (or other artifact) uses a macro.

    Initial use case: dbt models declare macro dependencies in manifest via
    depends_on.macros. This edge allows agents to trace macro changes to model
    behavior (especially in macro-heavy projects).
    """

    edge_type: ClassVar[EdgeType] = EdgeType.USES_MACRO
    allowed_pairs: ClassVar = [
        (DbtModel, DbtMacro),
    ]


class CallsMacro(GraphEdge):
    """Macro calls another macro."""

    edge_type: ClassVar[EdgeType] = EdgeType.CALLS_MACRO
    allowed_pairs: ClassVar = [
        (DbtMacro, DbtMacro),
    ]


# ==============================================================================
# dbt TEST EDGES
# ==============================================================================


class HasTest(GraphEdge):
    """Model or source has a data test.

    Links dbt models/sources to their data tests (generic or singular).
    Uses depends_on from manifest for reliable mapping.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_TEST
    allowed_pairs: ClassVar = [
        (DbtModel, DbtTest),
        (DbtSource, DbtTest),
    ]

    # No additional properties


class HasUnitTest(GraphEdge):
    """Model has a unit test.

    Links dbt models to their unit tests (dbt v1.8+).
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_UNIT_TEST
    allowed_pairs: ClassVar = [(DbtModel, DbtUnitTest)]

    # No additional properties


class TestsColumn(GraphEdge):
    """Test tests a specific column.

    Links column-scoped tests (unique, not_null, etc.) to the column being tested.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.TESTS_COLUMN
    allowed_pairs: ClassVar = [(DbtTest, DbtColumn)]

    # No additional properties


class TestReferences(GraphEdge):
    """Relationship test references another model/source.

    For relationship tests, tracks the "to" target model/source.
    E.g., test "relationships" with to: ref('customers') references customers model.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.TEST_REFERENCES
    allowed_pairs: ClassVar = [
        (DbtTest, DbtModel),
        (DbtTest, DbtSource),
    ]

    referenced_field: Optional[str] = None  # The field in the referenced model


# ==============================================================================
# OPENLINEAGE EDGES
# ==============================================================================


class Reads(GraphEdge):
    """Job reads dataset.

    Represents a job reading a dataset as input.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.READS
    allowed_pairs: ClassVar = [(Job, Dataset)]

    run_id: Optional[str] = None  # Optional run ID for run-specific reads


class Writes(GraphEdge):
    """Job writes dataset.

    Represents a job writing a dataset as output.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.WRITES
    allowed_pairs: ClassVar = [(Job, Dataset)]

    run_id: Optional[str] = None  # Optional run ID for run-specific writes


class InstanceOf(GraphEdge):
    """Run is instance of job.

    Links a run execution to its parent job.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.INSTANCE_OF
    allowed_pairs: ClassVar = [(Run, Job)]

    edge_id: str  # Unique edge identifier


class SameAs(GraphEdge):
    """Dataset refers to physical warehouse entity.

    Links OpenLineage datasets to physical warehouse relations.
    Replaces old SameAsModel/SameAsSource edges.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.SAME_AS
    allowed_pairs: ClassVar = [
        (Dataset, PhysicalTable),
        (Dataset, PhysicalView),
        (Dataset, PhysicalMaterializedView),
        (Dataset, PhysicalIncrementalModel),
    ]

    confidence: Confidence  # Confidence level in the match
    match_method: str  # "fqn_exact", "pattern_match", "manual"


class HasError(GraphEdge):
    """Run has error.

    Links a run to an error pattern that occurred during execution.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_ERROR
    allowed_pairs: ClassVar = [(Run, Error)]

    occurred_at: str  # ISO 8601 timestamp when error occurred


class Executes(GraphEdge):
    """Job executes logical dbt model.

    Links OpenLineage jobs to the logical dbt models they run.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.DEPENDS_ON  # Reuse DEPENDS_ON type
    allowed_pairs: ClassVar = [(Job, DbtModel)]

    # No additional properties


# ==============================================================================
# INFERRED SEMANTIC EDGES (LLM-derived)
# ==============================================================================


class HasInferredSemantics(GraphEdge):
    """Model has inferred semantic metadata.

    Links a dbt model to its LLM-inferred semantic analysis container.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_INFERRED_SEMANTICS
    allowed_pairs: ClassVar = [(DbtModel, InferredSemanticModel)]

    # No additional properties


class HasMeasure(GraphEdge):
    """Semantic model has measure.

    Links semantic models (inferred or native) to their measure definitions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_MEASURE
    allowed_pairs: ClassVar = [
        (InferredSemanticModel, InferredMeasure),
        (NativeSemanticModel, NativeMeasure),
    ]

    output_alias: Optional[str] = None  # Alias in SELECT clause


class HasDimension(GraphEdge):
    """Semantic model has dimension.

    Links semantic models (inferred or native) to their dimension definitions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_DIMENSION
    allowed_pairs: ClassVar = [
        (InferredSemanticModel, InferredDimension),
        (NativeSemanticModel, NativeDimension),
    ]

    output_alias: Optional[str] = None  # Alias in SELECT clause


class HasFact(GraphEdge):
    """Semantic model has fact.

    Links semantic models (inferred or native) to their fact definitions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_FACT
    allowed_pairs: ClassVar = [
        (InferredSemanticModel, InferredFact),
        (NativeSemanticModel, NativeFact),
    ]

    # No additional properties


class HasSegment(GraphEdge):
    """Inferred semantic model has segment.

    Links inferred semantic models to business segment definitions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_SEGMENT
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredSegment)]

    # No additional properties


class HasTimeWindow(GraphEdge):
    """Inferred semantic model has time window.

    Links inferred semantic models to time window filters.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_TIME_WINDOW
    allowed_pairs: ClassVar = [(InferredSemanticModel, TimeWindow)]

    # No additional properties


class HasTimeAttribute(GraphEdge):
    """Inferred semantic model has time attribute.

    Links inferred semantic models to time-based filter attributes.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_TIME_ATTRIBUTE
    allowed_pairs: ClassVar = [(InferredSemanticModel, TimeAttribute)]

    # No additional properties


class HasJoinEdge(GraphEdge):
    """Inferred semantic model has join edge.

    Links inferred semantic models to join relationship nodes.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_JOIN_EDGE
    allowed_pairs: ClassVar = [(InferredSemanticModel, JoinEdgeNode)]

    # No additional properties


class HasWindowFunction(GraphEdge):
    """Inferred semantic model has window function.

    Links inferred semantic models to window/analytic functions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_WINDOW_FUNCTION
    allowed_pairs: ClassVar = [(InferredSemanticModel, WindowFunction)]

    # No additional properties


class HasRelation(GraphEdge):
    """Inferred semantic model has relation use.

    Links inferred semantic models to relation occurrences (tables/views/CTEs).
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_RELATION
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredRelation)]

    # No additional properties


class ResolvesToModel(GraphEdge):
    """Inferred relation resolves to dbt model.

    Links relation aliases to actual DbtModel nodes when resolvable.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.RESOLVES_TO_MODEL
    allowed_pairs: ClassVar = [(InferredRelation, DbtModel), (InferredRelation, DbtSource)]

    confidence: Optional[str] = None  # high, medium, low


class HasFilter(GraphEdge):
    """Inferred semantic model has filter predicate.

    Links inferred semantic models to filter predicates (WHERE/HAVING/QUALIFY).
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_FILTER
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredFilter)]

    # No additional properties


class FiltersRelation(GraphEdge):
    """Filter applies to relation.

    Links filter predicates to the relation they filter.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.FILTERS_RELATION
    allowed_pairs: ClassVar = [(InferredFilter, InferredRelation)]

    # No additional properties


class HasGroupingScope(GraphEdge):
    """Inferred semantic model has grouping scope.

    Links inferred semantic models to per-scope grouping analysis.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_GROUPING_SCOPE
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredGroupingScope)]

    # No additional properties


class HasSelectItem(GraphEdge):
    """Grouping scope has select item.

    Links grouping scopes to SELECT items.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_SELECT_ITEM
    allowed_pairs: ClassVar = [(InferredGroupingScope, InferredSelectItem)]

    # No additional properties


class HasTimeScope(GraphEdge):
    """Inferred semantic model has time scope.

    Links inferred semantic models to per-scope time analysis.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_TIME_SCOPE
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredTimeScope)]

    # No additional properties


class HasWindowScope(GraphEdge):
    """Inferred semantic model has window scope.

    Links inferred semantic models to per-scope window function analysis.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_WINDOW_SCOPE
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredWindowScope)]

    # No additional properties


class HasOutputShape(GraphEdge):
    """Inferred semantic model has output shape.

    Links inferred semantic models to per-scope output shape analysis.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_OUTPUT_SHAPE
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredOutputShape)]

    # No additional properties


class HasAuditFinding(GraphEdge):
    """Inferred semantic model has audit finding.

    Links inferred semantic models to audit findings from validation.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_AUDIT_FINDING
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredAuditFinding)]

    # No additional properties


class HasAuditPatch(GraphEdge):
    """Inferred semantic model has audit patch.

    Links inferred semantic models to suggested patches from audit.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_AUDIT_PATCH
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredAuditPatch)]

    # No additional properties


class HasGrainToken(GraphEdge):
    """Inferred semantic model has grain token.

    Links inferred semantic models to grain tokens from humanization.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_GRAIN_TOKEN
    allowed_pairs: ClassVar = [(InferredSemanticModel, InferredGrainToken)]

    # No additional properties


class InferredJoinsWith(GraphEdge):
    """Model joins with another via inferred join edge.

    Links dbt models to JoinEdge nodes when aliases are resolved.
    This is bidirectional - both models link to the same JoinEdge.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.INFERRED_JOINS_WITH
    allowed_pairs: ClassVar = [(DbtModel, JoinEdgeNode), (DbtSource, JoinEdgeNode)]

    confidence: Optional[str] = None  # high, medium, low


class JoinsLeftModel(GraphEdge):
    """Join edge joins with left model.

    Direct link from JoinEdge to resolved left DbtModel.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.JOINS_LEFT_MODEL
    allowed_pairs: ClassVar = [(JoinEdgeNode, DbtModel), (JoinEdgeNode, DbtSource)]

    # No additional properties


class JoinsRightModel(GraphEdge):
    """Join edge joins with right model.

    Direct link from JoinEdge to resolved right DbtModel.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.JOINS_RIGHT_MODEL
    allowed_pairs: ClassVar = [(JoinEdgeNode, DbtModel), (JoinEdgeNode, DbtSource)]

    # No additional properties


# ==============================================================================
# NATIVE SEMANTIC EDGES (warehouse-declared)
# ==============================================================================


class DrawsFrom(GraphEdge):
    """Native semantic model draws from dbt model.

    Links warehouse-native semantic models to the dbt models they reference.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.DRAWS_FROM
    allowed_pairs: ClassVar = [(NativeSemanticModel, DbtModel)]

    # No additional properties


class HasSemanticTable(GraphEdge):
    """Native semantic model has base table.

    Links native semantic models to their base table definitions.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_SEMANTIC_TABLE
    allowed_pairs: ClassVar = [(NativeSemanticModel, NativeBaseTable)]

    # No additional properties


# ==============================================================================
# PROFILING EDGES
# ==============================================================================


class HasProfile(GraphEdge):
    """Physical entity has profile.

    Links physical relations/columns to their statistical profiles.
    Uses pair validation to prevent invalid combinations.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_PROFILE
    allowed_pairs: ClassVar = [
        # Physical relations have table profiles
        (PhysicalTable, TableProfile),
        (PhysicalView, TableProfile),
        (PhysicalMaterializedView, TableProfile),
        (PhysicalIncrementalModel, TableProfile),

        # Physical columns have column profiles
        (PhysicalColumn, ColumnProfile),
    ]

    # No additional properties


class HasColumnProfile(GraphEdge):
    """Table profile has column profile.

    Links table profiles to their component column profiles.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.HAS_COLUMN_PROFILE
    allowed_pairs: ClassVar = [(TableProfile, ColumnProfile)]

    # No additional properties


# ==============================================================================
# JOIN CLUSTERING EDGES
# ==============================================================================


class JoinsWith(GraphEdge):
    """Model joins with another via join edge.

    Links dbt models to JoinEdge nodes representing joins in their SQL.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.JOINS_WITH
    allowed_pairs: ClassVar = [(DbtModel, JoinEdgeNode)]

    # No additional properties


class InJoinCluster(GraphEdge):
    """Model is in join cluster.

    Links dbt models to join clusters based on join patterns.
    """

    edge_type: ClassVar[EdgeType] = EdgeType.IN_JOIN_CLUSTER
    allowed_pairs: ClassVar = [(DbtModel, JoinCluster)]

    # No additional properties


# ==============================================================================
# EXPORTS
# ==============================================================================

__all__ = [
    # Logical dbt edges
    "DependsOn",
    "Materializes",

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
    # New formalized semantic edges
    "HasRelation",
    "ResolvesToModel",
    "HasFilter",
    "FiltersRelation",
    "HasGroupingScope",
    "HasSelectItem",
    "HasTimeScope",
    "HasWindowScope",
    "HasOutputShape",
    "HasAuditFinding",
    "HasAuditPatch",
    "HasGrainToken",
    "InferredJoinsWith",
    "JoinsLeftModel",
    "JoinsRightModel",

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
