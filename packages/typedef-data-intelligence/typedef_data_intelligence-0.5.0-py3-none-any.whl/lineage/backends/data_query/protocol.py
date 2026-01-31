"""Protocol interface for data query backends."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Tuple,
    runtime_checkable,
)

from pydantic import BaseModel, Field, model_serializer

from lineage.backends.lineage.models.semantic_views import NativeSemanticModelData
from lineage.backends.types import DataBackendType

if TYPE_CHECKING:
    pass


class QueryResult(BaseModel):
    """Result from executing a query."""
    columns: List[str] = Field(default_factory=list)
    rows: List[Tuple[Any, ...]] = Field(default_factory=list)
    row_count: int = Field(default=0)
    execution_time_ms: Optional[float] = Field(default=None)
    error_message: Optional[str] = Field(default=None)
    query_name: Optional[str] = Field(default=None)

    @model_serializer
    def serialize_model(self) -> dict[str, Any]:
        """Custom serializer to handle Decimal, date, and datetime objects.

        Converts:
        - Decimal with no decimal places → int (e.g., Decimal('42') → 42)
        - Decimal with decimal places → float (e.g., Decimal('42.5') → 42.5)
        - date/datetime → ISO string
        - Recursively handles nested structures
        """
        def serialize_value(obj: Any) -> Any:
            if isinstance(obj, Decimal):
                # Convert to int if whole number, else float
                return int(obj) if obj % 1 == 0 else float(obj)
            elif isinstance(obj, (date, datetime)):
                return obj.isoformat()
            elif isinstance(obj, (list, tuple)):
                return [serialize_value(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: serialize_value(v) for k, v in obj.items()}
            return obj

        return {
            'columns': self.columns,
            'rows': [tuple(serialize_value(v) for v in row) for row in self.rows],
            'row_count': self.row_count,
            'execution_time_ms': self.execution_time_ms,
            'error_message': self.error_message,
            'query_name': self.query_name,
        }


class TableSchema(BaseModel):
    """Schema information for a table."""
    database_name: str
    schema_name: str
    table_name: str
    columns: List[Dict[str, Any]] = Field(default_factory=list)  # [{name, type, nullable, ...}]


class TablePreview(BaseModel):
    """Preview of table data."""
    table_schema: TableSchema
    sample_rows: List[List[Any]] = Field(default_factory=list)
    sample_row_count: int = Field(default=0)
    total_row_count: Optional[int] = None


class ColumnProfile(BaseModel):
    """Statistical profile for a single column."""
    column_name: str
    data_type: str

    # Cardinality metrics
    distinct_count: Optional[int] = None
    null_count: Optional[int] = None
    null_percentage: Optional[float] = None

    # Numeric statistics (for numeric columns)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    stddev_value: Optional[float] = None

    # String statistics (for string columns)
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    # Top values (most common)
    top_values: Optional[List[Dict[str, Any]]] = None  # [{value, count, percentage}]


class TableProfile(BaseModel):
    """Statistical profile for a table."""
    database_name: str
    schema_name: str
    table_name: str
    row_count: int
    column_profiles: List[ColumnProfile] = Field(default_factory=list)
    profile_timestamp: Optional[str] = None  # ISO timestamp when profile was created


class QueryValidationResult(BaseModel):
    """Result from validating a query."""
    valid: bool
    error_message: Optional[str] = None


class NativeSemanticModelQueryFragment(BaseModel):
    """Fragment for semantic view query construction."""
    table: str
    name: str

@runtime_checkable
class DataQueryBackend(Protocol):
    """Protocol for data query backend implementations.

    This interface allows different backends (DuckDB, Snowflake, etc.)
    to provide the same query capabilities to agents via MCP.
    """

    async def execute_query(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> QueryResult:
        """Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            limit: Maximum number of rows to return

        Returns:
            QueryResult with columns and rows
        """
        ...

    async def get_table_schema(
        self,
        database: str,
        schema: str,
        table: str,
    ) -> TableSchema:
        """Get schema information for a table.

        Args:
            database: Database name
            schema: Schema name
            table: Table name

        Returns:
            TableSchema with column definitions
        """
        ...

    async def preview_table(
        self,
        database: str,
        schema: str,
        table: str,
        limit: int = 10,
    ) -> TablePreview:
        """Preview first N rows of a table.

        Args:
            database: Database name
            schema: Schema name
            table: Table name
            limit: Number of rows to preview

        Returns:
            TablePreview with schema and sample data
        """
        ...

    async def list_databases(self) -> QueryResult:
        """List all available databases."""
        ...

    async def list_schemas(self, database: str) -> QueryResult:
        """List all schemas in a database."""
        ...

    async def list_tables(
        self,
        database: str,
        schema: str,
    ) -> QueryResult:
        """List all tables in a schema."""
        ...

    def validate_query(self, query: str) -> QueryValidationResult:
        """Validate a SQL query without executing it.

        Returns:
            QueryValidationResult with 'valid' (bool) and optional 'error_message'
        """
        ...

    async def get_query_plan(self, query: str) -> str:
        """Get the execution plan for a query."""
        ...

    async def profile_table(
        self,
        database: str,
        schema: str,
        table: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> TableProfile:
        """Profile a table to gather statistical metadata.

        Args:
            database: Database name
            schema: Schema name
            table: Table name
            sample_size: Optional sample size for large tables (None = full table)
            top_k: Number of top values to include per column

        Returns:
            TableProfile with comprehensive statistics for each column
        """
        ...

    async def profile_column(
        self,
        database: str,
        schema: str,
        table: str,
        column: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> ColumnProfile:
        """Profile a single column to gather statistics.

        Args:
            database: Database name
            schema: Schema name
            table: Table name
            column: Column name
            sample_size: Optional sample size for large tables
            top_k: Number of top values to include

        Returns:
            ColumnProfile with statistics for the column
        """
        ...

    async def get_semantic_views(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[NativeSemanticModelData]:
        """Get all semantic views in a schema.

        Semantic views are business-friendly views with semantic metadata
        (measures, dimensions, time dimensions).

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of SemanticViewData DTOs (view node + components)

        Note:
            For backends that don't support semantic views (e.g., DuckDB),
            this should return an empty list.
        """
        ...

    def get_backend_type(self) -> DataBackendType:
        """Get the type of the data query backend."""
        ...

    def get_general_query_hints(self) -> str:
        """Get general SQL syntax hints for this backend.

        Returns:
            String with data types, functions, joins, CTEs, etc.

        Note:
            This should include general SQL syntax that applies to all query types:
            - Data types and literals
            - String, date/time, and math functions
            - JOINs, CTEs, window functions
            - Aggregations and GROUP BY
            - Performance tips
        """
        ...

    def get_semantic_view_query_hints(self) -> str:
        """Get hints for querying semantic views.

        Returns:
            String with how to query semantic views (e.g., SEMANTIC_VIEW() function for Snowflake)

        Note:
            Should include:
            - Required syntax for querying semantic views
            - METRICS vs DIMENSIONS vs FACTS clauses
            - Common query patterns
            - Compatibility rules
        """
        ...

    def get_semantic_view_modification_hints(self) -> str:
        """Get hints for creating/modifying semantic views.

        Returns:
            String with how to CREATE/ALTER/DROP semantic views

        Note:
            Should include:
            - CREATE SEMANTIC VIEW syntax
            - How to define metrics/measures
            - How to define dimensions
            - Best practices
            - Privilege requirements
        """
        ...

    def get_agent_hints(self) -> str:
        """Get backend-specific hints for the agent to use when writing SQL queries.

        Returns:
            String with backend-specific hints

        Note:
            This is a convenience method that combines all hint types.
            For more granular control, use get_general_query_hints(),
            get_semantic_view_query_hints(), and get_semantic_view_modification_hints().
        """
        ...

    async def list_semantic_views(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List semantic views using backend's native MCP tooling.

        Args:
            database_name: Database name (optional)
            schema_name: Schema name (optional)
            like: Pattern to filter view names (SQL LIKE syntax)
            starts_with: Prefix to filter view names

        Returns:
            List of dictionaries with semantic view metadata

        Note:
            Backends without MCP support should raise NotImplementedError.
        """
        ...

    async def show_semantic_metrics(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        view_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ) -> QueryResult:
        """Show available metrics in semantic views.

        Args:
            database_name: Database name (optional)
            schema_name: Schema name (optional)
            view_name: Specific view to show metrics for (optional)
            like: Pattern to filter metric names
            starts_with: Prefix to filter metric names

        Returns:
            QueryResult with columns and rows

        Note:
            Backends without semantic views should raise NotImplementedError.
        """
        ...

    async def show_semantic_dimensions(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        view_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ) -> QueryResult:
        """Show available dimensions in semantic views.

        Args:
            database_name: Database name (optional)
            schema_name: Schema name (optional)
            view_name: Specific view to show dimensions for (optional)
            like: Pattern to filter dimension names
            starts_with: Prefix to filter dimension names

        Returns:
            QueryResult with columns and rows

        Note:
            Backends without semantic views should raise NotImplementedError.
        """
        ...
    
    async def show_semantic_facts(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        view_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ) -> QueryResult:
        """Show semantic facts with optional database/schema filtering.

        Args:
            database_name: Database name (optional)
            schema_name: Schema name (optional)
            view_name: View name (optional)
            like: Pattern to filter fact names (SQL LIKE syntax)
            starts_with: Prefix to filter fact names

        Returns:
            QueryResult with columns and rows
        """
        ...

    async def query_semantic_view(
        self,
        view_name: str,
        database_name: str,
        schema_name: str,
        measures: List[NativeSemanticModelQueryFragment] = None,
        dimensions: List[NativeSemanticModelQueryFragment] = None,
        facts: List[NativeSemanticModelQueryFragment] = None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> QueryResult:
        """Query semantic view using parameterized approach.

        Args:
            view_name: Name of semantic view
            database_name: Database name
            schema_name: Schema name
            measures: List of measures like [{"table": "view_name", "name": "measure_name"}]
            dimensions: List of dimensions like [{"table": "view_name", "name": "dim_name"}]
            facts: List of facts like [{"table": "view_name", "name": "fact_name"}]
            where_clause: Optional WHERE condition (without WHERE keyword)
            order_by: Optional ORDER BY clause (without ORDER BY keyword)
            limit: Maximum rows to return

        Returns:
            QueryResult with columns and rows

        Note:
            - Must include at least one of: measures, dimensions, or facts
            - Cannot combine facts with measures in same query
            - Backends without semantic views should raise NotImplementedError
        """
        ...

    async def get_semantic_view_ddl(
        self,
        database_name: str,
        schema_name: str,
        view_name: str,
    ) -> str:
        """Get DDL definition for semantic view.

        Args:
            database_name: Database name
            schema_name: Schema name
            view_name: Name of semantic view

        Returns:
            DDL definition string

        Note:
            Backends without semantic views should raise NotImplementedError.
        """
        ...