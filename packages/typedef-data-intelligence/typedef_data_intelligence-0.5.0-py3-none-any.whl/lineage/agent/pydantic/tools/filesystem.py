"""Filesystem tools for PydanticAI agents.

Provides Claude Code-equivalent file operations: read, write, edit, glob, grep.
All operations are restricted to the configured working directory for safety.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import AgentDeps
from lineage.backends.utils import atomic_write_text

logger = logging.getLogger(__name__)

# ============================================================================
# Result Models
# ============================================================================


class FileContent(BaseModel):
    """Result from read_file tool."""

    tool_name: str = "read_file"
    file_path: str
    content: str
    line_count: int
    start_line: int
    end_line: int


class WriteResult(BaseModel):
    """Result from write_file tool."""

    tool_name: str = "write_file"
    file_path: str
    bytes_written: int
    message: str


class EditResult(BaseModel):
    """Result from edit_file tool."""

    tool_name: str = "edit_file"
    file_path: str
    replacements: int
    message: str


class GrepMatch(BaseModel):
    """Single match from grep_files."""

    file: str
    line: int
    content: str


class GrepResult(BaseModel):
    """Result from grep_files tool."""

    tool_name: str = "grep_files"
    pattern: str
    matches: List[GrepMatch] = Field(default_factory=list)
    match_count: int = 0
    files_searched: int = 0


class GlobResult(BaseModel):
    """Result from glob_files tool."""

    tool_name: str = "glob_files"
    pattern: str
    files: List[str] = Field(default_factory=list)
    count: int = 0


# ============================================================================
# Path Validation
# ============================================================================


def _validate_path(base_dir: Path, requested_path: str) -> Path:
    """Validate that a path stays within the allowed directory.

    Args:
        base_dir: The base directory that paths must stay within
        requested_path: The path requested by the user (relative or absolute)

    Returns:
        Resolved absolute path

    Raises:
        ValueError: If path escapes the base directory
    """
    # Handle relative paths
    if not Path(requested_path).is_absolute():
        full_path = base_dir / requested_path
    else:
        full_path = Path(requested_path)

    # Resolve to absolute, following symlinks
    resolved = full_path.resolve()

    # Ensure path is within base directory
    try:
        resolved.relative_to(base_dir.resolve())
    except ValueError as e:
        raise ValueError(
            f"Path '{requested_path}' escapes working directory '{base_dir}'"
        ) from e

    return resolved


def _get_working_dir(ctx: RunContext[AgentDeps]) -> Path:
    """Get the working directory from context, with fallback to cwd.

    Returns resolved path to handle symlinks (e.g., /tmp -> /private/tmp on macOS).
    """
    if ctx.deps.filesystem_config and ctx.deps.filesystem_config.working_directory:
        return Path(ctx.deps.filesystem_config.working_directory).resolve()
    return Path.cwd().resolve()


def _is_read_only(ctx: RunContext[AgentDeps]) -> bool:
    """Check if filesystem is configured as read-only."""
    if ctx.deps.filesystem_config:
        return ctx.deps.filesystem_config.read_only
    return False


# ============================================================================
# Filesystem Toolset
# ============================================================================

filesystem_toolset = FunctionToolset()


@filesystem_toolset.tool
@safe_tool
async def read_file(
    ctx: RunContext[AgentDeps],
    file_path: str,
    offset: int = 0,
    limit: int = 2000,
) -> FileContent | ToolError:
    """Read a file from the filesystem with line numbers.

    Args:
        ctx: Runtime context with agent dependencies
        file_path: Path to the file (relative to working directory or absolute)
        offset: Line number to start reading from (0-indexed, default: 0)
        limit: Maximum number of lines to read (default: 2000)

    Returns:
        FileContent with numbered lines, or ToolError on failure

    Example:
        read_file("models/marts/fct_revenue.sql")
        read_file("models/schema.yml", offset=100, limit=50)
    """
    working_dir = _get_working_dir(ctx)

    try:
        resolved_path = _validate_path(working_dir, file_path)
    except ValueError as e:
        return tool_error(str(e))

    if not resolved_path.exists():
        return tool_error(f"File not found: {file_path}")

    if not resolved_path.is_file():
        return tool_error(f"Not a file: {file_path}")

    try:
        content = resolved_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        total_lines = len(lines)

        # Apply offset and limit
        start_idx = max(0, offset)
        end_idx = min(total_lines, start_idx + limit)
        selected_lines = lines[start_idx:end_idx]

        # Format with line numbers (1-indexed for display)
        numbered_lines = [
            f"{i + start_idx + 1:6d}\t{line}"
            for i, line in enumerate(selected_lines)
        ]
        formatted_content = "\n".join(numbered_lines)

        return FileContent(
            file_path=str(resolved_path.relative_to(working_dir)),
            content=formatted_content,
            line_count=total_lines,
            start_line=start_idx + 1,
            end_line=end_idx,
        )
    except UnicodeDecodeError:
        return tool_error(f"Cannot read binary file: {file_path}")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return tool_error(f"Error reading file: {e}")


@filesystem_toolset.tool
@safe_tool
async def write_file(
    ctx: RunContext[AgentDeps],
    file_path: str,
    content: str,
) -> WriteResult | ToolError:
    """Write content to a file atomically.

    Creates parent directories if they don't exist. Uses atomic write
    (temp file + rename) to prevent corruption.

    Args:
        ctx: Runtime context with agent dependencies
        file_path: Path to the file (relative to working directory or absolute)
        content: Content to write to the file

    Returns:
        WriteResult on success, or ToolError on failure

    Example:
        write_file("models/marts/fct_new_model.sql", "SELECT * FROM ...")
    """
    if _is_read_only(ctx):
        return tool_error("Filesystem is configured as read-only")

    working_dir = _get_working_dir(ctx)

    try:
        resolved_path = _validate_path(working_dir, file_path)
    except ValueError as e:
        return tool_error(str(e))

    try:
        atomic_write_text(resolved_path, content)
        bytes_written = len(content.encode("utf-8"))

        return WriteResult(
            file_path=str(resolved_path.relative_to(working_dir)),
            bytes_written=bytes_written,
            message=f"Successfully wrote {bytes_written} bytes to {file_path}",
        )
    except Exception as e:
        logger.error(f"Error writing file {file_path}: {e}")
        return tool_error(f"Error writing file: {e}")


@filesystem_toolset.tool
@safe_tool
async def edit_file(
    ctx: RunContext[AgentDeps],
    file_path: str,
    old_string: str,
    new_string: str,
    replace_all: bool = False,
) -> EditResult | ToolError:
    """Edit a file by replacing text.

    By default, requires old_string to appear exactly once in the file
    to prevent accidental replacements. Use replace_all=True to replace
    all occurrences.

    Args:
        ctx: Runtime context with agent dependencies
        file_path: Path to the file (relative to working directory or absolute)
        old_string: Text to find and replace
        new_string: Text to replace with
        replace_all: If True, replace all occurrences. If False (default),
                    require exactly one occurrence.

    Returns:
        EditResult on success, or ToolError on failure

    Example:
        edit_file("models/marts/fct_revenue.sql", "old_column", "new_column")
        edit_file("models/schema.yml", "TODO", "DONE", replace_all=True)
    """
    if _is_read_only(ctx):
        return tool_error("Filesystem is configured as read-only")

    working_dir = _get_working_dir(ctx)

    try:
        resolved_path = _validate_path(working_dir, file_path)
    except ValueError as e:
        return tool_error(str(e))

    if not resolved_path.exists():
        return tool_error(f"File not found: {file_path}")

    if not resolved_path.is_file():
        return tool_error(f"Not a file: {file_path}")

    try:
        content = resolved_path.read_text(encoding="utf-8")
        occurrences = content.count(old_string)

        if occurrences == 0:
            return tool_error(
                f"Text not found in {file_path}: '{old_string[:100]}...'"
                if len(old_string) > 100
                else f"Text not found in {file_path}: '{old_string}'"
            )

        if not replace_all and occurrences > 1:
            return tool_error(
                f"Text appears {occurrences} times in {file_path}. "
                "Use replace_all=True to replace all, or provide more context "
                "to make the match unique."
            )

        if replace_all:
            new_content = content.replace(old_string, new_string)
            replacements = occurrences
        else:
            new_content = content.replace(old_string, new_string, 1)
            replacements = 1

        atomic_write_text(resolved_path, new_content)

        return EditResult(
            file_path=str(resolved_path.relative_to(working_dir)),
            replacements=replacements,
            message=f"Successfully replaced {replacements} occurrence(s) in {file_path}",
        )
    except UnicodeDecodeError:
        return tool_error(f"Cannot edit binary file: {file_path}")
    except Exception as e:
        logger.error(f"Error editing file {file_path}: {e}")
        return tool_error(f"Error editing file: {e}")


@filesystem_toolset.tool
@safe_tool
async def glob_files(
    ctx: RunContext[AgentDeps],
    pattern: str,
    path: Optional[str] = None,
) -> GlobResult | ToolError:
    """Find files matching a glob pattern.

    Args:
        ctx: Runtime context with agent dependencies
        pattern: Glob pattern (e.g., "**/*.sql", "models/*.yml")
        path: Directory to search in (relative to working dir, default: working dir)

    Returns:
        GlobResult with matching file paths sorted by modification time

    Example:
        glob_files("**/*.sql")
        glob_files("*.yml", path="models")
    """
    working_dir = _get_working_dir(ctx)

    try:
        if path:
            search_dir = _validate_path(working_dir, path)
        else:
            search_dir = working_dir
    except ValueError as e:
        return tool_error(str(e))

    if not search_dir.exists():
        return tool_error(f"Directory not found: {path or '.'}")

    if not search_dir.is_dir():
        return tool_error(f"Not a directory: {path or '.'}")

    try:
        # Find all matching files
        matches = list(search_dir.glob(pattern))

        # Filter to only files (not directories)
        files = [m for m in matches if m.is_file()]

        # Validate all matches are within working directory
        validated_files = []
        for f in files:
            try:
                f.resolve().relative_to(working_dir.resolve())
                validated_files.append(f)
            except ValueError:
                # Skip files outside working directory
                continue

        # Sort by modification time (most recent first)
        validated_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Convert to relative paths
        relative_paths = [
            str(f.relative_to(working_dir)) for f in validated_files
        ]

        return GlobResult(
            pattern=pattern,
            files=relative_paths,
            count=len(relative_paths),
        )
    except Exception as e:
        logger.error(f"Error globbing {pattern}: {e}")
        return tool_error(f"Error searching files: {e}")


@filesystem_toolset.tool
@safe_tool
async def grep_files(
    ctx: RunContext[AgentDeps],
    pattern: str,
    path: Optional[str] = None,
    glob_pattern: str = "**/*",
    max_matches: int = 100,
) -> GrepResult | ToolError:
    """Search for text pattern in files using regex.

    Args:
        ctx: Runtime context with agent dependencies
        pattern: Regex pattern to search for
        path: Directory to search in (relative to working dir, default: working dir)
        glob_pattern: Glob pattern to filter files (default: "**/*" for all files)
        max_matches: Maximum number of matches to return (default: 100)

    Returns:
        GrepResult with matching lines and file locations

    Example:
        grep_files("def calculate_revenue")
        grep_files("TODO|FIXME", glob_pattern="**/*.py")
        grep_files("customer_id", path="models/marts")
    """
    working_dir = _get_working_dir(ctx)

    try:
        if path:
            search_dir = _validate_path(working_dir, path)
        else:
            search_dir = working_dir
    except ValueError as e:
        return tool_error(str(e))

    if not search_dir.exists():
        return tool_error(f"Directory not found: {path or '.'}")

    if not search_dir.is_dir():
        return tool_error(f"Not a directory: {path or '.'}")

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return tool_error(f"Invalid regex pattern: {e}")

    matches: List[GrepMatch] = []
    files_searched = 0

    try:
        # Find files matching glob pattern
        files = [f for f in search_dir.glob(glob_pattern) if f.is_file()]

        for file_path in files:
            # Skip files outside working directory
            try:
                file_path.resolve().relative_to(working_dir.resolve())
            except ValueError:
                continue

            # Skip binary files
            try:
                content = file_path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue

            files_searched += 1

            # Search each line
            for line_num, line in enumerate(content.splitlines(), start=1):
                if regex.search(line):
                    relative_path = str(file_path.relative_to(working_dir))
                    matches.append(
                        GrepMatch(
                            file=relative_path,
                            line=line_num,
                            content=line.strip()[:200],  # Truncate long lines
                        )
                    )
                    if len(matches) >= max_matches:
                        break

            if len(matches) >= max_matches:
                break

        return GrepResult(
            pattern=pattern,
            matches=matches,
            match_count=len(matches),
            files_searched=files_searched,
        )
    except Exception as e:
        logger.error(f"Error grepping for {pattern}: {e}")
        return tool_error(f"Error searching: {e}")
