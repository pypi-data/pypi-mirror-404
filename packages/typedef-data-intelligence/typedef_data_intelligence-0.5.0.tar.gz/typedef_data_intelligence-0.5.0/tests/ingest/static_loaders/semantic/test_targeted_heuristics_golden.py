"""Golden tests for heuristic targeted classification (hermetic SQL fixtures).

Note: PII detection has been merged into column_classification.
The semantic result now contains pii_columns and high_risk_pii_count fields.
"""

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
from lineage.ingest.static_loaders.semantic.deterministic.targeted.column_classification import (
    heuristic_column_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.incremental_watermark import (
    heuristic_watermark_classification,
)
from lineage.ingest.static_loaders.semantic.deterministic.targeted.time_classification import (
    heuristic_time_classification,
)


def _heuristics_payload(fixture_name: str, *, dialect: str = "duckdb") -> Dict[str, Any]:
    sql = read_sql_fixture(fixture_name)
    schema = fixture_schema(fixture_name)
    det = DeterministicExecutor(schema=schema).run_all_passes(sql, dialect)
    assert det.parse_error is None, det.parse_error

    grouping_outer: Optional[Dict[str, Any]] = None
    if det.grouping_by_scope and "outer" in det.grouping_by_scope:
        grouping_outer = det.grouping_by_scope["outer"].model_dump()

    filter_dict: Dict[str, Any] = det.filter_analysis.model_dump() if det.filter_analysis else {}
    relation_dict: Dict[str, Any] = (
        det.relation_analysis.model_dump() if det.relation_analysis else {}
    )

    time_result = heuristic_time_classification(grouping_outer or {}, filter_dict)
    # Column classification now includes PII detection (pii_columns, high_risk_pii_count)
    column_result = heuristic_column_classification(grouping_outer or {}, relation_dict)
    watermark_result = heuristic_watermark_classification(filter_dict)

    payload: Dict[str, Any] = {
        "fixture": fixture_name,
        "dialect": dialect,
        "heuristics": {
            "time": time_result.model_dump(),
            "semantic": column_result.model_dump(),  # Now includes PII fields
            "watermark": watermark_result.model_dump(),
        },
    }
    return normalize_semantic_payload(payload)


@pytest.mark.parametrize("fixture_name", list_sql_fixtures())
def test_targeted_heuristics_golden(fixture_name: str) -> None:
    """Heuristic targeted classification outputs should match committed goldens."""
    expected = read_expected(fixture_name)
    actual = _heuristics_payload(fixture_name, dialect=fixture_dialect(fixture_name))

    assert actual["heuristics"] == expected["heuristics"]


