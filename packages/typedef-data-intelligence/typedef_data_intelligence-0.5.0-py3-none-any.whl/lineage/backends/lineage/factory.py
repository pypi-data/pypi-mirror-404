"""Factory functions for creating storage backend instances.

This module provides simple factory functions to create lineage storage adapters
from unified configuration.
"""

from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

from .protocol import LineageStorage

if TYPE_CHECKING:
    from lineage.backends.config import LineageConfig


def create_storage(config: "LineageConfig", read_only: bool = False) -> LineageStorage:
    """Create storage adapter from unified configuration.

    Args:
        config: Unified lineage configuration
        read_only: Whether to open in read-only mode (default: False)

    Returns:
        Initialized storage adapter

    Raises:
        ValueError: If unknown config type

    Example:
        from lineage.backends.config import UnifiedConfig

        cfg = UnifiedConfig.from_yaml(Path("config.yml"))
        storage = create_storage(cfg.lineage, read_only=True)
    """
    # Import here to avoid circular dependency
    from lineage.backends.config import (
        FalkorDBLineageConfig,
        FalkorDBLiteLineageConfig,
    )
    # Suppress noisy FalkorDB import-time DeprecationWarnings (swig bindings)
    warnings.filterwarnings("ignore", message=".*swigvarlink.*")
    # Suppress noisy fenic sqlite3 warnings (default datetime adapter)
    warnings.filterwarnings("ignore", message=".*default datetime adapter is deprecated.*")
    if isinstance(config, FalkorDBLineageConfig):
        from lineage.backends.lineage.falkordb_adapter import FalkorDBAdapter
        return FalkorDBAdapter(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            graph_name=config.graph_name,
            read_only=read_only,
        )

    elif isinstance(config, FalkorDBLiteLineageConfig):
        from lineage.backends.lineage.falkordblite_adapter import FalkorDBLiteAdapter
        return FalkorDBLiteAdapter(
            db_path=config.db_path,
            graph_name=config.graph_name,
            read_only=read_only,
        )

    else:
        raise ValueError(f"Unknown lineage config type: {type(config)}")


def create_storage_for_cli(config: "LineageConfig", read_only: bool = False) -> LineageStorage:
    """Create storage adapter for CLI commands.

    CLI-specific wrapper that provides better error messages.

    Args:
        config: Unified lineage configuration
        read_only: Whether to open in read-only mode

    Returns:
        Initialized storage adapter

    Raises:
        SystemExit: If configuration invalid or database not found
    """
    try:
        return create_storage(config, read_only=read_only)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nRun 'lineage init --config <config.yml>' to initialize the database", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


__all__ = [
    "create_storage",
    "create_storage_for_cli",
]
