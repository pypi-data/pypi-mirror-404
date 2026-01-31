"""DuckDB implementation of DataQueryBackend."""
from __future__ import annotations

import logging
import time
from typing import List, Optional

import duckdb

from lineage.backends.config import DuckDBDataConfig
from lineage.backends.data_query.protocol import (
    ColumnProfile,
    QueryResult,
    QueryValidationResult,
    TablePreview,
    TableProfile,
    TableSchema,
)
from lineage.backends.lineage.models.semantic_views import NativeSemanticModelData
from lineage.backends.types import DataBackendType

logger = logging.getLogger(__name__)
class DuckDBBackend:
    """DuckDB backend for data queries.

    Can connect to a DuckDB database file or use in-memory database.
    Supports querying dbt models that have been materialized.

    Supports restricting access to specific schemas or table patterns
    to enforce analyst vs engineer boundaries.
    """

    def __init__(
        self,
        duckdb_config: DuckDBDataConfig
    ):
        """Initialize DuckDB backend.

        Args:
            duckdb_config: DuckDB data configuration
        """
        self.db_path = duckdb_config.db_path
        self.read_only = duckdb_config.read_only
        self.allowed_schemas = duckdb_config.allowed_schemas
        self.allowed_table_patterns = duckdb_config.allowed_table_patterns
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection."""
        if self._conn is None:
            if self.db_path:
                self._conn = duckdb.connect(str(self.db_path), read_only=self.read_only)
            else:
                self._conn = duckdb.connect(":memory:")
        return self._conn

    def _is_table_allowed(self, database: str, schema: str, table: str) -> bool:
        """Check if a table is allowed based on configured restrictions.

        Args:
            database: Database name
            schema: Schema name
            table: Table name

        Returns:
            True if table is allowed, False otherwise
        """
        # If no restrictions, allow all
        if not self.allowed_schemas and not self.allowed_table_patterns:
            return True

        # Check schema allowlist
        if self.allowed_schemas and schema not in self.allowed_schemas:
            return False

        # Check table pattern allowlist
        if self.allowed_table_patterns:
            import fnmatch
            if not any(fnmatch.fnmatch(table, pattern) for pattern in self.allowed_table_patterns):
                return False

        return True

    def _validate_table_access(self, database: str, schema: str, table: str) -> None:
        """Validate that a table is allowed to be accessed.

        Raises:
            PermissionError: If table access is not allowed
        """
        if not self._is_table_allowed(database, schema, table):
            raise PermissionError(
                f"Access denied to {database}.{schema}.{table}. "
                f"Only mart tables are accessible. "
                f"If you need data from intermediate models, please create a data engineering ticket."
            )

    def execute_query(
        self,
        query: str,
        limit: Optional[int] = None,
    ) -> QueryResult:
        """Execute a SQL query and return results.

        Thread-safe: Uses a cursor for each query execution.
        """
        conn = self._get_connection()

        # Apply limit if specified
        if limit:
            query = f"SELECT * FROM ({query}) AS limited_query LIMIT {limit}"

        start_time = time.time()
        # Use cursor for thread-safe execution
        cursor = conn.cursor()
        result = cursor.execute(query)
        execution_time = (time.time() - start_time) * 1000  # ms

        # Fetch all results
        rows = result.fetchall()
        columns = [desc[0] for desc in result.description] if result.description else []

        # Close cursor
        cursor.close()

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time_ms=execution_time,
        )

    def get_table_schema(
        self,
        database: str,
        schema: str,
        table: str,
    ) -> TableSchema:
        """Get schema information for a table.

        Thread-safe: Uses a cursor for each query execution.
        """
        # Validate access
        self._validate_table_access(database, schema, table)

        conn = self._get_connection()

        # Query information_schema for column details
        query = """
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_catalog = ?
                AND table_schema = ?
                AND table_name = ?
            ORDER BY ordinal_position
        """

        # Use cursor for thread-safe execution
        cursor = conn.cursor()
        result = cursor.execute(query, [database, schema, table])
        rows = result.fetchall()
        cursor.close()

        columns = [
            {
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "YES",
                "default": row[3],
            }
            for row in rows
        ]

        return TableSchema(
            database_name=database,
            schema_name=schema,
            table_name=table,
            columns=columns,
        )

    def preview_table(
        self,
        database: str,
        schema: str,
        table: str,
        limit: int = 10,
    ) -> TablePreview:
        """Preview first N rows of a table.

        Thread-safe: Uses cursors for each query execution.
        """
        # Validate access (get_table_schema will also validate)
        self._validate_table_access(database, schema, table)

        conn = self._get_connection()

        # Get schema first (this uses its own cursor internally)
        table_schema = self.get_table_schema(database, schema, table)

        # Get sample rows - use cursor
        qualified_name = f'"{database}"."{schema}"."{table}"'
        query = f"SELECT * FROM {qualified_name} LIMIT {limit}"
        cursor = conn.cursor()
        result = cursor.execute(query)
        sample_rows = result.fetchall()
        cursor.close()

        # Get total row count - use separate cursor
        count_query = f"SELECT COUNT(*) FROM {qualified_name}"
        count_cursor = conn.cursor()
        count_result = count_cursor.execute(count_query)
        total_count = count_result.fetchone()[0] if count_result else None
        count_cursor.close()

        return TablePreview(
            table_schema=table_schema,
            sample_rows=sample_rows,
            total_row_count=total_count,
        )

    def list_databases(self) -> List[str]:
        """List all available databases (catalogs in DuckDB).

        Thread-safe: Uses a cursor for query execution.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        result = cursor.execute("SELECT DISTINCT catalog_name FROM information_schema.schemata")
        databases = [row[0] for row in result.fetchall()]
        cursor.close()
        return databases

    def list_schemas(self, database: str) -> List[str]:
        """List all schemas in a database.

        Thread-safe: Uses a cursor for query execution.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        result = cursor.execute(
            "SELECT schema_name FROM information_schema.schemata WHERE catalog_name = ? ORDER BY schema_name",
            [database],
        )
        schemas = [row[0] for row in result.fetchall()]
        cursor.close()

        # Filter to allowed schemas if restrictions are set
        if self.allowed_schemas:
            schemas = [s for s in schemas if s in self.allowed_schemas]

        return schemas

    def list_tables(
        self,
        database: str,
        schema: str,
    ) -> List[str]:
        """List all tables in a schema.

        Thread-safe: Uses a cursor for query execution.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        result = cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_catalog = ?
                AND table_schema = ?
                AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """,
            [database, schema],
        )
        tables = [row[0] for row in result.fetchall()]
        cursor.close()

        # Filter to allowed table patterns if restrictions are set
        if self.allowed_table_patterns:
            import fnmatch
            tables = [
                t for t in tables
                if any(fnmatch.fnmatch(t, pattern) for pattern in self.allowed_table_patterns)
            ]

        return tables

    def validate_query(self, query: str) -> QueryValidationResult:
        """Validate a SQL query without executing it.

        Thread-safe: Uses a cursor for query execution.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Use EXPLAIN to validate without executing
            cursor.execute(f"EXPLAIN {query}")
            cursor.close()
            return QueryValidationResult(valid=True)
        except Exception as e:
            cursor.close()
            return QueryValidationResult(valid=False, error_message=str(e))

    def get_query_plan(self, query: str) -> str:
        """Get the execution plan for a query.

        Thread-safe: Uses a cursor for query execution.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        result = cursor.execute(f"EXPLAIN {query}")
        rows = result.fetchall()
        cursor.close()
        return "\n".join(row[1] for row in rows)  # Second column has the plan

    def profile_column(
        self,
        database: str,
        schema: str,
        table: str,
        column: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> ColumnProfile:
        """Profile a single column using DuckDB statistics.

        Uses DuckDB's built-in statistical functions for efficient profiling.
        """
        self._validate_table_access(database, schema, table)

        conn = self._get_connection()
        qualified_name = f'"{database}"."{schema}"."{table}"'
        col_quoted = f'"{column}"'

        # Get column data type from schema
        table_schema = self.get_table_schema(database, schema, table)
        col_info = next((c for c in table_schema.columns if c["name"] == column), None)
        if not col_info:
            raise ValueError(f"Column {column} not found in table {qualified_name}")

        data_type = col_info["type"]

        # Build sampling clause if needed
        sample_clause = f"USING SAMPLE {sample_size}" if sample_size else ""

        # Base statistics query - works for all types
        base_stats_query = f"""
            SELECT
                COUNT(*) as total_count,
                COUNT({col_quoted}) as non_null_count,
                COUNT(*) - COUNT({col_quoted}) as null_count,
                COUNT(DISTINCT {col_quoted}) as distinct_count
            FROM {qualified_name} {sample_clause}
        """

        cursor = conn.cursor()
        result = cursor.execute(base_stats_query)
        row = result.fetchone()
        cursor.close()

        total_count = row[0]
        non_null_count = row[1]
        null_count = row[2]
        distinct_count = row[3]
        null_percentage = (null_count / total_count * 100) if total_count > 0 else 0

        # Initialize profile
        profile = ColumnProfile(
            column_name=column,
            data_type=data_type,
            distinct_count=distinct_count,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
        )

        # Type-specific statistics
        is_numeric = any(t in data_type.upper() for t in [
            'INT', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC', 'REAL'
        ])
        is_string = any(t in data_type.upper() for t in ['VARCHAR', 'TEXT', 'CHAR', 'STRING'])
        is_temporal = any(t in data_type.upper() for t in ['DATE', 'TIMESTAMP', 'TIME'])

        try:
            if is_numeric or is_temporal:
                # Numeric/temporal statistics
                stats_query = f"""
                    SELECT
                        MIN({col_quoted}) as min_val,
                        MAX({col_quoted}) as max_val,
                        AVG(CAST({col_quoted} AS DOUBLE)) as avg_val,
                        STDDEV(CAST({col_quoted} AS DOUBLE)) as stddev_val
                    FROM {qualified_name} {sample_clause}
                    WHERE {col_quoted} IS NOT NULL
                """
                cursor = conn.cursor()
                result = cursor.execute(stats_query)
                row = result.fetchone()
                cursor.close()

                if row:
                    profile.min_value = row[0]
                    profile.max_value = row[1]
                    profile.avg_value = round(float(row[2]), 2) if row[2] is not None else None
                    profile.stddev_value = round(float(row[3]), 2) if row[3] is not None else None

            elif is_string:
                # String statistics
                str_stats_query = f"""
                    SELECT
                        MIN(LENGTH({col_quoted})) as min_len,
                        MAX(LENGTH({col_quoted})) as max_len,
                        AVG(LENGTH({col_quoted})) as avg_len
                    FROM {qualified_name} {sample_clause}
                    WHERE {col_quoted} IS NOT NULL
                """
                cursor = conn.cursor()
                result = cursor.execute(str_stats_query)
                row = result.fetchone()
                cursor.close()

                if row:
                    profile.min_length = row[0]
                    profile.max_length = row[1]
                    profile.avg_length = round(float(row[2]), 2) if row[2] is not None else None

        except Exception as e:
            logger.warning(f"Failed to get type-specific statistics for column {column}: {e}")

        # Top K values (most common)
        try:
            top_k_query = f"""
                SELECT
                    {col_quoted} as value,
                    COUNT(*) as count
                FROM {qualified_name} {sample_clause}
                WHERE {col_quoted} IS NOT NULL
                GROUP BY {col_quoted}
                ORDER BY count DESC
                LIMIT {top_k}
            """
            cursor = conn.cursor()
            result = cursor.execute(top_k_query)
            rows = result.fetchall()
            cursor.close()

            profile.top_values = [
                {
                    "value": str(row[0]),
                    "count": row[1],
                    "percentage": round(row[1] / non_null_count * 100, 2) if non_null_count > 0 else 0,
                }
                for row in rows
            ]
        except Exception:
            # If top values fail, skip
            profile.top_values = []

        return profile

    def profile_table(
        self,
        database: str,
        schema: str,
        table: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> TableProfile:
        """Profile all columns in a table using DuckDB statistics.

        This is more efficient than profiling columns individually because
        it can batch some statistics queries.
        """
        from datetime import datetime, timezone

        self._validate_table_access(database, schema, table)

        # Get schema first
        table_schema = self.get_table_schema(database, schema, table)

        # Get total row count
        conn = self._get_connection()
        qualified_name = f'"{database}"."{schema}"."{table}"'

        cursor = conn.cursor()
        result = cursor.execute(f"SELECT COUNT(*) FROM {qualified_name}")
        row_count = result.fetchone()[0]
        cursor.close()

        # Profile each column
        column_profiles = []
        for col_info in table_schema.columns:
            col_name = col_info["name"]
            try:
                col_profile = self.profile_column(
                    database, schema, table, col_name, sample_size, top_k
                )
                column_profiles.append(col_profile)
            except Exception as e:
                # If profiling a column fails, create a minimal profile
                logger.warning(f"Failed to profile column {col_name}: {e}")
                column_profiles.append(ColumnProfile(
                    column_name=col_name,
                    data_type=col_info["type"],
                ))

        return TableProfile(
            database_name=database,
            schema_name=schema,
            table_name=table,
            row_count=row_count,
            column_profiles=column_profiles,
            profile_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def get_semantic_views(
        self,
        database: str,
        schema: str,
    ) -> List[NativeSemanticModelData]:
        """Get all native semantic models in a schema.

        DuckDB does not support semantic views, so this always returns
        an empty list.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            Empty list (DuckDB doesn't support semantic views)
        """
        return []

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def get_backend_type(self) -> DataBackendType:
        """Get the type of the data query backend."""
        return DataBackendType.DUCKDB

    def get_general_query_hints(self) -> str:
        """Get general DuckDB SQL syntax hints.

        Returns:
            DuckDB SQL dialect guide for general queries
        """
        return """
### Data Types
- Use `BIGINT`, `DOUBLE`, `VARCHAR`, `TIMESTAMP`, `BOOLEAN`, `DATE`
- Strings use single quotes: `'text'`
- Identifiers use double quotes: `"column_name"`, `"table_name"`

### String Functions
- Case-insensitive matching: `column ILIKE '%pattern%'`
- String concatenation: `string1 || string2` or `CONCAT(string1, string2)`
- Length: `LENGTH(string)`
- Substring: `SUBSTRING(string, start, length)`

### Date/Time Functions
- Current timestamp: `CURRENT_TIMESTAMP`
- Date parts: `DATE_PART('year', timestamp_col)` or `EXTRACT(YEAR FROM timestamp_col)`
- Date arithmetic: `date_col + INTERVAL '1 day'`
- Formatting: `STRFTIME(timestamp_col, '%Y-%m-%d')`

### Aggregations
- Common: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`
- String aggregation: `STRING_AGG(column, ',')` or `LISTAGG(column, ',')`
- Array aggregation: `LIST(column)` returns array
- Distinct count: `COUNT(DISTINCT column)`

### Window Functions
- Fully supported: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`
- Use `OVER (PARTITION BY ... ORDER BY ...)`

### CTEs and Subqueries
- WITH clause (CTEs): Fully supported and recommended
- Example:
  ```sql
  WITH cte AS (
    SELECT * FROM table1
  )
  SELECT * FROM cte
  ```

### Joins
- All join types supported: `INNER JOIN`, `LEFT JOIN`, `RIGHT JOIN`, `FULL OUTER JOIN`
- Use explicit `ON` conditions

### LIMIT and OFFSET
- `LIMIT n` - return first n rows
- `LIMIT n OFFSET m` - skip m rows, return next n

### Boolean Logic
- Use `TRUE`, `FALSE`, `NULL`
- Boolean operators: `AND`, `OR`, `NOT`
- NULL handling: `IS NULL`, `IS NOT NULL`, `COALESCE(col, default_value)`

### Array/List Operations
- Create array: `LIST_VALUE(1, 2, 3)` or `[1, 2, 3]`
- Array access: `array_col[1]` (1-indexed!)
- Array length: `ARRAY_LENGTH(array_col)` or `LEN(array_col)`
- Unnest arrays: `UNNEST(array_col)`

### Important Quirks
- **Schema qualification**: Use `"database"."schema"."table"` format with double quotes
- **Case sensitivity**: Identifiers are case-insensitive unless quoted
- **Performance**: DuckDB is columnar - avoid `SELECT *`, specify columns
- **Sampling**: Use `USING SAMPLE 10%` for quick data exploration
- **UNION**: `UNION` (distinct) or `UNION ALL` (includes duplicates)

### Common Patterns
```sql
-- Ranked results
SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY value DESC) as rank
FROM table
QUALIFY rank <= 10

-- Date filtering
SELECT * FROM table
WHERE date_col >= CURRENT_DATE - INTERVAL '30 days'

-- String aggregation by group
SELECT category, STRING_AGG(name, ', ' ORDER BY name) as names
FROM table
GROUP BY category
```
""".strip()

    def get_semantic_view_query_hints(self) -> str:
        """Get hints for querying semantic views.

        DuckDB does not support semantic views.

        Returns:
            Empty string (DuckDB doesn't support semantic views)
        """
        return ""

    def get_semantic_view_modification_hints(self) -> str:
        """Get hints for creating/modifying semantic views.

        DuckDB does not support semantic views.

        Returns:
            Empty string (DuckDB doesn't support semantic views)
        """
        return ""

    def validate_semantic_view_query(
        self,
        query: str,
        semantic_views: List[str],
    ) -> QueryValidationResult:
        """Validate semantic view query for DuckDB.

        DuckDB does not support semantic views, so this always returns an error.

        Args:
            query: SQL query (ignored)
            semantic_views: List of semantic views (ignored)

        Returns:
            QueryValidationResult with error indicating DuckDB doesn't support semantic views
        """
        return QueryValidationResult(
            valid=False,
            error_message="DuckDB does not support semantic views. "
                         "Semantic views are only available in data warehouses like Snowflake."
        )

    def get_agent_hints(self) -> str:
        """Get DuckDB-specific hints for AI agents writing SQL queries.

        Returns:
            Comprehensive DuckDB SQL dialect guide for agents
        """
        hints = "## DUCKDB SPECIFIC DATA BACKEND GUIDELINES\n\n"
        hints += "You are querying a **DuckDB** data warehouse. Follow these DuckDB-specific guidelines:\n\n"
        hints += self.get_general_query_hints()
        return hints

    # =========================================================================
    # MCP Tool Delegation Methods (Not Supported in DuckDB)
    # =========================================================================

    async def list_semantic_views(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ):
        """DuckDB does not support semantic views."""
        raise NotImplementedError(
            "DuckDB does not support semantic views. "
            "Use the data engineering agent to explore tables directly."
        )

    async def show_semantic_metrics(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        view_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ):
        """DuckDB does not support semantic views."""
        raise NotImplementedError(
            "DuckDB does not support semantic views. "
            "Use the data engineering agent to explore tables directly."
        )

    async def show_semantic_dimensions(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        view_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ):
        """DuckDB does not support semantic views."""
        raise NotImplementedError(
            "DuckDB does not support semantic views. "
            "Use the data engineering agent to explore tables directly."
        )

    async def query_semantic_view(
        self,
        view_name: str,
        database_name: str,
        schema_name: str,
        measures=None,
        dimensions=None,
        facts=None,
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ):
        """DuckDB does not support semantic views."""
        raise NotImplementedError(
            "DuckDB does not support semantic views. "
            "Use the data engineering agent to explore tables directly."
        )

    async def get_semantic_view_ddl(
        self,
        database_name: str,
        schema_name: str,
        view_name: str,
    ):
        """DuckDB does not support semantic views."""
        raise NotImplementedError(
            "DuckDB does not support semantic views. "
            "Use the data engineering agent to explore tables directly."
        )
