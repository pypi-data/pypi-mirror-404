"""Snowflake native implementation using snowflake-connector-python."""
from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import sqlglot
from sqlglot import exp

from lineage.backends.config import SnowflakeDataConfig
from lineage.backends.data_query.protocol import (
    ColumnProfile,
    NativeSemanticModelQueryFragment,
    QueryResult,
    QueryValidationResult,
    TablePreview,
    TableProfile,
    TableSchema,
)
from lineage.backends.lineage.models.semantic_views import (
    NativeBaseTable,
    NativeDimension,
    NativeFact,
    NativeMeasure,
    NativeSemanticModel,
    NativeSemanticModelData,
)
from lineage.backends.types import DataBackendType

logger = logging.getLogger(__name__)

try:
    import snowflake.connector
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    SNOWFLAKE_AVAILABLE = True
except ImportError:
    SNOWFLAKE_AVAILABLE = False
    logger.warning(
        "snowflake-connector-python not installed. "
        "Install with: pip install snowflake-connector-python cryptography"
    )


class SnowflakeNativeBackend:
    """Snowflake backend using native Python connector.

    Uses snowflake-connector-python directly instead of MCP server.
    Supports private key authentication for security.

    Supports restricting access to specific schemas or table patterns
    to enforce analyst vs engineer boundaries.
    """

    def __init__(self, snowflake_config: SnowflakeDataConfig):
        """Initialize Snowflake native backend.

        Args:
            snowflake_config: Snowflake data configuration
        """
        if not SNOWFLAKE_AVAILABLE:
            raise ImportError(
                "snowflake-connector-python is not installed. "
                "Install with: pip install snowflake-connector-python cryptography"
            )

        self.config = snowflake_config
        self.allowed_schemas = snowflake_config.allowed_schemas
        self.allowed_table_patterns = snowflake_config.allowed_table_patterns
        self.allowed_databases = snowflake_config.allowed_databases
        self._connection = None

    def _load_private_key(self) -> bytes:
        """Load and decode private key from file.

        Returns:
            Private key bytes in DER format
        """
        with open(self.config.private_key_path, "rb") as key_file:
            private_key_data = key_file.read()

        # Parse the private key
        passphrase = None
        if self.config.private_key_passphrase:
            passphrase = self.config.private_key_passphrase.encode()

        private_key = serialization.load_pem_private_key(
            private_key_data,
            password=passphrase,
            backend=default_backend()
        )

        # Convert to DER format (required by Snowflake connector)
        private_key_der = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        return private_key_der

    @staticmethod
    def _escape_snowflake_string_literal(value: Optional[str]) -> str:
        """Escape a value for safe interpolation into a single-quoted Snowflake SQL string literal.

        Snowflake SQL uses standard SQL escaping: single quotes are escaped by doubling them.
        For example: 'It''s' represents the string It's.

        Args:
            value: The string value to escape (or None)

        Returns:
            Escaped string safe for interpolation into single-quoted SQL string literals
        """
        if value is None:
            return ""
        return str(value).replace("'", "''")

    @staticmethod
    def _quote_snowflake_identifier(identifier: str) -> str:
        """Quote an identifier for safe interpolation into Snowflake SQL.

        This is for *identifiers* (database/schema/view/table/column), not string literals.
        We always double-quote and escape embedded double quotes by doubling them.

        This prevents SQL injection when callers provide identifiers and access controls
        are not configured (allowed_* allowlists unset).
        """
        # Snowflake doesn't allow NUL bytes in identifiers; treat as invalid input.
        if "\x00" in identifier:
            raise ValueError("Invalid Snowflake identifier: contains NUL byte")
        escaped = str(identifier).replace('"', '""')
        return f'"{escaped}"'

    @staticmethod
    def _normalize_snowflake_identifier(identifier: Optional[str]) -> Optional[str]:
        """Normalize Snowflake identifiers to avoid case-sensitive mismatches.

        - If the identifier is wrapped in quotes/backticks/brackets, preserve inner case.
        - Otherwise, normalize to uppercase (Snowflake default for unquoted identifiers).
        """
        if identifier is None:
            return None
        value = str(identifier).strip()
        if not value:
            return value
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("`") and value.endswith("`")
        ):
            return value[1:-1]
        if value.startswith("[") and value.endswith("]"):
            return value[1:-1]
        return value.upper()

    @classmethod
    def _quote_snowflake_qualified_identifier(cls, *parts: str) -> str:
        """Quote a dot-qualified identifier (e.g., DB.SCHEMA.OBJECT)."""
        return ".".join(cls._quote_snowflake_identifier(p) for p in parts)

    async def _ensure_connected(self) -> None:
        """Ensure connection is established (lazy connection)."""
        if self._connection is None or self._connection.is_closed():
            logger.debug(f"Connecting to Snowflake account: {self.config.account}")

            # Load private key
            private_key_der = self._load_private_key()

            # Create connection with private key auth
            self._connection = snowflake.connector.connect(
                account=self.config.account,
                user=self.config.user,
                private_key=private_key_der,
                warehouse=self.config.warehouse,
                database=self.config.database,
                schema=self.config.schema_name,
                role=self.config.role,
                client_session_keep_alive=True,
                client_session_keep_alive_interval=900, # 15 minutes
            )

            logger.debug("Snowflake connection established")

    async def __aenter__(self):
        """Enter async context - establish connection."""
        await self._ensure_connected()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context - close connection."""
        if self._connection and not self._connection.is_closed():
            try:
                self._connection.close()
                logger.debug("Snowflake connection closed")
            except Exception as e:
                logger.warning(f"Error closing connection: {e}")

    # =========================================================================
    # Query Validation Helpers
    # =========================================================================

    def _require_database_when_schema_provided(
        self,
        *,
        database_name: Optional[str],
        schema_name: Optional[str],
    ) -> None:
        """Ensure callers don't provide schema_name without a database_name.

        In Snowflake, schemas are scoped to a database. Accepting schema_name alone
        is ambiguous and can cause unscoped SHOW commands that silently ignore the
        schema filter.
        """
        if schema_name and not database_name:
            raise ValueError(
                "schema_name requires database_name (Snowflake schemas are scoped to a database)"
            )

    def _validate_query_read_only(self, query: str) -> None:
        """Validate query is SELECT-only when read_only mode is enabled.

        Args:
            query: SQL query to validate

        Raises:
            PermissionError: If query is not a SELECT statement
        """
        try:
            # Parse with Snowflake dialect
            parsed = sqlglot.parse(query, dialect="snowflake")

            for statement in parsed:
                if statement is None:
                    continue

                # Allow SELECT statements (including WITH/CTE)
                if isinstance(statement, exp.Select):
                    continue

                # Allow SHOW commands (metadata queries)
                if isinstance(statement, exp.Command):
                    cmd_name = statement.this.upper() if statement.this else ""
                    if cmd_name in ("SHOW", "DESCRIBE", "DESC", "EXPLAIN"):
                        continue

                # Allow DESCRIBE statements
                if isinstance(statement, exp.Describe):
                    continue

                # Reject everything else (INSERT, UPDATE, DELETE, CREATE, DROP, etc.)
                stmt_type = type(statement).__name__
                raise PermissionError(
                    f"Read-only mode enabled: {stmt_type} statements are not allowed. "
                    "Only SELECT, SHOW, and DESCRIBE queries are permitted."
                )

        except sqlglot.errors.ParseError as e:
            # If we can't parse, do a basic check for dangerous keywords
            query_upper = query.upper().strip()
            dangerous_keywords = [
                "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
                "TRUNCATE", "MERGE", "GRANT", "REVOKE", "COPY"
            ]
            for keyword in dangerous_keywords:
                if query_upper.startswith(keyword):
                    raise PermissionError(
                        f"Read-only mode enabled: {keyword} statements are not allowed. "
                        "Only SELECT, SHOW, and DESCRIBE queries are permitted."
                    ) from e

    def _validate_database_access(self, database: str) -> None:
        """Validate database is in allowed_databases (case-insensitive).

        Args:
            database: Database name to validate

        Raises:
            PermissionError: If database is not allowed
        """
        if not self.allowed_databases:
            return  # No restrictions

        allowed_upper = {db.upper() for db in self.allowed_databases}
        if database.upper() not in allowed_upper:
            raise PermissionError(
                f"Access denied to database '{database}'. "
                f"Allowed databases: {self.allowed_databases}"
            )

    def _validate_schema_access(self, database: str, schema: str) -> None:
        """Validate database and schema are allowed (case-insensitive).

        Args:
            database: Database name to validate
            schema: Schema name to validate

        Raises:
            PermissionError: If database or schema is not allowed
        """
        # First validate database
        self._validate_database_access(database)

        # Then validate schema
        if not self.allowed_schemas:
            return  # No schema restrictions

        allowed_upper = {s.upper() for s in self.allowed_schemas}
        if schema.upper() not in allowed_upper:
            raise PermissionError(
                f"Access denied to schema '{database}.{schema}'. "
                f"Allowed schemas: {self.allowed_schemas}"
            )

    def _filter_results_by_allowed(
        self,
        results: List[Dict[str, Any]],
        database_key: str = "database_name",
        schema_key: str = "schema_name",
    ) -> List[Dict[str, Any]]:
        """Filter results to only include allowed databases and schemas.

        Args:
            results: List of result dictionaries
            database_key: Key name for database in result dicts
            schema_key: Key name for schema in result dicts

        Returns:
            Filtered list containing only allowed databases/schemas
        """
        if not self.allowed_databases and not self.allowed_schemas:
            return results

        filtered = []
        allowed_db_upper = {db.upper() for db in self.allowed_databases} if self.allowed_databases else None
        allowed_schema_upper = {s.upper() for s in self.allowed_schemas} if self.allowed_schemas else None
        for item in results:
            db = item.get(database_key, "")
            schema = item.get(schema_key, "")

            if allowed_db_upper and (db.upper() if db else "") not in allowed_db_upper:
                continue
            if allowed_schema_upper and (schema.upper() if schema else "") not in allowed_schema_upper:
                continue

            filtered.append(item)

        return filtered

    def _filter_query_result_by_allowed(
        self,
        result: QueryResult,
        database_col: str = "database_name",
        schema_col: str = "schema_name",
    ) -> QueryResult:
        """Filter QueryResult rows to only include allowed databases/schemas.

        Finds columns by name (case-insensitive) for robustness.

        Args:
            result: QueryResult to filter
            database_col: Column name for database
            schema_col: Column name for schema

        Returns:
            New QueryResult with filtered rows
        """
        if not self.allowed_databases and not self.allowed_schemas:
            return result

        # Find column indices by name (case-insensitive)
        columns_upper = [c.upper() for c in result.columns]
        try:
            db_idx = columns_upper.index(database_col.upper())
            schema_idx = columns_upper.index(schema_col.upper())
        except ValueError as e:
            # Security: Fail closed - cannot filter without expected columns
            # This prevents silently bypassing access control if Snowflake's
            # SHOW command returns unexpected column names
            error_msg = (
                f"Cannot apply access control filter: expected columns "
                f"'{database_col}' and '{schema_col}' not found in result. "
                f"Found columns: {result.columns}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        allowed_db_upper = {db.upper() for db in self.allowed_databases} if self.allowed_databases else None
        allowed_schema_upper = {s.upper() for s in self.allowed_schemas} if self.allowed_schemas else None

        filtered_rows = []
        for row in result.rows:
            db = str(row[db_idx]).upper() if row[db_idx] else ""
            schema = str(row[schema_idx]).upper() if row[schema_idx] else ""

            if allowed_db_upper and db not in allowed_db_upper:
                continue
            if allowed_schema_upper and schema not in allowed_schema_upper:
                continue

            filtered_rows.append(row)

        return QueryResult(
            columns=result.columns,
            rows=filtered_rows,
            row_count=len(filtered_rows),
        )

    def _detect_semantic_view_in_query(self, query: str) -> bool:
        """Check if query attempts to directly query a semantic view.

        Args:
            query: SQL query to check

        Returns:
            True if query appears to query a semantic view directly
        """
        # We explicitly disallow querying semantic views directly because Snowflake semantic
        # views require the SEMANTIC_VIEW() table function syntax.
        #
        # Historically this used a FROM-only regex, which allowed bypassing the check via
        # JOIN sv_* (or sv_* appearing later in a comma-separated FROM list). We now use
        # sqlglot to reliably extract table references across FROM/JOIN/etc., with a regex
        # fallback for unparseable SQL.
        query_upper = query.upper()

        # If using SEMANTIC_VIEW() function, that's allowed
        if "SEMANTIC_VIEW(" in query_upper:
            return False

        # Preferred: parse and extract all Table references (covers JOIN, nested queries, etc.)
        try:
            parsed = sqlglot.parse(query, dialect="snowflake")
            for statement in parsed:
                if statement is None:
                    continue
                for table in statement.find_all(exp.Table):
                    table_name = (table.name or "").upper()
                    if table_name.startswith("SV_"):
                        return True
        except sqlglot.errors.ParseError:
            # Fall back to regex heuristic below
            pass

        # Fallback heuristic: match SV_* after FROM or JOIN tokens, including qualified names.
        # Examples caught:
        #   FROM SV_METRICS
        #   JOIN sv_metrics ON ...
        #   FROM DB.SCHEMA.SV_METRICS
        # NOTE: This doesn't attempt to be a full SQL parser; sqlglot path above is preferred.
        sv_pattern = r"\b(?:FROM|JOIN)\s+(?:[\w.]+\.)?(SV_\w+)\b"
        return re.search(sv_pattern, query_upper) is not None

    def _extract_tables_from_query(self, query: str) -> Set[Tuple[Optional[str], Optional[str], str]]:
        """Parse SQL with sqlglot and extract table references.

        Args:
            query: SQL query to parse

        Returns:
            Set of (database, schema, table) tuples. Database/schema may be None if not qualified.
        """
        tables: Set[Tuple[Optional[str], Optional[str], str]] = set()

        parsed = sqlglot.parse(query, dialect="snowflake")

        for statement in parsed:
            if statement is None:
                continue

            # Find all Table expressions
            for table in statement.find_all(exp.Table):
                table_name = table.name
                schema_name = table.db  # In sqlglot, 'db' is the schema
                database_name = table.catalog  # 'catalog' is the database

                if table_name:
                    tables.add((database_name, schema_name, table_name))

        return tables

    def _extract_and_validate_tables_from_query(self, query: str) -> None:
        """Parse SQL with sqlglot, extract table references, validate each.

        Args:
            query: SQL query to validate

        Raises:
            PermissionError: If any table in the query is not allowed
        """
        # Skip validation if no restrictions are configured
        if not self.allowed_databases and not self.allowed_schemas and not self.allowed_table_patterns:
            return

        try:
            tables = self._extract_tables_from_query(query)
        except sqlglot.errors.ParseError as e:
            # SECURITY: fail closed. If allowlists are configured but we can't reliably parse the
            # query (sqlglot limitation vs Snowflake-supported syntax), table access controls
            # would otherwise be bypassed.
            logger.warning(
                "Could not parse query for table access validation; blocking query because "
                "allowlist restrictions are configured. Query prefix: %s",
                query[:200],
                exc_info=True,
            )
            raise PermissionError(
                "Could not parse SQL to validate table access. "
                "This query is blocked because allowed_databases/allowed_schemas/allowed_table_patterns are configured."
            ) from e

        for database, schema, table in tables:
            # Use defaults if not specified in query
            db = database or self.config.database
            sch = schema or self.config.schema_name

            # Validate using the existing method
            if not self._is_table_allowed(db, sch, table):
                raise PermissionError(
                    f"Access denied to table '{db}.{sch}.{table}'. "
                    f"Check allowed_databases, allowed_schemas, and allowed_table_patterns configuration."
                )

    async def execute_query(
        self,
        query: str,
        limit: Optional[int] = None,  # noqa: ARG002 - TODO: clean up
        *,
        _skip_validation: bool = False,
    ) -> QueryResult:
        """Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            limit: Unused parameter (TODO: clean up)
            _skip_validation: Internal flag to skip validation for queries generated
                by this class's own methods. Should NOT be exposed to external callers.

        Returns:
            QueryResult with columns, rows, and metadata

        Raises:
            PermissionError: If query violates read_only mode or accesses disallowed tables
            ValueError: If query attempts to directly query a semantic view
        """
        await self._ensure_connected()

        # Only validate external queries (not internal SHOW commands, etc.)
        if not _skip_validation:
            # Validate read-only mode if enabled
            if self.config.read_only:
                try:
                    self._validate_query_read_only(query)
                except PermissionError as e:
                    return QueryResult(
                        columns=[],
                        rows=[],
                        row_count=0,
                        error_message=str(e),
                    )

            # Check for direct semantic view queries - redirect to query_semantic_view tool
            if self._detect_semantic_view_in_query(query):
                return QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    error_message=(
                        "Direct queries to semantic views (tables prefixed with 'sv_') are not allowed. "
                        "Semantic views require special SEMANTIC_VIEW() syntax. "
                        "Please use the query_semantic_view tool instead, which handles the correct syntax automatically."
                    ),
                )

            # Validate table access based on allowed_databases/schemas/table_patterns
            try:
                self._extract_and_validate_tables_from_query(query)
            except PermissionError as e:
                return QueryResult(
                    columns=[],
                    rows=[],
                    row_count=0,
                    error_message=str(e),
                )

        sql = query

        logger.debug(f"Executing query: {sql}")

        start_time = time.time()

        try:
            cursor = self._connection.cursor()
            cursor = await asyncio.to_thread(cursor.execute, sql)

            # Get column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            # Fetch all rows
            rows = cursor.fetchall()

            cursor.close()

            execution_time = (time.time() - start_time) * 1000  # ms
            query_result = QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time,
            )
            return query_result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Query execution failed: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                execution_time_ms=execution_time,
                error_message=str(e),
            )

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
            TableSchema with column information
        """
        await self._ensure_connected()

        if database is not None:
            database = self._normalize_snowflake_identifier(database)
        if schema is not None:
            schema = self._normalize_snowflake_identifier(schema)
        if table is not None:
            table = self._normalize_snowflake_identifier(table)

        # Validate access
        self._validate_table_access(database, schema, table)

        # describe table
        qualified_name = self._quote_snowflake_qualified_identifier(database, schema, table)
        query = f"DESCRIBE TABLE {qualified_name}"

        result = await self.execute_query(query, _skip_validation=True)

        if result.error_message:
            raise ValueError(f"Failed to get table schema: {result.error_message}")
        rows = [dict(zip(result.columns, row, strict=True)) for row in result.rows]
        return TableSchema(
            database_name=database,
            schema_name=schema,
            table_name=table,
            columns=rows,
        )

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
            TablePreview with schema and sample rows
        """
        # Get schema first (handles normalization and validation internally)
        table_schema = await self.get_table_schema(database, schema, table)

        # Use normalized identifiers from table_schema for subsequent queries
        database = table_schema.database_name
        schema = table_schema.schema_name
        table = table_schema.table_name

        # Get sample rows
        qualified_name = self._quote_snowflake_qualified_identifier(database, schema, table)
        query = f"SELECT * FROM {qualified_name} LIMIT {limit}"  # nosec B608: identifiers are safely quoted
        query_result = await self.execute_query(query, _skip_validation=True)

        # Get total row count
        count_query = f"SELECT COUNT(*) FROM {qualified_name}"  # nosec B608: identifiers are safely quoted
        count_result = await self.execute_query(count_query, _skip_validation=True)
        total_count = count_result.rows[0][0] if count_result.rows else None

        return TablePreview(
            table_schema=table_schema,
            sample_rows=query_result.rows,
            sample_row_count=len(query_result.rows),
            total_row_count=total_count,
        )

    async def list_databases(self) -> QueryResult:
        """List all available databases.

        Returns:
            QueryResult with database names
        """
        await self._ensure_connected()

        query = "SHOW DATABASES"
        result = await self.execute_query(query, _skip_validation=True)

        if result.error_message:
            raise ValueError(f"Failed to list databases: {result.error_message}")

        databases = [row[1] for row in result.rows]
        logger.info(f"Allowed databases: {self.allowed_databases}")
        logger.info(f"Available databases: {databases}")
        if self.allowed_databases:
            # Normalize to uppercase for case-insensitive comparison (Snowflake uses uppercase)
            allowed_upper = {db.upper() for db in self.allowed_databases}
            filtered_rows = [(database,) for database in databases if database.upper() in allowed_upper]
        else:
            filtered_rows = [(database,) for database in databases]
        logger.info(f"Filtered databases: {filtered_rows}")
        return QueryResult(
            columns=["name"],
            rows=filtered_rows,
            row_count=len(filtered_rows),
            execution_time_ms=result.execution_time_ms,
        )

    async def list_schemas(self, database: str) -> QueryResult:
        """List all schemas in a database.

        Args:
            database: Database name

        Returns:
            QueryResult with schema names
        """
        if database is not None:
            database = self._normalize_snowflake_identifier(database)

        if self.allowed_databases:
            allowed_upper = {db.upper() for db in self.allowed_databases}
            if database.upper() not in allowed_upper:
                raise ValueError(f"Database {database} is not allowed in {self.allowed_databases}")

        await self._ensure_connected()

        database_identifier = self._quote_snowflake_identifier(database)
        query = f"SHOW SCHEMAS IN DATABASE {database_identifier}"
        result = await self.execute_query(query, _skip_validation=True)

        if result.error_message:
            raise ValueError(f"Failed to list schemas in {database}: {result.error_message}")


        # Filter to allowed schemas if restrictions are set (case-insensitive)
        if self.allowed_schemas:
            allowed_upper = {s.upper() for s in self.allowed_schemas}
            filtered_rows = [(row[1],) for row in result.rows if row[1].upper() in allowed_upper]
        else:
            filtered_rows = [(row[1],) for row in result.rows]

        return QueryResult(
            columns=["name"],
            rows=filtered_rows,
            row_count=len(filtered_rows),
            execution_time_ms=result.execution_time_ms,
            error_message=result.error_message,
        )

    async def list_tables(
        self,
        database: str,
        schema: str,
    ) -> QueryResult:
        """List all tables in a schema.

        Args:
            database: Database name
            schema: Schema name

        Returns:
            List of table names
        """
        if database is not None:
            database = self._normalize_snowflake_identifier(database)
        if schema is not None:
            schema = self._normalize_snowflake_identifier(schema)

        if self.allowed_databases:
            allowed_db_upper = {db.upper() for db in self.allowed_databases}
            if database.upper() not in allowed_db_upper:
                raise ValueError(f"Database {database} is not allowed in {self.allowed_databases}")
        if self.allowed_schemas:
            allowed_schema_upper = {s.upper() for s in self.allowed_schemas}
            if schema.upper() not in allowed_schema_upper:
                raise ValueError(f"Schema {schema} is not allowed in {self.allowed_schemas}")

        await self._ensure_connected()

        qualified_name = self._quote_snowflake_qualified_identifier(database, schema)
        query = f"SHOW TABLES IN {qualified_name}"
        result = await self.execute_query(query, _skip_validation=True)

        if result.error_message:
            raise ValueError(f"Failed to list tables in {database}.{schema}: {result.error_message}")

        # SHOW TABLES returns: created_on, name, database_name, schema_name, kind, comment, ...
        tables = [row[1] for row in result.rows]


        if self.allowed_table_patterns:
            tables = [
                t for t in tables
                if any(fnmatch.fnmatch(t, pattern) for pattern in self.allowed_table_patterns)
            ]

        return QueryResult(
            columns=["name"],
            rows=[(table,) for table in tables],
            row_count=len(tables),
            execution_time_ms=result.execution_time_ms,
        )

    async def validate_query(self, query: str) -> QueryValidationResult:
        """Validate a SQL query without executing it.

        Validates:
        1. Read-only compliance (if read_only mode enabled)
        2. Table access permissions
        3. Semantic view usage (must use query_semantic_view tool)
        4. SQL syntax via EXPLAIN

        Args:
            query: SQL query to validate

        Returns:
            QueryValidationResult indicating if query is valid
        """
        await self._ensure_connected()

        # Validate read-only mode if enabled
        if self.config.read_only:
            try:
                self._validate_query_read_only(query)
            except PermissionError as e:
                return QueryValidationResult(valid=False, error_message=str(e))

        # Check for direct semantic view queries
        if self._detect_semantic_view_in_query(query):
            return QueryValidationResult(
                valid=False,
                error_message=(
                    "Direct queries to semantic views (tables prefixed with 'sv_') are not allowed. "
                    "Please use the query_semantic_view tool instead."
                ),
            )

        # Validate table access
        try:
            self._extract_and_validate_tables_from_query(query)
        except PermissionError as e:
            return QueryValidationResult(valid=False, error_message=str(e))

        try:
            # Use EXPLAIN to validate SQL syntax without executing
            # Skip validation for the EXPLAIN wrapper since we already validated the inner query
            explain_query = f"EXPLAIN {query}"
            result = await self.execute_query(explain_query, _skip_validation=True)

            if result.error_message:
                return QueryValidationResult(valid=False, error_message=result.error_message)
            else:
                return QueryValidationResult(valid=True)
        except Exception as e:
            return QueryValidationResult(valid=False, error_message=str(e))

    async def get_query_plan(self, query: str) -> str:
        """Get the execution plan for a query.

        Validates query before generating plan.

        Args:
            query: SQL query

        Returns:
            Query execution plan as string

        Raises:
            PermissionError: If query violates read_only mode or accesses disallowed tables
            ValueError: If query attempts to directly query a semantic view or EXPLAIN fails
        """
        await self._ensure_connected()

        # Validate read-only mode if enabled
        if self.config.read_only:
            self._validate_query_read_only(query)

        # Check for direct semantic view queries
        if self._detect_semantic_view_in_query(query):
            raise ValueError(
                "Direct queries to semantic views (tables prefixed with 'sv_') are not allowed. "
                "Please use the query_semantic_view tool instead."
            )

        # Validate table access
        self._extract_and_validate_tables_from_query(query)

        # Skip validation for the EXPLAIN wrapper since we already validated the inner query
        explain_query = f"EXPLAIN {query}"
        result = await self.execute_query(explain_query, _skip_validation=True)

        if result.error_message:
            raise ValueError(f"Failed to get query plan: {result.error_message}")

        # Snowflake EXPLAIN returns a single column with plan text
        return "\n".join(str(row[0]) for row in result.rows)

    async def profile_column(
        self,
        database: str,
        schema: str,
        table: str,
        column: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> ColumnProfile:
        """Profile a single column using Snowflake statistics.

        Args:
            database: Database name
            schema: Schema name
            table: Table name
            column: Column name
            sample_size: Optional sample size
            top_k: Number of top values to return

        Returns:
            ColumnProfile with statistics
        """
        await self._ensure_connected()

        # Normalize column (get_table_schema handles database/schema/table normalization)
        if column is not None:
            column = self._normalize_snowflake_identifier(column)

        # Get schema first (handles normalization and validation internally)
        table_schema = await self.get_table_schema(database, schema, table)

        # Use normalized identifiers from table_schema for subsequent queries
        database = table_schema.database_name
        schema = table_schema.schema_name
        table = table_schema.table_name

        qualified_name = self._quote_snowflake_qualified_identifier(database, schema, table)
        col_info = next(
            (
                c
                for c in table_schema.columns
                if str(c.get("name", "")).upper() == str(column).upper()
            ),
            None,
        )
        if not col_info:
            raise ValueError(f"Column {column} not found in table {qualified_name}")

        # Use canonical column name from schema and always quote it to prevent SQL injection.
        col_name = self._quote_snowflake_identifier(str(col_info["name"]))
        data_type = col_info["type"]

        # Build sampling clause if needed
        sample_clause = f"SAMPLE ({sample_size} ROWS)" if sample_size else ""

        # Base statistics query (identifiers are safely quoted)
        base_stats_query = (
            "SELECT\n"
            "    COUNT(*) as total_count,\n"
            "    COUNT(" + col_name + ") as non_null_count,\n"
            "    COUNT(*) - COUNT(" + col_name + ") as null_count,\n"
            "    COUNT(DISTINCT " + col_name + ") as distinct_count\n"
            "FROM " + qualified_name + ((" " + sample_clause) if sample_clause else "") + "\n"
        )

        result = await self.execute_query(base_stats_query, _skip_validation=True)
        if result.error_message or not result.rows:
            raise ValueError(f"Failed to get base statistics for column {column}: {result.error_message}")

        row = result.rows[0]
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
            'NUMBER', 'INT', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC', 'REAL'
        ])
        is_string = any(t in data_type.upper() for t in ['VARCHAR', 'TEXT', 'CHAR', 'STRING'])
        is_temporal = any(t in data_type.upper() for t in ['DATE', 'TIMESTAMP', 'TIME'])

        # Numeric/temporal statistics
        if is_numeric or is_temporal:
            stats_query = (
                "SELECT\n"
                "    MIN(" + col_name + ") as min_val,\n"
                "    MAX(" + col_name + ") as max_val,\n"
                "    AVG(CAST(" + col_name + " AS DOUBLE)) as avg_val,\n"
                "    STDDEV(CAST(" + col_name + " AS DOUBLE)) as stddev_val\n"
                "FROM " + qualified_name + ((" " + sample_clause) if sample_clause else "") + "\n"
                "WHERE " + col_name + " IS NOT NULL\n"
            )
            result = await self.execute_query(stats_query, _skip_validation=True)
            if not result.error_message and result.rows:
                row = result.rows[0]
                profile.min_value = row[0]
                profile.max_value = row[1]
                profile.avg_value = round(float(row[2]), 2) if row[2] is not None else None
                profile.stddev_value = round(float(row[3]), 2) if row[3] is not None else None

        # String statistics
        elif is_string:
            str_stats_query = (
                "SELECT\n"
                "    MIN(LENGTH(" + col_name + ")) as min_len,\n"
                "    MAX(LENGTH(" + col_name + ")) as max_len,\n"
                "    AVG(LENGTH(" + col_name + ")) as avg_len\n"
                "FROM " + qualified_name + ((" " + sample_clause) if sample_clause else "") + "\n"
                "WHERE " + col_name + " IS NOT NULL\n"
            )
            result = await self.execute_query(str_stats_query, _skip_validation=True)
            if not result.error_message and result.rows:
                row = result.rows[0]
                profile.min_length = row[0]
                profile.max_length = row[1]
                profile.avg_length = round(float(row[2]), 2) if row[2] is not None else None

        # Top K values
        top_k_query = (
            "SELECT\n"
            "    " + col_name + " as value,\n"
            "    COUNT(*) as count\n"
            "FROM " + qualified_name + ((" " + sample_clause) if sample_clause else "") + "\n"
            "WHERE " + col_name + " IS NOT NULL\n"
            "GROUP BY " + col_name + "\n"
            "ORDER BY count DESC\n"
            "LIMIT " + str(top_k) + "\n"
        )
        result = await self.execute_query(top_k_query, _skip_validation=True)

        profile.top_values = [
            {
                "value": str(row[0]),
                "count": row[1],
                "percentage": round(row[1] / non_null_count * 100, 2) if non_null_count > 0 else 0,
            }
            for row in result.rows
        ]

        return profile

    async def profile_table(
        self,
        database: str,
        schema: str,
        table: str,
        sample_size: Optional[int] = None,
        top_k: int = 10,
    ) -> TableProfile:
        """Profile all columns in a table.

        Args:
            database: Database name
            schema: Schema name
            table: Table name
            sample_size: Optional sample size
            top_k: Number of top values per column

        Returns:
            TableProfile with all column profiles
        """
        await self._ensure_connected()

        from datetime import datetime, timezone

        # Get schema first (handles normalization and validation internally)
        table_schema = await self.get_table_schema(database, schema, table)

        # Use normalized identifiers from table_schema for subsequent queries
        database = table_schema.database_name
        schema = table_schema.schema_name
        table = table_schema.table_name

        # Get total row count
        qualified_name = self._quote_snowflake_qualified_identifier(database, schema, table)
        count_result = await self.execute_query(
            f"SELECT COUNT(*) FROM {qualified_name}",  # nosec B608: identifiers are safely quoted
            _skip_validation=True,
        )
        row_count = count_result.rows[0][0] if count_result.rows else 0

        # Profile each column
        column_profiles = []
        for col_info in table_schema.columns:
            col_name = col_info["name"]
            try:
                col_profile = await self.profile_column(
                    database, schema, table, col_name, sample_size, top_k
                )
                column_profiles.append(col_profile)
            except Exception:
                # If profiling a column fails, create a minimal profile
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

    async def get_semantic_views(
        self,
        database: Optional[str] = None,
        schema: Optional[str] = None,
    ) -> List[NativeSemanticModelData]:
        """Get all semantic views in a schema.

        Queries Snowflake's SHOW SEMANTIC VIEWS and DESCRIBE SEMANTIC VIEW
        to retrieve semantic view metadata.

        Args:
            database: Database name (defaults to config database)
            schema: Schema name (defaults to config schema)

        Returns:
            List of NativeSemanticModelData with view node and components

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database is None:
            database = self.config.database
        if schema is None:
            schema = self.config.schema_name

        raw_database = database
        raw_schema = schema
        database = self._normalize_snowflake_identifier(database)
        schema = self._normalize_snowflake_identifier(schema)
        if (raw_database, raw_schema) != (database, schema):
            logger.debug(
                "Normalized Snowflake identifiers for semantic views: %s.%s -> %s.%s",
                raw_database,
                raw_schema,
                database,
                schema,
            )

        # Validate database and schema access
        self._validate_schema_access(database, schema)

        try:
            # Get list of semantic views
            qualified_schema = self._quote_snowflake_qualified_identifier(database, schema)
            show_result = await self.execute_query(
                f"SHOW SEMANTIC VIEWS IN {qualified_schema}",
                _skip_validation=True,
            )

            semantic_views = []

            for row in show_result.rows:
                # SHOW SEMANTIC VIEWS returns columns:
                # 0: created_on, 1: name, 2: database_name, 3: schema_name,
                # 4: comment, 5: owner, 6: owner_role_type, 7: extension
                created_on = row[0]
                view_name = row[1]
                _db_name = row[2]  # Not used - view is in current database
                _schema_name_result = row[3]  # Not used - we use the schema param
                comment = row[4] if len(row) > 4 else None
                owner = row[5] if len(row) > 5 else None

                # Compute view_id
                view_id = f"semantic_view.snowflake.{database}.{schema}.{view_name}"

                measures: list[NativeMeasure] = []
                dimensions: list[NativeDimension] = []
                facts: list[NativeFact] = []
                base_tables: list[NativeBaseTable] = []

                desc_comment = comment
                desc_owner = owner
                view_synonyms = []
                raw_metadata = None

                try:
                    qualified_view = self._quote_snowflake_qualified_identifier(database, schema, view_name)
                    desc_result = await self.execute_query(
                        f"DESCRIBE SEMANTIC VIEW {qualified_view}",
                        _skip_validation=True,
                    )
                    desc_rows = desc_result.rows

                    # Parse property-value structure
                    objects = {}  # key: (object_kind, object_name), value: {property: value}

                    for desc_row in desc_rows:
                        object_kind = desc_row[0] if desc_row[0] else None
                        object_name = desc_row[1] if desc_row[1] else None
                        parent_entity = desc_row[2] if desc_row[2] else None
                        prop_name = desc_row[3]
                        prop_value = desc_row[4]

                        # View-level properties
                        if object_kind is None and object_name is None and parent_entity is None:
                            if prop_name == 'COMMENT':
                                desc_comment = prop_value
                            elif prop_name == 'OWNER':
                                desc_owner = prop_value
                            elif prop_name == 'SYNONYMS':
                                try:
                                    view_synonyms = json.loads(prop_value) if prop_value else []
                                except (json.JSONDecodeError, TypeError):
                                    view_synonyms = []
                        else:
                            # Object-level properties
                            key = (object_kind, object_name)
                            if key not in objects:
                                objects[key] = {}
                            objects[key][prop_name] = prop_value

                    # Extract measures, dimensions, facts, and tables
                    for (obj_kind, obj_name), properties in objects.items():
                        if obj_kind == 'METRIC':
                            expression = properties.get('EXPRESSION', obj_name)
                            agg_func = 'SUM'
                            if expression:
                                expr_upper = str(expression).upper()
                                for agg in ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX']:
                                    if agg in expr_upper:
                                        agg_func = agg
                                        break

                            synonyms = None
                            if properties.get('SYNONYMS'):
                                try:
                                    synonyms = json.loads(properties['SYNONYMS'])
                                    view_synonyms.extend(synonyms)
                                except (json.JSONDecodeError, TypeError):
                                    synonyms = None

                            measures.append(NativeMeasure(
                                semantic_table_name=properties.get('TABLE'),
                                name=obj_name,
                                model_id=view_id,
                                expression=expression,
                                aggregation=agg_func,
                                data_type=properties.get('DATA_TYPE'),
                                description=properties.get('COMMENT'),
                                synonyms=synonyms,
                            ))

                        elif obj_kind == 'DIMENSION':
                            expression = properties.get('EXPRESSION')
                            data_type = properties.get('DATA_TYPE', '')
                            is_time = any(t in data_type.upper() for t in ['DATE', 'TIME', 'TIMESTAMP'])

                            synonyms = None
                            if properties.get('SYNONYMS'):
                                try:
                                    synonyms = json.loads(properties['SYNONYMS'])
                                except (json.JSONDecodeError, TypeError):
                                    synonyms = None
                            dimensions.append(NativeDimension(
                                semantic_table_name=properties.get('TABLE'),
                                name=obj_name,
                                model_id=view_id,
                                expression=expression,
                                data_type=data_type,
                                description=properties.get('COMMENT'),
                                is_time_dimension=is_time,
                                synonyms=synonyms,
                            ))

                        elif obj_kind == 'FACT':
                            synonyms = None
                            if properties.get('SYNONYMS'):
                                try:
                                    synonyms = json.loads(properties['SYNONYMS'])
                                except (json.JSONDecodeError, TypeError):
                                    synonyms = None

                            facts.append(NativeFact(
                                semantic_table_name=properties.get('TABLE'),
                                name=obj_name,
                                model_id=view_id,
                                expression=properties.get('EXPRESSION'),
                                data_type=properties.get('DATA_TYPE'),
                                description=properties.get('COMMENT'),
                                synonyms=synonyms,
                            ))

                        elif obj_kind == 'TABLE':
                            base_table_db = properties.get('BASE_TABLE_DATABASE_NAME')
                            base_table_schema = properties.get('BASE_TABLE_SCHEMA_NAME')
                            base_table_name = properties.get('BASE_TABLE_NAME')
                            primary_key = None
                            if properties.get('PRIMARY_KEY'):
                                try:
                                    primary_key = json.loads(properties['PRIMARY_KEY'])
                                except (json.JSONDecodeError, TypeError):
                                    primary_key = None
                            synonyms = None
                            if properties.get('SYNONYMS'):
                                try:
                                    synonyms = json.loads(properties['SYNONYMS'])
                                    view_synonyms.extend(synonyms)
                                except (json.JSONDecodeError, TypeError):
                                    synonyms = None

                            if base_table_db and base_table_schema and base_table_name:
                                base_tables.append(NativeBaseTable(
                                    name=obj_name,
                                    base_table_database_name=base_table_db,
                                    base_table_schema_name=base_table_schema,
                                    base_table_name=base_table_name,
                                    synonyms=synonyms,
                                    primary_key=primary_key,
                                    model_id=view_id,
                                ))

                    # Store raw metadata
                    raw_metadata = {
                        "describe_output": [
                            {
                                "object_kind": row[0],
                                "object_name": row[1],
                                "parent_entity": row[2],
                                "property": row[3],
                                "property_value": row[4]
                            }
                            for row in desc_rows
                        ]
                    }

                except Exception as e:
                    logger.warning(f"Failed to describe semantic view {view_name}: {e}")

                # Create NativeSemanticModel node
                view = NativeSemanticModel(
                    name=view_name,
                    database_name=database,
                    schema_name=schema,
                    provider="snowflake",
                    owner=desc_owner,
                    comment=desc_comment,
                    created_on=str(created_on) if created_on else None,
                    synonyms=view_synonyms if view_synonyms else [],
                    raw_metadata=json.dumps(raw_metadata),
                )

                semantic_views.append(NativeSemanticModelData(
                    model=view,
                    measures=measures,
                    dimensions=dimensions,
                    facts=facts,
                    tables=base_tables,
                ))

            return semantic_views

        except Exception as e:
            logger.warning(f"Failed to get semantic views: {e}")
            return []

    async def list_semantic_views(
        self,
        database_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        like: Optional[str] = None,
        starts_with: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List semantic views using Snowflake SHOW commands.

        Args:
            database_name: Database name (optional)
            schema_name: Schema name (optional, requires database_name)
            like: Pattern to filter view names (SQL LIKE syntax)
            starts_with: Prefix to filter view names

        Returns:
            List of dictionaries with semantic view metadata

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)

        # Prevent ambiguous calls that would silently drop the schema filter.
        self._require_database_when_schema_provided(
            database_name=database_name,
            schema_name=schema_name,
        )

        # Validate database and schema access if provided
        if database_name and schema_name:
            self._validate_schema_access(database_name, schema_name)
        elif database_name:
            self._validate_database_access(database_name)

        # Build SHOW command
        show_cmd = "SHOW TERSE SEMANTIC VIEWS"

        if database_name and schema_name:
            qualified_schema = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
            )
            show_cmd += f" IN SCHEMA {qualified_schema}"
        elif database_name:
            show_cmd += f" IN DATABASE {self._quote_snowflake_identifier(database_name)}"

        if like:
            escaped_like = self._escape_snowflake_string_literal(like)
            show_cmd += f" LIKE '{escaped_like}'"
        elif starts_with:
            escaped_starts_with = self._escape_snowflake_string_literal(starts_with)
            show_cmd += f" STARTS WITH '{escaped_starts_with}'"

        logger.debug("list_semantic_views: show_cmd=%s", show_cmd)
        try:
            # If no database/schema is provided, prefer account-scoped discovery.
            # This matches Snowflake UI behavior more closely and avoids "empty"
            # results when the current database doesn't contain semantic views.
            if not database_name and not schema_name:
                account_cmd = "SHOW TERSE SEMANTIC VIEWS IN ACCOUNT"
                logger.debug("list_semantic_views: account_show_cmd=%s", account_cmd)
                result = await self.execute_query(account_cmd, _skip_validation=True)
                if result.error_message:
                    logger.warning(
                        "list_semantic_views: account scope failed; falling back to default scope. "
                        "error=%s",
                        result.error_message,
                    )
                    result = await self.execute_query(show_cmd, _skip_validation=True)
            else:
                result = await self.execute_query(show_cmd, _skip_validation=True)

            # Build column name to index mapping (case-insensitive)
            col_map = {col.upper(): idx for idx, col in enumerate(result.columns)}

            def get_col(row: tuple, col_name: str, default: Any = None) -> Any:
                """Get column value by name, case-insensitive."""
                idx = col_map.get(col_name.upper())
                if idx is not None and idx < len(row):
                    return row[idx]
                return default

            views = []
            for row in result.rows:
                # Use column names instead of positions for robustness
                views.append({
                    "created_on": str(get_col(row, "created_on")) if get_col(row, "created_on") else None,
                    "name": get_col(row, "name"),
                    "database_name": get_col(row, "database_name"),
                    "schema_name": get_col(row, "schema_name"),
                    "owner": get_col(row, "owner"),
                    "comment": get_col(row, "comment"),
                })

            # Filter to only allowed databases/schemas
            filtered = self._filter_results_by_allowed(views)
            logger.debug(
                "list_semantic_views: raw_count=%s, filtered_count=%s",
                len(views),
                len(filtered),
            )
            return filtered

        except Exception as e:
            logger.error(f"Failed to list semantic views: {e}")
            return []

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
            schema_name: Schema name (optional, requires database_name)
            view_name: Specific view to show metrics for (optional)
            like: Pattern to filter metric names
            starts_with: Prefix to filter metric names

        Returns:
            QueryResult with columns and rows

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)
        if view_name is not None:
            view_name = self._normalize_snowflake_identifier(view_name)

        # Prevent ambiguous calls that would silently drop the schema filter.
        self._require_database_when_schema_provided(
            database_name=database_name,
            schema_name=schema_name,
        )

        # Validate database and schema access if provided
        if view_name and database_name and schema_name:
            self._validate_schema_access(database_name, schema_name)
        elif schema_name and database_name:
            self._validate_schema_access(database_name, schema_name)
        elif database_name:
            self._validate_database_access(database_name)

        # Build SHOW command
        show_cmd = "SHOW TERSE SEMANTIC METRICS"

        if view_name and database_name and schema_name:
            qualified_view = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
                view_name,
            )
            show_cmd += f" IN {qualified_view}"
        elif schema_name and database_name:
            qualified_schema = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
            )
            show_cmd += f" IN SCHEMA {qualified_schema}"
        elif database_name:
            show_cmd += f" IN DATABASE {self._quote_snowflake_identifier(database_name)}"

        if like:
            escaped_like = self._escape_snowflake_string_literal(like)
            show_cmd += f" LIKE '{escaped_like}'"
        elif starts_with:
            escaped_starts_with = self._escape_snowflake_string_literal(starts_with)
            show_cmd += f" STARTS WITH '{escaped_starts_with}'"

        try:
            if not database_name and not schema_name and not view_name:
                account_cmd = "SHOW TERSE SEMANTIC METRICS IN ACCOUNT"
                result = await self.execute_query(account_cmd, _skip_validation=True)
                if result.error_message:
                    logger.warning(
                        "show_semantic_metrics: account scope failed; falling back to default scope. "
                        "error=%s",
                        result.error_message,
                    )
                    result = await self.execute_query(show_cmd, _skip_validation=True)
            else:
                result = await self.execute_query(show_cmd, _skip_validation=True)
            return self._filter_query_result_by_allowed(result)

        except Exception as e:
            logger.error(f"Failed to show semantic metrics: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                error_message=str(e),
            )

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
            schema_name: Schema name (optional, requires database_name)
            view_name: Specific view to show dimensions for (optional)
            like: Pattern to filter dimension names
            starts_with: Prefix to filter dimension names

        Returns:
            QueryResult with columns and rows

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)
        if view_name is not None:
            view_name = self._normalize_snowflake_identifier(view_name)

        # Prevent ambiguous calls that would silently drop the schema filter.
        self._require_database_when_schema_provided(
            database_name=database_name,
            schema_name=schema_name,
        )

        # Validate database and schema access if provided
        if view_name and database_name and schema_name:
            self._validate_schema_access(database_name, schema_name)
        elif schema_name and database_name:
            self._validate_schema_access(database_name, schema_name)
        elif database_name:
            self._validate_database_access(database_name)

        # Build SHOW command
        show_cmd = "SHOW TERSE SEMANTIC DIMENSIONS"

        if view_name and database_name and schema_name:
            qualified_view = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
                view_name,
            )
            show_cmd += f" IN {qualified_view}"
        elif schema_name and database_name:
            qualified_schema = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
            )
            show_cmd += f" IN SCHEMA {qualified_schema}"
        elif database_name:
            show_cmd += f" IN DATABASE {self._quote_snowflake_identifier(database_name)}"

        if like:
            escaped_like = self._escape_snowflake_string_literal(like)
            show_cmd += f" LIKE '{escaped_like}'"
        elif starts_with:
            escaped_starts_with = self._escape_snowflake_string_literal(starts_with)
            show_cmd += f" STARTS WITH '{escaped_starts_with}'"

        try:
            if not database_name and not schema_name and not view_name:
                account_cmd = "SHOW TERSE SEMANTIC DIMENSIONS IN ACCOUNT"
                result = await self.execute_query(account_cmd, _skip_validation=True)
                if result.error_message:
                    logger.warning(
                        "show_semantic_dimensions: account scope failed; falling back to default scope. "
                        "error=%s",
                        result.error_message,
                    )
                    result = await self.execute_query(show_cmd, _skip_validation=True)
            else:
                result = await self.execute_query(show_cmd, _skip_validation=True)
            return self._filter_query_result_by_allowed(result)

        except Exception as e:
            logger.error(f"Failed to show semantic dimensions: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                error_message=str(e),
            )

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
            schema_name: Schema name (optional, requires database_name)
            view_name: View name (optional)
            like: Pattern to filter fact names (SQL LIKE syntax)
            starts_with: Prefix to filter fact names

        Returns:
            QueryResult with columns and rows

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)
        if view_name is not None:
            view_name = self._normalize_snowflake_identifier(view_name)

        # Prevent ambiguous calls that would silently drop the schema filter.
        self._require_database_when_schema_provided(
            database_name=database_name,
            schema_name=schema_name,
        )

        # Validate database and schema access if provided
        if view_name and database_name and schema_name:
            self._validate_schema_access(database_name, schema_name)
        elif schema_name and database_name:
            self._validate_schema_access(database_name, schema_name)
        elif database_name:
            self._validate_database_access(database_name)

        # Build SHOW command
        show_cmd = "SHOW TERSE SEMANTIC FACTS"

        if view_name and database_name and schema_name:
            qualified_view = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
                view_name,
            )
            show_cmd += f" IN {qualified_view}"
        elif schema_name and database_name:
            qualified_schema = self._quote_snowflake_qualified_identifier(
                database_name,
                schema_name,
            )
            show_cmd += f" IN SCHEMA {qualified_schema}"
        elif database_name:
            show_cmd += f" IN DATABASE {self._quote_snowflake_identifier(database_name)}"

        if like:
            escaped_like = self._escape_snowflake_string_literal(like)
            show_cmd += f" LIKE '{escaped_like}'"
        elif starts_with:
            escaped_starts_with = self._escape_snowflake_string_literal(starts_with)
            show_cmd += f" STARTS WITH '{escaped_starts_with}'"

        try:
            if not database_name and not schema_name and not view_name:
                account_cmd = "SHOW TERSE SEMANTIC FACTS IN ACCOUNT"
                result = await self.execute_query(account_cmd, _skip_validation=True)
                if result.error_message:
                    logger.warning(
                        "show_semantic_facts: account scope failed; falling back to default scope. "
                        "error=%s",
                        result.error_message,
                    )
                    result = await self.execute_query(show_cmd, _skip_validation=True)
            else:
                result = await self.execute_query(show_cmd, _skip_validation=True)
            return self._filter_query_result_by_allowed(result)

        except Exception as e:
            logger.error(f"Failed to show semantic facts: {e}")
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                error_message=str(e),
            )

    async def query_semantic_view(
        self,
        view_name: str,
        database_name: str,
        schema_name: str,
        measures: List[NativeSemanticModelQueryFragment],
        dimensions: List[NativeSemanticModelQueryFragment],
        facts: List[NativeSemanticModelQueryFragment],
        where_clause: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> QueryResult:
        """Query semantic view using Snowflake's SEMANTIC_VIEW() function.

        Args:
            view_name: Name of semantic view
            database_name: Database name
            schema_name: Schema name
            measures: List of measures
            dimensions: List of dimensions
            facts: List of facts
            where_clause: Optional WHERE condition
            order_by: Optional ORDER BY clause
            limit: Maximum rows to return

        Returns:
            QueryResult with columns and rows

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)
        if view_name is not None:
            view_name = self._normalize_snowflake_identifier(view_name)

        # Validate database and schema access
        self._validate_schema_access(database_name, schema_name)

        measures = measures or []
        dimensions = dimensions or []
        facts = facts or []
        # Build SEMANTIC_VIEW query
        qualified_view = self._quote_snowflake_qualified_identifier(
            database_name,
            schema_name,
            view_name,
        )

        # Validate we have at least one of measures, dimensions, or facts
        if not (measures or dimensions or facts):
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                error_message="Must specify at least one of: measures, dimensions, or facts"
            )

        # Build SEMANTIC_VIEW clauses
        clauses = []

        # Add DIMENSIONS clause
        if dimensions:
            dim_parts = [f"{dim.table}.{dim.name}" for dim in dimensions]
            clauses.append(f"DIMENSIONS {', '.join(dim_parts)}")

        # Add METRICS clause (note: measures are called METRICS in Snowflake)
        if measures:
            metric_parts = [f"{m.table}.{m.name}" for m in measures]
            clauses.append(f"METRICS {', '.join(metric_parts)}")

        # Add FACTS clause
        if facts:
            fact_parts = [f"{f.table}.{f.name}" for f in facts]
            clauses.append(f"FACTS {', '.join(fact_parts)}")

        # Build query using SEMANTIC_VIEW() syntax
        # Note: FACTS and METRICS cannot be combined in the same query
        if facts and measures:
            return QueryResult(
                columns=[],
                rows=[],
                row_count=0,
                error_message="Cannot combine FACTS and METRICS in the same query"
            )

        # Add WHERE clause (inside SEMANTIC_VIEW parens so we can filter on any field)
        if where_clause:
            clauses.append(f"WHERE {where_clause}")

        semantic_view_clauses = "\n    ".join(clauses)
        # Query is assembled from safe quoted identifiers + agent-constructed clauses
        query = (
            "SELECT * FROM SEMANTIC_VIEW(\n"
            "    " + qualified_view + "\n"
            "    " + semantic_view_clauses + "\n"
            ")"
        )

        # Add ORDER BY (outside parens, operates on result set)
        if order_by:
            query += f"\nORDER BY {order_by}"

        # Add LIMIT (outside parens, operates on result set)
        if limit:
            query += f"\nLIMIT {limit}"

        # Execute the query (skip validation since we've already validated database/schema access)
        return await self.execute_query(query, limit=limit, _skip_validation=True)

    async def get_semantic_view_ddl(
        self,
        database_name: str,
        schema_name: str,
        view_name: str,
    ) -> str:
        """Get DDL definition for semantic view using GET_DDL function.

        Args:
            database_name: Database name
            schema_name: Schema name
            view_name: Name of semantic view

        Returns:
            DDL definition string

        Raises:
            PermissionError: If database or schema is not allowed
        """
        await self._ensure_connected()

        if database_name is not None:
            database_name = self._normalize_snowflake_identifier(database_name)
        if schema_name is not None:
            schema_name = self._normalize_snowflake_identifier(schema_name)
        if view_name is not None:
            view_name = self._normalize_snowflake_identifier(view_name)

        # Validate database and schema access
        self._validate_schema_access(database_name, schema_name)

        qualified_name = f"{database_name}.{schema_name}.{view_name}"
        escaped_qualified_name = self._escape_snowflake_string_literal(qualified_name)
        try:
            result = await self.execute_query(
                f"SELECT GET_DDL('SEMANTIC_VIEW', '{escaped_qualified_name}')",
                _skip_validation=True,
            )
            if result.rows:
                return result.rows[0][0]
            else:
                raise ValueError(f"No DDL found for semantic view {qualified_name}")

        except Exception as e:
            logger.error(f"Failed to get semantic view DDL: {e}")
            raise

    def get_backend_type(self) -> DataBackendType:
        """Get the type of the data query backend."""
        return DataBackendType.SNOWFLAKE

    def get_general_query_hints(self) -> str:
        """Get general Snowflake SQL syntax hints."""
        return """
### Data Types
- Use `NUMBER`, `VARCHAR`, `TIMESTAMP_NTZ`, `TIMESTAMP_LTZ`, `BOOLEAN`, `DATE`, `VARIANT` (JSON)
- Strings use single quotes: `'text'`
- Identifiers use double quotes for case-sensitivity: `"column_name"`, `"table_name"`
- Snowflake identifiers are case-insensitive unless quoted

### String Functions
- Case-insensitive matching: `column ILIKE '%pattern%'`
- String concatenation: `string1 || string2` or `CONCAT(string1, string2)`
- Length: `LENGTH(string)` or `LEN(string)`
- Substring: `SUBSTR(string, start, length)` (1-indexed)
- Trimming: `TRIM(string)`, `LTRIM(string)`, `RTRIM(string)`

### Date/Time Functions
- Current timestamp: `CURRENT_TIMESTAMP()` or `SYSDATE()`
- Date parts: `DATE_PART('year', timestamp_col)` or `EXTRACT(YEAR FROM timestamp_col)`
- Date arithmetic: `DATEADD(day, 1, date_col)` or `TIMESTAMPADD(DAY, 1, timestamp_col)`
- Date difference: `DATEDIFF(day, start_date, end_date)` (NO quotes around date part)
- Formatting: `TO_CHAR(timestamp_col, 'YYYY-MM-DD')`
- Date truncation: `DATE_TRUNC('month', timestamp_col)`

### Aggregations
- Common: `COUNT()`, `SUM()`, `AVG()`, `MIN()`, `MAX()`
- String aggregation: `LISTAGG(column, ',')` with optional `WITHIN GROUP (ORDER BY ...)`
- Array aggregation: `ARRAY_AGG(column)` returns array
- Distinct count: `COUNT(DISTINCT column)`
- Approximate distinct: `APPROX_COUNT_DISTINCT(column)` for large tables

### Window Functions
- Fully supported: `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `LAG()`, `LEAD()`
- Use `OVER (PARTITION BY ... ORDER BY ...)`
- `QUALIFY` clause for filtering window function results (Snowflake-specific):
  ```sql
  SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY value DESC) as rank
  FROM table
  QUALIFY rank <= 10
  ```

### CTEs and Subqueries
- WITH clause (CTEs): Fully supported and recommended
- Recursive CTEs: Supported
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
- Lateral joins: `LATERAL FLATTEN` for unnesting arrays/objects

### LIMIT and OFFSET
- `LIMIT n` - return first n rows
- `LIMIT n OFFSET m` - skip m rows, return next n
- `TOP n` - alternative to LIMIT (SQL Server syntax)

### Boolean Logic
- Use `TRUE`, `FALSE`, `NULL`
- Boolean operators: `AND`, `OR`, `NOT`
- NULL handling: `IS NULL`, `IS NOT NULL`, `COALESCE(col, default_value)`, `NVL(col, default)`

### JSON/VARIANT Operations
- Parse JSON: `PARSE_JSON(string_col)`
- Extract JSON: `json_col:field` or `json_col:field::TYPE`
- Flatten arrays: `LATERAL FLATTEN(input => json_col:array_field)`
- Example:
  ```sql
  SELECT
    json_col:name::VARCHAR as name,
    json_col:age::NUMBER as age
  FROM table
  ```

### Semi-Structured Data
- Snowflake excels at querying JSON, Avro, Parquet directly
- Use `VARIANT` columns to store JSON/XML
- Path notation: `variant_col:level1.level2[0].field`

### Sampling
- `SAMPLE (10)` - 10% sample
- `SAMPLE (100 ROWS)` - 100 row sample
- `TABLESAMPLE BERNOULLI (10)` - Bernoulli sampling
- Example: `SELECT * FROM large_table SAMPLE (1000 ROWS)`

### Important Quirks
- **Schema qualification**: Use `"database"."schema"."table"` format
- **Case sensitivity**: Unquoted identifiers are uppercase by default
- **Query result caching**: Snowflake caches identical queries for 24 hours
- **Zero-copy cloning**: `CREATE TABLE new_table CLONE old_table`
- **Time travel**: `SELECT * FROM table AT (TIMESTAMP => '2024-01-01'::TIMESTAMP)`
- **QUALIFY clause**: Filter window function results without subquery
- **Transactions**: `BEGIN`, `COMMIT`, `ROLLBACK` supported

### Performance Tips
- Use `CLUSTER BY` for frequently filtered columns
- Avoid `SELECT *`, specify columns
- Use materialized views for complex aggregations
- Consider using `APPROX_COUNT_DISTINCT` for cardinality on large datasets
- Use sampling for exploratory queries on large tables

### Common Patterns
```sql
-- Ranked results with QUALIFY (Snowflake-specific)
SELECT *, ROW_NUMBER() OVER (PARTITION BY category ORDER BY value DESC) as rank
FROM table
QUALIFY rank <= 10

-- Date filtering
SELECT * FROM table
WHERE date_col >= DATEADD(day, -30, CURRENT_DATE())

-- String aggregation by group
SELECT category, LISTAGG(name, ', ') WITHIN GROUP (ORDER BY name) as names
FROM table
GROUP BY category

-- JSON parsing and extraction
SELECT
  json_col:customer.name::VARCHAR as customer_name,
  json_col:order.total::NUMBER as order_total
FROM orders_json

-- Lateral flatten for nested arrays
SELECT
  f.value:id::NUMBER as item_id,
  f.value:name::VARCHAR as item_name
FROM table,
LATERAL FLATTEN(input => json_col:items) f
```
""".strip()

    def get_semantic_view_query_hints(self) -> str:
        """Get hints for querying Snowflake semantic views."""
        return """
# ⚠️ CRITICAL: SNOWFLAKE SEMANTIC VIEWS REQUIRE SPECIAL SYNTAX ⚠️

**YOU MUST use the `SEMANTIC_VIEW()` function** - regular SELECT syntax will NOT work.

**Required format:**
```sql
SELECT * FROM SEMANTIC_VIEW(
  <view_name>
  METRICS(<metric1>, <metric2>, ...) OR FACTS(<fact1>, <fact2>, ...)
  DIMENSIONS(<dim1>, <dim2>, ...)
)
```

**Rules:**
1. Use `SEMANTIC_VIEW()` function - NOT `SELECT * FROM view_name`
2. Specify either METRICS or FACTS (cannot mix both)
3. Specify DIMENSIONS you want
4. Use wildcards (`*`) to get all: `METRICS(*)`, `DIMENSIONS(*)`
5. Fully qualify the view name with the database and schema names

**Examples:**

```sql
-- ❌ WRONG - Regular SELECT doesn't work with semantic views
SELECT * FROM SV_ARR_REPORTING LIMIT 5;
-- Error: Semantic views require SEMANTIC_VIEW() function

-- ✅ CORRECT - Preview data with wildcards
SELECT * FROM SEMANTIC_VIEW(
  SV_ARR_REPORTING
  METRICS(*)
  DIMENSIONS(*)
) LIMIT 5;

-- ✅ CORRECT - Query specific metrics with dimensions
SELECT * FROM SEMANTIC_VIEW(
  demo_agents.marts.sv_monthly_revenue
  METRICS(total_revenue, unique_customers)
  DIMENSIONS(month, product_id, region)
  WHERE month >= '2024-01-01'
) LIMIT 5;

-- ✅ CORRECT - Query facts (row-level data)
SELECT * FROM SEMANTIC_VIEW(
  demo_agents.marts.sv_transactions
  FACTS(transaction_id, amount, customer_id)
  DIMENSIONS(transaction_date, region)
) LIMIT 100;

-- ✅ CORRECT - Use wildcards to explore all available data
SELECT * FROM SEMANTIC_VIEW(
  demo_agents.marts.sv_monthly_revenue
  METRICS(*)
  DIMENSIONS(month, region)
);
```

**Important Notes:**
- You need SELECT privilege on the semantic view itself (NOT the underlying tables)
- When pairing dimensions with metrics, the dimension must have equal or lower granularity than the metric
- Use `SHOW SEMANTIC DIMENSIONS FOR METRIC metric_name` to find compatible dimensions
- Column order in results follows: METRICS, DIMENSIONS, FACTS clause order
""".strip()

    def get_semantic_view_modification_hints(self) -> str:
        """Get hints for creating/modifying Snowflake semantic views."""
        return """
# Creating/Modifying Snowflake Semantic Views

## ⚠️ CRITICAL: Use dbt_semantic_view Package

**ALWAYS use the official `dbt_semantic_view` package from Snowflake Labs!**

Reference: https://docs.snowflake.com/en/user-guide/views-semantic/best-practices-dev#integration-with-dbt-projects

### Why this approach?
- ✅ Official Snowflake-supported dbt integration
- ✅ Native dbt materialization (not macros)
- ✅ Integrated with dbt lineage and documentation
- ✅ Version controlled in git automatically
- ✅ Deploy with standard `dbt build` or `dbt run`

### Workflow Overview

```
1. Install dbt_semantic_view package → 2. Create model with materialized='semantic_view' → 3. Deploy with dbt build
```

---

## Step 0: Install dbt_semantic_view Package (One-Time Setup)

### Add to packages.yml

Create or update `packages.yml` in dbt project root:

```yaml
packages:
  - package: Snowflake-Labs/dbt_semantic_view
    version: 1.0.3  # Use latest version
```

### Install the package

```bash
# Via dbt_cli tool:
dbt_cli('deps')

# Or via command line:
dbt deps
```

This installs the custom `semantic_view` materialization type.

### Configure in dbt_project.yml

Add semantic views configuration to `dbt_project.yml`:

```yaml
models:
  your_project_name:
    # ... other model configs ...
    
    semantic_views:
      +materialized: semantic_view
      +schema: semantic_views  # Optional: creates semantic views in separate schema
```

**What this does:**
- Tells dbt that models in `models/semantic_views/` folder use the custom materialization
- Optionally puts all semantic views in a dedicated schema (e.g., `analytics.semantic_views`)
- Allows you to omit `{{ config(materialized='semantic_view') }}` if you prefer (but recommended to keep it)

**Alternative: Configure per-folder**

If your project already has schema-specific folders (like `marts/product/`), you can organize semantic views there:

```yaml
models:
  your_project_name:
    marts:
      product:
        semantic_views:
          +materialized: semantic_view
          +schema: mart_product  # Put semantic views in same schema as marts
```

---

## Step 1: Create Semantic View Model
If the dbt project already has semantic views, use the existing folder structure to determine where to save the semantic views.
Otherwise, create a new folder structure in the dbt project:
    **File location:** `models/semantic_views/sv_<name>.sql` in the dbt project

**File structure:**
```sql
{{ config(materialized='semantic_view') }}

TABLES (
  -- Use short table aliases for readability
  orders AS {{ ref('fct_orders') }}
    PRIMARY KEY (order_id)
    WITH SYNONYMS = ('sales orders', 'order data')
    COMMENT = 'Order transactions',

  customers AS {{ ref('dim_customers') }}
    PRIMARY KEY (customer_id)
    WITH SYNONYMS = ('customers', 'accounts')
    COMMENT = 'Customer master data'
)
RELATIONSHIPS (
  -- Many-to-one: orders to customers
  orders (customer_id) REFERENCES customers
)
FACTS (
  -- Row-level fields (cannot combine with METRICS in queries)
  PUBLIC orders.order_id AS orders.order_id
    WITH SYNONYMS = ('order number', 'order identifier')
    COMMENT = 'Unique order identifier',

  PUBLIC orders.order_amount AS orders.amount
    WITH SYNONYMS = ('order value', 'order total')
    COMMENT = 'Order amount in USD'
)
DIMENSIONS (
  -- Identifiers
  orders.order_id AS orders.order_id
    COMMENT = 'Order identifier',

  customers.customer_id AS customers.customer_id
    WITH SYNONYMS = ('customer', 'account id')
    COMMENT = 'Customer identifier',

  -- Time dimensions from expressions
  orders.order_date AS DATE(orders.order_date)
    WITH SYNONYMS = ('date', 'order date')
    COMMENT = 'Date the order was placed',

  orders.order_month AS DATE_TRUNC('MONTH', orders.order_date)
    WITH SYNONYMS = ('month', 'order month')
    COMMENT = 'Month the order was placed',

  orders.order_year AS DATE_TRUNC('YEAR', orders.order_date)
    WITH SYNONYMS = ('year', 'order year')
    COMMENT = 'Year the order was placed',

  -- Attribute dimensions
  customers.customer_name AS customers.name
    WITH SYNONYMS = ('name', 'client name', 'account name')
    COMMENT = 'Customer full name',

  customers.customer_region AS customers.region
    WITH SYNONYMS = ('region', 'geography', 'location')
    COMMENT = 'Customer geographic region',

  -- Calculated dimensions
  orders.discounted_amount AS (orders.amount * (1 - orders.discount_rate))
    WITH SYNONYMS = ('net amount', 'discounted value')
    COMMENT = 'Order amount after discount'
)
METRICS (
  -- Count metrics
  PUBLIC orders.order_count AS COUNT(*)
    WITH SYNONYMS = ('count of orders', 'number of orders', 'order volume')
    COMMENT = 'Count of orders',

  PUBLIC orders.distinct_customers AS COUNT(DISTINCT orders.customer_id)
    WITH SYNONYMS = ('unique customers', 'customer count')
    COMMENT = 'Count of distinct customers',

  -- Sum metrics
  PUBLIC orders.total_revenue AS SUM(orders.amount)
    WITH SYNONYMS = ('revenue', 'sales', 'total sales')
    COMMENT = 'Total order revenue',

  PUBLIC orders.total_discounted_revenue AS SUM(orders.discounted_amount)
    WITH SYNONYMS = ('net revenue', 'discounted sales')
    COMMENT = 'Total revenue after discounts',

  -- Average metrics
  PUBLIC orders.avg_order_value AS AVG(orders.amount)
    WITH SYNONYMS = ('average order value', 'aov', 'mean order size')
    COMMENT = 'Average order amount',

  -- Min/Max metrics
  PUBLIC orders.max_order_value AS MAX(orders.amount)
    WITH SYNONYMS = ('largest order', 'max order')
    COMMENT = 'Maximum order amount',

  PUBLIC orders.min_order_value AS MIN(orders.amount)
    WITH SYNONYMS = ('smallest order', 'min order')
    COMMENT = 'Minimum order amount'
)
COMMENT = 'Order and customer analysis semantic view'
;
```

**Critical syntax rules:**
- **Config:** First line must be `{{ config(materialized='semantic_view') }}`
- **WITH SYNONYMS:** Must use equals sign: `WITH SYNONYMS = ('synonym1', 'synonym2')`
- **COMMENT:** Must use equals sign: `COMMENT = 'description'`
- **PUBLIC keyword:** Mark facts/metrics as `PUBLIC` for external visibility
- **Table aliases:** Short names make queries readable (`orders.field` not `fct_orders.field`)
- **Expressions:** Dimensions can use SQL functions: `DATE_TRUNC`, `YEAR`, calculations
- **References:** Use `{{ ref('model') }}` for dbt models, `{{ source('schema', 'table') }}` for sources
- **No CREATE:** The materialization generates the DDL automatically
- **Semicolon:** End with `;` (optional)

---

## Step 2: Deploy Semantic View via dbt CLI

**Use the `dbt_cli()` tool with standard dbt commands:**

```python
# Build specific semantic view
dbt_cli('build', ['--select', 'sv_revenue_analysis'])

# Build all semantic views
dbt_cli('build', ['--select', 'semantic_views/*'])

# Run all models including semantic views
dbt_cli('run')
```

**Benefits:**
- Uses standard dbt workflow (build/run/test)
- Automatically uses correct database/schema from dbt profile
- Shows in dbt lineage graphs
- Can add dbt tests to semantic views
- CI/CD friendly

---

## Step 3: Query Semantic View

After deployment, query using query_semantic_view tool

---

## Important: Understanding the `AS` Keyword

### ⚠️ `AS` Works BACKWARDS in Semantic Views

**In regular SQL:** `SELECT physical_column AS alias_name`
**In semantic views:** `table.semantic_name AS physical_column_or_expression`

**Think of `AS` as "IS DEFINED AS" not "RENAME TO":**
- **Left side:** The semantic name you're creating (what users will query)
- **Right side:** The physical column or SQL expression it maps to

**Examples:**
```sql
-- ❌ WRONG - This tries to create dimension 'geo' from column 'geo_region' (doesn't exist!)
orders.geo AS geo_region

-- ✅ CORRECT - Creates dimension 'geo_region' from physical column 'geo'
orders.geo_region AS geo

-- ✅ CORRECT - Creates dimension 'order_year' from YEAR expression
orders.order_year AS YEAR(order_date)

-- ✅ CORRECT - Creates metric 'total_revenue' using SUM aggregation
orders.total_revenue AS SUM(orders.amount)
```

---

## Complete Workflow Example

### User requests: "Create semantic view for monthly ARR analysis"

### Create dbt model: `models/semantic_views/sv_arr_monthly.sql`

```sql
{{ config(materialized='semantic_view') }}

TABLES (
  arr_facts AS {{ ref('fct_arr_reporting_monthly') }}
    PRIMARY KEY (arr_id)
    COMMENT = 'Monthly ARR facts',

  customers AS {{ ref('dim_customers') }}
    PRIMARY KEY (customer_id)
    COMMENT = 'Customer dimensions'
)
RELATIONSHIPS (
  arr_facts (customer_id) REFERENCES customers
)
DIMENSIONS (
  arr_facts.month AS arr_facts.month
    WITH SYNONYMS = ('reporting month', 'month')
    COMMENT = 'Reporting month',

  arr_facts.subscription_id AS arr_facts.subscription_id
    WITH SYNONYMS = ('subscription', 'sub id')
    COMMENT = 'Subscription identifier',

  customers.customer_name AS customers.name
    WITH SYNONYMS = ('client', 'account name', 'customer')
    COMMENT = 'Customer name',

  customers.region AS customers.region
    WITH SYNONYMS = ('geography', 'location')
    COMMENT = 'Customer region'
)
METRICS (
  PUBLIC arr_facts.total_arr AS SUM(arr_facts.arr)
    WITH SYNONYMS = ('recurring revenue', 'ARR', 'total ARR')
    COMMENT = 'Annual Recurring Revenue',

  PUBLIC arr_facts.customer_count AS COUNT(DISTINCT arr_facts.customer_id)
    WITH SYNONYMS = ('unique customers', 'customer base', 'distinct customers')
    COMMENT = 'Number of unique customers'
)
COMMENT = 'Monthly ARR analysis semantic view'
;
```

### Deploy with dbt

```python
# Build the semantic view
dbt_cli('build', ['--select', 'sv_arr_monthly'])

# Or build all semantic views
dbt_cli('build', ['--select', 'semantic_views/*'])
```

### Query the semantic view

```python
# Use the query_semantic_view tool (recommended)
query_semantic_view(
    view_name='sv_arr_monthly',
    database_name='analytics',
    schema_name='marts',
    measures=[
        {'table': 'arr_facts', 'name': 'total_arr'},
        {'table': 'arr_facts', 'name': 'customer_count'}
    ],
    dimensions=[
        {'table': 'arr_facts', 'name': 'month'},
        {'table': 'customers', 'name': 'region'}
    ],
    where_clause="arr_facts.month >= '2024-01-01'",
    order_by='arr_facts.month, customers.region'
)
```

---

## Key Rules

1. **Use dbt_semantic_view package** - Install it first with `dbt_cli('deps')`

2. **File location:** `models/semantic_views/sv_<name>.sql` (or match existing structure)

3. **First line:** Must be `{{ config(materialized='semantic_view') }}`

4. **Use {{ ref() }}:** Reference dbt models to maintain lineage

5. **Syntax:** Use `WITH SYNONYMS = (...)` and `COMMENT = '...'` with equals signs

6. **PUBLIC keyword:** Mark facts/metrics as PUBLIC for visibility

7. **Deploy:** Use `dbt_cli('build')` or `dbt_cli('run')`, not run-operation

8. **Test:** Validate with query_semantic_view tool after deployment

---

## Validation Checklist

Before deploying:
1. ✅ Installed dbt_semantic_view package via `dbt_cli('deps')`
2. ✅ All `{{ ref('model_name') }}` references exist in dbt project
3. ✅ Primary keys match actual model column names
4. ✅ Physical column names match what's in the models
5. ✅ Syntax uses `=` for WITH SYNONYMS and COMMENT
6. ✅ After deployment, query with `query_semantic_view()` tool to validate

---

## References
- Snowflake Semantic Views: https://docs.snowflake.com/en/user-guide/views-semantic/sql
- dbt Macros: https://docs.getdbt.com/docs/build/jinja-macros
- dbt Operations: https://docs.getdbt.com/reference/commands/run-operation
""".strip()

    def get_agent_hints(self, read_only: bool = True) -> str:
        """Get Snowflake-specific hints for AI agents writing SQL queries.

        Returns:
            Comprehensive Snowflake SQL dialect guide for agents
        """
        # Compose from specialized hint methods to avoid duplication
        # Note: Query hints excluded - agents use query_semantic_view tool which handles syntax
        general_hints = self.get_general_query_hints()
        if read_only:
            semantic_modification_hints = ""
        else:
            semantic_modification_hints = self.get_semantic_view_modification_hints()

        return f"""
## SNOWFLAKE SPECIFIC DATA BACKEND GUIDELINES

You are working with a **Snowflake** data warehouse.

---

{semantic_modification_hints}

---

{general_hints}

---

## Additional Resources

**Semantic Views:**
- Creating: https://docs.snowflake.com/en/user-guide/views-semantic/sql
- Validation Rules: https://docs.snowflake.com/user-guide/views-semantic/validation-rules
- Querying: https://docs.snowflake.com/en/user-guide/views-semantic/querying (use query_semantic_view tool instead)

**General Snowflake SQL:**
- SQL Reference: https://docs.snowflake.com/en/sql-reference
- Functions: https://docs.snowflake.com/en/sql-reference/functions-all
""".strip()

    def _is_table_allowed(self, database: str, schema: str, table: str) -> bool:
        """Check if a table is allowed based on configured restrictions.

        All comparisons are case-insensitive (Snowflake uses uppercase by default).

        Args:
            database: Database name to check
            schema: Schema name to check
            table: Table name to check

        Returns:
            True if table is allowed, False otherwise
        """
        # If no restrictions configured, allow all
        if not self.allowed_databases and not self.allowed_schemas and not self.allowed_table_patterns:
            return True

        # Check database (case-insensitive)
        if self.allowed_databases:
            allowed_db_upper = {db.upper() for db in self.allowed_databases}
            if database.upper() not in allowed_db_upper:
                return False

        # Check schema (case-insensitive)
        if self.allowed_schemas:
            allowed_schema_upper = {s.upper() for s in self.allowed_schemas}
            if schema.upper() not in allowed_schema_upper:
                return False

        # Check table patterns (case-insensitive using fnmatch)
        if self.allowed_table_patterns:
            table_upper = table.upper()
            patterns_upper = [p.upper() for p in self.allowed_table_patterns]
            if not any(fnmatch.fnmatch(table_upper, pattern) for pattern in patterns_upper):
                return False

        return True

    def _validate_table_access(self, database: str, schema: str, table: str) -> None:
        """Validate that a table is allowed to be accessed.

        Args:
            database: Database name
            schema: Schema name
            table: Table name

        Raises:
            PermissionError: If table access is not allowed
        """
        if not self._is_table_allowed(database, schema, table):
            raise PermissionError(
                f"Access denied to {database}.{schema}.{table}. "
                f"Allowed databases: {self.allowed_databases or 'all'}, "
                f"Allowed schemas: {self.allowed_schemas or 'all'}, "
                f"Allowed table patterns: {self.allowed_table_patterns or 'all'}. "
                f"If you need data from intermediate models, please create a data engineering ticket."
            )
