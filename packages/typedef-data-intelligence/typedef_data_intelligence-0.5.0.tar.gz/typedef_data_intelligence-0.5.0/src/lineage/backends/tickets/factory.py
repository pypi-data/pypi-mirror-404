"""Factory functions for creating ticket storage backend instances.

This module provides factory functions that create TicketStorage instances
from configuration objects, with graceful degradation when initialization fails.
"""

from __future__ import annotations

import logging
from pathlib import Path
import os
from typing import Optional, Union, Literal

from lineage.backends.tickets.protocol import TicketStorage

logger = logging.getLogger(__name__)


def create_ticket_backend(
    backend: str,
    base_path: str | Path = "./tickets",
    mcp_config_path: Optional[str | Path] = None,
    mcp_server_url: Optional[str] = None,
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
) -> Optional[TicketStorage]:
    """Create a ticket storage backend from configuration.

    This function creates ticket backend instances with graceful degradation:
    - If initialization fails, logs a warning and returns None
    - If successful, returns a working TicketStorage instance

    Args:
        backend: Backend type ("filesystem" or "linear")
        base_path: Base directory for ticket storage (filesystem backend only)
        mcp_config_path: Path to MCP configuration file (linear backend only)
        mcp_server_url: URL of MCP server (linear backend only)
        team_id: Linear team ID (linear backend only)
        project_id: Linear project ID (linear backend only)

    Returns:
        TicketStorage instance, or None if backend cannot be created

    Example:
        ```python
        # Filesystem backend
        ticket_storage = create_ticket_backend(
            backend="filesystem",
            base_path="./tickets"
        )

        # Linear backend
        ticket_storage = create_ticket_backend(
            backend="linear",
            mcp_config_path="./linear-mcp.json",
            team_id="team-123"
        )

        if ticket_storage:
            print("Ticket storage initialized")
        else:
        print("Ticket storage unavailable (graceful degradation)")
        ```

    Note:
        This function never raises exceptions - it always returns None on failure.
        This enables graceful degradation when ticket storage is unavailable.
    """
    backend_lower = backend.lower()


    if backend_lower == "filesystem":
        return _create_filesystem_backend(base_path=base_path)
    elif backend_lower == "linear":
        env_has_linear_keys = os.getenv("LINEAR_ANALYST_API_KEY") or os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
        if not env_has_linear_keys:
            logger.warning("No Linear API keys found in environment variables.  Ticket backend will be disabled.")
            return None
        return _create_linear_backend(
            mcp_config_path=mcp_config_path,
            mcp_server_url=mcp_server_url,
            team_id=team_id,
            project_id=project_id,
        )
    else:
        logger.warning(
            f"Unknown ticket backend: {backend}. Supported: filesystem, linear. "
            f"Ticket features will be disabled."
        )
        return None


def create_ticket_backend_from_config(config: "TicketConfig", role: Literal["analyst", "data_engineer"]) -> Optional[TicketStorage]:
    """Create ticket backend from unified configuration.

    Args:
        config: Ticket configuration object
        role: Role to use for tickets (analyst or data_engineer).  Dictates which user token to use for Linear.

    Returns:
        TicketStorage instance, or None if backend cannot be created
    """
    # Import here to avoid circular dependency
    from lineage.backends.config import FilesystemTicketConfig, LinearTicketConfig

    env_has_linear_keys = os.getenv("LINEAR_ANALYST_API_KEY") and os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
    if isinstance(config, FilesystemTicketConfig):
        return _create_filesystem_backend(base_path=config.base_path)
    elif isinstance(config, LinearTicketConfig):
        env_has_linear_keys = os.getenv("LINEAR_ANALYST_API_KEY") or os.getenv("LINEAR_DATA_ENGINEER_API_KEY")
        if not env_has_linear_keys:
            logger.warning("No Linear API keys found in environment variables.  Ticket backend will be disabled.")
            return None
        return _create_linear_backend(
            mcp_server_url=config.mcp_server_url,
            team_id=config.team_id,
            project_id=config.project_id,
            role=role,
        )
    else:
        logger.warning(f"Unknown ticket config type: {type(config)}")
        return None


def _create_filesystem_backend(
    base_path: str | Path,
) -> Optional[TicketStorage]:
    """Create filesystem ticket backend.

    Args:
        base_path: Base directory for ticket JSON files

    Returns:
        FilesystemTicketStorage instance, or None on failure
    """
    try:
        from lineage.backends.tickets.filesystem_backend import FilesystemTicketStorage

        storage = FilesystemTicketStorage(base_path=str(base_path))

        logger.info(
            f"✅ Ticket storage initialized: Filesystem at {base_path}"
        )
        return storage

    except Exception as e:
        logger.error(
            f"Failed to initialize filesystem ticket storage: {e}. "
            f"Ticket features will be disabled."
        )
        return None


def _create_linear_backend(
    mcp_server_url: Optional[str] = None,
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
    role: Optional[Literal["analyst", "data_engineer"]] = "analyst",
) -> Optional[TicketStorage]:
    """Create Linear ticket backend.

    Args:
        mcp_server_url: URL of Linear MCP server (optional)
        team_id: Linear team ID (optional)
        project_id: Linear project ID (optional)
        role: Role to use for tickets (analyst or data_engineer).  Dictates which user token to use for Linear.

    Returns:
        LinearTicketStorage instance, or None on failure
    """
    try:
        from lineage.backends.tickets.linear_backend import LinearTicketStorage

        if not mcp_server_url:
            raise ValueError("mcp_server_url is required for Linear backend")

        storage = LinearTicketStorage(
            mcp_server_url=mcp_server_url,
            team_id=team_id,
            project_id=project_id,
            role=role,
        )

        logger.info(
            f"✅ Ticket storage initialized: Linear MCP at {mcp_server_url}"
        )
        return storage

    except Exception as e:
        logger.error(
            f"Failed to initialize Linear ticket storage: {e}. "
            f"Ticket features will be disabled."
        )
        return None


__all__ = ["create_ticket_backend", "create_ticket_backend_from_config"]
