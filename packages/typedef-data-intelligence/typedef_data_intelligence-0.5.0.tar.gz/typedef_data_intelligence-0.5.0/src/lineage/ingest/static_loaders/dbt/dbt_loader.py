"""Load dbt artifacts (manifest/catalog/run_results) into typed Python objects.

This module provides lightweight dataclasses (`Dbt*Node`) and a `DbtArtifacts`
container that make downstream ingestion (lineage graph building, semantics, etc.)
much simpler than working with raw manifest JSON.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Dict,
    Iterator,
    List,
    Mapping,
    Optional,
    Protocol,
    Sequence,
    runtime_checkable,
)

from lineage.ingest.static_loaders.dbt.config import DbtArtifactsConfig
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema


@dataclass(slots=True)
class DbtColumn:
    """dbt column metadata (merged from manifest + catalog)."""
    name: str
    description: Optional[str]
    data_type: Optional[str]
    tests: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ChecksumInfo:
    """Checksum information from dbt manifest."""

    name: str  # e.g., "sha256"
    checksum: str  # The actual checksum value


@dataclass(slots=True)
class DbtBaseNode:
    """Base shape shared by dbt artifacts in the manifest."""
    unique_id: str
    name: str
    resource_type: str
    description: Optional[str]
    tags: List[str]
    meta: Mapping[str, object]


@dataclass(slots=True)
class DbtModelNode(DbtBaseNode):
    """dbt model node from the manifest."""
    database: Optional[str]
    schema: Optional[str]
    alias: Optional[str]
    relation_name: Optional[str]
    materialization: Optional[str]
    depends_on_nodes: List[str]
    depends_on_sources: List[str]
    depends_on_macros: List[str] = field(default_factory=list)
    compiled_sql: Optional[str] = None
    raw_sql: Optional[str] = None  # Original SQL from .sql file
    columns: Dict[str, DbtColumn] = field(default_factory=dict)
    original_path: Optional[str] = None
    source_path: Optional[str] = None
    declared_layer: Optional[str] = None
    compiled_path: Optional[str] = None
    checksum: Optional[ChecksumInfo] = None


@dataclass(slots=True)
class DbtSourceNode(DbtBaseNode):
    """dbt source node from the manifest."""
    database: Optional[str]
    schema: Optional[str]
    identifier: str
    relation_name: Optional[str]
    loader: Optional[str]
    columns: Dict[str, DbtColumn] = field(default_factory=dict)


@dataclass(slots=True)
class DbtMacroNode(DbtBaseNode):
    """dbt macro definition from manifest."""

    package_name: Optional[str] = None
    original_path: Optional[str] = None
    source_path: Optional[str] = None
    macro_sql: Optional[str] = None
    depends_on_macros: List[str] = field(default_factory=list)


@dataclass(slots=True)
class DbtTestNode(DbtBaseNode):
    """dbt data test node from the manifest (generic or singular)."""

    test_type: str = "generic"  # "generic" or "singular"
    test_name: Optional[str] = None  # For generic: "unique", "not_null", etc.
    column_name: Optional[str] = None
    model_id: Optional[str] = None  # Primary model/source being tested
    referenced_model_id: Optional[str] = None  # For relationship tests: the "to" target
    test_kwargs: Optional[Dict[str, object]] = None
    severity: str = "error"
    where_clause: Optional[str] = None
    store_failures: bool = False
    original_path: Optional[str] = None
    compiled_sql: Optional[str] = None
    depends_on_nodes: List[str] = field(default_factory=list)


@dataclass(slots=True)
class DbtUnitTestNode(DbtBaseNode):
    """dbt unit test node from the manifest (dbt v1.8+)."""

    model_id: Optional[str] = None
    given: Optional[List[Dict[str, object]]] = None
    expect: Optional[Dict[str, object]] = None
    overrides: Optional[Dict[str, object]] = None


@runtime_checkable
class DbtArtifacts(Protocol):
    """Protocol for dbt artifacts used by lineage builder + downstream analyzers.

    Keeping this as a Protocol lets us swap in filtered / synthetic implementations
    (e.g., for incremental processing) while preserving typing and picklability.
    """

    project_name: Optional[str]
    adapter_type: str
    target_name: str
    project_root: Path
    model_count: int
    source_count: int
    macro_count: int
    test_count: int
    unit_test_count: int

    def iter_models(self) -> Iterator[DbtModelNode]:
        """Iterate dbt models (including seeds)."""
        ...

    def iter_seeds(self) -> Iterator[DbtModelNode]:
        """Iterate dbt seed nodes."""
        ...

    def iter_sources(self) -> Iterator[DbtSourceNode]:
        """Iterate dbt sources."""
        ...

    def iter_macros(self) -> Iterator[DbtMacroNode]:
        """Iterate dbt macros."""
        ...

    def iter_tests(self) -> Iterator[DbtTestNode]:
        """Iterate dbt data tests."""
        ...

    def iter_unit_tests(self) -> Iterator[DbtUnitTestNode]:
        """Iterate dbt unit tests."""
        ...

    def get_model(self, unique_id: str) -> Optional[DbtModelNode]:
        """Get a model by unique_id."""
        ...

    def get_source(self, unique_id: str) -> Optional[DbtSourceNode]:
        """Get a source by unique_id."""
        ...

    def get_macro(self, unique_id: str) -> Optional[DbtMacroNode]:
        """Get a macro by unique_id."""
        ...

    def get_test(self, unique_id: str) -> Optional[DbtTestNode]:
        """Get a test by unique_id."""
        ...

    def get_unit_test(self, unique_id: str) -> Optional[DbtUnitTestNode]:
        """Get a unit test by unique_id."""
        ...

    def relation_lookup(self) -> Dict[str, str]:
        """Build a normalized relation-name → unique_id lookup for models/sources."""
        ...

    def sqlglot_schema(self) -> SqlglotSchema:
        """Build SQLGlot schema. Call .to_dict() to get the nested dict for SQLGlot functions."""
        ...

    @staticmethod
    def normalize_relation(value: str) -> str:
        """Normalize a relation identifier for matching (case/quoting insensitive)."""
        ...


class FilteredDbtArtifacts:
    """Pickle-friendly filtered view over dbt artifacts.

    This class *materializes* filtered model/seed dictionaries up-front instead of
    proxying to an underlying artifacts object. That avoids pickling edge cases
    (especially when used as an argument to ProcessPoolExecutor workers).

    Note: Tests and unit tests are intentionally excluded from this filtered view.
    Tests should be handled separately via write_incremental_tests() to avoid
    reprocessing all tests on every incremental model sync.
    """

    def __init__(self, artifacts: DbtArtifacts, model_ids: Sequence[str]) -> None:
        """Create a filtered artifacts view that only includes the given model IDs."""
        model_id_set = set(model_ids)

        self.project_name = artifacts.project_name
        self.adapter_type = artifacts.adapter_type
        self.target_name = artifacts.target_name
        self.project_root = artifacts.project_root

        self._models: Dict[str, DbtModelNode] = {
            m.unique_id: m for m in artifacts.iter_models() if m.unique_id in model_id_set
        }
        self._sources: Dict[str, DbtSourceNode] = {s.unique_id: s for s in artifacts.iter_sources()}
        self._macros: Dict[str, DbtMacroNode] = {m.unique_id: m for m in artifacts.iter_macros()}
        # Tests are intentionally empty - handle via write_incremental_tests() separately
        self._tests: Dict[str, DbtTestNode] = {}
        self._unit_tests: Dict[str, DbtUnitTestNode] = {}

        self.model_count = len(self._models)
        self.source_count = len(self._sources)
        self.macro_count = len(self._macros)
        self.test_count = 0
        self.unit_test_count = 0
        self._full_relation_lookup = artifacts.relation_lookup()
        self._full_sqlglot_schema = artifacts.sqlglot_schema()

    def iter_models(self) -> Iterator[DbtModelNode]:
        """Iterate filtered dbt models (including seeds)."""
        yield from self._models.values()

    def iter_sources(self) -> Iterator[DbtSourceNode]:
        """Iterate dbt sources (unfiltered)."""
        yield from self._sources.values()

    def iter_macros(self) -> Iterator[DbtMacroNode]:
        """Iterate dbt macros (unfiltered)."""
        yield from self._macros.values()

    def iter_tests(self) -> Iterator[DbtTestNode]:
        """Iterate dbt data tests (empty - tests handled via write_incremental_tests)."""
        yield from self._tests.values()

    def iter_unit_tests(self) -> Iterator[DbtUnitTestNode]:
        """Iterate dbt unit tests (empty - tests handled via write_incremental_tests)."""
        yield from self._unit_tests.values()

    def iter_seeds(self) -> Iterator[DbtModelNode]:
        """Iterate filtered seed nodes."""
        for node in self._models.values():
            if node.resource_type == "seed":
                yield node

    def get_model(self, unique_id: str) -> Optional[DbtModelNode]:
        """Get a filtered model by unique_id."""
        return self._models.get(unique_id)

    def get_source(self, unique_id: str) -> Optional[DbtSourceNode]:
        """Get a source by unique_id."""
        return self._sources.get(unique_id)

    def get_macro(self, unique_id: str) -> Optional[DbtMacroNode]:
        """Get a macro by unique_id."""
        return self._macros.get(unique_id)

    def get_test(self, unique_id: str) -> Optional[DbtTestNode]:
        """Get a test by unique_id."""
        return self._tests.get(unique_id)

    def get_unit_test(self, unique_id: str) -> Optional[DbtUnitTestNode]:
        """Get a unit test by unique_id."""
        return self._unit_tests.get(unique_id)

    def relation_lookup(self) -> Dict[str, str]:
        """Build a normalized relation-name → unique_id lookup (models + sources)."""
        # Reuse the precomputed relation lookup from the full artifacts so that
        # incremental runs can resolve upstream relations even when models are filtered.
        return dict(self._full_relation_lookup)

    def sqlglot_schema(self) -> SqlglotSchema:
        """Return full schema (unfiltered, needed for upstream resolution)."""
        return self._full_sqlglot_schema

    @staticmethod
    def normalize_relation(value: str) -> str:
        """Normalize a relation identifier for matching (case/quoting insensitive)."""
        return value.replace("`", "").replace('"', "").replace("[", "").replace("]", "").lower()


class RawDbtArtifacts:
    """Typed container for dbt artifacts."""
    def __init__(
        self,
        config: DbtArtifactsConfig,
        manifest: Mapping,
        catalog: Mapping,
        run_results: Optional[Mapping],
    ):
        """Initialize artifacts by parsing manifest/catalog into typed nodes."""
        self.config = config
        self.manifest = manifest
        self.catalog = catalog
        self.run_results = run_results or {}

        # Extract metadata from manifest
        metadata = manifest.get("metadata", {})
        self.project_name = metadata.get("project_name")
        self.adapter_type = metadata.get("adapter_type", "duckdb")
        self.target_name = metadata.get("target_name", "dev")

        self.project_root = self.config.target_path.parent

        self._models = self._load_models()
        self._sources = self._load_sources()
        self._macros = self._load_macros()
        self._tests = self._load_tests()
        self._unit_tests = self._load_unit_tests()
        self.model_count = len(self._models)
        self.source_count = len(self._sources)
        self.macro_count = len(self._macros)
        self.test_count = len(self._tests)
        self.unit_test_count = len(self._unit_tests)

        # Lazy caches
        self._sqlglot_schema_cache: Optional[SqlglotSchema] = None

    def iter_models(self) -> Iterator[DbtModelNode]:
        """Iterate dbt models (including seeds)."""
        yield from self._models.values()

    def iter_sources(self) -> Iterator[DbtSourceNode]:
        """Iterate dbt sources."""
        yield from self._sources.values()

    def iter_macros(self) -> Iterator[DbtMacroNode]:
        """Iterate dbt macros."""
        yield from self._macros.values()

    def iter_tests(self) -> Iterator[DbtTestNode]:
        """Iterate dbt data tests."""
        yield from self._tests.values()

    def iter_unit_tests(self) -> Iterator[DbtUnitTestNode]:
        """Iterate dbt unit tests."""
        yield from self._unit_tests.values()

    def iter_seeds(self) -> Iterator[DbtModelNode]:
        """Iterate dbt seed nodes."""
        for node in self._models.values():
            if node.resource_type == "seed":
                yield node

    def get_model(self, unique_id: str) -> Optional[DbtModelNode]:
        """Get a model by unique_id."""
        return self._models.get(unique_id)

    def get_source(self, unique_id: str) -> Optional[DbtSourceNode]:
        """Get a source by unique_id."""
        return self._sources.get(unique_id)

    def get_macro(self, unique_id: str) -> Optional[DbtMacroNode]:
        """Get a macro by unique_id."""
        return self._macros.get(unique_id)

    def get_test(self, unique_id: str) -> Optional[DbtTestNode]:
        """Get a test by unique_id."""
        return self._tests.get(unique_id)

    def get_unit_test(self, unique_id: str) -> Optional[DbtUnitTestNode]:
        """Get a unit test by unique_id."""
        return self._unit_tests.get(unique_id)

    def relation_lookup(self) -> Dict[str, str]:
        """Build a normalized relation-name → unique_id lookup for models/sources."""
        mapping: Dict[str, str] = {}

        def register(node: DbtModelNode | DbtSourceNode) -> None:
            # Sources use 'identifier', models use 'alias' or 'name'
            if isinstance(node, DbtSourceNode):
                table_name = node.identifier
            else:
                table_name = node.alias or node.name

            candidates = {
                node.relation_name,
                f"{node.database}.{node.schema}.{table_name}" if node.database else None,
                f"{node.schema}.{table_name}" if node.schema else None,
                table_name,
                node.name,
            }
            for candidate in candidates:
                if not candidate:
                    continue
                normalized = self.normalize_relation(candidate)
                mapping[normalized] = node.unique_id

        for node in self._models.values():
            register(node)
        for node in self._sources.values():
            register(node)
        return mapping

    def sqlglot_schema(self) -> SqlglotSchema:
        """Build SQLGlot schema from models/sources.

        Returns an immutable SqlglotSchema that can be used with SQLGlot's
        qualify() and lineage functions via .to_dict().
        """
        if self._sqlglot_schema_cache is not None:
            return self._sqlglot_schema_cache

        self._sqlglot_schema_cache = SqlglotSchema.from_iterables(
            models=self._models.values(),
            sources=self._sources.values(),
        )
        return self._sqlglot_schema_cache

    def _load_models(self) -> Dict[str, DbtModelNode]:
        nodes = {}
        manifest_nodes = self.manifest.get("nodes", {})
        catalog_nodes = self.catalog.get("nodes", {})

        tests_index = self._build_tests_index()

        for unique_id, raw in manifest_nodes.items():
            if raw.get("resource_type") not in {"model", "seed"}:
                continue

            columns = self._merge_columns(unique_id, raw, catalog_nodes.get(unique_id, {}), tests_index)

            # Compute absolute paths
            original_path = raw.get("original_file_path")
            source_path = None
            if original_path:
                source_path = str((self.project_root / original_path).resolve())

            # Extract checksum if present
            checksum_raw = raw.get("checksum")
            checksum = None
            if checksum_raw:
                checksum = ChecksumInfo(
                    name=checksum_raw.get("name", "sha256"),
                    checksum=checksum_raw.get("checksum", ""),
                )

            node = DbtModelNode(
                unique_id=unique_id,
                name=raw.get("name"),
                resource_type=raw.get("resource_type"),
                description=raw.get("description"),
                tags=raw.get("tags", []),
                meta=raw.get("meta", {}),
                database=raw.get("database"),
                schema=raw.get("schema"),
                alias=raw.get("alias"),
                relation_name=raw.get("relation_name"),
                materialization=(raw.get("config") or {}).get("materialized"),
                depends_on_nodes=raw.get("depends_on", {}).get("nodes", []),
                depends_on_sources=raw.get("depends_on", {}).get("sources", []),
                depends_on_macros=raw.get("depends_on", {}).get("macros", []),
                compiled_sql=self._load_compiled_sql(raw),
                raw_sql=raw.get("raw_code") or raw.get("raw_sql"),  # raw_code for newer dbt, raw_sql for older
                columns=columns,
                original_path=original_path,
                source_path=source_path,
                compiled_path=self._resolve_compiled_path(raw),
                checksum=checksum,
            )

            if node.original_path:
                parts = [part for part in node.original_path.split("/") if part]
                if parts:
                    if parts[0] == "models" and len(parts) > 1:
                        node.declared_layer = parts[1]
                    else:
                        node.declared_layer = parts[0]

            nodes[unique_id] = node

        return nodes

    def _load_macros(self) -> Dict[str, DbtMacroNode]:
        """Load dbt macros from manifest."""
        macros: Dict[str, DbtMacroNode] = {}
        manifest_macros = self.manifest.get("macros", {})

        for unique_id, raw in manifest_macros.items():
            if raw.get("resource_type") != "macro":
                continue

            original_path = raw.get("original_file_path")
            source_path = None
            if original_path:
                source_path = str((self.project_root / original_path).resolve())

            macro_sql = raw.get("macro_sql")
            if macro_sql is None:
                # Some manifests use "sql" for macros; keep both for robustness.
                macro_sql = raw.get("sql")

            node = DbtMacroNode(
                unique_id=unique_id,
                name=raw.get("name"),
                resource_type=raw.get("resource_type"),
                description=raw.get("description"),
                tags=raw.get("tags", []),
                meta=raw.get("meta", {}),
                package_name=raw.get("package_name"),
                original_path=original_path,
                source_path=source_path,
                macro_sql=macro_sql,
                depends_on_macros=raw.get("depends_on", {}).get("macros", []),
            )

            macros[unique_id] = node

        return macros

    def _load_sources(self) -> Dict[str, DbtSourceNode]:
        sources = {}
        manifest_sources = self.manifest.get("sources", {})
        catalog_sources = self.catalog.get("sources", {})
        tests_index = self._build_tests_index()

        for unique_id, raw in manifest_sources.items():
            columns = self._merge_columns(unique_id, raw, catalog_sources.get(unique_id, {}), tests_index)
            sources[unique_id] = DbtSourceNode(
                unique_id=unique_id,
                name=raw.get("name"),
                resource_type=raw.get("resource_type"),
                description=raw.get("description"),
                tags=raw.get("tags", []),
                meta=raw.get("meta", {}),
                database=raw.get("database"),
                schema=raw.get("schema"),
                identifier=raw.get("identifier"),
                relation_name=raw.get("relation_name"),
                loader=raw.get("loader"),
                columns=columns,
            )
        return sources

    def _load_tests(self) -> Dict[str, DbtTestNode]:
        """Load dbt data tests from manifest.

        Data tests are in manifest.nodes with resource_type == "test".
        Generic tests have test_metadata with name and kwargs.
        Singular tests are custom SQL in tests/*.sql files.
        """
        tests: Dict[str, DbtTestNode] = {}
        manifest_nodes = self.manifest.get("nodes", {})

        for unique_id, raw in manifest_nodes.items():
            if raw.get("resource_type") != "test":
                continue

            # Extract test metadata for generic tests
            # Guard against malformed manifests where test_metadata is not a dict
            test_metadata = raw.get("test_metadata")
            if not isinstance(test_metadata, dict):
                test_metadata = {}
            test_name = test_metadata.get("name")
            test_kwargs = test_metadata.get("kwargs")
            # Ensure test_kwargs is a dict (guard against malformed data)
            if not isinstance(test_kwargs, dict):
                test_kwargs = None

            # Determine test type
            test_type = "generic" if test_metadata else "singular"

            # Extract column name (for column-scoped generic tests)
            column_name = raw.get("column_name")

            # Get primary model/source being tested from depends_on.nodes
            depends_on = raw.get("depends_on") or {}
            if not isinstance(depends_on, dict):
                depends_on = {}
            depends_on_nodes = depends_on.get("nodes") or []
            if not isinstance(depends_on_nodes, list):
                depends_on_nodes = []
            model_id = depends_on_nodes[0] if depends_on_nodes else None

            # For relationship tests, find the referenced model
            referenced_model_id = None
            if test_name == "relationships" and len(depends_on_nodes) > 1:
                # For relationship tests, the second dependency is the referenced model
                referenced_model_id = depends_on_nodes[1]

            # Extract config values
            config = raw.get("config") or {}
            if not isinstance(config, dict):
                config = {}
            severity = config.get("severity", "error")
            where_clause = config.get("where")
            store_failures = config.get("store_failures", False)

            tests[unique_id] = DbtTestNode(
                unique_id=unique_id,
                name=raw.get("name"),
                resource_type=raw.get("resource_type"),
                description=raw.get("description"),
                tags=raw.get("tags", []),
                meta=raw.get("meta", {}),
                test_type=test_type,
                test_name=test_name,
                column_name=column_name,
                model_id=model_id,
                referenced_model_id=referenced_model_id,
                test_kwargs=test_kwargs,
                severity=severity,
                where_clause=where_clause,
                store_failures=store_failures,
                original_path=raw.get("original_file_path"),
                compiled_sql=raw.get("compiled_sql") or raw.get("compiled_code"),
                depends_on_nodes=depends_on_nodes,
            )

        return tests

    def _load_unit_tests(self) -> Dict[str, DbtUnitTestNode]:
        """Load dbt unit tests from manifest (dbt v1.8+).

        Unit tests are in manifest.nodes with resource_type == "unit_test".
        They validate model logic with mocked inputs.
        """
        unit_tests: Dict[str, DbtUnitTestNode] = {}
        manifest_nodes = self.manifest.get("nodes", {})

        for unique_id, raw in manifest_nodes.items():
            if raw.get("resource_type") != "unit_test":
                continue

            # Get the model being tested
            depends_on = raw.get("depends_on") or {}
            if not isinstance(depends_on, dict):
                depends_on = {}
            depends_on_nodes = depends_on.get("nodes") or []
            if not isinstance(depends_on_nodes, list):
                depends_on_nodes = []
            model_id = depends_on_nodes[0] if depends_on_nodes else None

            unit_tests[unique_id] = DbtUnitTestNode(
                unique_id=unique_id,
                name=raw.get("name"),
                resource_type=raw.get("resource_type"),
                description=raw.get("description"),
                tags=raw.get("tags", []),
                meta=raw.get("meta", {}),
                model_id=model_id,
                given=raw.get("given"),
                expect=raw.get("expect"),
                overrides=raw.get("overrides"),
            )

        return unit_tests

    def _merge_columns(
        self,
        unique_id: str,
        manifest_node: Mapping,
        catalog_node: Mapping,
        tests_index: Mapping[str, List[str]],
    ) -> Dict[str, DbtColumn]:
        manifest_columns = manifest_node.get("columns", {})
        catalog_columns = catalog_node.get("columns", {})
        result: Dict[str, DbtColumn] = {}
        seen_lowercase: set[str] = set()  # Track columns by lowercase name

        for column_name, manifest_column in manifest_columns.items():
            catalog_column = catalog_columns.get(column_name, {})
            result[column_name] = DbtColumn(
                name=column_name,
                description=manifest_column.get("description"),
                data_type=catalog_column.get("type"),
                tests=tests_index.get(f"{unique_id}::{column_name}", []),
            )
            seen_lowercase.add(column_name.lower())

        for column_name, catalog_column in catalog_columns.items():
            # Check if we already have this column (case-insensitive)
            if column_name.lower() in seen_lowercase:
                continue
            result[column_name] = DbtColumn(
                name=column_name,
                description=None,
                data_type=catalog_column.get("type"),
                tests=tests_index.get(f"{unique_id}::{column_name}", []),
            )
            seen_lowercase.add(column_name.lower())

        return result

    def _build_tests_index(self) -> Mapping[str, List[str]]:
        results = self.run_results.get("results", [])
        mapping: Dict[str, List[str]] = {}
        for item in results:
            if item.get("resource_type") != "test":
                continue
            for node in item.get("depends_on", {}).get("nodes", []):
                column_name = item.get("column_name")
                key = f"{node}::{column_name}" if column_name else node
                mapping.setdefault(key, []).append(item.get("unique_id"))
        return mapping

    @staticmethod
    def normalize_relation(value: str) -> str:
        """Normalize a relation identifier for matching (case/quoting insensitive)."""
        return value.replace("`", "").replace('"', "").replace("[", "").replace("]", "").lower()

    def _load_compiled_sql(self, raw: Mapping) -> Optional[str]:
        compiled = raw.get("compiled_sql") or raw.get("compiled_code")
        if compiled:
            return compiled
        original_path = raw.get("original_file_path")
        if not original_path:
            return None
        project_name = self.manifest.get("metadata", {}).get("project_name")
        if not project_name:
            return None
        candidate = self.config.target_path / "run" / project_name / original_path
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
        return None

    def _resolve_compiled_path(self, raw: Mapping) -> Optional[str]:
        compiled_path = raw.get("compiled_path")
        if compiled_path:
            return str((self.project_root / compiled_path).resolve())
        original = raw.get("original_file_path")
        if not original:
            return None
        candidate = self.config.target_path / "run"
        if self.project_name:
            candidate = candidate / self.project_name
        candidate = candidate / original
        return str(candidate.resolve())

    def __str__(self) -> str:
        """Human-readable summary for debugging."""
        return f"RawDbtArtifacts(config={self.config}, manifest={self.manifest}, catalog={self.catalog}, run_results={self.run_results}, project_name={self.project_name}, project_root={self.project_root}, models={self._models}"


class DbtLoader:
    """Loader for dbt artifacts from a `target/` directory."""
    def __init__(self, config: DbtArtifactsConfig):
        """Create a loader with a configured artifacts path."""
        self.config = config

    def load(self) -> RawDbtArtifacts:
        """Load manifest/catalog/run_results into a `RawDbtArtifacts` object."""
        manifest = self._load_json(self.config.manifest_path())
        # Be forgiving if catalog.json is not present (dbt docs generate not run)
        catalog = self._try_load_json(self.config.catalog_path()) or {}
        run_results_path = self.config.run_results_path()
        run_results = self._load_json(run_results_path) if run_results_path.exists() else {}
        return RawDbtArtifacts(config=self.config, manifest=manifest, catalog=catalog, run_results=run_results)

    @staticmethod
    def _load_json(path: Path) -> Mapping:
        """Load a JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"dbt artifact not found: {path}")
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    @staticmethod
    def _try_load_json(path: Path) -> Optional[Mapping]:
        """Try loading a JSON file, returning None if it does not exist."""
        try:
            return DbtLoader._load_json(path)
        except FileNotFoundError:
            return None


    