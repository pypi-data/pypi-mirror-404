from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from lineage.ingest.static_loaders.semantic.loader import SemanticLoader


@pytest.fixture
def loader() -> SemanticLoader:
    """Fixture to provide a SemanticLoader instance with a mocked storage."""
    storage = MagicMock()
    return SemanticLoader(storage)


def test_build_resolution_single_base(loader: SemanticLoader) -> None:
    """Test resolution when a CTE or subquery maps to exactly one base relation."""
    relations = [
        {
            "kind": "table",
            "scope": "cte:my_cte",
            "base": "base_table",
            "schema_name": "my_schema",
            "catalog": "my_db",
        },
        {
            "kind": "table",
            "scope": "subquery:sub1",
            "name": "other_table",
            "schema": "other_schema",
        },
    ]
    cte_res, sub_res = loader._build_cte_and_subquery_resolution(relations)

    assert cte_res == {"my_cte": ("base_table", "my_schema", "my_db")}
    assert sub_res == {"sub1": ("other_table", "other_schema", None)}


def test_build_resolution_multi_base_skipping(loader: SemanticLoader) -> None:
    """Test that CTEs/subqueries mapping to multiple base relations are skipped."""
    relations = [
        {
            "kind": "table",
            "scope": "cte:multi_cte",
            "base": "table1",
        },
        {
            "kind": "table",
            "scope": "cte:multi_cte",
            "base": "table2",
        },
        {
            "kind": "table",
            "scope": "subquery:multi_sub",
            "base": "table3",
        },
        {
            "kind": "table",
            "scope": "subquery:multi_sub",
            "base": "table4",
        },
        {
            "kind": "table",
            "scope": "cte:single_cte",
            "base": "table5",
        },
    ]
    cte_res, sub_res = loader._build_cte_and_subquery_resolution(relations)

    # multi_cte has two different bases, should be skipped
    assert "multi_cte" not in cte_res
    # multi_sub has two different bases, should be skipped
    assert "multi_sub" not in sub_res
    # single_cte should still be resolved
    assert cte_res["single_cte"] == ("table5", None, None)


def test_build_resolution_same_base_multiple_times(loader: SemanticLoader) -> None:
    """Test that multiple references to the same base relation still resolve if unique."""
    relations = [
        {
            "kind": "table",
            "scope": "cte:my_cte",
            "base": "table1",
            "schema": "s1",
        },
        {
            "kind": "table",
            "scope": "cte:my_cte",
            "base": "table1",
            "schema": "s1",
        },
    ]
    cte_res, _ = loader._build_cte_and_subquery_resolution(relations)

    # Identical resolutions (base, schema, catalog) should count as one
    assert cte_res == {"my_cte": ("table1", "s1", None)}


def test_build_resolution_different_schemas_skipping(loader: SemanticLoader) -> None:
    """Test that same table name in different schemas/catalogs counts as multiple bases."""
    relations = [
        {
            "kind": "table",
            "scope": "cte:my_cte",
            "base": "table1",
            "schema": "s1",
        },
        {
            "kind": "table",
            "scope": "cte:my_cte",
            "base": "table1",
            "schema": "s2",
        },
    ]
    cte_res, _ = loader._build_cte_and_subquery_resolution(relations)
    assert "my_cte" not in cte_res


def test_build_resolution_edge_cases(loader: SemanticLoader) -> None:
    """Test edge cases like empty inputs, missing scopes, and missing bases."""
    # Empty relations
    assert loader._build_cte_and_subquery_resolution([]) == ({}, {})

    # Missing scope or irrelevant scope
    relations = [
        {"kind": "table", "base": "t1"},  # no scope
        {"kind": "table", "scope": "outer", "base": "t1"},  # wrong scope
        {"kind": "cte", "scope": "cte:c1", "base": "t1"},  # wrong kind (only table/view allowed)
    ]
    assert loader._build_cte_and_subquery_resolution(relations) == ({}, {})

    # Missing base/name
    relations = [
        {"kind": "table", "scope": "cte:c1"},  # no base or name
    ]
    assert loader._build_cte_and_subquery_resolution(relations) == ({}, {})


def test_build_resolution_normalization(loader: SemanticLoader) -> None:
    """Test that identifiers are correctly normalized during resolution."""
    relations = [
        {
            "kind": "table",
            "scope": 'cte:"MY_CTE"',
            "base": '"Base_Table"',
            "schema": "`MY_SCHEMA`",
        }
    ]
    cte_res, _ = loader._build_cte_and_subquery_resolution(relations)

    # scope is normalized (lowered and stripped of quotes)
    # base and schema are stripped of quotes but preserved case
    assert cte_res == {"my_cte": ("Base_Table", "MY_SCHEMA", None)}


def test_resolve_alias_via_lookup_with_resolution(loader: SemanticLoader) -> None:
    """Test that aliases are resolved to models using pre-built resolution dictionaries.

    CTE/subquery resolution replaces both base and schema_name, so the lookup
    tries schema-qualified keys first (e.g. marts.fact_table) for specificity.
    """
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "my_alias": {"kind": "cte", "base": "my_cte"},
        "sub_alias": {"kind": "subquery", "base": "unused"},
    }
    # Schema-qualified keys from the resolution tuples
    model_lookup = {
        "marts.fact_table": ("model_id_1", NodeLabel.DBT_MODEL),
        "raw.base_table": ("model_id_2", NodeLabel.DBT_MODEL),
    }

    cte_resolution = {"my_cte": ("fact_table", "marts", None)}
    subquery_resolution = {"sub_alias": ("base_table", "raw", None)}

    # Resolve CTE alias — schema from resolution tuple used in lookup key
    res = loader._resolve_alias_via_lookup(
        "my_alias",
        alias_to_relation,
        model_lookup,
        cte_resolution=cte_resolution,
    )
    assert res == ("model_id_1", NodeLabel.DBT_MODEL)

    # Resolve subquery alias — same schema propagation
    res = loader._resolve_alias_via_lookup(
        "sub_alias",
        alias_to_relation,
        model_lookup,
        subquery_resolution=subquery_resolution,
    )
    assert res == ("model_id_2", NodeLabel.DBT_MODEL)


def test_resolve_alias_via_lookup_no_resolution(loader: SemanticLoader) -> None:
    """Test resolution when no resolution dict is provided (standard behavior)."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "direct_table": {"kind": "table", "base": "fact_table", "schema": "marts"},
    }
    model_lookup = {
        "marts.fact_table": ("model_id_1", NodeLabel.DBT_MODEL),
    }

    res = loader._resolve_alias_via_lookup("direct_table", alias_to_relation, model_lookup)
    assert res == ("model_id_1", NodeLabel.DBT_MODEL)


def test_resolve_alias_via_lookup_missing_lookup(loader: SemanticLoader) -> None:
    """Test resolution when the resolved table is not in the model lookup."""
    alias_to_relation = {
        "my_alias": {"kind": "cte", "base": "my_cte"},
    }
    model_lookup = {}
    cte_resolution = {"my_cte": ("missing_table", "marts", None)}

    res = loader._resolve_alias_via_lookup(
        "my_alias",
        alias_to_relation,
        model_lookup,
        cte_resolution=cte_resolution,
    )
    assert res is None


# ============================================================================
# Dependency hint disambiguation tests (collisions + upstream_deps)
# ============================================================================


def test_resolve_alias_collision_picks_upstream_dep(loader: SemanticLoader) -> None:
    """When multiple models map to the same key, prefer the one in upstream deps."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "orders": {"kind": "table", "base": "orders"},
    }
    # Two models share the name "orders" — lookup holds the last one inserted
    model_lookup = {
        "orders": ("model.staging.stg_orders", NodeLabel.DBT_MODEL),
    }
    collisions = {
        "orders": {"model.staging.stg_orders", "model.marts.fct_orders"},
    }
    # The consuming model depends on fct_orders, not stg_orders
    upstream_deps = {"model.marts.fct_orders"}

    res = loader._resolve_alias_via_lookup(
        "orders",
        alias_to_relation,
        model_lookup,
        collisions=collisions,
        upstream_deps=upstream_deps,
    )
    assert res is not None
    assert res[0] == "model.marts.fct_orders"


def test_resolve_alias_collision_keeps_default_when_it_is_upstream(loader: SemanticLoader) -> None:
    """When the default lookup winner IS in upstream deps, keep it despite collisions."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "orders": {"kind": "table", "base": "orders"},
    }
    model_lookup = {
        "orders": ("model.marts.fct_orders", NodeLabel.DBT_MODEL),
    }
    collisions = {
        "orders": {"model.staging.stg_orders", "model.marts.fct_orders"},
    }
    # The default winner is already an upstream dep
    upstream_deps = {"model.marts.fct_orders"}

    res = loader._resolve_alias_via_lookup(
        "orders",
        alias_to_relation,
        model_lookup,
        collisions=collisions,
        upstream_deps=upstream_deps,
    )
    assert res is not None
    assert res[0] == "model.marts.fct_orders"


def test_resolve_alias_collision_falls_back_when_no_dep_matches(loader: SemanticLoader) -> None:
    """When no collision candidate is in upstream deps, fall back to default winner."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "orders": {"kind": "table", "base": "orders"},
    }
    model_lookup = {
        "orders": ("model.staging.stg_orders", NodeLabel.DBT_MODEL),
    }
    collisions = {
        "orders": {"model.staging.stg_orders", "model.other.other_orders"},
    }
    # Upstream deps don't include any collision candidate
    upstream_deps = {"model.unrelated.something_else"}

    res = loader._resolve_alias_via_lookup(
        "orders",
        alias_to_relation,
        model_lookup,
        collisions=collisions,
        upstream_deps=upstream_deps,
    )
    assert res is not None
    # Falls back to the default lookup winner
    assert res[0] == "model.staging.stg_orders"


def test_resolve_alias_no_collision_ignores_deps(loader: SemanticLoader) -> None:
    """When there are no collisions for a key, upstream deps are irrelevant."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "orders": {"kind": "table", "base": "orders"},
    }
    model_lookup = {
        "orders": ("model.marts.fct_orders", NodeLabel.DBT_MODEL),
    }
    # No collisions for "orders"
    collisions = {
        "customers": {"model.a.x", "model.b.y"},
    }
    upstream_deps = {"model.unrelated.something"}

    res = loader._resolve_alias_via_lookup(
        "orders",
        alias_to_relation,
        model_lookup,
        collisions=collisions,
        upstream_deps=upstream_deps,
    )
    assert res is not None
    assert res[0] == "model.marts.fct_orders"


def test_resolve_alias_collision_with_schema_qualified_key(loader: SemanticLoader) -> None:
    """Disambiguation works with schema-qualified keys too."""
    from lineage.backends.types import NodeLabel

    alias_to_relation = {
        "o": {"kind": "table", "base": "orders", "schema": "raw"},
    }
    # Schema-qualified key takes priority
    model_lookup = {
        "raw.orders": ("model.raw.raw_orders", NodeLabel.DBT_MODEL),
        "orders": ("model.staging.stg_orders", NodeLabel.DBT_MODEL),
    }
    collisions = {
        "raw.orders": {"model.raw.raw_orders", "model.raw_v2.raw_orders"},
    }
    upstream_deps = {"model.raw_v2.raw_orders"}

    res = loader._resolve_alias_via_lookup(
        "o",
        alias_to_relation,
        model_lookup,
        collisions=collisions,
        upstream_deps=upstream_deps,
    )
    assert res is not None
    assert res[0] == "model.raw_v2.raw_orders"
