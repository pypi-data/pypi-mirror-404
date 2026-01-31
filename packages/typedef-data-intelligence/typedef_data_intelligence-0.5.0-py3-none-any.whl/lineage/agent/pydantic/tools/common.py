"""Shared helpers and error types for Pydantic agent tools."""

import logging
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ToolError(BaseModel):
    """Error raised when a tool fails."""
    error_message: str = Field(description="The error message returned by the tool.")


T = TypeVar("T")
ToolResult = T | ToolError


def tool_error(message: str) -> ToolError:
    """Create a ToolError with a consistent message field."""
    return ToolError(error_message=message)


def safe_tool(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    """Wrap a tool to return ToolError instead of raising on unexpected exceptions."""

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error("Unhandled tool error in %s: %s", func.__name__, e, exc_info=True)
            return tool_error(f"Unhandled tool error in {func.__name__}: {e}")

    return wrapper