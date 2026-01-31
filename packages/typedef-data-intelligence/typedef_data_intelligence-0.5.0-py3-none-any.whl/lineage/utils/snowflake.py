"""Snowflake utility functions for connection validation and metadata."""
from typing import Optional

import snowflake.connector
from snowflake.connector.errors import Error


def list_snowflake_databases(
    account: str,
    user: str,
    role: str,
    warehouse: str,
    private_key_path: str,
) -> list[str]:
    """Connect to Snowflake and return list of accessible database names.
    
    Args:
        account: Snowflake account identifier
        user: Snowflake username
        role: Snowflake role
        warehouse: Snowflake warehouse
        private_key_path: Path to RSA private key file
        
    Returns:
        List of database names
        
    Raises:
        Exception: If connection fails or query fails
    """
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # Load private key
    with open(private_key_path, "rb") as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=None,
            backend=default_backend(),
        )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        private_key=pkb,
        role=role,
        warehouse=warehouse,
    )

    try:
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        # Format: created_on, name, is_default, is_current, origin, owner, comment, options, retention_time
        # We just want the name (column 1)
        databases = [row[1] for row in cursor.fetchall()]
        return sorted(databases)
    finally:
        conn.close()


def list_snowflake_schemas(
    account: str,
    user: str,
    role: str,
    warehouse: str,
    private_key_path: str,
    database: str,
) -> list[str]:
    """Connect to Snowflake and return list of schemas in a database.

    Args:
        account: Snowflake account identifier
        user: Snowflake username
        role: Snowflake role
        warehouse: Snowflake warehouse
        private_key_path: Path to RSA private key file
        database: Database to list schemas from

    Returns:
        List of schema names

    Raises:
        Exception: If connection fails or query fails
    """
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    # Load private key
    with open(private_key_path, "rb") as key:
        p_key = serialization.load_pem_private_key(
            key.read(),
            password=None,
            backend=default_backend(),
        )

    pkb = p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    conn = snowflake.connector.connect(
        account=account,
        user=user,
        private_key=pkb,
        role=role,
        warehouse=warehouse,
        database=database,
    )

    try:
        cursor = conn.cursor()
        cursor.execute(f"SHOW SCHEMAS IN DATABASE {database}")
        # Format: created_on, name, is_default, is_current, ...
        # We just want the name (column 1)
        schemas = [row[1] for row in cursor.fetchall()]
        return sorted(schemas)
    finally:
        conn.close()


def validate_snowflake_read_access(
    account: str,
    user: str,
    role: str,
    warehouse: str,
    private_key_path: str,
    database: str,
    schema: str = "PUBLIC",
) -> tuple[bool, str, Optional[str]]:
    """Validate read access by listing tables and reading from one.
    
    Args:
        account: Snowflake account
        user: Snowflake user
        role: Snowflake role
        warehouse: Snowflake warehouse
        private_key_path: Path to private key
        database: Database to check
        schema: Schema to check (default: PUBLIC)
        
    Returns:
        tuple: (success, message, sample_table_name)
    """
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    try:
        # Load private key
        with open(private_key_path, "rb") as key:
            p_key = serialization.load_pem_private_key(
                key.read(),
                password=None,
                backend=default_backend(),
            )

        pkb = p_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )

        conn = snowflake.connector.connect(
            account=account,
            user=user,
            private_key=pkb,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
        )

        try:
            cursor = conn.cursor()
            
            # 1. List tables
            cursor.execute(f"SHOW TABLES IN SCHEMA {database}.{schema}")
            tables = cursor.fetchall()
            
            if not tables:
                return True, f"Connected to {database}.{schema} (no tables found)", None
            
            # 2. Pick first table
            # Format: created_on, name, database_name, schema_name, kind, ...
            first_table = tables[0][1]
            
            # 3. Try to read from it (inputs are wizard config + SHOW TABLES result)
            cursor.execute(f"SELECT * FROM {database}.{schema}.{first_table} LIMIT 1")  # nosec B608
            cursor.fetchall()
            
            return True, f"Successfully read from {database}.{schema}.{first_table}", first_table
            
        except Error as e:
            return False, f"Snowflake error: {str(e)}", None
        except Exception as e:
            return False, f"Unexpected error: {str(e)}", None
        finally:
            conn.close()
            
    except Exception as e:
        return False, f"Connection failed: {str(e)}", None




