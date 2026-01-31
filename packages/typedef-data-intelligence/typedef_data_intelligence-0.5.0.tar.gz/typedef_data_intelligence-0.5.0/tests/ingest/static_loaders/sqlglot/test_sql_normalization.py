"""Tests for SQL normalization functions.

Covers:
- canonicalize_sql (catalog stripping)
- qualify_sql (catalog preservation)
- normalize_sql_pair (single-pass dual output)
- Case sensitivity with SqlglotSchema for Snowflake/DuckDB
"""

from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import (
    NormalizedSQLPair,
    canonicalize_sql,
    normalize_sql_pair,
    qualify_sql,
)
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema, TableEntry


def _make_schema(
    database: str, schema: str, table: str, columns: dict[str, str]
) -> SqlglotSchema:
    """Helper to build a SqlglotSchema from a single table."""
    entry = TableEntry(
        database=database,
        schema=schema,
        table=table,
        columns=tuple(columns.items()),
    )
    return SqlglotSchema(_entries=(entry,))


# ============================================================================
# canonicalize_sql tests
# ============================================================================


class TestCanonicalizeSql:
    """Tests for canonicalize_sql (physically-agnostic SQL)."""

    def test_canonical_strips_catalog(self) -> None:
        """canonicalize_sql should remove database/catalog qualifiers."""
        sql = "SELECT id FROM my_db.my_schema.my_table"
        result = canonicalize_sql(sql, dialect="duckdb")
        # Database qualifier should be stripped
        assert "my_db" not in result
        # Schema and table should remain
        assert "my_schema" in result
        assert "my_table" in result

    def test_canonical_preserves_schema(self) -> None:
        """canonicalize_sql should preserve schema qualifiers."""
        sql = "SELECT id FROM my_schema.my_table"
        result = canonicalize_sql(sql, dialect="duckdb")
        assert "my_schema" in result
        assert "my_table" in result


# ============================================================================
# qualify_sql tests
# ============================================================================


class TestQualifySql:
    """Tests for qualify_sql (fully-qualified physical SQL)."""

    def test_qualified_preserves_catalog(self) -> None:
        """qualify_sql should keep database/catalog qualifiers."""
        sql = "SELECT id FROM my_db.my_schema.my_table"
        result = qualify_sql(sql, dialect="duckdb")
        # Database qualifier should be preserved
        assert "my_db" in result
        assert "my_schema" in result
        assert "my_table" in result


# ============================================================================
# normalize_sql_pair tests
# ============================================================================


class TestNormalizeSqlPair:
    """Tests for normalize_sql_pair (single-pass dual output)."""

    def test_pair_returns_dataclass(self) -> None:
        """normalize_sql_pair should return a NormalizedSQLPair."""
        result = normalize_sql_pair("SELECT 1", dialect="duckdb")
        assert isinstance(result, NormalizedSQLPair)
        assert result.qualified is not None
        assert result.canonical is not None

    def test_pair_matches_individual_calls(self) -> None:
        """normalize_sql_pair results should match separate qualify_sql + canonicalize_sql calls."""
        sql = "SELECT id FROM my_db.my_schema.my_table WHERE id > 1"
        dialect = "duckdb"

        pair = normalize_sql_pair(sql, dialect=dialect)
        individual_qualified = qualify_sql(sql, dialect=dialect)
        individual_canonical = canonicalize_sql(sql, dialect=dialect)

        assert pair.qualified == individual_qualified
        assert pair.canonical == individual_canonical

    def test_pair_no_schema(self) -> None:
        """normalize_sql_pair should work without schema argument."""
        result = normalize_sql_pair("SELECT 1 AS x", dialect="duckdb")
        assert isinstance(result, NormalizedSQLPair)
        assert "1" in result.qualified
        assert "1" in result.canonical

    def test_pair_with_schema(self) -> None:
        """normalize_sql_pair should expand SELECT * when schema is provided."""
        schema = _make_schema("my_db", "my_schema", "my_table", {"id": "INT", "name": "VARCHAR"})
        sql = "SELECT * FROM my_db.my_schema.my_table"

        pair = normalize_sql_pair(sql, dialect="duckdb", schema=schema)

        # Both forms should have expanded the star
        assert "id" in pair.qualified.lower() or "*" not in pair.qualified
        assert "id" in pair.canonical.lower() or "*" not in pair.canonical

    def test_pair_canonical_strips_catalog(self) -> None:
        """The canonical form should strip catalogs while qualified preserves them."""
        sql = "SELECT id FROM my_db.my_schema.my_table"
        pair = normalize_sql_pair(sql, dialect="duckdb")

        # Qualified should have catalog
        assert "my_db" in pair.qualified
        # Canonical should not
        assert "my_db" not in pair.canonical
        # Both should have schema
        assert "my_schema" in pair.qualified
        assert "my_schema" in pair.canonical


# ============================================================================
# Case sensitivity tests (C1)
# ============================================================================


class TestCaseSensitivity:
    """Tests for dialect-specific case handling in schema lookup."""

    def test_snowflake_uppercase_schema_lookup(self) -> None:
        """Snowflake convention: uppercase identifiers should resolve via qualify_sql."""
        schema = _make_schema(
            "MY_DB", "MY_SCHEMA", "MY_TABLE",
            {"ID": "NUMBER", "NAME": "VARCHAR"},
        )
        sql = "SELECT * FROM MY_DB.MY_SCHEMA.MY_TABLE"
        result = qualify_sql(sql, dialect="snowflake", schema=schema)

        # Columns should be resolved (star expanded)
        result_upper = result.upper()
        assert "ID" in result_upper
        assert "NAME" in result_upper

    def test_duckdb_lowercase_schema_lookup(self) -> None:
        """DuckDB convention: lowercase identifiers should resolve via qualify_sql."""
        schema = _make_schema(
            "my_db", "my_schema", "my_table",
            {"id": "INTEGER", "name": "VARCHAR"},
        )
        sql = "SELECT * FROM my_db.my_schema.my_table"
        result = qualify_sql(sql, dialect="duckdb", schema=schema)

        # Columns should be resolved (star expanded)
        result_lower = result.lower()
        assert "id" in result_lower
        assert "name" in result_lower
