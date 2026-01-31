"""Column-level lineage extraction using sqlglot."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError
from sqlglot.lineage import Node as LineageNode
from sqlglot.lineage import lineage as lineage_for_column
from sqlglot.optimizer import annotate_types, canonicalize, qualify

from lineage.backends.types import Confidence
from lineage.ingest.static_loaders.sqlglot.types import SqlglotSchema

logger = logging.getLogger(__name__)

# Fingerprint type constants (stored separately from hash)
class FingerprintType:
    """Fingerprint type identifiers."""

    CANONICAL = "canonical"  # sqlglot successfully parsed SQL
    FALLBACK = "fallback"  # sqlglot failed, used text normalization
    SEED = "seed"  # seed model, used dbt checksum
    RAW_CHECKSUM = "raw_checksum"  # no compiled SQL, used dbt checksum
    SOURCE = "source"  # source fingerprint based on schema/columns


@dataclass(slots=True)
class FingerprintResult:
    """Result of fingerprint computation with metadata.

    Separating the hash from metadata enables:
    - Detecting fingerprint type changes without triggering false positive "modified"
    - Auditing fingerprint quality across the project
    - Future: invalidation based on dialect/sqlglot version changes

    Attributes:
        hash: The SHA-256 hash value (without prefix)
        type: Fingerprint type (canonical, fallback, seed, raw_checksum, source)
        dialect: SQL dialect used for parsing (if applicable)
    """

    hash: str
    type: str  # One of FingerprintType values
    dialect: Optional[str] = None


@dataclass(slots=True)
class SourceColumn:
    """Represents a column in an upstream relation."""

    table: str
    column: str

    @property
    def qualified_name(self) -> str:
        """Return `table.column` when table is known, otherwise just `column`."""
        return f"{self.table}.{self.column}" if self.table else self.column


@dataclass(slots=True)
class ColumnLineage:
    """Column-level lineage information for a single target column."""

    target_column: str
    sources: List[SourceColumn]
    expression: Optional[str]
    confidence: Confidence = Confidence.DIRECT


def _leaf_nodes(node: LineageNode) -> Iterable[LineageNode]:
    if not node.downstream:
        yield node
        return

    for child in node.downstream:
        yield from _leaf_nodes(child)


def _expression_sql(expression: exp.Exp | None) -> Optional[str]:
    if not expression:
        return None
    try:
        return expression.sql(pretty=False)
    except Exception:  # pragma: no cover - defensive
        return None

@lru_cache(maxsize=4096)
def _parse_sql_internal(sql: str, dialect: Optional[str] = None) -> exp.Expression:
    """Internal LRU-cached SQL parsing helper.

    This function is memoized and returns the cached sqlglot expression
    instance for a given (sql, dialect) pair. Callers MUST treat the returned
    object as internal and potentially shared. External code should use
    :func:`parse_sql_cached` instead, which returns a defensive copy of the
    parsed expression to avoid mutating cached state.
    """
    return sqlglot.parse_one(sql, read=dialect)


def parse_sql_cached(sql: str, dialect: Optional[str] = None) -> exp.Expression:
    """Parse SQL with LRU caching for performance.

    This function uses a global cache so that repeated parsing of the same SQL
    (e.g., during canonicalization, lineage extraction, and semantic analysis)
    only parses once.

    Performance tradeoff:
        The cache stores parsed ASTs and returns a copy() on each call to prevent
        mutation of cached objects. This is necessary because SQLGlot ASTs are
        mutable and callers (e.g., qualify()) modify them in place. The copy()
        adds allocation overhead but avoids re-parsing, which is the expensive
        operation (~10-100x slower than copy depending on query complexity).

    Args:
        sql: SQL query string to parse
        dialect: SQL dialect (e.g., "snowflake", "bigquery", "duckdb")

    Returns:
        Parsed SQLGlot expression (a fresh copy from the cache)

    Raises:
        SqlglotError: If SQL cannot be parsed
    """
    return _parse_sql_internal(sql, dialect).copy()


def _iter_select_columns(expression: exp.Expression) -> Iterable[str]:
    select = expression.find(exp.Select)
    if not select:
        return []

    for projection in select.expressions:
        alias = projection.alias_or_name
        if alias:
            yield alias


def extract_column_lineage(
    expression: exp.Expression,
    dialect: Optional[str] = None,
    schema: Optional[SqlglotSchema] = None,
    is_pre_qualified: bool = False,
) -> Dict[str, ColumnLineage]:
    """Extract lineage for each projected column in the query.

    Args:
        expression: Pre-parsed SQL expression
        dialect: SQL dialect (optional, for lineage analysis)
        schema: SqlglotSchema instance for SELECT * expansion via qualify().
        is_pre_qualified: If True, skip qualify() call - expression is already
            fully qualified (schema-qualified and SELECT * expanded).

    Returns:
        A mapping of target column names to lineage metadata.
    """
    result: Dict[str, ColumnLineage] = {}

    # Convert schema to dict for SQLGlot functions
    # Always use the physical schema mapping for lineage accuracy
    schema_dict = schema.to_dict() if schema else None

    # Skip qualify if expression is already from qualified_sql (pre-qualified)
    if is_pre_qualified:
        qualified_expression = expression
    elif schema_dict:
        # Use qualify() to expand SELECT * wildcards
        mutable_expression = expression.copy()
        try:
            mutable_expression = qualify(
                mutable_expression,
                schema=schema_dict,
                dialect=dialect,
                validate_qualify_columns=False,  # Don't fail on missing columns
            )
            qualified_expression = mutable_expression
        except SqlglotError as e:
            # Fall back to original expression if qualify fails
            logger.warning(f"qualify() failed, using original expression: {e}")
            qualified_expression = expression
    else:
        qualified_expression = expression

    for column in _iter_select_columns(qualified_expression):
        try:
            graph = lineage_for_column(
                column, qualified_expression, dialect=dialect, schema=schema_dict, copy=True
            )
        except SqlglotError as e:
            # Skip columns we cannot analyse to keep pipeline resilient
            logger.warning(f"Skipping column {column} in expression {type(expression).__name__} (dialect={dialect}) because it cannot be analysed: {e}")
            continue

        sources: List[SourceColumn] = []
        for node in _leaf_nodes(graph):
            if not node.name:
                continue
            parts = node.name.split(".")
            if len(parts) == 1:
                sources.append(SourceColumn(table="", column=parts[0]))
            else:
                table = ".".join(parts[:-1])
                sources.append(SourceColumn(table=table, column=parts[-1]))

        result[column] = ColumnLineage(
            target_column=column,
            sources=sources,
            expression=_expression_sql(graph.expression),
        )

    return result


def normalize_sql(
    sql: str,
    dialect: Optional[str] = None,
    schema: Optional[SqlglotSchema] = None,
    physically_agnostic: bool = True,
) -> str:
    """Normalize SQL into a stable string form with qualification, stripping, and semantic optimization.

    This is the core implementation for all SQL normalization variants. It performs:
    1. Parsing (dialect-aware)
    2. Qualification (SELECT * expansion, column resolution) if schema provided
    3. Physical Stripping (database/catalog removal) if physically_agnostic=True
    4. Type Annotation (for robust canonicalization)
    5. Semantic Canonicalization (standardizing expressions)

    Args:
        sql: SQL query string to normalize
        dialect: SQL dialect (e.g., 'snowflake', 'duckdb')
        schema: Optional SqlglotSchema for column qualification and SELECT * expansion.
        physically_agnostic: If True, strip catalog/database references from tables while
            preserving schema names, to make the form independent of the physical environment.
    """
    # 1) Parse (uses global LRU cache)
    expression = parse_sql_cached(sql, dialect)

    # 2) Qualify tables/columns only if schema is provided
    if schema:
        schema_dict = schema.to_dict()
        try:
            expression = qualify.qualify(
                expression,
                schema=schema_dict,
                dialect=dialect,
                validate_qualify_columns=False,  # Don't fail on missing columns
            )
        except SqlglotError as e:
            # Fall back to unqualified if qualify fails
            logger.debug(f"qualify() failed during normalization: {e}")

    # 3) Physically agnostic: strip catalog only after qualification
    # We preserve the schema name to disambiguate tables with the same name
    # in different schemas (e.g. raw.orders vs staging.orders).
    if physically_agnostic:
        # Strip catalog (top-level database) but keep schema
        for table in expression.find_all(exp.Table):
            table.set("catalog", None)

    # 4) Annotate types before canonicalize (required for robust expression matching)
    try:
        expression = annotate_types.annotate_types(expression, dialect=dialect)
    except SqlglotError:
        # Fall back to unannotated if type annotation fails
        pass

    # 5) Canonical form (standardizes expressions; semantics-preserving)
    # This standardizes things like X + 1 vs 1 + X to ensure stable fingerprints.
    expression = canonicalize.canonicalize(expression, dialect=dialect)

    # 6) Render in a compact, stable, and token-efficient form.
    # identify=False ensures we don't over-quote identifiers.
    # comments=True preserves semantic hints for LLM analysis and change detection.
    return expression.sql(dialect=dialect, pretty=False, identify=False, comments=True)


def canonicalize_sql(
    sql: str, dialect: Optional[str] = None, schema: Optional[SqlglotSchema] = None
) -> str:
    """Produce clean, physically-agnostic SQL (logic-only).

    Matches the 'canonical_sql' property on DbtModel.
    Used for stable fingerprints and token-efficient LLM analysis.
    """
    return normalize_sql(sql, dialect=dialect, schema=schema, physically_agnostic=True)


def qualify_sql(
    sql: str, dialect: Optional[str] = None, schema: Optional[SqlglotSchema] = None
) -> str:
    """Produce fully-qualified physical SQL.

    Matches the 'qualified_sql' property on DbtModel.
    Used for high-fidelity column lineage and physical debugging.
    """
    return normalize_sql(sql, dialect=dialect, schema=schema, physically_agnostic=False)


@dataclass(frozen=True)
class NormalizedSQLPair:
    """Both SQL forms produced from a single normalization pass."""

    qualified: str  # Fully-qualified physical SQL (catalog preserved)
    canonical: str  # Physically-agnostic SQL (catalog stripped)


def normalize_sql_pair(
    sql: str,
    dialect: Optional[str] = None,
    schema: Optional[SqlglotSchema] = None,
) -> NormalizedSQLPair:
    """Normalize SQL and return both qualified and canonical forms in one pass.

    Avoids the expensive qualify() + annotate_types() running twice by producing
    both forms from a single normalization pipeline.

    Args:
        sql: SQL query string to normalize
        dialect: SQL dialect (e.g., 'snowflake', 'duckdb')
        schema: Optional SqlglotSchema for column qualification and SELECT * expansion.

    Returns:
        NormalizedSQLPair with .qualified and .canonical attributes
    """
    expression = parse_sql_cached(sql, dialect)

    if schema:
        schema_dict = schema.to_dict()
        try:
            expression = qualify.qualify(
                expression,
                schema=schema_dict,
                dialect=dialect,
                validate_qualify_columns=False,
            )
        except SqlglotError as e:
            logger.debug(f"qualify() failed during normalization: {e}")

    try:
        expression = annotate_types.annotate_types(expression, dialect=dialect)
    except SqlglotError as e:
        # Type inference is best-effort; continue without annotated types if it fails.
        logger.debug(f"annotate_types() failed during normalization: {e}")

    expression = canonicalize.canonicalize(expression, dialect=dialect)

    # Render qualified form (catalog preserved)
    qualified = expression.sql(dialect=dialect, pretty=False, identify=False, comments=True)

    # Strip catalog in-place (expression not reused after this), render canonical form
    for table in expression.find_all(exp.Table):
        table.set("catalog", None)
    canonical = expression.sql(dialect=dialect, pretty=False, identify=False, comments=True)

    return NormalizedSQLPair(qualified=qualified, canonical=canonical)


def compute_model_fingerprint_result(
    resource_type: str,
    compiled_sql: Optional[str] = None,
    checksum: Optional[str] = None,
    dialect: Optional[str] = None,
    schema: Optional[SqlglotSchema] = None,
    model_id: Optional[str] = None,
) -> Optional[FingerprintResult]:
    """Compute fingerprint for a dbt model with full metadata.

    This is the preferred function - returns FingerprintResult with hash, type, and dialect
    separated for better change detection and auditing.

    Args:
        resource_type: dbt resource type (e.g., "seed", "model")
        compiled_sql: Compiled SQL string (required for non-seed models)
        checksum: Checksum string (used for seed models)
        dialect: SQL dialect for compiled SQL parsing.
        schema: Optional SqlglotSchema for macro-aware fingerprinting (expands SELECT *).
        model_id: Optional model unique_id for error logging

    Returns:
        FingerprintResult with hash and metadata, or None if model cannot be fingerprinted
    """
    # Seeds frequently have no compiled SQL; use the seed checksum as a stable fingerprint.
    if resource_type == "seed":
        if checksum:
            return FingerprintResult(
                hash=checksum,
                type=FingerprintType.SEED,
                dialect=None,
            )
        return None

    # Models without compiled_sql cannot be fingerprinted
    if not compiled_sql:
        if checksum:
            return FingerprintResult(
                hash=checksum,
                type=FingerprintType.RAW_CHECKSUM,
                dialect=None,
            )
        return None

    # Parse and canonicalize compiled_sql (physically agnostic, macro-aware if schema provided)
    try:
        canonical = canonicalize_sql(compiled_sql, dialect=dialect, schema=schema)
        hash_value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return FingerprintResult(
            hash=hash_value,
            type=FingerprintType.CANONICAL,
            dialect=dialect,
        )
    except SqlglotError:
        # Fallback: normalize text-based SQL (not semantically aware)
        normalized = re.sub(r"--[^\n]*", "", compiled_sql)
        normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        hash_value = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        logger.warning(
            f"Using fallback fingerprint for unparseable SQL (dialect={dialect}, model_id={model_id})"
        )
        return FingerprintResult(
            hash=hash_value,
            type=FingerprintType.FALLBACK,
            dialect=dialect,
        )
    except Exception as e:
        model_ref = f" for {model_id}" if model_id else ""
        logger.warning(f"Failed to compute fingerprint{model_ref}: {e}")
        return None


def compute_source_fingerprint(
    database: Optional[str],
    schema: Optional[str],
    identifier: str,
    columns: Optional[Dict[str, Optional[str]]] = None,
) -> FingerprintResult:
    """Compute fingerprint for a dbt source based on schema, identifier and columns.

    Sources don't have compiled SQL, so we fingerprint based on:
    - Logical schema name (e.g., 'stripe', 'raw')
    - Table identifier (table name)
    - Column definitions (name and data type)

    The 'database' component is excluded to make the fingerprint agnostic to
    database-level clones (common in benchmarking/CI environments).

    Args:
        database: Database name (excluded from fingerprint for agnosticism)
        schema: Schema name (included to disambiguate table names)
        identifier: Table/identifier name
        columns: Dict mapping column name -> data type (can be None for type)

    Returns:
        FingerprintResult with hash and SOURCE type
    """
    # Build deterministic content string.
    # We include schema but exclude database to support agnostic database clones.
    # Force lowercase for logical stability.
    parts = [
        (schema or "").lower(),
        identifier.lower(),
    ]

    # Sort columns for deterministic ordering
    if columns:
        sorted_cols = sorted((name.lower(), (dtype or "").lower()) for name, dtype in columns.items())
        col_str = "|".join(f"{name}:{dtype}" for name, dtype in sorted_cols)
        parts.append(col_str)

    content = "|".join(parts)
    hash_value = hashlib.sha256(content.encode("utf-8")).hexdigest()

    return FingerprintResult(
        hash=hash_value,
        type=FingerprintType.SOURCE,
        dialect=None,
    )




