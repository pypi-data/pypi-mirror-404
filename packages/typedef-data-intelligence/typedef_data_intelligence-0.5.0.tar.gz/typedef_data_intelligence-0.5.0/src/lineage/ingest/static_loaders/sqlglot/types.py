"""Type definitions for SQLGlot-based analysis."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)

# Raw dict type for SQLGlot compatibility
SqlglotSchemaDict = Dict[str, Dict[str, Dict[str, Dict[str, str]]]]


class ColumnProvider(Protocol):
    """Protocol for objects that provide column information."""

    name: str
    data_type: Optional[str]


class TableProvider(Protocol):
    """Protocol for objects that provide table/model information for schema building."""

    database: Optional[str]
    schema: Optional[str]
    name: str
    columns: Dict[str, ColumnProvider]


class ModelTableProvider(TableProvider, Protocol):
    """Extended protocol for dbt models that may have an alias."""

    alias: Optional[str]


class SourceTableProvider(TableProvider, Protocol):
    """Extended protocol for dbt sources that have an identifier."""

    identifier: str


@dataclass(frozen=True, slots=True)
class TableEntry:
    """Immutable entry representing a table's schema information."""

    database: str
    schema: str
    table: str
    columns: Tuple[Tuple[str, str], ...]  # ((col_name, data_type), ...)

    @classmethod
    def from_model(cls, model: ModelTableProvider) -> Optional["TableEntry"]:
        """Create a TableEntry from a dbt model node.

        Args:
            model: A model-like object with database, schema, alias/name, and columns.

        Returns:
            TableEntry if the model has columns, None otherwise.
        """
        if not model.columns:
            logger.debug("Skipping model %s: no columns", model.name)
            return None

        table_name = model.alias or model.name
        columns = tuple(
            (col.name, col.data_type or "unknown")
            for col in model.columns.values()
        )

        return cls(
            database=model.database or "",
            schema=model.schema or "",
            table=table_name,
            columns=columns,
        )

    @classmethod
    def from_source(cls, source: SourceTableProvider) -> Optional["TableEntry"]:
        """Create a TableEntry from a dbt source node.

        Args:
            source: A source-like object with database, schema, identifier/name, and columns.

        Returns:
            TableEntry if the source has columns, None otherwise.
        """
        if not source.columns:
            logger.debug("Skipping source %s: no columns", source.name)
            return None

        table_name = source.identifier or source.name
        columns = tuple(
            (col.name, col.data_type or "unknown")
            for col in source.columns.values()
        )

        return cls(
            database=source.database or "",
            schema=source.schema or "",
            table=table_name,
            columns=columns,
        )


@dataclass(frozen=True, slots=True)
class SqlglotSchema:
    """Immutable schema container for SQLGlot operations.

    This class encapsulates the nested dict structure required by SQLGlot's
    qualify() and lineage functions: {database: {schema: {table: {column: type}}}}.

    The schema is built once from dbt models and sources, then provides
    defensive copies when needed for SQLGlot operations.

    Example:
        schema = SqlglotSchema.from_artifacts(artifacts)
        qualified_expr = qualify(expr, schema=schema.to_dict(), dialect="snowflake")
    """

    _entries: Tuple[TableEntry, ...] = field(default_factory=tuple)

    @classmethod
    def from_iterables(
        cls,
        models: Iterable[ModelTableProvider],
        sources: Iterable[SourceTableProvider],
    ) -> "SqlglotSchema":
        """Build a schema from model and source iterables.

        Args:
            models: Iterable of dbt model nodes (or model-like objects).
            sources: Iterable of dbt source nodes (or source-like objects).

        Returns:
            An immutable SqlglotSchema containing all tables with columns.
        """
        entries = []

        for model in models:
            entry = TableEntry.from_model(model)
            if entry is not None:
                entries.append(entry)

        for source in sources:
            entry = TableEntry.from_source(source)
            if entry is not None:
                entries.append(entry)

        return cls(_entries=tuple(entries))

    def to_dict(self) -> SqlglotSchemaDict:
        """Return a fresh dict copy suitable for SQLGlot functions.

        SQLGlot's qualify() and lineage functions expect a nested dict
        in the format: {database: {schema: {table: {column: type}}}}.

        Returns:
            A new dict (defensive copy) that can be safely mutated.
        """
        result: SqlglotSchemaDict = {}

        for entry in self._entries:
            if entry.database not in result:
                result[entry.database] = {}
            if entry.schema not in result[entry.database]:
                result[entry.database][entry.schema] = {}

            result[entry.database][entry.schema][entry.table] = dict(entry.columns)

        return result

    def __len__(self) -> int:
        """Return the number of tables in the schema."""
        return len(self._entries)

    def __bool__(self) -> bool:
        """Return True if the schema has any tables."""
        return len(self._entries) > 0

    def __repr__(self) -> str:
        """Return a string representation for debugging."""
        return f"SqlglotSchema({len(self._entries)} tables)"

    @property
    def table_count(self) -> int:
        """Return the number of tables in the schema."""
        return len(self._entries)


__all__ = ["SqlglotSchema", "SqlglotSchemaDict", "TableEntry"]
