"""Pass 1 (relations) contract tests."""

from __future__ import annotations

from lineage.ingest.static_loaders.semantic.models import RelationAnalysis, RelationUse

from .helpers import run_relations


def _find_relation(
    rel: RelationAnalysis, *, alias: str, scope: str, kind: str | None = None
) -> RelationUse | None:
    """Find a relation occurrence by alias+scope (and optionally kind)."""
    for r in rel.relations:
        if r.alias == alias and r.scope == scope and (kind is None or r.kind == kind):
            return r
    return None


def test_pass_01_relations_scopes_cte_and_subquery() -> None:
    """Scopes should distinguish outer vs CTE body vs subquery alias contexts."""
    sql = """
    WITH c AS (SELECT * FROM a)
    SELECT *
    FROM c
    JOIN (SELECT * FROM b) s ON 1=1
    """
    rel = run_relations(sql)

    assert rel.cte_defs == ["c"]

    # Table inside the CTE body.
    assert _find_relation(rel, alias="a", scope="cte:c", kind="table") is not None

    # CTE reference in outer scope.
    assert _find_relation(rel, alias="c", scope="outer", kind="cte") is not None

    # Subquery alias itself lives in outer scope.
    assert _find_relation(rel, alias="s", scope="outer", kind="subquery") is not None

    assert rel.from_clause_order == ["c", "s"]
    assert rel.driving_relations == ["c"]


def test_pass_01_relations_from_clause_order_and_driving_relation() -> None:
    """FROM/JOIN order should be stable and define driving relation."""
    sql = """
    SELECT *
    FROM a aa
    JOIN b bb ON aa.id = bb.id
    LEFT JOIN c cc ON bb.id = cc.id
    """
    rel = run_relations(sql)

    assert rel.from_clause_order == ["aa", "bb", "cc"]
    assert rel.driving_relations == ["aa"]

