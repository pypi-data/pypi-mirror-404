"""Factory functions for creating data query backend instances.

This module provides simple factory functions to create data query backends
from unified configuration.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from lineage.backends.config import DuckDBDataConfig, SnowflakeDataConfig
from lineage.backends.data_query.duckdb_backend import DuckDBBackend
from lineage.backends.data_query.snowflake_native_backend import SnowflakeNativeBackend

from .protocol import DataQueryBackend

if TYPE_CHECKING:
    from lineage.backends.config import DataConfig


def create_data_backend(config: "DataConfig", read_only: bool = True) -> DataQueryBackend:
    """Create data backend from unified configuration.

    Args:
        config: Unified data configuration
        read_only: Whether to open in read-only mode (default: True)

    Returns:
        Initialized data backend adapter

    Raises:
        ValueError: If unknown config type
        FileNotFoundError: If database file doesn't exist (DuckDB only)

    Example:
        from lineage.backends.config import UnifiedConfig

        cfg = UnifiedConfig.from_yaml(Path("config.yml"))
        backend = create_data_backend(cfg.data, read_only=True)
    """
    # Import here to avoid circular dependency

    if isinstance(config, DuckDBDataConfig):
        if not config.db_path.exists():
            raise FileNotFoundError(
                f"DuckDB database not found at {config.db_path}. "
                "Please provide a valid database path."
            )
        return DuckDBBackend(duckdb_config=config)

    elif isinstance(config, SnowflakeDataConfig):
        return SnowflakeNativeBackend(config)

    else:
        raise ValueError(f"Unknown data config type: {type(config)}")


def create_data_backend_for_cli(
    config: "DataConfig",
    read_only: bool = True,
) -> DataQueryBackend:
    """Create data backend for CLI commands.

    CLI-specific wrapper that provides better error messages.

    Args:
        config: Unified data configuration
        read_only: Whether to open in read-only mode (default: True)

    Returns:
        Initialized data backend adapter

    Raises:
        SystemExit: If configuration invalid or database not found
    """
    try:
        return create_data_backend(config, read_only=read_only)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "create_data_backend",
    "create_data_backend_for_cli",
]
