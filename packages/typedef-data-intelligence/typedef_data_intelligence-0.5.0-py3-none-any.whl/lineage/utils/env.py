"""Environment variable management for de-agentic-demo.

This module provides utilities for loading environment variables from .env files
and expanding ${VAR} placeholders in configuration dictionaries.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def get_repo_root() -> Path:
    """Find the repository root directory."""
    current = Path(__file__).resolve()
    # Go up to the repo root (src/utils/env.py -> utils -> src -> repo_root)
    return current.parent.parent.parent.parent.parent


def load_env_file() -> None:
    """Load environment variables from .env files.

    Loads from ~/.typedef/.env and <repo_root>/.env if they exist.
    Does nothing if files don't exist. This function is idempotent.
    """
    typedef_env = Path.home() / ".typedef" / ".env"
    if typedef_env.exists():
        load_dotenv(typedef_env, override=False)

    repo_env = get_repo_root() / ".env"
    if repo_env.exists():
        load_dotenv(repo_env, override=False)


def expand_env_vars(obj: Any) -> Any:
    """Recursively expand ${VAR} and ${VAR:-default} placeholders in strings.

    Supports:
    - ${VAR} - replaced with env var value, raises error if not set
    - ${VAR:-default} - replaced with env var value, or default if not set

    Args:
        obj: Any Python object (dict, list, str, or other)

    Returns:
        Object with all ${VAR} placeholders expanded

    Raises:
        ValueError: If a ${VAR} placeholder references an undefined variable
    """
    if isinstance(obj, dict):
        return {key: expand_env_vars(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        return _expand_string(obj)
    else:
        return obj


def _expand_string(value: str) -> str:
    """Expand environment variables in a string.

    Supports two formats:
    - ${VAR} - must be set, raises error if not
    - ${VAR:-default} - uses default if VAR not set
    """
    # Pattern matches ${VAR} or ${VAR:-default}
    pattern = re.compile(r"\$\{([^}:]+)(?::-(.*?))?\}")

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        default_value = match.group(2)

        env_value = os.environ.get(var_name)

        if env_value is not None:
            return env_value
        elif default_value is not None:
            return default_value
        else:
            raise ValueError(
                f"Environment variable '{var_name}' is not set and no default provided. "
                f"Please set it in your .env file or environment."
            )

    return pattern.sub(replacer, value)


def get_env(var_name: str, default: str | None = None) -> str:
    """Get an environment variable value with optional default.

    Args:
        var_name: Name of the environment variable
        default: Default value if variable is not set

    Returns:
        Value of the environment variable

    Raises:
        ValueError: If variable is not set and no default provided
    """
    value = os.environ.get(var_name)
    if value is None:
        if default is None:
            raise ValueError(
                f"Environment variable '{var_name}' is not set. "
                f"Please set it in your .env file or environment."
            )
        return default
    return value


# Auto-load .env file when this module is imported
load_env_file()
