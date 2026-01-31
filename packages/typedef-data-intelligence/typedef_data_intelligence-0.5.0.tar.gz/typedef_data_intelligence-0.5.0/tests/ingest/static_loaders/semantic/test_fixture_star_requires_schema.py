"""Fixture meta enforcement tests (hermetic).

Rule: if a SQL fixture selects a star in its SELECT list (e.g. `SELECT *`, `t.*`,
`* EXCLUDE (...)`), the fixture must provide a schema via `*.meta.json`.

Why: star expansion / qualification needs a schema; without it, deterministic
analysis and heuristics can become unstable or misleading.
"""

from __future__ import annotations

import pytest
from lineage.devtools.semantic_goldens import (
    fixture_dialect,
    fixture_schema,
    list_sql_fixtures,
    read_fixture_meta,
    read_sql_fixture,
)
from lineage.ingest.static_loaders.sqlglot.sqlglot_lineage import parse_sql_cached
from sqlglot import exp


def _select_has_output_star(select: exp.Select) -> bool:
    """Return True if the SELECT list contains a star expression."""
    for e in select.expressions:
        if isinstance(e, exp.Star):
            return True
        if isinstance(e, exp.Alias) and isinstance(e.this, exp.Star):
            return True
        # e.g. table.* may appear as Column with name == "*"
        if isinstance(e, exp.Column) and (e.name or "") == "*":
            return True
    return False


@pytest.mark.parametrize("fixture_name", list_sql_fixtures())
def test_fixture_star_select_requires_schema(fixture_name: str) -> None:
    sql = read_sql_fixture(fixture_name)
    dialect = fixture_dialect(fixture_name)
    ast = parse_sql_cached(sql, dialect=dialect)

    has_star = any(_select_has_output_star(s) for s in ast.find_all(exp.Select))
    if not has_star:
        return

    meta = read_fixture_meta(fixture_name)
    if meta.get("allow_star_without_schema") is True:
        return

    schema = fixture_schema(fixture_name)
    assert schema is not None, (
        f"{fixture_name} selects a star in the SELECT list but has no schema. "
        f"Add `{fixture_name}.meta.json` with a `schema` block."
    )


