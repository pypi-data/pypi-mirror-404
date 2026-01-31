"""Type definitions for storage backends.

This module defines enums for backend types to ensure type safety
and prevent typos when referring to backends throughout the codebase.
"""

from enum import Enum


class LineageStorageType(str, Enum):
    """Lineage storage backend types.

    This enum defines all supported lineage storage backends.
    Inherits from str to allow direct string comparisons and JSON serialization.

    Usage:
        from lineage.storage.types import LineageStorageType

        # Create storage with enum
        storage = create_storage(backend=LineageStorageType.KUZU)

        # In config files, use the enum value (lowercase string)
        # backend: kuzu
    """

    KUZU = "kuzu"
    """KùzuDB - Embedded graph database (recommended for local dev)"""

    FALKORDB = "falkordb"
    """FalkorDB - Redis-based graph database (recommended for production)"""

    FALKORDB_LITE = "falkordblite"
    """FalkorDBLite - Embedded file-backed graph database (not compatible with Apple Silicon)"""

    @classmethod
    def from_string(cls, value: str) -> "LineageStorageType":
        """Convert string to LineageStorageType, with helpful error message.

        Args:
            value: Backend type string (e.g., "neo4j", "kuzu")

        Returns:
            LineageStorageType enum value

        Raises:
            ValueError: If backend type is unknown

        Example:
            backend = LineageStorageType.from_string("neo4j")
            # Returns: LineageStorageType.NEO4J
        """
        try:
            return cls(value)
        except ValueError as e:
            valid = ", ".join([b.value for b in cls])
            raise ValueError(
                f"Unknown lineage storage type: '{value}'. "
                f"Valid types: {valid}"
            ) from e

    @classmethod
    def list_values(cls) -> list[str]:
        """Get list of all lineage storage type values.

        Returns:
            List of backend type strings

        Example:
            >>> LineageStorageType.list_values()
            ['kuzu', 'postgres-age', 'neo4j', 'arcadedb']
        """
        return [b.value for b in cls]


class DataBackendType(str, Enum):
    """Data query backend types.

    This enum defines all supported data warehouse/database backends
    for querying actual data (not lineage metadata).

    Usage:
        from lineage.storage.types import DataBackendType

        # Create data backend with enum
        backend = DuckDBBackend(db_path=path)
    """

    DUCKDB = "duckdb"
    """DuckDB - Embedded analytical database"""

    SNOWFLAKE = "snowflake"
    """Snowflake - Cloud data warehouse (future)"""

    BIGQUERY = "bigquery"
    """Google BigQuery - Cloud data warehouse (future)"""

    REDSHIFT = "redshift"
    """AWS Redshift - Cloud data warehouse (future)"""

    POSTGRES = "postgres"
    """PostgreSQL - Traditional database (future)"""

    @classmethod
    def from_string(cls, value: str) -> "DataBackendType":
        """Convert string to DataBackendType, with helpful error message.

        Args:
            value: Data backend type string (e.g., "duckdb")

        Returns:
            DataBackendType enum value

        Raises:
            ValueError: If backend type is unknown
        """
        try:
            return cls(value)
        except ValueError as e:
            valid = ", ".join([b.value for b in cls])
            raise ValueError(
                f"Unknown data backend type: '{value}'. "
                f"Valid types: {valid}"
            ) from e

    @classmethod
    def list_values(cls) -> list[str]:
        """Get list of all data backend type values.

        Returns:
            List of data backend type strings
        """
        return [b.value for b in cls]


class NodeLabel(str, Enum):
    """Node labels for the lineage graph.

    These labels correspond to node types in the graph database.
    Using enums ensures type safety and provides IDE autocomplete.

    Note: dbt node labels have been renamed for clarity:
    - DBT_MODEL (was MODEL) - value: "DbtModel"
    - DBT_SOURCE (was SOURCE) - value: "DbtSource"
    - DBT_COLUMN (was COLUMN) - value: "DbtColumn"
    """

    # dbt nodes - RENAMED for explicit dbt context (LOGICAL)
    DBT_MODEL = "DbtModel"
    DBT_SOURCE = "DbtSource"
    DBT_COLUMN = "DbtColumn"
    DBT_MACRO = "DbtMacro"
    DBT_TEST = "DbtTest"
    DBT_UNIT_TEST = "DbtUnitTest"

    # Physical warehouse nodes (PHYSICAL)
    PHYSICAL_RELATION = "PhysicalRelation"  # Base class
    PHYSICAL_TABLE = "PhysicalTable"
    PHYSICAL_VIEW = "PhysicalView"
    PHYSICAL_MATERIALIZED_VIEW = "PhysicalMaterializedView"
    PHYSICAL_INCREMENTAL_MODEL = "PhysicalIncrementalModel"
    PHYSICAL_EPHEMERAL = "PhysicalEphemeral"
    PHYSICAL_COLUMN = "PhysicalColumn"

    # OpenLineage nodes
    JOB = "Job"
    RUN = "Run"
    DATASET = "Dataset"
    ERROR = "Error"

    # Inferred semantic nodes (LLM-derived)
    INFERRED_SEMANTIC_MODEL = "InferredSemanticModel"
    INFERRED_MEASURE = "InferredMeasure"
    INFERRED_DIMENSION = "InferredDimension"
    INFERRED_FACT = "InferredFact"
    INFERRED_SEGMENT = "InferredSegment"
    TIME_WINDOW = "TimeWindow"
    TIME_ATTRIBUTE = "TimeAttribute"
    JOIN_EDGE = "JoinEdge"
    WINDOW_FUNCTION = "WindowFunction"
    # New formalized semantic nodes
    INFERRED_RELATION = "InferredRelation"
    INFERRED_FILTER = "InferredFilter"
    INFERRED_GROUPING_SCOPE = "InferredGroupingScope"
    INFERRED_SELECT_ITEM = "InferredSelectItem"
    INFERRED_TIME_SCOPE = "InferredTimeScope"
    INFERRED_WINDOW_SCOPE = "InferredWindowScope"
    INFERRED_OUTPUT_SHAPE = "InferredOutputShape"
    INFERRED_AUDIT_FINDING = "InferredAuditFinding"
    INFERRED_AUDIT_PATCH = "InferredAuditPatch"
    INFERRED_GRAIN_TOKEN = "InferredGrainToken" #nosec: B105 -- not a password

    # Clustering nodes
    JOIN_CLUSTER = "JoinCluster"

    # Profiling nodes
    TABLE_PROFILE = "TableProfile"
    COLUMN_PROFILE = "ColumnProfile"

    # Native semantic nodes (warehouse-declared)
    NATIVE_SEMANTIC_MODEL = "NativeSemanticModel"
    NATIVE_MEASURE = "NativeMeasure"
    NATIVE_DIMENSION = "NativeDimension"
    NATIVE_FACT = "NativeFact"
    NATIVE_BASE_TABLE = "NativeBaseTable"

    # Other nodes
    DATA_REQUEST_TICKET = "DataRequestTicket"


class Confidence(str, Enum):
    """Confidence levels for lineage relationships.

    Used in edges like DERIVES_FROM to indicate certainty of the relationship.
    """

    DIRECT = "direct"
    """Direct, verified relationship (e.g., PhysicalColumn -> DbtColumn)"""

    HIGH = "high"
    """High confidence (e.g., sqlglot-parsed column lineage with clear path)"""

    MEDIUM = "medium"
    """Medium confidence (e.g., inferred from patterns, partial information)"""

    LOW = "low"
    """Low confidence (e.g., heuristic-based, ambiguous source)"""


class EdgeType(str, Enum):
    """Edge types for the lineage graph.

    These edge types define relationships between nodes.
    Using enums ensures type safety and prevents typos in edge names.
    """

    # dbt relationships (logical)
    DEPENDS_ON = "DEPENDS_ON"
    MATERIALIZES = "MATERIALIZES"  # Logical model → logical columns
    DERIVES_FROM = "DERIVES_FROM"  # Data lineage (consolidated)
    USES_MACRO = "USES_MACRO"  # Model/Test/Macro uses a macro
    CALLS_MACRO = "CALLS_MACRO"  # Macro calls another macro

    # dbt test relationships
    HAS_TEST = "HAS_TEST"  # Model/Source → DbtTest
    HAS_UNIT_TEST = "HAS_UNIT_TEST"  # Model → DbtUnitTest
    TESTS_COLUMN = "TESTS_COLUMN"  # DbtTest → DbtColumn
    TEST_REFERENCES = "TEST_REFERENCES"  # DbtTest → Model/Source (relationship test target)

    # Physical relationships
    BUILDS = "BUILDS"  # Logical model → physical relation
    HAS_COLUMN = "HAS_COLUMN"  # Physical relation → physical columns

    # OpenLineage relationships
    READS = "READS"
    WRITES = "WRITES"
    INSTANCE_OF = "INSTANCE_OF"
    HAS_ERROR = "HAS_ERROR"
    SAME_AS = "SAME_AS"  # Dataset → PhysicalRelation

    # Semantic analysis relationships
    HAS_INFERRED_SEMANTICS = "HAS_INFERRED_SEMANTICS"  # Model → InferredSemanticModel
    HAS_MEASURE = "HAS_MEASURE"
    HAS_DIMENSION = "HAS_DIMENSION"
    HAS_SEGMENT = "HAS_SEGMENT"
    HAS_FACT = "HAS_FACT"
    HAS_TIME_WINDOW = "HAS_TIME_WINDOW"
    HAS_TIME_ATTRIBUTE = "HAS_TIME_ATTRIBUTE"
    HAS_JOIN_EDGE = "HAS_JOIN_EDGE"
    HAS_WINDOW_FUNCTION = "HAS_WINDOW_FUNCTION"
    # New formalized semantic relationships
    HAS_RELATION = "HAS_RELATION"  # InferredSemanticModel → InferredRelation
    RESOLVES_TO_MODEL = "RESOLVES_TO_MODEL"  # InferredRelation → DbtModel
    HAS_FILTER = "HAS_FILTER"  # InferredSemanticModel → InferredFilter
    FILTERS_RELATION = "FILTERS_RELATION"  # InferredFilter → InferredRelation
    HAS_GROUPING_SCOPE = "HAS_GROUPING_SCOPE"  # InferredSemanticModel → InferredGroupingScope
    HAS_SELECT_ITEM = "HAS_SELECT_ITEM"  # InferredGroupingScope → InferredSelectItem
    HAS_TIME_SCOPE = "HAS_TIME_SCOPE"  # InferredSemanticModel → InferredTimeScope
    HAS_WINDOW_SCOPE = "HAS_WINDOW_SCOPE"  # InferredSemanticModel → InferredWindowScope
    HAS_OUTPUT_SHAPE = "HAS_OUTPUT_SHAPE"  # InferredSemanticModel → InferredOutputShape
    HAS_AUDIT_FINDING = "HAS_AUDIT_FINDING"  # InferredSemanticModel → InferredAuditFinding
    HAS_AUDIT_PATCH = "HAS_AUDIT_PATCH"  # InferredSemanticModel → InferredAuditPatch
    HAS_GRAIN_TOKEN = "HAS_GRAIN_TOKEN"  # InferredSemanticModel → InferredGrainToken #nosec: B105 -- not a password

    # Join clustering relationships
    JOINS_WITH = "JOINS_WITH"
    INFERRED_JOINS_WITH = "INFERRED_JOINS_WITH"  # DbtModel → JoinEdge (bidirectional)
    JOINS_LEFT_MODEL = "JOINS_LEFT_MODEL"  # JoinEdge → DbtModel
    JOINS_RIGHT_MODEL = "JOINS_RIGHT_MODEL"  # JoinEdge → DbtModel
    IN_JOIN_CLUSTER = "IN_JOIN_CLUSTER"

    # Profiling relationships
    HAS_PROFILE = "HAS_PROFILE"
    HAS_COLUMN_PROFILE = "HAS_COLUMN_PROFILE"
    PROFILES_COLUMN = "PROFILES_COLUMN"

    # Semantic views
    DRAWS_FROM = "DRAWS_FROM"
    HAS_SEMANTIC_MEASURE = "HAS_SEMANTIC_MEASURE"
    HAS_SEMANTIC_DIMENSION = "HAS_SEMANTIC_DIMENSION"
    HAS_SEMANTIC_FACT = "HAS_SEMANTIC_FACT"
    HAS_SEMANTIC_TABLE = "HAS_SEMANTIC_TABLE"

__all__ = ["LineageStorageType", "DataBackendType", "NodeLabel", "EdgeType", "Confidence"]
