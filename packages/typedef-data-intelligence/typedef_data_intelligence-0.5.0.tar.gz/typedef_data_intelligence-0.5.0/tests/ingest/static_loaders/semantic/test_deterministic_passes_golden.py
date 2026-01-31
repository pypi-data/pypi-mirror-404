"""Golden tests for deterministic semantic passes (hermetic SQL fixtures)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pytest
from lineage.devtools.semantic_goldens import (
    fixture_dialect,
    fixture_schema,
    list_sql_fixtures,
    normalize_semantic_payload,
    read_expected,
    read_sql_fixture,
)
from lineage.ingest.static_loaders.semantic.deterministic.executor import (
    DeterministicExecutor,
)


def _deterministic_payload(fixture_name: str, *, dialect: str = "duckdb") -> Dict[str, Any]:
    sql = read_sql_fixture(fixture_name)
    schema = fixture_schema(fixture_name)
    det = DeterministicExecutor(schema=schema).run_all_passes(sql, dialect)
    assert det.parse_error is None, det.parse_error

    grouping_outer: Optional[Dict[str, Any]] = None
    if det.grouping_by_scope and "outer" in det.grouping_by_scope:
        grouping_outer = det.grouping_by_scope["outer"].model_dump()

    payload: Dict[str, Any] = {
        "fixture": fixture_name,
        "dialect": dialect,
        "deterministic": {
            "relation_analysis": det.relation_analysis.model_dump() if det.relation_analysis else None,
            "column_analysis": det.column_analysis.model_dump() if det.column_analysis else None,
            "join_analysis": det.join_analysis.model_dump() if det.join_analysis else None,
            "filter_analysis": det.filter_analysis.model_dump() if det.filter_analysis else None,
            "grouping_outer": grouping_outer,
            "window_outer": det.window_by_scope["outer"].model_dump()
            if det.window_by_scope and "outer" in det.window_by_scope
            else None,
            "output_outer": det.output_by_scope["outer"].model_dump()
            if det.output_by_scope and "outer" in det.output_by_scope
            else None,
        },
    }

    return normalize_semantic_payload(payload)


@pytest.mark.parametrize("fixture_name", list_sql_fixtures())
def test_deterministic_golden(fixture_name: str) -> None:
    """Deterministic pass outputs should match committed golden JSON."""
    expected = read_expected(fixture_name)
    actual = _deterministic_payload(fixture_name, dialect=fixture_dialect(fixture_name))

    # Compare only deterministic portion; heuristics are tested separately.
    assert actual["deterministic"] == expected["deterministic"]


