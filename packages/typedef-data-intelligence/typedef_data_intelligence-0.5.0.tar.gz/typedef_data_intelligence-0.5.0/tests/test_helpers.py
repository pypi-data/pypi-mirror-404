"""Helper functions for tests."""
from pathlib import Path
from typing import Any

from lineage.ingest.static_loaders.dbt.dbt_loader import (
    ChecksumInfo,
    DbtColumn,
    DbtMacroNode,
    DbtModelNode,
    DbtSourceNode,
    DbtTestNode,
    DbtUnitTestNode,
    RawDbtArtifacts,
)


def create_mock_model(
    unique_id: str,
    checksum: str | None = "abc123",
    name: str | None = None,
    compiled_sql: str = "SELECT 1",
    materialization: str | None = "table",
    depends_on_nodes: list[str] | None = None,
    depends_on_sources: list[str] | None = None,
    depends_on_macros: list[str] | None = None,
    columns: dict[str, DbtColumn] | None = None,
    database: str | None = "test_db",
    schema: str | None = "test_schema",
    relation_name: str | None | object = ...,  # Use ... as sentinel
) -> DbtModelNode:
    """Create a mock DbtModelNode for testing.

    Args:
        unique_id: Unique identifier for the model
        checksum: Checksum value (None for no checksum)
        name: Model name (extracted from unique_id if None)
        compiled_sql: Compiled SQL
        materialization: Materialization type (can be None)
        depends_on_nodes: List of node dependencies
        depends_on_sources: List of source dependencies
        depends_on_macros: List of macro dependencies
        columns: Dictionary of columns
        database: Database name (can be None for testing)
        schema: Schema name (can be None for testing)
        relation_name: Relation name (auto-constructed if not provided, can be explicitly None)
    """
    if name is None:
        # Extract name from unique_id (e.g., "model.test.fct_orders" -> "fct_orders")
        name = unique_id.split(".")[-1]

    # Handle relation_name: only construct default if using sentinel value (...)
    computed_relation_name: str | None
    if relation_name is ...:
        # Not explicitly provided, construct default
        if schema:
            computed_relation_name = f"{schema}.{name}"
        else:
            computed_relation_name = name
    else:
        # Explicitly provided (could be None or a string)
        computed_relation_name = relation_name  # type: ignore

    return DbtModelNode(
        unique_id=unique_id,
        name=name,
        resource_type="model",
        description=None,
        tags=[],
        meta={},
        database=database,
        schema=schema,
        alias=name,
        relation_name=computed_relation_name,
        materialization=materialization,
        depends_on_nodes=depends_on_nodes or [],
        depends_on_sources=depends_on_sources or [],
        depends_on_macros=depends_on_macros or [],
        compiled_sql=compiled_sql,
        columns=columns or {},
        checksum=ChecksumInfo(name="sha256", checksum=checksum) if checksum else None,
    )


def create_mock_macro(
    unique_id: str,
    name: str | None = None,
    package_name: str = "test",
    macro_sql: str = "{% macro example() %}select 1{% endmacro %}",
    depends_on_macros: list[str] | None = None,
) -> DbtMacroNode:
    """Create a mock DbtMacroNode for testing."""
    if name is None:
        name = unique_id.split(".")[-1]
    return DbtMacroNode(
        unique_id=unique_id,
        name=name,
        resource_type="macro",
        description=None,
        tags=[],
        meta={},
        package_name=package_name,
        original_path=f"macros/{name}.sql",
        source_path=f"/tmp/{name}.sql",
        macro_sql=macro_sql,
        depends_on_macros=depends_on_macros or [],
    )


def create_mock_source(
    unique_id: str,
    name: str | None = None,
    database: str = "test_db",
    schema: str = "test_schema",
    identifier: str | None = None,
    columns: dict[str, DbtColumn] | None = None,
    description: str = "",
    loader: str | None = None,
) -> DbtSourceNode:
    """Create a mock DbtSourceNode for testing.

    Args:
        unique_id: Source unique ID (e.g., "source.project.raw.orders")
        name: Source name (defaults to extracted from unique_id)
        database: Database name
        schema: Schema name
        identifier: Table identifier (defaults to name)
        columns: Column definitions
        description: Source description
        loader: Loader type (e.g., "fivetran")

    Returns:
        DbtSourceNode instance
    """
    if name is None:
        # Extract name from unique_id (e.g., "source.project.raw.orders" -> "orders")
        name = unique_id.split(".")[-1]
    if identifier is None:
        identifier = name

    return DbtSourceNode(
        unique_id=unique_id,
        name=name,
        resource_type="source",
        description=description,
        tags=[],
        meta={},
        database=database,
        schema=schema,
        identifier=identifier,
        relation_name=f"{schema}.{identifier}",
        loader=loader,
        columns=columns or {},
    )


def create_mock_test(
    unique_id: str,
    test_type: str = "generic",
    test_name: str | None = "unique",
    column_name: str | None = None,
    model_id: str | None = None,
    referenced_model_id: str | None = None,
    test_kwargs: Any | None = None,
    severity: str = "error",
    where_clause: str | None = None,
    store_failures: bool = False,
    compiled_sql: str | None = None,
    name: str | None = None,
) -> DbtTestNode:
    """Create a mock DbtTestNode for testing.

    Args:
        unique_id: Test unique ID (e.g., "test.project.unique_orders_id")
        test_type: "generic" or "singular"
        test_name: For generic tests, the test macro name (unique, not_null, etc.)
        column_name: Column being tested (for column-scoped generic tests)
        model_id: Primary model/source being tested
        referenced_model_id: For relationship tests, the referenced model/source
        test_kwargs: For generic tests, the kwargs dict
        severity: Test severity ("error" or "warn")
        where_clause: Optional WHERE filter from test config
        store_failures: Whether test stores failures
        compiled_sql: Compiled test SQL
        name: Test name (defaults to extracted from unique_id)

    Returns:
        DbtTestNode instance
    """
    if name is None:
        # Extract name from unique_id (e.g., "test.project.unique_orders_id" -> "unique_orders_id")
        name = unique_id.split(".")[-1]

    depends_on_nodes = []
    if model_id:
        depends_on_nodes.append(model_id)
    if referenced_model_id:
        depends_on_nodes.append(referenced_model_id)

    return DbtTestNode(
        unique_id=unique_id,
        name=name,
        resource_type="test",
        description=None,
        tags=[],
        meta={},
        test_type=test_type,
        test_name=test_name,
        column_name=column_name,
        model_id=model_id,
        referenced_model_id=referenced_model_id,
        test_kwargs=test_kwargs,
        severity=severity,
        where_clause=where_clause,
        store_failures=store_failures,
        original_path=f"tests/{name}.sql" if test_type == "singular" else None,
        compiled_sql=compiled_sql,
        depends_on_nodes=depends_on_nodes,
    )


def create_mock_unit_test(
    unique_id: str,
    model_id: str | None = None,
    given: list[dict[str, Any]] | None = None,
    expect: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
    name: str | None = None,
) -> DbtUnitTestNode:
    """Create a mock DbtUnitTestNode for testing.

    Args:
        unique_id: Unit test unique ID (e.g., "unit_test.project.test_orders_logic")
        model_id: Model being tested
        given: Input definitions (mocked data)
        expect: Expected output
        overrides: Model overrides
        name: Unit test name (defaults to extracted from unique_id)

    Returns:
        DbtUnitTestNode instance
    """
    if name is None:
        name = unique_id.split(".")[-1]

    return DbtUnitTestNode(
        unique_id=unique_id,
        name=name,
        resource_type="unit_test",
        description=None,
        tags=[],
        meta={},
        model_id=model_id,
        given=given,
        expect=expect,
        overrides=overrides,
    )


def create_mock_artifacts(
    models: list[DbtModelNode],
    macros: list[DbtMacroNode] | None = None,
    tests: list[DbtTestNode] | None = None,
    unit_tests: list[DbtUnitTestNode] | None = None,
    sources: list[DbtSourceNode] | None = None,
) -> RawDbtArtifacts:
    """Create mock DbtArtifacts from a list of models.

    Args:
        models: List of DbtModelNode instances
        macros: Optional list of DbtMacroNode instances
        tests: Optional list of DbtTestNode instances
        unit_tests: Optional list of DbtUnitTestNode instances
        sources: Optional list of DbtSourceNode instances

    Returns:
        RawDbtArtifacts instance
    """
    # Create minimal manifest structure
    nodes: dict[str, dict] = {}

    # Add models
    for model in models:
        nodes[model.unique_id] = {
            "resource_type": model.resource_type,
            "name": model.name,
            "original_file_path": f"models/{model.name}.sql",
            "compiled_sql": model.compiled_sql,
            "database": model.database,
            "schema": model.schema,
            "alias": model.alias,
            "relation_name": model.relation_name,
            "columns": {
                col_name: {
                    "description": (col.description or ""),
                }
                for col_name, col in (model.columns or {}).items()
            },
            "config": {
                "materialized": model.materialization,
            },
            "depends_on": {
                "nodes": model.depends_on_nodes,
                "sources": model.depends_on_sources,
                "macros": getattr(model, "depends_on_macros", []) or [],
            },
            "checksum": {
                "name": model.checksum.name if model.checksum else "sha256",
                "checksum": model.checksum.checksum if model.checksum else "",
            } if model.checksum else None,
        }

    # Add tests
    for test in (tests or []):
        test_metadata = None
        if test.test_type == "generic":
            test_metadata = {
                "name": test.test_name,
                "kwargs": test.test_kwargs or {},
            }

        nodes[test.unique_id] = {
            "resource_type": "test",
            "name": test.name,
            "description": test.description,
            "tags": test.tags,
            "meta": test.meta,
            "original_file_path": test.original_path,
            "compiled_sql": test.compiled_sql,
            "column_name": test.column_name,
            "test_metadata": test_metadata,
            "config": {
                "severity": test.severity,
                "where": test.where_clause,
                "store_failures": test.store_failures,
            },
            "depends_on": {
                "nodes": test.depends_on_nodes,
            },
        }

    # Add unit tests
    for unit_test in (unit_tests or []):
        depends_on_nodes = [unit_test.model_id] if unit_test.model_id else []
        nodes[unit_test.unique_id] = {
            "resource_type": "unit_test",
            "name": unit_test.name,
            "description": unit_test.description,
            "tags": unit_test.tags,
            "meta": unit_test.meta,
            "given": unit_test.given,
            "expect": unit_test.expect,
            "overrides": unit_test.overrides,
            "depends_on": {
                "nodes": depends_on_nodes,
            },
        }

    # Build sources dict
    sources_dict = {}
    for source in (sources or []):
        sources_dict[source.unique_id] = {
            "resource_type": "source",
            "name": source.name,
            "source_name": source.unique_id.split(".")[-2] if len(source.unique_id.split(".")) >= 3 else "raw",
            "source_description": "",
            "database": source.database,
            "schema": source.schema,
            "identifier": source.identifier,
            "relation_name": source.relation_name,
            "loader": source.loader,
            "description": source.description,
            "columns": {
                col_name: {
                    "description": col.description or "",
                }
                for col_name, col in (source.columns or {}).items()
            },
        }

    manifest = {
        "metadata": {
            "project_name": "test_project",
            "adapter_type": "duckdb",
            "target_name": "dev",
        },
        "nodes": nodes,
        "sources": sources_dict,
        "macros": {
            macro.unique_id: {
                "resource_type": "macro",
                "name": macro.name,
                "package_name": macro.package_name,
                "original_file_path": macro.original_path,
                "macro_sql": macro.macro_sql,
                "depends_on": {
                    "macros": macro.depends_on_macros,
                },
            }
            for macro in (macros or [])
        },
    }
# Build catalog sources
    catalog_sources = {}
    for source in (sources or []):
        catalog_sources[source.unique_id] = {
            "columns": {
                col_name: {
                    "type": col.data_type or "unknown",
                }
                for col_name, col in (source.columns or {}).items()
            }
        }
    catalog = {
        "nodes": {
            model.unique_id: {
                "columns": {
                    col_name: {
                        "type": (col.data_type or "unknown"),
                    }
                    for col_name, col in (model.columns or {}).items()
                }
            }
            for model in models
        },
        "sources": catalog_sources,
    }

    # Create minimal config
    from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
    config = DbtArtifactsConfig()
    config.target_path = Path("/tmp/test_target")

    return RawDbtArtifacts(
        config=config,
        manifest=manifest,
        catalog=catalog,
        run_results={},
    )

