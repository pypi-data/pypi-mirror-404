#!/usr/bin/env python3
"""Execute SQL file against Snowflake using private key authentication."""

import os
import sys
from pathlib import Path
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

# Load environment variables from .env file
from lineage.utils.env import load_env_file

load_env_file()


def execute_sql_file(sql_file: str):
    """Execute SQL file against Snowflake."""
    # Get connection details from environment
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    user = os.getenv("SNOWFLAKE_USER")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE")
    role = os.getenv("SNOWFLAKE_ROLE")
    database = os.getenv("SNOWFLAKE_DATABASE")
    schema = os.getenv("SNOWFLAKE_SCHEMA")
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    key_passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE", "")

    # Load private key
    print(f"🔑 Loading private key from {key_path}")

    with open(key_path, "rb") as key_file:
        private_key_bytes = key_file.read()

    # Parse the private key
    if key_passphrase:
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=key_passphrase.encode(),
            backend=default_backend()
        )
    else:
        private_key = serialization.load_pem_private_key(
            private_key_bytes,
            password=None,
            backend=default_backend()
        )

    # Serialize to DER format for Snowflake
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Read SQL file
    sql_path = Path(sql_file)
    if not sql_path.exists():
        print(f"❌ SQL file not found: {sql_file}")
        sys.exit(1)

    print(f"📄 Reading SQL from {sql_file}")
    sql_content = sql_path.read_text()

    # Connect to Snowflake
    print(f"🔌 Connecting to Snowflake ({account})")
    conn = snowflake.connector.connect(
        user=user,
        account=account,
        private_key=private_key_der,
        warehouse=warehouse,
        role=role,
        database=database,
        schema=schema,
    )

    try:
        cursor = conn.cursor()
        cursor.execute(f"USE ROLE {role}")
        cursor.execute(f"USE DATABASE {database}")
        cursor.execute(f"USE WAREHOUSE {warehouse}")
        cursor.execute(f"USE SCHEMA {schema}")

        # Split into individual statements (simple split on semicolon)
        statements = [
            s.strip()
            for s in sql_content.split(";")
            if s.strip() and not s.strip().startswith("--")
        ]

        print(f"⚙️  Executing {len(statements)} SQL statements...")

        for i, statement in enumerate(statements, 1):
            # Skip comments
            if statement.startswith("--"):
                continue

            print(f"  [{i}/{len(statements)}] Executing: {statement}")
            cursor.execute(statement)

            # Fetch results if available
            if cursor.rowcount > 0:
                results = cursor.fetchall()
                for row in results:
                    print(f"    {row}")

        print("✅ All statements executed successfully")

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python run_snowflake_sql.py <sql_file>")
        sys.exit(1)

    execute_sql_file(sys.argv[1])
