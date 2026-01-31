"""Runtime configuration for lineage and data backends.

This module provides runtime configuration for:
- Lineage backend configuration (graph database)
- Data backend configuration (data warehouse)
- Agent runtime settings (model selection)
- Memory backend settings
- Ticket backend settings
- Git workspace settings

Note: Data population settings (semantic analysis, profiling, clustering) are now
in lineage.ingest.config and loaded separately during ingest operations.

Configuration supports environment variable interpolation using ${VAR_NAME} syntax.

Example config.yml:
    lineage:
      backend: neo4j
      uri: bolt://localhost:7687
      username: neo4j
      password: ${NEO4J_PASSWORD}  # References environment variable
      database: lineage

    data:
      backend: duckdb
      db_path: ./data.duckdb
      allowed_schemas:
        - marts

    agent:
      analyst:
        model: anthropic:claude-haiku-4-5
      data_engineer:
        model: anthropic:claude-sonnet-4-5-20250929
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import List, Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from lineage.backends.types import DataBackendType, LineageStorageType

# ============================================================================
# Agent Configuration (Runtime)
# ============================================================================

class AnalystConfig(BaseModel):
    """Configuration for analyst agent."""
    model: str = Field(
        default="anthropic:claude-haiku-4-5",
        description="LLM model for analyst agent"
    )

class DataEngineerConfig(BaseModel):
    """Configuration for data engineer agent."""
    model: str = Field(
        default="anthropic:claude-sonnet-4-5-20250929",
        description="LLM model for data engineer agent"
    )

class InvestigatorConfig(BaseModel):
    """Configuration for investigator agent (reactive troubleshooting)."""
    model: str = Field(
        default="anthropic:claude-sonnet-4-5-20250929",
        description="LLM model for investigator agent"
    )

class InsightsConfig(BaseModel):
    """Configuration for insights agent (architecture explanation)."""
    model: str = Field(
        default="anthropic:claude-sonnet-4-5-20250929",
        description="LLM model for insights agent"
    )

class QualityConfig(BaseModel):
    """Configuration for quality agent (operational monitoring)."""
    model: str = Field(
        default="anthropic:claude-sonnet-4-5-20250929",
        description="LLM model for quality agent"
    )

class AgentConfig(BaseModel):
    """Configuration for agent runtime (webui/interactive queries).

    This controls the LLM model and settings for interactive agent queries.
    Uses an accurate/smart model for high-quality responses.
    """
    analyst: AnalystConfig = Field(default_factory=AnalystConfig)
    data_engineer: DataEngineerConfig = Field(default_factory=DataEngineerConfig)
    investigator: InvestigatorConfig = Field(default_factory=InvestigatorConfig)
    insights: InsightsConfig = Field(default_factory=InsightsConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)


# ============================================================================
# Lineage Backend Configurations
# ============================================================================


class BaseLineageConfig(BaseModel):
    """Base configuration for lineage backends."""

    backend: str  # Will be validated as LineageStorageType

    @field_validator('backend')
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate backend type."""
        try:
            LineageStorageType.from_string(v)
        except ValueError as e:
            raise ValueError(f"Invalid lineage backend type: {v}. {e}") from e
        return v


class FalkorDBLineageConfig(BaseLineageConfig):
    """FalkorDB lineage backend configuration."""

    backend: Literal["falkordb"] = "falkordb"
    host: str = Field(default="localhost", description="FalkorDB/Redis host")
    port: int = Field(default=6379, ge=1, le=65535, description="FalkorDB/Redis port")
    username: str = Field(default="td-data-intelligence", description="FalkorDB username (use ${ENV_VAR} for security)")
    password: str = Field(default="", description="FalkorDB password (use ${ENV_VAR} for security)")
    graph_name: str = Field(default="lineage", description="FalkorDB graph name")


class FalkorDBLiteLineageConfig(BaseLineageConfig):
    """FalkorDBLite lineage backend configuration (embedded, no Docker)."""

    backend: Literal["falkordblite"] = "falkordblite"
    db_path: str = Field(
        default=".lineage_workspace/falkordb.db",
        description="Path to FalkorDBLite database file"
    )
    graph_name: str = Field(default="lineage", description="FalkorDB graph name")


# Union of all lineage config types
LineageConfig = Union[
    FalkorDBLineageConfig,
    FalkorDBLiteLineageConfig,
]


# ============================================================================
# Data Backend Configurations
# ============================================================================


class BaseDataConfig(BaseModel):
    """Base configuration for data backends."""

    backend: str  # Will be validated as DataBackendType

    @field_validator('backend')
    @classmethod
    def validate_backend(cls, v: str) -> str:
        """Validate backend type."""
        try:
            DataBackendType(v.lower())
        except ValueError as e:
            valid = [b.value for b in DataBackendType]
            raise ValueError(f"Invalid data backend type: {v}. Must be one of: {valid}") from e
        return v.lower()


class DuckDBDataConfig(BaseDataConfig):
    """DuckDB data backend configuration."""

    backend: Literal["duckdb"] = "duckdb"
    db_path: Path = Field(..., description="Path to DuckDB database file")
    allowed_schemas: Optional[List[str]] = Field(
        default=None,
        description="Allowed schema names (None = all schemas allowed)"
    )
    allowed_table_patterns: Optional[List[str]] = Field(
        default=None,
        description="Allowed table name patterns (e.g., ['fct_*', 'dim_*'])"
    )


class SnowflakeDataConfig(BaseDataConfig):
    """Snowflake data backend configuration."""

    backend: Literal["snowflake"] = "snowflake"
    account: str = Field(..., description="Snowflake account identifier")
    user: str = Field(..., description="Snowflake user name")
    warehouse: str = Field(..., description="Snowflake warehouse to use")
    role: str = Field(..., description="Snowflake role to use")
    database: str = Field(..., description="Default Snowflake database")
    schema_name: str = Field(default="PUBLIC", description="Default Snowflake schema")
    private_key_path: Path = Field(
        ...,
        description="Path to private key file for authentication"
    )
    private_key_passphrase: Optional[str] = Field(
        default=None,
        description="Passphrase for encrypted private key (use ${ENV_VAR} for security)"
    )
    mcp_server_url: Optional[str] = Field(
        default=None,
        description="URL of Snowflake MCP server (e.g., http://localhost:8001). If not provided, uses native Snowflake connector instead of MCP."
    )
    allowed_databases: Optional[List[str]] = Field(
        default=None,
        description="Allowed database names (None = all databases allowed)"
    )
    allowed_schemas: Optional[List[str]] = Field(
        default=None,
        description="Allowed schema names (None = all schemas allowed)"
    )
    allowed_table_patterns: Optional[List[str]] = Field(
        default=None,
        description="Allowed table name patterns (e.g., ['fct_*', 'dim_*'])"
    )
    read_only: bool = Field(
        default=True,
        description="Enforce read-only mode (SELECT queries only). Recommended for analyst agents."
    )


# Union of all data config types
DataConfig = Union[DuckDBDataConfig, SnowflakeDataConfig]


# ============================================================================
# Memory Backend Configuration
# ============================================================================


class BaseMemoryConfig(BaseModel):
    """Base configuration for memory backends."""

    backend: str  # Will be validated in subclasses
    enabled: bool = Field(
        default=False,
        description="Enable memory backend for user-specific preferences and context"
    )
    default_org_id: str = Field(
        default="default",
        description="Default organization ID for shared memory across sessions"
    )
    default_user_id: str = Field(
        default="local-user",
        description="Default user ID for personal memory across sessions"
    )


class FalkorDBMemoryConfig(BaseMemoryConfig):
    """FalkorDB memory backend configuration (server-based).

    Uses Graphiti temporal knowledge graphs with FalkorDB for:
    - User-specific preferences and context
    - Organization-wide data patterns and insights
    """

    backend: Literal["falkordb"] = "falkordb"
    host: str = Field(default="localhost", description="FalkorDB host")
    port: int = Field(default=6379, ge=1, le=65535, description="FalkorDB port")
    username: str = Field(default="", description="FalkorDB username (optional)")
    password: str = Field(default="", description="FalkorDB password (use ${ENV_VAR} for security)")


class FalkorDBLiteMemoryConfig(BaseMemoryConfig):
    """FalkorDBLite memory backend configuration (embedded, no Docker)."""

    backend: Literal["falkordblite"] = "falkordblite"
    db_path: str = Field(
        default=".lineage_workspace/falkordb_memory.db",
        description="Path to FalkorDBLite memory database file"
    )


# Union of all memory config types
MemoryConfig = Union[FalkorDBMemoryConfig, FalkorDBLiteMemoryConfig]


# ============================================================================
# Ticket Backend Configuration
# ============================================================================


class BaseTicketConfig(BaseModel):
    """Base configuration for ticket storage backends."""

    enabled: bool = Field(
        default=False,
        description="Enable ticket storage for inter-agent communication"
    )


class FilesystemTicketConfig(BaseTicketConfig):
    """Configuration for filesystem-based ticket storage."""

    backend: Literal["filesystem"] = "filesystem"
    base_path: Path = Field(
        default=Path("./tickets"),
        description="Base directory for ticket storage"
    )


class LinearTicketConfig(BaseTicketConfig):
    """Configuration for Linear MCP-based ticket storage."""

    backend: Literal["linear"] = "linear"
    mcp_server_url: str = Field(
        ...,
        description="URL of Linear MCP server (e.g., http://localhost:8002)"
    )
    team_id: Optional[str] = Field(
        default=None,
        description="Linear team ID to use for tickets (if not specified, uses default team)"
    )
    analyst_user_token: Optional[str] = Field(
        default=None,
        description="analyst's Linear user token for tickets. Use {ENV_VAR} for security"
    )
    data_engineer_user_token: Optional[str] = Field(
        default=None,
        description="data engineer' Linear user token for tickets. Use {ENV_VAR} for security"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Linear project ID to assign tickets to (optional)"
    )



# Union of all ticket config types
TicketConfig = Union[FilesystemTicketConfig, LinearTicketConfig]

# ============================================================================
# Reports Backend Configuration
# ============================================================================

class BaseReportsConfig(BaseModel):
    """Configuration for reports backend."""

    enabled: bool = Field(
        default=False,
        description="Enable reports storage for agent reports"
    )
    backend: Literal["filesystem"] = Field(
        default="filesystem",
        description="Reports backend type (currently only filesystem supported)"
    )

class FilesystemReportsConfig(BaseReportsConfig):
    """Filesystem reports backend configuration."""

    base_path: Path = Field(
        default=Path(".lineage_workspace/reports"),
        description="Base directory for reports storage (filesystem backend)"
    )

ReportsConfig = Union[FilesystemReportsConfig]

# ============================================================================
# Threads Backend Configuration
# ============================================================================

class BaseThreadsConfig(BaseModel):
    """Configuration for threads backend."""

    enabled: bool = Field(
        default=True,
        description="Enable threads storage for conversation memory"
    )
    backend: Literal["sqlite"] = Field(
        default="sqlite",
        description="Threads backend type (sqlite only)"
    )

class SQLiteThreadsConfig(BaseThreadsConfig):
    """SQLite threads backend configuration."""

    backend: Literal["sqlite"] = "sqlite"
    db_path: Path = Field(
        default=Path(".lineage_workspace/threads.db"),
        description="Path to SQLite database file"
    )

ThreadsConfig = SQLiteThreadsConfig

# ============================================================================
# Git Backend Configuration
# ============================================================================

class GitConfig(BaseModel):
    """Configuration for git backend."""
    enabled: bool = Field(
        default=False,
        description="Enable git operations for the data engineering agent"
    )
    working_directory: Optional[Path] = Field(
        default=None,
        description="Working directory for git operations (required when enabled=True)"
    )
    repo_url: Optional[str] = Field(
        default=None,
        description="URL of git repository (optional, used for clone operations)"
    )

    @model_validator(mode="after")
    def validate_enabled_fields(self) -> "GitConfig":
        if self.enabled and not self.working_directory:
            raise ValueError("git.working_directory is required when git.enabled=True")
        return self


# ============================================================================
# Project Configuration (Per-Project Overrides)
# ============================================================================


class ProjectDataOverrides(BaseModel):
    """Fields that can be overridden per-project.

    These settings override the shared `data:` configuration when syncing
    or querying a specific project. This allows multiple dbt projects to
    share a single Snowflake account but use different databases/warehouses.
    """

    database: Optional[str] = Field(
        default=None,
        description="Override the default database for this project"
    )
    warehouse: Optional[str] = Field(
        default=None,
        description="Override the default warehouse for this project"
    )
    allowed_databases: Optional[List[str]] = Field(
        default=None,
        description="Override allowed databases for this project"
    )
    allowed_schemas: Optional[List[str]] = Field(
        default=None,
        description="Override allowed schemas for this project"
    )


class ProjectConfig(BaseModel):
    """Configuration for a single dbt project.

    Each project can have its own dbt path, graph name, and optionally
    override specific data backend settings.
    """

    name: str = Field(..., description="Human-readable project name")
    dbt_path: Path = Field(..., description="Path to dbt project directory")
    graph_name: str = Field(..., description="Graph name in the lineage database")
    profile_name: Optional[str] = Field(
        default=None,
        description="dbt profile name to use (if different from project name)"
    )
    profiles_dir: Optional[Path] = Field(
        default=None,
        description="Directory containing profiles.yml for this project"
    )
    allowed_databases: Optional[List[str]] = Field(
        default=None,
        description="Databases this project can access"
    )
    allowed_schemas: Optional[List[str]] = Field(
        default=None,
        description="Schemas this project can access"
    )
    default_database: Optional[str] = Field(
        default=None,
        description="Default database for queries"
    )
    env: Optional[dict[str, str]] = Field(
        default=None,
        description="Environment variables to set when working with this project"
    )
    data: Optional[ProjectDataOverrides] = Field(
        default=None,
        description="Per-project data backend overrides"
    )
    git: Optional[GitConfig] = Field(
        default=None,
        description="Per-project git configuration for Data Engineer agents"
    )


def merge_data_config_with_overrides(
    base_config: DataConfig,
    overrides: Optional[ProjectDataOverrides]
) -> DataConfig:
    """Merge a base data config with per-project overrides.

    Args:
        base_config: The shared data configuration
        overrides: Optional per-project overrides

    Returns:
        A new DataConfig with overrides applied
    """
    if overrides is None:
        return base_config

    # Create a copy of the base config as a dict
    config_dict = base_config.model_dump()

    # Apply overrides (only non-None values)
    if overrides.database is not None:
        config_dict["database"] = overrides.database
    if overrides.warehouse is not None:
        config_dict["warehouse"] = overrides.warehouse
    if overrides.allowed_databases is not None:
        config_dict["allowed_databases"] = overrides.allowed_databases
    if overrides.allowed_schemas is not None:
        config_dict["allowed_schemas"] = overrides.allowed_schemas

    # Reconstruct the appropriate config type
    backend_type = config_dict.get("backend", "").lower()
    if backend_type == "snowflake":
        return SnowflakeDataConfig(**config_dict)
    elif backend_type == "duckdb":
        return DuckDBDataConfig(**config_dict)
    else:
        raise ValueError(f"Unknown data backend type: {backend_type}")


# ============================================================================
# Unified Configuration
# ============================================================================


class UnifiedConfig(BaseModel):
    """Complete system configuration.

    Combines lineage backend, data backend, memory backend, ticket backend,
    and agent settings into a single configuration file.

    Configuration supports environment variable interpolation using ${VAR_NAME} syntax.

    Example:
        config = UnifiedConfig.from_yaml(Path("config.yml"))
        lineage_storage = create_storage_from_unified_config(config.lineage)
        data_backend = create_data_backend_from_unified_config(config.data)
        memory_backend = create_memory_backend_from_unified_config(config.memory)
        ticket_storage = create_ticket_backend_from_unified_config(config.ticket)
        agent_model = config.agent.model
        git_config = config.get_project_git_config(project_name)
    """

    model_config = ConfigDict(extra="forbid")

    lineage: LineageConfig = Field(..., description="Lineage backend configuration")
    data: DataConfig = Field(..., description="Data backend configuration")
    memory: Optional[MemoryConfig] = Field(
        default=None,
        description="Memory backend configuration (optional)"
    )
    ticket: TicketConfig = Field(
        default_factory=TicketConfig,
        description="Ticket storage backend configuration (optional)"
    )
    agent: AgentConfig = Field(
        default_factory=AgentConfig,
        description="Agent runtime configuration"
    )
    reports: ReportsConfig = Field(
        default_factory=ReportsConfig,
        description="Reports backend configuration"
    )
    threads: ThreadsConfig = Field(
        default_factory=SQLiteThreadsConfig,
        description="Threads backend configuration (conversation memory)"
    )

    # Multi-project support
    default_project: Optional[str] = Field(
        default=None,
        description="Default project name (used when no project is specified)"
    )
    projects: Optional[dict[str, ProjectConfig]] = Field(
        default=None,
        description="Per-project configurations with optional data overrides"
    )

    # Population settings (for typedef sync command)
    # Stored as dict to avoid circular import with ingest.config
    # Use get_population_config() to parse as PopulationConfig
    population: Optional[dict] = Field(
        default=None,
        description="Population settings for sync (semantic analysis, profiling, clustering)"
    )

    def get_project_data_config(self, project_name: str) -> DataConfig:
        """Get data config for a specific project with overrides applied.

        Args:
            project_name: Name of the project

        Returns:
            DataConfig with project-specific overrides applied

        Raises:
            KeyError: If project not found in configuration
        """
        if not self.projects or project_name not in self.projects:
            raise KeyError(f"Project '{project_name}' not found in configuration")

        project = self.projects[project_name]

        # Merge project-level allowlists/defaults into per-project overrides.
        # This ensures settings collected by the TUI wizard (stored at the project
        # level) are applied to the data backend used for the active project.
        overrides = project.data.model_copy(deep=True) if project.data else ProjectDataOverrides()

        if project.allowed_databases is not None and overrides.allowed_databases is None:
            overrides.allowed_databases = project.allowed_databases
        if project.allowed_schemas is not None and overrides.allowed_schemas is None:
            overrides.allowed_schemas = project.allowed_schemas
        if project.default_database is not None and overrides.database is None:
            overrides.database = project.default_database

        has_overrides = any(
            getattr(overrides, field) is not None
            for field in ("database", "warehouse", "allowed_databases", "allowed_schemas")
        )
        return merge_data_config_with_overrides(self.data, overrides if has_overrides else None)

    def get_project_git_config(self, project_name: str) -> Optional[GitConfig]:
        """Get git config for a specific project.

        Args:
            project_name: Name of the project

        Returns:
            GitConfig if configured for this project, None otherwise

        Raises:
            KeyError: If project not found in configuration
        """
        if not self.projects or project_name not in self.projects:
            raise KeyError(f"Project '{project_name}' not found in configuration")

        project = self.projects[project_name]
        return project.git

    @classmethod
    def from_yaml(cls, path: Path) -> "UnifiedConfig":
        """Load configuration from YAML file with environment variable interpolation.

        Supports ${VAR_NAME} syntax for environment variable substitution.

        Optional environment variables can be specified using ${VAR_NAME?} syntax.
        If an optional variable is not set, it will be substituted with `null` (None in Python).

        Args:
            path: Path to YAML configuration file

        Returns:
            Parsed and validated UnifiedConfig

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If required environment variable is referenced but not set
            yaml.YAMLError: If YAML is invalid
            pydantic.ValidationError: If configuration is invalid

        Example:
            # config.yml contains:
            #   password: ${NEO4J_PASSWORD}  # Required
            #   team_id: ${LINEAR_TEAM_ID?}  # Optional
            # Set environment: export NEO4J_PASSWORD=secret
            config = UnifiedConfig.from_yaml(Path("config.yml"))
        """
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        with open(path) as f:
            raw_yaml = f.read()

        # Interpolate environment variables: ${VAR_NAME} or ${VAR_NAME?} for optional
        def interpolate(match):
            var_spec = match.group(1)
            # Check if it's optional (ends with ?)
            is_optional = var_spec.endswith('?')
            var_name = var_spec.rstrip('?')
            value = os.getenv(var_name)
            if value is None:
                if is_optional:
                    # Return null for optional variables (YAML will parse as None)
                    return 'null'
                else:
                    raise ValueError(
                        f"Environment variable '{var_name}' is not set "
                        f"(required by {path})"
                        f"Raw Yaml: {raw_yaml}"
                    )
            return value

        interpolated = re.sub(r'\$\{([^}]+)\}', interpolate, raw_yaml)
        data = yaml.safe_load(interpolated)

        try:
            return cls(**data)
        except Exception as e:
            # Detect legacy top-level git key and give a clear migration message
            if isinstance(data, dict) and "git" in data:
                raise ValueError(
                    f"Your configuration at {path} contains a top-level 'git:' block "
                    "which is no longer supported. Git settings are now per-project "
                    "under 'projects.<name>.git:'. "
                    "Run 'typedef init --reset' to regenerate your configuration."
                ) from e
            raise

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file.

        WARNING: This will write passwords in plaintext if they were interpolated.
        Use this for generating example configs, not for saving production configs.

        Args:
            path: Path to save YAML file
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            yaml.safe_dump(
                self.model_dump(mode='json'),
                f,
                default_flow_style=False,
                sort_keys=False,
            )
