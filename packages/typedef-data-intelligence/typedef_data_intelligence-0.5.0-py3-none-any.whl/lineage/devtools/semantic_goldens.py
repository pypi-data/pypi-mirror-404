"""Helpers for hermetic SQL fixtures + golden snapshots.

This module supports deterministic + heuristic goldens stored in
`tests/fixtures/semantic_expected/`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple


def _project_root() -> Path:
    """Return the typedef_data_intelligence project root directory."""
    # .../typedef_data_intelligence/src/lineage/devtools/semantic_goldens.py
    return Path(__file__).resolve().parents[3]


FIXTURES_DIR = _project_root() / "tests" / "fixtures" / "semantic_sql"
EXPECTED_DIR = _project_root() / "tests" / "fixtures" / "semantic_expected"


def read_fixture_meta(name: str) -> Dict[str, Any]:
    """Read optional fixture metadata.

    If present, it should be located alongside the SQL fixture as:
      `<name>.meta.json`
    """
    meta_path = FIXTURES_DIR / f"{name}.meta.json"
    if not meta_path.exists():
        return {}
    return json.loads(meta_path.read_text(encoding="utf-8"))


def fixture_dialect(name: str) -> str:
    """Return SQL dialect for a fixture (default: duckdb)."""
    meta = read_fixture_meta(name)
    dialect = meta.get("dialect")
    return dialect if isinstance(dialect, str) and dialect else "duckdb"


def fixture_schema(name: str) -> Optional[Dict[str, Any]]:
    """Return SQLGlot-compatible schema for a fixture, if defined.

    Schema format in meta.json:
    {
        "dialect": "snowflake",
        "schema": {
            "CATALOG": {
                "SCHEMA": {
                    "TABLE": {
                        "col1": "VARCHAR",
                        "col2": "INTEGER"
                    }
                }
            }
        }
    }
    """
    meta = read_fixture_meta(name)
    schema = meta.get("schema")
    return schema if isinstance(schema, dict) else None


def list_sql_fixtures() -> List[str]:
    """List fixture names (without .sql suffix), sorted."""
    return sorted(p.stem for p in FIXTURES_DIR.glob("*.sql"))


def read_sql_fixture(name: str) -> str:
    """Read a SQL fixture from `tests/fixtures/semantic_sql/<name>.sql`."""
    return (FIXTURES_DIR / f"{name}.sql").read_text(encoding="utf-8")


def expected_path(name: str) -> Path:
    """Path to deterministic/heuristic golden JSON for a fixture."""
    return EXPECTED_DIR / f"{name}.json"


def read_expected(name: str) -> Dict[str, Any]:
    """Read deterministic/heuristic golden JSON for a fixture."""
    return json.loads(expected_path(name).read_text(encoding="utf-8"))


def write_expected(name: str, payload: Dict[str, Any]) -> None:
    """Write deterministic/heuristic golden JSON for a fixture."""
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    expected_path(name).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _sort_list(items: List[Any], key: Callable[[Any], Tuple]) -> List[Any]:
    try:
        return sorted(items, key=key)
    except Exception:
        # If we can't sort safely (mixed types), leave order unchanged.
        return items


def normalize_semantic_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize analysis payload for stable golden snapshots.

    This is intentionally conservative: we only sort lists where order is not
    semantically meaningful and where we have stable keys.
    """
    out = json.loads(json.dumps(payload))  # force JSON-serializable, deep copy

    det = out.get("deterministic") or {}

    # relation_analysis
    ra = det.get("relation_analysis") or {}
    if isinstance(ra, dict):
        if isinstance(ra.get("relations"), list):
            ra["relations"] = _sort_list(
                ra["relations"],
                lambda r: (
                    (r or {}).get("scope", ""),
                    (r or {}).get("alias", ""),
                    (r or {}).get("base", ""),
                    (r or {}).get("kind", ""),
                ),
            )
        if isinstance(ra.get("alias_mappings"), list):
            ra["alias_mappings"] = _sort_list(
                ra["alias_mappings"],
                lambda m: ((m or {}).get("alias", ""), (m or {}).get("base", "")),
            )
        if isinstance(ra.get("self_join_groups"), list):
            ra["self_join_groups"] = _sort_list(
                ra["self_join_groups"],
                lambda g: (
                    (g or {}).get("base", ""),
                    ",".join((g or {}).get("aliases", []) or []),
                ),
            )
        for k in (
            "tables",
            "cte_defs",
            "subqueries",
            "from_clause_order",
            "driving_relations",
        ):
            if isinstance(ra.get(k), list):
                ra[k] = list(ra[k])

    # column_analysis
    ca = det.get("column_analysis") or {}
    if isinstance(ca, dict):
        if isinstance(ca.get("columns_by_alias"), list):
            ca["columns_by_alias"] = _sort_list(
                ca["columns_by_alias"],
                lambda c: ((c or {}).get("alias", ""),),
            )
            for c in ca["columns_by_alias"]:
                if isinstance(c, dict) and isinstance(c.get("columns"), list):
                    c["columns"] = sorted(c["columns"])
        if isinstance(ca.get("column_refs"), list):
            ca["column_refs"] = _sort_list(
                ca["column_refs"],
                lambda r: (
                    (r or {}).get("scope", ""),
                    (r or {}).get("alias", ""),
                    (r or {}).get("column", ""),
                ),
            )
        if isinstance(ca.get("unresolved_unqualified"), list):
            ca["unresolved_unqualified"] = sorted(ca["unresolved_unqualified"])

    # join_analysis
    ja = det.get("join_analysis") or {}
    if isinstance(ja, dict) and isinstance(ja.get("joins"), list):
        ja["joins"] = _sort_list(
            ja["joins"],
            lambda j: (
                (j or {}).get("left", ""),
                (j or {}).get("right", ""),
                (j or {}).get("type", ""),
                (j or {}).get("effective_type", ""),
                (j or {}).get("equi_condition", (j or {}).get("condition", "")),
            ),
        )

    # filter_analysis
    fa = det.get("filter_analysis") or {}
    if isinstance(fa, dict):
        for k in (
            "where",
            "having",
            "qualify",
            "null_killing_on_outer",
            "unresolved_predicates",
        ):
            if isinstance(fa.get(k), list):
                fa[k] = sorted([str(x) for x in fa[k]])

    # grouping_outer
    go = det.get("grouping_outer") or {}
    if isinstance(go, dict) and isinstance(go.get("select"), list):
        go["select"] = _sort_list(
            go["select"],
            lambda s: ((s or {}).get("alias", ""), (s or {}).get("expr", "")),
        )
        for s in go["select"]:
            if isinstance(s, dict) and isinstance(s.get("source_aliases"), list):
                s["source_aliases"] = sorted(s["source_aliases"])

    # window_outer
    wo = det.get("window_outer") or {}
    if isinstance(wo, dict) and isinstance(wo.get("windows"), list):
        wo["windows"] = _sort_list(
            wo["windows"],
            lambda w: ((w or {}).get("func", ""),),
        )

    # output_outer
    oo = det.get("output_outer") or {}
    if isinstance(oo, dict):
        if isinstance(oo.get("order_by"), list):
            oo["order_by"] = _sort_list(
                oo["order_by"],
                lambda o: ((o or {}).get("expr", ""), (o or {}).get("dir", "")),
            )
        if isinstance(oo.get("set_ops"), list):
            oo["set_ops"] = _sort_list(
                oo["set_ops"],
                lambda o: ((o or {}).get("position", 0), (o or {}).get("op", "")),
            )

    # heuristics
    heur = out.get("heuristics") or {}
    if isinstance(heur, dict):
        t = heur.get("time") or {}
        if isinstance(t, dict) and isinstance(t.get("classifications"), list):
            # Support both old "qualified_name" and new "column_alias" field names
            t["classifications"] = _sort_list(
                t["classifications"],
                lambda c: (
                    (c or {}).get("column_alias", "") or (c or {}).get("qualified_name", ""),
                ),
            )
        s = heur.get("semantic") or {}
        if isinstance(s, dict) and isinstance(s.get("classifications"), list):
            # Support both old "alias" and new "column_alias" field names
            s["classifications"] = _sort_list(
                s["classifications"],
                lambda c: (
                    (c or {}).get("column_alias", "") or (c or {}).get("alias", ""),
                    (c or {}).get("semantic_role", ""),
                ),
            )

    return out

