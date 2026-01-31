"""Pydantic models for dbt nodes (models, sources, columns, macros, tests).

These models represent the static metadata from dbt projects:
- DbtModel: dbt models (tables, views, incremental models, seeds)
- DbtSource: dbt sources (external data sources)
- DbtColumn: Columns from models and sources
- DbtMacro: dbt macro definitions
- DbtTest: dbt data tests (generic and singular)
- DbtUnitTest: dbt unit tests (dbt v1.8+)
"""

from typing import Any, ClassVar, Optional

from pydantic import Field, computed_field, field_validator

from lineage.backends.lineage.models.base import BaseNode, NodeIdentifier
from lineage.backends.types import NodeLabel


class DbtModel(BaseNode):
    """dbt model node (LOGICAL definition only).

    Represents the logical dbt model definition from the dbt project.
    This is separate from physical warehouse materializations (see PhysicalRelation).

    A single DbtModel can be deployed to multiple environments (dev, staging, prod),
    each creating a separate PhysicalRelation node connected via BUILDS edges.

    Properties:
        name: Logical model name
        materialization: How dbt should materialize this (table, view, incremental, etc.)
        unique_id: dbt's unique identifier (e.g., "model.project_name.model_name")
        description: Description of the model
        original_path: Path to .sql file in dbt project
        source_path: Absolute path to source file
        compiled_path: Path to compiled SQL
        checksum: SHA-256 checksum of raw model SQL from dbt manifest (legacy incremental signal)
        model_fingerprint: Model fingerprint used for incremental gating (initially derived from compiled SQL)

    Physical properties (database, schema, relation_name) are stored in PhysicalRelation.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_MODEL

    # Core logical properties
    name: str = ""
    materialization: str = ""  # table, view, incremental, ephemeral, seed (logical concept)
    unique_id: str = ""  # dbt unique identifier
    description: Optional[str] = None

    # dbt project file paths
    original_path: Optional[str] = None  # Path to .sql file in project
    source_path: Optional[str] = None  # Absolute path to source file
    compiled_path: Optional[str] = None  # Path to compiled SQL

    checksum: Optional[str] = Field(
        None,
        description="Original dbt manifest checksum (SHA-256 of raw model SQL)",
    )
    model_fingerprint: Optional[str] = Field(
        None,
        description="Compiled SQL fingerprint hash (SHA-256, no prefix) for change detection",
    )
    fingerprint_type: Optional[str] = Field(
        None,
        description="Fingerprint method: canonical, fallback, seed, raw_checksum",
    )
    fingerprint_dialect: Optional[str] = Field(
        None,
        description="SQL dialect used for fingerprint computation (e.g., duckdb, snowflake)",
    )

    # SQL code (matches dbt naming conventions)
    raw_sql: Optional[str] = None  # Original SQL from .sql file
    compiled_sql: Optional[str] = None  # Compiled SQL after dbt processing
    canonical_sql: Optional[str] = Field(
        None,
        description="Clean, physically-agnostic SQL (stripped db/catalog). "
        "Used for stable fingerprinting and token-efficient LLM analysis.",
    )
    qualified_sql: Optional[str] = Field(
        None,
        description="Schema-qualified, fully resolved SQL (preserves physical references). "
        "Used for high-fidelity column lineage and debugging.",
    )

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from dbt unique_id."""
        if self.unique_id:
            return self.unique_id
        # Fallback: use name if unique_id not set
        return f"dbt_model.{self.name}"


    @classmethod
    def identifier(cls, unique_id: str) -> "NodeIdentifier":
        """Create NodeIdentifier from unique_id.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            unique_id: Model unique ID (e.g., "model.package.model_name")

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = DbtModel.identifier("model.demo.orders")
            storage.create_edge(from_node, identifier, edge)
            ```
        """
        temp = cls(unique_id=unique_id)
        return temp.get_node_identifier()

class DbtSource(BaseNode):
    """dbt source node (LOGICAL definition only).

    Represents the logical dbt source definition from sources.yml.
    Sources are external tables that exist outside of dbt (loaded by ETL tools).

    Like DbtModel, a DbtSource is separate from its physical warehouse table(s).
    Physical properties are stored in PhysicalRelation.

    Properties:
        name: Logical source name
        loader: ETL tool that loads this source (e.g., "fivetran", "stitch")
        unique_id: dbt's unique identifier (e.g., "source.project.source_name.table_name")
        source_fingerprint: Fingerprint hash based on schema location and columns
        fingerprint_type: Always "source" for DbtSource nodes

    Physical properties (database, schema, identifier) are stored in PhysicalRelation.
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_SOURCE

    # Core logical properties
    name: str = ""
    loader: Optional[str] = None  # ETL tool that loads this source
    unique_id: str = ""  # dbt unique identifier
    description: Optional[str] = None

    # Fingerprint for incremental change detection
    source_fingerprint: Optional[str] = Field(
        None,
        description="Fingerprint hash based on schema location (database/schema/identifier) and column definitions",
    )
    fingerprint_type: Optional[str] = Field(
        None,
        description="Fingerprint method (always 'source' for DbtSource)",
    )

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from dbt unique_id."""
        if self.unique_id:
            return self.unique_id
        # Fallback: use name if unique_id not set
        return f"dbt_source.{self.name}"

    @classmethod
    def identifier(cls, unique_id: str) -> "NodeIdentifier":
        """Create NodeIdentifier from unique_id.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            unique_id: Source unique ID (e.g., "source.package.source_name.table_name")

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = DbtSource.identifier("source.demo.raw.orders")
            storage.create_edge(from_node, identifier, edge)
            ```
        """
        temp = cls(unique_id=unique_id)
        return temp.get_node_identifier()

class DbtColumn(BaseNode):
    """Column from a dbt model or source (LOGICAL definition).

    Represents the logical column definition from the dbt project.
    This is separate from physical warehouse columns (see PhysicalColumn).

    Physical columns (with actual warehouse data types, statistics, etc.) are
    stored in PhysicalColumn nodes, which DERIVE_FROM these logical columns.

    Properties:
        name: Column name
        parent_id: ID of parent DbtModel or DbtSource
        parent_label: "DbtModel" or "DbtSource"
        data_type: Logical data type from dbt schema.yml

    The ID is constructed as: {parent_id}.{column_name_lowercase}
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_COLUMN

    # Core properties
    name: str = ""
    description: Optional[str] = None
    parent_id: str = ""  # ID of parent DbtModel or DbtSource
    parent_label: str = ""  # "DbtModel" or "DbtSource"
    data_type: Optional[str] = None  # Logical data type from schema.yml

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID: {parent_id}.{column_name_lowercase}."""
        if not self.name:
            return self.parent_id
        return f"{self.parent_id}.{self.name.lower()}"

    @classmethod
    def identifier(cls, parent_id: str, column_name: str) -> "NodeIdentifier":
        """Create NodeIdentifier from parent_id and column_name.

        Uses the id property to ensure single source of truth for ID format.

        Args:
            parent_id: Parent model or source unique ID
            column_name: Column name

        Returns:
            NodeIdentifier with correct ID and label

        Example:
            ```python
            identifier = DbtColumn.identifier("model.demo.orders", "customer_id")
            storage.create_edge(from_node, identifier, edge)
            ```
        """
        temp = cls(name=column_name, parent_id=parent_id)
        return temp.get_node_identifier()

class DbtMacro(BaseNode):
    """dbt macro node (LOGICAL definition).

    Represents a macro definition from the dbt manifest. In macro-heavy projects,
    macro dependencies are critical to understand why compiled SQL changes even
    when model SQL text is unchanged.

    Properties:
        name: Macro name
        unique_id: dbt macro unique identifier (e.g., "macro.package.macro_name")
        package_name: Package that defines this macro
        original_path: Path to macro file in project
        source_path: Absolute path to macro file
        macro_sql: Macro SQL definition (as provided by dbt manifest, when present)
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_MACRO

    name: str = ""
    unique_id: str = ""
    description: Optional[str] = None
    package_name: Optional[str] = None
    original_path: Optional[str] = None
    source_path: Optional[str] = None
    macro_sql: Optional[str] = None

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from dbt unique_id."""
        if self.unique_id:
            return self.unique_id
        return f"dbt_macro.{self.name}"

    @classmethod
    def identifier(cls, unique_id: str) -> "NodeIdentifier":
        """Create a NodeIdentifier for a macro unique_id."""
        temp = cls(unique_id=unique_id)
        return temp.get_node_identifier()


class DbtTest(BaseNode):
    """dbt data test node (generic or singular).

    Represents a data test defined in the dbt project. Generic tests (unique, not_null,
    accepted_values, relationships) have test_metadata with name and kwargs.
    Singular tests are custom SQL in tests/*.sql files.

    Properties:
        name: Test name (e.g., "unique_orders_order_id" or singular test filename)
        unique_id: dbt's unique identifier (e.g., "test.project.unique_orders_order_id")
        test_type: "generic" or "singular"
        test_name: For generic tests, the test macro name (unique, not_null, etc.)
        column_name: Column being tested (for column-scoped generic tests)
        model_id: Primary model/source being tested (from depends_on.nodes[0])
        referenced_model_id: For relationship tests, the referenced model/source
        test_kwargs: For generic tests, the kwargs dict (e.g., {"to": "ref('other')", "field": "id"})
        severity: "error" or "warn" (from test config)
        tags: Test tags from config
        where_clause: Optional WHERE filter from test config
        store_failures: Whether test stores failures (from config)
        original_path: Path to test SQL file (for singular tests)
        compiled_sql: Compiled test SQL
        test_fingerprint: Fingerprint for change detection
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_TEST

    name: str = ""
    unique_id: str = ""
    description: Optional[str] = None

    # Test classification
    test_type: str = "generic"  # "generic" or "singular"
    test_name: Optional[str] = None  # e.g., "unique", "not_null", "accepted_values", "relationships"

    # Test target
    column_name: Optional[str] = None  # Column being tested (if column-scoped)
    model_id: Optional[str] = None  # Primary model/source tested
    referenced_model_id: Optional[str] = None  # For relationship tests: the "to" target

    # Test config
    severity: str = "error"  # "error" or "warn"
    tags: list[str] = Field(default_factory=list)
    where_clause: Optional[str] = None
    store_failures: bool = False

    @field_validator("store_failures", mode="before")
    @classmethod
    def _coerce_store_failures(cls, v: Any) -> bool:
        """Coerce None to False for store_failures."""
        return bool(v) if v is not None else False

    # Test kwargs (for generic tests)
    test_kwargs: Optional[dict[str, Any]] = None

    # File paths and SQL
    original_path: Optional[str] = None
    compiled_sql: Optional[str] = None

    # Fingerprint for incremental loading
    test_fingerprint: Optional[str] = Field(
        None,
        description="Test config fingerprint hash (SHA-256) for change detection",
    )
    fingerprint_type: Optional[str] = Field(
        None,
        description="Fingerprint method (always 'test_config' for DbtTest)",
    )

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from dbt unique_id."""
        if self.unique_id:
            return self.unique_id
        return f"dbt_test.{self.name}"

    @classmethod
    def identifier(cls, unique_id: str) -> "NodeIdentifier":
        """Create NodeIdentifier from unique_id."""
        temp = cls(unique_id=unique_id)
        return temp.get_node_identifier()


class DbtUnitTest(BaseNode):
    """dbt unit test node (dbt v1.8+).

    Represents a unit test that validates model logic with mocked inputs.
    Unit tests are defined in YAML under models/ and use the resource_type "unit_test".

    Properties:
        name: Unit test name
        unique_id: dbt's unique identifier
        model_id: Model being tested
        description: Test description
        given: Input definitions (mocked data)
        expect: Expected output
        overrides: Model overrides
        tags: Test tags
        test_fingerprint: Fingerprint for change detection
    """

    node_label: ClassVar[NodeLabel] = NodeLabel.DBT_UNIT_TEST

    name: str = ""
    unique_id: str = ""
    description: Optional[str] = None
    model_id: Optional[str] = None
    given: Optional[list[dict[str, Any]]] = None
    expect: Optional[dict[str, Any]] = None
    overrides: Optional[dict[str, Any]] = None
    tags: list[str] = Field(default_factory=list)

    # Fingerprint for incremental loading
    test_fingerprint: Optional[str] = Field(
        None,
        description="Unit test config fingerprint hash (SHA-256) for change detection",
    )

    @computed_field
    @property
    def id(self) -> str:
        """Generate unique ID from dbt unique_id."""
        if self.unique_id:
            return self.unique_id
        return f"dbt_unit_test.{self.name}"

    @classmethod
    def identifier(cls, unique_id: str) -> "NodeIdentifier":
        """Create NodeIdentifier from unique_id."""
        temp = cls(unique_id=unique_id)
        return temp.get_node_identifier()


__all__ = ["DbtModel", "DbtSource", "DbtColumn", "DbtMacro", "DbtTest", "DbtUnitTest"]
