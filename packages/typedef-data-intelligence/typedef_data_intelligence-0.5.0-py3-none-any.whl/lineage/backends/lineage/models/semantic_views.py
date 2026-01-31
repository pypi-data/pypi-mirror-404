"""Pydantic models for native semantic models (warehouse-declared).

This module defines models for semantic layers declared natively in warehouses:
- NativeSemanticModel: Warehouse-native semantic layer (Snowflake, etc.)
- NativeMeasure: Warehouse-declared measure
- NativeDimension: Warehouse-declared dimension
- NativeFact: Warehouse-declared fact
- NativeBaseTable: Base table referenced by semantic model

These are NATIVE/DECLARED in the warehouse, separate from INFERRED semantic
metadata extracted by LLM analysis (see semantic_analysis.py).

Key features:
- Computed IDs via @computed_field (auto-generated from component fields)
- Nested validation (measures, dimensions, facts validated recursively)
- Type safety with Pydantic validation
- Self-documenting with field descriptions
"""
from __future__ import annotations

from typing import ClassVar, List, Optional

from pydantic import BaseModel, Field, computed_field

from lineage.backends.lineage.models.base import BaseNode
from lineage.backends.types import NodeLabel


class NativeMeasure(BaseNode):
    """Warehouse-declared metric/measure from a semantic model.

    Measures are aggregated values (SUM, COUNT, AVG, etc.) that represent
    quantitative business metrics in a native semantic model.

    Examples:
        - total_revenue (SUM of revenue)
        - customer_count (COUNT DISTINCT of customer_id)
        - avg_deal_size (AVG of deal_amount)
    """
    node_label: ClassVar[NodeLabel] = NodeLabel.NATIVE_MEASURE

    # Measure-specific fields
    semantic_table_name: str
    expression: str  # SQL expression for the measure
    aggregation: str  # SUM, COUNT, AVG, MAX, MIN, etc.
    data_type: Optional[str] = None
    description: Optional[str] = None
    format: Optional[str] = None  # e.g., "currency", "percentage"
    synonyms: Optional[List[str]] = Field(default_factory=list)

    # Parent context for ID generation (required)
    model_id: str  # Parent NativeSemanticModel ID

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: `{model_id}.measure.{name}`."""
        return f"{self.model_id}.measure.{self.name}"


class NativeDimension(BaseNode):
    """Warehouse-declared dimension/attribute from a semantic model.

    Dimensions are non-aggregated attributes used for grouping, filtering,
    and slicing data in analytics queries.

    Examples:
        - customer_name
        - product_category
        - transaction_date (time dimension)
    """
    node_label: ClassVar[NodeLabel] = NodeLabel.NATIVE_DIMENSION

    # Dimension-specific fields
    semantic_table_name: str
    expression: Optional[str] = None  # SQL expression (if derived)
    data_type: Optional[str] = None
    description: Optional[str] = None
    is_time_dimension: bool = False
    time_granularity: Optional[str] = None  # day, week, month, quarter, year
    synonyms: Optional[List[str]] = Field(default_factory=list)

    # Parent context for ID generation (required)
    model_id: str  # Parent NativeSemanticModel ID

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: `{model_id}.dimension.{name}`."""
        return f"{self.model_id}.dimension.{self.name}"


class NativeFact(BaseNode):
    """Warehouse-declared row-level fact from a semantic model.

    Facts represent quantitative row-level data that can be queried individually,
    unlike measures which are always aggregated. In Snowflake, facts are accessed
    via the FACTS() clause in SEMANTIC_VIEW() queries.

    Examples:
        - transaction_amount (row-level value, not aggregated)
        - order_quantity
        - revenue_value
    """
    node_label: ClassVar[NodeLabel] = NodeLabel.NATIVE_FACT

    # Fact-specific fields
    semantic_table_name: str
    expression: Optional[str] = None  # SQL expression (if derived)
    data_type: Optional[str] = None
    description: Optional[str] = None
    synonyms: Optional[List[str]] = Field(default_factory=list)

    # Parent context for ID generation (required)
    model_id: str  # Parent NativeSemanticModel ID

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: `{model_id}.fact.{name}`."""
        return f"{self.model_id}.fact.{self.name}"


class NativeBaseTable(BaseNode):
    """Base table referenced by a native semantic model.

    Represents a base table that is referenced by a semantic model.
    """
    node_label: ClassVar[NodeLabel] = NodeLabel.NATIVE_BASE_TABLE

    name: str
    base_table_database_name: str
    base_table_schema_name: str
    base_table_name: str
    synonyms: Optional[List[str]] = Field(default_factory=list)
    primary_key: Optional[List[str]] = Field(default_factory=list)
    model_id: str  # Parent NativeSemanticModel ID

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: `{model_id}.base_table.{name}`."""
        return f"{self.model_id}.base_table.{self.name}"


class NativeSemanticModel(BaseNode):
    """Warehouse-native semantic model node (flat properties only).

    Represents a provider-specific semantic layer (Snowflake, Databricks, BigQuery, etc.)
    as a graph node with flat properties. Relationships to measures, dimensions, and facts
    are created via edges, not nested properties.

    This is NATIVE/DECLARED in the warehouse, separate from LLM-inferred semantic
    metadata (see InferredSemanticModel).

    Children:
        - NativeMeasure nodes (via HAS_MEASURE edges)
        - NativeDimension nodes (via HAS_DIMENSION edges)
        - NativeFact nodes (via HAS_FACT edges)
        - NativeBaseTable nodes (via HAS_SEMANTIC_TABLE edges)

    The ID is auto-computed from provider, database, schema, and name.

    Usage:
        >>> model = NativeSemanticModel(
        ...     name="sv_arr_reporting",
        ...     database_name="DEMO_DB",
        ...     schema_name="MARTS",
        ...     provider="snowflake",
        ... )
        >>> model.id
        'native_semantic_model.snowflake.DEMO_DB.MARTS.sv_arr_reporting'
    """
    node_label: ClassVar[NodeLabel] = NodeLabel.NATIVE_SEMANTIC_MODEL

    # Core identification
    database_name: str
    schema_name: str
    provider: str  # snowflake, databricks, bigquery, etc.

    # Metadata (flat properties only)
    owner: Optional[str] = None
    comment: Optional[str] = None
    created_on: Optional[str] = None  # ISO timestamp
    synonyms: Optional[List[str]] = Field(default_factory=list)
    raw_metadata: Optional[str] = None  # Backend-specific metadata as JSON string

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from provider, database, schema, name."""
        return f"native_semantic_model.{self.provider}.{self.database_name}.{self.schema_name}.{self.name}"

    class GraphSchema:
        """Metadata for graph database schema generation.

        This metadata is used by schema_loader to generate backend-specific DDL
        (e.g., CREATE NODE TABLE for KùzuDB, constraints for Neo4j).
        """
        primary_key = "id"
        indexes = ["name", "provider"]


class NativeSemanticModelData(BaseModel):
    """DTO for transferring native semantic model with all its components.

    This class separates data transfer concerns from graph storage. Backends
    return this DTO, and loaders decompose it into individual nodes + edges.

    Usage:
        Backend creates DTO:
        >>> data = NativeSemanticModelData(
        ...     model=NativeSemanticModel(name="sv_arr", database_name="DEMO", schema_name="MARTS", provider="snowflake"),
        ...     measures=[NativeMeasure(...)],
        ...     dimensions=[NativeDimension(...)],
        ... )

        Loader decomposes into graph:
        >>> storage.upsert_node(data.model)  # Create model node
        >>> for measure in data.measures:
        ...     storage.upsert_node(measure)  # Create measure node
        ...     storage.create_edge(data.model, measure, HasMeasure())  # Link
    """
    model: NativeSemanticModel
    measures: List[NativeMeasure] = Field(default_factory=list)
    dimensions: List[NativeDimension] = Field(default_factory=list)
    facts: List[NativeFact] = Field(default_factory=list)
    tables: List[NativeBaseTable] = Field(default_factory=list)


class NativeSemanticModelOverview(BaseModel):
    """Lightweight native semantic model metadata for list/search operations.

    Used by list tools to return basic model information without loading
    all measures/dimensions/facts.
    """
    name: str
    database_name: str
    schema_name: str
    description: Optional[str] = None
    provider: str
    synonyms: Optional[List[str]] = Field(default_factory=list)

    @classmethod
    def from_native_semantic_model(cls, model: NativeSemanticModel) -> NativeSemanticModelOverview:
        """Create a NativeSemanticModelOverview from a NativeSemanticModel."""
        return cls(
            name=model.name,
            database_name=model.database_name,
            schema_name=model.schema_name,
            description=model.comment or "",
            provider=model.provider,
            synonyms=model.synonyms or [],
        )


__all__ = [
    "NativeSemanticModel",
    "NativeMeasure",
    "NativeDimension",
    "NativeFact",
    "NativeBaseTable",
    "NativeSemanticModelData",
    "NativeSemanticModelOverview",
]
