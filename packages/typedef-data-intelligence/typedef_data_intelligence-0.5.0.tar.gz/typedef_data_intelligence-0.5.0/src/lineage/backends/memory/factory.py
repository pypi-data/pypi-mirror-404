"""Factory functions for creating memory backend instances.

This module provides factory functions that create MemoryStorage instances
from configuration objects, with graceful degradation when dependencies
are unavailable.
"""

from __future__ import annotations

import logging
from typing import Optional

from lineage.backends.config import (
    FalkorDBLiteMemoryConfig,
    FalkorDBMemoryConfig,
    MemoryConfig,
)
from lineage.backends.memory.falkordb_adapter import FalkorDBMemoryAdapter
from lineage.backends.memory.protocol import MemoryStorage

logger = logging.getLogger(__name__)


def create_memory_backend(config: MemoryConfig) -> Optional[MemoryStorage]:
    """Create memory storage backend from unified configuration.

    This function creates memory backend instances with graceful degradation:
    - If dependencies are unavailable, logs a warning and returns None
    - If connection fails, logs an error and returns None
    - If successful, returns a working MemoryStorage instance

    Args:
        config: Memory configuration (FalkorDBMemoryConfig or KuzuMemoryConfig)

    Returns:
        MemoryStorage instance, or None if backend cannot be created

    Example:
        ```python
        from lineage.backends.config import UnifiedConfig

        cfg = UnifiedConfig.from_yaml(Path("config.yml"))

        # Only create if memory is configured
        memory = None
        if cfg.memory:
            memory = create_memory_backend(cfg.memory)

        if memory:
            print("Memory backend initialized")
        else:
            print("Memory backend unavailable")
        ```

    Note:
        This function never raises exceptions - it always returns None on failure.
        This enables graceful degradation when memory backend is unavailable.
    """
    if isinstance(config, FalkorDBMemoryConfig):
        return _create_falkordb_backend(config)
    elif isinstance(config, FalkorDBLiteMemoryConfig):
        return _create_falkordblite_backend(config)
    else:
        logger.warning(
            f"Unknown memory config type: {type(config)}. "
            f"Memory features will be disabled."
        )
        return None


def _create_falkordb_backend(config: FalkorDBMemoryConfig) -> Optional[MemoryStorage]:
    """Create FalkorDB memory backend from configuration.

    Args:
        config: FalkorDB memory configuration

    Returns:
        FalkorDBMemoryAdapter instance, or None on failure
    """
    try:

        adapter = FalkorDBMemoryAdapter(
            host=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
            default_org_id=config.default_org_id,
        )

        logger.info(
            f"✅ Memory backend initialized: FalkorDB at {config.host}:{config.port} "
            f"(org={config.default_org_id})"
        )
        return adapter

    except ImportError as e:
        logger.warning(
            f"FalkorDB memory backend unavailable: {e}. "
            f"Install with: pip install graphiti-core graphiti-core-falkordb. "
            f"Memory features will be disabled."
        )
        return None

    except Exception as e:
        logger.error(
            f"Failed to initialize FalkorDB memory backend: {e}. "
            f"Memory features will be disabled."
        )
        return None


def _create_falkordblite_backend(config: FalkorDBLiteMemoryConfig) -> Optional[MemoryStorage]:
    """Create FalkorDBLite memory backend from configuration.

    Args:
        config: FalkorDBLite memory configuration

    Returns:
        FalkorDBLiteMemoryBackend instance, or None on failure
    """
    try:
        from lineage.backends.memory.falkordblite_backend import (
            FalkorDBLiteMemoryBackend,
        )

        adapter = FalkorDBLiteMemoryBackend(
            db_path=config.db_path,
            default_org_id=config.default_org_id,
            default_user_id=config.default_user_id,
        )

        logger.info(f"✅ Memory backend initialized: FalkorDBLite at {config.db_path}")
        return adapter

    except ImportError as e:
        logger.warning(
            f"FalkorDBLite memory backend unavailable: {e}. "
            f"Install with: pip install redislite. "
            f"Memory features will be disabled."
        )
        return None

    except Exception as e:
        logger.error(
            f"Failed to initialize FalkorDBLite memory backend: {e}. "
            f"Memory features will be disabled."
        )
        return None


__all__ = ["create_memory_backend"]
