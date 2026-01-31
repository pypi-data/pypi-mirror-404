"""Automatic MCP tool generation from Protocol classes.

This module provides utilities to automatically expose Protocol methods as FastMCP tools,
eliminating boilerplate and keeping MCP servers in sync with protocol definitions.

Benefits:
- Zero boilerplate: Protocol methods automatically become MCP tools
- Single source of truth: Docstrings and signatures stay in sync
- Type-safe: Pydantic models work natively with FastMCP
- Future-proof: New protocol methods automatically exposed
"""

from __future__ import annotations

import inspect
import logging
from typing import Any, Callable, Optional, Protocol, Set

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


def auto_expose_protocol(
    mcp: FastMCP,
    backend: Any,
    protocol_class: type[Protocol],
    exclude_methods: Optional[Set[str]] = None,
) -> None:
    """Automatically expose all protocol methods as FastMCP tools.

    This function inspects a Protocol class and creates MCP tools for each method,
    preserving docstrings, signatures, and handling async methods automatically.

    Args:
        mcp: FastMCP server instance to register tools on
        backend: Backend instance implementing the protocol
        protocol_class: Protocol class to inspect for methods
        exclude_methods: Set of method names to skip (e.g., {"get_backend_type"})

    Example:
        ```python
        mcp = FastMCP("data-query")
        backend = DuckDBBackend(db_path="data.duckdb")

        # Automatically expose all DataQueryBackend methods
        auto_expose_protocol(
            mcp=mcp,
            backend=backend,
            protocol_class=DataQueryBackend,
            exclude_methods={"get_backend_type"}
        )
        ```

    Note:
        - Async methods are automatically wrapped to work with FastMCP
        - Pydantic models are returned directly (FastMCP handles serialization)
        - Docstrings and parameter names are preserved from protocol
        - Private methods (starting with '_') are automatically excluded
    """
    exclude_methods = exclude_methods or set()

    # Get all methods from the protocol
    for name, method in inspect.getmembers(protocol_class, predicate=inspect.isfunction):
        # Skip private methods, dunder methods, and excluded methods
        if name.startswith("_") or name in exclude_methods:
            continue

        # Get the actual implementation from the backend
        backend_method = getattr(backend, name, None)
        if backend_method is None:
            logger.warning(f"Backend does not implement protocol method: {name}")
            continue

        # Create wrapper that preserves signature and docstring
        wrapper = _create_tool_wrapper(
            method_name=name,
            backend_method=backend_method,
            protocol_method=method,
        )

        # Register as MCP tool
        mcp.tool()(wrapper)
        logger.debug(f"Registered MCP tool: {name}")


def _create_tool_wrapper(
    method_name: str,
    backend_method: Callable,
    protocol_method: Callable,
) -> Callable:
    """Create a wrapper function that FastMCP can use as a tool.

    Args:
        method_name: Name of the method
        backend_method: Actual implementation from backend
        protocol_method: Protocol method (for signature/docstring)

    Returns:
        Wrapper function with preserved signature and docstring
    """
    # Check if method is async
    is_async = inspect.iscoroutinefunction(backend_method)

    # Get signature from protocol (for parameter names/types)
    sig = inspect.signature(protocol_method)

    # Get docstring from protocol
    doc = inspect.getdoc(protocol_method) or f"{method_name} (auto-generated)"

    # Create parameter list (excluding 'self')
    params = [
        p for p in sig.parameters.values()
        if p.name != "self"
    ]

    if is_async:
        # For async methods, create an async wrapper
        async def async_wrapper(**kwargs):
            # Call backend method with kwargs
            result = await backend_method(**kwargs)
            # FastMCP handles Pydantic serialization automatically
            return result

        # Set function metadata
        async_wrapper.__name__ = method_name
        async_wrapper.__doc__ = doc
        async_wrapper.__signature__ = sig.replace(parameters=params)

        return async_wrapper
    else:
        # For sync methods, create a sync wrapper
        def sync_wrapper(**kwargs):
            # Call backend method with kwargs
            result = backend_method(**kwargs)
            # FastMCP handles Pydantic serialization automatically
            return result

        # Set function metadata
        sync_wrapper.__name__ = method_name
        sync_wrapper.__doc__ = doc
        sync_wrapper.__signature__ = sig.replace(parameters=params)

        return sync_wrapper


__all__ = ["auto_expose_protocol"]
