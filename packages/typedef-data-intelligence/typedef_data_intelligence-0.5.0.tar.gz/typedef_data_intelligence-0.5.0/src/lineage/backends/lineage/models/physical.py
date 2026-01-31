"""Pydantic models for physical warehouse entities (tables, views, columns).

These models represent physical data assets in the warehouse, separate from
logical dbt definitions:

- PhysicalRelation: Base class for all physical tables/views
  - PhysicalTable: Materialized table
  - PhysicalView: View
  - PhysicalMaterializedView: Materialized view
  - PhysicalIncrementalModel: Incrementally maintained table
  - PhysicalEphemeral: Ephemeral/CTE (may not persist)

- PhysicalColumn: Column in physical warehouse table/view

Physical entities are environment-specific (dev, staging, prod) and linked to
logical dbt definitions via BUILDS edges.
"""

from datetime import datetime
from typing import ClassVar, Optional

from pydantic import computed_field

from lineage.backends.lineage.models.base import BaseNode, NodeIdentifier
from lineage.backends.types import NodeLabel


class PhysicalRelation(BaseNode):
    """Base class for physical warehouse relations (PHYSICAL entity).

    Represents an actual table, view, or other relation that exists in the warehouse.
    This is separate from logical dbt definitions (DbtModel, DbtSource).

    A single logical DbtModel can create multiple PhysicalRelation instances
    (one per environment: dev, staging, prod).

    Properties:
        fqn: Fully qualified name (database.schema.relation)
        database: Database/catalog name
        schema: Schema name
        relation_name: Table/view name
        warehouse_type: Type of warehouse (snowflake, bigquery, duckdb, etc.)
        environment: Deployment environment (dev, staging, prod, etc.)
        materialization_strategy: How data is materialized (full-refresh, incremental, etc.)
        created_at: When first seen in lineage
        updated_at: When last seen/updated

    Subclasses define specific relation types (table, view, etc.).
    """

    # Will be set in subclasses
    node_label: ClassVar[NodeLabel]

    # Core properties
    name: str = ""  # Relation name (for BaseNode requirement)
    fqn: str = ""  # Fully qualified name (database.schema.table)
    database: str = ""
    schema_name: str = ""
    relation_name: str = ""  # Table/view name

    # Deployment metadata
    warehouse_type: str = ""  # snowflake, bigquery, duckdb, postgres, etc.
    environment: str = ""  # dev, staging, prod, or custom
    materialization_strategy: Optional[str] = None  # full-refresh, incremental, append, etc.

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from FQN + environment.

        Format: physical://{environment}/{fqn}
        Example: physical://prod/analytics_db.marts.customers
        """
        return f"physical://{self.environment}/{self.fqn}"

    @computed_field
    @property
    def search_tokenized_name(self) -> str:
        """Search-only tokenized variant of fqn for full-text recall."""
        return (self.fqn or "").replace(".", " ")

    @classmethod
    def identifier(cls, fqn: str, environment: str) -> "NodeIdentifier":
        """Create NodeIdentifier from FQN and environment.

        Args:
            fqn: Fully qualified name (database.schema.table)
            environment: Environment (dev, staging, prod)

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = PhysicalTable.identifier("db.schema.table", "prod")
            storage.create_edge(from_node, identifier, edge)
            ```
        """
        temp = cls(fqn=fqn, environment=environment)
        return temp.get_node_identifier()


class PhysicalTable(PhysicalRelation):
    """Physical table in warehouse.

    A standard materialized table with persistent storage.
    Typically created by dbt models with materialization='table'.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_TABLE


class PhysicalView(PhysicalRelation):
    """Physical view in warehouse.

    A view (virtual table) that doesn't store data.
    Created by dbt models with materialization='view'.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_VIEW


class PhysicalMaterializedView(PhysicalRelation):
    """Physical materialized view in warehouse.

    A view with cached/materialized results for faster queries.
    Supported by some warehouses (e.g., Snowflake, Postgres).
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_MATERIALIZED_VIEW


class PhysicalIncrementalModel(PhysicalRelation):
    """Physical incrementally-maintained table.

    A table that's updated incrementally (only new/changed rows).
    Created by dbt models with materialization='incremental'.

    Additional properties can track merge/upsert strategy.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_INCREMENTAL_MODEL


class PhysicalEphemeral(PhysicalRelation):
    """Physical ephemeral model (CTE).

    An ephemeral dbt model compiled as a CTE, not materialized as a physical table.
    May have a placeholder entry in lineage but no persistent warehouse object.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_EPHEMERAL


class PhysicalColumn(BaseNode):
    """Column in physical warehouse relation (PHYSICAL entity).

    Represents an actual column in a warehouse table/view.
    This is separate from logical dbt columns (DbtColumn).

    Physical columns can differ from logical dbt columns due to:
    - Type coercion (BIGINT vs INT)
    - Warehouse-specific types (VARCHAR(MAX) in Snowflake)
    - Dynamic columns added at runtime
    - Column transformations during materialization

    Physical columns DERIVE_FROM logical DbtColumn nodes (can be one-to-many or many-to-one).

    Properties:
        name: Column name
        parent_id: PhysicalRelation ID
        data_type: Actual warehouse data type
        nullable: Whether column accepts nulls
        default_value: Default value (if any)

    The ID is constructed as: {parent_id}.{column_name_lowercase}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.PHYSICAL_COLUMN

    # Core properties
    name: str = ""
    fqn: str = ""  # Fully qualified name (database.schema.table.column)
    parent_id: str = ""  # ID of parent PhysicalRelation
    data_type: Optional[str] = None  # Actual warehouse data type (e.g., "VARCHAR(255)", "BIGINT")
    nullable: Optional[bool] = None  # Whether column accepts NULLs
    default_value: Optional[str] = None  # Default value expression

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {parent_id}.{column_name_lowercase}."""
        if not self.name:
            return self.parent_id
        return f"{self.parent_id}.{self.name.lower()}"

    @classmethod
    def identifier(cls, parent_id: str, column_name: str) -> "NodeIdentifier":
        """Create NodeIdentifier from parent_id and column_name.

        Args:
            parent_id: Parent PhysicalRelation ID
            column_name: Column name

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = PhysicalColumn.identifier(
                "physical://prod/db.schema.table",
                "customer_id"
            )
            storage.create_edge(from_node, identifier, edge)
            ```
        """
        temp = cls(name=column_name, parent_id=parent_id)
        return temp.get_node_identifier()


__all__ = [
    "PhysicalRelation",
    "PhysicalTable",
    "PhysicalView",
    "PhysicalMaterializedView",
    "PhysicalIncrementalModel",
    "PhysicalEphemeral",
    "PhysicalColumn",
]
