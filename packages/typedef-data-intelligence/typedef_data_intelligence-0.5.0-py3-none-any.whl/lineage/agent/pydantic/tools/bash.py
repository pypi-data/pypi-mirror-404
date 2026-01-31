"""Sandboxed bash tools for PydanticAI agents.

Provides a sandboxed bash execution with command whitelist for safety.
Only allows specific commands to prevent arbitrary code execution.
"""
from __future__ import annotations

import asyncio
import logging
import re
import shlex
from pathlib import Path
from typing import Optional, Set

from pydantic_ai import FunctionToolset, RunContext

from lineage.agent.pydantic.tools.common import ToolError, safe_tool, tool_error
from lineage.agent.pydantic.types import AgentDeps, BashResult

logger = logging.getLogger(__name__)

# Maximum output size to prevent token overflow
MAX_OUTPUT_SIZE = 20000

# ============================================================================
# Command Whitelist
# ============================================================================

# Allowed commands for sandboxed execution
ALLOWED_COMMANDS: Set[str] = {
    # Navigation and listing
    "ls",
    "pwd",
    "tree",
    "find",
    # File reading (read-only)
    "cat",
    "head",
    "tail",
    "wc",
    "file",
    "stat",
    "less",
    "more",
    # Text processing
    "sort",
    "uniq",
    "cut",
    "awk",
    "sed",
    "grep",
    "egrep",
    "fgrep",
    "tr",
    "diff",
    # File operations (careful - can modify)
    "mkdir",
    "rm",
    "cp",
    "mv",
    "touch",
    "ln",
    # Utility
    "echo",
    "env",
    "which",
    "whoami",
    "date",
    "basename",
    "dirname",
    "realpath",
    # Compression
    "tar",
    "gzip",
    "gunzip",
    "zip",
    "unzip",
    # JSON/YAML processing
    "jq",
    "yq",
}

# Commands that are always blocked (dangerous)
BLOCKED_COMMANDS: Set[str] = {
    "sudo",
    "su",
    "chmod",
    "chown",
    "chgrp",
    "curl",
    "wget",
    "ssh",
    "scp",
    "rsync",
    "nc",
    "netcat",
    "telnet",
    "ftp",
    "sftp",
    "python",
    "python3",
    "node",
    "ruby",
    "perl",
    "php",
    "sh",
    "bash",
    "zsh",
    "fish",
    "eval",
    "exec",
    "source",
    ".",
    "kill",
    "killall",
    "pkill",
    "nohup",
    "screen",
    "tmux",
    "at",
    "cron",
    "crontab",
}

# ============================================================================
# Shell Operator Patterns (for security validation)
# ============================================================================

# Matches pipe operator | but not || (logical OR)
# Uses negative lookbehind/lookahead to exclude ||
PIPE_PATTERN = re.compile(r"(?<!\|)\|(?!\|)")

# Matches command chaining operators: &&, ||, or ;
CHAIN_PATTERN = re.compile(r"(&&|\|\||;)")

# Matches command substitution: $( or backtick
# Also matches process substitution: <( and >(
SUBST_PATTERN = re.compile(r"(\$\(|`|<\(|>\()")


# ============================================================================
# Helper Functions
# ============================================================================


def _get_working_dir(ctx: RunContext[AgentDeps]) -> Path:
    """Get the working directory from context.

    Returns resolved path to handle symlinks (e.g., /tmp -> /private/tmp on macOS).
    """
    if ctx.deps.filesystem_config and ctx.deps.filesystem_config.working_directory:
        return Path(ctx.deps.filesystem_config.working_directory).resolve()
    if ctx.deps.git_config and ctx.deps.git_config.working_directory:
        return Path(ctx.deps.git_config.working_directory).resolve()
    return Path.cwd().resolve()


def _extract_base_command(command: str) -> Optional[str]:
    """Extract the base command from a shell command string.

    Handles pipes, redirects, and command substitution by extracting
    the first command in a pipeline.

    Args:
        command: Full shell command string

    Returns:
        Base command name, or None if parsing fails
    """
    try:
        # Use shlex to properly parse the command
        parts = shlex.split(command)
        if not parts:
            return None

        # Get the first part (the command)
        base = parts[0]

        # Handle path-qualified commands (e.g., /usr/bin/ls)
        if "/" in base:
            base = Path(base).name

        return base
    except ValueError:
        # shlex parsing failed, try a simpler approach
        # Split on common shell operators
        for sep in ["|", ";", "&&", "||", "`", "$("]:
            if sep in command:
                command = command.split(sep)[0].strip()

        parts = command.split()
        if parts:
            base = parts[0]
            if "/" in base:
                base = Path(base).name
            return base
        return None


def _validate_command(command: str) -> Optional[str]:
    """Validate that a command is allowed.

    Args:
        command: Shell command to validate

    Returns:
        Error message if command is not allowed, None if allowed
    """
    # Check for newline characters (command separators in shell)
    # These bypass per-command validation since shell executes each line separately
    if "\n" in command or "\r" in command:
        return "Newline characters are not allowed for security"

    # Check for command/process substitution first (highest security risk)
    # This catches $(...), backticks, <(...), and >(...) regardless of context
    if SUBST_PATTERN.search(command):
        return "Command substitution and process substitution are not allowed for security"

    # Check for command chaining (&&, ||, ;) - block entirely
    # These allow running multiple commands which bypasses per-command validation
    if CHAIN_PATTERN.search(command):
        return "Command chaining (&&, ||, ;) is not allowed for security"

    # Split on pipes (using regex to handle any whitespace around |)
    # and validate each command in the pipeline
    pipe_parts = PIPE_PATTERN.split(command)

    for part in pipe_parts:
        part = part.strip()
        if not part:
            continue

        part_cmd = _extract_base_command(part)

        if not part_cmd:
            return f"Could not parse command segment: {part}"

        # Check against blocked commands first
        if part_cmd in BLOCKED_COMMANDS:
            if len(pipe_parts) > 1:
                return f"Piped command '{part_cmd}' is blocked for security reasons"
            return f"Command '{part_cmd}' is blocked for security reasons"

        # Check against allowed commands
        if part_cmd not in ALLOWED_COMMANDS:
            allowed_list = ", ".join(sorted(ALLOWED_COMMANDS)[:20])
            if len(pipe_parts) > 1:
                return (
                    f"Piped command '{part_cmd}' is not in the allowed list. "
                    f"Allowed commands include: {allowed_list}..."
                )
            return (
                f"Command '{part_cmd}' is not in the allowed list. "
                f"Allowed commands include: {allowed_list}..."
            )

    return None


def _truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> str:
    """Truncate output if it exceeds max size."""
    if len(output) > max_size:
        return f"... (truncated, showing last {max_size} chars)\n" + output[-max_size:]
    return output


# ============================================================================
# Bash Toolset
# ============================================================================

bash_toolset = FunctionToolset()


@bash_toolset.tool
@safe_tool
async def bash(
    ctx: RunContext[AgentDeps],
    command: str,
    timeout_s: int = 120,
) -> BashResult | ToolError:
    r"""Execute a sandboxed bash command.

    Only commands in the allowed whitelist can be run. This provides
    flexibility for file operations and text processing while preventing
    arbitrary code execution.

    Allowed commands include:
    - Navigation: ls, pwd, tree, find
    - Reading: cat, head, tail, wc, file, stat
    - Text processing: sort, uniq, cut, awk, sed, grep, tr, diff
    - File operations: mkdir, rm, cp, mv, touch
    - Utility: echo, env, which, date, basename, dirname
    - JSON/YAML: jq, yq

    Blocked patterns:
    - Shell interpreters (bash, sh, python, etc.)
    - Network commands (curl, wget, ssh, etc.)
    - System commands (sudo, chmod, kill, etc.)
    - Command chaining (&&, ||, ;)
    - Command substitution ($(), ``)
    - Process substitution (<(), >())
    - Newline characters (\n, \r)

    Args:
        ctx: Runtime context with agent dependencies
        command: Shell command to execute
        timeout_s: Command timeout in seconds (default: 120)

    Returns:
        BashResult with exit code and output, or ToolError if command is not allowed

    Example:
        bash(command="ls -la models/")
        bash(command="cat models/schema.yml | grep 'description'")
        bash(command="find . -name '*.sql' | head -20")
        bash(command="wc -l models/marts/*.sql")
    """
    working_dir = _get_working_dir(ctx)

    if not working_dir.exists():
        return tool_error(f"Working directory not found: {working_dir}")

    # Validate command against whitelist
    validation_error = _validate_command(command)
    if validation_error:
        return tool_error(validation_error)

    logger.info(f"Executing sandboxed bash: {command} in {working_dir}")

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=working_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_s,
        )

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode or 0

        # Truncate output if too long
        stdout = _truncate_output(stdout)
        if stderr:
            stderr = _truncate_output(stderr)

        return BashResult(
            command=command,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr if stderr else None,
            working_dir=str(working_dir),
        )

    except asyncio.TimeoutError:
        return tool_error(f"Command timed out after {timeout_s} seconds: {command}")
    except Exception as e:
        logger.error(f"Error executing bash command: {e}")
        return tool_error(f"Error executing command: {e}")


@bash_toolset.tool
@safe_tool
async def list_allowed_commands(
    ctx: RunContext[AgentDeps],
) -> str:
    """List all commands allowed in the sandboxed bash environment.

    Use this tool ONLY when you need to check what shell commands are
    available in the bash tool. This does not tell you what tools are allowed in general.

    Do NOT use this tool for:
    - Searching for features or capabilities
    - Ticket management or issue tracking
    - Any purpose other than checking bash command availability

    Returns:
        Formatted list of allowed commands by category
    """
    categories = {
        "Navigation": ["ls", "pwd", "tree", "find"],
        "File Reading": ["cat", "head", "tail", "wc", "file", "stat", "less", "more"],
        "Text Processing": ["sort", "uniq", "cut", "awk", "sed", "grep", "egrep", "fgrep", "tr", "diff"],
        "File Operations": ["mkdir", "rm", "cp", "mv", "touch", "ln"],
        "Utility": ["echo", "env", "which", "whoami", "date", "basename", "dirname", "realpath"],
        "Compression": ["tar", "gzip", "gunzip", "zip", "unzip"],
        "JSON/YAML": ["jq", "yq"],
    }

    lines = ["Allowed commands in sandboxed bash:\n"]
    for category, cmds in categories.items():
        available = [c for c in cmds if c in ALLOWED_COMMANDS]
        if available:
            lines.append(f"**{category}**: {', '.join(available)}")

    lines.append("\nNot allowed: Shell interpreters, network commands, system admin commands, command chaining, newlines")

    return "\n".join(lines)
