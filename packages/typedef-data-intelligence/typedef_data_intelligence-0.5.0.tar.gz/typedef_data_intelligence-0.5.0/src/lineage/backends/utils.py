"""Filesystem utility functions for atomic file operations.

This module provides utility functions for safely writing JSON and text files
atomically using temporary files and os.replace.
"""
import json
import os
import uuid
from pathlib import Path


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating parent directories as needed.

    Args:
        path: Directory path to create.
    """
    path.mkdir(parents=True, exist_ok=True)


def atomic_write_json(path: Path, data: dict[str, object]) -> None:
    """Write JSON data to a file atomically using a temporary file.

    Args:
        path: Target file path.
        data: Dictionary to write as JSON.
    """
    ensure_directory(path.parent)
    tmp_path = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    os.replace(tmp_path, path)


def atomic_write_text(path: Path, content: str) -> None:
    """Write text content to a file atomically using a temporary file.

    Args:
        path: Target file path.
        content: Text content to write.
    """
    ensure_directory(path.parent)
    tmp_path = path.with_suffix(path.suffix + f".{uuid.uuid4().hex}.tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(tmp_path, path)


def read_json(path: Path) -> dict:
    """Read and parse a JSON file.

    Args:
        path: File path to read.

    Returns:
        Parsed JSON data as a dictionary.
    """
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    """Read a text file.

    Args:
        path: File path to read.

    Returns:
        File contents as a string.
    """
    with path.open(encoding="utf-8") as handle:
        return handle.read()
