"""Template rendering utilities for typedef configuration generation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def yaml_escape(value: str | None) -> str:
    """Escape a string value for safe use in YAML double-quoted strings.
    
    This handles backslashes, double quotes, and other special characters
    that could break YAML parsing when used inside double-quoted strings.
    
    Args:
        value: String value to escape (None will be converted to empty string)
        
    Returns:
        Escaped string safe for YAML double-quoted scalars
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    
    # Use JSON encoding which properly escapes for YAML (JSON strings are valid YAML strings)
    # The tojson filter would add quotes, so we use json.dumps and strip them
    escaped = json.dumps(value)
    # json.dumps adds surrounding quotes, which we'll add in the template
    # So we strip the quotes to get just the escaped content
    return escaped[1:-1]


def yaml_quote_key(key: str | None) -> str:
    """Quote a YAML key if it contains special characters.
    
    Args:
        key: YAML key name (None will be converted to empty string)
        
    Returns:
        Quoted key if needed, or unquoted if safe
    """
    if key is None:
        return '""'
    if not isinstance(key, str):
        key = str(key)
    
    # Characters that require quoting in YAML keys
    needs_quote = any(c in key for c in [':', '"', "'", '\\', '{', '}', '[', ']', ',', '&', '*', '#', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', ' '])
    
    if needs_quote:
        # Escape any double quotes and backslashes, then wrap in quotes
        escaped = yaml_escape(key)
        return f'"{escaped}"'
    return key


def get_template_env() -> Environment:
    """Get Jinja2 environment configured for typedef templates."""
    template_dir = Path(__file__).parent
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(default_for_string=False, default=False),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Register custom filters for YAML-safe escaping
    env.filters['yaml_escape'] = yaml_escape
    env.filters['yaml_quote_key'] = yaml_quote_key
    return env


def render_typedef_config(
    project_name: str,
    dbt_path: str,
    graph_db_path: str,
    typedef_home: str,
    profiles_dir: str,
    snowflake_account: str,
    snowflake_user: str,
    snowflake_warehouse: str,
    snowflake_role: str,
    snowflake_database: str,
    snowflake_schema: str = "PUBLIC",
    snowflake_private_key_path: str = "",
    profile_name: str = "dev",
    allowed_databases: list[str] | None = None,
    allowed_schemas: list[str] | None = None,
    default_database: str | None = None,
    project_env_vars: dict[str, str] | None = None,
    git_enabled: bool = True,
    git_working_directory: str | None = None,
    ticket_enabled: bool = False,
    ticket_backend: str = "filesystem",
    linear_team_id: str | None = None,
    linear_mcp_server_url: str = "https://mcp.linear.app/mcp",
) -> str:
    """Render the unified typedef config template.

    Args:
        project_name: Name of the dbt project
        dbt_path: Path to the dbt project directory
        graph_db_path: Path to the FalkorDB Lite database file
        typedef_home: Path to ~/.typedef directory
        profiles_dir: Path to the directory with the dbt profiles.yml file
        snowflake_account: Snowflake account identifier
        snowflake_user: Snowflake username
        snowflake_warehouse: Snowflake warehouse name
        snowflake_role: Snowflake role
        snowflake_database: Default Snowflake database
        snowflake_schema: Default Snowflake schema
        snowflake_private_key_path: Path to Snowflake private key
        profile_name: dbt profile name
        allowed_databases: List of allowed databases for this project
        allowed_schemas: List of allowed schemas
        default_database: Default database for queries
        project_env_vars: Environment variables specific to this project
        git_enabled: Whether git operations are enabled for this project (used by CLI data engineer agent)
        git_working_directory: Per-project working directory for git operations (defaults to dbt_path)
        ticket_enabled: Whether ticketing is enabled
        ticket_backend: Ticketing backend type ("filesystem" or "linear")
        linear_team_id: Linear team ID (required when ticket_backend is "linear")
        linear_mcp_server_url: Linear MCP server URL (default: https://mcp.linear.app/mcp)

    Returns:
        Rendered YAML configuration string
    """
    env = get_template_env()
    template = env.get_template("typedef_config.yaml.j2")

    context: dict[str, Any] = {
        "project_name": project_name,
        "dbt_path": dbt_path,
        "graph_db_path": graph_db_path,
        "typedef_home": typedef_home,
        "profiles_dir": profiles_dir,
        "snowflake_account": snowflake_account,
        "snowflake_user": snowflake_user,
        "snowflake_warehouse": snowflake_warehouse,
        "snowflake_role": snowflake_role,
        "snowflake_database": snowflake_database,
        "snowflake_schema": snowflake_schema,
        "snowflake_private_key_path": snowflake_private_key_path,
        "profile_name": profile_name,
        "allowed_databases": allowed_databases,
        "allowed_schemas": allowed_schemas,
        "default_database": default_database,
        "project_env_vars": project_env_vars,
        "git_enabled": str(git_enabled).lower(),
        "git_working_directory": git_working_directory or dbt_path,
        "ticket_enabled": str(ticket_enabled).lower(),
        "ticket_backend": ticket_backend,
        "linear_team_id": linear_team_id,
        "linear_mcp_server_url": linear_mcp_server_url,
    }

    return template.render(**context)
