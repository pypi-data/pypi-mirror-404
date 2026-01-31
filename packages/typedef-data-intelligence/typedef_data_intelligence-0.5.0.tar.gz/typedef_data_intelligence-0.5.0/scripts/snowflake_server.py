#!/usr/bin/env python3
"""Standalone Snowflake MCP Server for HTTP/SSE transport.

**NOTE**: This is a CUSTOM MCP server implementation using our SnowflakeBackend.
For production use, we recommend using the OFFICIAL Snowflake Labs MCP server:
https://github.com/Snowflake-Labs/mcp

See SNOWFLAKE_MCP_SETUP.md for instructions on using the official server with Docker.

This custom server is useful for:
- Testing custom backend features
- Development without Docker
- Custom MCP tool implementations

This script runs the Snowflake MCP server in HTTP/SSE mode for use in Docker
or as a standalone service. Multiple clients can connect to the same server.

Usage:
    # Run with environment variables
    export SNOWFLAKE_ACCOUNT=myaccount
    export SNOWFLAKE_USER=myuser
    export SNOWFLAKE_DATABASE=mydb
    export SNOWFLAKE_SCHEMA=myschema
    export SNOWFLAKE_PRIVATE_KEY_PATH=/path/to/key.pem
    export SNOWFLAKE_ROLE=myrole
    export SNOWFLAKE_WAREHOUSE=mywarehouse

    python snowflake_server.py

    # Or with command-line arguments
    python snowflake_server.py --port 8001 --host 0.0.0.0

Environment Variables:
    MCP_PORT: Port to listen on (default: 8001)
    MCP_HOST: Host to bind to (default: 0.0.0.0)
    SNOWFLAKE_ACCOUNT: Snowflake account identifier
    SNOWFLAKE_USER: Snowflake username
    SNOWFLAKE_DATABASE: Default database
    SNOWFLAKE_SCHEMA: Default schema
    SNOWFLAKE_PRIVATE_KEY_PATH: Path to private key file
    SNOWFLAKE_ROLE: Snowflake role
    SNOWFLAKE_WAREHOUSE: Snowflake warehouse
"""
import argparse
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def main():
    """Run Snowflake MCP server in HTTP/SSE mode."""
    parser = argparse.ArgumentParser(description="Snowflake MCP Server")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("MCP_PORT", "9000")),
        help="Port to listen on (default: 9000)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("MCP_HOST", "0.0.0.0"), # nosec B104: intentional binding
        help="Host to bind to (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    logger.info("Starting Snowflake MCP Server...")
    logger.info(f"Server will listen on {args.host}:{args.port}")

    # Validate required environment variables
    required_env_vars = [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_SCHEMA",
        "SNOWFLAKE_PRIVATE_KEY_PATH",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
    ]

    missing = [var for var in required_env_vars if not os.getenv(var)]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        sys.exit(1)

    # Import here after validation
    from lineage.backends.data_query.snowflake_backend import SnowflakeConfig, SnowflakeBackend
    from lineage.backends.data_query.mcp import create_data_query_server

    # Create Snowflake configuration
    config = SnowflakeConfig(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        database_name=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        private_key_path=Path(os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    )

    logger.info(f"Snowflake configuration:")
    logger.info(f"  Account: {config.account}")
    logger.info(f"  User: {config.user}")
    logger.info(f"  Database: {config.database_name}")
    logger.info(f"  Schema: {config.schema_name}")
    logger.info(f"  Role: {config.role}")
    logger.info(f"  Warehouse: {config.warehouse}")

    # Initialize Snowflake backend
    logger.info("Initializing Snowflake backend...")
    backend = SnowflakeBackend(config)

    # Create FastMCP server
    logger.info("Creating MCP server...")
    mcp = create_data_query_server(backend, name="snowflake-mcp")

    # Get transport from environment or use default
    transport = os.getenv("MCP_TRANSPORT", "http")

    # Run server using FastMCP's built-in HTTP transport
    logger.info(f"Starting server with {transport} transport on {args.host}:{args.port}")
    logger.info(f"Server URL: http://{args.host}:{args.port}")

    # FastMCP provides its own uvicorn runner
    mcp.run(transport=transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
