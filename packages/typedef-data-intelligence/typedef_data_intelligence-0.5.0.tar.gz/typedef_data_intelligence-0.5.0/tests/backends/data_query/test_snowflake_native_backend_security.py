"""Security regression tests for SnowflakeNativeBackend.

This file consolidates tests that ensure:
- Identifier interpolation is safely quoted in SHOW-based semantic methods
- String literal escaping is correct for GET_DDL and other literal contexts
- Schema/database argument validation prevents ambiguous/unscoped calls
- Table allowlist validation fails closed when SQL parsing fails
"""

# ruff: noqa: D103

import pytest
from lineage.backends.data_query.snowflake_native_backend import SnowflakeNativeBackend


def _backend_without_init() -> SnowflakeNativeBackend:
    """Create a backend instance without importing Snowflake connector in tests."""
    return SnowflakeNativeBackend.__new__(SnowflakeNativeBackend)


def _set_no_restrictions(backend: SnowflakeNativeBackend) -> None:
    backend.allowed_databases = []  # type: ignore[attr-defined]
    backend.allowed_schemas = []  # type: ignore[attr-defined]
    backend.allowed_table_patterns = []  # type: ignore[attr-defined]


def _set_none_restrictions(backend: SnowflakeNativeBackend) -> None:
    """Simulate 'no restrictions configured' (None-style) for older callers."""
    backend.allowed_databases = None  # type: ignore[attr-defined]
    backend.allowed_schemas = None  # type: ignore[attr-defined]
    backend.allowed_table_patterns = None  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Argument validation + string literal escaping
# ---------------------------------------------------------------------------


def test_require_database_when_schema_provided_errors() -> None:
    """schema_name without database_name should error (avoid ambiguity + unscoped SHOW)."""
    with pytest.raises(ValueError, match="schema_name requires database_name"):
        SnowflakeNativeBackend._require_database_when_schema_provided(
            object(),
            database_name=None,
            schema_name="ANALYTICS",
        )


def test_require_database_when_schema_provided_allows_database_only() -> None:
    """database_name without schema_name is OK."""
    SnowflakeNativeBackend._require_database_when_schema_provided(
        object(),
        database_name="DB1",
        schema_name=None,
    )


def test_require_database_when_schema_provided_allows_database_and_schema() -> None:
    """database_name + schema_name is OK."""
    SnowflakeNativeBackend._require_database_when_schema_provided(
        object(),
        database_name="DB1",
        schema_name="SC1",
    )


def test_escape_snowflake_string_literal_escapes_single_quotes() -> None:
    """Single quotes must be doubled to prevent SQL injection in Snowflake SQL string literals."""
    assert SnowflakeNativeBackend._escape_snowflake_string_literal(None) == ""
    assert SnowflakeNativeBackend._escape_snowflake_string_literal("simple") == "simple"
    assert SnowflakeNativeBackend._escape_snowflake_string_literal("test'") == "test''"
    assert (
        SnowflakeNativeBackend._escape_snowflake_string_literal("foo'; DROP TABLE users; --")
        == "foo''; DROP TABLE users; --"
    )
    assert (
        SnowflakeNativeBackend._escape_snowflake_string_literal("It's a test")
        == "It''s a test"
    )
    assert SnowflakeNativeBackend._escape_snowflake_string_literal("O'Reilly") == "O''Reilly"
    assert SnowflakeNativeBackend._escape_snowflake_string_literal("'test'") == "''test''"


@pytest.mark.asyncio
async def test_get_semantic_view_ddl_escapes_qualified_name_to_prevent_sql_injection() -> None:
    """Ensure view_name cannot break out of GET_DDL string literal via quotes."""
    from lineage.backends.data_query.protocol import QueryResult

    backend = _backend_without_init()

    captured: dict[str, str] = {}

    async def _ensure_connected() -> None:
        return None

    def _validate_schema_access(_database_name: str, _schema_name: str) -> None:
        return None

    async def execute_query(query: str, **_kwargs) -> QueryResult:
        captured["query"] = query
        return QueryResult(columns=["ddl"], rows=[("ddl",)], row_count=1)

    backend._ensure_connected = _ensure_connected  # type: ignore[attr-defined]
    backend._validate_schema_access = _validate_schema_access  # type: ignore[attr-defined]
    backend.execute_query = execute_query  # type: ignore[attr-defined]

    malicious_view_name = "test'); DROP TABLE users; --"
    ddl = await backend.get_semantic_view_ddl("DB", "SCHEMA", malicious_view_name)
    assert ddl == "ddl"

    query = captured["query"]
    assert "GET_DDL('SEMANTIC_VIEW'," in query
    # Unquoted identifiers are uppercased by Snowflake normalization
    assert "test'); DROP TABLE users; --" not in query
    assert "DB.SCHEMA.TEST''); DROP TABLE USERS; --" in query


# ---------------------------------------------------------------------------
# SHOW semantic methods: identifier quoting (database/schema/view)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_semantic_views_quotes_database_and_schema_identifiers() -> None:
    from lineage.backends.data_query.protocol import QueryResult

    backend = _backend_without_init()
    _set_none_restrictions(backend)

    captured: dict[str, str] = {}

    async def _ensure_connected() -> None:
        return None

    def _validate_schema_access(_database_name: str, _schema_name: str) -> None:
        return None

    async def execute_query(query: str, **_kwargs) -> QueryResult:
        captured["query"] = query
        return QueryResult(
            columns=["created_on", "name", "database_name", "schema_name", "owner", "comment"],
            rows=[(None, "SV", "DB", "SCHEMA", None, None)],
            row_count=1,
        )

    backend._ensure_connected = _ensure_connected  # type: ignore[attr-defined]
    backend._validate_schema_access = _validate_schema_access  # type: ignore[attr-defined]
    backend.execute_query = execute_query  # type: ignore[attr-defined]

    db = 'DB"; DROP TABLE users; --'
    schema = "SCHEMA"
    await backend.list_semantic_views(database_name=db, schema_name=schema)

    query = captured["query"]
    # Unquoted identifiers are uppercased by Snowflake normalization
    assert 'IN SCHEMA "DB""; DROP TABLE USERS; --"."SCHEMA"' in query
    assert 'IN SCHEMA DB"; DROP TABLE users; --.SCHEMA' not in query
    assert 'DB""; DROP TABLE USERS; --' in query


@pytest.mark.asyncio
async def test_show_semantic_metrics_quotes_database_schema_and_view_identifiers() -> None:
    from lineage.backends.data_query.protocol import QueryResult

    backend = _backend_without_init()
    _set_none_restrictions(backend)

    captured: dict[str, str] = {}

    async def _ensure_connected() -> None:
        return None

    def _validate_schema_access(_database_name: str, _schema_name: str) -> None:
        return None

    async def execute_query(query: str, **_kwargs) -> QueryResult:
        captured["query"] = query
        return QueryResult(columns=["x"], rows=[], row_count=0)

    backend._ensure_connected = _ensure_connected  # type: ignore[attr-defined]
    backend._validate_schema_access = _validate_schema_access  # type: ignore[attr-defined]
    backend.execute_query = execute_query  # type: ignore[attr-defined]

    db = 'DB"; DROP TABLE users; --'
    schema = "SCHEMA"
    view = 'SV"; SELECT 1; --'
    await backend.show_semantic_metrics(database_name=db, schema_name=schema, view_name=view)

    query = captured["query"]
    # Unquoted identifiers are uppercased by Snowflake normalization
    assert 'IN "DB""; DROP TABLE USERS; --"."SCHEMA"."SV""; SELECT 1; --"' in query
    assert 'SV"; SELECT 1; --' not in query
    assert 'SV""; SELECT 1; --' in query


@pytest.mark.asyncio
async def test_show_semantic_dimensions_quotes_database_schema_and_view_identifiers() -> None:
    from lineage.backends.data_query.protocol import QueryResult

    backend = _backend_without_init()
    _set_none_restrictions(backend)

    captured: dict[str, str] = {}

    async def _ensure_connected() -> None:
        return None

    def _validate_schema_access(_database_name: str, _schema_name: str) -> None:
        return None

    async def execute_query(query: str, **_kwargs) -> QueryResult:
        captured["query"] = query
        return QueryResult(columns=["x"], rows=[], row_count=0)

    backend._ensure_connected = _ensure_connected  # type: ignore[attr-defined]
    backend._validate_schema_access = _validate_schema_access  # type: ignore[attr-defined]
    backend.execute_query = execute_query  # type: ignore[attr-defined]

    db = "DB"
    schema = 'SCHEMA"; DROP TABLE users; --'
    view = "SV"
    await backend.show_semantic_dimensions(database_name=db, schema_name=schema, view_name=view)

    query = captured["query"]
    # Unquoted identifiers are uppercased by Snowflake normalization
    assert 'IN "DB"."SCHEMA""; DROP TABLE USERS; --"."SV"' in query
    assert 'SCHEMA"; DROP TABLE users; --' not in query


@pytest.mark.asyncio
async def test_show_semantic_facts_quotes_database_schema_and_view_identifiers() -> None:
    from lineage.backends.data_query.protocol import QueryResult

    backend = _backend_without_init()
    _set_none_restrictions(backend)

    captured: dict[str, str] = {}

    async def _ensure_connected() -> None:
        return None

    def _validate_schema_access(_database_name: str, _schema_name: str) -> None:
        return None

    async def execute_query(query: str, **_kwargs) -> QueryResult:
        captured["query"] = query
        return QueryResult(columns=["x"], rows=[], row_count=0)

    backend._ensure_connected = _ensure_connected  # type: ignore[attr-defined]
    backend._validate_schema_access = _validate_schema_access  # type: ignore[attr-defined]
    backend.execute_query = execute_query  # type: ignore[attr-defined]

    db = "DB"
    schema = "SCHEMA"
    view = 'SV"; DROP TABLE users; --'
    await backend.show_semantic_facts(database_name=db, schema_name=schema, view_name=view)

    query = captured["query"]
    # Unquoted identifiers are uppercased by Snowflake normalization
    assert 'IN "DB"."SCHEMA"."SV""; DROP TABLE USERS; --"' in query
    assert 'SV"; DROP TABLE users; --' not in query


# ---------------------------------------------------------------------------
# Table allowlist validation: fail closed on parse errors
# ---------------------------------------------------------------------------


def test_table_access_validation_fails_closed_when_sqlglot_cannot_parse(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If allowlists are configured, an un-parseable query must be blocked."""
    from lineage.backends.data_query import snowflake_native_backend as mod

    backend = _backend_without_init()
    backend.allowed_databases = ["DB1"]  # type: ignore[attr-defined]
    backend.allowed_schemas = []  # type: ignore[attr-defined]
    backend.allowed_table_patterns = []  # type: ignore[attr-defined]

    class _Cfg:
        database = "DB1"
        schema_name = "SC1"

    backend.config = _Cfg()  # type: ignore[attr-defined]

    def _boom(*_args, **_kwargs):
        raise mod.sqlglot.errors.ParseError("boom")

    monkeypatch.setattr(mod.sqlglot, "parse", _boom)

    with pytest.raises(PermissionError, match="Could not parse SQL to validate table access"):
        backend._extract_and_validate_tables_from_query(  # type: ignore[attr-defined]
            "SELECT * FROM DB1.SC1.SECRET_TABLE"
        )


def test_table_access_validation_does_not_block_when_no_restrictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """If no allowlists are configured, validation is skipped (no parse required)."""
    from lineage.backends.data_query import snowflake_native_backend as mod

    backend = _backend_without_init()
    _set_no_restrictions(backend)

    def _boom(*_args, **_kwargs):
        raise mod.sqlglot.errors.ParseError("boom")

    monkeypatch.setattr(mod.sqlglot, "parse", _boom)

    backend._extract_and_validate_tables_from_query("SELECT 1")  # type: ignore[attr-defined]


