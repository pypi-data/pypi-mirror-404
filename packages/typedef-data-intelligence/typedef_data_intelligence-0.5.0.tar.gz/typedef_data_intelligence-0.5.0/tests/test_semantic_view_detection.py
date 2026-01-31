"""Tests for semantic view detection in SnowflakeNativeBackend."""
import pytest


def _backend_without_init():
    # Avoid Snowflake connector dependency in unit tests by bypassing __init__.
    from lineage.backends.data_query.snowflake_native_backend import (
        SnowflakeNativeBackend,
    )

    return SnowflakeNativeBackend.__new__(SnowflakeNativeBackend)


@pytest.mark.parametrize(
    "query",
    [
        "SELECT * FROM SV_METRICS",
        "SELECT * FROM other_table JOIN SV_METRICS ON other_table.id = SV_METRICS.id",
        "SELECT * FROM other_table JOIN sv_metrics ON other_table.id = sv_metrics.id",
        "SELECT * FROM DB.MARTS.SV_METRICS",
        "SELECT * FROM other_table JOIN DB.MARTS.SV_METRICS ON 1=1",
        # Comma-separated FROM list should be caught by sqlglot path
        "SELECT * FROM other_table, SV_METRICS",
        # Nested usage should be caught
        "WITH x AS (SELECT * FROM other_table JOIN sv_metrics ON 1=1) SELECT * FROM x",
    ],
)
def test_detects_semantic_views_in_from_and_join(query: str) -> None:
    """Test that semantic views are detected in FROM and JOIN clauses."""
    backend = _backend_without_init()
    assert backend._detect_semantic_view_in_query(query) is True


@pytest.mark.parametrize(
    "query",
    [
        # Allowed: semantic views must be queried via SEMANTIC_VIEW() function
        "SELECT * FROM TABLE(SEMANTIC_VIEW('SV_METRICS'))",
        "SELECT * FROM TABLE(SEMANTIC_VIEW('db.marts.sv_metrics'))",
        # Non-semantic tables should not be flagged
        "SELECT * FROM some_table JOIN other_table ON 1=1",
        "WITH x AS (SELECT * FROM some_table) SELECT * FROM x",
    ],
)
def test_allows_semantic_view_function_and_non_semantic_tables(query: str) -> None:
    """Test that semantic views are allowed when queried via SEMANTIC_VIEW() function."""
    backend = _backend_without_init()
    assert backend._detect_semantic_view_in_query(query) is False


