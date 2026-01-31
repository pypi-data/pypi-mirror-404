"""Pydantic models for data profiling nodes.

These models represent profiling statistics collected from data warehouses:
- TableProfile: Table-level statistics (row counts, profiling metadata)
- ColumnProfile: Column-level statistics (nulls, distinct values, distributions)
"""

from typing import ClassVar, Optional

from pydantic import computed_field

from lineage.backends.lineage.models.base import BaseNode
from lineage.backends.types import NodeLabel


class TableProfile(BaseNode):
    """Table-level profiling statistics.

    Stores metadata about when a table was profiled and basic table-level
    statistics like row count.

    The ID is constructed as: profile.table.{database}.{schema}.{table}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.TABLE_PROFILE

    # Core properties
    name: str  # Table name
    database_name: str
    schema_name: str
    table_name: str
    row_count: int
    profiled_at: str  # ISO 8601 timestamp

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: profile.table.{database_name}.{schema_name}.{table_name}."""
        return f"profile.table.{self.database_name}.{self.schema_name}.{self.table_name}"


class ColumnProfile(BaseNode):
    """Column-level profiling statistics.

    Stores detailed statistics about a column including null counts,
    distinct values, min/max values, and value distributions.

    The ID is constructed as: {table_profile_id}.column.{column_name}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.COLUMN_PROFILE

    # Core properties
    name: str  # Column name
    column_name: str  # Column name (redundant with name for clarity)
    data_type: str  # SQL data type
    null_count: int
    distinct_count: int
    min_value: Optional[str] = None  # Min value as string
    max_value: Optional[str] = None  # Max value as string
    avg_value: Optional[str] = None  # Average value as string
    top_values: Optional[str] = None  # For now, store as JSON string (TODO(bc): better serialization)

    # Parent table profile ID (set externally)
    table_profile_id: str = ""

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {table_profile_id}.column.{column_name}."""
        if self.table_profile_id:
            return f"{self.table_profile_id}.column.{self.column_name}"
        # Fallback
        return f"profile.column.{self.column_name}"


__all__ = ["TableProfile", "ColumnProfile"]
