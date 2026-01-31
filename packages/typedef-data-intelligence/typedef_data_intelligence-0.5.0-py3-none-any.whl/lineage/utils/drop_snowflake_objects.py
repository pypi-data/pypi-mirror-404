#!/usr/bin/env python3
"""Drop all tables and semantic views in specified schemas."""

import os
from typing import Optional

import snowflake.connector

# Load environment variables from .env file
from lineage.utils.env import load_env_file

mattermost_analytics_db_seed_schemas = ["ORGM_RAW", "MATTERMOST_JIRA", "RUDDERSTACK_SUPPORT"]

load_env_file()

def _get_schemas(conn: snowflake.connector.SnowflakeConnection) -> list[str]:
    """Get all schemas in a database."""
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW SCHEMAS")
        return [row[1] for row in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()
        # Don't close connection here - caller needs it

def drop_objects_in_database(database: str, account: str, user: str, warehouse: str, role: str, key_path: str, schema_ignore_list: Optional[list[str]] = None) -> list[str]:
    """Get all schemas in a database."""
    conn = snowflake.connector.connect(
        user=user,
        account=account,
        private_key_file=key_path,
        warehouse=warehouse,
        database=database,
        role=role,
    )
    # Connect to Snowflake
    print(f"account: {account}")
    print(f"user: {user}")
    print(f"warehouse: {warehouse}")
    print(f"database: {database}")
    print(f"role: {role}")
    print(f"key_path: {key_path}")
    print(f"🔌 Connecting to Snowflake ({account})")
    cursor = None
    skipped_schemas_count = 0
    dropped_tables_count = 0
    dropped_semantic_views_count = 0
    try:
        schemas = _get_schemas(conn)
        print(f"Schemas: {schemas}")

        for schema in schemas:
            if schema == "INFORMATION_SCHEMA":
                continue
            if schema_ignore_list and schema in schema_ignore_list:
                print(f"Ignoring schema: {schema}")
                skipped_schemas_count += 1
                continue
            cursor = conn.cursor()
            # Fetch base tables and semantic views
            cursor.execute(
                """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type IN ('BASE TABLE', 'VIEW');
            """,
                (schema,),
            )

            objects = cursor.fetchall()
            try:
                # Drop each object
                for obj_name, obj_type in objects:
                    if obj_type == "BASE TABLE":
                        drop_sql = f"DROP TABLE IF EXISTS {schema}.{obj_name} CASCADE"
                    else:
                        drop_sql = f"DROP VIEW IF EXISTS {schema}.{obj_name} CASCADE"
                    print(f"Executing: {drop_sql}")
                    cursor.execute(drop_sql)
                    dropped_tables_count += 1

                # Try to drop semantic views (may not exist in all Snowflake editions)
                cursor.execute(f"""
                    SHOW SEMANTIC VIEWS IN SCHEMA {schema};
                """)
                semantic_views = cursor.fetchall()

                # Drop each semantic view
                for row in semantic_views:
                    view_name = row[1]  # Second column is typically the name
                    drop_sql = f"DROP SEMANTIC VIEW IF EXISTS {schema}.{view_name}"
                    print(f"  Dropping semantic view: {drop_sql}")
                    cursor.execute(drop_sql)
                    dropped_semantic_views_count += 1
            except Exception as e:
                print(f"  ⚠️  Could not drop semantic views in {schema}: {e}")

            # Close cursor after each schema
            cursor.close()
            cursor = None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print(f"Skipped {skipped_schemas_count} schemas")
        print(f"Dropped {dropped_tables_count} tables")
        print(f"Dropped {dropped_semantic_views_count} semantic views")

def drop_objects(ignore_staging: bool):
    """Drop all tables and semantic views in the schemas.

    Args:
        ignore_staging: Ignore staging tables (i.e.: tables added by synthetic data generator).
    """
    # Get connection details from environment
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    role = os.getenv("SNOWFLAKE_ROLE")
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")

    if ignore_staging:
        schema_ignore_list = mattermost_analytics_db_seed_schemas
    else:
        schema_ignore_list = None
    database = os.getenv("SNOWFLAKE_DATABASE")
    if database:
        drop_objects_in_database(database, account, user, warehouse, role, key_path, schema_ignore_list=schema_ignore_list)
    database = os.getenv("MATTERMOST_ANALYTICS_DB")
    if database:
        drop_objects_in_database(database, account, user, warehouse, role, key_path, schema_ignore_list=schema_ignore_list)
    database = os.getenv("MATTERMOST_RAW_DB")
    if database and not ignore_staging:
        drop_objects_in_database(database, account, user, warehouse, role, key_path)



if __name__ == "__main__":
    drop_objects()
