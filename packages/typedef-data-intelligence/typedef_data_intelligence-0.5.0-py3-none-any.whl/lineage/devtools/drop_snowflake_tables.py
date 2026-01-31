#!/usr/bin/env python3
"""Drop Snowflake tables and views in parallel.

This module provides functions to drop all tables and views in a Snowflake database,
with support for schema preservation and parallel execution.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Optional

import snowflake.connector
from snowflake.connector import SnowflakeConnection

# Project-specific schemas to preserve (same as old script)
MATTERMOST_SEED_SCHEMAS = frozenset({"ORGM_RAW", "MATTERMOST_JIRA", "RUDDERSTACK_SUPPORT"})
ALWAYS_SKIP_SCHEMAS = frozenset({"INFORMATION_SCHEMA"})


@dataclass
class DropResult:
    """Result of a drop operation."""

    schema: str
    tables_dropped: int
    views_dropped: int
    semantic_views_dropped: int
    errors: list[str]


@dataclass
class DatabaseDropResult:
    """Result of dropping objects in a database."""

    database: str
    schemas_processed: int
    schemas_skipped: int
    total_tables_dropped: int
    total_views_dropped: int
    total_semantic_views_dropped: int
    errors: list[str]


def get_connection(
    account: str,
    user: str,
    warehouse: str,
    role: str,
    database: str,
    private_key_path: str,
) -> SnowflakeConnection:
    """Create a Snowflake connection."""
    return snowflake.connector.connect(
        user=user,
        account=account,
        private_key_file=private_key_path,
        warehouse=warehouse,
        database=database,
        role=role,
    )


def get_schemas(conn: SnowflakeConnection) -> list[str]:
    """Get all schemas in the connected database."""
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW SCHEMAS")
        return [row[1] for row in cursor.fetchall()]
    finally:
        cursor.close()


def get_objects_in_schema(
    conn: SnowflakeConnection, schema: str
) -> tuple[list[str], list[str], list[str]]:
    """Get tables, views, and semantic views in a schema.

    Returns:
        Tuple of (table_names, view_names, semantic_view_names)
    """
    cursor = conn.cursor()
    tables = []
    views = []
    semantic_views = []

    try:
        # Get tables and views
        cursor.execute(
            """
            SELECT table_name, table_type
            FROM information_schema.tables
            WHERE table_schema = %s
            AND table_type IN ('BASE TABLE', 'VIEW')
            """,
            (schema,),
        )
        for name, obj_type in cursor.fetchall():
            if obj_type == "BASE TABLE":
                tables.append(name)
            else:
                views.append(name)

        # Get semantic views (may not exist in all editions)
        try:
            cursor.execute(f"SHOW SEMANTIC VIEWS IN SCHEMA {schema}")
            semantic_views = [row[1] for row in cursor.fetchall()]
        except Exception:
            pass  # Semantic views not supported

    finally:
        cursor.close()

    return tables, views, semantic_views


def drop_objects_in_schema(
    conn: SnowflakeConnection,
    schema: str,
    tables: list[str],
    views: list[str],
    semantic_views: list[str],
    dry_run: bool = False,
) -> DropResult:
    """Drop all objects in a schema.

    Args:
        conn: Snowflake connection
        schema: Schema name
        tables: List of table names to drop
        views: List of view names to drop
        semantic_views: List of semantic view names to drop
        dry_run: If True, only log what would be dropped

    Returns:
        DropResult with counts and any errors
    """
    errors = []
    tables_dropped = 0
    views_dropped = 0
    semantic_views_dropped = 0

    cursor = conn.cursor()
    try:
        # Drop tables
        for table in tables:
            sql = f"DROP TABLE IF EXISTS {schema}.{table} CASCADE"
            if dry_run:
                print(f"  [dry-run] {sql}")
            else:
                print(f"Executing: {sql}")
                try:
                    cursor.execute(sql)
                    tables_dropped += 1
                except Exception as e:
                    errors.append(f"Failed to drop table {schema}.{table}: {e}")

        # Drop views
        for view in views:
            sql = f"DROP VIEW IF EXISTS {schema}.{view} CASCADE"
            if dry_run:
                print(f"  [dry-run] {sql}")
            else:
                print(f"Executing: {sql}")
                try:
                    cursor.execute(sql)
                    views_dropped += 1
                except Exception as e:
                    errors.append(f"Failed to drop view {schema}.{view}: {e}")

        # Drop semantic views
        for sv in semantic_views:
            sql = f"DROP SEMANTIC VIEW IF EXISTS {schema}.{sv}"
            if dry_run:
                print(f"  [dry-run] {sql}")
            else:
                print(f"  Dropping semantic view: {sql}")
                try:
                    cursor.execute(sql)
                    semantic_views_dropped += 1
                except Exception as e:
                    errors.append(f"Failed to drop semantic view {schema}.{sv}: {e}")

    finally:
        cursor.close()

    return DropResult(
        schema=schema,
        tables_dropped=tables_dropped,
        views_dropped=views_dropped,
        semantic_views_dropped=semantic_views_dropped,
        errors=errors,
    )


def _process_schema(creds: dict, schema: str, dry_run: bool) -> DropResult:
    """Process a single schema - get objects and drop them.

    Each thread gets its own connection to avoid connection sharing issues.

    Args:
        creds: Snowflake credentials
        schema: Schema name to process
        dry_run: If True, only log what would be dropped

    Returns:
        DropResult for this schema
    """
    conn = get_connection(**creds)
    try:
        tables, views, semantic_views = get_objects_in_schema(conn, schema)
        print(f"  {schema}: {len(tables)} tables, {len(views)} views, {len(semantic_views)} semantic views")

        if not tables and not views and not semantic_views:
            return DropResult(
                schema=schema,
                tables_dropped=0,
                views_dropped=0,
                semantic_views_dropped=0,
                errors=[],
            )

        return drop_objects_in_schema(conn, schema, tables, views, semantic_views, dry_run)
    finally:
        conn.close()


def drop_database_objects(
    creds: dict,
    ignore_schemas: Optional[set[str]] = None,
    max_workers: int = 4,
    dry_run: bool = False,
) -> DatabaseDropResult:
    """Drop all objects in a database in parallel.

    Args:
        creds: Dictionary with Snowflake credentials:
            - account, user, warehouse, role, database, private_key_path
        ignore_schemas: Set of schema names to skip (case-insensitive)
        max_workers: Number of parallel workers for dropping objects
        dry_run: If True, only show what would be dropped

    Returns:
        DatabaseDropResult with summary statistics
    """
    database = creds["database"]
    print(f"account: {creds['account']}")
    print(f"user: {creds['user']}")
    print(f"warehouse: {creds['warehouse']}")
    print(f"database: {database}")
    print(f"role: {creds['role']}")
    print(f"key_path: {creds['private_key_path']}")
    print(f"Connecting to Snowflake ({creds['account']})")

    # Normalize ignore list to uppercase
    skip_schemas = ALWAYS_SKIP_SCHEMAS.copy()
    if ignore_schemas:
        skip_schemas = skip_schemas | {s.upper() for s in ignore_schemas}

    # Get schemas list with a single connection
    conn = get_connection(**creds)
    try:
        schemas = get_schemas(conn)
        print(f"Schemas: {schemas}")
    finally:
        conn.close()

    # Filter schemas
    schemas_to_process = []
    schemas_skipped = 0
    for schema in schemas:
        if schema.upper() in skip_schemas:
            print(f"Ignoring schema: {schema}")
            schemas_skipped += 1
        else:
            schemas_to_process.append(schema)

    if not schemas_to_process:
        print("No schemas to process")
        return DatabaseDropResult(
            database=database,
            schemas_processed=0,
            schemas_skipped=schemas_skipped,
            total_tables_dropped=0,
            total_views_dropped=0,
            total_semantic_views_dropped=0,
            errors=[],
        )

    print(f"\nProcessing {len(schemas_to_process)} schemas with {max_workers} workers: {', '.join(schemas_to_process)}")

    # Process schemas in parallel - each thread gets its own connection
    all_results: list[DropResult] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_schema, creds, schema, dry_run): schema
            for schema in schemas_to_process
        }
        for future in as_completed(futures):
            schema = futures[future]
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                print(f"Error processing schema {schema}: {e}")
                all_results.append(DropResult(
                    schema=schema,
                    tables_dropped=0,
                    views_dropped=0,
                    semantic_views_dropped=0,
                    errors=[str(e)],
                ))

    # Aggregate results
    total_tables = sum(r.tables_dropped for r in all_results)
    total_views = sum(r.views_dropped for r in all_results)
    total_semantic = sum(r.semantic_views_dropped for r in all_results)
    all_errors = [e for r in all_results for e in r.errors]

    print(f"\n--- Summary ---")
    print(f"Schemas processed: {len(schemas_to_process)}")
    print(f"Schemas skipped: {schemas_skipped}")
    print(f"Tables dropped: {total_tables}")
    print(f"Views dropped: {total_views}")
    print(f"Total tables+views: {total_tables + total_views}")
    print(f"Semantic views dropped: {total_semantic}")
    if all_errors:
        print(f"Errors: {len(all_errors)}")
        for err in all_errors[:5]:
            print(f"  - {err}")
        if len(all_errors) > 5:
            print(f"  ... and {len(all_errors) - 5} more")

    return DatabaseDropResult(
        database=database,
        schemas_processed=len(schemas_to_process),
        schemas_skipped=schemas_skipped,
        total_tables_dropped=total_tables,
        total_views_dropped=total_views,
        total_semantic_views_dropped=total_semantic,
        errors=all_errors,
    )


def get_project_ignore_schemas(project_type: Optional[str] = None) -> set[str]:
    """Get schemas to ignore based on project type.

    Args:
        project_type: "mattermost", "medallion", or None for no special handling

    Returns:
        Set of schema names to preserve
    """
    if project_type and project_type.lower() == "mattermost":
        return set(MATTERMOST_SEED_SCHEMAS)
    # Medallion and other projects: don't preserve any special schemas
    return set()


def drop_objects_from_config(
    creds: dict,
    project_type: Optional[str] = None,
    max_workers: int = 4,
    dry_run: bool = False,
) -> DatabaseDropResult:
    """Drop objects using credentials dict and project type.

    Args:
        creds: Snowflake credentials dict
        project_type: "mattermost" or "medallion" to determine schema preservation
        max_workers: Number of parallel workers
        dry_run: Preview mode

    Returns:
        DatabaseDropResult
    """
    ignore_schemas = get_project_ignore_schemas(project_type)
    if ignore_schemas:
        print(f"Preserving schemas for {project_type}: {ignore_schemas}")

    return drop_database_objects(
        creds=creds,
        ignore_schemas=ignore_schemas,
        max_workers=max_workers,
        dry_run=dry_run,
    )
