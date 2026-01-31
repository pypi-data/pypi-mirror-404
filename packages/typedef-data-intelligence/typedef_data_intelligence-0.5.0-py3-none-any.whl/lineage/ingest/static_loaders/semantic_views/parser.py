"""SQL parsing utilities for extracting table references from view definitions."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional, Set

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError


@dataclass(frozen=True)
class TableReference:
    """Represents a table reference extracted from SQL."""
    table: str
    schema: Optional[str] = None
    database: Optional[str] = None

    @property
    def qualified_name(self) -> str:
        """Get fully qualified table name."""
        parts = []
        if self.database:
            parts.append(self.database)
        if self.schema:
            parts.append(self.schema)
        parts.append(self.table)
        return ".".join(parts)


@lru_cache(maxsize=256)
def _parse_sql(sql: str, dialect: Optional[str]) -> exp.Expression:
    """Parse SQL with caching."""
    return sqlglot.parse_one(sql, read=dialect)


def extract_table_references(
    sql: str,
    dialect: str = "snowflake",
    default_database: Optional[str] = None,
    default_schema: Optional[str] = None,
) -> Set[TableReference]:
    """Extract all table references from a SQL query.

    This function uses sqlglot to parse the SQL and extract all table
    references (FROM, JOIN, etc.). It's simpler than the full column-level
    lineage extraction in sqlglot_lineage.py - we only need table names.

    Args:
        sql: SQL query to parse
        dialect: SQL dialect (default: snowflake)
        default_database: Default database for unqualified table names
        default_schema: Default schema for unqualified table names

    Returns:
        Set of TableReference objects

    Example:
        >>> sql = "SELECT * FROM db1.schema1.table1 JOIN schema2.table2"
        >>> refs = extract_table_references(sql, default_database="db1")
        >>> sorted([r.qualified_name for r in refs])
        ['db1.schema1.table1', 'db1.schema2.table2']
    """
    tables = set()

    try:
        expression = _parse_sql(sql, dialect)
    except SqlglotError:
        # If parsing fails, return empty set
        # This is resilient to malformed SQL
        return tables

    # Find all Table nodes in the AST
    for table_node in expression.find_all(exp.Table):
        # Extract table parts from the node
        # sqlglot represents tables as catalog.db.table
        # but we use database.schema.table
        table_name = table_node.name
        schema = table_node.db if hasattr(table_node, "db") and table_node.db else None
        database = table_node.catalog if hasattr(table_node, "catalog") and table_node.catalog else None

        # Apply defaults if parts are missing
        if not database and default_database:
            database = default_database
        if not schema and default_schema:
            schema = default_schema

        if table_name:
            tables.add(TableReference(
                table=table_name,
                schema=schema,
                database=database,
            ))

    return tables


def normalize_table_reference(
    ref: TableReference,
    case_sensitive: bool = False,
) -> str:
    """Normalize a table reference for matching.

    Args:
        ref: TableReference to normalize
        case_sensitive: Whether to preserve case (default: False for Snowflake)

    Returns:
        Normalized qualified name

    Example:
        >>> ref = TableReference(table="MyTable", schema="MySchema", database="MyDB")
        >>> normalize_table_reference(ref)
        'mydb.myschema.mytable'
    """
    if case_sensitive:
        return ref.qualified_name
    else:
        # Snowflake is case-insensitive, normalize to lowercase
        parts = []
        if ref.database:
            parts.append(ref.database.lower())
        if ref.schema:
            parts.append(ref.schema.lower())
        parts.append(ref.table.lower())
        return ".".join(parts)
