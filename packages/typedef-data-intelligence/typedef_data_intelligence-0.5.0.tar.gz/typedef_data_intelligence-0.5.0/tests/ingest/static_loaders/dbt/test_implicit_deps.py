"""Tests for implicit source dependency extraction.

Tests cover:
- build_source_lookup() - creates source lookup from artifacts
- extract_implicit_source_deps() - extracts deps from compiled SQL
- Edge cases: CTEs, subqueries, explicit deps, parse failures
"""

import json
from pathlib import Path
from typing import Dict

from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
from lineage.ingest.static_loaders.dbt.dbt_loader import RawDbtArtifacts
from lineage.ingest.static_loaders.dbt.implicit_deps import (
    ImplicitDependency,
    build_source_lookup,
    extract_implicit_source_deps,
)


def create_manifest_with_sources(
    sources: Dict[str, dict],
    models: Dict[str, dict] | None = None,
) -> dict:
    """Create a minimal manifest with sources and optionally models.

    Args:
        sources: Dictionary of source unique_id -> source node dict
        models: Optional dictionary of model unique_id -> model node dict

    Returns:
        Manifest dict suitable for RawDbtArtifacts
    """
    manifest_nodes = {}
    if models:
        manifest_nodes.update(models)

    return {
        "metadata": {
            "project_name": "test_project",
            "adapter_type": "duckdb",
            "target_name": "dev",
        },
        "nodes": manifest_nodes,
        "sources": sources,
        "macros": {},
    }


def create_artifacts_from_manifest(manifest: dict, tmp_path: Path) -> RawDbtArtifacts:
    """Create RawDbtArtifacts from a manifest dict."""
    target_dir = tmp_path / "target"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "manifest.json").write_text(json.dumps(manifest))
    (target_dir / "catalog.json").write_text(json.dumps({"nodes": {}, "sources": {}}))

    config = DbtArtifactsConfig()
    config.target_path = target_dir

    return RawDbtArtifacts(
        config=config,
        manifest=manifest,
        catalog={"nodes": {}, "sources": {}},
        run_results={},
    )


class TestBuildSourceLookup:
    """Tests for build_source_lookup() function."""

    def test_builds_lookup_with_schema_and_identifier(self, tmp_path: Path) -> None:
        """Source with schema and identifier creates schema.identifier key."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders_raw",
                "schema": "raw_data",
                "database": "analytics",
                "relation_name": "raw_data.orders_raw",
                "loader": "airbyte",
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        manifest = create_manifest_with_sources(sources)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        lookup = build_source_lookup(artifacts)

        # Should have schema.identifier key
        assert "raw_data.orders_raw" in lookup
        assert lookup["raw_data.orders_raw"] == "source.project.raw.orders"

        # Should also have just identifier as fallback
        assert "orders_raw" in lookup
        assert lookup["orders_raw"] == "source.project.raw.orders"

    def test_builds_lookup_with_fqn(self, tmp_path: Path) -> None:
        """Source with database creates database.schema.identifier key."""
        sources = {
            "source.project.warehouse.events": {
                "resource_type": "source",
                "name": "events",
                "unique_id": "source.project.warehouse.events",
                "identifier": "event_log",
                "schema": "analytics",
                "database": "prod_db",
                "relation_name": "prod_db.analytics.event_log",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        manifest = create_manifest_with_sources(sources)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        lookup = build_source_lookup(artifacts)

        # Should have fully qualified key
        assert "prod_db.analytics.event_log" in lookup
        assert lookup["prod_db.analytics.event_log"] == "source.project.warehouse.events"

    def test_builds_lookup_case_insensitive(self, tmp_path: Path) -> None:
        """Lookup keys are lowercase for case-insensitive matching."""
        sources = {
            "source.project.raw.Orders": {
                "resource_type": "source",
                "name": "Orders",
                "unique_id": "source.project.raw.Orders",
                "identifier": "ORDERS",
                "schema": "RAW",
                "database": "ANALYTICS",
                "relation_name": "RAW.ORDERS",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        manifest = create_manifest_with_sources(sources)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        lookup = build_source_lookup(artifacts)

        # All keys should be lowercase
        assert "raw.orders" in lookup
        assert "orders" in lookup
        assert "analytics.raw.orders" in lookup

    def test_multiple_sources(self, tmp_path: Path) -> None:
        """Multiple sources create entries for each."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.orders",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
            "source.project.raw.customers": {
                "resource_type": "source",
                "name": "customers",
                "unique_id": "source.project.raw.customers",
                "identifier": "customers",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.customers",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        manifest = create_manifest_with_sources(sources)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        lookup = build_source_lookup(artifacts)

        assert "raw.orders" in lookup
        assert lookup["raw.orders"] == "source.project.raw.orders"
        assert "raw.customers" in lookup
        assert lookup["raw.customers"] == "source.project.raw.customers"


class TestExtractImplicitSourceDeps:
    """Tests for extract_implicit_source_deps() function."""

    def test_finds_implicit_source_dep(self, tmp_path: Path) -> None:
        """Model referencing source table without {{ source() }} is detected."""
        sources = {
            "source.project.raw.events": {
                "resource_type": "source",
                "name": "events",
                "unique_id": "source.project.raw.events",
                "identifier": "events",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.events",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        # Model uses dbt_utils.get_relations_by_pattern() which compiles
        # to direct table reference without depends_on_sources
        models = {
            "model.project.stg_events": {
                "resource_type": "model",
                "name": "stg_events",
                "unique_id": "model.project.stg_events",
                "database": "analytics",
                "schema": "staging",
                "alias": "stg_events",
                "relation_name": "staging.stg_events",
                "original_file_path": "models/staging/stg_events.sql",
                "compiled_sql": "SELECT * FROM raw.events",  # Direct reference!
                "config": {"materialized": "view"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],  # Empty - source not explicitly declared
                    "macros": ["macro.dbt_utils.get_relations_by_pattern"],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.stg_events")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        assert len(implicit_deps) == 1
        assert implicit_deps[0].source_id == "source.project.raw.events"
        assert implicit_deps[0].table_name == "events"
        assert implicit_deps[0].schema_name == "raw"

    def test_excludes_explicit_deps(self, tmp_path: Path) -> None:
        """Sources already in depends_on_sources are not duplicated."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.orders",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.stg_orders": {
                "resource_type": "model",
                "name": "stg_orders",
                "unique_id": "model.project.stg_orders",
                "database": "analytics",
                "schema": "staging",
                "alias": "stg_orders",
                "relation_name": "staging.stg_orders",
                "original_file_path": "models/staging/stg_orders.sql",
                "compiled_sql": "SELECT * FROM raw.orders",
                "config": {"materialized": "view"},
                "depends_on": {
                    "nodes": [],
                    "sources": ["source.project.raw.orders"],  # Already explicit!
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.stg_orders")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        # Should be empty - source is already explicit
        assert len(implicit_deps) == 0

    def test_ignores_ctes(self, tmp_path: Path) -> None:
        """CTE references are not matched as source dependencies."""
        sources = {
            "source.project.raw.events": {
                "resource_type": "source",
                "name": "events",
                "unique_id": "source.project.raw.events",
                "identifier": "base_data",  # Same name as CTE
                "schema": "raw",
                "database": None,
                "relation_name": "raw.base_data",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.report": {
                "resource_type": "model",
                "name": "report",
                "unique_id": "model.project.report",
                "database": "analytics",
                "schema": "marts",
                "alias": "report",
                "relation_name": "marts.report",
                "original_file_path": "models/marts/report.sql",
                "compiled_sql": """
                WITH base_data AS (
                    SELECT 1 AS id
                )
                SELECT * FROM base_data
                """,
                "config": {"materialized": "table"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.report")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        # Should be empty - base_data is a CTE, not the source table
        assert len(implicit_deps) == 0

    def test_handles_no_compiled_sql(self, tmp_path: Path) -> None:
        """Model without compiled_sql returns empty list."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.orders",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.ephemeral": {
                "resource_type": "model",
                "name": "ephemeral",
                "unique_id": "model.project.ephemeral",
                "database": None,
                "schema": None,
                "alias": "ephemeral",
                "relation_name": None,
                "original_file_path": "models/ephemeral.sql",
                "compiled_sql": None,  # No compiled SQL
                "config": {"materialized": "ephemeral"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.ephemeral")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        assert len(implicit_deps) == 0

    def test_handles_unparseable_sql(self, tmp_path: Path) -> None:
        """Model with unparseable SQL returns empty list gracefully."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.orders",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.broken": {
                "resource_type": "model",
                "name": "broken",
                "unique_id": "model.project.broken",
                "database": "analytics",
                "schema": "staging",
                "alias": "broken",
                "relation_name": "staging.broken",
                "original_file_path": "models/broken.sql",
                "compiled_sql": "SELECT * FROM raw.orders WHERE (unclosed",  # Invalid SQL
                "config": {"materialized": "view"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.broken")
        assert model is not None

        # Should not raise, just return empty
        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        assert len(implicit_deps) == 0

    def test_multiple_implicit_deps(self, tmp_path: Path) -> None:
        """Model can have multiple implicit source dependencies."""
        sources = {
            "source.project.raw.orders": {
                "resource_type": "source",
                "name": "orders",
                "unique_id": "source.project.raw.orders",
                "identifier": "orders",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.orders",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
            "source.project.raw.customers": {
                "resource_type": "source",
                "name": "customers",
                "unique_id": "source.project.raw.customers",
                "identifier": "customers",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.customers",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.joined": {
                "resource_type": "model",
                "name": "joined",
                "unique_id": "model.project.joined",
                "database": "analytics",
                "schema": "marts",
                "alias": "joined",
                "relation_name": "marts.joined",
                "original_file_path": "models/marts/joined.sql",
                "compiled_sql": """
                SELECT o.*, c.name
                FROM raw.orders o
                JOIN raw.customers c ON o.customer_id = c.id
                """,
                "config": {"materialized": "table"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],  # Neither source is explicit
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.joined")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        assert len(implicit_deps) == 2
        source_ids = {d.source_id for d in implicit_deps}
        assert "source.project.raw.orders" in source_ids
        assert "source.project.raw.customers" in source_ids

    def test_no_duplicates(self, tmp_path: Path) -> None:
        """Same source referenced multiple times only creates one dependency."""
        sources = {
            "source.project.raw.events": {
                "resource_type": "source",
                "name": "events",
                "unique_id": "source.project.raw.events",
                "identifier": "events",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.events",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.self_join": {
                "resource_type": "model",
                "name": "self_join",
                "unique_id": "model.project.self_join",
                "database": "analytics",
                "schema": "marts",
                "alias": "self_join",
                "relation_name": "marts.self_join",
                "original_file_path": "models/marts/self_join.sql",
                "compiled_sql": """
                SELECT a.*, b.parent_id
                FROM raw.events a
                JOIN raw.events b ON a.parent_id = b.id
                """,
                "config": {"materialized": "table"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.self_join")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        # Should only have one dependency even though table is referenced twice
        assert len(implicit_deps) == 1
        assert implicit_deps[0].source_id == "source.project.raw.events"

    def test_ignores_subqueries(self, tmp_path: Path) -> None:
        """Subquery aliases are not matched as source dependencies."""
        sources = {
            "source.project.raw.derived": {
                "resource_type": "source",
                "name": "derived",
                "unique_id": "source.project.raw.derived",
                "identifier": "derived",
                "schema": "raw",
                "database": None,
                "relation_name": "raw.derived",
                "loader": None,
                "description": None,
                "tags": [],
                "meta": {},
                "columns": {},
            },
        }

        models = {
            "model.project.outer": {
                "resource_type": "model",
                "name": "outer",
                "unique_id": "model.project.outer",
                "database": "analytics",
                "schema": "marts",
                "alias": "outer",
                "relation_name": "marts.outer",
                "original_file_path": "models/marts/outer.sql",
                "compiled_sql": """
                SELECT *
                FROM (SELECT 1 AS id) AS derived
                """,
                "config": {"materialized": "table"},
                "depends_on": {
                    "nodes": [],
                    "sources": [],
                    "macros": [],
                },
                "columns": {},
                "checksum": {"name": "sha256", "checksum": "abc123"},
            },
        }

        manifest = create_manifest_with_sources(sources, models)
        artifacts = create_artifacts_from_manifest(manifest, tmp_path)

        source_lookup = build_source_lookup(artifacts)
        model = artifacts.get_model("model.project.outer")
        assert model is not None

        implicit_deps = extract_implicit_source_deps(model, source_lookup, dialect="duckdb")

        # Should be empty - "derived" is a subquery alias, not the source table
        assert len(implicit_deps) == 0


class TestImplicitDependencyDataclass:
    """Tests for ImplicitDependency dataclass."""

    def test_dataclass_fields(self) -> None:
        """ImplicitDependency has expected fields."""
        dep = ImplicitDependency(
            source_id="source.project.raw.orders",
            schema_name="raw",
            table_name="orders",
        )

        assert dep.source_id == "source.project.raw.orders"
        assert dep.schema_name == "raw"
        assert dep.table_name == "orders"

    def test_schema_name_optional(self) -> None:
        """schema_name can be None."""
        dep = ImplicitDependency(
            source_id="source.project.raw.orders",
            schema_name=None,
            table_name="orders",
        )

        assert dep.schema_name is None
