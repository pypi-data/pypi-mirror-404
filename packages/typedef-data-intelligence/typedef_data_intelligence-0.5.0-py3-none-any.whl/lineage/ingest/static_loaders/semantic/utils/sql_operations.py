"""SQL operations and canonicalization utilities."""

from typing import Callable, Optional

from fenic.api.functions import udf
from fenic.core.types import StringType

from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    canonicalize_sql as _canonicalize_sql,
)
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema


def create_schema_aware_canonicalize_udf(
    schema: Optional[SqlglotSchema] = None,
) -> Callable[[str, str], str]:
    """Create a Fenic UDF for SQL canonicalization with optional schema.

    The schema is captured in a closure, enabling parallel execution via Polars
    while having access to the full schema for SELECT * expansion.

    Args:
        schema: SqlglotSchema instance for SELECT * expansion and column qualification.

    Returns:
        A Fenic UDF function that can be used with df.with_column()

    Example:
        schema = artifacts.sqlglot_schema()
        canonicalize_udf = create_schema_aware_canonicalize_udf(schema)
        df = df.with_column("canonical_sql", canonicalize_udf(fc.col("sql"), fc.lit("snowflake")))
    """
    # Capture schema in closure
    captured_schema = schema

    @udf(return_type=StringType)
    def canonicalize_with_schema(sql: str, dialect: str = "hive") -> str:
        """Produce clean, physically-agnostic SQL with schema-aware qualification."""
        try:
            return _canonicalize_sql(sql, dialect=dialect, schema=captured_schema)
        except Exception as e:
            # Return original SQL with error comment if parsing fails
            return f"-- Error canonicalizing: {str(e)}\n{sql}"

    return canonicalize_with_schema


# Default UDF without schema (for backwards compatibility)
@udf(return_type=StringType)
def canonicalize_sql_udf(sql: str, dialect: str = "hive") -> str:
    """Fenic UDF for producing agnostic SQL (without schema)."""
    try:
        return _canonicalize_sql(sql, dialect=dialect, schema=None)
    except Exception as e:
        # Return original SQL with error comment if parsing fails
        return f"-- Error canonicalizing: {str(e)}\n{sql}"
